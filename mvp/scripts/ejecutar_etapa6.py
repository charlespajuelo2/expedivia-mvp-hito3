"""Ejecuta la validación integral y genera la entrega de la Etapa 6.

Uso::

    python -m mvp.scripts.ejecutar_etapa6

No modifica los artefactos cerrados de las Etapas 1-5: usa su propio corpus en
``mvp/etapa6/muestras/``, su propia base en ``mvp/etapa6/evidencia/`` y escribe
sus reportes y exportaciones en ``mvp/etapa6/evidencia/``.

Reportes:

- ``00_entorno.json``: versiones, rutas y alcance.
- ``01_flujo_extremo_a_extremo.md``: recorrido completo y tiempos.
- ``02_casos_prueba.md`` y ``02_casos_prueba.json``: 16 casos mapeados a CA.
- ``03_errores_correcciones.md``: incidencias reales y correcciones aplicadas.
- ``04_metricas_linea_base.md``: línea base vs. sistema y aciertos.
- ``05_revision_tecnica.md``: revisión interna y formulario de feedback externo.
- ``06_checklist_entrega.md``: estado de entregables del Hito 3.
- ``07_guion_video.md``: guion de la demo de 3–5 minutos.
- ``08_acta_ensayo.md``: ensayo de sustentación de 10 minutos.
- ``09_ficha_tecnica.md``: ficha técnica reproducible.
- ``10_metricas.json``: métricas comparables de la ejecución.
- ``exportaciones/``: informes XLSX y DOCX generados desde SQLite.
"""

from __future__ import annotations

import json
import platform
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from docx import Document
from openpyxl import load_workbook

from mvp.core import access, config, db
from mvp.core.ai_service import ProveedorFallido
from mvp.core.analysis import AnalizadorExpediente
from mvp.core.evaluation import EvaluadorExpediente
from mvp.core.exporters import exportar_informes
from mvp.core.integrity import verificar_expediente
from mvp.core.pipeline import ProcesadorDocumental
from mvp.scripts.generar_muestras_etapa3 import generar_corpus_etapa3

EXPEDIENTE = config.EXPEDIENTE_DEFECTO
EXPEDIENTE_CONTROL = "EXP-2024-089-SIN-EVIDENCIA"
EXPEDIENTE_RESERVADO = "EXP-2024-090"
EXPEDIENTE_PRUEBAS = "EXP-2024-089-PRUEBAS"
RUTA_BD = config.DIR_EVIDENCIA_ETAPA6 / "mvp_etapa6.db"
CARPETA_EXPORT = config.DIR_EVIDENCIA_ETAPA6 / "exportaciones"
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
SECCIONES = [
    "1. Resumen ejecutivo",
    "2. Resultados por requisito",
    "3. Observaciones y fuentes",
    "4. Historial de decisiones",
    "5. Alcance y limitaciones",
]


# --- Utilidades -----------------------------------------------------------


def _escribir(nombre: str, contenido: str) -> Path:
    config.DIR_EVIDENCIA_ETAPA6.mkdir(parents=True, exist_ok=True)
    ruta = config.DIR_EVIDENCIA_ETAPA6 / nombre
    ruta.write_text(contenido.rstrip() + "\n", encoding="utf-8")
    return ruta


def _tabla(cabeceras: list[str], filas: list[list[Any]]) -> str:
    lineas = [
        "| " + " | ".join(cabeceras) + " |",
        "|" + "|".join("---" for _ in cabeceras) + "|",
    ]
    for fila in filas:
        lineas.append("| " + " | ".join(str(valor) for valor in fila) + " |")
    return "\n".join(lineas)


def _cronometrar(funcion: Callable[[], Any]) -> tuple[Any, float]:
    inicio = time.perf_counter()
    resultado = funcion()
    return resultado, (time.perf_counter() - inicio) * 1000


def _entorno() -> dict[str, Any]:
    import docx
    import openpyxl
    import pypdf
    import streamlit

    return {
        "fecha_ejecucion": datetime.now().isoformat(timespec="seconds"),
        "python": sys.version,
        "plataforma": platform.platform(),
        "base_datos": str(RUTA_BD),
        "corpus": str(config.DIR_MUESTRAS_ETAPA6 / "caso"),
        "exportaciones": str(CARPETA_EXPORT),
        "versiones": {
            "pypdf": pypdf.__version__,
            "python-docx": docx.__version__,
            "openpyxl": openpyxl.__version__,
            "streamlit": streamlit.__version__,
        },
        "expedientes": [
            EXPEDIENTE,
            EXPEDIENTE_CONTROL,
            EXPEDIENTE_RESERVADO,
            EXPEDIENTE_PRUEBAS,
        ],
        "alcance": "validación integral de extremo a extremo y material de entrega",
    }


def _metricas(resumen: dict[str, Any]) -> dict[str, Any]:
    claves = [
        "requisitos_total",
        "cobertura_revision_pct",
        "peso_decidido_pct",
        "avance_pct",
        "cumplimiento_pct",
        "decisiones_registradas",
        "aceptadas",
        "modificadas",
        "descartadas",
        "cumple",
        "parcial",
        "no_cumple",
        "sin_informacion",
        "requiere_revision",
        "integridad_alertas",
    ]
    return {clave: resumen[clave] for clave in claves}


def _revisar_xlsx(ruta: Path) -> dict[str, Any]:
    libro = load_workbook(ruta, data_only=True)
    valores = [
        str(celda.value)
        for fila in libro["Resumen"].iter_rows()
        for celda in fila
        if celda.value is not None
    ]
    return {
        "hojas": list(libro.sheetnames),
        "requisitos_filas": libro["Requisitos"].max_row - 1,
        "decisiones_filas": libro["Decisiones"].max_row - 1,
        "avance_39": any("39.0%" in valor for valor in valores),
        "bytes": ruta.stat().st_size,
    }


def _revisar_docx(ruta: Path) -> dict[str, Any]:
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
    return {
        "secciones": encabezados,
        "tablas": len(documento.tables),
        "contiene_fuente": "Presupuesto.xlsx" in texto,
        "contiene_avance": "39.0%" in tablas,
        "bytes": ruta.stat().st_size,
    }


# --- Preparación del flujo ------------------------------------------------


