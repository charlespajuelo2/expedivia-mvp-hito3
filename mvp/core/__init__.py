"""Núcleo del MVP: configuración, integridad, persistencia y procesamiento."""

from .classifier import Clasificacion, clasificar
from .extractors import ErrorExtraccion, Extraccion, Fragmento, extraer
from .hashing import hash_archivo, hash_bytes
from .pipeline import ProcesadorDocumental, ResultadoIngesta

__all__ = [
    "Clasificacion",
    "ErrorExtraccion",
    "Extraccion",
    "Fragmento",
    "ProcesadorDocumental",
    "ResultadoIngesta",
    "clasificar",
    "extraer",
    "hash_archivo",
    "hash_bytes",
]
