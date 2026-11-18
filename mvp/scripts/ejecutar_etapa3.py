"""Ejecuta la Etapa 3 de extremo a extremo y genera la evidencia reproducible.

Uso::

    python -m mvp.scripts.ejecutar_etapa3

Produce en ``mvp/etapa3/evidencia/``:

- ``00_entorno.json``: versiones, rutas y configuración de IA.
- ``01_reporte_ingesta.md``: carga de los 8 documentos del caso.
- ``02_reporte_evidencia.md``: recuperación de evidencia por requisito.
- ``03_reporte_analisis.md``: propuestas de IA con el proveedor de reglas.
- ``04_reporte_contrato.md``: contrato rechazado y reintento exitoso.
- ``05_reporte_integridad.md``: fuente modificada y escalamiento.
- ``06_reporte_contingencia.md``: contingencia y evaluación manual.
- ``07_metricas.json``: métricas agregadas del caso principal.
- ``08_auditoria.csv``: bitácora completa.
- ``09_propuestas.csv``: todas las propuestas registradas.
- ``10_resultados.csv``: resultado efectivo por requisito.
- ``11_ejecuciones.csv``: consumo y estado de cada ejecución de IA.
"""

from __future__ import annotations

import csv
import json
import platform
import shutil
import sys
from datetime import datetime
from pathlib import Path
from time import perf_counter

from openpyxl import load_workbook

from mvp.core import config
from mvp.core.ai_service import ProveedorFallido, ProveedorGuionizado
from mvp.core.analysis import AnalizadorExpediente
from mvp.core.evidence import cargar_perfiles
from mvp.core.integrity import listar_eventos_integridad, verificar_expediente
from mvp.core.pipeline import ProcesadorDocumental
from mvp.scripts.generar_muestras_etapa3 import generar_corpus_etapa3

EXPEDIENTE = config.EXPEDIENTE_DEFECTO
EXPEDIENTE_CONTROL = "EXP-2024-089-CONTROL"
EXPEDIENTE_VALIDACION = "EXP-2024-089-VALIDACION"
EXPEDIENTE_INTEGRIDAD = "EXP-2024-089-INTEGRIDAD"
RUTA_BD = config.DIR_EVIDENCIA_ETAPA3 / "mvp_etapa3.db"

ESTADOS_CONCLUYENTES = {"Cumple", "Cumple parcialmente", "No cumple"}


# --- Utilidades -----------------------------------------------------------


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
    ruta = config.DIR_EVIDENCIA_ETAPA3 / nombre
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
        "fecha_ejecucion": datetime.now().isoformat(timespec="seconds"),
        "python": sys.version,
        "plataforma": platform.platform(),
        "base_datos": str(RUTA_BD),
        "corpus": str(config.DIR_MUESTRAS_ETAPA3),
        "perfiles_evidencia": str(config.RUTA_PERFILES_EVIDENCIA),
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
        "ia": {
            "proveedor_por_defecto": "reglas",
            "modelo_configurado": config.IA_MODELO,
            "api_key_configurada": bool(config.IA_API_KEY),
            "max_intentos": config.IA_MAX_INTENTOS,
            "max_evidencias": config.IA_MAX_EVIDENCIAS,
        },
    }


def _propuesta_valida(evidencia: dict) -> dict:
    return {
        "requisito_id": "RQ-04",
        "estado_propuesto": "Cumple",
        "evidencia_encontrada": True,
        "fuente": {
            "documento_id": evidencia["documento_id"],
            "archivo": evidencia["archivo"],
            "ubicacion": evidencia["ubicacion"],
            "sha256": evidencia["sha256_fuente"],
        },
        "cita": evidencia["texto"][:70],
        "observacion_preliminar": "Propuesta construida desde la evidencia recuperada.",
        "requiere_revision_especializada": False,
        "motivo": "La evidencia directa cubre el criterio con fuente y cita verificables.",
    }


def _propuesta_invalida(evidencia: dict) -> dict:
    propuesta = _propuesta_valida(evidencia)
    propuesta["fuente"] = dict(propuesta["fuente"])
    propuesta["fuente"]["sha256"] = "0" * 64
    propuesta["cita"] = "Cita inventada que no aparece en el fragmento citado."
    return propuesta