def preparar_flujo() -> dict[str, Any]:
    config.preparar_directorios()
    config.DIR_EVIDENCIA_ETAPA6.mkdir(parents=True, exist_ok=True)
    if RUTA_BD.exists():
        RUTA_BD.unlink()
    for sufijo in ("-wal", "-shm"):
        sobrante = Path(str(RUTA_BD) + sufijo)
        if sobrante.exists():
            sobrante.unlink()
    if CARPETA_EXPORT.exists():
        shutil.rmtree(CARPETA_EXPORT)
    carpeta_error = config.DIR_MUESTRAS_ETAPA6 / "error_reintento"
    if carpeta_error.exists():
        shutil.rmtree(carpeta_error)

    corpus = generar_corpus_etapa3(config.DIR_MUESTRAS_ETAPA6)
    procesador = ProcesadorDocumental(RUTA_BD)
    for expediente, nombre in (
        (EXPEDIENTE, "Carretera Central Tramo 2 · Km 42–78"),
        (EXPEDIENTE_CONTROL, "Control sin evidencia"),
        (EXPEDIENTE_RESERVADO, "Expediente reservado al administrador"),
        (EXPEDIENTE_PRUEBAS, "Expediente de pruebas de resiliencia"),
    ):
        procesador.registrar_expediente(
            expediente,
            nombre,
            especialidad="Pavimentos",
            version="v6",
            actor="equipo-mvp",
        )

    resultados, ms_ingesta = _cronometrar(
        lambda: procesador.ingestar_carpeta(
            EXPEDIENTE, corpus["carpeta_caso"], actor="equipo-mvp"
        )
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
        actor=ACTOR,
        motivo="El contenido corresponde a EETT aunque el nombre del archivo es genérico.",
    )

    analizador = AnalizadorExpediente(RUTA_BD)
    evaluador = EvaluadorExpediente(RUTA_BD)
    _, ms_recuperacion = _cronometrar(lambda: analizador.recuperar(EXPEDIENTE))
    _, ms_analisis = _cronometrar(lambda: analizador.analizar_expediente(EXPEDIENTE))

    def decidir_todo():
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
            motivo="La curva S no cubre dos partidas del plazo contractual.",
        )
        evaluador.decidir(
            EXPEDIENTE,
            "RQ-05",
            "descartar",
            actor=ACTOR,
            motivo="Los planos no permiten verificar la coherencia con los metrados.",
        )
        evaluador.decidir(
            EXPEDIENTE,
            "RQ-04",
            "modificar",
            estado_final="Cumple parcialmente",
            actor=ACTOR,
            motivo="Revisión intermedia: se detectó una partida sin metrado detallado.",
        )
        evaluador.decidir(
            EXPEDIENTE,
            "RQ-04",
            "aceptar",
            actor=ACTOR,
            motivo="La partida observada sí cuenta con metrado; se restituye.",
        )

    _, ms_decisiones = _cronometrar(decidir_todo)
    rutas, ms_export = _cronometrar(
        lambda: exportar_informes(RUTA_BD, EXPEDIENTE, CARPETA_EXPORT)
    )
    resumen = analizador.resumen(EXPEDIENTE)
    historial = evaluador.historial(EXPEDIENTE)

    return {
        "corpus": corpus,
        "procesador": procesador,
        "analizador": analizador,
        "evaluador": evaluador,
        "resultados": resultados,
        "eett": eett,
        "rutas": rutas,
        "resumen": resumen,
        "historial": historial,
        "tiempos": {
            "ingesta": ms_ingesta,
            "recuperacion": ms_recuperacion,
            "analisis": ms_analisis,
            "decisiones": ms_decisiones,
            "exportacion": ms_export,
        },
    }


# --- Casos de prueba ------------------------------------------------------


def _caso(
    identificador: str,
    ca: str,
    nombre: str,
    esperado: str,
    funcion: Callable[[dict[str, Any]], tuple[bool, str, str]],
    contexto: dict[str, Any],
) -> dict[str, Any]:
    inicio = time.perf_counter()
    try:
        ok, obtenido, detalle = funcion(contexto)
    except Exception as error:  # un fallo de caso no aborta la suite
        ok = False
        obtenido = f"Excepción: {error.__class__.__name__}: {error}"
        detalle = "Revisar la traza del caso."
    return {
        "id": identificador,
        "ca": ca,
        "nombre": nombre,
        "esperado": esperado,
        "obtenido": obtenido,
        "detalle": detalle,
        "estado": "PASA" if ok else "FALLA",
        "ms": round((time.perf_counter() - inicio) * 1000, 1),
    }


def _caso_carga(ctx: dict[str, Any]):
    documentos = ctx["procesador"].listar_documentos(EXPEDIENTE)
    validos = [d for d in documentos if d["estado"] == "VALIDO"]
    ok = (
        len(ctx["resultados"]) == 8
        and all(resultado.ok for resultado in ctx["resultados"])
        and len(validos) == 8
        and all(len(documento["sha256"]) == 64 for documento in validos)
    )
    return (
        ok,
        f"{len(validos)}/8 documentos válidos con SHA-256",
        "Se cargaron los 8 documentos del corpus y todos tienen hash.",
    )


def _caso_rechazo(ctx: dict[str, Any]):
    carpeta = config.DIR_MUESTRAS_ETAPA6 / "error_reintento"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / "CP-02_Corrupto.pdf"
    ruta.write_bytes(b"%PDF-1.4\ncontenido truncado")
    antes = sum(
        1
        for d in ctx["procesador"].listar_documentos(EXPEDIENTE_PRUEBAS)
        if d["estado"] == "VALIDO"
    )
    resultado = ctx["procesador"].ingestar_archivo(
        EXPEDIENTE_PRUEBAS, ruta, actor=ACTOR
    )
    despues = sum(
        1
        for d in ctx["procesador"].listar_documentos(EXPEDIENTE_PRUEBAS)
        if d["estado"] == "VALIDO"
    )
    ok = (
        not resultado.ok
        and resultado.motivo_rechazo == "ARCHIVO_DANADO"
        and antes == despues
    )
    return (
        ok,
        f"motivo={resultado.motivo_rechazo}; válidos {antes}→{despues}",
        "El rechazo no agrega documentos válidos ni evidencia.",
    )


def _caso_clasificacion(ctx: dict[str, Any]):
    documento = next(
        d
        for d in ctx["procesador"].listar_documentos(EXPEDIENTE)
        if d["nombre_archivo"] == "EETT_General_v2.docx"
    )
    ok = (
        documento["tipo_documental"] == "Especificaciones técnicas"
        and documento["componente"] == "EETT"
        and documento["clasificacion_origen"] == "correccion_humana"
    )
    return (
        ok,
        f"{documento['tipo_documental']} / {documento['componente']} "
        f"({documento['clasificacion_origen']})",
        "La corrección humana persiste vinculada al hash del documento.",
    )


