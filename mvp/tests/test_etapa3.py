"""Pruebas del análisis de evidencia e IA (Etapa 3)."""

from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
from openpyxl import load_workbook

from mvp.core import config
from mvp.core.ai_contract import validar_propuesta
from mvp.core.ai_service import ProveedorFallido, ProveedorGuionizado
from mvp.core.analysis import AnalizadorExpediente
from mvp.core.evidence import Evidencia, cargar_perfiles
from mvp.core.integrity import verificar_documento
from mvp.core.pipeline import ProcesadorDocumental

EXPEDIENTE = config.EXPEDIENTE_DEFECTO


# --- Fixtures -------------------------------------------------------------


@pytest.fixture(scope="module")
def servicio(tmp_path_factory: pytest.TempPathFactory, corpus_etapa3: dict):
    base = tmp_path_factory.mktemp("etapa3_db")
    ruta_bd = base / "prueba.db"
    procesador = ProcesadorDocumental(ruta_bd)
    procesador.registrar_expediente(
        EXPEDIENTE,
        "Carretera Central Tramo 2",
        especialidad="Pavimentos",
        version="v3",
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
    return SimpleNamespace(
        procesador=procesador,
        analizador=AnalizadorExpediente(ruta_bd),
        ruta_bd=ruta_bd,
        carpeta_caso=corpus_etapa3["carpeta_caso"],
    )


@pytest.fixture(scope="module")
def evidencia_rq04(servicio):
    return servicio.analizador.recuperar(EXPEDIENTE, "RQ-04")[0]


def _expediente_con_presupuesto(servicio, tmp_path: Path, expediente_id: str):
    copia = tmp_path / f"{expediente_id}.xlsx"
    shutil.copy2(servicio.carpeta_caso / "Presupuesto.xlsx", copia)
    servicio.procesador.registrar_expediente(
        expediente_id, "Validación", especialidad="Pavimentos", actor="prueba"
    )
    servicio.procesador.ingestar_archivo(expediente_id, copia, actor="prueba")
    servicio.analizador.recuperar(expediente_id, "RQ-04")
    return copia


def _propuesta_valida(evidencia) -> dict:
    return {
        "requisito_id": "RQ-04",
        "estado_propuesto": "Cumple",
        "evidencia_encontrada": True,
        "fuente": evidencia.fuente(),
        "cita": evidencia.texto[:70],
        "observacion_preliminar": "Evidencia directa del presupuesto.",
        "requiere_revision_especializada": False,
        "motivo": "El presupuesto contiene partidas y precios unitarios.",
    }


# --- Perfiles y evidencia -------------------------------------------------


def test_perfiles_suman_cien_y_cubren_siete_requisitos() -> None:
    perfiles = cargar_perfiles()
    assert len(perfiles.requisitos) == 7
    assert perfiles.peso_total == 100
    assert perfiles.ids() == [f"RQ-0{indice}" for indice in range(1, 8)]


def test_recuperacion_de_evidencia_por_requisito(servicio) -> None:
    evidencias = servicio.analizador.recuperar(EXPEDIENTE)
    assert set(evidencias) == set(servicio.analizador.perfiles.ids())
    for requisito_id, seleccion in evidencias.items():
        assert seleccion, requisito_id
        for evidencia in seleccion:
            assert evidencia.archivo
            assert evidencia.ubicacion
            assert len(evidencia.sha256_fuente) == 64
            assert evidencia.puntaje > 0


def test_evidencia_solo_de_documentos_validos_y_clasificados(servicio) -> None:
    documentos = {
        documento["id"]: documento
        for documento in servicio.procesador.listar_documentos(EXPEDIENTE)
    }
    for evidencia in servicio.analizador.evidencias(EXPEDIENTE):
        documento = documentos[evidencia["documento_id"]]
        assert documento["estado"] == "VALIDO"
        assert documento["estado_clasificacion"] == "Clasificado"
        assert documento["sha256"] == evidencia["sha256_fuente"]


# --- Contrato JSON --------------------------------------------------------


def test_contrato_acepta_propuesta_coherente(evidencia_rq04) -> None:
    resultado = validar_propuesta(
        _propuesta_valida(evidencia_rq04),
        requisito_id="RQ-04",
        evidencias=[evidencia_rq04],
    )
    assert resultado.valida
    assert resultado.propuesta is not None
    assert resultado.propuesta.estado_propuesto == "Cumple"


def test_contrato_rechaza_hash_y_cita_falsos(evidencia_rq04) -> None:
    propuesta = _propuesta_valida(evidencia_rq04)
    propuesta["fuente"] = dict(propuesta["fuente"])
    propuesta["fuente"]["sha256"] = "0" * 64
    propuesta["cita"] = "Una cita que no existe en el fragmento."
    resultado = validar_propuesta(
        propuesta, requisito_id="RQ-04", evidencias=[evidencia_rq04]
    )
    codigos = {error.codigo for error in resultado.errores}
    assert not resultado.valida
    assert "HASH_NO_COINCIDE" in codigos
    assert "CITA_NO_ENCONTRADA" in codigos


def test_contrato_rechaza_campos_faltantes_y_desconocidos(evidencia_rq04) -> None:
    propuesta = _propuesta_valida(evidencia_rq04)
    propuesta["campo_extra"] = "no permitido"
    del propuesta["motivo"]
    resultado = validar_propuesta(
        propuesta, requisito_id="RQ-04", evidencias=[evidencia_rq04]
    )
    codigos = {error.codigo for error in resultado.errores}
    assert not resultado.valida
    assert "CAMPO_DESCONOCIDO" in codigos
    assert "CAMPO_FALTANTE" in codigos


def test_contrato_exige_fuente_nula_si_no_hay_informacion() -> None:
    propuesta = {
        "requisito_id": "RQ-01",
        "estado_propuesto": "No se encontró información",
        "evidencia_encontrada": False,
        "fuente": None,
        "cita": None,
        "observacion_preliminar": "No se localizó evidencia suficiente.",
        "requiere_revision_especializada": False,
        "motivo": "El expediente no contiene los documentos requeridos.",
    }
    resultado = validar_propuesta(propuesta, requisito_id="RQ-01", evidencias=[])
    assert resultado.valida

    propuesta["fuente"] = {"documento_id": 1}
    invalida = validar_propuesta(propuesta, requisito_id="RQ-01", evidencias=[])
    assert not invalida.valida


def test_contrato_no_permite_conclusion_sin_evidencia() -> None:
    propuesta = {
        "requisito_id": "RQ-04",
        "estado_propuesto": "No cumple",
        "evidencia_encontrada": False,
        "fuente": None,
        "cita": None,
        "observacion_preliminar": "Sin evidencia.",
        "requiere_revision_especializada": False,
        "motivo": "No se encontró el documento.",
    }
    resultado = validar_propuesta(propuesta, requisito_id="RQ-04", evidencias=[])
    assert not resultado.valida
    assert any(error.codigo == "EVIDENCIA_REQUERIDA" for error in resultado.errores)


# --- Reglas y métricas ----------------------------------------------------


def test_reglas_concluyen_cumple_solo_con_prueba_directa(servicio) -> None:
    resultados = {
        resultado.requisito_id: resultado
        for resultado in servicio.analizador.analizar_expediente(EXPEDIENTE)
    }
    assert resultados["RQ-04"].estado == "Cumple"
    assert resultados["RQ-07"].estado == "Cumple"
    assert all(resultado.valida for resultado in resultados.values())


def test_reglas_escalan_cuando_falta_prueba_directa(servicio) -> None:
    resultados = {
        resultado.requisito_id: resultado
        for resultado in servicio.analizador.analizar_expediente(EXPEDIENTE)
    }
    for requisito_id in ("RQ-01", "RQ-02", "RQ-03", "RQ-05", "RQ-06"):
        assert resultados[requisito_id].estado == "Requiere revisión especializada"


def test_control_sin_documentos_no_es_no_cumple(servicio) -> None:
    expediente = "EXP-PRUEBA-CONTROL"
    servicio.procesador.registrar_expediente(expediente, "Control", actor="prueba")
    resultado = servicio.analizador.analizar_requisito(expediente, "RQ-01")
    assert resultado.estado == "No se encontró información"
    assert resultado.propuesta is not None
    assert resultado.propuesta["fuente"] is None


def test_metricas_separan_cobertura_de_cumplimiento(servicio) -> None:
    resumen = servicio.analizador.resumen(EXPEDIENTE)
    assert resumen["cobertura_revision_pct"] == 100.0
    assert resumen["cumplimiento_pct"] is not None
    assert resumen["cumple"] == 2
    assert resumen["cumple"] + resumen["parcial"] + resumen["no_cumple"] == 2


# --- Reintentos y contingencia -------------------------------------------


def test_reintento_acepta_segunda_respuesta_valida(
    servicio, tmp_path: Path
) -> None:
    expediente = "EXP-PRUEBA-REINTENTO"
    _expediente_con_presupuesto(servicio, tmp_path, expediente)
    registros = servicio.analizador.evidencias(expediente, "RQ-04")
    evidencia = next(item for item in registros if item["archivo"].endswith(".xlsx"))
    objeto = Evidencia(
        expediente_id=expediente,
        requisito_id="RQ-04",
        documento_id=evidencia["documento_id"],
        fragmento_orden=evidencia["fragmento_orden"],
        archivo=evidencia["archivo"],
        tipo_documental=evidencia["tipo_documental"],
        ubicacion=evidencia["ubicacion"],
        sha256_fuente=evidencia["sha256_fuente"],
        texto=evidencia["texto"],
        puntaje=evidencia["puntaje"],
        terminos=evidencia["terminos"],
    )
    invalida = _propuesta_valida(objeto)
    invalida["cita"] = "Cita inventada."
    proveedor = ProveedorGuionizado([invalida, _propuesta_valida(objeto)])
    resultado = servicio.analizador.analizar_requisito(
        expediente, "RQ-04", proveedor=proveedor, recuperar=False
    )
    assert resultado.valida
    assert resultado.intentos == 2


def test_rechazo_agota_intentos_y_activa_contingencia(
    servicio, evidencia_rq04, tmp_path: Path
) -> None:
    expediente = "EXP-PRUEBA-RECHAZO"
    _expediente_con_presupuesto(servicio, tmp_path, expediente)
    propuesta = _propuesta_valida(evidencia_rq04)
    propuesta["cita"] = "Cita inventada."
    proveedor = ProveedorGuionizado([propuesta, propuesta, propuesta])
    resultado = servicio.analizador.analizar_requisito(
        expediente, "RQ-04", proveedor=proveedor, recuperar=False
    )
    assert not resultado.valida
    assert resultado.contingencia
    assert resultado.intentos == 3
    ultima = servicio.analizador.ultima_propuesta(
        expediente, "RQ-04", solo_valida=False
    )
    assert ultima is not None and not ultima["valida"]


def test_contingencia_permite_evaluacion_manual(
    servicio, tmp_path: Path
) -> None:
    expediente = "EXP-PRUEBA-CONTINGENCIA"
    _expediente_con_presupuesto(servicio, tmp_path, expediente)
    resultado = servicio.analizador.analizar_requisito(
        expediente, "RQ-04", proveedor=ProveedorFallido()
    )
    assert resultado.contingencia
    assert resultado.intentos == 3
    manual = servicio.analizador.registrar_evaluacion_manual(
        expediente,
        "RQ-04",
        "Requiere revisión especializada",
        "El servicio de IA no está disponible.",
        actor="Lucía Ramos",
    )
    assert manual["estado"] == "Requiere revisión especializada"
    resumen = servicio.analizador.resumen(expediente)
    assert resumen["con_evaluacion_manual"] == 1


# --- Integridad -----------------------------------------------------------


def test_fuente_modificada_bloquea_la_conclusion(
    servicio, tmp_path: Path
) -> None:
    expediente = "EXP-PRUEBA-INTEGRIDAD"
    copia = _expediente_con_presupuesto(servicio, tmp_path, expediente)
    previo = servicio.analizador.analizar_requisito(expediente, "RQ-04")
    assert previo.estado == "Cumple"

    libro = load_workbook(copia)
    libro["Resumen"]["A1"] = "PRESUPUESTO MODIFICADO"
    libro.save(copia)

    documento_id = servicio.procesador.listar_documentos(expediente)[0]["id"]
    verificacion = verificar_documento(servicio.ruta_bd, documento_id)
    assert verificacion["estado"] == "FUENTE_MODIFICADA"
    assert verificacion["evidencias_afectadas"] >= 1

    posterior = servicio.analizador.analizar_requisito(expediente, "RQ-04")
    assert posterior.estado == "Requiere revisión especializada"
    assert posterior.proveedor == "integridad"


def test_evaluacion_manual_invalida_se_rechaza(servicio) -> None:
    with pytest.raises(ValueError):
        servicio.analizador.registrar_evaluacion_manual(
            EXPEDIENTE,
            "RQ-01",
            "Estado inventado",
            "Motivo",
            actor="Lucía Ramos",
        )
