"""Exportación real a Excel y Word (Etapa 5).

Ambos formatos se construyen desde la base SQLite, no desde datos fijos:

- **Excel**: resumen, requisitos, decisiones, propuestas, evidencias, documentos
  y auditoría, con encabezados, filtros y anchos legibles.
- **Word**: informe con metadatos, resumen ejecutivo, resultados por requisito,
  observaciones con fuentes y historial de decisiones.

Los archivos generados se abren con ``openpyxl`` y ``python-docx`` en las
pruebas de aceptación.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document
from docx.shared import Pt
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from . import db
from .analysis import AnalizadorExpediente
from .evaluation import EvaluadorExpediente


# --- Utilidades -----------------------------------------------------------


def _datos_expediente(ruta_bd: str | Path, expediente_id: str) -> dict[str, Any]:
    with db.conectar(ruta_bd) as conexion:
        fila = conexion.execute(
            "SELECT * FROM expedientes WHERE id = ?", (expediente_id,)
        ).fetchone()
    return db.fila_a_dict(fila) or {"id": expediente_id, "nombre": expediente_id}


def _texto(valor: Any, limite: int = 500) -> str:
    texto = "" if valor is None else str(valor)
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"


def _encabezado(hoja, columnas: list[str]) -> None:
    hoja.append(columnas)
    relleno = PatternFill("solid", fgColor="1F4E78")
    for celda in hoja[1]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = relleno
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    hoja.freeze_panes = "A2"
    hoja.auto_filter.ref = hoja.dimensions


def _anchos(hoja, anchos: list[int]) -> None:
    for indice, ancho in enumerate(anchos, start=1):
        hoja.column_dimensions[get_column_letter(indice)].width = ancho


def _metricas(resumen: dict[str, Any]) -> list[tuple[str, Any]]:
    return [
        ("Expediente", resumen["expediente_id"]),
        ("Requisitos", resumen["requisitos_total"]),
        ("Peso total", f"{resumen['peso_total_pct']}%"),
        ("Cobertura de revisión", f"{resumen['cobertura_revision_pct']}%"),
        ("Peso decidido", f"{resumen['peso_decidido_pct']}%"),
        ("Avance ponderado", f"{resumen['avance_pct']}%"),
        (
            "Cumplimiento ponderado",
            f"{resumen['cumplimiento_pct']}%"
            if resumen["cumplimiento_pct"] is not None
            else "—",
        ),
        ("Decisiones vigentes", resumen["decisiones_registradas"]),
        ("Aceptadas", resumen["aceptadas"]),
        ("Modificadas", resumen["modificadas"]),
        ("Descartadas", resumen["descartadas"]),
        ("Cumple", resumen["cumple"]),
        ("Cumple parcialmente", resumen["parcial"]),
        ("No cumple", resumen["no_cumple"]),
        ("No se encontró información", resumen["sin_informacion"]),
        ("Requiere revisión especializada", resumen["requiere_revision"]),
        ("Alertas de integridad", resumen["integridad_alertas"]),
    ]


def _mejor_evidencia(
    analizador: AnalizadorExpediente, expediente_id: str, requisito_id: str
) -> dict[str, Any] | None:
    evidencias = analizador.evidencias(expediente_id, requisito_id)
    return evidencias[0] if evidencias else None


# --- Excel ----------------------------------------------------------------


def exportar_excel(
    ruta_bd: str | Path,
    expediente_id: str,
    destino: str | Path,
) -> Path:
    """Genera un ``.xlsx`` con los resultados reales del expediente."""

    analizador = AnalizadorExpediente(ruta_bd)
    evaluador = EvaluadorExpediente(ruta_bd)
    expediente = _datos_expediente(ruta_bd, expediente_id)
    resumen = analizador.resumen(expediente_id)
    historial = evaluador.historial(expediente_id)
    propuestas = analizador.propuestas(expediente_id, limite=1000)
    documentos = analizador.procesador.listar_documentos(expediente_id)

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    libro = Workbook()

    # 1. Resumen
    hoja = libro.active
    hoja.title = "Resumen"
    hoja["A1"] = "Informe de revisión de expediente técnico"
    hoja["A1"].font = Font(bold=True, size=16, color="1F4E78")
    hoja.merge_cells("A1:D1")
    hoja["A2"] = expediente.get("nombre") or expediente_id
    hoja["A2"].font = Font(bold=True, size=12)
    hoja.merge_cells("A2:D2")
    hoja["A3"] = (
        f"Expediente: {expediente_id} · Especialidad: "
        f"{expediente.get('especialidad') or '—'} · Versión: "
        f"{expediente.get('version') or '—'}"
    )
    hoja["A4"] = f"Generado: {datetime.now().isoformat(timespec='seconds')}"
    hoja["A4"].font = Font(italic=True, size=9)

    fila = 6
    hoja.cell(row=fila, column=1, value="Métrica").font = Font(bold=True)
    hoja.cell(row=fila, column=2, value="Valor").font = Font(bold=True)
    for etiqueta, valor in _metricas(resumen):
        fila += 1
        hoja.cell(row=fila, column=1, value=etiqueta)
        hoja.cell(row=fila, column=2, value=valor)
    fila += 2
    hoja.cell(row=fila, column=1, value="Fórmula de avance").font = Font(bold=True)
    hoja.cell(row=fila, column=2, value=resumen["avance_formula"])
    hoja.column_dimensions["A"].width = 34
    hoja.column_dimensions["B"].width = 68

    # 2. Requisitos
    hoja = libro.create_sheet("Requisitos")
    _encabezado(
        hoja,
        [
            "Req.",
            "Requisito",
            "Peso %",
            "Criterio",
            "Evidencias",
            "Estado propuesto",
            "Decisión",
            "Estado final",
            "Origen",
            "Responsable",
            "Fecha decisión",
            "Motivo",
            "Fuente",
            "Ubicación",
            "Cita",
        ],
    )
    for detalle in resumen["requisitos"]:
        evidencia = _mejor_evidencia(
            analizador, expediente_id, detalle["requisito_id"]
        )
        hoja.append(
            [
                detalle["requisito_id"],
                detalle["requisito"],
                detalle["peso_pct"],
                detalle["criterio"],
                detalle["evidencias"],
                detalle["estado_propuesto"] or "—",
                detalle["decision"] or "sin decidir",
                detalle["estado_efectivo"],
                detalle["origen"],
                detalle["decision_actor"] or "—",
                detalle["decision_fecha"] or "—",
                _texto(detalle["motivo"], 500),
                evidencia["archivo"] if evidencia else "—",
                evidencia["ubicacion"] if evidencia else "—",
                _texto(evidencia["texto"], 300) if evidencia else "—",
            ]
        )
    _anchos(hoja, [8, 26, 8, 34, 10, 26, 14, 28, 16, 16, 20, 52, 26, 24, 48])
    for fila_datos in hoja.iter_rows(min_row=2):
        for celda in fila_datos:
            celda.alignment = Alignment(vertical="top", wrap_text=True)

    # 3. Decisiones
    hoja = libro.create_sheet("Decisiones")
    _encabezado(
        hoja,
        [
            "ID",
            "Req.",
            "Decisión",
            "Estado propuesto",
            "Estado final",
            "Motivo",
            "Responsable",
            "Versión",
            "Vigente",
            "Archivo",
            "Ubicación",
            "Cita",
            "Fecha",
            "Huella",
        ],
    )
    for registro in historial:
        hoja.append(
            [
                registro["id"],
                registro["requisito_id"],
                registro["decision"],
                registro["estado_propuesto"],
                registro["estado_final"],
                _texto(registro["motivo"], 500),
                registro["actor"],
                registro.get("version_kb") or "—",
                "sí" if registro["es_vigente"] else "no",
                registro.get("archivo") or "—",
                registro.get("ubicacion") or "—",
                _texto(registro.get("cita"), 300),
                registro["creado_en"],
                registro.get("huella_propuesta") or "—",
            ]
        )
    _anchos(hoja, [6, 8, 12, 28, 28, 50, 16, 10, 9, 24, 22, 40, 20, 20])

    # 4. Propuestas
    hoja = libro.create_sheet("Propuestas")
    _encabezado(
        hoja,
        [
            "ID",
            "Req.",
            "Proveedor",
            "Modelo",
            "Estado propuesto",
            "Válida",
            "Integridad",
            "Archivo",
            "Ubicación",
            "SHA-256",
            "Cita",
            "Observación",
            "Huella",
            "Creado",
        ],
    )
    for propuesta in propuestas:
        hoja.append(
            [
                propuesta["id"],
                propuesta["requisito_id"],
                propuesta["proveedor"],
                propuesta.get("modelo") or "—",
                propuesta.get("estado_propuesto") or "—",
                "sí" if propuesta["valida"] else "no",
                propuesta.get("integridad") or "—",
                propuesta.get("archivo") or "—",
                propuesta.get("ubicacion") or "—",
                propuesta.get("sha256_fuente") or "—",
                _texto(propuesta.get("cita"), 300),
                _texto(propuesta.get("observacion"), 300),
                propuesta.get("huella") or "—",
                propuesta["creado_en"],
            ]
        )
    _anchos(hoja, [6, 8, 18, 18, 26, 8, 18, 24, 22, 24, 40, 40, 20, 20])

    # 5. Evidencias
    hoja = libro.create_sheet("Evidencias")
    _encabezado(
        hoja,
        [
            "Req.",
            "Archivo",
            "Ubicación",
            "Tipo documental",
            "Puntaje",
            "SHA-256",
            "Integridad",
            "Texto",
            "Creado",
        ],
    )
    for requisito_id in analizador.perfiles.ids():
        for evidencia in analizador.evidencias(expediente_id, requisito_id):
            hoja.append(
                [
                    requisito_id,
                    evidencia["archivo"],
                    evidencia["ubicacion"],
                    evidencia["tipo_documental"],
                    evidencia["puntaje"],
                    evidencia["sha256_fuente"],
                    evidencia["integridad"],
                    _texto(evidencia["texto"], 500),
                    evidencia["creado_en"],
                ]
            )
    _anchos(hoja, [8, 26, 24, 26, 9, 24, 18, 70, 20])

    # 6. Documentos
    hoja = libro.create_sheet("Documentos")
    _encabezado(
        hoja,
        [
            "ID",
            "Archivo",
            "Formato",
            "Estado",
            "Texto",
            "Tipo documental",
            "Componente",
            "Confianza",
            "Clasificación",
            "SHA-256",
            "Fragmentos",
        ],
    )
    for documento in documentos:
        hoja.append(
            [
                documento["id"],
                documento["nombre_archivo"],
                documento["formato"],
                documento["estado"],
                documento.get("texto_recuperable") or "—",
                documento.get("tipo_documental") or "—",
                documento.get("componente") or "—",
                documento.get("confianza"),
                documento.get("estado_clasificacion") or "—",
                documento.get("sha256") or "—",
                documento.get("fragmentos"),
            ]
        )
    _anchos(hoja, [6, 30, 9, 10, 10, 28, 16, 10, 16, 24, 10])

    # 7. Auditoría
    hoja = libro.create_sheet("Auditoría")
    _encabezado(hoja, ["Fecha", "Actor", "Acción", "Entidad", "ID", "Detalle"])
    for registro in analizador.procesador.listar_auditoria(1000):
        hoja.append(
            [
                registro["ts"],
                registro["actor"],
                registro["accion"],
                registro["entidad"],
                registro["entidad_id"],
                _texto(registro["detalle"], 500),
            ]
        )
    _anchos(hoja, [20, 18, 30, 16, 22, 80])

    libro.save(destino)
    return destino


# --- Word -----------------------------------------------------------------


def _tabla_word(documento, cabeceras: list[str], filas: list[list[Any]]) -> None:
    tabla = documento.add_table(rows=1, cols=len(cabeceras))
    tabla.style = "Table Grid"
    for indice, cabecera in enumerate(cabeceras):
        celda = tabla.rows[0].cells[indice]
        celda.text = cabecera
        for parrafo in celda.paragraphs:
            for ejecucion in parrafo.runs:
                ejecucion.bold = True
    for fila in filas:
        celdas = tabla.add_row().cells
        for indice, valor in enumerate(fila):
            celdas[indice].text = "" if valor is None else str(valor)
    documento.add_paragraph()


def exportar_word(
    ruta_bd: str | Path,
    expediente_id: str,
    destino: str | Path,
) -> Path:
    """Genera un ``.docx`` con observaciones, decisiones y fuentes."""

    analizador = AnalizadorExpediente(ruta_bd)
    evaluador = EvaluadorExpediente(ruta_bd)
    expediente = _datos_expediente(ruta_bd, expediente_id)
    resumen = analizador.resumen(expediente_id)
    historial = evaluador.historial(expediente_id)

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    documento = Document()

    estilo = documento.styles["Normal"]
    estilo.font.name = "Calibri"
    estilo.font.size = Pt(10)

    documento.add_heading("Informe de revisión de expediente técnico", level=0)
    documento.add_paragraph(
        f"Expediente: {expediente_id}\n"
        f"Nombre: {expediente.get('nombre') or '—'}\n"
        f"Especialidad: {expediente.get('especialidad') or '—'}\n"
        f"Versión: {expediente.get('version') or '—'}\n"
        f"Generado: {datetime.now().isoformat(timespec='seconds')}"
    )

    documento.add_heading("1. Resumen ejecutivo", level=1)
    if resumen["decisiones_registradas"] == 0:
        documento.add_paragraph(
            "El expediente tiene propuestas automáticas, pero todavía no cuenta con "
            "decisiones humanas registradas. El avance validado es 0%."
        )
    else:
        documento.add_paragraph(
            f"Se revisaron {resumen['requisitos_total']} requisitos. Hay "
            f"{resumen['decisiones_registradas']} decisiones vigentes: "
            f"{resumen['aceptadas']} aceptadas, {resumen['modificadas']} modificadas "
            f"y {resumen['descartadas']} descartadas."
        )
    _tabla_word(
        documento,
        ["Métrica", "Valor"],
        [[etiqueta, valor] for etiqueta, valor in _metricas(resumen)],
    )
    documento.add_paragraph(f"Fórmula de avance: {resumen['avance_formula']}")

    documento.add_heading("2. Resultados por requisito", level=1)
    _tabla_word(
        documento,
        ["Req.", "Peso", "Estado final", "Decisión", "Responsable", "Motivo"],
        [
            [
                detalle["requisito_id"],
                f"{detalle['peso_pct']}%",
                detalle["estado_efectivo"],
                detalle["decision"] or "sin decidir",
                detalle["decision_actor"] or "—",
                _texto(detalle["motivo"], 220),
            ]
            for detalle in resumen["requisitos"]
        ],
    )

    documento.add_heading("3. Observaciones y fuentes", level=1)
    for detalle in resumen["requisitos"]:
        documento.add_heading(
            f"{detalle['requisito_id']} · {detalle['requisito']}", level=2
        )
        documento.add_paragraph(
            f"Criterio: {detalle['criterio']}\n"
            f"Estado propuesto: {detalle['estado_propuesto'] or '—'}\n"
            f"Estado final: {detalle['estado_efectivo']}\n"
            f"Decisión: {detalle['decision'] or 'sin decidir'}\n"
            f"Motivo: {detalle['motivo'] or '—'}"
        )
        evidencias = analizador.evidencias(expediente_id, detalle["requisito_id"])
        if not evidencias:
            documento.add_paragraph("Sin evidencia persistida para este requisito.")
            continue
        for indice, evidencia in enumerate(evidencias[:3], start=1):
            documento.add_paragraph(
                f"Fuente {indice}: {evidencia['archivo']} · "
                f"{evidencia['ubicacion']} ({evidencia['tipo_documental']}). "
                f"SHA-256: {evidencia['sha256_fuente'][:16]}… "
                f"Integridad: {evidencia['integridad']}."
            )
            documento.add_paragraph(
                f"Cita: {_texto(evidencia['texto'], 400)}", style="Intense Quote"
            )

    documento.add_heading("4. Historial de decisiones", level=1)
    if not historial:
        documento.add_paragraph("Sin decisiones registradas.")
    else:
        _tabla_word(
            documento,
            ["Fecha", "Req.", "Decisión", "Propuesto", "Final", "Responsable", "Vigente"],
            [
                [
                    registro["creado_en"],
                    registro["requisito_id"],
                    registro["decision"],
                    registro["estado_propuesto"],
                    registro["estado_final"],
                    registro["actor"],
                    "sí" if registro["es_vigente"] else "no",
                ]
                for registro in historial
            ],
        )

    documento.add_heading("5. Alcance y limitaciones", level=1)
    documento.add_paragraph(
        "Los datos del caso son sintéticos y representativos. La conclusión "
        "automática no sustituye el juicio del especialista: los requisitos que "
        "exigen ingeniería se escalan. La ausencia de evidencia se registra como "
        "«No se encontró información», nunca como «No cumple»."
    )

    documento.add_paragraph()
    documento.add_paragraph("____________________________")
    documento.add_paragraph("Especialista responsable")
    documento.add_paragraph("____________________________")
    documento.add_paragraph("Fecha")

    documento.save(destino)
    return destino


def exportar_informes(
    ruta_bd: str | Path,
    expediente_id: str,
    carpeta: str | Path,
) -> dict[str, Path]:
    """Genera ambos formatos y devuelve sus rutas."""

    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    return {
        "xlsx": exportar_excel(
            ruta_bd, expediente_id, carpeta / f"informe_{expediente_id}.xlsx"
        ),
        "docx": exportar_word(
            ruta_bd, expediente_id, carpeta / f"informe_{expediente_id}.docx"
        ),
    }