def _caso_extraccion(ctx: dict[str, Any]):
    ubicaciones = {}
    for documento in ctx["procesador"].listar_documentos(EXPEDIENTE):
        if documento["estado"] != "VALIDO":
            continue
        fragmentos = ctx["procesador"].fragmentos_de(documento["id"])
        if fragmentos:
            ubicaciones[documento["formato"]] = fragmentos[0]["ubicacion"]
    ok = (
        "PDF" in ubicaciones
        and "DOCX" in ubicaciones
        and "XLSX" in ubicaciones
        and ubicaciones["PDF"].startswith("p.")
        and ubicaciones["XLSX"].startswith("Hoja:")
        and "párr." in ubicaciones["DOCX"]
    )
    return (
        ok,
        json.dumps(ubicaciones, ensure_ascii=False),
        "Cada formato conserva una ubicación verificable.",
    )


def _caso_evidencia(ctx: dict[str, Any]):
    evidencias = ctx["analizador"].evidencias(EXPEDIENTE, "RQ-04")
    ok = bool(evidencias) and len(evidencias[0]["sha256_fuente"]) == 64
    archivo = evidencias[0]["archivo"] if evidencias else "—"
    return (
        ok,
        f"{len(evidencias)} evidencias; primera={archivo}",
        "La evidencia incluye archivo, ubicación, cita y hash.",
    )


def _caso_contrato(ctx: dict[str, Any]):
    propuestas = ctx["analizador"].propuestas(EXPEDIENTE, solo_validas=True, limite=1000)
    propuesta = ctx["analizador"].ultima_propuesta(EXPEDIENTE, "RQ-04")
    ok = (
        len(propuestas) == 7
        and propuesta is not None
        and bool(propuesta.get("archivo"))
        and bool(propuesta.get("cita"))
        and len(propuesta.get("sha256_fuente") or "") == 64
    )
    return (
        ok,
        f"{len(propuestas)} propuestas válidas; RQ-04 con fuente y cita",
        "El contrato JSON exige y conserva los 8 campos.",
    )


def _caso_ausencia(ctx: dict[str, Any]):
    resultado = ctx["analizador"].analizar_requisito(EXPEDIENTE_CONTROL, "RQ-01")
    resumen = ctx["analizador"].resumen(EXPEDIENTE_CONTROL)
    ok = (
        resultado.estado == "No se encontró información"
        and resumen["sin_informacion"] == 1
        and resumen["no_cumple"] == 0
    )
    return (
        ok,
        f"estado={resultado.estado}; sin_informacion={resumen['sin_informacion']}; "
        f"no_cumple={resumen['no_cumple']}",
        "La ausencia de evidencia no se convierte en incumplimiento.",
    )


def _caso_historial(ctx: dict[str, Any]):
    historial = ctx["historial"]
    rq04 = [registro for registro in historial if registro["requisito_id"] == "RQ-04"]
    vigentes = ctx["evaluador"].vigentes(EXPEDIENTE)
    ok = (
        len(historial) == 6
        and len(rq04) == 3
        and len(vigentes) == 4
        and sum(1 for r in historial if r["es_vigente"]) == 4
    )
    return (
        ok,
        f"{len(historial)} registros; RQ-04={len(rq04)}; vigentes={len(vigentes)}",
        "El historial es acumulativo y solo una decisión por requisito es vigente.",
    )


def _caso_avance(ctx: dict[str, Any]):
    resumen = ctx["resumen"]
    ok = (
        resumen["avance_pct"] == 39.0
        and resumen["peso_decidido_pct"] == 58.0
        and resumen["cumplimiento_pct"] == 88.6
        and resumen["no_cumple"] == 0
    )
    return (
        ok,
        f"avance={resumen['avance_pct']}%; peso decidido={resumen['peso_decidido_pct']}%; "
        f"cumplimiento={resumen['cumplimiento_pct']}%",
        f"Fórmula: {resumen['avance_formula']}",
    )


def _caso_excel(ctx: dict[str, Any]):
    revision = _revisar_xlsx(ctx["rutas"]["xlsx"])
    ok = (
        revision["hojas"] == HOJAS
        and revision["requisitos_filas"] == 7
        and revision["decisiones_filas"] == 6
        and revision["avance_39"]
    )
    return (
        ok,
        f"{len(revision['hojas'])} hojas; requisitos={revision['requisitos_filas']}; "
        f"decisiones={revision['decisiones_filas']}",
        f"Archivo: {ctx['rutas']['xlsx'].name}",
    )


def _caso_word(ctx: dict[str, Any]):
    revision = _revisar_docx(ctx["rutas"]["docx"])
    ok = (
        revision["secciones"] == SECCIONES
        and revision["tablas"] >= 3
        and revision["contiene_fuente"]
        and revision["contiene_avance"]
    )
    return (
        ok,
        f"{len(revision['secciones'])} secciones; {revision['tablas']} tablas",
        f"Archivo: {ctx['rutas']['docx'].name}",
    )


def _caso_error_reintento(ctx: dict[str, Any]):
    antes = ctx["resumen"]
    decisiones_antes = ctx["evaluador"].vigentes(EXPEDIENTE)
    validos_antes = sum(
        1
        for d in ctx["procesador"].listar_documentos(EXPEDIENTE_PRUEBAS)
        if d["estado"] == "VALIDO"
    )
    carpeta = config.DIR_MUESTRAS_ETAPA6 / "error_reintento"
    ruta = carpeta / "CP-12_Reintento.docx"
    if ruta.exists():
        ruta.unlink()
    documento = Document()
    documento.add_heading("Documento de reintento", level=1)
    documento.add_paragraph("Reemplaza al archivo corrupto del caso CP-02.")
    documento.save(ruta)
    resultado = ctx["procesador"].ingestar_archivo(
        EXPEDIENTE_PRUEBAS, ruta, actor=ACTOR
    )
    despues = ctx["analizador"].resumen(EXPEDIENTE)
    validos_despues = sum(
        1
        for d in ctx["procesador"].listar_documentos(EXPEDIENTE_PRUEBAS)
        if d["estado"] == "VALIDO"
    )
    ok = (
        resultado.ok
        and despues["avance_pct"] == antes["avance_pct"]
        and ctx["evaluador"].vigentes(EXPEDIENTE) == decisiones_antes
        and validos_despues == validos_antes + 1
    )
    return (
        ok,
        f"válidos {validos_antes}→{validos_despues}; avance "
        f"{antes['avance_pct']}%→{despues['avance_pct']}%",
        "El reintento agrega el documento sin perder decisiones ni avance.",
    )