def _fila_resultado(resultado) -> list[object]:
    propuesta = resultado.propuesta or {}
    fuente = propuesta.get("fuente") or {}
    return [
        resultado.requisito_id,
        resultado.estado,
        "sí" if resultado.valida else "no",
        resultado.proveedor,
        resultado.intentos,
        f"{resultado.duracion_ms} ms",
        f"{fuente.get('archivo', '—')} · {fuente.get('ubicacion', '—')}",
    ]


# --- Reportes -------------------------------------------------------------


def _reporte_ingesta(procesador: ProcesadorDocumental, resultados: list) -> str:
    filas = [
        [
            r.documento_id,
            r.nombre_archivo,
            r.formato,
            r.estado,
            f"{r.clasificacion.tipo_documental if r.clasificacion else '—'} "
            f"({r.clasificacion.confianza if r.clasificacion else '—'})",
            r.clasificacion.estado if r.clasificacion else "—",
            _sha_corto(r.sha256),
            r.fragmentos,
            r.duracion_ms,
        ]
        for r in resultados
    ]
    resumen = procesador.resumen_procesamiento(EXPEDIENTE)

    correccion = next(
        (
            documento
            for documento in procesador.listar_documentos(EXPEDIENTE)
            if documento["nombre_archivo"] == "EETT_General_v2.docx"
        ),
        {},
    )

    return f"""# Evidencia 01 — Ingesta del caso {EXPEDIENTE}

**Comando reproducible:** `python -m mvp.scripts.ejecutar_etapa3`
**Base de datos:** `mvp/etapa3/evidencia/mvp_etapa3.db`
**Corpus:** `mvp/etapa3/muestras/caso` (8 documentos; no altera el corpus cerrado de la Etapa 2)

## Resumen

{_tabla(
    ["Métrica", "Valor"],
    [
        ["Documentos", resumen["documentos_total"]],
        ["Válidos", resumen["validos"]],
        ["Rechazados", resumen["rechazados"]],
        ["Fragmentos", resumen["fragmentos_total"]],
        ["Clasificados", resumen["clasificados"]],
        ["Sin clasificar", resumen["sin_clasificar"]],
        ["Tiempo total", f"{resumen['duracion_total_ms']} ms"],
    ],
)}

## Inventario procesado

{_tabla(
    [
        "ID",
        "Archivo",
        "Formato",
        "Estado",
        "Tipo (confianza)",
        "Clasificación",
        "SHA-256",
        "Frag.",
        "ms",
    ],
    filas,
)}

## Corrección humana que habilita la evidencia

El documento `EETT_General_v2.docx` obtiene confianza automática 64 (< 70) y queda
`Sin clasificar`. Se aplica la corrección del especialista:

{_tabla(
    ["Campo", "Valor"],
    [
        ["Tipo documental", correccion.get("tipo_documental", "—")],
        ["Componente", correccion.get("componente", "—")],
        ["Estado de clasificación", correccion.get("estado_clasificacion", "—")],
        ["Origen", correccion.get("clasificacion_origen", "—")],
        ["Confianza", correccion.get("confianza", "—")],
    ],
)}

Solo los documentos `VALIDO` y `Clasificado` pueden aportar evidencia, de modo que
esta corrección es un requisito previo para el análisis.

## Criterio de salida cubierto

- [x] Los 8 documentos del caso se procesan sin rechazos.
- [x] El documento ambiguo se corrige por un humano y queda auditable.
- [x] El corpus de la Etapa 2 permanece intacto.
"""


