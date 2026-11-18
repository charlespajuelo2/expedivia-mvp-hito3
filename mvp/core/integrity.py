"""Verificación de integridad de las fuentes documentales (Etapa 3).

Cada documento registra el SHA-256 calculado al momento de la ingesta. Antes de
usar evidencia (y cuando el especialista lo solicite) se vuelve a calcular el
hash del archivo actual:

- ``VIGENTE``: el hash coincide.
- ``FUENTE_MODIFICADA``: el archivo cambió después de la revisión.
- ``ARCHIVO_NO_DISPONIBLE``: la ruta ya no existe o no se puede leer.

El resultado se registra en ``integridad_eventos`` y se propaga a las evidencias
y propuestas vinculadas, de modo que una conclusión antigua no siga apareciendo
como válida si la fuente cambió.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import db
from .hashing import hash_archivo

ACTOR_INTEGRIDAD = "verificador-integridad"
ESTADO_VIGENTE = "VIGENTE"
ESTADO_MODIFICADA = "FUENTE_MODIFICADA"
ESTADO_NO_DISPONIBLE = "FUENTE_NO_DISPONIBLE"
ESTADO_NO_APLICA = "NO_APLICA"

_MAPA_EVIDENCIA = {
    ESTADO_VIGENTE: "VIGENTE",
    ESTADO_MODIFICADA: "FUENTE_MODIFICADA",
    ESTADO_NO_DISPONIBLE: "FUENTE_NO_DISPONIBLE",
}


def verificar_documento(
    ruta_bd: str | Path,
    documento_id: int,
    *,
    actor: str = ACTOR_INTEGRIDAD,
) -> dict[str, Any]:
    """Verifica un documento y propaga el resultado a evidencias y propuestas."""

    with db.conectar(ruta_bd) as conexion:
        fila = conexion.execute(
            "SELECT * FROM documentos WHERE id = ?", (documento_id,)
        ).fetchone()
        if fila is None:
            raise ValueError(f"No existe el documento con id {documento_id}.")

        documento = db.fila_a_dict(fila) or {}
        if documento.get("estado") != "VALIDO":
            return {
                "documento_id": documento_id,
                "archivo": documento.get("nombre_archivo"),
                "estado": ESTADO_NO_APLICA,
                "sha256_registrado": documento.get("sha256"),
                "sha256_actual": None,
                "detalle": "El documento no es válido; la integridad no aplica.",
                "evidencias_afectadas": 0,
                "propuestas_afectadas": 0,
            }

        registrado = documento.get("sha256")
        ruta = Path(documento.get("ruta") or "")
        actual: str | None = None
        detalle = ""

        if not ruta.exists() or not ruta.is_file():
            estado = ESTADO_NO_DISPONIBLE
            detalle = f"No se encontró el archivo: {ruta}"
        else:
            try:
                actual = hash_archivo(ruta)
            except OSError as exc:
                estado = ESTADO_NO_DISPONIBLE
                detalle = f"No se pudo leer el archivo: {exc}"
            else:
                if actual.lower() == str(registrado or "").lower():
                    estado = ESTADO_VIGENTE
                    detalle = "El hash actual coincide con el registrado."
                else:
                    estado = ESTADO_MODIFICADA
                    detalle = "El archivo cambió después de la revisión."

        timestamp = db.ahora()
        conexion.execute(
            "INSERT INTO integridad_eventos "
            "(ts, expediente_id, documento_id, archivo, sha256_registrado, "
            "sha256_actual, estado, detalle) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                timestamp,
                documento.get("expediente_id"),
                documento_id,
                documento.get("nombre_archivo"),
                registrado,
                actual,
                estado,
                detalle,
            ),
        )

        estado_evidencia = _MAPA_EVIDENCIA.get(estado)
        evidencias_afectadas = 0
        propuestas_afectadas = 0
        if estado_evidencia:
            cursor = conexion.execute(
                "UPDATE evidencias SET integridad = ? WHERE documento_id = ?",
                (estado_evidencia, documento_id),
            )
            evidencias_afectadas = cursor.rowcount
            cursor = conexion.execute(
                "UPDATE propuestas_ia SET integridad = ? WHERE documento_id = ?",
                (estado_evidencia, documento_id),
            )
            propuestas_afectadas = cursor.rowcount

        accion = (
            "INTEGRIDAD_VERIFICADA"
            if estado == ESTADO_VIGENTE
            else "FUENTE_MODIFICADA"
            if estado == ESTADO_MODIFICADA
            else "FUENTE_NO_DISPONIBLE"
            if estado == ESTADO_NO_DISPONIBLE
            else "INTEGRIDAD_OMITIDA"
        )
        db.auditar(
            conexion,
            actor=actor,
            accion=accion,
            entidad="documento",
            entidad_id=documento_id,
            detalle={
                "archivo": documento.get("nombre_archivo"),
                "estado": estado,
                "sha256_registrado": registrado,
                "sha256_actual": actual,
                "evidencias_afectadas": evidencias_afectadas,
                "propuestas_afectadas": propuestas_afectadas,
                "detalle": detalle,
            },
        )

    return {
        "documento_id": documento_id,
        "archivo": documento.get("nombre_archivo"),
        "estado": estado,
        "sha256_registrado": registrado,
        "sha256_actual": actual,
        "detalle": detalle,
        "evidencias_afectadas": evidencias_afectadas,
        "propuestas_afectadas": propuestas_afectadas,
    }


def aplicar_estado_integridad(
    ruta_bd: str | Path, documento_id: int, estado: str
) -> tuple[int, int]:
    """Propaga un estado de integridad ya calculado a evidencias y propuestas."""

    estado_evidencia = _MAPA_EVIDENCIA.get(estado)
    if not estado_evidencia:
        return (0, 0)
    with db.conectar(ruta_bd) as conexion:
        evidencias = conexion.execute(
            "UPDATE evidencias SET integridad = ? WHERE documento_id = ?",
            (estado_evidencia, documento_id),
        ).rowcount
        propuestas = conexion.execute(
            "UPDATE propuestas_ia SET integridad = ? WHERE documento_id = ?",
            (estado_evidencia, documento_id),
        ).rowcount
    return (evidencias, propuestas)


def verificar_expediente(
    ruta_bd: str | Path,
    expediente_id: str,
    *,
    actor: str = ACTOR_INTEGRIDAD,
) -> dict[str, Any]:
    """Verifica todos los documentos válidos de un expediente."""

    with db.conectar(ruta_bd) as conexion:
        filas = conexion.execute(
            "SELECT id FROM documentos WHERE expediente_id = ? AND estado = 'VALIDO' "
            "ORDER BY id",
            (expediente_id,),
        ).fetchall()

    resultados = [
        verificar_documento(ruta_bd, int(fila["id"]), actor=actor) for fila in filas
    ]
    conteo = {
        ESTADO_VIGENTE: sum(1 for r in resultados if r["estado"] == ESTADO_VIGENTE),
        ESTADO_MODIFICADA: sum(
            1 for r in resultados if r["estado"] == ESTADO_MODIFICADA
        ),
        ESTADO_NO_DISPONIBLE: sum(
            1 for r in resultados if r["estado"] == ESTADO_NO_DISPONIBLE
        ),
        ESTADO_NO_APLICA: sum(1 for r in resultados if r["estado"] == ESTADO_NO_APLICA),
    }
    resumen = {
        "expediente_id": expediente_id,
        "documentos": len(resultados),
        **conteo,
        "requiere_atencion": conteo[ESTADO_MODIFICADA] + conteo[ESTADO_NO_DISPONIBLE],
        "resultados": resultados,
    }

    with db.conectar(ruta_bd) as conexion:
        db.auditar(
            conexion,
            actor=actor,
            accion="INTEGRIDAD_EXPEDIENTE",
            entidad="expediente",
            entidad_id=expediente_id,
            detalle={
                "documentos": len(resultados),
                "vigentes": conteo[ESTADO_VIGENTE],
                "modificados": conteo[ESTADO_MODIFICADA],
                "no_disponibles": conteo[ESTADO_NO_DISPONIBLE],
            },
        )
    return resumen


def listar_eventos_integridad(
    ruta_bd: str | Path,
    expediente_id: str | None = None,
    *,
    limite: int = 100,
) -> list[dict[str, Any]]:
    """Devuelve los eventos de integridad más recientes."""

    consulta = "SELECT * FROM integridad_eventos"
    parametros: list[Any] = []
    if expediente_id:
        consulta += " WHERE expediente_id = ?"
        parametros.append(expediente_id)
    consulta += " ORDER BY id DESC LIMIT ?"
    parametros.append(limite)

    with db.conectar(ruta_bd) as conexion:
        filas = conexion.execute(consulta, parametros).fetchall()
    return [db.fila_a_dict(fila) or {} for fila in filas]
