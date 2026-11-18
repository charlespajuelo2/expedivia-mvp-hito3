"""Generador reproducible del corpus de prueba de la Etapa 2.

Crea:

- ``caso/``: los 6 documentos del expediente representativo ``EXP-2024-089``.
- ``casos_borde/``: PDF escaneado, PDF protegido, PDF corrupto, documento
  ambiguo y archivo con formato no soportado.

Uso::

    python -m mvp.scripts.generar_muestras
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.shared import Pt
from openpyxl import Workbook
from openpyxl.styles import Font
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from mvp.core import config


# --- Utilidades ----------------------------------------------------------


def _parrafo(estilos, texto: str, tamano: int = 10) -> Paragraph:
    estilo = estilos["BodyText"].clone("cuerpo", fontSize=tamano, leading=tamano + 3)
    return Paragraph(texto, estilo)


def _tabla(datos: list[list[str]], anchos: list[float] | None = None) -> Table:
    tabla = Table(datos, colWidths=anchos)
    tabla.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDE7F0")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return tabla


def _pdf_texto(destino: Path, titulo: str, lineas: list[str]) -> None:
    estilos = getSampleStyleSheet()
    documento = SimpleDocTemplate(
        str(destino),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=titulo,
    )
    historia = [Paragraph(titulo, estilos["Title"]), Spacer(1, 0.4 * cm)]
    for linea in lineas:
        historia.append(_parrafo(estilos, linea))
        historia.append(Spacer(1, 0.15 * cm))
    documento.build(historia)


# --- Documentos del caso -------------------------------------------------


def crear_tdr(destino: Path) -> None:
    estilos = getSampleStyleSheet()
    documento = SimpleDocTemplate(str(destino), pagesize=A4, title="TDR Carretera Central")
    historia = [
        Paragraph("TÉRMINOS DE REFERENCIA (TDR)", estilos["Title"]),
        Spacer(1, 0.3 * cm),
        _parrafo(
            estilos,
            "Contratación pública para la ejecución de la obra: mejoramiento de la "
            "Carretera Central Tramo 2, Km 42-78. Las bases del proceso de selección "
            "establecen los requisitos que debe cumplir todo postor.",
        ),
        Spacer(1, 0.3 * cm),
        Paragraph("2.1 Experiencia del postor", estilos["Heading2"]),
        _parrafo(
            estilos,
            "El postor debe acreditar facturación mayor a S/ 5 000 000 en los últimos "
            "cinco años, mediante contratos, facturas o constancias de facturación.",
        ),
        Paragraph("2.4 Personal clave", estilos["Heading2"]),
        _parrafo(
            estilos,
            "El residente de obra debe ser ingeniero civil colegiado con ocho años de "
            "experiencia. Se exige CV, certificados y constancia de colegiatura.",
        ),
        Paragraph("2.6 Equipamiento mínimo", estilos["Heading2"]),
        _parrafo(
            estilos,
            "El postor debe presentar una lista de quince equipos propios o alquilados, "
            "con inventario, facturas o contratos de alquiler.",
        ),
        Spacer(1, 0.3 * cm),
        _tabla(
            [
                ["Requisito", "Criterio", "Peso"],
                ["Experiencia del postor", "Facturación > S/ 5 MM en 5 años", "14%"],
                ["Personal clave", "Ing. civil colegiado, 8 años", "17%"],
                ["Equipamiento", "15 equipos propios o alquilados", "11%"],
                ["Presupuesto", "Partidas y precios unitarios", "21%"],
            ],
            [4.5 * cm, 8.5 * cm, 2 * cm],
        ),
    ]
    documento.build(historia)


def crear_presupuesto(destino: Path) -> None:
    import xlsxwriter

    libro = xlsxwriter.Workbook(str(destino))
    hoja = libro.add_worksheet("Resumen")
    formato_titulo = libro.add_format({"bold": True, "font_size": 13})
    formato_cabecera = libro.add_format(
        {"bold": True, "bg_color": "#DDE7F0", "border": 1}
    )
    formato_numero = libro.add_format({"num_format": "#,##0.00"})
    formato_entero = libro.add_format({"num_format": "#,##0"})

    hoja.write("A1", "PRESUPUESTO DE OBRA - CARRETERA CENTRAL TRAMO 2", formato_titulo)
    for columna, texto in enumerate(
        ["Ítem", "Partida", "Metrado", "Precio unitario", "Parcial"], start=0
    ):
        hoja.write(2, columna, texto, formato_cabecera)

    partidas = [
        ("01.01", "Movilización y desmovilización", 1, 185_000.0),
        ("01.02", "Trazo y replanteo", 36_000, 2.5),
        ("02.01", "Excavación en material suelto", 48_500, 12.8),
        ("02.02", "Perfilado y compactación de subrasante", 36_000, 8.4),
        ("03.01", "Base granular compactada", 32_400, 46.5),
        ("03.02", "Imprimación asfáltica", 32_400, 5.2),
        ("04.01", "Carpeta asfáltica en caliente", 28_800, 128.0),
        ("04.02", "Sello de fisuras", 6_500, 14.5),
        ("05.01", "Alcantarillas de concreto", 24, 3_850.0),
        ("05.02", "Cunetas revestidas", 12_600, 62.0),
        ("06.01", "Señalización horizontal", 36_000, 4.8),
        ("06.02", "Señalización vertical", 180, 420.0),
    ]

    parciales: list[float] = []
    for indice, (item, descripcion, metrado, precio) in enumerate(partidas):
        fila = 4 + indice
        parcial = metrado * precio
        parciales.append(parcial)
        hoja.write(f"A{fila}", item)
        hoja.write(f"B{fila}", descripcion)
        hoja.write(f"C{fila}", metrado, formato_entero)
        hoja.write(f"D{fila}", precio, formato_numero)
        # Fórmula con valor calculado en caché, como lo guarda una hoja real.
        hoja.write_formula(
            f"E{fila}", f"=C{fila}*D{fila}", formato_numero, parcial
        )

    subtotal = round(sum(parciales), 2)
    igv = round(subtotal * 0.18, 2)
    total = round(subtotal + igv, 2)

    hoja.write("A16", "Subtotal")
    hoja.write_formula("E16", "=SUM(E4:E15)", formato_numero, subtotal)
    hoja.write("A17", "IGV (18%)")
    hoja.write_formula("E17", "=E16*0.18", formato_numero, igv)
    hoja.write("A18", "TOTAL PRESUPUESTO", libro.add_format({"bold": True}))
    hoja.write_formula("F18", "=E16+E17", formato_numero, total)
    hoja.set_column("A:A", 10)
    hoja.set_column("B:B", 42)
    hoja.set_column("C:C", 12)
    hoja.set_column("D:D", 16)
    hoja.set_column("E:E", 16)
    hoja.set_column("F:F", 18)

    detalle = libro.add_worksheet("Partidas")
    detalle.write("A1", "ANÁLISIS DE PRECIOS UNITARIOS", formato_titulo)
    for columna, texto in enumerate(
        ["Partida", "Insumo", "Unidad", "Cantidad", "Costo unitario"], start=0
    ):
        detalle.write(2, columna, texto, formato_cabecera)
    insumos = [
        ("03.01", "Material granular", "m3", 1.25, 28.0),
        ("03.01", "Agua", "m3", 0.12, 8.0),
        ("03.01", "Rodillo autopropulsado", "hm", 0.02, 145.0),
        ("04.01", "Mezcla asfáltica", "ton", 2.35, 380.0),
        ("04.01", "Planta de asfalto", "hm", 0.05, 620.0),
    ]
    for indice, fila_datos in enumerate(insumos, start=3):
        for columna, valor in enumerate(fila_datos):
            detalle.write(indice, columna, valor)
    detalle.set_column("A:A", 10)
    detalle.set_column("B:B", 28)

    libro.close()


def crear_memoria(destino: Path) -> None:
    documento = Document()
    documento.add_heading("MEMORIA DE CÁLCULO DE PAVIMENTOS", level=1)
    documento.add_paragraph(
        "El presente documento sustenta el diseño estructural del pavimento flexible "
        "para la Carretera Central Tramo 2, Km 42-78."
    )
    documento.add_heading("1. Tránsito y variables de diseño", level=2)
    documento.add_paragraph(
        "Se consideró un tránsito equivalente de 8.4 millones de ejes equivalentes "
        "en el carril de diseño, con una tasa de crecimiento anual de 4.2%."
    )
    documento.add_heading("2. Capacidad de soporte", level=2)
    documento.add_paragraph(
        "El CBR de diseño de la subrasante es 6.5% para un percentil de 85%. El "
        "módulo de elasticidad estimado alcanza 42 MPa."
    )
    documento.add_heading("3. Estructura propuesta", level=2)
    tabla = documento.add_table(rows=1, cols=4)
    tabla.style = "Table Grid"
    encabezados = ["Capa", "Material", "Espesor (cm)", "Observación"]
    for celda, texto in zip(tabla.rows[0].cells, encabezados):
        celda.text = texto
    capas = [
        ("Carpeta asfáltica", "Mezcla en caliente", "12", "Módulo 3 200 MPa"),
        ("Base granular", "Afirmado granular", "20", "CBR >= 80%"),
        ("Subbase granular", "Material de cantera", "15", "CBR >= 40%"),
    ]
    for capa in capas:
        celdas = tabla.add_row().cells
        for celda, texto in zip(celdas, capa):
            celda.text = texto
    documento.add_paragraph(
        "El diseño estructural cumple con la normativa vial vigente y el periodo de "
        "diseño de diez años definido en los términos de referencia."
    )
    for parrafo in documento.paragraphs:
        for corrida in parrafo.runs:
            if corrida.font.size is None:
                corrida.font.size = Pt(10.5)
    documento.save(str(destino))


def crear_planos(destino: Path) -> None:
    from reportlab.pdfgen import canvas

    ancho, alto = A4
    lienzo = canvas.Canvas(str(destino), pagesize=A4)

    paginas_con_texto = {
        1: ("PLANO PL-01", "PLANTA GENERAL DEL TRAZO", "ESCALA 1:1000"),
        2: ("PLANO PL-02", "PERFIL LONGITUDINAL", "ESCALA H 1:1000 / V 1:100"),
        6: ("PLANO PL-06", "SECCIÓN TRANSVERSAL TÍPICA", "ESCALA 1:50"),
        7: ("PLANO PL-07", "DETALLE DE ALCANTARILLA", "ESCALA 1:25"),
        8: ("PLANO PL-08", "DETALLE DE SEÑALIZACIÓN", "ESCALA 1:20"),
    }

    for numero in range(1, 9):
        if numero in paginas_con_texto:
            titulo, subtitulo, escala = paginas_con_texto[numero]
            lienzo.setFont("Helvetica-Bold", 16)
            lienzo.drawString(2 * cm, alto - 3 * cm, titulo)
            lienzo.setFont("Helvetica", 12)
            lienzo.drawString(2 * cm, alto - 4 * cm, subtitulo)
            lienzo.drawString(2 * cm, alto - 5 * cm, escala)
            lienzo.setFont("Helvetica", 9)
            lienzo.drawString(
                2 * cm,
                alto - 6 * cm,
                "Proyecto: Carretera Central Tramo 2, Km 42-78. Lámina del expediente.",
            )
            lienzo.rect(2 * cm, 3 * cm, ancho - 4 * cm, alto - 10 * cm)
        else:
            # Páginas 3 a 5: lámina escaneada sin capa de texto.
            lienzo.setFillColorRGB(0.88, 0.88, 0.88)
            lienzo.rect(2 * cm, 3 * cm, ancho - 4 * cm, alto - 10 * cm, fill=1)
            lienzo.setFillColorRGB(0, 0, 0)
            lienzo.rect(6 * cm, 8 * cm, 8 * cm, 5 * cm)
        lienzo.showPage()

    lienzo.save()


def crear_eett(destino: Path) -> None:
    documento = Document()
    documento.add_heading("DOCUMENTO COMPLEMENTARIO DEL EXPEDIENTE", level=1)
    documento.add_paragraph(
        "El presente documento reúne información general del proyecto. Incluye "
        "referencias a especificaciones técnicas, presupuesto, cronograma, estudio de "
        "suelos, planos y memoria de cálculo. Su contenido es descriptivo y no "
        "desarrolla ninguna especialidad en detalle."
    )
    documento.add_paragraph(
        "Alcance general: ordenar los antecedentes disponibles y facilitar la lectura "
        "del expediente por parte del revisor. No reemplaza a los documentos técnicos "
        "ni constituye una especificación contractual."
    )
    documento.add_paragraph(
        "Observación del revisor: la denominación del archivo no coincide con su "
        "contenido; se requiere confirmar el tipo documental antes de usarlo como "
        "evidencia."
    )
    documento.save(str(destino))


def crear_suelos(destino: Path) -> None:
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Ensayos"
    hoja["A1"] = "ESTUDIO DE SUELOS - ENSAYOS DE LABORATORIO"
    hoja["A1"].font = Font(bold=True, size=13)
    encabezados = [
        "Calicata",
        "Profundidad (m)",
        "Granulometría",
        "Límite líquido",
        "Proctor (g/cm3)",
        "CBR (%)",
    ]
    for columna, texto in enumerate(encabezados, start=1):
        hoja.cell(row=3, column=columna, value=texto).font = Font(bold=True)

    ensayos = [
        ("C-01", 0.8, "GP-GM", 24, 2.08, 38),
        ("C-01", 1.5, "GM", 27, 2.05, 32),
        ("C-02", 1.0, "SP-SM", 22, 2.02, 28),
        ("C-02", 1.8, "SM", 29, 1.98, 24),
        ("C-03", 1.2, "CL", 34, 1.92, 12),
        ("C-03", 2.0, "CH", 41, 1.88, 8),
        ("C-04", 1.0, "GP", 20, 2.10, 45),
        ("C-05", 1.4, "SM", 28, 2.00, 22),
    ]
    for indice, fila_datos in enumerate(ensayos, start=4):
        for columna, valor in enumerate(fila_datos, start=1):
            hoja.cell(row=indice, column=columna, value=valor)

    hoja["A14"] = "CBR de diseño (percentil 85%)"
    hoja["F14"] = 6.5
    for columna, ancho in {"A": 12, "B": 16, "C": 16, "D": 14, "E": 16, "F": 10}.items():
        hoja.column_dimensions[columna].width = ancho

    resumen = libro.create_sheet("Resumen")
    resumen["A1"] = "RESUMEN GEOTÉCNICO"
    resumen["A1"].font = Font(bold=True)
    resumen["A3"] = "La subrasante presenta un CBR de diseño de 6.5%."
    resumen["A4"] = "Se recomienda mejorar los tramos con calicatas C-03 y C-05."
    libro.save(destino)


# --- Casos borde ---------------------------------------------------------


def crear_pdf_escaneado(destino: Path) -> None:
    from reportlab.pdfgen import canvas

    lienzo = canvas.Canvas(str(destino), pagesize=A4)
    for _ in range(2):
        lienzo.setFillColorRGB(0.75, 0.75, 0.75)
        lienzo.rect(2 * cm, 2 * cm, A4[0] - 4 * cm, A4[1] - 4 * cm, fill=1)
        lienzo.setFillColorRGB(0.2, 0.2, 0.2)
        lienzo.rect(5 * cm, 10 * cm, 10 * cm, 6 * cm)
        lienzo.showPage()
    lienzo.save()


def crear_pdf_protegido(destino: Path) -> None:
    temporal = destino.with_suffix(".base.pdf")
    _pdf_texto(temporal, "Documento protegido", ["Contenido reservado con contraseña."])
    lector = PdfReader(str(temporal))
    escritor = PdfWriter()
    for pagina in lector.pages:
        escritor.add_page(pagina)
    escritor.encrypt("clave-demo", "dueno-demo", algorithm="AES-128")
    with destino.open("wb") as manejador:
        escritor.write(manejador)
    temporal.unlink(missing_ok=True)


def crear_pdf_corrupto(destino: Path, base: Path) -> None:
    datos = base.read_bytes()
    destino.write_bytes(datos[:800])


def crear_documento_ambiguo(destino: Path) -> None:
    _pdf_texto(
        destino,
        "DOCUMENTO GENERAL",
        [
            "Documento complementario del expediente. Contiene información general del "
            "proyecto y notas de coordinación.",
            "No se identifica una especialidad ni un contenido técnico verificable.",
        ],
    )


# --- API -----------------------------------------------------------------


def generar_corpus(destino: str | Path | None = None) -> dict[str, object]:
    """Genera el corpus completo y devuelve las rutas creadas."""

    destino = Path(destino or config.DIR_MUESTRAS)
    caso = destino / "caso"
    borde = destino / "casos_borde"
    caso.mkdir(parents=True, exist_ok=True)
    borde.mkdir(parents=True, exist_ok=True)

    rutas_caso = {
        "TDR_Carretera_Central_v3.pdf": caso / "TDR_Carretera_Central_v3.pdf",
        "Presupuesto.xlsx": caso / "Presupuesto.xlsx",
        "Memoria_Calculo_Pavimentos.docx": caso
        / "Memoria_Calculo_Pavimentos.docx",
        "Planos_PL-01_PL-08.pdf": caso / "Planos_PL-01_PL-08.pdf",
        "EETT_General_v2.docx": caso / "EETT_General_v2.docx",
        "Estudio_Suelos_Lab.xlsx": caso / "Estudio_Suelos_Lab.xlsx",
    }

    crear_tdr(rutas_caso["TDR_Carretera_Central_v3.pdf"])
    crear_presupuesto(rutas_caso["Presupuesto.xlsx"])
    crear_memoria(rutas_caso["Memoria_Calculo_Pavimentos.docx"])
    crear_planos(rutas_caso["Planos_PL-01_PL-08.pdf"])
    crear_eett(rutas_caso["EETT_General_v2.docx"])
    crear_suelos(rutas_caso["Estudio_Suelos_Lab.xlsx"])

    rutas_borde = {
        "PDF_Escaneado.pdf": borde / "PDF_Escaneado.pdf",
        "PDF_Protegido.pdf": borde / "PDF_Protegido.pdf",
        "PDF_Corrupto.pdf": borde / "PDF_Corrupto.pdf",
        "Documento_General.pdf": borde / "Documento_General.pdf",
        "notas.txt": borde / "notas.txt",
    }

    crear_pdf_escaneado(rutas_borde["PDF_Escaneado.pdf"])
    crear_pdf_protegido(rutas_borde["PDF_Protegido.pdf"])
    crear_pdf_corrupto(
        rutas_borde["PDF_Corrupto.pdf"], rutas_caso["TDR_Carretera_Central_v3.pdf"]
    )
    crear_documento_ambiguo(rutas_borde["Documento_General.pdf"])
    rutas_borde["notas.txt"].write_text(
        "Archivo de texto no soportado por el MVP (solo PDF, DOCX y XLSX).",
        encoding="utf-8",
    )

    return {
        "carpeta_caso": caso,
        "carpeta_borde": borde,
        "caso": rutas_caso,
        "borde": rutas_borde,
    }


if __name__ == "__main__":
    resultado = generar_corpus()
    print(f"Corpus generado en: {resultado['carpeta_caso'].parent}")
    print(f"Documentos del caso: {len(resultado['caso'])}")
    print(f"Casos borde: {len(resultado['borde'])}")