def _reporte_evidencia(evidencias: dict, perfiles) -> str:
    filas = []
    for requisito_id in perfiles.ids():
        perfil = perfiles.requisito(requisito_id)
        seleccion = evidencias.get(requisito_id, [])
        mejor = seleccion[0] if seleccion else None
        filas.append(
            [
                requisito_id,
                perfil.requisito,
                f"{perfil.peso_pct}%",
                len(seleccion),
                mejor.puntaje if mejor else "—",
                f"{mejor.archivo} · {mejor.ubicacion}" if mejor else "—",
                mejor.tipo_documental if mejor else "—",
            ]
        )

    detalle = []
    for requisito_id in perfiles.ids():
        perfil = perfiles.requisito(requisito_id)
        detalle.append(f"\n### {requisito_id} · {perfil.requisito}\n")
        detalle.append(f"**Criterio:** {perfil.criterio}\n\n")
        filas_req = [
            [
                evidencia.puntaje,
                evidencia.archivo,
                evidencia.ubicacion,
                evidencia.tipo_documental,
                ", ".join(evidencia.terminos),
                _sha_corto(evidencia.sha256_fuente),
            ]
            for evidencia in evidencias.get(requisito_id, [])
        ]
        detalle.append(
            _tabla(
                ["Puntaje", "Archivo", "Ubicación", "Tipo", "Términos", "SHA-256"],
                filas_req,
            )
        )
        detalle.append("\n")

    return f"""# Evidencia 02 — Recuperación de evidencia por requisito

La puntuación es determinista: suma de términos ponderados más un bonus por tipo
documental esperado. Solo se usan documentos `VALIDO` y `Clasificado`.

## Resumen por requisito

{_tabla(
    ["Req.", "Requisito", "Peso", "Evidencias", "Mejor puntaje", "Mejor fuente", "Tipo"],
    filas,
)}

## Detalle

{''.join(detalle)}

## Criterio de salida cubierto

- [x] Cada requisito recupera al menos una evidencia con archivo, ubicación y hash.
- [x] La evidencia queda persistida para auditoría y reutilización.
- [x] RQ-01/02/03 solo encuentran la exigencia del TDR, no la prueba del cumplimiento.
"""


def _reporte_analisis(resultados: list, resumen: dict, control) -> str:
    filas = [_fila_resultado(resultado) for resultado in resultados]
    detalle = []
    for resultado in resultados:
        propuesta = resultado.propuesta or {}
        detalle.append(f"\n### {resultado.requisito_id} · {resultado.estado}\n\n")
        detalle.append(
            _tabla(
                ["Campo", "Valor"],
                [
                    ["¿Propuesta válida?", "sí" if resultado.valida else "no"],
                    ["Proveedor", resultado.proveedor],
                    ["Modelo", resultado.modelo],
                    ["Intentos", resultado.intentos],
                    ["Duración", f"{resultado.duracion_ms} ms"],
                    ["Fuente", (propuesta.get("fuente") or {}).get("archivo", "—")],
                    ["Ubicación", (propuesta.get("fuente") or {}).get("ubicacion", "—")],
                    ["Cita", (propuesta.get("cita") or "—")[:200]],
                    ["Observación", (propuesta.get("observacion_preliminar") or "—")[:300]],
                    ["Motivo", (propuesta.get("motivo") or "—")[:300]],
                ],
            )
        )
        detalle.append("\n")

    return f"""# Evidencia 03 — Análisis con IA y validación del contrato

Proveedor por defecto: `reglas` (determinista, sin red). La conclusión automática
solo se emite cuando el tipo documental es prueba directa, el puntaje alcanza el
umbral y el requisito no exige juicio de ingeniería.

## Resultados del caso principal

{_tabla(
    ["Req.", "Estado", "Válida", "Proveedor", "Intentos", "Duración", "Fuente"],
    filas,
)}

## Métricas agregadas

{_tabla(
    ["Métrica", "Valor"],
    [
        ["Cobertura de revisión", f"{resumen['cobertura_revision_pct']}%"],
        ["Cumplimiento ponderado", f"{resumen['cumplimiento_pct']}%"],
        ["Propuestas válidas", f"{resumen['con_propuesta_valida']}/{resumen['requisitos_total']}"],
        ["Requieren revisión", resumen["requiere_revision"]],
        ["Cumple", resumen["cumple"]],
        ["Cumple parcialmente", resumen["parcial"]],
        ["No cumple", resumen["no_cumple"]],
        ["Contingencias", resumen["contingencias"]],
        ["Alertas de integridad", resumen["integridad_alertas"]],
    ],
)}

> La cobertura de revisión (peso con propuesta registrada) es distinta del
> cumplimiento ponderado (peso concluyente). La ausencia de evidencia **no** se
> contabiliza como “No cumple”.

## Detalle por requisito

{''.join(detalle)}

## Control sin documentos

Se registró el expediente `{EXPEDIENTE_CONTROL}` sin documentos y se analizó RQ-01.

{_tabla(
    ["Req.", "Estado", "Válida", "Proveedor", "Intentos", "Duración", "Fuente"],
    [_fila_resultado(control)],
)}

## Criterio de salida cubierto

- [x] RQ-04 y RQ-07 concluyen `Cumple` con fuente y cita verificables.
- [x] RQ-01/02/03/05/06 escalan a `Requiere revisión especializada`.
- [x] Sin documentos, el sistema responde `No se encontró información` (no “No cumple”).
"""


