"""Configuración de pruebas: raíz del proyecto y corpus compartido."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from mvp.scripts.generar_muestras import generar_corpus  # noqa: E402
from mvp.scripts.generar_muestras_etapa3 import generar_corpus_etapa3  # noqa: E402


@pytest.fixture(scope="session")
def corpus(tmp_path_factory: pytest.TempPathFactory) -> dict:
    destino = tmp_path_factory.mktemp("corpus_etapa2")
    return generar_corpus(destino)


@pytest.fixture(scope="session")
def corpus_etapa3(tmp_path_factory: pytest.TempPathFactory) -> dict:
    destino = tmp_path_factory.mktemp("corpus_etapa3")
    return generar_corpus_etapa3(destino)
