"""Recuperación de evidencia por requisito (Etapa 3).

El recuperador no "adivina": busca términos ponderados en los fragmentos ya
extraídos, exige que el documento esté válido y clasificado, y conserva la
fuente exacta (documento, archivo, ubicación y SHA-256) para que cualquier
propuesta posterior pueda auditarse.

La puntuación es determinista y explicable::

    puntaje = Σ peso de los términos presentes + bonus por tipo documental

El resultado se ordena por puntaje y se limita por documento para no concentrar
toda la evidencia en una sola página o fila.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from . import config, db
from .extractors import sin_acentos
from .pipeline import ProcesadorDocumental


# --- Perfiles -------------------------------------------------------------


@dataclass(frozen=True)
class PerfilEvidencia:
    """Configuración de búsqueda de evidencia para un requisito."""

    id: str
    requisito: str
    criterio: str
    evidencia_esperada: str
    peso_pct: int
    terminos: dict[str, int]
    tipos_esperados: tuple[str, ...] = ()
    tipos_que_prueban: tuple[str, ...] = ()
    tipos_complementarios: tuple[str, ...] = ()
    requiere_juicio: bool = False
    puntaje_cumple: int = 18
    puntaje_minimo: int | None = None
    juicio_esperado: str = ""
    nota: str = ""

    def a_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "requisito": self.requisito,
            "criterio": self.criterio,
            "evidencia_esperada": self.evidencia_esperada,
            "peso_pct": self.peso_pct,
            "terminos": dict(self.terminos),
            "tipos_esperados": list(self.tipos_esperados),
            "tipos_que_prueban": list(self.tipos_que_prueban),
            "tipos_complementarios": list(self.tipos_complementarios),
            "requiere_juicio": self.requiere_juicio,
            "puntaje_cumple": self.puntaje_cumple,
            "puntaje_minimo": self.puntaje_minimo,
            "juicio_esperado": self.juicio_esperado,
            "nota": self.nota,
        }


@dataclass(frozen=True)
class PerfilesEvidencia:
    """Colección versionada de perfiles de recuperación."""

    version: str
    ruta: Path
    requisitos: tuple[PerfilEvidencia, ...]
    puntaje_minimo: int = 6
    max_evidencias: int = 5
    max_por_documento: int = 2
    bonus_tipo_esperado: int = 4

    def requisito(self, requisito_id: str) -> PerfilEvidencia:
        for perfil in self.requisitos:
            if perfil.id == requisito_id:
                return perfil
        raise KeyError(f"No existe el perfil de evidencia para {requisito_id}.")

    def ids(self) -> list[str]:
        return [perfil.id for perfil in self.requisitos]

    @property
    def peso_total(self) -> int:
        return sum(perfil.peso_pct for perfil in self.requisitos)


def cargar_perfiles(ruta: str | Path | None = None) -> PerfilesEvidencia:
    """Carga ``requisitos_evidencia.json`` y valida su estructura mínima."""

    ruta = Path(ruta or config.RUTA_PERFILES_EVIDENCIA)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo de perfiles: {ruta}")
    datos = json.loads(ruta.read_text(encoding="utf-8"))

    perfiles = []
    for item in datos.get("requisitos", []):
        terminos = item.get("terminos", {})
        if not isinstance(terminos, dict) or not terminos:
            raise ValueError(f"El requisito {item.get('id')} no tiene términos.")
        if not all(isinstance(peso, int) and peso > 0 for peso in terminos.values()):
            raise ValueError(
                f"Los pesos de los términos de {item.get('id')} deben ser enteros positivos."
            )
        perfiles.append(
            PerfilEvidencia(
                id=str(item["id"]),
                requisito=str(item["requisito"]),
                criterio=str(item["criterio"]),
                evidencia_esperada=str(item.get("evidencia_esperada", "")),
                peso_pct=int(item["peso_pct"]),
                terminos=dict(terminos),
                tipos_esperados=tuple(item.get("tipos_esperados", [])),
                tipos_que_prueban=tuple(item.get("tipos_que_prueban", [])),
                tipos_complementarios=tuple(item.get("tipos_complementarios", [])),
                requiere_juicio=bool(item.get("requiere_juicio", False)),
                puntaje_cumple=int(item.get("puntaje_cumple", 18)),
                puntaje_minimo=(
                    int(item["puntaje_minimo"])
                    if item.get("puntaje_minimo") is not None
                    else None
                ),
                juicio_esperado=str(item.get("juicio_esperado", "")),
                nota=str(item.get("nota", "")),
            )
        )

    if not perfiles:
        raise ValueError("El archivo de perfiles no contiene requisitos.")
    if sum(perfil.peso_pct for perfil in perfiles) != 100:
        raise ValueError("Los pesos de los perfiles deben sumar 100%.")

    return PerfilesEvidencia(
        version=str(datos.get("version", "1.0")),
        ruta=ruta,
        requisitos=tuple(perfiles),
        puntaje_minimo=int(datos.get("puntaje_minimo", 6)),
        max_evidencias=int(datos.get("max_evidencias", 5)),
        max_por_documento=int(datos.get("max_por_documento", 2)),
        bonus_tipo_esperado=int(datos.get("bonus_tipo_esperado", 4)),
    )


# --- Evidencia ------------------------------------------------------------


@dataclass
class Evidencia:
    """Fragmento recuperado, con su fuente verificable."""

    expediente_id: str
    requisito_id: str
    documento_id: int
    fragmento_orden: int
    archivo: str
    tipo_documental: str
    ubicacion: str
    sha256_fuente: str
    texto: str
    puntaje: int
    terminos: list[str] = field(default_factory=list)
    integridad: str = "VIGENTE"
    id: int | None = None
    creado_en: str | None = None

    def fuente(self) -> dict[str, Any]:
        return {
            "documento_id": self.documento_id,
            "archivo": self.archivo,
            "ubicacion": self.ubicacion,
            "sha256": self.sha256_fuente,
        }

    def a_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "expediente_id": self.expediente_id,
            "requisito_id": self.requisito_id,
            "documento_id": self.documento_id,
            "fragmento_orden": self.fragmento_orden,
            "archivo": self.archivo,
            "tipo_documental": self.tipo_documental,
            "ubicacion": self.ubicacion,
            "sha256_fuente": self.sha256_fuente,
            "texto": self.texto,
            "puntaje": self.puntaje,
            "terminos": list(self.terminos),
            "integridad": self.integridad,
            "creado_en": self.creado_en,
        }


# --- Puntuación -----------------------------------------------------------


def _normalizar(texto: str) -> str:
    """Minúsculas, sin diacríticos y con espacios uniformes."""

    texto = sin_acentos(texto)
    texto = texto.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", texto).strip()


def _patron_termino(termino: str) -> re.Pattern[str]:
    """Patrón tolerante al plural y con límites de palabra alfanuméricos."""

    normalizado = _normalizar(termino)
    return re.compile(
        r"(?<![a-z0-9])" + re.escape(normalizado) + r"(?:s|es)?(?![a-z0-9])"
    )


def puntuar_texto(texto: str, terminos: dict[str, int]) -> tuple[int, list[str]]:
    """Devuelve el puntaje y los términos encontrados en un fragmento."""

    normalizado = _normalizar(texto)
    puntaje = 0
    encontrados: list[str] = []
    for termino, peso in terminos.items():
        if _patron_termino(termino).search(normalizado):
            puntaje += peso
            encontrados.append(termino)
    return puntaje, encontrados


def _bonus_tipo(perfil: PerfilEvidencia, tipos: Iterable[str], bonus: int) -> int:
    if not bonus:
        return 0
    return bonus if any(tipo in perfil.tipos_esperados for tipo in tipos) else 0


# --- Recuperador ----------------------------------------------------------


class RecuperadorEvidencia:
    """Recupera, ordena y persiste evidencia por requisito."""

    def __init__(
        self,
        procesador: ProcesadorDocumental,
        perfiles: PerfilesEvidencia | None = None,
    ) -> None:
        self.procesador = procesador
        self.perfiles = perfiles or cargar_perfiles()

    def recuperar(
        self,
        expediente_id: str,
        requisito_id: str,
        *,
        persistir: bool = True,
    ) -> list[Evidencia]:
        perfil = self.perfiles.requisito(requisito_id)
        documentos = self.procesador.listar_documentos(expediente_id)

        candidatos: list[Evidencia] = []
        for documento in documentos:
            if documento.get("estado") != "VALIDO":
                continue
            # Un documento sin clasificación confirmada no se usa como evidencia.
            if documento.get("estado_clasificacion") != "Clasificado":
                continue

            tipo = str(documento.get("tipo_documental") or "No reconocido")
            bonus = _bonus_tipo(perfil, (tipo,), self.perfiles.bonus_tipo_esperado)
            for fragmento in self.procesador.fragmentos_de(int(documento["id"])):
                puntaje_terminos, terminos = puntuar_texto(
                    str(fragmento.get("texto", "")), perfil.terminos
                )
                if not terminos and not bonus:
                    continue
                puntaje = puntaje_terminos + bonus
                umbral = perfil.puntaje_minimo or self.perfiles.puntaje_minimo
                if puntaje < umbral:
                    continue
                candidatos.append(
                    Evidencia(
                        expediente_id=expediente_id,
                        requisito_id=requisito_id,
                        documento_id=int(documento["id"]),
                        fragmento_orden=int(fragmento.get("orden", 0)),
                        archivo=str(documento.get("nombre_archivo", "")),
                        tipo_documental=tipo,
                        ubicacion=str(fragmento.get("ubicacion", "")),
                        sha256_fuente=str(documento.get("sha256") or ""),
                        texto=str(fragmento.get("texto", "")),
                        puntaje=puntaje,
                        terminos=terminos,
                    )
                )

        candidatos.sort(
            key=lambda evidencia: (
                -evidencia.puntaje,
                evidencia.tipo_documental,
                evidencia.documento_id,
                evidencia.fragmento_orden,
            )
        )

        seleccionados: list[Evidencia] = []
        por_documento: Counter[int] = Counter()
        for candidato in candidatos:
            if por_documento[candidato.documento_id] >= self.perfiles.max_por_documento:
                continue
            seleccionados.append(candidato)
            por_documento[candidato.documento_id] += 1
            if len(seleccionados) >= self.perfiles.max_evidencias:
                break

        if persistir:
            self._persistir(expediente_id, requisito_id, seleccionados)
        return seleccionados

    def recuperar_todas(
        self, expediente_id: str, *, persistir: bool = True
    ) -> dict[str, list[Evidencia]]:
        return {
            requisito_id: self.recuperar(
                expediente_id, requisito_id, persistir=persistir
            )
            for requisito_id in self.perfiles.ids()
        }

    # -- Persistencia ----------------------------------------------------

    def _persistir(
        self,
        expediente_id: str,
        requisito_id: str,
        evidencias: list[Evidencia],
    ) -> None:
        """Inserta o actualiza sin duplicar y conserva los IDs referenciados."""

        timestamp = db.ahora()
        with db.conectar(self.procesador.ruta_bd) as conexion:
            existentes = conexion.execute(
                "SELECT id, documento_id, ubicacion FROM evidencias "
                "WHERE expediente_id = ? AND requisito_id = ?",
                (expediente_id, requisito_id),
            ).fetchall()
            indice = {
                (int(fila["documento_id"]), str(fila["ubicacion"])): int(fila["id"])
                for fila in existentes
            }
            nuevas_claves = {
                (evidencia.documento_id, evidencia.ubicacion) for evidencia in evidencias
            }

            for evidencia in evidencias:
                clave = (evidencia.documento_id, evidencia.ubicacion)
                valores = (
                    evidencia.archivo,
                    evidencia.tipo_documental,
                    evidencia.sha256_fuente,
                    evidencia.texto,
                    evidencia.puntaje,
                    json.dumps(evidencia.terminos, ensure_ascii=False),
                )
                if clave in indice:
                    evidencia_id = indice[clave]
                    conexion.execute(
                        "UPDATE evidencias SET archivo = ?, tipo_documental = ?, "
                        "sha256_fuente = ?, texto = ?, puntaje = ?, terminos = ?, "
                        "integridad = 'VIGENTE', creado_en = ? WHERE id = ?",
                        (*valores, timestamp, evidencia_id),
                    )
                else:
                    cursor = conexion.execute(
                        "INSERT INTO evidencias "
                        "(expediente_id, requisito_id, documento_id, fragmento_orden, "
                        "archivo, tipo_documental, ubicacion, sha256_fuente, texto, "
                        "puntaje, terminos, integridad, creado_en) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'VIGENTE', ?)",
                        (
                            expediente_id,
                            requisito_id,
                            evidencia.documento_id,
                            evidencia.fragmento_orden,
                            evidencia.archivo,
                            evidencia.tipo_documental,
                            evidencia.ubicacion,
                            evidencia.sha256_fuente,
                            evidencia.texto,
                            evidencia.puntaje,
                            json.dumps(evidencia.terminos, ensure_ascii=False),
                            timestamp,
                        ),
                    )
                    evidencia_id = int(cursor.lastrowid)
                evidencia.id = evidencia_id
                evidencia.integridad = "VIGENTE"
                evidencia.creado_en = timestamp

            # Elimina evidencia obsoleta que no esté referenciada por una propuesta.
            for clave, evidencia_id in indice.items():
                if clave in nuevas_claves:
                    continue
                referenciada = conexion.execute(
                    "SELECT 1 FROM propuestas_ia WHERE evidencia_id = ? LIMIT 1",
                    (evidencia_id,),
                ).fetchone()
                if not referenciada:
                    conexion.execute("DELETE FROM evidencias WHERE id = ?", (evidencia_id,))

            db.auditar(
                conexion,
                actor="recuperador-evidencia",
                accion="EVIDENCIA_RECUPERADA",
                entidad="requisito",
                entidad_id=f"{expediente_id}:{requisito_id}",
                detalle={
                    "requisito_id": requisito_id,
                    "evidencias": len(evidencias),
                    "puntaje_maximo": max(
                        (evidencia.puntaje for evidencia in evidencias), default=0
                    ),
                    "documentos": sorted(
                        {evidencia.archivo for evidencia in evidencias}
                    ),
                },
            )


def listar_evidencias(
    ruta_bd: str | Path,
    expediente_id: str,
    requisito_id: str | None = None,
    *,
    solo_vigentes: bool = True,
) -> list[dict[str, Any]]:
    """Devuelve la evidencia persistida, lista para la interfaz o un reporte."""

    consulta = "SELECT * FROM evidencias WHERE expediente_id = ?"
    parametros: list[Any] = [expediente_id]
    if requisito_id:
        consulta += " AND requisito_id = ?"
        parametros.append(requisito_id)
    if solo_vigentes:
        consulta += " AND integridad = 'VIGENTE'"
    consulta += " ORDER BY requisito_id, puntaje DESC, documento_id, fragmento_orden"

    with db.conectar(ruta_bd) as conexion:
        filas = conexion.execute(consulta, parametros).fetchall()

    evidencias = []
    for fila in filas:
        datos = db.fila_a_dict(fila) or {}
        datos["terminos"] = json.loads(datos["terminos"]) if datos.get("terminos") else []
        evidencias.append(datos)
    return evidencias