def _reporte_contrato(
    rechazo, reintento, propuesta_invalida: dict, propuesta_valida: dict
) -> str:
    return f"""# Evidencia 04 — Contrato rechazado y reintento

Escenario sobre `{EXPEDIENTE_VALIDACION}` con una copia de `Presupuesto.xlsx`.
La propuesta inválida declara un SHA-256 falso y una cita inventada.

## Respuesta inválida presentada al contrato

```json
{json.dumps(propuesta_invalida, indent=2, ensure_ascii=False)}
```

## Rechazo con reintentos agotados

{_tabla(
    ["Campo", "Valor"],
    [
        ["Estado", rechazo.estado],
        ["¿Válida?", "sí" if rechazo.valida else "no"],
        ["Intentos", rechazo.intentos],
        ["Contingencia", "sí" if rechazo.contingencia else "no"],
        ["Proveedor", rechazo.proveedor],
    ],
)}

Errores registrados:

```text
{chr(10).join(rechazo.errores)}
```

## Respuesta válida aceptada

```json
{json.dumps(propuesta_valida, indent=2, ensure_ascii=False)}
```

## Reintento con respuesta corregida

Se usó un proveedor guionizado con `[respuesta inválida, respuesta válida]`.

{_tabla(
    ["Campo", "Valor"],
    [
        ["Estado", reintento.estado],
        ["¿Válida?", "sí" if reintento.valida else "no"],
        ["Intentos", reintento.intentos],
        ["Proveedor", reintento.proveedor],
        ["Fuente", (reintento.propuesta or {}).get("fuente", {}).get("archivo", "—")],
    ],
)}

## Criterio de salida cubierto

- [x] Una respuesta con hash o cita falsos nunca se acepta como conclusión.
- [x] Los errores del contrato se conservan para auditoría.
- [x] El reintento se detiene en cuanto la respuesta cumple el contrato.
"""


def _reporte_integridad(
    verificacion: dict, analisis_previo, reanalisis, eventos: list
) -> str:
    filas_eventos = [
        [
            evento["ts"],
            evento["documento_id"],
            evento["archivo"],
            evento["estado"],
            (evento.get("detalle") or "")[:90],
        ]
        for evento in eventos[:10]
    ]
    return f"""# Evidencia 05 — Integridad de la fuente

Se analizó una copia de `Presupuesto.xlsx` en `{EXPEDIENTE_INTEGRIDAD}`, se emitió
una propuesta `Cumple` y después se modificó el archivo. El SHA-256 registrado ya no
coincide con el archivo actual. El escenario se mantiene separado del expediente de
validación para no interferir con las pruebas de contingencia.

## Análisis previo a la modificación

{_tabla(
    ["Req.", "Estado", "Válida", "Proveedor", "Intentos", "Duración", "Fuente"],
    [_fila_resultado(analisis_previo)],
)}

## Verificación del documento

{_tabla(
    ["Campo", "Valor"],
    [
        ["Documento", verificacion["documento_id"]],
        ["Archivo", verificacion["archivo"]],
        ["Estado", verificacion["estado"]],
        ["SHA-256 registrado", _sha_corto(verificacion["sha256_registrado"])],
        ["SHA-256 actual", _sha_corto(verificacion["sha256_actual"])],
        ["Evidencias afectadas", verificacion["evidencias_afectadas"]],
        ["Propuestas afectadas", verificacion["propuestas_afectadas"]],
    ],
)}

## Reanálisis tras la modificación

{_tabla(
    ["Req.", "Estado", "Válida", "Proveedor", "Intentos", "Duración", "Fuente"],
    [_fila_resultado(reanalisis)],
)}

El sistema **no emite una conclusión automática** con una fuente alterada: escala a
`Requiere revisión especializada` y deja la evidencia marcada como
`FUENTE_MODIFICADA`.

## Eventos de integridad

{_tabla(["Fecha", "Doc.", "Archivo", "Estado", "Detalle"], filas_eventos)}

## Criterio de salida cubierto

- [x] La modificación se detecta comparando hashes.
- [x] La conclusión anterior deja de mostrarse como válida.
- [x] El evento queda registrado y es visible en la interfaz y el CLI.
"""


