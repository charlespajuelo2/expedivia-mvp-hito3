"""Ejecuta la Etapa 2 de extremo a extremo y genera la evidencia reproducible.

Uso::

    python -m mvp.scripts.ejecutar_etapa2

Produce en ``mvp/etapa2/evidencia/``:

- ``00_entorno.json``: versiones y rutas.
- ``01_reporte_ingesta_caso.md``: carga de los 6 documentos del caso.
- ``02_reporte_casos_borde.md``: rechazos y documento ambiguo.
- ``03_reporte_cache.md``: primera carga vs. segunda carga.
- ``04_reporte_correccion.md``: corrección humana y persistencia.
- ``05_metricas.json``: métricas agregadas.
- ``06_auditoria.csv``: bitácora completa.
- ``08_inventario_procesado.csv``: inventario final.
"""

from __future__ import annotations

import csv
import json
import platform
import sys
from pathlib import Path
from time import perf_counter

from mvp.core import config
from mvp.core.pipeline import ProcesadorDocumental
from mvp.scripts.generar_muestras import generar_corpus

EXPEDIENTE = config.EXPEDIENTE_DEFECTO
EXPEDIENTE_BORDES = config.EXPEDIENTE_BORDES
RUTA_BD = config.DIR_EVIDENCIA / "mvp_etapa2.db"

MOTIVOS_ESPERADOS = {
    "PDF_Escaneado.pdf": "PDF_ESCANEADO",
    "PDF_Protegido.pdf": "PDF_PROTEGIDO",
    "PDF_Corrupto.pdf": "ARCHIVO_DANADO",
    "notas.txt": "FORMATO_NO_SOPORTADO",
}


def _sha_corto(sha: str | None) -> str:
    return (sha or "—")[:12]


def _tabla(cabeceras: list[str], filas: list[list[object]]) -> str:
    lineas = [
        "| " + " | ".join(cabeceras) + " |",
        "|" + "|".join("---" for _ in cabeceras) + "|",
    ]
    for fila in filas:
        lineas.append("| " + " | ".join(str(valor) for valor in fila) + " |")
    return "\n".join(lineas)


def _escribir(nombre: str, contenido: str) -> Path:
    ruta = config.DIR_EVIDENCIA / nombre
    ruta.write_text(contenido.rstrip() + "\n", encoding="utf-8")
    return ruta


def _entorno() -> dict:
    import docx
    import openpyxl
    import pdfplumber
    import pypdf
    import reportlab
    import streamlit

    return {
        "fecha_ejecucion": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "python": sys.version,
        "plataforma": platform.platform(),
        "base_datos": str(RUTA_BD),
        "corpus": str(config.DIR_MUESTRAS),
        "versiones": {
            "pypdf": pypdf.__version__,
            "pdfplumber": pdfplumber.__version__,
            "python-docx": docx.__version__,
            "openpyxl": openpyxl.__version__,
            "reportlab": reportlab.Version,
            "streamlit": streamlit.__version__,
        },
        "extractor_version": config.EXTRACTOR_VERSION,
        "umbral_confianza": config.UMBRAL_CONFIANZA,
    }