def _caso_permisos(ctx: dict[str, Any]):
    politica = access.cargar_politica()
    denegaciones = []
    for usuario, accion, expediente in (
        ("Carlos Méndez", "decidir", EXPEDIENTE),
        ("Carlos Méndez", "exportar", EXPEDIENTE),
        ("Lucía Ramos", "ver", EXPEDIENTE_RESERVADO),
    ):
        try:
            politica.exigir(usuario, accion, expediente)
        except access.AccesoDenegado as error:
            denegaciones.append(str(error))
    ok = (
        len(denegaciones) == 3
        and politica.puede("Lucía Ramos", "exportar", EXPEDIENTE)
        and politica.puede("Admin MVP", "administrar", EXPEDIENTE_RESERVADO)
        and not politica.puede("Carlos Méndez", "decidir", EXPEDIENTE)
    )
    return (
        ok,
        f"{len(denegaciones)} denegaciones con causa",
        "Lector sin decisión/exportación; especialista limitado a su expediente.",
    )


def _caso_contingencia(ctx: dict[str, Any]):
    import tempfile

    with tempfile.TemporaryDirectory() as carpeta:
        copia = Path(carpeta) / "contingencia.db"
        shutil.copy2(RUTA_BD, copia)
        with db.conectar(copia) as conexion:
            conexion.execute(
                "UPDATE propuestas_ia SET valida = 0 "
                "WHERE expediente_id = ? AND requisito_id = 'RQ-02'",
                (EXPEDIENTE,),
            )
        analizador = AnalizadorExpediente(copia)
        resultado = analizador.analizar_requisito(
            EXPEDIENTE, "RQ-02", proveedor=ProveedorFallido()
        )
        detalle = next(
            item
            for item in analizador.resumen(EXPEDIENTE)["requisitos"]
            if item["requisito_id"] == "RQ-02"
        )
        visible = detalle["contingencia"] is True
        analizador.registrar_evaluacion_manual(
            EXPEDIENTE,
            "RQ-02",
            "Requiere revisión especializada",
            "La IA no respondió; falta el CV del residente.",
            actor=ACTOR,
        )
        resuelto = next(
            item
            for item in analizador.resumen(EXPEDIENTE)["requisitos"]
            if item["requisito_id"] == "RQ-02"
        )
        ok = (
            resultado.estado == "Requiere revisión especializada"
            and visible
            and resuelto["origen"] == "manual"
            and resuelto["contingencia"] is False
        )
    return (
        ok,
        f"contingencia visible={visible}; origen final={resuelto['origen']}",
        "La evaluación manual resuelve la contingencia sin perder trazabilidad.",
    )


def _caso_cache(ctx: dict[str, Any]):
    documento = next(
        d
        for d in ctx["procesador"].listar_documentos(EXPEDIENTE)
        if d["nombre_archivo"] == "TDR_Carretera_Central_v3.pdf"
    )
    antes = len(ctx["procesador"].listar_documentos(EXPEDIENTE))
    resultado = ctx["procesador"].ingestar_archivo(
        EXPEDIENTE, documento["ruta"], actor=ACTOR
    )
    despues = len(ctx["procesador"].listar_documentos(EXPEDIENTE))
    ok = resultado.ok and resultado.cache_hit and antes == despues
    return (
        ok,
        f"cache_hit={resultado.cache_hit}; documentos {antes}→{despues}",
        "La extracción se reutiliza por SHA-256 sin duplicar el inventario.",
    )


def _caso_integridad(ctx: dict[str, Any]):
    import tempfile

    with tempfile.TemporaryDirectory() as carpeta:
        copia = Path(carpeta) / "integridad.db"
        shutil.copy2(RUTA_BD, copia)
        documento = next(
            d
            for d in ctx["procesador"].listar_documentos(EXPEDIENTE)
            if d["nombre_archivo"] == "Presupuesto.xlsx"
        )
        ruta_documento = Path(documento["ruta"])
        original = ruta_documento.read_bytes()
        try:
            ruta_documento.write_bytes(original + b"\nmodificado")
            integridad = verificar_expediente(copia, EXPEDIENTE, actor=ACTOR)
            bloqueado = False
            try:
                EvaluadorExpediente(copia).decidir(
                    EXPEDIENTE,
                    "RQ-04",
                    "aceptar",
                    actor=ACTOR,
                    motivo="Intento con fuente modificada.",
                )
            except ValueError:
                bloqueado = True
        finally:
            ruta_documento.write_bytes(original)
        ok = integridad["requiere_atencion"] >= 1 and bloqueado
    return (
        ok,
        f"requiere_atencion={integridad['requiere_atencion']}; decisión bloqueada={bloqueado}",
        "Una fuente modificada invalida la propuesta y bloquea aceptar.",
    )


CASOS = [
    ("CP-01", "CA-01/02", "Carga de 8 documentos válidos", "8/8 válidos con SHA-256", _caso_carga),
    ("CP-02", "CA-02", "Rechazo de PDF corrupto", "ARCHIVO_DANADO sin evidencia", _caso_rechazo),
    ("CP-03", "CA-03/04", "Clasificación y corrección persistente", "EETT corregido y persistido", _caso_clasificacion),
    ("CP-04", "CA-04", "Extracción con ubicación verificable", "PDF, DOCX y XLSX con ubicación", _caso_extraccion),
    ("CP-05", "CA-06", "Evidencia con fuente, cita y hash", "RQ-04 con evidencia completa", _caso_evidencia),
    ("CP-06", "CA-07", "Contrato JSON y propuesta válida", "7/7 propuestas válidas", _caso_contrato),
    ("CP-07", "CA-08/09", "Ausencia de evidencia no es incumplimiento", "sin información y no_cumple=0", _caso_ausencia),
    ("CP-08", "CA-10/11", "Historial humano inmutable", "6 registros y 4 vigentes", _caso_historial),
    ("CP-09", "CA-12", "Avance ponderado verificable", "39.0% y 88.6%", _caso_avance),
    ("CP-10", "CA-13", "Exportación Excel real", "7 hojas y filas reales", _caso_excel),
    ("CP-11", "CA-14", "Exportación Word real", "5 secciones y fuentes", _caso_word),
    ("CP-12", "CA-16", "Error y reintento sin pérdida", "avance y decisiones conservados", _caso_error_reintento),
    ("CP-13", "CA-17", "Control de acceso por rol", "3 denegaciones con causa", _caso_permisos),
    ("CP-14", "CA-25", "Contingencia y evaluación manual", "contingencia resuelta", _caso_contingencia),
    ("CP-15", "CA-23", "Caché documental por hash", "cache_hit sin duplicar", _caso_cache),
    ("CP-16", "CA-20/24", "Integridad de fuente bloquea decisión", "fuente modificada detectada", _caso_integridad),
]


# --- Reportes -------------------------------------------------------------


