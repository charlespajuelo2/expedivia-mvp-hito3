"""Decisión humana, historial y avance ponderado (Etapa 4).

Reglas del catálogo de cinco estados:

- ``Cumple``, ``Cumple parcialmente`` y ``No cumple`` son concluyentes y aportan
  al cumplimiento ponderado con factores 1.0, 0.5 y 0.0.
- ``No se encontró información`` **nunca** equivale a ``No cumple``: no aporta al
  cumplimiento y se contabiliza aparte.
- ``Requiere revisión especializada`` tampoco es un incumplimiento.

Decisión humana (inmutable, se agrega una fila por cada decisión):

- ``aceptar``: el estado final es el estado propuesto por la IA.
- ``modificar``: el especialista fija un estado final distinto y lo motiva.
- ``descartar``: la propuesta se descarta; el requisito queda como
  ``No se encontró información`` (no se inventa un ``No cumple``).

La propuesta original **nunca se sobrescribe**: la tabla ``decisiones`` conserva
``estado_propuesto`` y el historial se une con ``propuestas_ia`` para mostrar la
fuente, la cita y la huella.

Avance ponderado (redondeo ``ROUND_HALF_UP`` a 1 decimal)::

    avance_pct = Σ(peso × factor_avance) / peso_total × 100

donde ``factor_avance`` es 0 si el requisito no tiene decisión o si la decisión
fue ``descartar``; en otro caso es el factor del estado final. Así, el avance
solo refleja hallazgos efectivamente validados por una persona.
"""

from __future__ import annotations

import hashlib
import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from . import config, db
from .evidence import PerfilesEvidencia, cargar_perfiles

DECISIONES = ("aceptar", "modificar", "descartar")

ESTADO_SIN_INFORMACION = "No se encontró información"
ESTADO_REVISION = "Requiere revisión especializada"

FACTORES_ESTADO = {
    "Cumple": Decimal("1.0"),
    "Cumple parcialmente": Decimal("0.5"),
    "No cumple": Decimal("0.0"),
}

#: Efecto de cada decisión sobre el factor del estado final.
#: ``descartar`` anula el avance; las otras dos usan el factor del estado final.
FACTORES_DECISION = {
    "aceptar": "estado_final",
    "modificar": "estado_final",
    "descartar": "cero",
}


# --- Utilidades -----------------------------------------------------------


