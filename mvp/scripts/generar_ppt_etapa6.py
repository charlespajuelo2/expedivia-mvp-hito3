"""Genera la presentación final del Hito 3 (14 diapositivas, 9 secciones)."""

from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

RAIZ = Path(__file__).resolve().parents[2]
DIR_ETAPA6 = RAIZ / "mvp" / "etapa6"
ENTREGA = DIR_ETAPA6 / "entrega"
CAPTURAS = ENTREGA / "capturas"
SALIDA = ENTREGA / "PPT_Expedivia_Hito3.pptx"

FONT = "Segoe UI"
NAVY = RGBColor(0x0F, 0x1E, 0x35)
NAVY_2 = RGBColor(0x1B, 0x2E, 0x4B)
AMBER = RGBColor(0xF2, 0xA3, 0x3C)
TEAL = RGBColor(0x2F, 0xBF, 0x9F)
LIGHT = RGBColor(0xF4, 0xF6, 0xFA)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRAY = RGBColor(0x5A, 0x6B, 0x82)
LINE = RGBColor(0xD9, 0xDF, 0xE8)
RED = RGBColor(0xC0, 0x54, 0x4C)

ANCHO = Inches(13.333)
ALTO = Inches(7.5)


def _metricas() -> dict:
    """Lee la medición real para no dejar cifras fijas en la diapositiva."""
    ruta = DIR_ETAPA6 / "evidencia" / "10_metricas.json"
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _slide(prs: Presentation):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _rect(slide, l, t, w, h, fill, line=None, radius=True, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    forma = slide.shapes.add_shape(shape, l, t, w, h)
    forma.fill.solid()
    forma.fill.fore_color.rgb = fill
    if line is None:
        forma.line.fill.background()
    else:
        forma.line.color.rgb = line
        forma.line.width = Pt(1)
    forma.shadow.inherit = False
    if radius:
        try:
            forma.adjustments[0] = 0.08
        except (IndexError, ValueError):
            pass
    return forma


def _text(
    slide,
    l,
    t,
    w,
    h,
    texto,
    *,
    size=18,
    bold=False,
    color=NAVY,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
    spacing=0,
    font=FONT,
    italic=False,
):
    caja = slide.shapes.add_textbox(l, t, w, h)
    tf = caja.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    parrafo = tf.paragraphs[0]
    parrafo.alignment = align
    if spacing:
        parrafo.space_after = Pt(spacing)
    run = parrafo.add_run()
    run.text = texto
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return caja


def _bullets(slide, l, t, w, h, items, size=17, color=NAVY_2, gap=9):
    caja = slide.shapes.add_textbox(l, t, w, h)
    tf = caja.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for indice, item in enumerate(items):
        parrafo = tf.paragraphs[0] if indice == 0 else tf.add_paragraph()
        parrafo.space_after = Pt(gap)
        parrafo.line_spacing = 1.12
        if isinstance(item, tuple):
            texto, negrita = item
        else:
            texto, negrita = item, False
        run = parrafo.add_run()
        run.text = f"•  {texto}"
        run.font.name = FONT
        run.font.size = Pt(size)
        run.font.bold = negrita
        run.font.color.rgb = color
    return caja


def _cabecera(slide, seccion: str, titulo: str, subtitulo: str | None = None):
    _text(slide, Inches(0.72), Inches(0.42), Inches(11.9), Inches(0.3), seccion.upper(), size=11, bold=True, color=AMBER)
    _text(slide, Inches(0.72), Inches(0.73), Inches(11.9), Inches(0.75), titulo, size=30, bold=True, color=NAVY)
    if subtitulo:
        _text(slide, Inches(0.72), Inches(1.43), Inches(11.6), Inches(0.35), subtitulo, size=14, color=GRAY)
    linea = slide.shapes.add_connector(1, Inches(0.72), Inches(1.75), Inches(12.62), Inches(1.75))
    linea.line.color.rgb = LINE
    linea.line.width = Pt(0.75)


def _pie(slide, numero: int):
    _text(slide, Inches(0.72), Inches(7.08), Inches(6), Inches(0.25), "Expedivia · Hito 3 · MVP funcional", size=9, color=GRAY)
    _text(slide, Inches(11.9), Inches(7.08), Inches(0.72), Inches(0.25), f"{numero:02d}", size=9, bold=True, color=GRAY, align=PP_ALIGN.RIGHT)


def _tarjeta(slide, l, t, w, h, valor, etiqueta, color=NAVY, fondo=LIGHT):
    _rect(slide, l, t, w, h, fondo)
    _text(slide, l + Inches(0.24), t + Inches(0.2), w - Inches(0.4), Inches(0.7), valor, size=30, bold=True, color=color)
    _text(slide, l + Inches(0.24), t + h - Inches(0.62), w - Inches(0.4), Inches(0.45), etiqueta, size=11, color=GRAY)


def _imagen(slide, ruta: Path, l, t, w, h, borde=True):
    marco = _rect(slide, l - Inches(0.04), t - Inches(0.04), w + Inches(0.08), h + Inches(0.08), WHITE, LINE)
    marco.shadow.inherit = False
    return slide.shapes.add_picture(str(ruta), l, t, width=w, height=h)


def _pastilla(slide, l, t, texto, color=AMBER, ancho=Inches(1.55)):
    _rect(slide, l, t, ancho, Inches(0.34), color)
    _text(slide, l, t + Inches(0.05), ancho, Inches(0.28), texto, size=10, bold=True, color=NAVY, align=PP_ALIGN.CENTER)


def _flecha(slide, l, t, w, h, color=LINE):
    forma = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, l, t, w, h)
    forma.fill.solid()
    forma.fill.fore_color.rgb = color
    forma.line.fill.background()
    forma.shadow.inherit = False