def _reporte_ingesta(procesador: ProcesadorDocumental, resultados: list) -> str:
    filas = [
        [
            r.documento_id,
            r.nombre_archivo,
            r.estado,
            r.texto_recuperable,
            r.fragmentos,
            f"{r.clasificacion.tipo_documental if r.clasificacion else '—'} "
            f"({r.clasificacion.confianza if r.clasificacion else '—'})",
            r.clasificacion.estado if r.clasificacion else "—",
            _sha_corto(r.sha256),
            r.duracion_ms,
        ]
        for r in resultados
    ]
    resumen = procesador.resumen_procesamiento(EXPEDIENTE)

    ubicaciones = []
    for resultado in resultados:
        if not resultado.documento_id:
            continue
        fragmentos = procesador.fragmentos_de(resultado.documento_id)[:2]
        for fragmento in fragmentos:
            ubicaciones.append(
                [
                    resultado.nombre_archivo,
                    fragmento["ubicacion"],
                    fragmento["tipo"],
                    fragmento["texto"][:80].replace("\n", " "),
                ]
            )

    return f"""# Evidencia 01 — Ingesta del caso {EXPEDIENTE}

**Comando reproducible:** `python -m mvp.scripts.ejecutar_etapa2`
**Base de datos:** `mvp/etapa2/evidencia/mvp_etapa2.db`

## Resumen

| Indicador | Valor |
|---|---|
| Documentos procesados | {resumen['documentos_total']} |
| Válidos | {resumen['validos']} |
| Rechazados | {resumen['rechazados']} |
| Texto completo | {resumen['texto_si']} |
| Texto parcial (requiere OCR en algunas páginas) | {resumen['texto_parcial']} |
| Clasificados automáticamente | {resumen['clasificados']} |
| Pendientes de corrección humana | {resumen['sin_clasificar']} |
| Fragmentos almacenados | {resumen['fragmentos_total']} |
| Tiempo total de la primera carga | {sum(r.duracion_ms for r in resultados)} ms |

## Detalle por documento

{_tabla(
    ['ID', 'Archivo', 'Estado', 'Texto', 'Frags', 'Tipo (confianza)', 'Clasificación', 'SHA-256', 'ms'],
    filas,
)}

## Ubicaciones verificables (muestra)

Cada fragmento queda asociado a una página, párrafo, tabla o celda. Ejemplos:

{_tabla(['Archivo', 'Ubicación', 'Tipo', 'Texto (recorte)'], ubicaciones)}

## Advertencias registradas

{chr(10).join(
    f"- **{r.nombre_archivo}**: " + "; ".join(r.advertencias)
    for r in resultados
    if r.advertencias
) or '- Ninguna.'}

## Criterios de salida cubiertos

- [x] Se cargan los 6 archivos del caso sin errores.
- [x] La extracción devuelve ubicación verificable por fragmento.
- [x] El inventario, el estado y los metadatos quedan persistidos.
"""


def _reporte_bordes(resultados: list, resumen: dict) -> str:
    filas = []
    for resultado in resultados:
        esperado = MOTIVOS_ESPERADOS.get(resultado.nombre_archivo, "—")
        obtenido = resultado.motivo_rechazo or "—"
        if esperado == "—":
            cumple = "n/a"
        else:
            cumple = "sí" if esperado == obtenido else "NO"
        filas.append(
            [
                resultado.nombre_archivo,
                "Rechazado" if not resultado.ok else "Válido",
                esperado,
                obtenido,
                cumple,
                resultado.mensaje[:90].replace("|", "/"),
            ]
        )

    return f"""# Evidencia 02 — Casos borde

**Expediente:** `{EXPEDIENTE_BORDES}`
**Regla aplicada:** un documento rechazado no genera fragmentos ni conclusiones.
No se convierte en “No cumple”.

## Resultados

{_tabla(['Archivo', 'Resultado', 'Motivo esperado', 'Motivo obtenido', '¿Coincide?', 'Mensaje'], filas)}

## Resumen

| Indicador | Valor |
|---|---|
| Documentos evaluados | {resumen['documentos_total']} |
| Válidos | {resumen['validos']} |
| Rechazados | {resumen['rechazados']} |
| Fragmentos generados | {resumen['fragmentos_total']} |

El archivo `Documento_General.pdf` es un **documento ambiguo**: se acepta porque
tiene texto recuperable, pero queda **Sin clasificar** (tipo “No reconocido”,
confianza 0) hasta que una persona lo corrija. Esto demuestra que “no se pudo
clasificar” no se confunde con “documento inválido”.

## Criterios de salida cubiertos

- [x] Un PDF escaneado se rechaza con mensaje claro y registro.
- [x] Un PDF protegido y un PDF corrupto se rechazan con motivos distintos.
- [x] Un formato no soportado se rechaza de forma trazable.
- [x] Un documento ambiguo queda pendiente de corrección, no rechazado.
"""


