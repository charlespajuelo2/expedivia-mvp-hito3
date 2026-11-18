"""Persistencia SQLite del MVP.

Tablas principales:

- ``expedientes``: caso en revisión.
- ``documentos``: inventario procesado, con hash, estado y clasificación.
- ``fragmentos``: texto extraído con ubicación verificable.
- ``cache_extraccion``: extracción reutilizable por SHA-256.
- ``correcciones_clasificacion``: corrección humana por SHA-256, de modo que
  sobreviva a una nueva carga o a un acierto de caché.
- ``propuestas_ia``: propuesta automática con fuente; ``huella`` evita duplicar
  el mismo hallazgo al reejecutar el análisis.
- ``decisiones``: historial inmutable de aceptar / modificar / descartar. Cada
  fila conserva el estado propuesto original y el estado final decidido.
- ``auditoria``: bitácora de acciones.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from . import config

ESQUEMA = """
CREATE TABLE IF NOT EXISTS expedientes (
    id            TEXT PRIMARY KEY,
    nombre        TEXT NOT NULL,
    especialidad  TEXT,
    version       TEXT,
    creado_en     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documentos (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    expediente_id         TEXT NOT NULL REFERENCES expedientes(id),
    nombre_archivo        TEXT NOT NULL,
    ruta                  TEXT,
    formato               TEXT NOT NULL,
    tamano_bytes          INTEGER,
    sha256                TEXT,
    extractor_version     TEXT,
    estado                TEXT NOT NULL,
    motivo_rechazo        TEXT,
    mensaje               TEXT,
    texto_recuperable     TEXT,
    paginas               INTEGER,
    caracteres            INTEGER,
    fragmentos            INTEGER NOT NULL DEFAULT 0,
    cache_hit             INTEGER NOT NULL DEFAULT 0,
    tipo_documental       TEXT,
    componente            TEXT,
    confianza             INTEGER,
    clasificacion_origen  TEXT,
    advertencias          TEXT,
    duracion_ms           INTEGER,
    creado_en             TEXT NOT NULL,
    actualizado_en        TEXT NOT NULL,
    UNIQUE (expediente_id, nombre_archivo)
);

CREATE TABLE IF NOT EXISTS fragmentos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    documento_id INTEGER NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    orden        INTEGER NOT NULL,
    ubicacion    TEXT NOT NULL,
    tipo         TEXT NOT NULL,
    texto        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fragmentos_documento ON fragmentos(documento_id);

CREATE TABLE IF NOT EXISTS cache_extraccion (
    sha256            TEXT PRIMARY KEY,
    extractor_version TEXT NOT NULL,
    formato           TEXT NOT NULL,
    payload           TEXT NOT NULL,
    creado_en         TEXT NOT NULL,
    ultimo_uso        TEXT NOT NULL,
    hits              INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS correcciones_clasificacion (
    sha256           TEXT PRIMARY KEY,
    tipo_documental  TEXT NOT NULL,
    componente       TEXT NOT NULL,
    confianza        INTEGER NOT NULL,
    decidido_por     TEXT NOT NULL,
    motivo           TEXT NOT NULL,
    creado_en        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidencias (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    expediente_id     TEXT NOT NULL,
    requisito_id      TEXT NOT NULL,
    documento_id      INTEGER NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    fragmento_orden   INTEGER,
    archivo           TEXT NOT NULL,
    tipo_documental   TEXT,
    ubicacion         TEXT NOT NULL,
    sha256_fuente     TEXT NOT NULL,
    texto             TEXT NOT NULL,
    puntaje           INTEGER NOT NULL DEFAULT 0,
    terminos          TEXT,
    integridad        TEXT NOT NULL DEFAULT 'VIGENTE',
    creado_en         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidencias_requisito
    ON evidencias(expediente_id, requisito_id);

CREATE TABLE IF NOT EXISTS propuestas_ia (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    expediente_id     TEXT NOT NULL,
    requisito_id      TEXT NOT NULL,
    evidencia_id      INTEGER,
    proveedor         TEXT NOT NULL,
    modelo            TEXT,
    estado_propuesto  TEXT,
    evidencia_encontrada INTEGER,
    documento_id      INTEGER,
    archivo           TEXT,
    ubicacion         TEXT,
    sha256_fuente     TEXT,
    cita              TEXT,
    observacion       TEXT,
    requiere_revision INTEGER,
    motivo            TEXT,
    valida            INTEGER NOT NULL DEFAULT 0,
    errores           TEXT,
    integridad        TEXT NOT NULL DEFAULT 'VIGENTE',
    huella            TEXT,
    creado_en         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_propuestas_requisito
    ON propuestas_ia(expediente_id, requisito_id);

CREATE TABLE IF NOT EXISTS decisiones (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    expediente_id     TEXT NOT NULL,
    requisito_id      TEXT NOT NULL,
    propuesta_id      INTEGER REFERENCES propuestas_ia(id),
    decision          TEXT NOT NULL,
    estado_propuesto  TEXT,
    estado_final      TEXT NOT NULL,
    motivo            TEXT NOT NULL,
    actor             TEXT NOT NULL,
    version_kb        TEXT,
    huella_propuesta  TEXT,
    creado_en         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_decisiones_requisito
    ON decisiones(expediente_id, requisito_id, id);

CREATE TABLE IF NOT EXISTS ejecuciones_ia (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    expediente_id  TEXT NOT NULL,
    requisito_id   TEXT NOT NULL,
    proveedor      TEXT NOT NULL,
    modelo         TEXT,
    estado         TEXT NOT NULL,
    intentos       INTEGER NOT NULL DEFAULT 1,
    duracion_ms    INTEGER NOT NULL DEFAULT 0,
    tokens_entrada INTEGER NOT NULL DEFAULT 0,
    tokens_salida  INTEGER NOT NULL DEFAULT 0,
    error          TEXT,
    creado_en      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ejecuciones_expediente
    ON ejecuciones_ia(expediente_id, creado_en);

CREATE TABLE IF NOT EXISTS evaluaciones_manuales (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    expediente_id  TEXT NOT NULL,
    requisito_id   TEXT NOT NULL,
    estado         TEXT NOT NULL,
    motivo         TEXT NOT NULL,
    actor          TEXT NOT NULL,
    evidencia_id   INTEGER,
    creado_en      TEXT NOT NULL,
    UNIQUE (expediente_id, requisito_id)
);

CREATE TABLE IF NOT EXISTS integridad_eventos (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                 TEXT NOT NULL,
    expediente_id      TEXT NOT NULL,
    documento_id       INTEGER,
    archivo            TEXT,
    sha256_registrado  TEXT,
    sha256_actual      TEXT,
    estado             TEXT NOT NULL,
    detalle            TEXT
);

CREATE TABLE IF NOT EXISTS auditoria (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT NOT NULL,
    actor      TEXT NOT NULL,
    accion     TEXT NOT NULL,
    entidad    TEXT NOT NULL,
    entidad_id TEXT,
    detalle    TEXT
);

CREATE INDEX IF NOT EXISTS idx_auditoria_ts ON auditoria(ts);
"""


def ahora() -> str:
    """Marca temporal ISO-8601 con precisión de segundos."""

    return datetime.now().replace(microsecond=0).isoformat()


@contextmanager
def conectar(ruta_bd: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    """Abre una conexión con filas tipo diccionario y cierre garantizado."""

    ruta = Path(ruta_bd or config.RUTA_BD)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def inicializar(ruta_bd: str | Path | None = None) -> Path:
    """Crea el esquema si no existe y devuelve la ruta de la base."""

    ruta = Path(ruta_bd or config.RUTA_BD)
    with conectar(ruta) as conexion:
        conexion.executescript(ESQUEMA)
        # Migraciones ligeras para bases creadas en etapas anteriores.
        _asegurar_columnas(conexion, "evidencias", {"integridad": "TEXT NOT NULL DEFAULT 'VIGENTE'"})
        _asegurar_columnas(
            conexion,
            "propuestas_ia",
            {
                "integridad": "TEXT NOT NULL DEFAULT 'VIGENTE'",
                "huella": "TEXT",
            },
        )
        # El índice se crea después de la migración: una base de la Etapa 3 aún
        # no tiene la columna ``huella`` cuando se ejecuta el esquema.
        conexion.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_propuestas_huella "
            "ON propuestas_ia(expediente_id, requisito_id, huella)"
        )
    return ruta


def _asegurar_columnas(
    conexion: sqlite3.Connection, tabla: str, columnas: dict[str, str]
) -> None:
    """Agrega columnas faltantes sin perder los datos existentes."""

    existentes = {
        fila["name"]
        for fila in conexion.execute(f"PRAGMA table_info({tabla})").fetchall()
    }
    for nombre, definicion in columnas.items():
        if nombre not in existentes:
            conexion.execute(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}")


def auditar(
    conexion: sqlite3.Connection,
    *,
    actor: str,
    accion: str,
    entidad: str,
    entidad_id: str | int | None = None,
    detalle: dict[str, Any] | None = None,
) -> None:
    """Inserta un registro de auditoría dentro de una transacción existente."""

    conexion.execute(
        "INSERT INTO auditoria (ts, actor, accion, entidad, entidad_id, detalle) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            ahora(),
            actor,
            accion,
            entidad,
            None if entidad_id is None else str(entidad_id),
            None if detalle is None else json.dumps(detalle, ensure_ascii=False),
        ),
    )


def fila_a_dict(fila: sqlite3.Row | None) -> dict[str, Any] | None:
    """Convierte una fila SQLite en diccionario normal."""

    if fila is None:
        return None
    return {clave: fila[clave] for clave in fila.keys()}
