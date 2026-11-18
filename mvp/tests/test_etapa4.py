"""Pruebas de evaluación, trazabilidad, persistencia y avance (Etapa 4)."""

from __future__ import annotations

import shutil
import sqlite3
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from mvp.core import config, db
from mvp.core.analysis import AnalizadorExpediente
from mvp.core.evaluation import (
    DECISIONES,
    ESTADO_SIN_INFORMACION,
    EvaluadorExpediente,
    avance_ponderado,
    factor_avance,
    historial,
    redondear_1,
)
from mvp.core.pipeline import ProcesadorDocumental

EXPEDIENTE = config.EXPEDIENTE_DEFECTO
ACTOR = "Lucía Ramos"


# --- Fixtures -------------------------------------------------------------


@pytest.fixture(scope="module")
def base(tmp_path_factory: pytest.TempPathFactory, corpus_etapa3: dict):
    """Analiza el caso una sola vez y sirve como plantilla para cada prueba."""

    ruta_bd = tmp_path_factory.mktemp("etapa4_base") / "base.db"
    procesador = ProcesadorDocumental(ruta_bd)
    procesador.registrar_expediente(
        EXPEDIENTE,
        "Carretera Central Tramo 2",
        especialidad="Pavimentos",
        version="v4",
        actor="prueba",
    )
    procesador.ingestar_carpeta(
        EXPEDIENTE, corpus_etapa3["carpeta_caso"], actor="prueba"
    )
    eett = next(
        documento
        for documento in procesador.listar_documentos(EXPEDIENTE)
        if documento["nombre_archivo"] == "EETT_General_v2.docx"
    )
    procesador.corregir_clasificacion(
        eett["id"],
        "Especificaciones técnicas",
        "EETT",
        actor="prueba",
        motivo="Corrección necesaria para usar la evidencia.",
    )
    analizador = AnalizadorExpediente(ruta_bd)
    analizador.recuperar(EXPEDIENTE)
    analizador.analizar_expediente(EXPEDIENTE)
    return SimpleNamespace(ruta_bd=ruta_bd, analizador=analizador)


@pytest.fixture()
def servicio(base, tmp_path: Path):
    """Copia la base analizada para aislar las decisiones de cada prueba."""

    ruta_bd = tmp_path / "prueba.db"
    shutil.copy2(base.ruta_bd, ruta_bd)
    return SimpleNamespace(
        ruta_bd=ruta_bd,
        analizador=AnalizadorExpediente(ruta_bd),
        evaluador=EvaluadorExpediente(ruta_bd),
    )


# --- Catálogo y reglas ----------------------------------------------------


def test_catalogo_tiene_los_cinco_estados() -> None:
    assert len(config.ESTADOS_REQUISITO) == 5
    assert "No se encontró información" in config.ESTADOS_REQUISITO
    assert "Requiere revisión especializada" in config.ESTADOS_REQUISITO
    assert set(DECISIONES) == {"aceptar", "modificar", "descartar"}


def test_redondeo_half_up_y_factores() -> None:
    assert redondear_1(Decimal("88.65")) == 88.7
    assert redondear_1(Decimal("39.04")) == 39.0
    assert factor_avance("aceptar", "Cumple") == Decimal("1.0")
    assert factor_avance("modificar", "Cumple parcialmente") == Decimal("0.5")
    assert factor_avance("aceptar", "No se encontró información") == Decimal("0.0")
    assert factor_avance("descartar", "Cumple") == Decimal("0.0")
    assert factor_avance(None, "Cumple") == Decimal("0.0")


def test_aceptar_conserva_propuesta_y_cambia_contadores(servicio) -> None:
    antes = servicio.analizador.resumen(EXPEDIENTE)
    assert antes["avance_pct"] == 0.0
    assert antes["decisiones_registradas"] == 0

    decision = servicio.evaluador.decidir(
        EXPEDIENTE,
        "RQ-04",
        "aceptar",
        actor=ACTOR,
        motivo="Fuente y cita verificadas por el especialista.",
    )
    assert decision["estado_propuesto"] == "Cumple"
    assert decision["estado_final"] == "Cumple"
    assert decision["version_kb"] == "v4"

    despues = servicio.analizador.resumen(EXPEDIENTE)
    assert despues["decisiones_registradas"] == 1
    assert despues["aceptadas"] == 1
    assert despues["avance_pct"] == 21.0
    assert despues["peso_decidido_pct"] == 21.0
    detalle = next(
        item for item in despues["requisitos"] if item["requisito_id"] == "RQ-04"
    )
    assert detalle["origen"] == "decision"
    assert detalle["estado_efectivo"] == "Cumple"
    assert detalle["estado_propuesto"] == "Cumple"