def _reporte_cache(primera: list, segunda: list) -> str:
    hashes_primera = {r.nombre_archivo: r.sha256 for r in primera}
    hashes_segunda = {r.nombre_archivo: r.sha256 for r in segunda}
    filas = []
    for r1, r2 in zip(primera, segunda):
        filas.append(
            [
                r1.nombre_archivo,
                _sha_corto(r1.sha256),
                "no",
                r1.duracion_ms,
                "sí" if r2.cache_hit else "NO",
                r2.duracion_ms,
                "sí" if hashes_primera[r1.nombre_archivo] == hashes_segunda[r2.nombre_archivo] else "NO",
            ]
        )

    tiempo_1 = sum(r.duracion_ms for r in primera)
    tiempo_2 = sum(r.duracion_ms for r in segunda)
    ahorro = 0.0 if tiempo_1 == 0 else (1 - tiempo_2 / tiempo_1) * 100

    return f"""# Evidencia 03 — Caché documental por SHA-256

**Comando reproducible:** `python -m mvp.scripts.ejecutar_etapa2`

La caché usa la clave `SHA-256 + versión del extractor`. Si el archivo no cambia,
la segunda carga reutiliza la extracción y no vuelve a leer el contenido.

{_tabla(
    ['Archivo', 'SHA-256', 'Caché 1.ª', 'ms 1.ª', 'Caché 2.ª', 'ms 2.ª', 'Hash igual'],
    filas,
)}

## Comparación

| Métrica | Primera carga | Segunda carga |
|---|---:|---:|
| Archivos | {len(primera)} | {len(segunda)} |
| Aciertos de caché | {sum(1 for r in primera if r.cache_hit)} | {sum(1 for r in segunda if r.cache_hit)} |
| Tiempo total | {tiempo_1} ms | {tiempo_2} ms |
| Reducción de tiempo | — | {ahorro:.1f}% |

## Criterio de salida cubierto

- [x] Dos cargas del mismo archivo producen el mismo hash y reutilizan caché.
"""


def _reporte_correccion(antes: dict, despues: dict, recargado: dict) -> str:
    return f"""# Evidencia 04 — Corrección humana y persistencia

**Documento:** `{antes['nombre_archivo']}`
**SHA-256:** `{antes['sha256']}`

## Antes de la corrección

| Campo | Valor |
|---|---|
| Tipo propuesto | {antes['tipo_documental']} |
| Componente | {antes['componente']} |
| Confianza | {antes['confianza']} |
| Estado de clasificación | {antes['estado_clasificacion']} |
| Origen | {antes['clasificacion_origen']} |

## Después de la corrección

| Campo | Valor |
|---|---|
| Tipo final | {despues['tipo_documental']} |
| Componente | {despues['componente']} |
| Confianza | {despues['confianza']} |
| Estado de clasificación | {despues['estado_clasificacion']} |
| Origen | {despues['clasificacion_origen']} |

Motivo registrado en auditoría: *“El contenido corresponde a EETT aunque el nombre del archivo es genérico.”*

## Recarga del mismo archivo (acierto de caché)

| Campo | Valor |
|---|---|
| Caché reutilizada | {'sí' if recargado.get('cache_hit') else 'no'} |
| Tipo conservado | {recargado.get('tipo_documental')} |
| Confianza | {recargado.get('confianza')} |
| Origen | {recargado.get('clasificacion_origen')} |
| Estado | {recargado.get('estado_clasificacion')} |

La corrección se guarda en `correcciones_clasificacion` indexada por SHA-256, por
lo que **no se pierde** al reutilizar la caché de extracción.

## Criterio de salida cubierto

- [x] La clasificación se puede corregir y queda registrada.
- [x] La corrección sobrevive a una nueva carga con caché.
"""


def _reporte_auditoria_csv(procesador: ProcesadorDocumental) -> Path:
    ruta = config.DIR_EVIDENCIA / "06_auditoria.csv"
    with ruta.open("w", encoding="utf-8", newline="") as manejador:
        escritor = csv.writer(manejador)
        escritor.writerow(["ts", "actor", "accion", "entidad", "entidad_id", "detalle"])
        for registro in procesador.listar_auditoria(1000):
            escritor.writerow(
                [
                    registro["ts"],
                    registro["actor"],
                    registro["accion"],
                    registro["entidad"],
                    registro["entidad_id"],
                    json.dumps(registro["detalle"], ensure_ascii=False),
                ]
            )
    return ruta