def redondear_1(valor: Decimal | float | int) -> float:
    """Redondeo definido para todas las métricas porcentuales."""

    return float(
        Decimal(str(valor)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    )


def factor_estado(estado: str | None) -> Decimal:
    """Factor del estado final; los no concluyentes valen cero."""

    return FACTORES_ESTADO.get(str(estado or ""), Decimal("0.0"))


def factor_avance(decision: str | None, estado_final: str | None) -> Decimal:
    """Factor de avance de un requisito según su decisión vigente."""

    if not decision:
        return Decimal("0.0")
    if FACTORES_DECISION.get(decision) == "cero":
        return Decimal("0.0")
    return factor_estado(estado_final)


def calcular_huella(propuesta: dict[str, Any]) -> str:
    """Huella canónica de una propuesta para no duplicar hallazgos.

    Incluye estado, fuente, cita, observación y motivo. El resultado es estable
    entre ejecuciones y no depende del orden de las claves.
    """

    fuente = propuesta.get("fuente")
    fuente = fuente if isinstance(fuente, dict) else {}
    canonica = {
        "requisito_id": propuesta.get("requisito_id"),
        "estado_propuesto": propuesta.get("estado_propuesto"),
        "evidencia_encontrada": bool(propuesta.get("evidencia_encontrada")),
        "documento_id": fuente.get("documento_id"),
        "archivo": fuente.get("archivo"),
        "ubicacion": fuente.get("ubicacion"),
        "sha256": fuente.get("sha256"),
        "cita": propuesta.get("cita"),
        "observacion": propuesta.get("observacion_preliminar"),
        "requiere_revision": bool(propuesta.get("requiere_revision_especializada")),
        "motivo": propuesta.get("motivo"),
    }
    texto = json.dumps(canonica, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# --- Decisiones -----------------------------------------------------------


def _version_expediente(conexion, expediente_id: str) -> str:
    fila = conexion.execute(
        "SELECT version FROM expedientes WHERE id = ?", (expediente_id,)
    ).fetchone()
    return str(fila["version"] or "") if fila else ""


def decidir(
    ruta_bd: str | Path | None,
    expediente_id: str,
    requisito_id: str,
    decision: str,
    *,
    actor: str,
    motivo: str,
    estado_final: str | None = None,
    propuesta_id: int | None = None,
) -> dict[str, Any]:
    """Registra una decisión humana motivada y auditable.

    La propuesta original se conserva intacta. Cada llamada agrega una fila al
    historial; la decisión vigente es la de mayor ``id`` para el requisito.
    """

    decision = (decision or "").strip().lower()
    if decision not in DECISIONES:
        raise ValueError(
            f"Decisión inválida: {decision}. Use una de: " + ", ".join(DECISIONES)
        )
    actor = (actor or "").strip()
    motivo = (motivo or "").strip()
    if not actor:
        raise ValueError("El responsable de la decisión es obligatorio.")
    if not motivo:
        raise ValueError("El motivo de la decisión es obligatorio.")

    with db.conectar(ruta_bd or config.RUTA_BD) as conexion:
        if propuesta_id is not None:
            propuesta = conexion.execute(
                "SELECT * FROM propuestas_ia WHERE id = ? AND expediente_id = ? "
                "AND requisito_id = ?",
                (propuesta_id, expediente_id, requisito_id),
            ).fetchone()
        else:
            propuesta = conexion.execute(
                "SELECT * FROM propuestas_ia WHERE expediente_id = ? AND "
                "requisito_id = ? AND valida = 1 ORDER BY id DESC LIMIT 1",
                (expediente_id, requisito_id),
            ).fetchone()

        if propuesta is None:
            raise ValueError(
                f"No hay propuesta válida que decidir para {requisito_id}. "
                "Ejecute el análisis antes de evaluar."
            )

        estado_propuesto = propuesta["estado_propuesto"]
        if not estado_propuesto:
            raise ValueError(
                "La propuesta no declara estado; no se puede aceptar ni modificar."
            )
        if str(propuesta["integridad"] or "VIGENTE") != "VIGENTE":
            raise ValueError(
                "La fuente de la propuesta cambió o no está disponible. "
                "Vuelva a analizar el requisito antes de decidir."
            )

        if decision == "aceptar":
            if estado_final and estado_final != estado_propuesto:
                raise ValueError(
                    "Aceptar conserva el estado propuesto; use 'modificar' para "
                    "cambiarlo."
                )
            estado_final = estado_propuesto
        elif decision == "modificar":
            if not estado_final:
                raise ValueError("Modificar exige indicar el estado final.")
            if estado_final not in config.ESTADOS_REQUISITO:
                raise ValueError(
                    f"Estado final inválido: {estado_final}. Use uno de: "
                    + ", ".join(config.ESTADOS_REQUISITO)
                )
            if estado_final == estado_propuesto:
                raise ValueError(
                    "El estado final de una modificación debe ser distinto del "
                    "estado propuesto."
                )
        else:  # descartar
            if estado_final and estado_final != ESTADO_SIN_INFORMACION:
                raise ValueError(
                    "Descartar deja el requisito en 'No se encontró información'; "
                    "no fija otro estado."
                )
            estado_final = ESTADO_SIN_INFORMACION

        version_kb = _version_expediente(conexion, expediente_id)
        cursor = conexion.execute(
            "INSERT INTO decisiones (expediente_id, requisito_id, propuesta_id, "
            "decision, estado_propuesto, estado_final, motivo, actor, version_kb, "
            "huella_propuesta, creado_en) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                expediente_id,
                requisito_id,
                int(propuesta["id"]),
                decision,
                estado_propuesto,
                estado_final,
                motivo,
                actor,
                version_kb,
                propuesta["huella"],
                db.ahora(),
            ),
        )
        decision_id = int(cursor.lastrowid)
        db.auditar(
            conexion,
            actor=actor,
            accion="DECISION_REGISTRADA",
            entidad="requisito",
            entidad_id=f"{expediente_id}:{requisito_id}",
            detalle={
                "decision_id": decision_id,
                "decision": decision,
                "propuesta_id": int(propuesta["id"]),
                "estado_propuesto": estado_propuesto,
                "estado_final": estado_final,
                "motivo": motivo,
                "version_kb": version_kb,
            },
        )
        fila = conexion.execute(
            "SELECT * FROM decisiones WHERE id = ?", (decision_id,)
        ).fetchone()

    return db.fila_a_dict(fila) or {}


def _fila_historial(fila) -> dict[str, Any]:
    datos = db.fila_a_dict(fila) or {}
    return datos


def historial(
    ruta_bd: str | Path | None,
    expediente_id: str,
    requisito_id: str | None = None,
    *,
    limite: int = 500,
) -> list[dict[str, Any]]:
    """Historial completo de decisiones con la propuesta original asociada."""

    consulta = (
        "SELECT d.*, p.proveedor, p.modelo, p.cita, p.archivo, p.ubicacion, "
        "p.observacion AS propuesta_observacion, p.requiere_revision, "
        "p.integridad AS propuesta_integridad "
        "FROM decisiones d "
        "LEFT JOIN propuestas_ia p ON p.id = d.propuesta_id "
        "WHERE d.expediente_id = ?"
    )
    parametros: list[Any] = [expediente_id]
    if requisito_id:
        consulta += " AND d.requisito_id = ?"
        parametros.append(requisito_id)
    consulta += " ORDER BY d.id DESC LIMIT ?"
    parametros.append(limite)

    with db.conectar(ruta_bd or config.RUTA_BD) as conexion:
        filas = conexion.execute(consulta, parametros).fetchall()

    registros = [_fila_historial(fila) for fila in filas]
    vistos: set[str] = set()
    for registro in registros:
        requisito = str(registro["requisito_id"])
        registro["es_vigente"] = requisito not in vistos
        vistos.add(requisito)
    return registros


def decision_vigente(
    ruta_bd: str | Path | None, expediente_id: str, requisito_id: str
) -> dict[str, Any] | None:
    """Última decisión registrada para un requisito."""

    with db.conectar(ruta_bd or config.RUTA_BD) as conexion:
        fila = conexion.execute(
            "SELECT * FROM decisiones WHERE expediente_id = ? AND requisito_id = ? "
            "ORDER BY id DESC LIMIT 1",
            (expediente_id, requisito_id),
        ).fetchone()
    return db.fila_a_dict(fila)


def decisiones_vigentes(
    ruta_bd: str | Path | None, expediente_id: str
) -> dict[str, dict[str, Any]]:
    """Decisión vigente por requisito (una sola por requisito)."""

    with db.conectar(ruta_bd or config.RUTA_BD) as conexion:
        filas = conexion.execute(
            "SELECT d.* FROM decisiones d "
            "JOIN (SELECT requisito_id, MAX(id) AS ultimo FROM decisiones "
            "      WHERE expediente_id = ? GROUP BY requisito_id) u "
            "  ON u.ultimo = d.id "
            "WHERE d.expediente_id = ?",
            (expediente_id, expediente_id),
        ).fetchall()
    return {str(fila["requisito_id"]): db.fila_a_dict(fila) or {} for fila in filas}


def contar_por_decision(
    ruta_bd: str | Path | None, expediente_id: str
) -> dict[str, int]:
    """Cantidad de decisiones vigentes por tipo."""

    vigentes = decisiones_vigentes(ruta_bd, expediente_id)
    conteo = {decision: 0 for decision in DECISIONES}
    for registro in vigentes.values():
        decision = str(registro.get("decision") or "")
        if decision in conteo:
            conteo[decision] += 1
    return conteo


def avance_ponderado(
    perfiles: PerfilesEvidencia,
    detalles: list[dict[str, Any]],
) -> dict[str, Any]:
    """Calcula el avance validado sobre el peso total del catálogo.

    ``detalles`` son las filas de ``AnalizadorExpediente.resumen``; se espera
    que incluyan ``peso_pct``, ``decision`` y ``estado_efectivo``.
    """

    peso_total = Decimal(perfiles.peso_total or 0)
    peso_decidido = Decimal(0)
    numerador = Decimal(0)
    for detalle in detalles:
        decision = detalle.get("decision")
        if not decision:
            continue
        peso = Decimal(int(detalle.get("peso_pct") or 0))
        peso_decidido += peso
        numerador += peso * factor_avance(decision, detalle.get("estado_efectivo"))

    avance = (
        redondear_1(numerador / peso_total * Decimal(100)) if peso_total else 0.0
    )
    peso_decidido_pct = (
        redondear_1(peso_decidido / peso_total * Decimal(100)) if peso_total else 0.0
    )
    return {
        "peso_total_pct": perfiles.peso_total,
        "peso_decidido_pct": peso_decidido_pct,
        "avance_pct": avance,
        "formula": "Σ(peso × factor_avance) / peso_total × 100, ROUND_HALF_UP 1 decimal",
    }


class EvaluadorExpediente:
    """Fachada de evaluación: decisión, historial y avance."""

    def __init__(
        self,
        ruta_bd: str | Path | None = None,
        *,
        perfiles: PerfilesEvidencia | None = None,
    ) -> None:
        self.ruta_bd = db.inicializar(ruta_bd or config.RUTA_BD)
        self.perfiles = perfiles or cargar_perfiles()

    def decidir(
        self,
        expediente_id: str,
        requisito_id: str,
        decision: str,
        *,
        actor: str,
        motivo: str,
        estado_final: str | None = None,
        propuesta_id: int | None = None,
    ) -> dict[str, Any]:
        return decidir(
            self.ruta_bd,
            expediente_id,
            requisito_id,
            decision,
            actor=actor,
            motivo=motivo,
            estado_final=estado_final,
            propuesta_id=propuesta_id,
        )

    def historial(
        self, expediente_id: str, requisito_id: str | None = None
    ) -> list[dict[str, Any]]:
        return historial(self.ruta_bd, expediente_id, requisito_id)

    def vigentes(self, expediente_id: str) -> dict[str, dict[str, Any]]:
        return decisiones_vigentes(self.ruta_bd, expediente_id)

    def avance(self, detalles: list[dict[str, Any]]) -> dict[str, Any]:
        return avance_ponderado(self.perfiles, detalles)