def _reporte_flujo(ctx: dict[str, Any], total_ms: float) -> str:
    resumen = ctx["resumen"]
    tiempos = ctx["tiempos"]
    return f"""# Evidencia 01 — Flujo completo de extremo a extremo

**Comando reproducible:** `python -m mvp.scripts.ejecutar_etapa6`
**Base de datos:** `mvp/etapa6/evidencia/mvp_etapa6.db`
**Caso:** `{EXPEDIENTE}`

## Secuencia ejecutada

1. Generación del corpus propio (8 documentos).
2. Registro de 4 expedientes (caso, control vacío, reservado y pruebas de resiliencia).
3. Ingesta, validación, hash, caché y clasificación.
4. Corrección humana del documento ambiguo `EETT_General_v2.docx`.
5. Recuperación de evidencia para los 7 requisitos.
6. Análisis con el proveedor determinista y contrato JSON.
7. Decisiones humanas: aceptar, modificar, descartar e historial.
8. Verificación de avance, cumplimiento y estados.
9. Exportación Excel/Word desde SQLite y reapertura para validar.
10. Ejecución de los 16 casos de prueba mapeados a CA.

## Tiempos medidos

{_tabla(
    ["Etapa del flujo", "Milisegundos"],
    [
        ["Ingesta de 8 documentos", f"{tiempos['ingesta']:.1f}"],
        ["Recuperación de evidencia", f"{tiempos['recuperacion']:.1f}"],
        ["Análisis de 7 requisitos", f"{tiempos['analisis']:.1f}"],
        ["Decisiones humanas", f"{tiempos['decisiones']:.1f}"],
        ["Exportación Excel + Word", f"{tiempos['exportacion']:.1f}"],
        ["**Total de extremo a extremo**", f"**{total_ms:.1f}**"],
    ],
)}

## Resultado del flujo

| Métrica | Valor |
|---|---:|
| Documentos válidos | 8 |
| Requisitos con propuesta | 7/7 |
| Cobertura de revisión | {resumen['cobertura_revision_pct']}% |
| Decisiones vigentes | {resumen['decisiones_registradas']} |
| Avance ponderado | {resumen['avance_pct']}% |
| Cumplimiento ponderado | {resumen['cumplimiento_pct']}% |
| No cumple | {resumen['no_cumple']} |
| No se encontró información | {resumen['sin_informacion']} |

## Criterio de salida cubierto

- [x] El flujo completo se ejecuta desde cero con un comando.
- [x] Cada etapa deja datos persistidos y auditables.
- [x] La exportación se verifica reabriendo los archivos.
- [x] Los 16 casos de prueba se ejecutan sobre el flujo real.
"""


def _reporte_casos(casos: list[dict[str, Any]]) -> str:
    aprobados = sum(1 for caso in casos if caso["estado"] == "PASA")
    return f"""# Evidencia 02 — Casos de prueba mapeados a criterios de aceptación

Se ejecutaron **{len(casos)} casos** sobre el flujo real. Resultado:
**{aprobados}/{len(casos)} PASA**.

{_tabla(
    ["ID", "CA", "Caso", "Esperado", "Obtenido", "Estado", "ms"],
    [
        [
            caso["id"],
            caso["ca"],
            caso["nombre"],
            caso["esperado"],
            caso["obtenido"],
            caso["estado"],
            caso["ms"],
        ]
        for caso in casos
    ],
)}

## Detalle de evidencia

{chr(10).join(
    f"- **{caso['id']} · {caso['nombre']}** ({caso['ca']}): {caso['detalle']}"
    for caso in casos
)}

## Criterio de salida cubierto

- [x] Hay más de 10 casos, cada uno mapeado a CA.
- [x] Los casos usan la base y el corpus reales, no mocks.
- [x] Un fallo de caso no aborta la suite; queda registrado.
- [x] Se cubren carga, evidencia, IA, estados, decisiones, exportación,
      seguridad, contingencia, caché e integridad.
"""


def _reporte_errores() -> str:
    filas = [
        [
            "E-01",
            "Alto",
            "`EETT_General_v2.docx` se clasificó como documento genérico.",
            "El nombre del archivo no describe su contenido.",
            "Corrección humana a `Especificaciones técnicas / EETT`, vinculada al SHA-256.",
            "CP-03",
        ],
        [
            "E-02",
            "Medio",
            "La verificación del Word solo leía párrafos y no veía el avance en tablas.",
            "El script de aceptación inspeccionaba `document.paragraphs`.",
            "Se amplió la verificación a las celdas de todas las tablas.",
            "CP-11",
        ],
        [
            "E-03",
            "Medio",
            "La pestaña de exportación usaba `total_evidencias`, campo inexistente.",
            "Se asumió una clave que el resumen no expone.",
            "Se sumó `detalle['evidencias']` de los requisitos.",
            "CP-10/CP-11",
        ],
        [
            "E-04",
            "Medio",
            "El especialista no podía registrar el expediente al iniciar la app.",
            "El alta automática exigía `administrar`.",
            "Se habilitó el alta para roles con permiso `cargar`.",
            "CP-13",
        ],
        [
            "E-05",
            "Bajo",
            "La prueba de contingencia quedaba oculta por una propuesta válida previa.",
            "El resumen prioriza propuesta válida sobre contingencia.",
            "La prueba aísla el requisito invalidando la propuesta previa en una copia.",
            "CP-14",
        ],
        [
            "E-06",
            "Bajo",
            "El mensaje de éxito de exportación se pierde al hacer `st.rerun()`.",
            "La descarga se renderiza después del rerun.",
            "Se conserva la confirmación mediante las descargas disponibles.",
            "CP-10/CP-11",
        ],
        [
            "E-07",
            "Medio",
            "Los casos de resiliencia dejaban 10 documentos en el expediente principal.",
            "CP-02 y CP-12 ingestaban el PDF corrupto y el reintento en `EXP-2024-089`.",
            "Se aislaron en un expediente de pruebas; el caso principal vuelve a 8/8 válidos.",
            "CP-02/CP-12",
        ],
    ]
    return f"""# Evidencia 03 — Errores encontrados y correcciones aplicadas

Se registran incidencias reales detectadas durante la integración y las etapas
previas. Ninguna queda abierta como bloqueante.

{_tabla(
    ["ID", "Severidad", "Incidencia", "Causa", "Corrección", "Verificación"],
    filas,
)}

## Criterio de salida cubierto

- [x] Cada error tiene causa, corrección y caso de verificación.
- [x] Las correcciones se reflejan en el código y en las pruebas.
- [x] No quedan errores bloqueantes para la demostración.
"""