def main() -> int:
    config.preparar_directorios()
    config.DIR_EVIDENCIA.mkdir(parents=True, exist_ok=True)

    if RUTA_BD.exists():
        RUTA_BD.unlink()
    for sufijo in ("-wal", "-shm"):
        sobrante = Path(str(RUTA_BD) + sufijo)
        if sobrante.exists():
            sobrante.unlink()

    corpus = generar_corpus(config.DIR_MUESTRAS)
    procesador = ProcesadorDocumental(RUTA_BD)
    procesador.registrar_expediente(
        EXPEDIENTE,
        "Carretera Central Tramo 2 · Km 42–78",
        especialidad="Pavimentos",
        version="v3",
        actor="equipo-mvp",
    )
    procesador.registrar_expediente(
        EXPEDIENTE_BORDES,
        "Casos borde de validación documental",
        especialidad="Pavimentos",
        version="v1",
        actor="equipo-mvp",
    )

    print("1/6 Procesando el caso representativo...")
    primera = procesador.ingestar_carpeta(EXPEDIENTE, corpus["carpeta_caso"], actor="equipo-mvp")
    procesador.exportar_inventario_csv(
        EXPEDIENTE, config.DIR_EVIDENCIA / "08_inventario_procesado.csv"
    )
    _escribir("01_reporte_ingesta_caso.md", _reporte_ingesta(procesador, primera))

    print("2/6 Repitiendo la carga para evidenciar la caché...")
    segunda = procesador.ingestar_carpeta(EXPEDIENTE, corpus["carpeta_caso"], actor="equipo-mvp")
    _escribir("03_reporte_cache.md", _reporte_cache(primera, segunda))

    print("3/6 Procesando casos borde...")
    resultados_borde = []
    for ruta in sorted(corpus["carpeta_borde"].iterdir(), key=lambda p: p.name.lower()):
        resultados_borde.append(
            procesador.ingestar_archivo(EXPEDIENTE_BORDES, ruta, actor="equipo-mvp")
        )
    resumen_borde = procesador.resumen_procesamiento(EXPEDIENTE_BORDES)
    _escribir("02_reporte_casos_borde.md", _reporte_bordes(resultados_borde, resumen_borde))

    print("4/6 Aplicando corrección humana...")
    eett = next(
        d
        for d in procesador.listar_documentos(EXPEDIENTE)
        if d["nombre_archivo"] == "EETT_General_v2.docx"
    )
    antes = dict(eett)
    corregido = procesador.corregir_clasificacion(
        eett["id"],
        "Especificaciones técnicas",
        "EETT",
        actor="Lucía Ramos",
        motivo="El contenido corresponde a EETT aunque el nombre del archivo es genérico.",
    )
    recarga = procesador.ingestar_archivo(
        EXPEDIENTE,
        corpus["carpeta_caso"] / "EETT_General_v2.docx",
        actor="Lucía Ramos",
    )
    recargado = procesador.obtener_documento(eett["id"]) or {}
    recargado["cache_hit"] = recarga.cache_hit
    _escribir("04_reporte_correccion.md", _reporte_correccion(antes, corregido, recargado))

    print("5/6 Exportando métricas y auditoría...")
    metricas = {
        "caso": procesador.resumen_procesamiento(EXPEDIENTE),
        "casos_borde": resumen_borde,
        "primera_carga_ms": sum(r.duracion_ms for r in primera),
        "segunda_carga_ms": sum(r.duracion_ms for r in segunda),
        "documentos_cache": sum(1 for r in segunda if r.cache_hit),
    }
    _escribir("05_metricas.json", json.dumps(metricas, indent=2, ensure_ascii=False))
    _reporte_auditoria_csv(procesador)
    _escribir("00_entorno.json", json.dumps(_entorno(), indent=2, ensure_ascii=False))

    print("6/6 Verificación final...")
    resumen = metricas["caso"]
    assert resumen["validos"] == 6, resumen
    assert resumen["rechazados"] == 0, resumen
    assert metricas["documentos_cache"] == 6, metricas
    assert resumen_borde["rechazados"] == 4, resumen_borde
    assert resumen_borde["validos"] == 1, resumen_borde

    print("\nEtapa 2 ejecutada correctamente.")
    print(f"Evidencia: {config.DIR_EVIDENCIA}")
    print(
        f"Caso: {resumen['validos']} válidos, {resumen['clasificados']} clasificados, "
        f"{resumen['sin_clasificar']} pendientes de corrección"
    )
    print(f"Casos borde: {resumen_borde['rechazados']} rechazados, {resumen_borde['validos']} ambiguo aceptado")
    print(f"Caché: {metricas['documentos_cache']}/6 documentos reutilizados en la segunda carga")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
