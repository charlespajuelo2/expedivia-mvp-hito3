"""Extracción de texto y tablas con ubicación verificable.

Formatos soportados: PDF (con capa de texto), DOCX y XLSX.

El resultado siempre indica **dónde** está cada fragmento (página, párrafo,
tabla/fila o hoja/celda), de modo que una decisión posterior pueda auditarse.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from . import config

#: pypdf registra advertencias internas (p. ej. "EOF marker not found") que ya
#: se traducen a un ``ErrorExtraccion`` controlado. Se silencian para no
#: duplicar el mensaje en consola o en la interfaz.
logging.getLogger("pypdf").setLevel(logging.ERROR)


class ErrorExtraccion(Exception):
    """Error controlado de extracción con código trazable."""

    def __init__(self, codigo: str, mensaje: str, detalle: str | None = None) -> None:
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje
        self.detalle = detalle

    def a_dict(self) -> dict[str, str]:
        return {
            "codigo": self.codigo,
            "mensaje": self.mensaje,
            "detalle": self.detalle or "",
        }


@dataclass
class Fragmento:
    """Porción de texto extraída con su ubicación exacta."""

    orden: int
    ubicacion: str
    tipo: str  # texto | tabla | fila | parrafo
    texto: str

    def a_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def desde_dict(cls, datos: dict[str, Any]) -> "Fragmento":
        return cls(
            orden=int(datos["orden"]),
            ubicacion=str(datos["ubicacion"]),
            tipo=str(datos["tipo"]),
            texto=str(datos["texto"]),
        )


@dataclass
class Extraccion:
    """Resultado completo de extraer un documento."""

    formato: str
    paginas: int | None
    texto_recuperable: str  # si | parcial | no
    caracteres: int
    fragmentos: list[Fragmento] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)
    metadatos: dict[str, Any] = field(default_factory=dict)

    def a_dict(self) -> dict[str, Any]:
        return {
            "formato": self.formato,
            "paginas": self.paginas,
            "texto_recuperable": self.texto_recuperable,
            "caracteres": self.caracteres,
            "fragmentos": [f.a_dict() for f in self.fragmentos],
            "advertencias": list(self.advertencias),
            "metadatos": dict(self.metadatos),
        }

    @classmethod
    def desde_dict(cls, datos: dict[str, Any]) -> "Extraccion":
        return cls(
            formato=str(datos["formato"]),
            paginas=datos.get("paginas"),
            texto_recuperable=str(datos["texto_recuperable"]),
            caracteres=int(datos.get("caracteres", 0)),
            fragmentos=[Fragmento.desde_dict(f) for f in datos.get("fragmentos", [])],
            advertencias=list(datos.get("advertencias", [])),
            metadatos=dict(datos.get("metadatos", {})),
        )

    @property
    def texto_completo(self) -> str:
        return "\n".join(fragmento.texto for fragmento in self.fragmentos)


def normalizar_texto(texto: str) -> str:
    """Uniforma espacios sin perder los saltos de línea relevantes."""

    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"[ \t\u00a0]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def sin_acentos(texto: str) -> str:
    """Minúsculas sin diacríticos, para comparaciones tolerantes."""

    descompuesto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def _agregar_fragmento(
    fragmentos: list[Fragmento],
    advertencias: list[str],
    ubicacion: str,
    tipo: str,
    texto: str,
) -> None:
    texto = normalizar_texto(texto)
    if not texto:
        return
    if len(fragmentos) >= config.MAX_FRAGMENTOS:
        if "Se alcanzó el máximo de fragmentos por documento." not in advertencias:
            advertencias.append("Se alcanzó el máximo de fragmentos por documento.")
        return
    fragmentos.append(
        Fragmento(orden=len(fragmentos), ubicacion=ubicacion, tipo=tipo, texto=texto)
    )


# --- PDF -----------------------------------------------------------------


def _extraer_pdf(ruta: Path) -> Extraccion:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependencia declarada
        raise ErrorExtraccion("DEPENDENCIA_FALTANTE", "Falta la librería pypdf.") from exc

    try:
        lector = PdfReader(str(ruta))
    except Exception as exc:
        raise ErrorExtraccion(
            "ARCHIVO_DANADO",
            "El PDF está dañado o no es un PDF válido.",
            str(exc),
        ) from exc

    if lector.is_encrypted:
        try:
            desbloqueado = lector.decrypt("")
        except Exception:
            desbloqueado = 0
        if not desbloqueado:
            raise ErrorExtraccion(
                "PDF_PROTEGIDO",
                "El PDF está protegido con contraseña; no se puede extraer su contenido.",
            )

    try:
        total_paginas = len(lector.pages)
    except Exception as exc:
        raise ErrorExtraccion(
            "ARCHIVO_DANADO", "No se pudo leer la estructura del PDF.", str(exc)
        ) from exc

    if total_paginas == 0:
        raise ErrorExtraccion("ARCHIVO_VACIO", "El PDF no contiene páginas.")

    fragmentos: list[Fragmento] = []
    advertencias: list[str] = []
    paginas_sin_texto: list[int] = []
    caracteres = 0

    for numero, pagina in enumerate(lector.pages, start=1):
        try:
            texto = pagina.extract_text() or ""
        except Exception as exc:  # página dañada: se registra y se continúa
            texto = ""
            advertencias.append(f"Página {numero}: no se pudo extraer texto ({exc}).")

        texto_normalizado = normalizar_texto(texto)
        if not texto_normalizado:
            paginas_sin_texto.append(numero)
            continue

        caracteres += len(texto_normalizado)
        _agregar_fragmento(
            fragmentos, advertencias, f"p. {numero}", "texto", texto_normalizado
        )

    if caracteres == 0:
        raise ErrorExtraccion(
            "PDF_ESCANEADO",
            "El PDF no contiene capa de texto (probablemente es un documento escaneado). "
            "Se rechaza para no generar conclusiones sin evidencia verificable.",
            f"Páginas sin texto: {', '.join(map(str, paginas_sin_texto))}",
        )

    _extraer_tablas_pdf(ruta, fragmentos, advertencias)

    if paginas_sin_texto:
        texto_recuperable = "parcial"
        advertencias.append(
            "Páginas sin capa de texto: "
            + ", ".join(str(p) for p in paginas_sin_texto)
            + ". Requieren OCR o reemplazo antes de usarlas como evidencia."
        )
    else:
        texto_recuperable = "si"

    return Extraccion(
        formato="PDF",
        paginas=total_paginas,
        texto_recuperable=texto_recuperable,
        caracteres=caracteres,
        fragmentos=fragmentos,
        advertencias=advertencias,
        metadatos={
            "paginas_sin_texto": paginas_sin_texto,
            "tablas_detectadas": sum(1 for f in fragmentos if f.tipo == "tabla"),
        },
    )


def _extraer_tablas_pdf(
    ruta: Path, fragmentos: list[Fragmento], advertencias: list[str]
) -> None:
    """Intenta recuperar tablas con pdfplumber sin bloquear la extracción."""

    try:
        import pdfplumber
    except ImportError:  # pragma: no cover
        advertencias.append("pdfplumber no está disponible; no se extrajeron tablas.")
        return

    try:
        with pdfplumber.open(str(ruta)) as pdf:
            for numero, pagina in enumerate(pdf.pages, start=1):
                try:
                    tablas = pagina.extract_tables() or []
                except Exception as exc:
                    advertencias.append(
                        f"Página {numero}: no se pudieron extraer tablas ({exc})."
                    )
                    continue
                for indice, tabla in enumerate(tablas, start=1):
                    lineas = []
                    for fila in tabla:
                        celdas = [
                            "" if celda is None else str(celda).strip() for celda in fila
                        ]
                        if any(celdas):
                            lineas.append(" | ".join(celdas))
                    if lineas:
                        _agregar_fragmento(
                            fragmentos,
                            advertencias,
                            f"p. {numero} · tabla {indice}",
                            "tabla",
                            "\n".join(lineas),
                        )
    except Exception as exc:
        advertencias.append(f"No se pudieron extraer tablas del PDF: {exc}")


# --- DOCX ----------------------------------------------------------------


def _extraer_docx(ruta: Path) -> Extraccion:
    try:
        from docx import Document
    except ImportError as exc:  # pragma: no cover
        raise ErrorExtraccion("DEPENDENCIA_FALTANTE", "Falta la librería python-docx.") from exc

    try:
        documento = Document(str(ruta))
    except Exception as exc:
        raise ErrorExtraccion(
            "ARCHIVO_DANADO",
            "El archivo DOCX está dañado o no es un DOCX válido.",
            str(exc),
        ) from exc

    fragmentos: list[Fragmento] = []
    advertencias: list[str] = []
    caracteres = 0
    seccion = ""

    for indice, parrafo in enumerate(documento.paragraphs, start=1):
        texto = normalizar_texto(parrafo.text)
        if not texto:
            continue
        estilo = (parrafo.style.name if parrafo.style is not None else "") or ""
        if estilo.lower().startswith(("heading", "título", "titulo")):
            seccion = texto

        ubicacion = f"párr. {indice}"
        if seccion and seccion != texto:
            ubicacion += f" · sección: {seccion[:60]}"

        caracteres += len(texto)
        _agregar_fragmento(fragmentos, advertencias, ubicacion, "parrafo", texto)

    for t_indice, tabla in enumerate(documento.tables, start=1):
        for f_indice, fila in enumerate(tabla.rows, start=1):
            celdas = [normalizar_texto(celda.text) for celda in fila.cells]
            celdas = [c for c in celdas if c]
            if not celdas:
                continue
            texto = " | ".join(celdas)
            caracteres += len(texto)
            _agregar_fragmento(
                fragmentos,
                advertencias,
                f"tabla {t_indice} · fila {f_indice}",
                "tabla",
                texto,
            )

    if caracteres == 0:
        raise ErrorExtraccion(
            "SIN_TEXTO_RECUPERABLE",
            "El DOCX no contiene texto recuperable.",
        )

    return Extraccion(
        formato="DOCX",
        paginas=None,
        texto_recuperable="si",
        caracteres=caracteres,
        fragmentos=fragmentos,
        advertencias=advertencias,
        metadatos={
            "parrafos": len(documento.paragraphs),
            "tablas": len(documento.tables),
        },
    )


# --- XLSX ----------------------------------------------------------------


def _formatear_valor(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "VERDADERO" if valor else "FALSO"
    if isinstance(valor, int):
        return f"{valor:,}"
    if isinstance(valor, float):
        return f"{valor:,.2f}"
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    return str(valor).strip()


def _extraer_xlsx(ruta: Path) -> Extraccion:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover
        raise ErrorExtraccion("DEPENDENCIA_FALTANTE", "Falta la librería openpyxl.") from exc

    try:
        libro = load_workbook(str(ruta), data_only=True)
    except Exception as exc:
        raise ErrorExtraccion(
            "ARCHIVO_DANADO",
            "El archivo XLSX está dañado o no es un XLSX válido.",
            str(exc),
        ) from exc

    formulas: dict[tuple[str, str], str] = {}
    try:
        libro_crudo = load_workbook(str(ruta), data_only=False)
        for hoja in libro_crudo.worksheets:
            for fila in hoja.iter_rows():
                for celda in fila:
                    if isinstance(celda.value, str) and celda.value.startswith("="):
                        formulas[(hoja.title, celda.coordinate)] = celda.value
        libro_crudo.close()
    except Exception:
        formulas = {}

    fragmentos: list[Fragmento] = []
    advertencias: list[str] = []
    caracteres = 0
    celdas_sin_valor: list[str] = []

    for hoja in libro.worksheets:
        filas_procesadas = 0
        for fila in hoja.iter_rows():
            if filas_procesadas >= config.MAX_FILAS_XLSX:
                advertencias.append(
                    f"Hoja '{hoja.title}': se procesaron solo las primeras "
                    f"{config.MAX_FILAS_XLSX} filas."
                )
                break

            celdas: list[tuple[str, Any]] = []
            for celda in fila:
                valor = celda.value
                formula = formulas.get((hoja.title, celda.coordinate))
                if valor in (None, "") and not formula:
                    continue
                celdas.append((celda.coordinate, (valor, formula)))

            if not celdas:
                continue

            filas_procesadas += 1
            partes: list[str] = []
            for coordenada, (valor, formula) in celdas:
                etiqueta = _formatear_valor(valor)
                texto_celda = f"{coordenada}={etiqueta}"
                if formula:
                    texto_celda += f" [fórmula {formula}]"
                    if valor is None:
                        celdas_sin_valor.append(f"{hoja.title}!{coordenada}")
                partes.append(texto_celda)

            coordenada_inicio = celdas[0][0]
            coordenada_fin = celdas[-1][0]
            texto = " | ".join(partes)
            caracteres += len(texto)

            _agregar_fragmento(
                fragmentos,
                advertencias,
                f"Hoja:{hoja.title}!{coordenada_inicio}:{coordenada_fin}",
                "fila",
                texto,
            )

    libro.close()

    if caracteres == 0:
        raise ErrorExtraccion(
            "SIN_TEXTO_RECUPERABLE",
            "El XLSX no contiene celdas con contenido recuperable.",
        )

    if celdas_sin_valor:
        advertencias.append(
            "Celdas con fórmula sin valor calculado en el archivo: "
            + ", ".join(celdas_sin_valor[:10])
            + ("…" if len(celdas_sin_valor) > 10 else "")
        )

    return Extraccion(
        formato="XLSX",
        paginas=None,
        texto_recuperable="si",
        caracteres=caracteres,
        fragmentos=fragmentos,
        advertencias=advertencias,
        metadatos={
            "hojas": [hoja.title for hoja in libro.worksheets],
        },
    )


# --- API pública ---------------------------------------------------------

_EXTRACTORES = {
    ".pdf": _extraer_pdf,
    ".docx": _extraer_docx,
    ".xlsx": _extraer_xlsx,
}


def extraer(ruta: str | Path) -> Extraccion:
    """Extrae un archivo soportado o lanza ``ErrorExtraccion``."""

    ruta = Path(ruta)
    if not ruta.exists():
        raise ErrorExtraccion(
            "ARCHIVO_NO_ENCONTRADO", f"No existe el archivo: {ruta.name}"
        )
    if not ruta.is_file():
        raise ErrorExtraccion("ARCHIVO_INVALIDO", f"La ruta no es un archivo: {ruta}")

    extension = ruta.suffix.lower()
    extractor = _EXTRACTORES.get(extension)
    if extractor is None:
        raise ErrorExtraccion(
            "FORMATO_NO_SOPORTADO",
            f"Formato '{extension or 'sin extensión'}' no soportado. "
            f"Use: {', '.join(sorted(config.FORMATOS_PERMITIDOS))}.",
        )

    if ruta.stat().st_size == 0:
        raise ErrorExtraccion("ARCHIVO_VACIO", "El archivo está vacío (0 bytes).")

    return extractor(ruta)