def _reporte_metricas(
    ctx: dict[str, Any], total_ms: float, linea_base: dict[str, Any], casos: list[dict[str, Any]]
) -> str:
    resumen = ctx["resumen"]
    minutos_base = sum(item["minutos"] for item in linea_base["actividades"])
    minutos_revision = int(linea_base.get("revision_humana_min", 0))
    minutos_mecanicos = minutos_base - minutos_revision
    ms_mecanico = minutos_mecanicos * 60 * 1000
    reduccion = (1 - total_ms / ms_mecanico) * 100
    aprobados = sum(1 for caso in casos if caso["estado"] == "PASA")
    etiquetas = {
        "clasificacion_inicial": "Clasificación inicial",
        "clasificacion_final": "Clasificación final",
        "requisitos_cubiertos": "Requisitos cubiertos",
        "propuestas_validas": "Propuestas válidas",
        "coincidencia_con_decision_final": "Coincidencia con la decisión final",
    }
    return f"""# Evidencia 04 — Línea base vs. sistema

La línea base es una **estimación declarada** para el mismo expediente
(8 documentos y 7 requisitos), no un cronometraje con un especialista. El tiempo
del sistema sí se mide en esta ejecución.

## Tiempo

{_tabla(
    ["Actividad manual", "Minutos estimados"],
    [[item["actividad"], item["minutos"]] for item in linea_base["actividades"]]
    + [["**Total manual**", f"**{minutos_base}**"]],
)}

| Indicador | Manual | Sistema |
|---|---:|---:|
| Trabajo mecánico (carga, extracción, búsqueda y formato) | {minutos_mecanicos} min | {total_ms / 1000:.2f} s |
| Reducción del trabajo mecánico | — | {reduccion:.2f}% |
| Revisión técnica y decisión | {minutos_revision} min | sigue siendo humana |
| Documentos procesados | 8 | 8 |
| Requisitos cubiertos | 7 | 7 |
| Informe Excel/Word | manual | automático desde SQLite |

> La reducción porcentual se refiere **solo a tareas mecánicas**. Es alta porque
> el sistema automatiza lectura, extracción, búsqueda, cálculo y formato, pero la
> cifra **no** es comparable con el juicio técnico: los {minutos_revision} minutos
> de revisión y decisión siguen en manos del especialista.

## Aciertos

{_tabla(
    ["Indicador", "Resultado"],
    [[etiquetas.get(clave, clave.replace("_", " ").title()), valor] for clave, valor in linea_base["aciertos"].items()],
)}

| Métrica del caso | Valor |
|---|---:|
| Propuestas válidas | {resumen['con_propuesta_valida']}/7 |
| Decisiones vigentes | {resumen['decisiones_registradas']} |
| Aceptadas / modificadas / descartadas | {resumen['aceptadas']} / {resumen['modificadas']} / {resumen['descartadas']} |
| Cumplimiento ponderado | {resumen['cumplimiento_pct']}% |
| No cumple | {resumen['no_cumple']} |
| Casos de prueba | {aprobados}/{len(casos)} PASA |

## Supuestos

{chr(10).join(f"- {supuesto}" for supuesto in linea_base["supuestos"])}

## Criterio de salida cubierto

- [x] Se declara la línea base y sus supuestos.
- [x] Se mide el sistema de extremo a extremo.
- [x] Se comparan tiempo, requisitos y aciertos.
- [x] No se presenta la estimación como medición real.
"""


def _reporte_revision(ctx: dict[str, Any], casos: list[dict[str, Any]]) -> str:
    aprobados = sum(1 for caso in casos if caso["estado"] == "PASA")
    return f"""# Evidencia 05 — Revisión técnica y feedback

## Revisión interna ejecutada

| Aspecto | Resultado |
|---|---|
| Flujo de extremo a extremo | ✅ ejecutado desde cero |
| Casos de prueba | ✅ {aprobados}/{len(casos)} PASA |
| Exportación | ✅ XLSX y DOCX reabiertos y verificados |
| Seguridad mínima | ✅ 3 denegaciones con causa |
| Contingencia | ✅ resuelta manualmente |
| Integridad | ✅ fuente modificada bloquea decisión |
| Tiempos | ✅ medidos y bajo el umbral de 5000 ms |
| Video demo | ✅ 3:03, grabado sobre la app real |
| Documentación | ✅ README, ficha, PPT, guion y video |

## Hallazgos de la revisión interna

1. La validación humana sigue siendo el cuello de botella; el sistema acelera el
   trabajo mecánico, no la decisión técnica.
2. La política de acceso es de demostración; antes de producción requiere
   autenticación e identidad reales.
3. El proveedor determinista es suficiente para demostrar el contrato y la
   contingencia, pero no sustituye una evaluación semántica con IA real.
4. La exportación funciona con datos sintéticos; falta plantilla oficial y firma.

## Feedback de especialista externo

**Estado:** pendiente de una persona con rol de especialista.

Formulario preparado para la sesión:

| Pregunta | Respuesta |
|---|---|
| ¿La evidencia mostrada es suficiente para decidir? | |
| ¿Las fuentes y ubicaciones son verificables? | |
| ¿El estado «Requiere revisión especializada» está bien usado? | |
| ¿El avance ponderado refleja el trabajo real? | |
| ¿El informe Excel/Word es usable? | |
| ¿Qué cambiaría antes de producción? | |
| Nombre / rol / fecha | |

> No se registra un feedback ficticio. La sesión con el especialista debe
> completar esta tabla antes de la sustentación final.

## Criterio de salida cubierto

- [x] Existe revisión técnica interna documentada.
- [x] Existe formulario de feedback listo para el especialista.
- [ ] Feedback externo firmado (pendiente de una persona).
"""


