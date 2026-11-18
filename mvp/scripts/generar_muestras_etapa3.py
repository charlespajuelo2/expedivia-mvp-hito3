"""Generador reproducible del corpus de la Etapa 3.

Parte del corpus de la Etapa 2 y agrega dos documentos complementarios que
permiten demostrar los estados ``Cumple`` y ``Requiere revisión especializada``:

- ``Cronograma_Valorizado.xlsx``: cronograma, curva S y ruta crítica.
- ``PMA_Ambiental.pdf``: Plan de Manejo Ambiental y certificación vigente.

Uso::

    python -m mvp.scripts.generar_muestras_etapa3
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from mvp.core import config
from mvp.scripts.generar_muestras import _pdf_texto, generar_corpus


def _cabecera(hoja, fila: int, textos: list[str]) -> None:
    relleno = PatternFill("solid", fgColor="DDE7F0")
    for columna, texto in enumerate(textos, start=1):
        celda = hoja.cell(row=fila, column=columna, value=texto)
        celda.font = Font(bold=True)
        celda.fill = relleno


def _anchos(hoja, anchos: dict[str, int]) -> None:
    for columna, ancho in anchos.items():
        hoja.column_dimensions[columna].width = ancho


def crear_cronograma(destino: Path) -> None:
    libro = Workbook()
    cronograma = libro.active
    cronograma.title = "Cronograma"

    cronograma["A1"] = "CRONOGRAMA VALORIZADO - CARRETERA CENTRAL TRAMO 2"
    cronograma["A1"].font = Font(bold=True, size=13)
    cronograma["A2"] = (
        "Plazo de ejecución: 6 meses. Moneda: Soles. "
        "El cronograma valorizado se vincula con el presupuesto por partidas."
    )
    _cabecera(
        cronograma,
        4,
        [
            "Partida",
            "Descripción",
            "Peso %",
            "Mes 1",
            "Mes 2",
            "Mes 3",
            "Mes 4",
            "Mes 5",
            "Mes 6",
            "Valorizado",
        ],
    )

    partidas = [
        ("01.01", "Movilización y desmovilización", 4, [1, 1, 1, 1, 0, 0], 1_012_320),
        ("01.02", "Trazo y replanteo", 2, [1, 1, 0, 0, 0, 0], 506_160),
        ("02.01", "Excavación en material suelto", 12, [2, 3, 3, 2, 1, 1], 3_036_960),
        ("02.02", "Perfilado y compactación", 10, [1, 2, 2, 2, 2, 1], 2_530_800),
        ("03.01", "Base granular compactada", 18, [0, 2, 4, 5, 4, 3], 4_555_440),
        ("03.02", "Imprimación asfáltica", 4, [0, 0, 1, 2, 1, 0], 1_012_320),
        ("04.01", "Carpeta asfáltica en caliente", 28, [0, 0, 2, 5, 8, 13], 7_086_240),
        ("04.02", "Sello de fisuras", 3, [0, 0, 0, 1, 1, 1], 759_240),
        ("05.01", "Alcantarillas de concreto", 6, [0, 1, 2, 1, 1, 1], 1_518_480),
        ("05.02", "Cunetas revestidas", 5, [0, 0, 1, 2, 1, 1], 1_265_400),
        ("06.01", "Señalización horizontal", 4, [0, 0, 0, 1, 2, 1], 1_012_320),
        ("06.02", "Señalización vertical", 4, [0, 0, 0, 1, 1, 2], 1_012_320),
    ]

    fila = 5
    for partida, descripcion, peso, meses, valorizado in partidas:
        valores = [partida, descripcion, peso, *meses, valorizado]
        for columna, valor in enumerate(valores, start=1):
            cronograma.cell(row=fila, column=columna, value=valor)
        fila += 1

    cronograma.cell(row=fila, column=1, value="TOTAL").font = Font(bold=True)
    cronograma.cell(row=fila, column=2, value="TOTAL CRONOGRAMA VALORIZADO").font = Font(
        bold=True
    )
    cronograma.cell(row=fila, column=3, value=100).font = Font(bold=True)
    cronograma.cell(row=fila, column=10, value=25_307_160).font = Font(bold=True)
    _anchos(
        cronograma,
        {
            "A": 10,
            "B": 38,
            "C": 8,
            "D": 8,
            "E": 8,
            "F": 8,
            "G": 8,
            "H": 8,
            "I": 8,
            "J": 14,
        },
    )

    curva = libro.create_sheet("Curva S")
    curva["A1"] = "CURVA S - AVANCE ACUMULADO"
    curva["A1"].font = Font(bold=True, size=13)
    _cabecera(curva, 3, ["Mes", "Avance mensual %", "Avance acumulado %"])
    avances = [
        (1, 4, 4),
        (2, 9, 13),
        (3, 17, 30),
        (4, 24, 54),
        (5, 26, 80),
        (6, 20, 100),
    ]
    for indice, (mes, mensual, acumulado) in enumerate(avances, start=4):
        curva.cell(row=indice, column=1, value=f"Mes {mes}")
        curva.cell(row=indice, column=2, value=mensual)
        curva.cell(row=indice, column=3, value=acumulado)

    curva["A11"] = (
        "Observación: la coherencia de la curva S con el presupuesto y la ruta "
        "crítica debe ser validada por el especialista."
    )
    curva["A12"] = "La curva S acumula el 100% del valorizado al mes 6."
    _anchos(curva, {"A": 12, "B": 20, "C": 22})

    ruta = libro.create_sheet("Ruta crítica")
    ruta["A1"] = "RUTA CRÍTICA DEL PROYECTO"
    ruta["A1"].font = Font(bold=True, size=13)
    _cabecera(
        ruta,
        3,
        ["Actividad", "Predecesora", "Duración (días)", "Holgura (días)"],
    )
    actividades = [
        ("Movilización", "—", 15, 0),
        ("Trazo y replanteo", "Movilización", 20, 0),
        ("Movimiento de tierras", "Trazo y replanteo", 45, 0),
        ("Base granular", "Movimiento de tierras", 40, 0),
        ("Carpeta asfáltica", "Base granular", 35, 0),
        ("Señalización", "Carpeta asfáltica", 20, 0),
        ("Obras de arte", "Movimiento de tierras", 30, 10),
    ]
    for indice, actividad in enumerate(actividades, start=4):
        for columna, valor in enumerate(actividad, start=1):
            ruta.cell(row=indice, column=columna, value=valor)

    ruta["A12"] = (
        "Las actividades con holgura cero conforman la ruta crítica; el plazo "
        "de ejecución total es de 175 días."
    )
    _anchos(ruta, {"A": 28, "B": 22, "C": 18, "D": 16})

    libro.save(destino)


def crear_pma(destino: Path) -> None:
    _pdf_texto(
        destino,
        "PLAN DE MANEJO AMBIENTAL (PMA)",
        [
            "Proyecto: Carretera Central Tramo 2, Km 42-78. "
            "Expediente técnico para la ejecución de la obra.",
            "Instrumento ambiental: Estudio de Impacto Ambiental (EIA) aprobado "
            "mediante Resolución Directoral N.° 045-2024-MTC/16.",
            "Certificación ambiental: el instrumento ambiental se encuentra vigente "
            "a la fecha de referencia del expediente.",
            "El Plan de Manejo Ambiental (PMA) establece las medidas de mitigación, "
            "seguimiento y control para las actividades de construcción.",
            "Medidas de mitigación: riego de vías para control de polvo, manejo de "
            "residuos sólidos, control de erosión, protección de cauces y "
            "revegetación de áreas intervenidas.",
            "El PMA se encuentra integrado al expediente técnico y cuenta con "
            "presupuesto ambiental asignado.",
            "Responsable: Oficina de Medio Ambiente. Vigencia: 2024-2026.",
        ],
    )


def generar_corpus_etapa3(destino: str | Path | None = None) -> dict:
    """Genera el corpus de la Etapa 3 y devuelve las rutas creadas."""

    destino = Path(destino or config.DIR_MUESTRAS_ETAPA3)
    corpus = generar_corpus(destino)
    caso = corpus["carpeta_caso"]

    nuevos = {
        "Cronograma_Valorizado.xlsx": caso / "Cronograma_Valorizado.xlsx",
        "PMA_Ambiental.pdf": caso / "PMA_Ambiental.pdf",
    }
    crear_cronograma(nuevos["Cronograma_Valorizado.xlsx"])
    crear_pma(nuevos["PMA_Ambiental.pdf"])

    corpus["caso"].update(nuevos)
    corpus["documentos_etapa3"] = sorted(corpus["caso"])
    return corpus


if __name__ == "__main__":
    resultado = generar_corpus_etapa3()
    print(f"Corpus Etapa 3 generado en: {resultado['carpeta_caso']}")
    print(f"Documentos del caso: {len(resultado['caso'])}")
    for nombre in sorted(resultado["caso"]):
        print(f"- {nombre}")