def test_modificar_exige_estado_distinto_y_valido(servicio) -> None:
    with pytest.raises(ValueError):
        servicio.evaluador.decidir(
            EXPEDIENTE,
            "RQ-06",
            "modificar",
            estado_final="Requiere revisión especializada",
            actor=ACTOR,
            motivo="Sin cambio real.",
        )
    with pytest.raises(ValueError):
        servicio.evaluador.decidir(
            EXPEDIENTE,
            "RQ-06",
            "modificar",
            estado_final="Estado inventado",
            actor=ACTOR,
            motivo="Estado fuera del catálogo.",
        )

    servicio.evaluador.decidir(
        EXPEDIENTE,
        "RQ-06",
        "modificar",
        estado_final="Cumple parcialmente",
        actor=ACTOR,
        motivo="La curva S no cubre dos partidas del plazo.",
    )
    resumen = servicio.analizador.resumen(EXPEDIENTE)
    assert resumen["parcial"] == 1
    assert resumen["avance_pct"] == 5.0
    assert resumen["cumplimiento_pct"] == 88.6
    assert resumen["modificadas"] == 1


def test_descartar_no_convierte_en_no_cumple(servicio) -> None:
    decision = servicio.evaluador.decidir(
        EXPEDIENTE,
        "RQ-05",
        "descartar",
        actor=ACTOR,
        motivo="Los planos no permiten verificar la coherencia con los metrados.",
    )
    assert decision["estado_propuesto"] == "Requiere revisión especializada"
    assert decision["estado_final"] == ESTADO_SIN_INFORMACION

    resumen = servicio.analizador.resumen(EXPEDIENTE)
    assert resumen["sin_informacion"] == 1
    assert resumen["no_cumple"] == 0
    assert resumen["descartadas"] == 1
    assert resumen["avance_pct"] == 0.0


def test_motivo_y_responsable_son_obligatorios(servicio) -> None:
    with pytest.raises(ValueError):
        servicio.evaluador.decidir(
            EXPEDIENTE, "RQ-04", "aceptar", actor="", motivo="Motivo"
        )
    with pytest.raises(ValueError):
        servicio.evaluador.decidir(
            EXPEDIENTE, "RQ-04", "aceptar", actor=ACTOR, motivo="   "
        )
    with pytest.raises(ValueError):
        servicio.evaluador.decidir(
            EXPEDIENTE, "RQ-04", "aprobar", actor=ACTOR, motivo="Motivo"
        )


def test_no_hay_propuesta_no_se_puede_decidir(servicio) -> None:
    expediente = "EXP-PRUEBA-SIN-PROPUESTA"
    servicio.analizador.procesador.registrar_expediente(
        expediente, "Sin propuestas", actor="prueba"
    )
    with pytest.raises(ValueError):
        servicio.evaluador.decidir(
            expediente, "RQ-01", "aceptar", actor=ACTOR, motivo="Sin propuesta."
        )


def test_fuente_modificada_bloquea_la_decision(servicio) -> None:
    with db.conectar(servicio.ruta_bd) as conexion:
        conexion.execute(
            "UPDATE propuestas_ia SET integridad = 'FUENTE_MODIFICADA' "
            "WHERE expediente_id = ? AND requisito_id = 'RQ-04' AND valida = 1",
            (EXPEDIENTE,),
        )
    with pytest.raises(ValueError):
        servicio.evaluador.decidir(
            EXPEDIENTE,
            "RQ-04",
            "aceptar",
            actor=ACTOR,
            motivo="La fuente cambió.",
        )


# --- Historial y persistencia --------------------------------------------


def test_historial_es_acumulativo_y_solo_una_vigente(servicio) -> None:
    servicio.evaluador.decidir(
        EXPEDIENTE, "RQ-04", "aceptar", actor=ACTOR, motivo="Aceptación inicial."
    )
    servicio.evaluador.decidir(
        EXPEDIENTE,
        "RQ-04",
        "modificar",
        estado_final="Cumple parcialmente",
        actor=ACTOR,
        motivo="Revisión intermedia.",
    )
    servicio.evaluador.decidir(
        EXPEDIENTE, "RQ-04", "aceptar", actor=ACTOR, motivo="Aceptación final."
    )

    registros = historial(servicio.ruta_bd, EXPEDIENTE, "RQ-04")
    assert len(registros) == 3
    assert [registro["es_vigente"] for registro in registros] == [True, False, False]
    assert all(registro["estado_propuesto"] == "Cumple" for registro in registros)
    assert registros[0]["estado_final"] == "Cumple"
    assert registros[1]["estado_final"] == "Cumple parcialmente"
    assert registros[0]["archivo"] == "Presupuesto.xlsx"
    assert registros[0]["motivo"] == "Aceptación final."

    resumen = servicio.analizador.resumen(EXPEDIENTE)
    detalle = next(
        item for item in resumen["requisitos"] if item["requisito_id"] == "RQ-04"
    )
    assert detalle["decision"] == "aceptar"
    assert detalle["decision_actor"] == ACTOR
    assert resumen["decisiones_registradas"] == 1