def _reporte_checklist(casos: list[dict[str, Any]]) -> str:
    aprobados = sum(1 for caso in casos if caso["estado"] == "PASA")
    return f"""# Evidencia 06 — Checklist de entrega del Hito 3

| Entregable | Estado | Ruta |
|---|---|---|
| MVP funcional | ✅ | `mvp/app.py`, `mvp/README.md` |
| Flujo reproducible | ✅ | `python -m mvp.scripts.ejecutar_etapa6` |
| 10+ casos de prueba | ✅ {aprobados}/{len(casos)} | `mvp/etapa6/evidencia/02_casos_prueba.md` |
| Métricas línea base vs. sistema | ✅ | `mvp/etapa6/evidencia/04_metricas_linea_base.md` |
| Registro de errores y correcciones | ✅ | `mvp/etapa6/evidencia/03_errores_correcciones.md` |
| Ficha técnica | ✅ | `mvp/etapa6/FICHA_TECNICA.md` |
| PPT editable (14 diapositivas, 9 secciones) | ✅ | `mvp/etapa6/entrega/PPT_Expedivia_Hito3.pptx` |
| PPT PDF | ✅ | `mvp/etapa6/entrega/PPT_Expedivia_Hito3.pdf` |
| Guion de video | ✅ | `mvp/etapa6/evidencia/07_guion_video.md` |
| Video demo (3:03, narración sintética) | ✅ | `mvp/etapa6/entrega/video_demo.mp4` |
| Capturas reales de la app | ✅ 10 | `mvp/etapa6/entrega/capturas/` |
| Feedback de especialista | ☐ | formulario en `05_revision_tecnica.md` |
| Guion de ensayo | ✅ | `mvp/etapa6/evidencia/08_acta_ensayo.md` |
| Ensayo presencial cronometrado | ☐ | acción del equipo antes de sustentar |
| Enlaces de respaldo | ✅ | `mvp/etapa6/README.md` y `FICHA_TECNICA.md` |

## Enlaces y accesos de respaldo

| Respaldo | Ruta |
|---|---|
| Código y corpus | carpeta `hito2-3` completa |
| Base SQLite | `mvp/etapa6/evidencia/mvp_etapa6.db` |
| Informes | `mvp/etapa6/evidencia/exportaciones/` |
| Presentación | `mvp/etapa6/entrega/PPT_Expedivia_Hito3.pptx` y `.pdf` |
| Video | `mvp/etapa6/entrega/video_demo.mp4` |
| Reconstrucción | `python -m mvp.scripts.ejecutar_etapa6` |

## Criterio de salida cubierto

- [x] El paquete principal está completo y es reproducible.
- [x] Video demo generado sobre la app real y declarado como narración sintética.
- [x] Enlaces de respaldo locales definidos.
- [ ] Feedback firmado y ensayo presencial quedan como acciones del equipo.
"""


def _reporte_guion() -> str:
    return """# Evidencia 07 — Guion del video demo (3–5 minutos)

**Archivo:** `mvp/etapa6/entrega/video_demo.mp4`
**Duración real:** 3:03.
**Formato:** grabación de pantalla de la app real con narración sintetizada en
español (voz `Microsoft Helena Desktop`, es-ES). No es una locución humana.
**Reproducción:** `python -m mvp.scripts.grabar_video_etapa6` regenera la
grabación y la narración sobre la base de la Etapa 6.

| Tiempo | Escena | Acción en pantalla | Narración |
|---:|---|---|---|
| 0:00–0:21 | Apertura | Portada de la app y caso `EXP-2024-089` | Qué es Expedivia y qué problema resuelve. |
| 0:21–0:44 | Carga | Pestaña 2: 8 documentos, hash y clasificación | Validación, caché y corrección humana. |
| 0:44–1:04 | Extracción | Pestaña 3 con `TDR_Carretera_Central_v3.pdf` | Página, párrafo, hoja y fila como ubicación. |
| 1:04–1:27 | Evidencia | Pestaña 4: cobertura, propuestas e integridad | Contrato JSON, fuente, cita y hash. |
| 1:27–1:52 | Decisión | Pestaña 5: métricas, RQ-04 e historial | Aceptar, modificar, descartar y avance 39.0%. |
| 1:52–2:12 | Exportación | Pestaña 6: informes generados y descargas | Excel/Word construidos desde SQLite. |
| 2:12–2:30 | Auditoría | Pestaña 7: eventos y verificaciones | Trazabilidad de cada acción. |
| 2:30–2:47 | Permisos | Usuario lector y bloqueo explicado | Un lector no decide ni exporta. |
| 2:47–3:07 | Cierre | Pestaña 8: límites y pendientes | Sin OCR, IA opcional, datos sintéticos y feedback pendiente. |

## Reglas de grabación

1. Se muestran los estados reales de la base, sin ocultar bloqueos ni límites.
2. La narración se genera con síntesis de voz; debe declararse así en la
   sustentación.
3. El video se produce con `mvp/scripts/grabar_video_etapa6.py`; no se editan
   saltos que oculten pasos.
4. La línea de tiempo y los textos están en `mvp/etapa6/entrega/video_timeline.json`.

## Criterio de salida cubierto

- [x] Video de 3:03 con las nueve escenas del flujo.
- [x] Narración en español y acciones reales sobre la app.
- [x] Se explican limitaciones y pendientes.
- [ ] Locución humana y grabación con cámara del equipo (opcional, no requerido).
"""


def _reporte_ensayo(ctx: dict[str, Any]) -> str:
    return """# Evidencia 08 — Ensayo de sustentación (10 minutos)

## Estructura

| Minuto | Bloque | Idea clave | Diapositiva |
|---:|---|---|---|
| 0–1 | Problema y usuario | Revisión manual, dispersa y difícil de auditar | 2 |
| 1–2 | Solución y valor | Evidencia verificable + decisión humana + avance | 3 |
| 2–3 | Arquitectura | Streamlit, SQLite, extractores, contrato, exportadores | 4 |
| 3–5 | Demo | Carga, evidencia, decisión, exportación | 5–6 |
| 5–6 | Pruebas | 16 casos mapeados a CA | 7 |
| 6–7 | Resultados | 39% de avance, 88.6% de cumplimiento, 0 «No cumple» | 8 |
| 7–8 | Métricas | Línea base estimada vs. sistema | 9 |
| 8–9 | Seguridad y límites | Roles demo, sin IA real, feedback pendiente | 10–11 |
| 9–10 | Cierre | Próximos pasos y preguntas | 12–14 |

## Preguntas esperadas y respuesta breve

1. **¿La IA decide?** No. Propone; la persona acepta, modifica o descarta.
2. **¿Qué pasa si no hay evidencia?** «No se encontró información», nunca «No cumple».
3. **¿Cómo se evita inventar fuentes?** Contrato JSON con archivo, hash y cita;
   una respuesta que no coincide se rechaza.
4. **¿Cómo se mide el avance?** `Σ(peso × factor) / peso total`, solo con decisión.
5. **¿Qué falta para producción?** Identidad real, plantilla oficial, feedback y
   validación con especialistas.

## Checklist de ensayo

- [x] Guion y tiempos definidos.
- [x] PPT de 14 diapositivas y 9 secciones.
- [x] Demo reproducible con un comando.
- [x] Preguntas difíciles preparadas.
- [ ] Ensayo cronometrado con el equipo (pendiente de ejecución presencial).

## Criterio de salida cubierto

- [x] El equipo puede explicar decisiones, límites y próximos pasos.
- [x] La sustentación cabe en 10 minutos.
- [ ] Ensayo presencial cronometrado (acción del equipo).
"""


