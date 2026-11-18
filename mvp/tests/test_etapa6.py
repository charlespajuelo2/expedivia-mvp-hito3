"""Pruebas de aceptación de la entrega del Hito 3 (Etapa 6).

Verifican los artefactos producidos por ``python -m mvp.scripts.ejecutar_etapa6``:
casos, métricas, base final, exportaciones, PPT, video y documentación.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

from mvp.core import config
from mvp.core.evaluation import EvaluadorExpediente
from mvp.core.pipeline import ProcesadorDocumental

EXPEDIENTE = config.EXPEDIENTE_DEFECTO
EVIDENCIA = config.DIR_EVIDENCIA_ETAPA6
ENTREGA = config.DIR_ETAPA6 / "entrega"
HOJAS = [
    "Resumen",
    "Requisitos",
    "Decisiones",
    "Propuestas",
    "Evidencias",
    "Documentos",
    "Auditoría",
]
SECCIONES = [
    "1. Resumen ejecutivo",
    "2. Resultados por requisito",
    "3. Observaciones y fuentes",
    "4. Historial de decisiones",
    "5. Alcance y limitaciones",
]
SECCIONES_PPT = {
    "1 · PROBLEMA Y USUARIO",
    "2 · SOLUCIÓN",
    "3 · ARQUITECTURA",
    "4 · DEMOSTRACIÓN",
    "5 · RESULTADOS",
    "6 · PRUEBAS Y MÉTRICAS",
    "7 · SEGURIDAD Y LÍMITES",
    "8 · APRENDIZAJES",
    "9 · CIERRE",
}


def _json(nombre: str) -> object:
    return json.loads((EVIDENCIA / nombre).read_text(encoding="utf-8"))


# --- Evidencia y base -----------------------------------------------------


def test_reportes_de_etapa6_existen() -> None:
    esperados = [
        "00_entorno.json",
        "01_flujo_extremo_a_extremo.md",
        "02_casos_prueba.md",
        "02_casos_prueba.json",
        "03_errores_correcciones.md",
        "04_metricas_linea_base.md",
        "05_revision_tecnica.md",
        "06_checklist_entrega.md",
        "07_guion_video.md",
        "08_acta_ensayo.md",
        "09_ficha_tecnica.md",
        "10_metricas.json",
        "mvp_etapa6.db",
    ]
    for nombre in esperados:
        ruta = EVIDENCIA / nombre
        assert ruta.exists(), nombre
        assert ruta.stat().st_size > 0, nombre


def test_caso_principal_queda_con_ocho_documentos() -> None:
    procesador = ProcesadorDocumental(EVIDENCIA / "mvp_etapa6.db")
    documentos = procesador.listar_documentos(EXPEDIENTE)
    validos = [d for d in documentos if d["estado"] == "VALIDO"]
    assert len(documentos) == 8
    assert len(validos) == 8
    assert all(len(d["sha256"]) == 64 for d in validos)


def test_decisiones_e_historial_del_caso() -> None:
    evaluador = EvaluadorExpediente(EVIDENCIA / "mvp_etapa6.db")
    assert len(evaluador.vigentes(EXPEDIENTE)) == 4
    historial = evaluador.historial(EXPEDIENTE)
    assert len(historial) == 6
    assert sum(1 for registro in historial if registro["requisito_id"] == "RQ-04") == 3
    assert sum(1 for registro in historial if registro["es_vigente"]) == 4


# --- Casos y métricas -----------------------------------------------------


def test_dieciséis_casos_mapeados_a_ca_y_aprobados() -> None:
    casos = _json("02_casos_prueba.json")
    assert isinstance(casos, list)
    assert len(casos) == 16
    assert {caso["id"] for caso in casos} == {f"CP-{n:02d}" for n in range(1, 17)}
    assert all(caso["ca"].startswith("CA-") for caso in casos)
    assert all(caso["estado"] == "PASA" for caso in casos)
    assert all(caso["esperado"] and caso["obtenido"] for caso in casos)


def test_metricas_del_caso() -> None:
    metricas = _json("10_metricas.json")
    caso = metricas["caso"]
    assert caso["cobertura_revision_pct"] == 100.0
    assert caso["peso_decidido_pct"] == 58.0
    assert caso["avance_pct"] == 39.0
    assert caso["cumplimiento_pct"] == 88.6
    assert caso["decisiones_registradas"] == 4
    assert caso["no_cumple"] == 0
    assert caso["sin_informacion"] == 1
    assert metricas["total_casos"] == 16
    assert metricas["aprobados"] == 16
    assert metricas["linea_base"]["minutos"] == 260
    assert metricas["linea_base"]["minutos_revision_humana"] == 90


def test_linea_base_declara_supuestos_y_revision_humana() -> None:
    reporte = (EVIDENCIA / "04_metricas_linea_base.md").read_text(encoding="utf-8")
    assert "estimación declarada" in reporte
    assert "90 min" in reporte
    assert "sigue siendo humana" in reporte
    assert "99." in reporte


# --- Exportaciones --------------------------------------------------------


def test_excel_generado_desde_sqlite() -> None:
    ruta = EVIDENCIA / "exportaciones" / "informe_EXP-2024-089.xlsx"
    assert ruta.exists()
    libro = load_workbook(ruta, data_only=True)
    assert libro.sheetnames == HOJAS
    assert libro["Requisitos"].max_row - 1 == 7
    assert libro["Decisiones"].max_row - 1 == 6
    valores = [
        str(celda.value)
        for fila in libro["Resumen"].iter_rows()
        for celda in fila
        if celda.value is not None
    ]
    assert any("39.0%" in valor for valor in valores)


def test_word_generado_desde_sqlite() -> None:
    ruta = EVIDENCIA / "exportaciones" / "informe_EXP-2024-089.docx"
    assert ruta.exists()
    documento = Document(ruta)
    encabezados = [
        parrafo.text
        for parrafo in documento.paragraphs
        if parrafo.style.name == "Heading 1"
    ]
    assert encabezados == SECCIONES
    assert len(documento.tables) >= 3
    texto = "\n".join(
        celda.text
        for tabla in documento.tables
        for fila in tabla.rows
        for celda in fila.cells
    )
    assert "39.0%" in texto


# --- Presentación, video y documentación ---------------------------------


def test_ppt_tiene_catorce_diapositivas_y_nueve_secciones() -> None:
    ruta = ENTREGA / "PPT_Expedivia_Hito3.pptx"
    assert ruta.exists()
    prs = Presentation(ruta)
    assert len(prs.slides) == 14
    etiquetas = set()
    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for parrafo in shape.text_frame.paragraphs:
                texto = parrafo.text.strip()
                if texto in SECCIONES_PPT:
                    etiquetas.add(texto)
    assert etiquetas == SECCIONES_PPT
    assert (ENTREGA / "PPT_Expedivia_Hito3.pdf").stat().st_size > 100_000


def test_video_y_capturas_existen() -> None:
    video = ENTREGA / "video_demo.mp4"
    assert video.exists()
    assert video.stat().st_size > 1_000_000
    timeline = json.loads((ENTREGA / "video_timeline.json").read_text(encoding="utf-8"))
    assert len(timeline["escenas"]) == 9
    assert timeline["duracion_estimada_s"] >= 180
    capturas = [ruta for ruta in (ENTREGA / "capturas").glob("*.png")]
    assert len(capturas) >= 10
    assert all(ruta.stat().st_size > 20_000 for ruta in capturas)


def test_ficha_y_readme_reproducibles() -> None:
    ficha = (config.DIR_ETAPA6 / "FICHA_TECNICA.md").read_text(encoding="utf-8")
    readme = (config.DIR_ETAPA6 / "README.md").read_text(encoding="utf-8")
    for texto in (ficha, readme):
        assert "python -m mvp.scripts.ejecutar_etapa6" in texto
        assert "streamlit run mvp/app.py" in texto
        assert "EXP-2024-089" in texto


def test_checklist_declara_pendientes_externos() -> None:
    checklist = (EVIDENCIA / "06_checklist_entrega.md").read_text(encoding="utf-8")
    assert "Video demo (3:03" in checklist
    assert "Feedback de especialista | ☐" in checklist
    assert "Enlaces de respaldo | ✅" in checklist
