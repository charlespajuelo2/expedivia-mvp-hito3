"""Cálculo de hashes SHA-256 para integridad documental."""

from __future__ import annotations

import hashlib
from pathlib import Path

BLOQUE_BYTES = 1024 * 1024


def hash_bytes(datos: bytes) -> str:
    """Devuelve el SHA-256 hexadecimal de un bloque de bytes."""

    return hashlib.sha256(datos).hexdigest()


def hash_archivo(ruta: str | Path, bloque: int = BLOQUE_BYTES) -> str:
    """Calcula el SHA-256 de un archivo leyéndolo por bloques.

    Se lee por bloques para no cargar en memoria archivos grandes.
    """

    ruta = Path(ruta)
    digest = hashlib.sha256()
    with ruta.open("rb") as manejador:
        while True:
            trozo = manejador.read(bloque)
            if not trozo:
                break
            digest.update(trozo)
    return digest.hexdigest()


def hash_texto(texto: str) -> str:
    """SHA-256 de un texto en UTF-8 (útil para huellas de fragmentos)."""

    return hash_bytes(texto.encode("utf-8"))
