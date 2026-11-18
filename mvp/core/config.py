"""Parámetros de configuración del MVP (Etapa 2).

Todos los valores pueden sobreescribirse con variables de entorno para no
depender de rutas absolutas ni de credenciales dentro del código.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- Rutas ---------------------------------------------------------------

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
DIR_MVP = RAIZ_PROYECTO / "mvp"

DIR_DATOS = Path(os.environ.get("MVP_DATA_DIR", DIR_MVP / "data"))
DIR_UPLOADS = DIR_DATOS / "uploads"
DIR_CACHE = DIR_DATOS / "cache"
RUTA_BD = Path(os.environ.get("MVP_DB_PATH", DIR_DATOS / "mvp.db"))

DIR_ETAPA1 = DIR_MVP / "etapa1"
DIR_ETAPA2 = DIR_MVP / "etapa2"
DIR_ETAPA3 = DIR_MVP / "etapa3"
DIR_ETAPA4 = DIR_MVP / "etapa4"
DIR_ETAPA5 = DIR_MVP / "etapa5"
DIR_ETAPA6 = DIR_MVP / "etapa6"
DIR_EVIDENCIA = DIR_ETAPA2 / "evidencia"
DIR_EVIDENCIA_ETAPA3 = DIR_ETAPA3 / "evidencia"
DIR_EVIDENCIA_ETAPA4 = DIR_ETAPA4 / "evidencia"
DIR_EVIDENCIA_ETAPA5 = DIR_ETAPA5 / "evidencia"
DIR_EVIDENCIA_ETAPA6 = DIR_ETAPA6 / "evidencia"
DIR_MUESTRAS = DIR_ETAPA2 / "muestras"
DIR_MUESTRAS_ETAPA3 = DIR_ETAPA3 / "muestras"
DIR_MUESTRAS_ETAPA4 = DIR_ETAPA4 / "muestras"
DIR_MUESTRAS_ETAPA5 = DIR_ETAPA5 / "muestras"
DIR_MUESTRAS_ETAPA6 = DIR_ETAPA6 / "muestras"

RUTA_KB = DIR_ETAPA1 / "03_base_conocimiento" / "checklist_v1.json"
RUTA_SEMILLA = DIR_ETAPA1 / "05_datos_semilla.json"
RUTA_PERFILES_EVIDENCIA = DIR_ETAPA3 / "config" / "requisitos_evidencia.json"
RUTA_USUARIOS = Path(
    os.environ.get("MVP_USUARIOS_PATH", DIR_ETAPA5 / "config" / "usuarios.json")
)

# --- Procesamiento -------------------------------------------------------

FORMATOS_PERMITIDOS = {".pdf", ".docx", ".xlsx"}
TAMANO_MAXIMO_MB = 25
TAMANO_MAXIMO_BYTES = TAMANO_MAXIMO_MB * 1024 * 1024

#: Versión del extractor. Forma parte de la clave de caché: si cambia la lógica
#: de extracción, el caché anterior se ignora de forma controlada.
EXTRACTOR_VERSION = "1.0.0"

#: Confianza mínima (0-100) para dar una clasificación por válida.
UMBRAL_CONFIANZA = 70

#: Máximo de fragmentos por documento para evitar crecimientos desmedidos.
MAX_FRAGMENTOS = 2000

#: Número de filas de una hoja XLSX que se procesan como texto.
MAX_FILAS_XLSX = 2000

# --- Servicio de IA (opcional, Etapa 3) ----------------------------------

IA_BASE_URL = os.environ.get("MVP_IA_BASE_URL", "https://api.openai.com/v1")
IA_MODELO = os.environ.get("MVP_IA_MODEL", "gpt-4o-mini")
IA_API_KEY = os.environ.get("MVP_IA_API_KEY", "")
IA_TIMEOUT = int(os.environ.get("MVP_IA_TIMEOUT", "30"))
IA_MAX_INTENTOS = int(os.environ.get("MVP_IA_MAX_INTENTOS", "3"))

#: Número máximo de fragmentos de evidencia enviados a la IA por requisito.
IA_MAX_EVIDENCIAS = 3
#: Recorte de texto por fragmento para controlar el consumo de tokens.
IA_MAX_CARACTERES_EVIDENCIA = 900
#: Pausa base entre reintentos (segundos).
IA_ESPERA_REINTENTO = 0.5

ESTADOS_REQUISITO = (
    "Cumple",
    "Cumple parcialmente",
    "No cumple",
    "No se encontró información",
    "Requiere revisión especializada",
)

EXPEDIENTE_DEFECTO = "EXP-2024-089"
EXPEDIENTE_BORDES = "EXP-2024-089-BORDES"

ESTADOS_DOCUMENTO = ("VALIDO", "RECHAZADO")
TEXTO_RECUPERABLE = ("si", "parcial", "no")


def rutas_datos() -> dict[str, str]:
    """Devuelve las rutas efectivas para mostrarlas en la interfaz y los reportes."""

    return {
        "raiz_proyecto": str(RAIZ_PROYECTO),
        "datos": str(DIR_DATOS),
        "uploads": str(DIR_UPLOADS),
        "base_datos": str(RUTA_BD),
        "base_conocimiento": str(RUTA_KB),
        "perfiles_evidencia": str(RUTA_PERFILES_EVIDENCIA),
        "muestras": str(DIR_MUESTRAS),
        "muestras_etapa3": str(DIR_MUESTRAS_ETAPA3),
        "evidencia": str(DIR_EVIDENCIA),
        "evidencia_etapa3": str(DIR_EVIDENCIA_ETAPA3),
        "evidencia_etapa4": str(DIR_EVIDENCIA_ETAPA4),
        "evidencia_etapa5": str(DIR_EVIDENCIA_ETAPA5),
        "muestras_etapa4": str(DIR_MUESTRAS_ETAPA4),
        "muestras_etapa5": str(DIR_MUESTRAS_ETAPA5),
        "evidencia_etapa6": str(DIR_EVIDENCIA_ETAPA6),
        "muestras_etapa6": str(DIR_MUESTRAS_ETAPA6),
        "usuarios": str(RUTA_USUARIOS),
        "ia_configurada": bool(IA_API_KEY),
        "ia_modelo": IA_MODELO,
    }


def preparar_directorios() -> None:
    """Crea los directorios de trabajo si no existen."""

    for directorio in (
        DIR_DATOS,
        DIR_UPLOADS,
        DIR_CACHE,
        DIR_EVIDENCIA,
        DIR_EVIDENCIA_ETAPA3,
        DIR_EVIDENCIA_ETAPA4,
        DIR_EVIDENCIA_ETAPA5,
        DIR_EVIDENCIA_ETAPA6,
        DIR_MUESTRAS_ETAPA6,
    ):
        directorio.mkdir(parents=True, exist_ok=True)
