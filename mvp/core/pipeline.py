"""Pipeline de procesamiento documental (Etapa 2).

Flujo por archivo::

    validar ruta/formato/tamaño → SHA-256 → caché por hash → extraer
    → clasificar → aplicar corrección humana previa → persistir + auditar

La caché se indexa por ``sha256 + versión del extractor``. Las correcciones de
clasificación se guardan aparte, también por ``sha256``, para que sobrevivan a
una recarga o a un acierto de caché.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any

from . import classifier, config, db
from .extractors import ErrorExtraccion, Extraccion, extraer
from .hashing import hash_archivo


@dataclass
class ResultadoIngesta:
    """Resultado de procesar un archivo, exitoso o rechazado."""

    ok: bool
    nombre_archivo: str
    ruta: str
    formato: str
    estado: str
    sha256: str | None = None
    motivo_rechazo: str | None = None
    mensaje: str = ""
    documento_id: int | None = None
    cache_hit: bool = False
    clasificacion: classifier.Clasificacion | None = None
    texto_recuperable: str | None = None
    fragmentos: int = 0
    duracion_ms: int = 0
    advertencias: list[str] = field(default_factory=list)

    def a_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "nombre_archivo": self.nombre_archivo,
            "ruta": self.ruta,
            "formato": self.formato,
            "estado": self.estado,
            "sha256": self.sha256,
            "motivo_rechazo": self.motivo_rechazo,
            "mensaje": self.mensaje,
            "documento_id": self.documento_id,
            "cache_hit": self.cache_hit,
            "tipo_documental": self.clasificacion.tipo_documental
            if self.clasificacion
            else None,
            "componente": self.clasificacion.componente if self.clasificacion else None,
            "confianza": self.clasificacion.confianza if self.clasificacion else None,
            "texto_recuperable": self.texto_recuperable,
            "fragmentos": self.fragmentos,
            "duracion_ms": self.duracion_ms,
            "advertencias": list(self.advertencias),
        }


class ProcesadorDocumental:
    """Servicio de ingesta y consulta documental sobre SQLite."""

    def __init__(
        self,
        ruta_bd: str | Path | None = None,
        *,
        umbral_confianza: int = config.UMBRAL_CONFIANZA,
        extractor_version: str = config.EXTRACTOR_VERSION,
    ) -> None:
        self.ruta_bd = db.inicializar(ruta_bd or config.RUTA_BD)
        self.umbral_confianza = umbral_confianza
        self.extractor_version = extractor_version

    # -- Expedientes ------------------------------------------------------

    def registrar_expediente(
        self,
        expediente_id: str,
        nombre: str,
        *,
        especialidad: str = "",
        version: str = "",
        actor: str = "sistema",
    ) -> dict[str, Any]:
        expediente_id = expediente_id.strip()
        if not expediente_id:
            raise ValueError("El identificador del expediente es obligatorio.")

        with db.conectar(self.ruta_bd) as conexion:
            existente = conexion.execute(
                "SELECT id FROM expedientes WHERE id = ?", (expediente_id,)
            ).fetchone()
            if existente:
                conexion.execute(
                    "UPDATE expedientes SET nombre = ?, especialidad = ?, version = ? "
                    "WHERE id = ?",
                    (nombre, especialidad, version, expediente_id),
                )
            else:
                conexion.execute(
                    "INSERT INTO expedientes (id, nombre, especialidad, version, creado_en) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (expediente_id, nombre, especialidad, version, db.ahora()),
                )
                db.auditar(
                    conexion,
                    actor=actor,
                    accion="EXPEDIENTE_REGISTRADO",
                    entidad="expediente",
                    entidad_id=expediente_id,
                    detalle={"nombre": nombre, "especialidad": especialidad},
                )
            fila = conexion.execute(
                "SELECT * FROM expedientes WHERE id = ?", (expediente_id,)
            ).fetchone()
        return db.fila_a_dict(fila) or {}

    def listar_expedientes(self) -> list[dict[str, Any]]:
        with db.conectar(self.ruta_bd) as conexion:
            filas = conexion.execute(
                "SELECT * FROM expedientes ORDER BY creado_en, id"
            ).fetchall()
        return [db.fila_a_dict(f) or {} for f in filas]

    # -- Ingesta ----------------------------------------------------------

    def ingestar_archivo(
        self,
        expediente_id: str,
        ruta: str | Path,
        *,
        actor: str = "sistema",
    ) -> ResultadoIngesta:
        """Procesa un archivo y devuelve el resultado sin lanzar excepciones de negocio."""

        inicio = perf_counter()
        ruta = Path(ruta)
        nombre = ruta.name
        formato = ruta.suffix.lower().lstrip(".").upper() or "SIN_EXTENSION"

        def rechazar(
            codigo: str,
            mensaje: str,
            *,
            sha256: str | None = None,
            detalle: str | None = None,
        ) -> ResultadoIngesta:
            duracion = int((perf_counter() - inicio) * 1000)
            documento_id = self._persistir(
                expediente_id=expediente_id,
                nombre=nombre,
                ruta=str(ruta),
                formato=formato,
                tamano=ruta.stat().st_size if ruta.exists() else 0,
                sha256=sha256,
                estado="RECHAZADO",
                motivo=codigo,
                mensaje=mensaje,
                texto_recuperable=None,
                paginas=None,
                caracteres=0,
                fragmentos=[],
                cache_hit=False,
                clasificacion=None,
                advertencias=[],
                duracion_ms=duracion,
                actor=actor,
            )
            return ResultadoIngesta(
                ok=False,
                nombre_archivo=nombre,
                ruta=str(ruta),
                formato=formato,
                estado="RECHAZADO",
                sha256=sha256,
                motivo_rechazo=codigo,
                mensaje=mensaje + (f" Detalle: {detalle}" if detalle else ""),
                documento_id=documento_id,
                duracion_ms=duracion,
            )

        if not ruta.exists():
            return rechazar("ARCHIVO_NO_ENCONTRADO", "No se encontró el archivo indicado.")
        if not ruta.is_file():
            return rechazar("ARCHIVO_INVALIDO", "La ruta no corresponde a un archivo.")

        tamano = ruta.stat().st_size
        if tamano == 0:
            return rechazar("ARCHIVO_VACIO", "El archivo está vacío (0 bytes).")
        if tamano > config.TAMANO_MAXIMO_BYTES:
            return rechazar(
                "TAMANO_EXCEDIDO",
                f"El archivo supera el límite de {config.TAMANO_MAXIMO_MB} MB.",
            )

        try:
            sha256 = hash_archivo(ruta)
        except OSError as exc:
            return rechazar("ARCHIVO_ILEGIBLE", "No se pudo leer el archivo.", detalle=str(exc))

        if ruta.suffix.lower() not in config.FORMATOS_PERMITIDOS:
            return rechazar(
                "FORMATO_NO_SOPORTADO",
                f"Formato '{ruta.suffix or 'sin extensión'}' no soportado. "
                f"Use: {', '.join(sorted(config.FORMATOS_PERMITIDOS))}.",
                sha256=sha256,
            )

        try:
            with db.conectar(self.ruta_bd) as conexion:
                extraccion, cache_hit = self._extraer_con_cache(conexion, ruta, sha256)
        except ErrorExtraccion as exc:
            return rechazar(exc.codigo, exc.mensaje, sha256=sha256, detalle=exc.detalle)

        clasificacion = classifier.clasificar(
            nombre, extraccion, umbral=self.umbral_confianza
        )

        with db.conectar(self.ruta_bd) as conexion:
            correccion = self._obtener_correccion(conexion, sha256)
            if correccion:
                clasificacion = classifier.Clasificacion(
                    tipo_documental=correccion["tipo_documental"],
                    componente=correccion["componente"],
                    confianza=int(correccion["confianza"]),
                    estado="Clasificado",
                    coincidencias=["corrección humana previa"],
                    origen="correccion_humana",
                )

        duracion = int((perf_counter() - inicio) * 1000)

        documento_id = self._persistir(
            expediente_id=expediente_id,
            nombre=nombre,
            ruta=str(ruta),
            formato=formato,
            tamano=tamano,
            sha256=sha256,
            estado="VALIDO",
            motivo=None,
            mensaje="Documento procesado correctamente.",
            texto_recuperable=extraccion.texto_recuperable,
            paginas=extraccion.paginas,
            caracteres=extraccion.caracteres,
            fragmentos=extraccion.fragmentos,
            cache_hit=cache_hit,
            clasificacion=clasificacion,
            advertencias=extraccion.advertencias,
            duracion_ms=duracion,
            actor=actor,
        )

        return ResultadoIngesta(
            ok=True,
            nombre_archivo=nombre,
            ruta=str(ruta),
            formato=formato,
            estado="VALIDO",
            sha256=sha256,
            mensaje="Documento procesado correctamente.",
            documento_id=documento_id,
            cache_hit=cache_hit,
            clasificacion=clasificacion,
            texto_recuperable=extraccion.texto_recuperable,
            fragmentos=len(extraccion.fragmentos),
            duracion_ms=duracion,
            advertencias=list(extraccion.advertencias),
        )

    def ingestar_carpeta(
        self,
        expediente_id: str,
        carpeta: str | Path,
        *,
        actor: str = "sistema",
        extensiones: set[str] | None = None,
    ) -> list[ResultadoIngesta]:
        """Procesa todos los archivos de una carpeta (orden alfabético)."""

        carpeta = Path(carpeta)
        if not carpeta.is_dir():
            raise ValueError(f"No es una carpeta válida: {carpeta}")

        permitidas = extensiones or config.FORMATOS_PERMITIDOS
        archivos = sorted(
            (
                ruta
                for ruta in carpeta.iterdir()
                if ruta.is_file() and ruta.suffix.lower() in permitidas
            ),
            key=lambda ruta: ruta.name.lower(),
        )
        resultados = [
            self.ingestar_archivo(expediente_id, ruta, actor=actor) for ruta in archivos
        ]

        with db.conectar(self.ruta_bd) as conexion:
            db.auditar(
                conexion,
                actor=actor,
                accion="INGESTA_CARPETA",
                entidad="expediente",
                entidad_id=expediente_id,
                detalle={
                    "carpeta": str(carpeta),
                    "archivos": len(archivos),
                    "validos": sum(1 for r in resultados if r.ok),
                    "rechazados": sum(1 for r in resultados if not r.ok),
                },
            )
        return resultados

    # -- Caché y persistencia --------------------------------------------

    def _extraer_con_cache(
        self, conexion: Any, ruta: Path, sha256: str
    ) -> tuple[Extraccion, bool]:
        fila = conexion.execute(
            "SELECT payload FROM cache_extraccion WHERE sha256 = ? AND extractor_version = ?",
            (sha256, self.extractor_version),
        ).fetchone()
        if fila:
            conexion.execute(
                "UPDATE cache_extraccion SET hits = hits + 1, ultimo_uso = ? WHERE sha256 = ?",
                (db.ahora(), sha256),
            )
            return Extraccion.desde_dict(json.loads(fila["payload"])), True

        extraccion = extraer(ruta)
        conexion.execute(
            "INSERT OR REPLACE INTO cache_extraccion "
            "(sha256, extractor_version, formato, payload, creado_en, ultimo_uso, hits) "
            "VALUES (?, ?, ?, ?, ?, ?, 0)",
            (
                sha256,
                self.extractor_version,
                extraccion.formato,
                json.dumps(extraccion.a_dict(), ensure_ascii=False),
                db.ahora(),
                db.ahora(),
            ),
        )
        return extraccion, False

    def _obtener_correccion(
        self, conexion: Any, sha256: str | None
    ) -> dict[str, Any] | None:
        if not sha256:
            return None
        fila = conexion.execute(
            "SELECT * FROM correcciones_clasificacion WHERE sha256 = ?", (sha256,)
        ).fetchone()
        return db.fila_a_dict(fila)

    def _persistir(
        self,
        *,
        expediente_id: str,
        nombre: str,
        ruta: str,
        formato: str,
        tamano: int,
        sha256: str | None,
        estado: str,
        motivo: str | None,
        mensaje: str,
        texto_recuperable: str | None,
        paginas: int | None,
        caracteres: int,
        fragmentos: list[Any],
        cache_hit: bool,
        clasificacion: classifier.Clasificacion | None,
        advertencias: list[str],
        duracion_ms: int,
        actor: str,
    ) -> int:
        timestamp = db.ahora()
        valores = (
            expediente_id,
            nombre,
            ruta,
            formato,
            tamano,
            sha256,
            self.extractor_version,
            estado,
            motivo,
            mensaje,
            texto_recuperable,
            paginas,
            caracteres,
            len(fragmentos),
            1 if cache_hit else 0,
            clasificacion.tipo_documental if clasificacion else None,
            clasificacion.componente if clasificacion else None,
            clasificacion.confianza if clasificacion else None,
            clasificacion.origen if clasificacion else None,
            json.dumps(advertencias, ensure_ascii=False) if advertencias else None,
            duracion_ms,
            timestamp,
            timestamp,
        )

        with db.conectar(self.ruta_bd) as conexion:
            conexion.execute(
                """
                INSERT INTO documentos (
                    expediente_id, nombre_archivo, ruta, formato, tamano_bytes, sha256,
                    extractor_version, estado, motivo_rechazo, mensaje, texto_recuperable,
                    paginas, caracteres, fragmentos, cache_hit, tipo_documental,
                    componente, confianza, clasificacion_origen, advertencias,
                    duracion_ms, creado_en, actualizado_en
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (expediente_id, nombre_archivo) DO UPDATE SET
                    ruta = excluded.ruta,
                    formato = excluded.formato,
                    tamano_bytes = excluded.tamano_bytes,
                    sha256 = excluded.sha256,
                    extractor_version = excluded.extractor_version,
                    estado = excluded.estado,
                    motivo_rechazo = excluded.motivo_rechazo,
                    mensaje = excluded.mensaje,
                    texto_recuperable = excluded.texto_recuperable,
                    paginas = excluded.paginas,
                    caracteres = excluded.caracteres,
                    fragmentos = excluded.fragmentos,
                    cache_hit = excluded.cache_hit,
                    tipo_documental = excluded.tipo_documental,
                    componente = excluded.componente,
                    confianza = excluded.confianza,
                    clasificacion_origen = excluded.clasificacion_origen,
                    advertencias = excluded.advertencias,
                    duracion_ms = excluded.duracion_ms,
                    actualizado_en = excluded.actualizado_en
                """,
                valores,
            )
            fila = conexion.execute(
                "SELECT id FROM documentos WHERE expediente_id = ? AND nombre_archivo = ?",
                (expediente_id, nombre),
            ).fetchone()
            documento_id = int(fila["id"])

            conexion.execute(
                "DELETE FROM fragmentos WHERE documento_id = ?", (documento_id,)
            )
            conexion.executemany(
                "INSERT INTO fragmentos (documento_id, orden, ubicacion, tipo, texto) "
                "VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        documento_id,
                        fragmento.orden,
                        fragmento.ubicacion,
                        fragmento.tipo,
                        fragmento.texto,
                    )
                    for fragmento in fragmentos
                ],
            )

            if estado == "VALIDO":
                db.auditar(
                    conexion,
                    actor=actor,
                    accion="DOCUMENTO_PROCESADO",
                    entidad="documento",
                    entidad_id=documento_id,
                    detalle={
                        "archivo": nombre,
                        "sha256": sha256,
                        "cache_hit": cache_hit,
                        "tipo_documental": clasificacion.tipo_documental
                        if clasificacion
                        else None,
                        "confianza": clasificacion.confianza if clasificacion else None,
                        "fragmentos": len(fragmentos),
                    },
                )
                if cache_hit:
                    db.auditar(
                        conexion,
                        actor=actor,
                        accion="CACHE_REUTILIZADA",
                        entidad="documento",
                        entidad_id=documento_id,
                        detalle={"sha256": sha256, "archivo": nombre},
                    )
            else:
                db.auditar(
                    conexion,
                    actor=actor,
                    accion="DOCUMENTO_RECHAZADO",
                    entidad="documento",
                    entidad_id=documento_id,
                    detalle={
                        "archivo": nombre,
                        "motivo": motivo,
                        "sha256": sha256,
                        "mensaje": mensaje,
                    },
                )

        return documento_id

    # -- Corrección humana ------------------------------------------------

    def corregir_clasificacion(
        self,
        documento_id: int,
        tipo_documental: str,
        componente: str,
        *,
        actor: str,
        motivo: str,
        confianza: int = 100,
    ) -> dict[str, Any]:
        """Registra una corrección humana y la vincula al hash del documento."""

        if not motivo.strip():
            raise ValueError("El motivo de la corrección es obligatorio.")

        with db.conectar(self.ruta_bd) as conexion:
            fila = conexion.execute(
                "SELECT * FROM documentos WHERE id = ?", (documento_id,)
            ).fetchone()
            if fila is None:
                raise ValueError(f"No existe el documento con id {documento_id}.")
            documento = db.fila_a_dict(fila) or {}

            anterior = {
                "tipo_documental": documento.get("tipo_documental"),
                "componente": documento.get("componente"),
                "confianza": documento.get("confianza"),
                "origen": documento.get("clasificacion_origen"),
            }

            timestamp = db.ahora()
            if documento.get("sha256"):
                conexion.execute(
                    """
                    INSERT INTO correcciones_clasificacion
                        (sha256, tipo_documental, componente, confianza, decidido_por, motivo, creado_en)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (sha256) DO UPDATE SET
                        tipo_documental = excluded.tipo_documental,
                        componente = excluded.componente,
                        confianza = excluded.confianza,
                        decidido_por = excluded.decidido_por,
                        motivo = excluded.motivo,
                        creado_en = excluded.creado_en
                    """,
                    (
                        documento["sha256"],
                        tipo_documental,
                        componente,
                        confianza,
                        actor,
                        motivo.strip(),
                        timestamp,
                    ),
                )

            conexion.execute(
                "UPDATE documentos SET tipo_documental = ?, componente = ?, confianza = ?, "
                "clasificacion_origen = 'correccion_humana', actualizado_en = ? WHERE id = ?",
                (tipo_documental, componente, confianza, timestamp, documento_id),
            )

            db.auditar(
                conexion,
                actor=actor,
                accion="CLASIFICACION_CORREGIDA",
                entidad="documento",
                entidad_id=documento_id,
                detalle={
                    "archivo": documento.get("nombre_archivo"),
                    "sha256": documento.get("sha256"),
                    "anterior": anterior,
                    "nuevo": {
                        "tipo_documental": tipo_documental,
                        "componente": componente,
                        "confianza": confianza,
                    },
                    "motivo": motivo.strip(),
                },
            )

            fila = conexion.execute(
                "SELECT * FROM documentos WHERE id = ?", (documento_id,)
            ).fetchone()
        return self._documento_a_dict(fila)

    # -- Consultas --------------------------------------------------------

    @staticmethod
    def _documento_a_dict(fila: Any) -> dict[str, Any]:
        documento = db.fila_a_dict(fila) or {}
        if documento:
            documento["cache_hit"] = bool(documento.get("cache_hit"))
            advertencias = documento.get("advertencias")
            documento["advertencias"] = (
                json.loads(advertencias) if advertencias else []
            )
            documento["estado_clasificacion"] = (
                "Clasificado"
                if documento.get("estado") == "VALIDO"
                and documento.get("tipo_documental")
                and documento.get("tipo_documental") != classifier.TIPO_NO_RECONOCIDO
                and (documento.get("confianza") or 0) >= config.UMBRAL_CONFIANZA
                else "Sin clasificar"
            )
        return documento

    def listar_documentos(self, expediente_id: str) -> list[dict[str, Any]]:
        with db.conectar(self.ruta_bd) as conexion:
            filas = conexion.execute(
                "SELECT * FROM documentos WHERE expediente_id = ? ORDER BY id",
                (expediente_id,),
            ).fetchall()
        return [self._documento_a_dict(fila) for fila in filas]

    def obtener_documento(self, documento_id: int) -> dict[str, Any] | None:
        with db.conectar(self.ruta_bd) as conexion:
            fila = conexion.execute(
                "SELECT * FROM documentos WHERE id = ?", (documento_id,)
            ).fetchone()
        return self._documento_a_dict(fila) if fila else None

    def fragmentos_de(self, documento_id: int) -> list[dict[str, Any]]:
        with db.conectar(self.ruta_bd) as conexion:
            filas = conexion.execute(
                "SELECT orden, ubicacion, tipo, texto FROM fragmentos "
                "WHERE documento_id = ? ORDER BY orden",
                (documento_id,),
            ).fetchall()
        return [db.fila_a_dict(fila) or {} for fila in filas]

    def listar_auditoria(self, limite: int = 200) -> list[dict[str, Any]]:
        with db.conectar(self.ruta_bd) as conexion:
            filas = conexion.execute(
                "SELECT * FROM auditoria ORDER BY id DESC LIMIT ?", (limite,)
            ).fetchall()
        registros = []
        for fila in filas:
            registro = db.fila_a_dict(fila) or {}
            registro["detalle"] = (
                json.loads(registro["detalle"]) if registro.get("detalle") else {}
            )
            registros.append(registro)
        return registros

    def resumen_procesamiento(self, expediente_id: str) -> dict[str, Any]:
        documentos = self.listar_documentos(expediente_id)
        validos = [d for d in documentos if d["estado"] == "VALIDO"]
        rechazados = [d for d in documentos if d["estado"] == "RECHAZADO"]

        motivos = Counter(d.get("motivo_rechazo") for d in rechazados)
        tipos = Counter(
            d.get("tipo_documental") for d in validos if d.get("tipo_documental")
        )
        texto = Counter(d.get("texto_recuperable") for d in validos)

        return {
            "expediente_id": expediente_id,
            "documentos_total": len(documentos),
            "validos": len(validos),
            "rechazados": len(rechazados),
            "cache_hits": sum(1 for d in documentos if d.get("cache_hit")),
            "texto_si": texto.get("si", 0),
            "texto_parcial": texto.get("parcial", 0),
            "texto_no": texto.get("no", 0),
            "clasificados": sum(
                1 for d in validos if d.get("estado_clasificacion") == "Clasificado"
            ),
            "sin_clasificar": sum(
                1 for d in validos if d.get("estado_clasificacion") == "Sin clasificar"
            ),
            "corregidos": sum(
                1 for d in validos if d.get("clasificacion_origen") == "correccion_humana"
            ),
            "fragmentos_total": sum(int(d.get("fragmentos") or 0) for d in documentos),
            "duracion_total_ms": sum(int(d.get("duracion_ms") or 0) for d in documentos),
            "motivos_rechazo": dict(motivos),
            "tipos_documentales": dict(tipos),
        }

    def exportar_inventario_csv(
        self, expediente_id: str, destino: str | Path
    ) -> Path:
        """Exporta el inventario procesado para evidencia de la etapa."""

        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        columnas = [
            "id",
            "nombre_archivo",
            "formato",
            "estado",
            "motivo_rechazo",
            "sha256",
            "texto_recuperable",
            "paginas",
            "fragmentos",
            "cache_hit",
            "tipo_documental",
            "componente",
            "confianza",
            "estado_clasificacion",
            "clasificacion_origen",
            "duracion_ms",
        ]
        with destino.open("w", encoding="utf-8", newline="") as manejador:
            escritor = csv.DictWriter(manejador, fieldnames=columnas)
            escritor.writeheader()
            for documento in self.listar_documentos(expediente_id):
                escritor.writerow({clave: documento.get(clave) for clave in columnas})
        return destino