def test_persistencia_en_instancia_nueva(servicio) -> None:
    servicio.evaluador.decidir(
        EXPEDIENTE,
        "RQ-07",
        "aceptar",
        actor=ACTOR,
        motivo="PMA vigente y verificable.",
    )
    resumen = servicio.analizador.resumen(EXPEDIENTE)
    historial_original = servicio.evaluador.historial(EXPEDIENTE)

    analizador_nuevo = AnalizadorExpediente(servicio.ruta_bd)
    evaluador_nuevo = EvaluadorExpediente(servicio.ruta_bd)
    resumen_nuevo = analizador_nuevo.resumen(EXPEDIENTE)

    assert resumen_nuevo["avance_pct"] == resumen["avance_pct"] == 13.0
    assert resumen_nuevo["decisiones_registradas"] == 1
    assert evaluador_nuevo.historial(EXPEDIENTE) == historial_original
    assert evaluador_nuevo.vigentes(EXPEDIENTE)["RQ-07"]["actor"] == ACTOR


def test_reejecucion_no_duplica_y_conserva_decisiones(servicio) -> None:
    servicio.evaluador.decidir(
        EXPEDIENTE,
        "RQ-04",
        "aceptar",
        actor=ACTOR,
        motivo="Aceptación antes de reejecutar.",
    )
    propuestas_antes = servicio.analizador.propuestas(EXPEDIENTE, limite=1000)
    decisiones_antes = servicio.evaluador.vigentes(EXPEDIENTE)

    servicio.analizador.analizar_expediente(EXPEDIENTE)

    propuestas_despues = servicio.analizador.propuestas(EXPEDIENTE, limite=1000)
    assert len(propuestas_despues) == len(propuestas_antes)
    assert servicio.evaluador.vigentes(EXPEDIENTE) == decisiones_antes
    assert servicio.analizador.resumen(EXPEDIENTE)["avance_pct"] == 21.0

    with db.conectar(servicio.ruta_bd) as conexion:
        duplicadas = conexion.execute(
            "SELECT COUNT(*) FROM ("
            "SELECT expediente_id, requisito_id, huella, valida, COUNT(*) AS n "
            "FROM propuestas_ia WHERE huella IS NOT NULL "
            "GROUP BY expediente_id, requisito_id, huella, valida HAVING n > 1)"
        ).fetchone()[0]
        sin_huella = conexion.execute(
            "SELECT COUNT(*) FROM propuestas_ia WHERE huella IS NULL"
        ).fetchone()[0]
    assert duplicadas == 0
    assert sin_huella == 0


def test_ausencia_de_evidencia_se_decide_sin_marcar_no_cumple(servicio) -> None:
    expediente = "EXP-PRUEBA-AUSENCIA"
    servicio.analizador.procesador.registrar_expediente(
        expediente, "Control sin documentos", actor="prueba"
    )
    resultado = servicio.analizador.analizar_requisito(expediente, "RQ-01")
    assert resultado.estado == "No se encontró información"

    decision = servicio.evaluador.decidir(
        expediente,
        "RQ-01",
        "aceptar",
        actor=ACTOR,
        motivo="El expediente no contiene documentos.",
    )
    assert decision["estado_final"] == "No se encontró información"

    resumen = servicio.analizador.resumen(expediente)
    assert resumen["sin_informacion"] == 1
    assert resumen["no_cumple"] == 0
    assert resumen["avance_pct"] == 0.0


# --- Avance y migración ---------------------------------------------------


def test_avance_ponderado_usa_peso_total(servicio) -> None:
    detalles = [
        {"peso_pct": 21, "decision": "aceptar", "estado_efectivo": "Cumple"},
        {"peso_pct": 10, "decision": "modificar", "estado_efectivo": "Cumple parcialmente"},
        {"peso_pct": 14, "decision": "descartar", "estado_efectivo": "Cumple"},
        {"peso_pct": 17, "decision": None, "estado_efectivo": "Cumple"},
    ]
    calculo = avance_ponderado(servicio.analizador.perfiles, detalles)
    assert calculo["peso_decidido_pct"] == 45.0
    assert calculo["avance_pct"] == 26.0


def test_migracion_agrega_huella_a_una_base_anterior(tmp_path: Path) -> None:
    ruta = tmp_path / "base_etapa3.db"
    conexion = sqlite3.connect(ruta)
    conexion.execute(
        "CREATE TABLE propuestas_ia ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, expediente_id TEXT, "
        "requisito_id TEXT, integridad TEXT)"
    )
    conexion.commit()
    conexion.close()

    db.inicializar(ruta)

    with db.conectar(ruta) as conexion:
        columnas = {
            fila["name"]
            for fila in conexion.execute("PRAGMA table_info(propuestas_ia)")
        }
        indices = {
            fila["name"] for fila in conexion.execute("PRAGMA index_list(propuestas_ia)")
        }
    assert "huella" in columnas
    assert "idx_propuestas_huella" in indices