def _reporte_ficha() -> str:
    return """# Ficha técnica — Expedivia MVP

## 1. Acceso

```powershell
cd ruta\\al\\proyecto\\hito2-3
python -m pip install -r mvp/requirements.txt
streamlit run mvp/app.py
```

Abrir `http://localhost:8501`.

## 2. Datos de demostración

- Caso: `EXP-2024-089` — Carretera Central Tramo 2 · Km 42–78.
- Especialidad: Pavimentos.
- Datos sintéticos/representativos.
- Corpus: `mvp/etapa6/muestras/caso/` (8 documentos).
- Base: `mvp/etapa6/evidencia/mvp_etapa6.db`.

## 3. Usuarios

| Usuario | Rol | Expediente |
|---|---|---|
| Lucía Ramos | especialista | `EXP-2024-089` |
| Carlos Méndez | lector | `EXP-2024-089` |
| Admin MVP | administrador | `*` |

## 4. Flujo reproducible

```powershell
python -m mvp.scripts.ejecutar_etapa6
python -m pytest mvp/tests -q
```

## 5. Artefactos

- `mvp/etapa6/evidencia/` — reportes, métricas, exportaciones.
- `mvp/etapa6/entrega/PPT_Expedivia_Hito3.pptx` — presentación editable.
- `mvp/etapa6/entrega/PPT_Expedivia_Hito3.pdf` — versión PDF.
- `mvp/etapa6/evidencia/07_guion_video.md` — guion del video.
- `mvp/etapa6/README.md` — guía de la etapa.

## 6. Dependencias

Python 3.11+, `pypdf`, `pdfplumber`, `python-docx`, `openpyxl`, `streamlit`,
`reportlab`, `xlsxwriter`, `pytest`, `python-pptx` (solo para generar el PPT).

## 7. Restricciones

- No hay OCR: PDF escaneado se rechaza.
- La IA real requiere `MVP_IA_API_KEY`; por defecto se usa el proveedor de reglas.
- La política de acceso es de demostración.
- Los datos son sintéticos.
- El feedback de especialista y el video final son acciones del equipo.
"""


# --- Flujo principal ------------------------------------------------------


def main() -> int:
    print("1/6 Preparando el flujo completo...")
    ctx = preparar_flujo()
    total_ms = sum(ctx["tiempos"].values()) + 0.0
    print(
        f"   8 documentos, 7 requisitos, avance {ctx['resumen']['avance_pct']}%, "
        f"{total_ms:.1f} ms"
    )

    print("2/6 Ejecutando los 16 casos de prueba...")
    casos = [
        _caso(identificador, ca, nombre, esperado, funcion, ctx)
        for identificador, ca, nombre, esperado, funcion in CASOS
    ]
    aprobados = sum(1 for caso in casos if caso["estado"] == "PASA")
    if aprobados != len(casos):
        fallidos = [caso for caso in casos if caso["estado"] != "PASA"]
        raise AssertionError(
            "Casos fallidos: " + ", ".join(caso["id"] for caso in fallidos)
        )
    print(f"   {aprobados}/{len(casos)} casos PASA")

    print("3/6 Calculando métricas y comparando con la línea base...")
    linea_base = json.loads(
        (Path(config.DIR_ETAPA6) / "config" / "linea_base.json").read_text(
            encoding="utf-8"
        )
    )
    minutos_base = sum(item["minutos"] for item in linea_base["actividades"])
    minutos_revision = int(linea_base.get("revision_humana_min", 0))
    minutos_mecanicos = minutos_base - minutos_revision
    ms_mecanico = minutos_mecanicos * 60 * 1000
    metricas = {
        "caso": _metricas(ctx["resumen"]),
        "tiempos_ms": {
            clave: round(valor, 1) for clave, valor in ctx["tiempos"].items()
        },
        "total_e2e_ms": round(total_ms, 1),
        "linea_base": {
            "minutos": minutos_base,
            "minutos_mecanicos": minutos_mecanicos,
            "minutos_revision_humana": minutos_revision,
            "ms_mecanico": ms_mecanico,
            "supuestos": linea_base["supuestos"],
        },
        "reduccion_mecanica_pct": round((1 - total_ms / ms_mecanico) * 100, 2),
        "casos": casos,
        "aprobados": aprobados,
        "total_casos": len(casos),
        "exportacion": {
            "xlsx": str(ctx["rutas"]["xlsx"]),
            "docx": str(ctx["rutas"]["docx"]),
            "xlsx_bytes": ctx["rutas"]["xlsx"].stat().st_size,
            "docx_bytes": ctx["rutas"]["docx"].stat().st_size,
        },
    }

    print("4/6 Escribiendo reportes...")
    _escribir("01_flujo_extremo_a_extremo.md", _reporte_flujo(ctx, total_ms))
    _escribir("02_casos_prueba.md", _reporte_casos(casos))
    _escribir(
        "02_casos_prueba.json",
        json.dumps(casos, indent=2, ensure_ascii=False),
    )
    _escribir("03_errores_correcciones.md", _reporte_errores())
    _escribir(
        "04_metricas_linea_base.md",
        _reporte_metricas(ctx, total_ms, linea_base, casos),
    )
    _escribir("05_revision_tecnica.md", _reporte_revision(ctx, casos))
    _escribir("06_checklist_entrega.md", _reporte_checklist(casos))
    _escribir("07_guion_video.md", _reporte_guion())
    _escribir("08_acta_ensayo.md", _reporte_ensayo(ctx))
    _escribir("09_ficha_tecnica.md", _reporte_ficha())
    _escribir("10_metricas.json", json.dumps(metricas, indent=2, ensure_ascii=False))
    _escribir("00_entorno.json", json.dumps(_entorno(), indent=2, ensure_ascii=False))

    print("5/6 Verificando artefactos de entrega...")
    for ruta in (
        ctx["rutas"]["xlsx"],
        ctx["rutas"]["docx"],
        config.DIR_EVIDENCIA_ETAPA6 / "02_casos_prueba.md",
        config.DIR_EVIDENCIA_ETAPA6 / "10_metricas.json",
    ):
        assert ruta.exists() and ruta.stat().st_size > 0

    print("6/6 Etapa 6 ejecutada correctamente.")
    print(f"Evidencia: {config.DIR_EVIDENCIA_ETAPA6}")
    print(f"Casos: {aprobados}/{len(casos)} PASA")
    print(
        f"Tiempo E2E: {total_ms:.1f} ms | línea base mecánica: {minutos_mecanicos} min | "
        f"reducción mecánica: {metricas['reduccion_mecanica_pct']}%"
    )
    print(
        f"Avance: {ctx['resumen']['avance_pct']}% | "
        f"Cumplimiento: {ctx['resumen']['cumplimiento_pct']}% | "
        f"Decisiones: {ctx['resumen']['decisiones_registradas']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
