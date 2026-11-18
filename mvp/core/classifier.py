"""Clasificación documental automática y corregible por humanos.

La clasificación es **determinista y explicable**: se apoya en señales del
nombre del archivo y del texto extraído, y devuelve la evidencia usada
(palabras clave detectadas). No usa IA en esta etapa, por lo que puede
reproducirse y auditarse.

Fórmula de confianza (0-100)::

    densidad   = mejor / (mejor + segundo + 1)
    cobertura  = min(1, mejor / 60)
    confianza  = round(100 * (0.5 * densidad + 0.5 * cobertura))

Si ``mejor`` es 0 el documento queda como ``No reconocido``. Si la confianza
es menor que el umbral (70 por defecto), el estado es ``Sin clasificar`` y se
exige corrección humana antes de usarlo como evidencia.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from . import config
from .extractors import Extraccion, sin_acentos

PESO_PATRON_NOMBRE = 12
PESO_FORMATO = 5
PUNTAJE_COBERTURA_PLENA = 65


@dataclass(frozen=True)
class PerfilDocumental:
    tipo: str
    componente: str
    palabras_clave: dict[str, int]
    patrones_nombre: tuple[str, ...] = ()
    formatos: tuple[str, ...] = ()


CATALOGO: tuple[PerfilDocumental, ...] = (
    PerfilDocumental(
        tipo="TDR / Bases",
        componente="TDR",
        palabras_clave={
            "terminos de referencia": 30,
            "tdr": 25,
            "bases del proceso": 25,
            "proceso de seleccion": 20,
            "postor": 15,
            "contratacion": 10,
            "experiencia del postor": 20,
        },
        patrones_nombre=(r"\btdr\b", r"terminos[_ -]de[_ -]referencia", r"bases"),
        formatos=(".pdf", ".docx"),
    ),
    PerfilDocumental(
        tipo="Presupuesto por partidas",
        componente="Presupuesto",
        palabras_clave={
            "presupuesto": 30,
            "precio unitario": 20,
            "partida": 15,
            "valor referencial": 15,
            "igv": 10,
            "subtotal": 5,
            "analisis de precios": 20,
        },
        patrones_nombre=(r"presupuesto", r"ppto", r"valorizacion"),
        formatos=(".xlsx", ".pdf"),
    ),
    PerfilDocumental(
        tipo="Memoria técnica",
        componente="Pavimentos",
        palabras_clave={
            "memoria de calculo": 30,
            "memoria descriptiva": 25,
            "pavimento": 20,
            "diseno estructural": 15,
            "espesor": 10,
            "modulo de elasticidad": 10,
            "cbr": 8,
        },
        patrones_nombre=(r"memoria", r"calculo"),
        formatos=(".docx", ".pdf"),
    ),
    PerfilDocumental(
        tipo="Planos",
        componente="Planos",
        palabras_clave={
            "plano": 30,
            "escala": 10,
            "seccion transversal": 15,
            "planta": 10,
            "perfil longitudinal": 15,
            "detalle": 8,
            "pl-0": 15,
        },
        patrones_nombre=(r"plano", r"\bpl[-_ ]?\d", r"lamina"),
        formatos=(".pdf",),
    ),
    PerfilDocumental(
        tipo="Especificaciones técnicas",
        componente="EETT",
        palabras_clave={
            "especificaciones tecnicas": 30,
            "eett": 20,
            "materiales": 10,
            "compactacion": 15,
            "curado": 8,
            "ejecucion de partidas": 15,
        },
        patrones_nombre=(r"eett", r"especificaciones"),
        formatos=(".docx", ".pdf"),
    ),
    PerfilDocumental(
        tipo="Estudio de suelos",
        componente="Geotecnia",
        palabras_clave={
            "estudio de suelos": 30,
            "calicata": 20,
            "granulometria": 15,
            "limite liquido": 10,
            "proctor": 12,
            "cbr": 10,
            "ensayo de laboratorio": 15,
        },
        patrones_nombre=(r"suelo", r"geotecnia", r"calicata"),
        formatos=(".xlsx", ".pdf", ".docx"),
    ),
    PerfilDocumental(
        tipo="Cronograma valorizado",
        componente="Cronograma",
        palabras_clave={
            "cronograma": 30,
            "curva s": 15,
            "ruta critica": 15,
            "plazo de ejecucion": 12,
            "hito": 5,
        },
        patrones_nombre=(r"cronograma", r"curva[_ -]?s"),
        formatos=(".xlsx", ".pdf"),
    ),
    PerfilDocumental(
        tipo="Metrados",
        componente="Metrados",
        palabras_clave={
            "metrados": 30,
            "planilla de metrados": 25,
            "computo metrico": 25,
            "hoja de metrados": 20,
        },
        patrones_nombre=(r"metrado",),
        formatos=(".xlsx", ".pdf"),
    ),
    PerfilDocumental(
        tipo="Estudio ambiental",
        componente="Ambiental",
        palabras_clave={
            "plan de manejo ambiental": 30,
            "impacto ambiental": 25,
            "instrumento ambiental": 25,
            "pma": 10,
            "medidas de mitigacion": 15,
        },
        patrones_nombre=(r"ambiental", r"\bpma\b", r"\bdia\b"),
        formatos=(".pdf", ".docx"),
    ),
)

TIPOS_DOCUMENTALES: tuple[tuple[str, str], ...] = tuple(
    (perfil.tipo, perfil.componente) for perfil in CATALOGO
) + (("No reconocido", "Sin asignar"),)

TIPO_NO_RECONOCIDO = "No reconocido"
COMPONENTE_SIN_ASIGNAR = "Sin asignar"


@dataclass
class Clasificacion:
    tipo_documental: str
    componente: str
    confianza: int
    estado: str  # Clasificado | Sin clasificar
    coincidencias: list[str] = field(default_factory=list)
    origen: str = "automatico"
    puntajes: dict[str, int] = field(default_factory=dict)

    def a_dict(self) -> dict[str, object]:
        return {
            "tipo_documental": self.tipo_documental,
            "componente": self.componente,
            "confianza": self.confianza,
            "estado": self.estado,
            "coincidencias": list(self.coincidencias),
            "origen": self.origen,
            "puntajes": dict(self.puntajes),
        }


def _patron(palabra: str) -> re.Pattern[str]:
    return re.compile(r"(?<![a-z0-9])" + re.escape(palabra) + r"(?![a-z0-9])")


def _puntuar_perfil(
    perfil: PerfilDocumental,
    texto: str,
    nombre: str,
    formato: str,
) -> tuple[int, list[str]]:
    puntaje = 0
    coincidencias: list[str] = []

    for palabra, peso in perfil.palabras_clave.items():
        if _patron(palabra).search(texto):
            puntaje += peso
            coincidencias.append(palabra)

    for patron in perfil.patrones_nombre:
        if re.search(patron, nombre):
            puntaje += PESO_PATRON_NOMBRE
            coincidencias.append(f"nombre:{patron}")
            break

    if formato in perfil.formatos:
        puntaje += PESO_FORMATO

    return puntaje, coincidencias


def calcular_confianza(mejor: int, segundo: int) -> int:
    """Confianza 0-100 según evidencia absoluta y dominio sobre el segundo."""

    if mejor <= 0:
        return 0
    densidad = mejor / (mejor + max(segundo, 0) + 1)
    cobertura = min(1.0, mejor / PUNTAJE_COBERTURA_PLENA)
    return max(0, min(96, round(100 * (0.5 * densidad + 0.5 * cobertura))))


def clasificar(
    nombre_archivo: str,
    extraccion: Extraccion,
    *,
    umbral: int = config.UMBRAL_CONFIANZA,
    tipos: Iterable[PerfilDocumental] = CATALOGO,
) -> Clasificacion:
    """Clasifica un documento y explica las señales usadas."""

    nombre = sin_acentos(nombre_archivo)
    texto = sin_acentos(extraccion.texto_completo)[:200_000]
    formato = "." + extraccion.formato.lower()

    resultados: list[tuple[int, PerfilDocumental, list[str]]] = []
    for perfil in tipos:
        puntaje, coincidencias = _puntuar_perfil(perfil, texto, nombre, formato)
        resultados.append((puntaje, perfil, coincidencias))

    resultados.sort(key=lambda item: item[0], reverse=True)
    mejor, perfil_mejor, coincidencias = resultados[0]
    segundo = resultados[1][0] if len(resultados) > 1 else 0
    confianza = calcular_confianza(mejor, segundo)

    puntajes = {
        perfil.tipo: puntaje for puntaje, perfil, _ in resultados if puntaje > 0
    }

    if mejor <= 0 or not coincidencias:
        return Clasificacion(
            tipo_documental=TIPO_NO_RECONOCIDO,
            componente=COMPONENTE_SIN_ASIGNAR,
            confianza=0,
            estado="Sin clasificar",
            coincidencias=[],
            puntajes=puntajes,
        )

    estado = "Clasificado" if confianza >= umbral else "Sin clasificar"
    return Clasificacion(
        tipo_documental=perfil_mejor.tipo,
        componente=perfil_mejor.componente,
        confianza=confianza,
        estado=estado,
        coincidencias=coincidencias,
        puntajes=puntajes,
    )


def componentes() -> list[str]:
    """Componentes conocidos, para poblar formularios de corrección."""

    vistos: list[str] = []
    for _, componente in TIPOS_DOCUMENTALES:
        if componente not in vistos:
            vistos.append(componente)
    return vistos