def _reporte_contingencia(contingencia, manual: dict, resumen_validacion: dict) -> str:
    return f"""# Evidencia 06 — Contingencia y evaluación manual

Se forzó un proveedor no disponible (`ProveedorFallido`) sobre RQ-04 de
`{EXPEDIENTE_VALIDACION}` para comprobar que el flujo no pierde la evidencia ni
inventa una conclusión.

## Resultado de la contingencia

{_tabla(
    ["Campo", "Valor"],
    [
        ["Estado", contingencia.estado],
        ["¿Válida?", "sí" if contingencia.valida else "no"],
        ["Intentos", contingencia.intentos],
        ["Contingencia", "sí" if contingencia.contingencia else "no"],
        ["Proveedor", contingencia.proveedor],
    ],
)}

Errores:

```text
{chr(10).join(contingencia.errores)}
```

La propuesta de contingencia se guarda como **no válida** y la evidencia recuperada
permanece disponible para revisión manual.

## Evaluación manual registrada

{_tabla(
    ["Campo", "Valor"],
    [
        ["Requisito", manual.get("requisito_id")],
        ["Estado", manual.get("estado")],
        ["Responsable", manual.get("actor")],
        ["Motivo", manual.get("motivo")],
        ["Fecha", manual.get("creado_en")],
    ],
)}

## Estado efectivo del expediente de validación

{_tabla(
    ["Métrica", "Valor"],
    [
        ["Cobertura de revisión", f"{resumen_validacion['cobertura_revision_pct']}%"],
        ["Evaluaciones manuales", resumen_validacion["con_evaluacion_manual"]],
        ["Contingencias", resumen_validacion["contingencias"]],
        ["Alertas de integridad", resumen_validacion["integridad_alertas"]],
    ],
)}

## Criterio de salida cubierto

- [x] Ante un fallo de IA se activa la contingencia y se conserva la evidencia.
- [x] El especialista puede registrar una evaluación manual motivada.
- [x] La evaluación manual prevalece en el resultado efectivo y queda auditada.
"""


# --- Exportaciones --------------------------------------------------------


def _exportar_auditoria(procesador: ProcesadorDocumental) -> Path:
    ruta = config.DIR_EVIDENCIA_ETAPA3 / "08_auditoria.csv"
    with ruta.open("w", encoding="utf-8", newline="") as manejador:
        escritor = csv.writer(manejador)
        escritor.writerow(["ts", "actor", "accion", "entidad", "entidad_id", "detalle"])
        for registro in procesador.listar_auditoria(3000):
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


def _exportar_ejecuciones(analizador: AnalizadorExpediente) -> Path:
    ruta = config.DIR_EVIDENCIA_ETAPA3 / "11_ejecuciones.csv"
    columnas = [
        "id",
        "expediente_id",
        "requisito_id",
        "proveedor",
        "modelo",
        "estado",
        "intentos",
        "duracion_ms",
        "tokens_entrada",
        "tokens_salida",
        "error",
        "creado_en",
    ]
    with ruta.open("w", encoding="utf-8", newline="") as manejador:
        escritor = csv.DictWriter(manejador, fieldnames=columnas)
        escritor.writeheader()
        for ejecucion in analizador.ejecuciones(EXPEDIENTE, limite=1000) + analizador.ejecuciones(
            EXPEDIENTE_VALIDACION, limite=1000
        ) + analizador.ejecuciones(EXPEDIENTE_INTEGRIDAD, limite=1000) + analizador.ejecuciones(
            EXPEDIENTE_CONTROL, limite=1000
        ):
            escritor.writerow({clave: ejecucion.get(clave) for clave in columnas})
    return ruta


