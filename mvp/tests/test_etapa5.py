"""Pruebas de exportación, acceso, contingencia y tolerancia a errores (Etapa 5)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
from docx import Document
from openpyxl import load_workbook

from mvp.core import access, config
from mvp.core.ai_service import ProveedorFallido
from mvp.core.analysis import AnalizadorExpediente
from mvp.core.evaluation import EvaluadorExpediente
from mvp.core.exporters import exportar_excel, exportar_informes, exportar_word
from mvp.core.pipeline import ProcesadorDocumental

EXPEDIENTE = config.EXPEDIENTE_DEFECTO
ACTOR = "Lucía Ramos"

HOJAS = [
    "Resumen",
    "Requisitos",
    "Decisiones",
    "Propuestas",
    "Evidencias",
    "Documentos",
    "Auditoría",
]


# --- Fixtures -------------------------------------------------------------


@pytest.fixture(scope="module")
def base(tmp_path_factory: pytest.TempPathFactory, corpus_etapa3: dict):
    """Caso analizado y decidido, reutilizado como plantilla de solo lectura."""

    ruta_bd = tmp_path_factory.mktemp("etapa5_base") / "base.db"
    procesador = ProcesadorDocumental(ruta_bd)
    procesador.registrar_expediente(
        EXPEDIENTE,
        "Carretera Central Tramo 2 · Km 42–78",
        especialidad="Pavimentos",
        version="v5",
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
    evaluador = EvaluadorExpediente(ruta_bd)
    analizador.recuperar(EXPEDIENTE)
    analizador.analizar_expediente(EXPEDIENTE)
    for requisito_id in ("RQ-04", "RQ-07"):
        evaluador.decidir(
            EXPEDIENTE,
            requisito_id,
            "aceptar",
            actor=ACTOR,
            motivo="Fuente y cita verificadas por el especialista.",
        )
    evaluador.decidir(
        EXPEDIENTE,
        "RQ-06",
        "modificar",
        estado_final="Cumple parcialmente",
        actor=ACTOR,
        motivo="La curva S no cubre dos partidas del plazo.",
    )
    evaluador.decidir(
        EXPEDIENTE,
        "RQ-05",
        "descartar",
        actor=ACTOR,
        motivo="Los planos no permiten verificar la coherencia con los metrados.",
    )
    return SimpleNamespace(ruta_bd=ruta_bd, analizador=analizador, evaluador=evaluador)


@pytest.fixture()
def servicio(base, tmp_path: Path):
    """Copia la base para aislar las escrituras de cada prueba."""

    ruta_bd = tmp_path / "prueba.db"
    shutil.copy2(base.ruta_bd, ruta_bd)
    return SimpleNamespace(
        ruta_bd=ruta_bd,
        analizador=AnalizadorExpediente(ruta_bd),
        evaluador=EvaluadorExpediente(ruta_bd),
    )


# --- Política de acceso ---------------------------------------------------


def test_politica_distribuye_roles_y_expedientes() -> None:
    politica = access.cargar_politica()

    assert politica.rol("Lucía Ramos") == "especialista"
    assert politica.rol("Carlos Méndez") == "lector"
    assert politica.rol("Admin MVP") == "administrador"
    assert politica.expedientes("Admin MVP") == ["*"]
    assert politica.puede("Lucía Ramos", "ver", EXPEDIENTE)
    assert politica.puede("Lucía Ramos", "decidir", EXPEDIENTE)
    assert politica.puede("Lucía Ramos", "exportar", EXPEDIENTE)
    assert politica.puede("Carlos Méndez", "ver", EXPEDIENTE)
    assert not politica.puede("Carlos Méndez", "cargar", EXPEDIENTE)
    assert not politica.puede("Carlos Méndez", "decidir", EXPEDIENTE)
    assert not politica.puede("Carlos Méndez", "exportar", EXPEDIENTE)


def test_politica_deniega_con_causa_y_respeta_asignacion() -> None:
    politica = access.cargar_politica()

    with pytest.raises(access.AccesoDenegado, match="permiso"):
        politica.exigir("Carlos Méndez", "exportar", EXPEDIENTE)
    with pytest.raises(access.AccesoDenegado, match="no tiene asignado"):
        politica.exigir("Lucía Ramos", "ver", "EXP-2024-090")
    with pytest.raises(access.AccesoDenegado, match="no está registrado"):
        politica.exigir("Usuario Inexistente", "ver", EXPEDIENTE)

    assert politica.puede("Admin MVP", "administrar", "EXP-2024-090")
    assert not access.verificar_acceso("Carlos Méndez", "decidir", EXPEDIENTE)


def test_politica_rechaza_json_incompleto(tmp_path: Path) -> None:
    ruta = tmp_path / "usuarios.json"
    ruta.write_text(json.dumps({"roles": {}, "usuarios": {}}), encoding="utf-8")
    with pytest.raises(ValueError):
        access.cargar_politica(ruta)

    ruta.write_text(
        json.dumps(
            {
                "roles": {"lector": {"permisos": ["ver", "aprobar"]}},
                "usuarios": {"X": {"rol": "lector", "expedientes": ["EXP-1"]}},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="permisos desconocidos"):
        access.cargar_politica(ruta)


# --- Exportación real -----------------------------------------------------


def test_exportar_excel_genera_siete_hojas(base, tmp_path: Path) -> None:
    ruta = exportar_excel(
        base.ruta_bd, EXPEDIENTE, tmp_path / "informe.xlsx"
    )
    libro = load_workbook(ruta, data_only=True)

    assert libro.sheetnames == HOJAS
    assert libro["Requisitos"].max_row == 8
    assert libro["Decisiones"].max_row == 5
    assert libro["Documentos"].max_row - 1 == 8
    valores = [
        celda.value
        for fila in libro["Resumen"].iter_rows()
        for celda in fila
        if celda.value is not None
    ]
    assert "39.0%" in [str(valor) for valor in valores]
    assert "EXP-2024-089" in [str(valor) for valor in valores]


def test_exportar_word_incluye_secciones_y_fuentes(base, tmp_path: Path) -> None:
    ruta = exportar_word(base.ruta_bd, EXPEDIENTE, tmp_path / "informe.docx")
    documento = Document(ruta)
    encabezados = [
        parrafo.text
        for parrafo in documento.paragraphs
        if parrafo.style.name == "Heading 1"
    ]
    texto = "\n".join(parrafo.text for parrafo in documento.paragraphs)
    tablas = "\n".join(
        celda.text
        for tabla in documento.tables
        for fila in tabla.rows
        for celda in fila.cells
    )

    assert encabezados == [
        "1. Resumen ejecutivo",
        "2. Resultados por requisito",
        "3. Observaciones y fuentes",
        "4. Historial de decisiones",
        "5. Alcance y limitaciones",
    ]
    assert len(documento.tables) >= 3
    assert "39.0%" in tablas
    assert "Presupuesto.xlsx" in texto
    assert "No se encontró información" in tablas


def test_exportacion_refleja_la_base_y_no_datos_fijos(
    servicio, tmp_path: Path
) -> None:
    primera = exportar_informes(servicio.ruta_bd, EXPEDIENTE, tmp_path / "uno")
    libro = load_workbook(primera["xlsx"], data_only=True)
    assert libro["Decisiones"].max_row == 5

    servicio.evaluador.decidir(
        EXPEDIENTE,
        "RQ-06",
        "modificar",
        estado_final="Cumple",
        actor=ACTOR,
        motivo="La revisión posterior confirma que el cronograma sí cubre el plazo.",
    )
    segunda = exportar_informes(servicio.ruta_bd, EXPEDIENTE, tmp_path / "dos")
    libro_nuevo = load_workbook(segunda["xlsx"], data_only=True)
    assert libro_nuevo["Decisiones"].max_row == 6

    filas = list(libro_nuevo["Decisiones"].iter_rows(min_row=2, values_only=True))
    motivos = [fila[5] for fila in filas]
    assert any("revisión posterior" in (motivo or "") for motivo in motivos)


# --- Contingencia ---------------------------------------------------------


def test_contingencia_visible_y_resoluble_manual(servicio) -> None:
    from mvp.core import db

    with db.conectar(servicio.ruta_bd) as conexion:
        conexion.execute(
            "UPDATE propuestas_ia SET valida = 0 "
            "WHERE expediente_id = ? AND requisito_id = 'RQ-02'",
            (EXPEDIENTE,),
        )
    resultado = servicio.analizador.analizar_requisito(
        EXPEDIENTE, "RQ-02", proveedor=ProveedorFallido()
    )
    assert resultado.estado == "Requiere revisión especializada"

    resumen = servicio.analizador.resumen(EXPEDIENTE)
    detalle = next(
        item for item in resumen["requisitos"] if item["requisito_id"] == "RQ-02"
    )
    assert detalle["contingencia"] is True
    assert resumen["contingencias"] >= 1

    servicio.analizador.registrar_evaluacion_manual(
        EXPEDIENTE,
        "RQ-02",
        "Requiere revisión especializada",
        "La IA no respondió; se revisó el expediente y falta el CV del residente.",
        actor=ACTOR,
    )
    resuelto = next(
        item
        for item in servicio.analizador.resumen(EXPEDIENTE)["requisitos"]
        if item["requisito_id"] == "RQ-02"
    )
    assert resuelto["origen"] == "manual"
    assert resuelto["contingencia"] is False


# --- Error, reintento y estado vacío -------------------------------------


def test_error_conserva_avance_y_reintento_agrega_documento(servicio, tmp_path: Path) -> None:
    antes = servicio.analizador.resumen(EXPEDIENTE)
    decisiones_antes = servicio.evaluador.vigentes(EXPEDIENTE)
    validos_antes = sum(
        1
        for documento in servicio.analizador.procesador.listar_documentos(EXPEDIENTE)
        if documento["estado"] == "VALIDO"
    )

    roto = tmp_path / "roto.pdf"
    roto.write_bytes(b"%PDF-1.4\ncontenido truncado")
    fallo = servicio.analizador.procesador.ingestar_archivo(
        EXPEDIENTE, roto, actor=ACTOR
    )
    assert not fallo.ok
    assert fallo.motivo_rechazo == "ARCHIVO_DANADO"

    durante = servicio.analizador.resumen(EXPEDIENTE)
    assert durante["avance_pct"] == antes["avance_pct"]
    assert servicio.evaluador.vigentes(EXPEDIENTE) == decisiones_antes
    validos_durante = sum(
        1
        for documento in servicio.analizador.procesador.listar_documentos(EXPEDIENTE)
        if documento["estado"] == "VALIDO"
    )
    assert validos_durante == validos_antes

    roto.unlink()
    valido = tmp_path / "reintento.docx"
    documento = Document()
    documento.add_heading("Reintento", level=1)
    documento.add_paragraph("Documento válido que reemplaza al archivo corrupto.")
    documento.save(valido)
    reintento = servicio.analizador.procesador.ingestar_archivo(
        EXPEDIENTE, valido, actor=ACTOR
    )
    assert reintento.ok

    despues = servicio.analizador.resumen(EXPEDIENTE)
    assert despues["avance_pct"] == antes["avance_pct"]
    assert servicio.evaluador.vigentes(EXPEDIENTE) == decisiones_antes
    validos_despues = sum(
        1
        for documento in servicio.analizador.procesador.listar_documentos(EXPEDIENTE)
        if documento["estado"] == "VALIDO"
    )
    assert validos_despues == validos_antes + 1


def test_expediente_vacio_exporta_sin_excepciones(servicio, tmp_path: Path) -> None:
    vacio = "EXP-PRUEBA-VACIO"
    servicio.analizador.procesador.registrar_expediente(
        vacio, "Sin documentos ni decisiones", actor="prueba"
    )
    resumen = servicio.analizador.resumen(vacio)
    assert resumen["decisiones_registradas"] == 0
    assert resumen["avance_pct"] == 0.0
    assert resumen["cobertura_revision_pct"] == 0.0

    rutas = exportar_informes(servicio.ruta_bd, vacio, tmp_path / "vacio")
    libro = load_workbook(rutas["xlsx"], data_only=True)
    documento = Document(rutas["docx"])

    assert libro.sheetnames == HOJAS
    assert libro["Decisiones"].max_row == 1
    assert "Sin decisiones registradas." in [
        parrafo.text for parrafo in documento.paragraphs
    ]
    assert "0.0%" in "\n".join(
        celda.text
        for tabla in documento.tables
        for fila in tabla.rows
        for celda in fila.cells
    )


# --- Interfaz -------------------------------------------------------------


def test_app_arranca_y_respeta_el_rol(monkeypatch, base) -> None:
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(config, "RUTA_BD", base.ruta_bd)
    ruta_app = Path(__file__).resolve().parents[2] / "mvp" / "app.py"
    at = AppTest.from_file(ruta_app, default_timeout=120).run()

    assert not at.exception
    assert len(at.tabs) == 8
    assert "especialista" in " ".join(caption.value for caption in at.sidebar.caption)

    at.sidebar.selectbox[0].set_value("Carlos Méndez").run()
    assert not at.exception
    infos = " ".join(info.value for info in at.info)
    assert "no cargar documentos" in infos
    assert "no exportarlos" in infos
    assert "no registrar decisiones" in infos