def _tabla(slide, l, t, w, h, filas, anchos, size=12):
    tabla = slide.shapes.add_table(len(filas), len(anchos), l, t, w, h).table
    for indice, ancho in enumerate(anchos):
        tabla.columns[indice].width = ancho
    for fila, valores in enumerate(filas):
        for columna, valor in enumerate(valores):
            celda = tabla.cell(fila, columna)
            celda.text = str(valor)
            celda.margin_left = Inches(0.1)
            celda.margin_right = Inches(0.08)
            celda.margin_top = Inches(0.05)
            celda.margin_bottom = Inches(0.05)
            celda.vertical_anchor = MSO_ANCHOR.MIDDLE
            celda.fill.solid()
            celda.fill.fore_color.rgb = NAVY if fila == 0 else (WHITE if fila % 2 else LIGHT)
            for parrafo in celda.text_frame.paragraphs:
                for run in parrafo.runs:
                    run.font.name = FONT
                    run.font.size = Pt(size)
                    run.font.bold = fila == 0
                    run.font.color.rgb = WHITE if fila == 0 else NAVY_2


def crear() -> Path:
    prs = Presentation()
    prs.slide_width = ANCHO
    prs.slide_height = ALTO
    ENTREGA.mkdir(parents=True, exist_ok=True)

    # 1. Portada ------------------------------------------------------------
    slide = _slide(prs)
    _rect(slide, 0, 0, ANCHO, ALTO, NAVY, shape=MSO_SHAPE.RECTANGLE)
    _rect(slide, Inches(0), Inches(0), Inches(0.18), ALTO, AMBER, shape=MSO_SHAPE.RECTANGLE)
    _text(slide, Inches(0.95), Inches(0.8), Inches(5), Inches(0.3), "HITO 3 · MVP FUNCIONAL", size=12, bold=True, color=AMBER)
    _text(slide, Inches(0.95), Inches(1.55), Inches(7.4), Inches(1.3), "Expedivia", size=62, bold=True, color=WHITE)
    _text(
        slide,
        Inches(0.95),
        Inches(2.85),
        Inches(7.2),
        Inches(1.35),
        "Revisión de expedientes técnicos viales con evidencia verificable y decisión humana.",
        size=22,
        color=RGBColor(0xD7, 0xDF, 0xEB),
    )
    _rect(slide, Inches(0.95), Inches(4.55), Inches(1.3), Inches(0.05), AMBER)
    _text(slide, Inches(0.95), Inches(4.85), Inches(7), Inches(0.4), "Caso EXP-2024-089 · Carretera Central Tramo 2 · Km 42–78", size=14, color=WHITE)
    _text(slide, Inches(0.95), Inches(5.3), Inches(7), Inches(0.4), "Pavimentos · Datos sintéticos representativos", size=12, color=RGBColor(0xA9, 0xB7, 0xC9))
    _text(slide, Inches(0.95), Inches(6.55), Inches(7), Inches(0.35), "Equipo del proyecto · 12/11/2026", size=11, color=RGBColor(0xA9, 0xB7, 0xC9))

    for indice, (valor, etiqueta) in enumerate(
        [("8", "documentos"), ("7", "requisitos"), ("16/16", "casos PASA")]
    ):
        top = Inches(1.75 + indice * 1.45)
        _rect(slide, Inches(9.45), top, Inches(2.95), Inches(1.05), NAVY_2)
        _text(slide, Inches(9.7), top + Inches(0.12), Inches(2.5), Inches(0.5), valor, size=26, bold=True, color=AMBER)
        _text(slide, Inches(9.7), top + Inches(0.62), Inches(2.5), Inches(0.3), etiqueta, size=11, color=RGBColor(0xD7, 0xDF, 0xEB))

    # 2. Problema -----------------------------------------------------------
    slide = _slide(prs)
    _cabecera(slide, "1 · Problema y usuario", "La revisión técnica es manual, dispersa y difícil de auditar")
    _bullets(
        slide,
        Inches(0.72),
        Inches(1.95),
        Inches(6.6),
        Inches(4.2),
        [
            ("8 documentos en PDF, DOCX y XLSX por expediente.", False),
            ("La evidencia vive en una página, un párrafo o una fila de Excel.", False),
            ("El avance suele ser una opinión, no un cálculo trazable.", False),
            ("Sin fuente verificable, la conclusión no se puede sustentar.", False),
            ("La IA sin control puede inventar citas o conclusiones.", False),
        ],
        size=18,
    )
    _rect(slide, Inches(7.75), Inches(1.95), Inches(4.85), Inches(3.55), LIGHT)
    _rect(slide, Inches(7.75), Inches(1.95), Inches(0.09), Inches(3.55), AMBER)
    _text(slide, Inches(8.1), Inches(2.2), Inches(4.2), Inches(0.3), "LO QUE PIDE EL USUARIO", size=10, bold=True, color=AMBER)
    _text(
        slide,
        Inches(8.1),
        Inches(2.65),
        Inches(4.2),
        Inches(2.4),
        "«Necesito saber qué falta, con qué fuente y quién lo decidió. Y poder demostrarlo.»",
        size=20,
        italic=True,
        color=NAVY,
    )
    _text(slide, Inches(8.1), Inches(4.75), Inches(4.2), Inches(0.5), "Especialista en expedientes viales", size=11, color=GRAY)
    _text(slide, Inches(0.72), Inches(6.2), Inches(11.8), Inches(0.4), "El costo no es solo el tiempo: es la dificultad de defender una decisión sin rastro verificable.", size=13, color=GRAY)
    _pie(slide, 2)

    # 3. Usuario y checklist ------------------------------------------------
    slide = _slide(prs)
    _cabecera(slide, "1 · Problema y usuario", "Un usuario, un checklist y siete requisitos ponderados", "El especialista revisa, decide y sustenta. El sistema le quita el trabajo mecánico, no el criterio.")
    _rect(slide, Inches(0.72), Inches(1.95), Inches(3.9), Inches(4.35), LIGHT)
    _text(slide, Inches(1.0), Inches(2.18), Inches(3.3), Inches(0.3), "USUARIO PRINCIPAL", size=10, bold=True, color=AMBER)
    _text(slide, Inches(1.0), Inches(2.55), Inches(3.3), Inches(0.45), "Lucía Ramos", size=24, bold=True, color=NAVY)
    _text(slide, Inches(1.0), Inches(3.0), Inches(3.3), Inches(0.3), "Especialista · Pavimentos", size=12, color=GRAY)
    _bullets(
        slide,
        Inches(1.0),
        Inches(3.45),
        Inches(3.25),
        Inches(2.6),
        [
            "Revisa 8 documentos por expediente.",
            "Decide requisito por requisito.",
            "Debe explicar y sustentar cada conclusión.",
        ],
        size=13,
    )
    _text(slide, Inches(4.95), Inches(1.95), Inches(7.6), Inches(0.3), "CHECKLIST REPRESENTATIVO · PESOS QUE SUMAN 100%", size=10, bold=True, color=GRAY)
    requisitos = [
        ("RQ-01", "Experiencia del postor", 14),
        ("RQ-02", "Personal clave · Residente", 17),
        ("RQ-03", "Equipamiento mínimo", 11),
        ("RQ-04", "Presupuesto por partidas", 21),
        ("RQ-05", "Metrados y sustento", 14),
        ("RQ-06", "Cronograma valorizado", 10),
        ("RQ-07", "Plan de manejo ambiental", 13),
    ]
    for indice, (codigo, nombre, peso) in enumerate(requisitos):
        top = Inches(2.4 + indice * 0.53)
        _text(slide, Inches(4.95), top, Inches(0.7), Inches(0.3), codigo, size=11, bold=True, color=NAVY)
        _text(slide, Inches(5.65), top, Inches(3.9), Inches(0.3), nombre, size=12, color=NAVY_2)
        barra_fondo = _rect(slide, Inches(9.75), top + Inches(0.04), Inches(2.05), Inches(0.18), RGBColor(0xE6, 0xEB, 0xF2), radius=False, shape=MSO_SHAPE.RECTANGLE)
        barra = _rect(slide, Inches(9.75), top + Inches(0.04), Inches(2.05 * peso / 21), Inches(0.18), AMBER, radius=False, shape=MSO_SHAPE.RECTANGLE)
        _text(slide, Inches(11.95), top - Inches(0.02), Inches(0.6), Inches(0.3), f"{peso}%", size=11, bold=True, color=NAVY, align=PP_ALIGN.RIGHT)
    _text(slide, Inches(4.95), Inches(6.2), Inches(7.7), Inches(0.35), "La ponderación evita que un requisito menor bloquee la lectura global del expediente.", size=12, color=GRAY)
    _pie(slide, 3)

    # 4. Solución -----------------------------------------------------------
    slide = _slide(prs)
    _cabecera(slide, "2 · Solución", "Convertir documentos dispersos en evidencia decidible", "Cuatro pasos, una regla: nada se concluye sin fuente y sin responsable.")
    pasos = [
        ("1", "Carga", "Valida formato, calcula SHA-256 y reutiliza caché.", AMBER),
        ("2", "Evidencia", "Extrae texto y ubica página, párrafo o fila.", TEAL),
        ("3", "Decisión", "La persona acepta, modifica o descarta con motivo.", AMBER),
        ("4", "Informe", "Excel y Word se construyen desde SQLite.", TEAL),
    ]
    for indice, (numero, titulo, detalle, color) in enumerate(pasos):
        left = Inches(0.72 + indice * 3.03)
        _rect(slide, left, Inches(2.0), Inches(2.72), Inches(2.55), LIGHT)
        _rect(slide, left, Inches(2.0), Inches(2.72), Inches(0.08), color)
        _text(slide, left + Inches(0.22), Inches(2.22), Inches(0.5), Inches(0.4), numero, size=22, bold=True, color=color)
        _text(slide, left + Inches(0.22), Inches(2.75), Inches(2.3), Inches(0.4), titulo, size=18, bold=True, color=NAVY)
        _text(slide, left + Inches(0.22), Inches(3.25), Inches(2.3), Inches(1.1), detalle, size=12, color=NAVY_2)
    _rect(slide, Inches(0.72), Inches(4.95), Inches(11.85), Inches(1.25), NAVY)
    _rect(slide, Inches(0.72), Inches(4.95), Inches(0.1), Inches(1.25), AMBER)
    _text(slide, Inches(1.05), Inches(5.15), Inches(11.2), Inches(0.4), "Principio de diseño", size=11, bold=True, color=AMBER)
    _text(slide, Inches(1.05), Inches(5.5), Inches(11.2), Inches(0.5), "La IA propone; la persona decide. La ausencia de evidencia nunca se convierte en «No cumple».", size=17, color=WHITE)
    _text(slide, Inches(0.72), Inches(6.55), Inches(11.8), Inches(0.3), "Cada conclusión conserva archivo, ubicación, cita, hash y responsable de la decisión.", size=12, color=GRAY)
    _pie(slide, 4)

    # 5. Arquitectura -------------------------------------------------------
    slide = _slide(prs)
    _cabecera(slide, "3 · Arquitectura", "Una arquitectura pequeña, auditable y reproducible", "Streamlit + SQLite + extractores + exportadores. Sin servicios externos obligatorios.")
    cajas = [
        (0.72, "Interfaz", "Streamlit · 8 pestañas\nroles y bloqueos explicados", AMBER),
        (3.75, "Procesamiento", "pypdf · pdfplumber\npython-docx · openpyxl", TEAL),
        (6.78, "Datos", "SQLite\ndocumentos · evidencias\npropuestas · decisiones", AMBER),
        (9.81, "Salidas", "Excel 7 hojas\nWord 5 secciones\nCSV de decisiones", TEAL),
    ]
    for left, titulo, detalle, color in cajas:
        _rect(slide, Inches(left), Inches(2.05), Inches(2.65), Inches(1.85), LIGHT)
        _rect(slide, Inches(left), Inches(2.05), Inches(2.65), Inches(0.07), color)
        _text(slide, Inches(left + 0.22), Inches(2.28), Inches(2.2), Inches(0.35), titulo, size=16, bold=True, color=NAVY)
        _text(slide, Inches(left + 0.22), Inches(2.72), Inches(2.25), Inches(1.0), detalle, size=11, color=NAVY_2)
    for left in (3.4, 6.43, 9.46):
        _flecha(slide, Inches(left), Inches(2.82), Inches(0.3), Inches(0.28), RGBColor(0xC5, 0xCE, 0xDB))
    _rect(slide, Inches(0.72), Inches(4.25), Inches(7.3), Inches(1.35), WHITE, LINE)
    _text(slide, Inches(0.95), Inches(4.42), Inches(6.8), Inches(0.3), "SERVICIO DE IA OPCIONAL", size=10, bold=True, color=AMBER)
    _text(slide, Inches(0.95), Inches(4.75), Inches(6.8), Inches(0.7), "Contrato JSON estricto: archivo, ubicación, cita, hash y estado.\nSin clave se usa el proveedor determinista de reglas.", size=12, color=NAVY_2)
    _rect(slide, Inches(8.3), Inches(4.25), Inches(4.3), Inches(1.35), WHITE, LINE)
    _text(slide, Inches(8.53), Inches(4.42), Inches(3.9), Inches(0.3), "REPRODUCIBILIDAD", size=10, bold=True, color=TEAL)
    _text(slide, Inches(8.53), Inches(4.75), Inches(3.9), Inches(0.7), "Un comando reconstruye corpus, base, decisiones, informes y 16 casos.", size=12, color=NAVY_2)
    _text(slide, Inches(0.72), Inches(5.85), Inches(11.85), Inches(0.35), "python -m mvp.scripts.ejecutar_etapa6", size=14, bold=True, color=NAVY, font="Consolas")
    _text(slide, Inches(0.72), Inches(6.35), Inches(11.85), Inches(0.4), "La base es el contrato entre la interfaz, los cálculos y los informes. Nada se genera desde datos fijos.", size=12, color=GRAY)
    _pie(slide, 5)

    # 6. Demo 1 -------------------------------------------------------------
    slide = _slide(prs)
    _cabecera(slide, "4 · Demostración", "Del archivo a la evidencia verificable", "Carga, clasificación, extracción y recuperación sobre el caso real.")
    _imagen(slide, CAPTURAS / "03_extraccion.png", Inches(0.72), Inches(1.95), Inches(7.55), Inches(4.98))
    _bullets(
        slide,
        Inches(8.6),
        Inches(2.0),
        Inches(3.95),
        Inches(4.3),
        [
            ("SHA-256 identifica el archivo y evita duplicados.", False),
            ("El caché reutiliza la extracción sin perder inventario.", False),
            ("PDF conserva página; DOCX, párrafo; XLSX, hoja y fila.", False),
            ("La corrección humana de clasificación queda vinculada al hash.", False),
        ],
        size=14,
    )
    _text(slide, Inches(8.6), Inches(6.15), Inches(3.95), Inches(0.6), "8/8 documentos válidos · 0 duplicados", size=12, bold=True, color=TEAL)
    _pie(slide, 6)

    # 7. Demo 2 -------------------------------------------------------------
    slide = _slide(prs)
    _cabecera(slide, "4 · Demostración", "La decisión humana y el avance ponderado", "La propuesta es insumo; la decisión es del especialista.")
    _imagen(slide, CAPTURAS / "05_evaluacion.png", Inches(0.72), Inches(1.95), Inches(7.55), Inches(4.98))
    _bullets(
        slide,
        Inches(8.6),
        Inches(2.0),
        Inches(3.95),
        Inches(4.2),
        [
            ("Aceptar conserva el estado propuesto.", False),
            ("Modificar exige un estado final distinto y motivo.", False),
            ("Descartar deja «No se encontró información».", False),
            ("El historial es inmutable; solo una decisión vigente por requisito.", False),
            ("El avance solo suma decisiones humanas.", False),
        ],
        size=13,
    )
    _text(slide, Inches(8.6), Inches(6.15), Inches(3.95), Inches(0.6), "RQ-04: 3 registros · 4 decisiones vigentes", size=12, bold=True, color=TEAL)
    _pie(slide, 7)

    # 8. Resultados ---------------------------------------------------------
    slide = _slide(prs)
    _cabecera(slide, "5 · Resultados", "Resultados del caso EXP-2024-089", "8 documentos, 7 requisitos y 4 decisiones vigentes sobre el flujo real.")
    tarjetas = [
        ("100.0%", "Cobertura de revisión"),
        ("39.0%", "Avance ponderado"),
        ("88.6%", "Cumplimiento ponderado"),
        ("0", "Estados «No cumple»"),
    ]
    for indice, (valor, etiqueta) in enumerate(tarjetas):
        _tarjeta(slide, Inches(0.72 + indice * 3.03), Inches(1.98), Inches(2.72), Inches(1.5), valor, etiqueta, AMBER if indice < 2 else TEAL)
    _text(slide, Inches(0.72), Inches(3.85), Inches(6.1), Inches(0.3), "LECTURA DEL RESULTADO", size=10, bold=True, color=GRAY)
    _bullets(
        slide,
        Inches(0.72),
        Inches(4.22),
        Inches(6.6),
        Inches(2.1),
        [
            ("7/7 requisitos con propuesta válida y fuente.", False),
            ("4/7 requisitos decididos: 2 aceptados, 1 modificado, 1 descartado.", False),
            ("1 requisito queda «No se encontró información»: no se fuerza una conclusión.", False),
            ("6 registros de historial: la trazabilidad no se sobrescribe.", False),
        ],
        size=14,
    )
    _rect(slide, Inches(7.65), Inches(3.85), Inches(4.9), Inches(2.55), LIGHT)
    _text(slide, Inches(7.95), Inches(4.05), Inches(4.3), Inches(0.3), "FÓRMULA DEL AVANCE", size=10, bold=True, color=AMBER)
    _text(slide, Inches(7.95), Inches(4.42), Inches(4.3), Inches(0.9), "Σ(peso × factor) / Σ(pesos)", size=20, bold=True, color=NAVY, font="Consolas")
    _text(slide, Inches(7.95), Inches(5.25), Inches(4.35), Inches(0.95), "aceptar = 1.0\nmodificar = 0.5\ndescartar = 0.0", size=13, color=NAVY_2, font="Consolas")
    _text(slide, Inches(0.72), Inches(6.55), Inches(11.85), Inches(0.35), "El avance mide trabajo decidido; el cumplimiento solo considera estados concluyentes. Son métricas distintas a propósito.", size=12, color=GRAY)
    _pie(slide, 8)

    # 9. Pruebas ------------------------------------------------------------
    slide = _slide(prs)
    _cabecera(slide, "6 · Pruebas y métricas", "16 casos de prueba, 16 aprobados", "Cada caso está mapeado a un criterio de aceptación y corre sobre la base real.")
    _text(slide, Inches(0.72), Inches(1.95), Inches(2.4), Inches(0.9), "16/16", size=46, bold=True, color=TEAL)
    _text(slide, Inches(0.72), Inches(2.75), Inches(2.5), Inches(0.35), "casos PASA", size=13, bold=True, color=GRAY)
    _text(slide, Inches(0.72), Inches(3.35), Inches(2.55), Inches(2.7), "Carga, evidencia, IA, estados, decisiones, exportación, seguridad, contingencia, caché e integridad.", size=12, color=NAVY_2)
    filas = [
        ["Grupo", "Casos", "Cobertura"],
        ["Carga y extracción", "CP-01 a CP-04", "8/8 documentos, rechazo, clasificación, ubicación"],
        ["Evidencia y contrato IA", "CP-05 a CP-07", "Fuente, cita, hash, 7/7 propuestas"],
        ["Decisión e historial", "CP-08 a CP-09", "6 registros, 4 vigentes, avance 39.0%"],
        ["Informes", "CP-10 a CP-11", "Excel 7 hojas, Word 5 secciones"],
        ["Resiliencia", "CP-12, CP-15, CP-16", "Reintento, caché, fuente modificada"],
        ["Seguridad y control", "CP-13, CP-14", "3 denegaciones, contingencia resuelta"],
    ]
    _tabla(
        slide,
        Inches(3.45),
        Inches(1.98),
        Inches(9.1),
        Inches(3.7),
        filas,
        [Inches(2.25), Inches(2.0), Inches(4.85)],
        size=11,
    )
    _rect(slide, Inches(3.45), Inches(5.95), Inches(9.1), Inches(0.7), LIGHT)
    _text(slide, Inches(3.7), Inches(6.12), Inches(8.6), Inches(0.4), "Sin errores bloqueantes. Las incidencias y correcciones están documentadas en 03_errores_correcciones.md.", size=12, color=NAVY_2)
    _pie(slide, 9)

    # 10. Métricas ----------------------------------------------------------
    slide = _slide(prs)
    medicion = _metricas()
    total_ms = float(medicion.get("total_e2e_ms", 0) or 0)
    tiempo_sistema = f"{total_ms / 1000:.2f} s" if total_ms else "—"
    reduccion_pct = float(medicion.get("reduccion_mecanica_pct", 0) or 0)
    reduccion = f"{reduccion_pct:.2f}%" if reduccion_pct else "—"
    _cabecera(slide, "6 · Pruebas y métricas", "Línea base vs. sistema: qué se automatiza y qué no", "La línea base es una estimación declarada; el tiempo del sistema sí se midió.")
    _text(slide, Inches(0.72), Inches(1.95), Inches(6.0), Inches(0.3), "TRABAJO MECÁNICO (ESTIMADO)", size=10, bold=True, color=GRAY)
    _text(slide, Inches(0.72), Inches(2.35), Inches(2.2), Inches(0.35), "170 min", size=20, bold=True, color=NAVY)
    _rect(slide, Inches(0.72), Inches(2.85), Inches(7.2), Inches(0.55), AMBER, radius=False, shape=MSO_SHAPE.RECTANGLE)
    _text(slide, Inches(0.72), Inches(3.55), Inches(6.0), Inches(0.3), "SISTEMA (MEDIDO)", size=10, bold=True, color=GRAY)
    _text(slide, Inches(0.72), Inches(3.95), Inches(2.2), Inches(0.35), tiempo_sistema, size=20, bold=True, color=TEAL)
    _rect(slide, Inches(0.72), Inches(4.45), Inches(0.14), Inches(0.55), TEAL, radius=False, shape=MSO_SHAPE.RECTANGLE)
    _text(slide, Inches(0.72), Inches(5.15), Inches(7.3), Inches(0.35), f"Reducción del trabajo mecánico: {reduccion}", size=14, bold=True, color=TEAL)
    _text(slide, Inches(0.72), Inches(5.65), Inches(7.3), Inches(1.1), "La cifra no incluye el juicio técnico: los 90 minutos de revisión y decisión siguen siendo humanos. Comparar ambos tiempos sin esa aclaración sería engañoso.", size=12, color=GRAY)
    _rect(slide, Inches(8.45), Inches(1.95), Inches(4.15), Inches(4.35), LIGHT)
    _text(slide, Inches(8.72), Inches(2.12), Inches(3.6), Inches(0.3), "ACIERTOS DEL CASO", size=10, bold=True, color=AMBER)
    logros = [
        ("8/8", "documentos válidos"),
        ("7/7", "requisitos con propuesta"),
        ("7/7", "propuestas válidas"),
        ("2/4", "aceptadas sin cambio"),
        ("0", "«No cumple» inventados"),
    ]
    for indice, (valor, etiqueta) in enumerate(logros):
        top = Inches(2.5 + indice * 0.72)
        _text(slide, Inches(8.72), top, Inches(0.95), Inches(0.35), valor, size=16, bold=True, color=NAVY)
        _text(slide, Inches(9.7), top + Inches(0.03), Inches(2.6), Inches(0.3), etiqueta, size=11, color=NAVY_2)
    _text(slide, Inches(0.72), Inches(6.8), Inches(11.85), Inches(0.3), "Fuente: mvp/etapa6/evidencia/04_metricas_linea_base.md", size=10, color=GRAY)
    _pie(slide, 10)

    # 11. Seguridad y límites ----------------------------------------------
    slide = _slide(prs)
    _cabecera(slide, "7 · Seguridad y límites", "Controles reales, límites declarados", "Lo que el MVP ya protege y lo que todavía no debe prometer.")
    columnas = [
        (
            "CONTROLES IMPLEMENTADOS",
            TEAL,
            [
                "Roles: administrador, especialista y lector.",
                "3 denegaciones con causa en la prueba.",
                "SHA-256 por documento y por propuesta.",
                "Fuente modificada bloquea la decisión.",
                "Auditoría de cada acción en SQLite.",
            ],
        ),
        (
            "LÍMITES ACTUALES",
            AMBER,
            [
                "Sin OCR: PDF escaneado se rechaza.",
                "IA real opcional; por defecto, reglas.",
                "Datos sintéticos, no expedientes reales.",
                "Acceso de demostración, sin SSO.",
                "Plantilla oficial y firma pendientes.",
            ],
        ),
        (
            "PENDIENTES EXTERNOS",
            GRAY,
            [
                "Feedback firmado de un especialista.",
                "Grabación final del video demo.",
                "Validación de la plantilla institucional.",
                "Autenticación e identidad reales.",
                "Piloto con 3 expedientes reales.",
            ],
        ),
    ]
    for indice, (titulo, color, items) in enumerate(columnas):
        left = Inches(0.72 + indice * 4.03)
        _rect(slide, left, Inches(1.98), Inches(3.72), Inches(3.25), LIGHT)
        _rect(slide, left, Inches(1.98), Inches(3.72), Inches(0.08), color)
        _text(slide, left + Inches(0.24), Inches(2.2), Inches(3.25), Inches(0.3), titulo, size=10, bold=True, color=color)
        _bullets(slide, left + Inches(0.24), Inches(2.65), Inches(3.25), Inches(2.45), items, size=12, gap=10)
    _text(slide, Inches(0.72), Inches(5.48), Inches(11.85), Inches(0.35), "Declarar los límites es parte de la entrega: evita prometer un producto que el MVP todavía no es.", size=12, color=GRAY)
    _rect(slide, Inches(0.72), Inches(5.98), Inches(11.85), Inches(0.7), NAVY)
    _text(slide, Inches(1.0), Inches(6.17), Inches(11.2), Inches(0.4), "La confianza no se pide: se demuestra con rol, hash, historial y una decisión humana.", size=14, color=WHITE)
    _pie(slide, 11)

    # 12. Errores -----------------------------------------------------------
    slide = _slide(prs)
    _cabecera(slide, "8 · Aprendizajes", "Los errores que reveló la integración", "Probar el flujo completo encontró lo que las pruebas aisladas no veían.")
    filas = [
        ["ID", "Incidencia", "Corrección aplicada"],
        ["E-01", "EETT con nombre genérico mal clasificado", "Corrección humana persistida y vinculada al SHA-256"],
        ["E-02", "La verificación del Word no leía las tablas", "Inspección de celdas, no solo de párrafos"],
        ["E-03", "Exportación usaba un campo inexistente", "Se sumaron las evidencias reales del resumen"],
        ["E-04", "El alta de expediente exigía «administrar»", "Se habilitó para roles con permiso «cargar»"],
        ["E-05", "La contingencia quedaba oculta por otra propuesta", "Prueba aislada sobre copia de la base"],
    ]
    _tabla(
        slide,
        Inches(0.72),
        Inches(1.98),
        Inches(11.85),
        Inches(3.55),
        filas,
        [Inches(0.9), Inches(5.05), Inches(5.9)],
        size=12,
    )
    _rect(slide, Inches(0.72), Inches(5.85), Inches(11.85), Inches(0.8), NAVY)
    _text(slide, Inches(1.0), Inches(6.05), Inches(11.2), Inches(0.4), "Lección: la calidad no está en que el camino feliz funcione, sino en que el error deje rastro y no destruya datos.", size=14, color=WHITE)
    _pie(slide, 12)

    # 13. Próximos pasos ----------------------------------------------------
    slide = _slide(prs)
    _cabecera(slide, "8 · Aprendizajes", "Qué sigue para pasar de MVP a piloto", "Un plan por etapas, con una puerta de decisión en cada tramo.")
    hitos = [
        ("30 días", "Validar con el especialista", "Sesión de feedback, ajuste del checklist y de la plantilla de informes.", AMBER),
        ("60 días", "Cerrar brechas técnicas", "Autenticación real, OCR y evaluación semántica con IA supervisada.", TEAL),
        ("90 días", "Piloto controlado", "3 expedientes reales, medición de tiempos y comparación con la línea base.", AMBER),
    ]
    for indice, (plazo, titulo, detalle, color) in enumerate(hitos):
        left = Inches(0.72 + indice * 4.03)
        _rect(slide, left, Inches(1.98), Inches(3.72), Inches(2.75), LIGHT)
        _rect(slide, left, Inches(1.98), Inches(3.72), Inches(0.08), color)
        _text(slide, left + Inches(0.25), Inches(2.2), Inches(3.2), Inches(0.3), plazo.upper(), size=10, bold=True, color=color)
        _text(slide, left + Inches(0.25), Inches(2.6), Inches(3.2), Inches(0.7), titulo, size=17, bold=True, color=NAVY)
        _text(slide, left + Inches(0.25), Inches(3.35), Inches(3.2), Inches(1.2), detalle, size=12, color=NAVY_2)
    _rect(slide, Inches(0.72), Inches(5.05), Inches(11.85), Inches(1.15), WHITE, LINE)
    _text(slide, Inches(1.0), Inches(5.23), Inches(11.2), Inches(0.3), "PUERTA DE DECISIÓN", size=10, bold=True, color=AMBER)
    _text(slide, Inches(1.0), Inches(5.57), Inches(11.2), Inches(0.45), "Si el especialista no valida la evidencia y el avance, no se escala el piloto: se corrige el modelo de revisión.", size=15, color=NAVY)
    _pie(slide, 13)

    # 14. Cierre ------------------------------------------------------------
    slide = _slide(prs)
    _rect(slide, 0, 0, ANCHO, ALTO, NAVY, shape=MSO_SHAPE.RECTANGLE)
    _rect(slide, 0, 0, Inches(0.18), ALTO, AMBER, shape=MSO_SHAPE.RECTANGLE)
    _text(slide, Inches(0.95), Inches(0.85), Inches(6), Inches(0.3), "9 · CIERRE", size=11, bold=True, color=AMBER)
    _text(slide, Inches(0.95), Inches(1.35), Inches(8.6), Inches(1.4), "Una revisión defendible,\nno una caja negra.", size=38, bold=True, color=WHITE)
    _bullets(
        slide,
        Inches(0.95),
        Inches(3.05),
        Inches(6.7),
        Inches(2.4),
        [
            "Evidencia con fuente, ubicación y hash.",
            "Decisión humana con motivo e historial.",
            "Avance y cumplimiento calculados, no opinados.",
        ],
        size=16,
        color=RGBColor(0xD7, 0xDF, 0xEB),
        gap=12,
    )
    _rect(slide, Inches(8.15), Inches(1.55), Inches(4.2), Inches(4.55), NAVY_2)
    _text(slide, Inches(8.45), Inches(1.8), Inches(3.6), Inches(0.3), "PARA REVISAR", size=10, bold=True, color=AMBER)
    _text(slide, Inches(8.45), Inches(2.2), Inches(3.6), Inches(2.9), "mvp/etapa6/README.md\nmvp/etapa6/FICHA_TECNICA.md\nmvp/etapa6/evidencia/\nmvp/etapa6/entrega/", size=13, color=WHITE, font="Consolas")
    _text(slide, Inches(8.45), Inches(5.35), Inches(3.55), Inches(0.5), "Un comando reconstruye todo el flujo y sus 16 pruebas.", size=11, color=RGBColor(0xA9, 0xB7, 0xC9))
    _text(slide, Inches(0.95), Inches(6.55), Inches(6), Inches(0.35), "Gracias · Preguntas", size=15, bold=True, color=AMBER)

    prs.save(SALIDA)
    return SALIDA


if __name__ == "__main__":
    ruta = crear()
    print(f"PPT generado: {ruta}")
    print(f"Diapositivas: {len(Presentation(ruta).slides)}")
