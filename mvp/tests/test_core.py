"""Pruebas del procesamiento documental (Etapa 2)."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from mvp.core import config
from mvp.core.classifier import clasificar
from mvp.core.extractors import ErrorExtraccion, extraer
from mvp.core.hashing import hash_archivo, hash_bytes
from mvp.core.pipeline import ProcesadorDocumental

EXPEDIENTE = config.EXPEDIENTE_DEFECTO


@pytest.fixture()
def procesador(tmp_path: Path) -> ProcesadorDocumental:
    servicio = ProcesadorDocumental(tmp_path / "prueba.db")
    servicio.registrar_expediente(
        EXPEDIENTE,
        "Carretera Central Tramo 2",
        especialidad="Pavimentos",
        version="v3",
        actor="prueba",
    )
    return servicio


# --- Integridad ----------------------------------------------------------


def test_hash_archivo_es_estable(corpus: dict) -> None:
    ruta = corpus["caso"]["TDR_Carretera_Central_v3.pdf"]
    primero = hash_archivo(ruta)
    segundo = hash_archivo(ruta)
    assert primero == segundo
    assert len(primero) == 64
    assert primero != hash_bytes(b"otro contenido")


# --- Extracción ----------------------------------------------------------


def test_extraer_pdf_con_texto(corpus: dict) -> None:
    extraccion = extraer(corpus["caso"]["TDR_Carretera_Central_v3.pdf"])
    assert extraccion.formato == "PDF"
    assert extraccion.texto_recuperable == "si"
    assert extraccion.paginas and extraccion.paginas >= 1
    assert extraccion.caracteres > 500
    assert all(fragmento.ubicacion.startswith("p. ") for fragmento in extraccion.fragmentos)
    assert "términos de referencia" in extraccion.texto_completo.lower()


def test_extraer_pdf_parcial_por_paginas_sin_texto(corpus: dict) -> None:
    extraccion = extraer(corpus["caso"]["Planos_PL-01_PL-08.pdf"])
    assert extraccion.texto_recuperable == "parcial"
    assert extraccion.paginas == 8
    assert extraccion.metadatos["paginas_sin_texto"] == [3, 4, 5]
    assert any("OCR" in aviso for aviso in extraccion.advertencias)


def test_extraer_docx_con_parrafos_y_tabla(corpus: dict) -> None:
    extraccion = extraer(corpus["caso"]["Memoria_Calculo_Pavimentos.docx"])
    assert extraccion.formato == "DOCX"
    assert extraccion.texto_recuperable == "si"
    assert any(fragmento.tipo == "parrafo" for fragmento in extraccion.fragmentos)
    assert any(fragmento.tipo == "tabla" for fragmento in extraccion.fragmentos)
    assert any("párr." in fragmento.ubicacion for fragmento in extraccion.fragmentos)


def test_extraer_xlsx_con_celda_verificable(corpus: dict) -> None:
    extraccion = extraer(corpus["caso"]["Presupuesto.xlsx"])
    assert extraccion.formato == "XLSX"
    ubicaciones = [fragmento.ubicacion for fragmento in extraccion.fragmentos]
    assert "Hoja:Resumen!A18:F18" in ubicaciones
    total = next(f for f in extraccion.fragmentos if f.ubicacion == "Hoja:Resumen!A18:F18")
    assert "F18=" in total.texto
    assert "fórmula" in total.texto


# --- Rechazos ------------------------------------------------------------


def test_rechazo_pdf_escaneado(corpus: dict) -> None:
    with pytest.raises(ErrorExtraccion) as error:
        extraer(corpus["borde"]["PDF_Escaneado.pdf"])
    assert error.value.codigo == "PDF_ESCANEADO"


def test_rechazo_pdf_protegido(corpus: dict) -> None:
    with pytest.raises(ErrorExtraccion) as error:
        extraer(corpus["borde"]["PDF_Protegido.pdf"])
    assert error.value.codigo == "PDF_PROTEGIDO"


def test_rechazo_pdf_corrupto(corpus: dict) -> None:
    with pytest.raises(ErrorExtraccion) as error:
        extraer(corpus["borde"]["PDF_Corrupto.pdf"])
    assert error.value.codigo == "ARCHIVO_DANADO"


def test_rechazo_formato_no_soportado(corpus: dict) -> None:
    with pytest.raises(ErrorExtraccion) as error:
        extraer(corpus["borde"]["notas.txt"])
    assert error.value.codigo == "FORMATO_NO_SOPORTADO"


# --- Clasificación -------------------------------------------------------


def test_clasificacion_tdr_alta_confianza(corpus: dict) -> None:
    extraccion = extraer(corpus["caso"]["TDR_Carretera_Central_v3.pdf"])
    resultado = clasificar("TDR_Carretera_Central_v3.pdf", extraccion)
    assert resultado.tipo_documental == "TDR / Bases"
    assert resultado.componente == "TDR"
    assert resultado.confianza >= 70
    assert resultado.estado == "Clasificado"


def test_clasificacion_ambigua_exige_correccion(corpus: dict) -> None:
    extraccion = extraer(corpus["caso"]["EETT_General_v2.docx"])
    resultado = clasificar("EETT_General_v2.docx", extraccion)
    assert resultado.confianza < config.UMBRAL_CONFIANZA
    assert resultado.estado == "Sin clasificar"
    assert resultado.tipo_documental == "Especificaciones técnicas"


def test_documento_sin_senales_no_reconocido(corpus: dict) -> None:
    extraccion = extraer(corpus["borde"]["Documento_General.pdf"])
    resultado = clasificar("Documento_General.pdf", extraccion)
    assert resultado.tipo_documental == "No reconocido"
    assert resultado.confianza == 0
    assert resultado.estado == "Sin clasificar"


def test_umbral_de_confianza_es_configurable(corpus: dict) -> None:
    extraccion = extraer(corpus["caso"]["EETT_General_v2.docx"])
    resultado = clasificar("EETT_General_v2.docx", extraccion, umbral=50)
    assert resultado.estado == "Clasificado"


# --- Pipeline ------------------------------------------------------------


def test_ingesta_del_caso_completo(procesador: ProcesadorDocumental, corpus: dict) -> None:
    resultados = procesador.ingestar_carpeta(EXPEDIENTE, corpus["carpeta_caso"], actor="prueba")
    assert len(resultados) == 6
    assert all(resultado.ok for resultado in resultados)
    assert all(resultado.sha256 and len(resultado.sha256) == 64 for resultado in resultados)
    assert all(resultado.fragmentos > 0 for resultado in resultados)

    resumen = procesador.resumen_procesamiento(EXPEDIENTE)
    assert resumen["documentos_total"] == 6
    assert resumen["validos"] == 6
    assert resumen["rechazados"] == 0
    assert resumen["clasificados"] == 5
    assert resumen["sin_clasificar"] == 1
    assert resumen["texto_parcial"] == 1
    assert resumen["fragmentos_total"] > 40


def test_segunda_carga_reutiliza_cache(procesador: ProcesadorDocumental, corpus: dict) -> None:
    primera = procesador.ingestar_carpeta(EXPEDIENTE, corpus["carpeta_caso"], actor="prueba")
    hashes = {r.nombre_archivo: r.sha256 for r in primera}
    assert not any(r.cache_hit for r in primera)

    segunda = procesador.ingestar_carpeta(EXPEDIENTE, corpus["carpeta_caso"], actor="prueba")
    assert all(r.cache_hit for r in segunda)
    assert {r.nombre_archivo: r.sha256 for r in segunda} == hashes

    resumen = procesador.resumen_procesamiento(EXPEDIENTE)
    assert resumen["cache_hits"] == 6
    assert resumen["documentos_total"] == 6


def test_correccion_humana_sobrevive_a_la_cache(
    procesador: ProcesadorDocumental, corpus: dict
) -> None:
    procesador.ingestar_carpeta(EXPEDIENTE, corpus["carpeta_caso"], actor="prueba")
    eett = next(
        d
        for d in procesador.listar_documentos(EXPEDIENTE)
        if d["nombre_archivo"] == "EETT_General_v2.docx"
    )
    assert eett["estado_clasificacion"] == "Sin clasificar"

    corregido = procesador.corregir_clasificacion(
        eett["id"],
        "Especificaciones técnicas",
        "EETT",
        actor="Lucía Ramos",
        motivo="El contenido corresponde a EETT aunque el archivo es genérico.",
    )
    assert corregido["confianza"] == 100
    assert corregido["clasificacion_origen"] == "correccion_humana"
    assert corregido["estado_clasificacion"] == "Clasificado"

    segunda = procesador.ingestar_carpeta(EXPEDIENTE, corpus["carpeta_caso"], actor="prueba")
    eett_recargado = next(r for r in segunda if r.nombre_archivo == "EETT_General_v2.docx")
    assert eett_recargado.cache_hit is True
    assert eett_recargado.clasificacion is not None
    assert eett_recargado.clasificacion.tipo_documental == "Especificaciones técnicas"
    assert eett_recargado.clasificacion.origen == "correccion_humana"
    assert eett_recargado.clasificacion.confianza == 100

    documento = procesador.obtener_documento(eett["id"])
    assert documento is not None
    assert documento["clasificacion_origen"] == "correccion_humana"


def test_casos_borde_se_rechazan_con_motivo(
    procesador: ProcesadorDocumental, corpus: dict
) -> None:
    esperados = {
        "PDF_Escaneado.pdf": "PDF_ESCANEADO",
        "PDF_Protegido.pdf": "PDF_PROTEGIDO",
        "PDF_Corrupto.pdf": "ARCHIVO_DANADO",
        "notas.txt": "FORMATO_NO_SOPORTADO",
    }
    for nombre, motivo in esperados.items():
        resultado = procesador.ingestar_archivo(
            EXPEDIENTE, corpus["borde"][nombre], actor="prueba"
        )
        assert resultado.ok is False
        assert resultado.motivo_rechazo == motivo
        assert resultado.estado == "RECHAZADO"
        assert resultado.documento_id is not None
        documento = procesador.obtener_documento(resultado.documento_id)
        assert documento is not None
        assert documento["fragmentos"] == 0
        assert documento["estado"] == "RECHAZADO"

    valido = procesador.ingestar_archivo(
        EXPEDIENTE, corpus["borde"]["Documento_General.pdf"], actor="prueba"
    )
    assert valido.ok is True
    assert valido.texto_recuperable == "si"
    assert valido.clasificacion is not None
    assert valido.clasificacion.estado == "Sin clasificar"


def test_auditoria_registra_acciones(
    procesador: ProcesadorDocumental, corpus: dict
) -> None:
    procesador.ingestar_carpeta(EXPEDIENTE, corpus["carpeta_caso"], actor="prueba")
    acciones = {registro["accion"] for registro in procesador.listar_auditoria(100)}
    assert "DOCUMENTO_PROCESADO" in acciones
    assert "INGESTA_CARPETA" in acciones
    assert "EXPEDIENTE_REGISTRADO" in acciones


def test_exportar_inventario_csv(
    procesador: ProcesadorDocumental, corpus: dict, tmp_path: Path
) -> None:
    procesador.ingestar_carpeta(EXPEDIENTE, corpus["carpeta_caso"], actor="prueba")
    destino = procesador.exportar_inventario_csv(EXPEDIENTE, tmp_path / "inventario.csv")
    assert destino.exists()
    with destino.open(encoding="utf-8") as manejador:
        filas = list(csv.DictReader(manejador))
    assert len(filas) == 6
    assert all(len(fila["sha256"]) == 64 for fila in filas)
    assert {fila["estado"] for fila in filas} == {"VALIDO"}


def test_documento_rechazado_no_genera_fragmentos(
    procesador: ProcesadorDocumental, corpus: dict
) -> None:
    resultado = procesador.ingestar_archivo(
        EXPEDIENTE, corpus["borde"]["PDF_Escaneado.pdf"], actor="prueba"
    )
    assert resultado.documento_id is not None
    assert procesador.fragmentos_de(resultado.documento_id) == []