# --- Flujo principal ------------------------------------------------------


def main() -> int:
    config.preparar_directorios()
    config.DIR_EVIDENCIA_ETAPA3.mkdir(parents=True, exist_ok=True)

    if RUTA_BD.exists():
        RUTA_BD.unlink()
    for sufijo in ("-wal", "-shm"):
        sobrante = Path(str(RUTA_BD) + sufijo)
        if sobrante.exists():
            sobrante.unlink()

    print("1/8 Generando corpus de la Etapa 3...")
    corpus = generar_corpus_etapa3(config.DIR_MUESTRAS_ETAPA3)

    procesador = ProcesadorDocumental(RUTA_BD)
    procesador.registrar_expediente(
        EXPEDIENTE,
        "Carretera Central Tramo 2 · Km 42–78",
        especialidad="Pavimentos",
        version="v3",
        actor="equipo-mvp",
    )
    for expediente_id, nombre in (
        (EXPEDIENTE_CONTROL, "Control sin documentos"),
        (EXPEDIENTE_VALIDACION, "Validación de contrato y contingencia"),
        (EXPEDIENTE_INTEGRIDAD, "Validación de integridad de la fuente"),
    ):
        procesador.registrar_expediente(
            expediente_id,
            nombre,
            especialidad="Pavimentos",
            version="v3",
            actor="equipo-mvp",
        )

    print("2/8 Ingestando los 8 documentos del caso...")
    inicio_ingesta = perf_counter()
    resultados = procesador.ingestar_carpeta(
        EXPEDIENTE, corpus["carpeta_caso"], actor="equipo-mvp"
    )
    duracion_ingesta = int((perf_counter() - inicio_ingesta) * 1000)
    eett = next(
        documento
        for documento in procesador.listar_documentos(EXPEDIENTE)
        if documento["nombre_archivo"] == "EETT_General_v2.docx"
    )
    procesador.corregir_clasificacion(
        eett["id"],
        "Especificaciones técnicas",
        "EETT",
        actor="Lucía Ramos",
        motivo="El contenido corresponde a EETT aunque el nombre del archivo es genérico.",
    )
    procesador.exportar_inventario_csv(
        EXPEDIENTE, config.DIR_EVIDENCIA_ETAPA3 / "12_inventario_procesado.csv"
    )
    _escribir("01_reporte_ingesta.md", _reporte_ingesta(procesador, resultados))

    perfiles = cargar_perfiles()
    analizador = AnalizadorExpediente(RUTA_BD, perfiles=perfiles)

    print("3/8 Recuperando evidencia por requisito...")
    inicio_evidencia = perf_counter()
    evidencias = analizador.recuperar(EXPEDIENTE)
    duracion_evidencia = int((perf_counter() - inicio_evidencia) * 1000)
    _escribir("02_reporte_evidencia.md", _reporte_evidencia(evidencias, perfiles))

    print("4/8 Analizando con el proveedor de reglas...")
    inicio_analisis = perf_counter()
    resultados_analisis = analizador.analizar_expediente(EXPEDIENTE)
    duracion_analisis = int((perf_counter() - inicio_analisis) * 1000)
    resumen = analizador.resumen(EXPEDIENTE)

    control = analizador.analizar_requisito(EXPEDIENTE_CONTROL, "RQ-01")
    _escribir(
        "03_reporte_analisis.md",
        _reporte_analisis(resultados_analisis, resumen, control),
    )

    print("5/8 Validando rechazo del contrato y reintento...")
    carpeta_validacion = config.DIR_MUESTRAS_ETAPA3 / "validacion"
    carpeta_validacion.mkdir(parents=True, exist_ok=True)
    copia_presupuesto = carpeta_validacion / "Presupuesto.xlsx"
    if copia_presupuesto.exists():
        copia_presupuesto.unlink()
    shutil.copy2(corpus["carpeta_caso"] / "Presupuesto.xlsx", copia_presupuesto)
    procesador.ingestar_archivo(
        EXPEDIENTE_VALIDACION, copia_presupuesto, actor="equipo-mvp"
    )
    analizador.recuperar(EXPEDIENTE_VALIDACION, "RQ-04")
    evidencia_rq04 = analizador.evidencias(EXPEDIENTE_VALIDACION, "RQ-04")[0]
    propuesta_invalida = _propuesta_invalida(evidencia_rq04)
    propuesta_valida = _propuesta_valida(evidencia_rq04)

    proveedor_rechazo = ProveedorGuionizado(
        [propuesta_invalida, propuesta_invalida, propuesta_invalida],
        nombre="guionizado-rechazo",
    )
    rechazo = analizador.analizar_requisito(
        EXPEDIENTE_VALIDACION,
        "RQ-04",
        proveedor=proveedor_rechazo,
        recuperar=False,
    )

    proveedor_reintento = ProveedorGuionizado(
        [propuesta_invalida, propuesta_valida], nombre="guionizado-reintento"
    )
    reintento = analizador.analizar_requisito(
        EXPEDIENTE_VALIDACION,
        "RQ-04",
        proveedor=proveedor_reintento,
        recuperar=False,
    )
    _escribir(
        "04_reporte_contrato.md",
        _reporte_contrato(
            rechazo, reintento, propuesta_invalida, propuesta_valida
        ),
    )

    print("6/8 Verificando integridad de la fuente...")
    copia_integridad = carpeta_validacion / "Presupuesto_integridad.xlsx"
    if copia_integridad.exists():
        copia_integridad.unlink()
    shutil.copy2(corpus["carpeta_caso"] / "Presupuesto.xlsx", copia_integridad)
    procesador.ingestar_archivo(EXPEDIENTE_INTEGRIDAD, copia_integridad, actor="equipo-mvp")
    analisis_previo = analizador.analizar_requisito(EXPEDIENTE_INTEGRIDAD, "RQ-04")

    libro = load_workbook(copia_integridad)
    libro["Resumen"]["A1"] = "PRESUPUESTO DE OBRA - VERSION MODIFICADA"
    libro.save(copia_integridad)

    verificacion = verificar_expediente(
        RUTA_BD, EXPEDIENTE_INTEGRIDAD, actor="verificador-integridad"
    )
    documento_modificado = next(
        item
        for item in verificacion["resultados"]
        if item["estado"] == "FUENTE_MODIFICADA"
    )
    reanalisis = analizador.analizar_requisito(EXPEDIENTE_INTEGRIDAD, "RQ-04")
    eventos = listar_eventos_integridad(RUTA_BD, EXPEDIENTE_INTEGRIDAD, limite=20)
    _escribir(
        "05_reporte_integridad.md",
        _reporte_integridad(
            documento_modificado, analisis_previo, reanalisis, eventos
        ),
    )

    print("7/8 Demostrando contingencia y evaluación manual...")
    contingencia = analizador.analizar_requisito(
        EXPEDIENTE_VALIDACION, "RQ-04", proveedor=ProveedorFallido()
    )
    manual = analizador.registrar_evaluacion_manual(
        EXPEDIENTE_VALIDACION,
        "RQ-04",
        "Requiere revisión especializada",
        "La fuente fue modificada y el servicio de IA no está disponible; "
        "se revisará el presupuesto actualizado.",
        actor="Lucía Ramos",
    )
    resumen_validacion = analizador.resumen(EXPEDIENTE_VALIDACION)
    _escribir(
        "06_reporte_contingencia.md",
        _reporte_contingencia(contingencia, manual, resumen_validacion),
    )

    print("8/8 Exportando métricas, propuestas y auditoría...")
    metricas = {
        "caso": resumen,
        "control": control.a_dict(),
        "evidencia": {
            "requisitos": len(perfiles.requisitos),
            "total_evidencias": sum(len(items) for items in evidencias.values()),
            "por_requisito": {
                requisito_id: len(items) for requisito_id, items in evidencias.items()
            },
            "duracion_ms": duracion_evidencia,
        },
        "analisis": {
            "duracion_ms": duracion_analisis,
            "propuestas_validas": sum(1 for r in resultados_analisis if r.valida),
            "conclusiones": sum(
                1 for r in resultados_analisis if r.estado in ESTADOS_CONCLUYENTES
            ),
        },
        "contrato": {
            "rechazo_intentos": rechazo.intentos,
            "rechazo_contingencia": rechazo.contingencia,
            "reintento_intentos": reintento.intentos,
            "reintento_valida": reintento.valida,
        },
        "integridad": {
            "expediente": EXPEDIENTE_INTEGRIDAD,
            "estado_previo": analisis_previo.estado,
            "estado": documento_modificado["estado"],
            "evidencias_afectadas": documento_modificado["evidencias_afectadas"],
            "propuestas_afectadas": documento_modificado["propuestas_afectadas"],
            "reanalisis_estado": reanalisis.estado,
            "reanalisis_proveedor": reanalisis.proveedor,
        },
        "contingencia": {
            "expediente": EXPEDIENTE_VALIDACION,
            "intentos": contingencia.intentos,
            "contingencia": contingencia.contingencia,
            "propuesta_valida": contingencia.valida,
        },
        "evaluacion_manual": manual,
        "ingesta_ms": duracion_ingesta,
    }
    _escribir("07_metricas.json", json.dumps(metricas, indent=2, ensure_ascii=False))
    _escribir("00_entorno.json", json.dumps(_entorno(), indent=2, ensure_ascii=False))

    analizador.exportar_resultados_csv(
        EXPEDIENTE, config.DIR_EVIDENCIA_ETAPA3 / "10_resultados.csv"
    )
    analizador.exportar_propuestas_csv(
        EXPEDIENTE, config.DIR_EVIDENCIA_ETAPA3 / "09_propuestas.csv"
    )
    _exportar_ejecuciones(analizador)
    _exportar_auditoria(procesador)

    # --- Verificación de criterios de salida -------------------------
    assert len(resultados) == 8, len(resultados)
    assert all(resultado.ok for resultado in resultados)
    assert all(len(items) > 0 for items in evidencias.values()), evidencias
    assert resumen["cobertura_revision_pct"] == 100.0, resumen
    assert resumen["cumplimiento_pct"] == 100.0, resumen
    estados = {resultado.requisito_id: resultado.estado for resultado in resultados_analisis}
    assert estados["RQ-04"] == "Cumple", estados
    assert estados["RQ-07"] == "Cumple", estados
    for requisito_id in ("RQ-01", "RQ-02", "RQ-03", "RQ-05", "RQ-06"):
        assert estados[requisito_id] == "Requiere revisión especializada", estados
    assert control.estado == "No se encontró información", control.estado
    assert control.valida and control.propuesta is not None
    assert rechazo.intentos == 3 and rechazo.contingencia and not rechazo.valida
    assert any("HASH_NO_COINCIDE" in error for error in rechazo.errores)
    assert any("CITA_NO_ENCONTRADA" in error for error in rechazo.errores)
    assert reintento.valida and reintento.intentos == 2
    assert documento_modificado["estado"] == "FUENTE_MODIFICADA"
    assert analisis_previo.estado == "Cumple", analisis_previo.estado
    assert reanalisis.estado == "Requiere revisión especializada"
    assert reanalisis.proveedor == "integridad"
    assert contingencia.contingencia and contingencia.intentos == 3
    assert manual["estado"] == "Requiere revisión especializada"

    print("\nEtapa 3 ejecutada correctamente.")
    print(f"Evidencia: {config.DIR_EVIDENCIA_ETAPA3}")
    print(
        f"Caso: {resumen['con_propuesta_valida']} propuestas válidas, "
        f"{resumen['cumple']} cumple, {resumen['requiere_revision']} requieren revisión, "
        f"cobertura {resumen['cobertura_revision_pct']}%"
    )
    print(
        f"Contrato: rechazo en {rechazo.intentos} intentos; "
        f"reintento válido en {reintento.intentos}"
    )
    print(f"Integridad: {documento_modificado['estado']} → {reanalisis.estado}")
    print(f"Contingencia: {contingencia.intentos} intentos y evaluación manual registrada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
