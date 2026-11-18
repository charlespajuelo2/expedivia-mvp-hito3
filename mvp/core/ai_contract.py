"""Contrato JSON estricto para las propuestas de IA (Etapa 3).

Una respuesta solo se acepta si cumple **todo** lo siguiente:

1. Es un objeto JSON con exactamente los campos del contrato.
2. ``requisito_id`` coincide con el requisito analizado.
3. ``estado_propuesto`` pertenece a los cinco estados aprobados.
4. Si se declara evidencia, la fuente existe entre los fragmentos recuperados
   y coinciden documento, archivo, ubicación y SHA-256.
5. La cita aparece textualmente en el fragmento citado.
6. Los estados concluyentes exigen evidencia; la ausencia de información exige
   ``fuente = null`` y no puede convertirse en “No cumple”.

La validación devuelve **todos** los errores encontrados para que puedan
registrarse y mostrarse, en lugar de fallar en el primer campo.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from . import config
from .evidence import Evidencia
from .extractors import sin_acentos

CAMPOS_OBLIGATORIOS: tuple[str, ...] = (
    "requisito_id",
    "estado_propuesto",
    "evidencia_encontrada",
    "fuente",
    "cita",
    "observacion_preliminar",
    "requiere_revision_especializada",
    "motivo",
)

CAMPOS_FUENTE: tuple[str, ...] = (
    "documento_id",
    "archivo",
    "ubicacion",
    "sha256",
)

ESTADOS_CONCLUYENTES = ("Cumple", "Cumple parcialmente", "No cumple")
ESTADOS_VALIDOS = set(config.ESTADOS_REQUISITO)

MAX_CITA = 600
MAX_TEXTO = 1200
MIN_CITA = 8


# --- Errores --------------------------------------------------------------


@dataclass
class ErrorContrato:
    codigo: str
    mensaje: str
    campo: str | None = None

    def a_dict(self) -> dict[str, str]:
        return {
            "codigo": self.codigo,
            "mensaje": self.mensaje,
            "campo": self.campo or "",
        }

    def __str__(self) -> str:
        ubicacion = f" [{self.campo}]" if self.campo else ""
        return f"{self.codigo}{ubicacion}: {self.mensaje}"


# --- Propuesta ------------------------------------------------------------


@dataclass
class Propuesta:
    """Representación ya validada de una respuesta de IA."""

    requisito_id: str
    estado_propuesto: str
    evidencia_encontrada: bool
    fuente: dict[str, Any] | None
    cita: str | None
    observacion_preliminar: str
    requiere_revision_especializada: bool
    motivo: str

    def a_dict(self) -> dict[str, Any]:
        return {
            "requisito_id": self.requisito_id,
            "estado_propuesto": self.estado_propuesto,
            "evidencia_encontrada": self.evidencia_encontrada,
            "fuente": self.fuente,
            "cita": self.cita,
            "observacion_preliminar": self.observacion_preliminar,
            "requiere_revision_especializada": self.requiere_revision_especializada,
            "motivo": self.motivo,
        }


@dataclass
class ResultadoValidacion:
    valida: bool
    propuesta: Propuesta | None
    errores: list[ErrorContrato] = field(default_factory=list)

    def mensajes(self) -> list[str]:
        return [str(error) for error in self.errores]

    def a_dict(self) -> dict[str, Any]:
        return {
            "valida": self.valida,
            "propuesta": self.propuesta.a_dict() if self.propuesta else None,
            "errores": [error.a_dict() for error in self.errores],
        }


# --- Utilidades -----------------------------------------------------------


def extraer_json(respuesta: Any) -> dict[str, Any]:
    """Convierte una respuesta en objeto JSON, tolerando cercas de Markdown."""

    if isinstance(respuesta, dict):
        return respuesta
    if not isinstance(respuesta, str):
        raise ValueError("La respuesta de IA no es texto ni un objeto JSON.")

    texto = respuesta.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?\s*", "", texto, flags=re.IGNORECASE)
        texto = re.sub(r"\s*```$", "", texto)
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError:
        inicio = texto.find("{")
        fin = texto.rfind("}")
        if inicio < 0 or fin <= inicio:
            raise ValueError("La respuesta no contiene un objeto JSON reconocible.")
        datos = json.loads(texto[inicio : fin + 1])
    if not isinstance(datos, dict):
        raise ValueError("La respuesta JSON debe ser un objeto, no una lista o un valor simple.")
    return datos


def _normalizar_cita(texto: str) -> str:
    texto = texto.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", texto).strip()


def cita_en_texto(cita: str, texto: str) -> bool:
    """Comprueba que la cita sea un fragmento real del texto fuente.

    Tolera diferencias de espaciado, mayúsculas y tildes, pero no cambios de
    contenido: la cita debe ser una subcadena continua del fragmento.
    """

    cita_normalizada = _normalizar_cita(cita)
    texto_normalizado = _normalizar_cita(texto)
    if not cita_normalizada:
        return False
    if cita_normalizada in texto_normalizado:
        return True
    if cita_normalizada.lower() in texto_normalizado.lower():
        return True
    return _normalizar_cita(sin_acentos(cita_normalizada)) in _normalizar_cita(
        sin_acentos(texto_normalizado)
    )


def _agregar(
    errores: list[ErrorContrato], codigo: str, mensaje: str, campo: str | None = None
) -> None:
    errores.append(ErrorContrato(codigo=codigo, mensaje=mensaje, campo=campo))


def _es_entero(valor: Any) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def _es_booleano(valor: Any) -> bool:
    return isinstance(valor, bool)


def _texto_no_vacio(valor: Any) -> bool:
    return isinstance(valor, str) and bool(valor.strip())


# --- Validación -----------------------------------------------------------


def validar_propuesta(
    respuesta: Any,
    *,
    requisito_id: str,
    evidencias: Iterable[Evidencia],
    estados_validos: Iterable[str] | None = None,
) -> ResultadoValidacion:
    """Valida el contrato y la trazabilidad de una respuesta de IA."""

    errores: list[ErrorContrato] = []
    estados = set(estados_validos or ESTADOS_VALIDOS)
    evidencias = list(evidencias)

    try:
        datos = extraer_json(respuesta)
    except (ValueError, json.JSONDecodeError) as exc:
        _agregar(errores, "JSON_INVALIDO", str(exc))
        return ResultadoValidacion(False, None, errores)

    desconocidos = sorted(set(datos) - set(CAMPOS_OBLIGATORIOS))
    for campo in desconocidos:
        _agregar(
            errores,
            "CAMPO_DESCONOCIDO",
            f"El campo '{campo}' no forma parte del contrato.",
            campo,
        )

    for campo in CAMPOS_OBLIGATORIOS:
        if campo not in datos:
            _agregar(errores, "CAMPO_FALTANTE", "Falta un campo obligatorio.", campo)

    # Si faltan campos, no se intenta construir la propuesta.
    if any(error.codigo == "CAMPO_FALTANTE" for error in errores):
        return ResultadoValidacion(False, None, errores)

    requisito = datos.get("requisito_id")
    estado = datos.get("estado_propuesto")
    encontrada = datos.get("evidencia_encontrada")
    fuente = datos.get("fuente")
    cita = datos.get("cita")
    observacion = datos.get("observacion_preliminar")
    revision = datos.get("requiere_revision_especializada")
    motivo = datos.get("motivo")

    if not _texto_no_vacio(requisito):
        _agregar(errores, "TIPO_INVALIDO", "Debe ser un texto no vacío.", "requisito_id")
    elif requisito != requisito_id:
        _agregar(
            errores,
            "REQUISITO_NO_COINCIDE",
            f"Se esperaba '{requisito_id}' y se recibió '{requisito}'.",
            "requisito_id",
        )

    if not _texto_no_vacio(estado):
        _agregar(errores, "TIPO_INVALIDO", "Debe ser un texto no vacío.", "estado_propuesto")
    elif estado not in estados:
        _agregar(
            errores,
            "ESTADO_INVALIDO",
            f"'{estado}' no es uno de los cinco estados aprobados: "
            + ", ".join(sorted(estados))
            + ".",
            "estado_propuesto",
        )

    if not _es_booleano(encontrada):
        _agregar(
            errores,
            "TIPO_INVALIDO",
            "Debe ser verdadero o falso.",
            "evidencia_encontrada",
        )

    if not _es_booleano(revision):
        _agregar(
            errores,
            "TIPO_INVALIDO",
            "Debe ser verdadero o falso.",
            "requiere_revision_especializada",
        )

    if not _texto_no_vacio(observacion):
        _agregar(
            errores,
            "TIPO_INVALIDO",
            "La observación preliminar no puede estar vacía.",
            "observacion_preliminar",
        )
    elif len(observacion) > MAX_TEXTO:
        _agregar(
            errores,
            "TEXTO_DEMASIADO_LARGO",
            f"Supera {MAX_TEXTO} caracteres.",
            "observacion_preliminar",
        )

    if not _texto_no_vacio(motivo):
        _agregar(errores, "TIPO_INVALIDO", "El motivo no puede estar vacío.", "motivo")
    elif len(motivo) > MAX_TEXTO:
        _agregar(
            errores,
            "TEXTO_DEMASIADO_LARGO",
            f"Supera {MAX_TEXTO} caracteres.",
            "motivo",
        )

    if cita is not None and not isinstance(cita, str):
        _agregar(errores, "TIPO_INVALIDO", "La cita debe ser texto o nulo.", "cita")

    if fuente is not None and not isinstance(fuente, dict):
        _agregar(
            errores,
            "TIPO_INVALIDO",
            "La fuente debe ser un objeto o nulo.",
            "fuente",
        )

    # Reglas de coherencia entre estado, evidencia y fuente.
    if _es_booleano(encontrada):
        if encontrada:
            if not isinstance(fuente, dict):
                _agregar(
                    errores,
                    "FUENTE_OBLIGATORIA",
                    "Si hay evidencia, la fuente es obligatoria.",
                    "fuente",
                )
            if not _texto_no_vacio(cita):
                _agregar(
                    errores,
                    "CITA_OBLIGATORIA",
                    "Si hay evidencia, la cita textual es obligatoria.",
                    "cita",
                )
            elif len(cita.strip()) < MIN_CITA:
                _agregar(
                    errores,
                    "CITA_MUY_CORTA",
                    f"La cita debe tener al menos {MIN_CITA} caracteres.",
                    "cita",
                )
            elif len(cita) > MAX_CITA:
                _agregar(
                    errores,
                    "CITA_DEMASIADO_LARGA",
                    f"La cita supera {MAX_CITA} caracteres.",
                    "cita",
                )
        else:
            if fuente is not None:
                _agregar(
                    errores,
                    "FUENTE_NO_PERMITIDA",
                    "Si no hay evidencia, la fuente debe ser nula.",
                    "fuente",
                )
            if cita not in (None, ""):
                _agregar(
                    errores,
                    "CITA_NO_PERMITIDA",
                    "Si no hay evidencia, la cita debe ser nula o vacía.",
                    "cita",
                )
            if estado in ESTADOS_CONCLUYENTES:
                _agregar(
                    errores,
                    "EVIDENCIA_REQUERIDA",
                    f"El estado '{estado}' exige evidencia verificable.",
                    "estado_propuesto",
                )

    if estado == "No se encontró información":
        if encontrada is True:
            _agregar(
                errores,
                "ESTADO_INCOMPATIBLE",
                "'No se encontró información' no puede declarar evidencia encontrada.",
                "estado_propuesto",
            )
        if revision is True:
            _agregar(
                errores,
                "ESTADO_INCOMPATIBLE",
                "'No se encontró información' no debe exigir revisión especializada; "
                "use 'Requiere revisión especializada' si el caso lo amerita.",
                "requiere_revision_especializada",
            )

    if estado == "Requiere revisión especializada" and revision is False:
        _agregar(
            errores,
            "REVISION_INCONSISTENTE",
            "El estado exige 'requiere_revision_especializada = true'.",
            "requiere_revision_especializada",
        )

    if estado in ESTADOS_CONCLUYENTES and revision is True:
        _agregar(
            errores,
            "REVISION_INCONSISTENTE",
            f"El estado '{estado}' es concluyente y no puede exigir revisión especializada.",
            "requiere_revision_especializada",
        )

    # Validación de la fuente contra la evidencia recuperada.
    if isinstance(fuente, dict) and encontrada is True:
        _validar_fuente(fuente, cita, evidencias, errores)

    valida = not errores
    propuesta = None
    if valida:
        propuesta = Propuesta(
            requisito_id=str(requisito),
            estado_propuesto=str(estado),
            evidencia_encontrada=bool(encontrada),
            fuente=dict(fuente) if isinstance(fuente, dict) else None,
            cita=str(cita) if cita is not None else None,
            observacion_preliminar=str(observacion).strip(),
            requiere_revision_especializada=bool(revision),
            motivo=str(motivo).strip(),
        )
    return ResultadoValidacion(valida, propuesta, errores)


def _validar_fuente(
    fuente: dict[str, Any],
    cita: Any,
    evidencias: list[Evidencia],
    errores: list[ErrorContrato],
) -> None:
    for campo in CAMPOS_FUENTE:
        if campo not in fuente:
            _agregar(
                errores,
                "FUENTE_INCOMPLETA",
                f"Falta '{campo}' en la fuente.",
                f"fuente.{campo}",
            )
    if any(error.codigo == "FUENTE_INCOMPLETA" for error in errores):
        return

    documento_id = fuente.get("documento_id")
    archivo = fuente.get("archivo")
    ubicacion = fuente.get("ubicacion")
    sha256 = fuente.get("sha256")

    if not _es_entero(documento_id):
        _agregar(
            errores,
            "TIPO_INVALIDO",
            "documento_id debe ser un entero.",
            "fuente.documento_id",
        )
    if not _texto_no_vacio(archivo):
        _agregar(
            errores, "TIPO_INVALIDO", "archivo debe ser texto.", "fuente.archivo"
        )
    if not _texto_no_vacio(ubicacion):
        _agregar(
            errores, "TIPO_INVALIDO", "ubicacion debe ser texto.", "fuente.ubicacion"
        )
    if not isinstance(sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", sha256):
        _agregar(
            errores,
            "HASH_INVALIDO",
            "sha256 debe ser un hash hexadecimal de 64 caracteres.",
            "fuente.sha256",
        )

    if any(
        error.codigo in {"TIPO_INVALIDO", "HASH_INVALIDO"}
        and (error.campo or "").startswith("fuente")
        for error in errores
    ):
        return

    candidatas = [
        evidencia
        for evidencia in evidencias
        if evidencia.documento_id == documento_id
    ]
    if not candidatas:
        _agregar(
            errores,
            "FUENTE_NO_CORRESPONDE",
            f"El documento {documento_id} no está entre la evidencia recuperada.",
            "fuente.documento_id",
        )
        return

    evidencia = next(
        (
            item
            for item in candidatas
            if item.archivo == archivo and item.ubicacion == ubicacion
        ),
        None,
    )
    if evidencia is None:
        _agregar(
            errores,
            "UBICACION_NO_CORRESPONDE",
            f"No existe el fragmento '{archivo}' · '{ubicacion}' en la evidencia.",
            "fuente.ubicacion",
        )
        return

    if evidencia.sha256_fuente.lower() != str(sha256).lower():
        _agregar(
            errores,
            "HASH_NO_COINCIDE",
            "El SHA-256 no coincide con el documento fuente registrado.",
            "fuente.sha256",
        )

    if _texto_no_vacio(cita) and not cita_en_texto(str(cita), evidencia.texto):
        _agregar(
            errores,
            "CITA_NO_ENCONTRADA",
            "La cita no aparece textualmente en el fragmento citado.",
            "cita",
        )
