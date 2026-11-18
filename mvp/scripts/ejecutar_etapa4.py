"""Ejecuta la Etapa 4 de extremo a extremo y genera evidencia reproducible.

Uso::

    python -m mvp.scripts.ejecutar_etapa4

No modifica los artefactos cerrados de las Etapas 1-3: usa su propio corpus en
``mvp/etapa4/muestras/``, su propia base en ``mvp/etapa4/evidencia/`` y escribe
sus reportes en ``mvp/etapa4/evidencia/``.

Reportes:

- ``00_entorno.json``: versiones y rutas.
- ``01_reporte_antes.md``: métricas antes de decidir.
- ``02_reporte_decisiones.md``: aceptar / modificar / descartar con propuesta original.
- ``03_reporte_despues.md``: métricas después y verificación de la fórmula.
- ``04_reporte_persistencia.md``: lectura desde una instancia nueva.
- ``05_reporte_reejecucion.md``: reanálisis sin duplicar hallazgos.
- ``06_metricas.json``: métricas comparables antes/después.
- ``07_historial_decisiones.csv``, ``08_resultados.csv``,
  ``09_propuestas.csv``, ``10_auditoria.csv``.
"""

from __future__ import annotations

import csv
import json
import platform
import sys
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from mvp.core import config, db
from mvp.core.analysis import AnalizadorExpediente
from mvp.core.evaluation import EvaluadorExpediente, decisiones_vigentes
from mvp.core.pipeline import ProcesadorDocumental
from mvp.scripts.generar_muestras_etapa3 import generar_corpus_etapa3

EXPEDIENTE = config.EXPEDIENTE_DEFECTO
EXPEDIENTE_CONTROL = "EXP-2024-089-SIN-EVIDENCIA"
RUTA_BD = config.DIR_EVIDENCIA_ETAPA4 / "mvp_etapa4.db"
ACTOR = "Lucía Ramos"


# --- Utilidades -----------------------------------------------------------


def _escribir(nombre: str, contenido: str) -> Path:
    ruta = config.DIR_EVIDENCIA_ETAPA4 / nombre
    ruta.write_text(contenido.rstrip() + "\n", encoding="utf-8")
    return ruta


def _tabla(cabeceras: list[str], filas: list[list[Any]]) -> str:
    lineas = [
        "| " + " | ".join(cabeceras) + " |",
        "|" + "|".join("---" for _ in cabeceras) + "|",
    ]
    for fila in filas:
        lineas.append("| " + " | ".join(str(valor) for valor in fila) + " |")
    return "\n".join(lineas)


def _entorno() -> dict[str, Any]:
    import openpyxl
    import pypdf
    import streamlit

    return {
        "fecha_ejecucion": datetime.now().isoformat(timespec="seconds"),
        "python": sys.version,
        "plataforma": platform.platform(),
        "base_datos": str(RUTA_BD),
        "corpus": str(config.DIR_MUESTRAS_ETAPA4 / "caso"),
        "versiones": {
            "pypdf": pypdf.__version__,
            "openpyxl": openpyxl.__version__,
            "streamlit": streamlit.__version__,
        },
        "decisiones_soportadas": ["aceptar", "modificar", "descartar"],
        "estados_soportados": list(config.ESTADOS_REQUISITO),
        "redondeo": "ROUND_HALF_UP a 1 decimal",
    }


def _fila_requisito(detalle: dict[str, Any]) -> list[Any]:
    return [
        detalle["requisito_id"],
        f"{detalle['peso_pct']}%",
        detalle["estado_propuesto"] or "—",
        detalle["estado_efectivo"],
        detalle["decision"] or "sin decidir",
        detalle["decision_actor"] or "—",
        (detalle["motivo"] or "—")[:70],
    ]


def _tabla_requisitos(resumen: dict[str, Any]) -> str:
    return _tabla(
        [
            "Req.",
            "Peso",
            "Estado propuesto",
            "Estado efectivo",
            "Decisión",
            "Responsable",
            "Motivo (recortado)",
        ],
        [_fila_requisito(detalle) for detalle in resumen["requisitos"]],
    )


def _metricas(resumen: dict[str, Any]) -> dict[str, Any]:
    claves = [
        "requisitos_total",
        "peso_total_pct",
        "cobertura_revision_pct",
        "peso_concluyente_pct",
        "cumplimiento_pct",
        "peso_decidido_pct",
        "avance_pct",
        "decisiones_registradas",
        "aceptadas",
        "modificadas",
        "descartadas",
        "cumple",
        "parcial",
        "no_cumple",
        "sin_informacion",
        "requiere_revision",
        "integridad_alertas",
    ]
    return {clave: resumen[clave] for clave in claves}


# --- Reportes -------------------------------------------------------------


def _reporte_antes(resumen: dict[str, Any]) -> str:
    metricas = _metricas(resumen)
    return f"""# Evidencia 01 — Estado antes de decidir

**Comando reproducible:** `python -m mvp.scripts.ejecutar_etapa4`
**Base de datos:** `mvp/etapa4/evidencia/mvp_etapa4.db`

El análisis automático terminó y todavía **no existe ninguna decisión humana**.
Por eso el avance validado es 0%: el sistema no se autoaprueba.

## Métricas iniciales

{_tabla(["Métrica", "Valor"], [[clave, valor] for clave, valor in metricas.items()])}

> La cobertura de revisión (100%) indica que los 7 requisitos tienen propuesta.
> El avance ponderado (0%) indica que ninguno ha sido validado por una persona.
> El cumplimiento ponderado (100%) se calcula solo sobre el 34% concluyente.

## Estado por requisito

{_tabla_requisitos(resumen)}

## Criterio de salida cubierto

- [x] El contador de decisiones inicia en 0 y el avance en 0%.
- [x] La propuesta automática no se muestra como decisión validada.
"""


def _reporte_decisiones(
    decisiones: list[dict[str, Any]],
    historial: list[dict[str, Any]],
    vigentes: dict[str, dict[str, Any]],
) -> str:
    filas = [
        [
            registro["requisito_id"],
            registro["decision"],
            registro["estado_propuesto"],
            registro["estado_final"],
            registro["actor"],
            registro["creado_en"],
            (registro["motivo"] or "")[:80],
        ]
        for registro in decisiones
    ]
    historial_filas = [
        [
            registro["id"],
            registro["requisito_id"],
            registro["decision"],
            registro["estado_propuesto"],
            registro["estado_final"],
            registro["actor"],
            "sí" if registro["es_vigente"] else "no",
            (registro.get("archivo") or "—")[:34],
            (registro.get("cita") or "—")[:50],
        ]
        for registro in historial
    ]
    return f"""# Evidencia 02 — Decisiones humanas y trazabilidad

Se registraron las tres decisiones posibles sobre propuestas reales del caso:

{_tabla(
    ["Req.", "Decisión", "Propuesto", "Final", "Responsable", "Fecha", "Motivo"],
    filas,
)}

## Propuesta original conservada

La tabla `decisiones` guarda `estado_propuesto` y la huella de la propuesta; la
tabla `propuestas_ia` no se modifica. El historial se une con la propuesta para
mostrar archivo, ubicación y cita:

{_tabla(
    ["ID", "Req.", "Decisión", "Propuesto", "Final", "Responsable", "Vigente", "Archivo", "Cita"],
    historial_filas,
)}

## Historial, no sobrescritura

Para demostrar que el historial es acumulativo, RQ-04 se decidió tres veces:
aceptación inicial, modificación temporal y aceptación definitiva. Las tres
filas se conservan y solo la última queda vigente:

{_tabla(
    ["Req.", "Decisiones registradas", "Decisión vigente", "Estado final vigente"],
    [
        [
            requisito_id,
            len([item for item in historial if item["requisito_id"] == requisito_id]),
            registro["decision"],
            registro["estado_final"],
        ]
        for requisito_id, registro in sorted(vigentes.items())
    ],
)}

## Regla de ausencia de evidencia

`descartar` **no** produce `No cumple`: deja el requisito en
`No se encontró información`, que no aporta al cumplimiento ni se cuenta como
incumplimiento.

## Criterio de salida cubierto

- [x] Aceptar conserva el estado propuesto.
- [x] Modificar exige un estado final distinto y motivado.
- [x] Descartar deja el requisito en `No se encontró información`.
- [x] Cada decisión registra motivo, responsable, fecha y versión del expediente.
- [x] La propuesta original y la decisión final se conservan por separado.
"""


def _reporte_despues(
    resumen: dict[str, Any], antes: dict[str, Any], calculo: dict[str, Any]
) -> str:
    metricas = _metricas(resumen)
    comparacion = [
        ["Cobertura de revisión", f"{antes['cobertura_revision_pct']}%", f"{resumen['cobertura_revision_pct']}%"],
        ["Avance ponderado", f"{antes['avance_pct']}%", f"{resumen['avance_pct']}%"],
        ["Cumplimiento ponderado", f"{antes['cumplimiento_pct']}%", f"{resumen['cumplimiento_pct']}%"],
        ["Decisiones registradas", antes["decisiones_registradas"], resumen["decisiones_registradas"]],
        ["Cumple", antes["cumple"], resumen["cumple"]],
        ["Cumple parcialmente", antes["parcial"], resumen["parcial"]],
        ["No se encontró información", antes["sin_informacion"], resumen["sin_informacion"]],
        ["Requiere revisión", antes["requiere_revision"], resumen["requiere_revision"]],
    ]
    return f"""# Evidencia 03 — Avance ponderado después de decidir

## Antes / después

{_tabla(["Métrica", "Antes", "Después"], comparacion)}

## Verificación manual de la fórmula

Fórmula documentada: `Σ(peso × factor_avance) / peso_total × 100`, con
`ROUND_HALF_UP` a 1 decimal. `descartar` aporta factor 0.

{_tabla(
    ["Concepto", "Valor"],
    [
        ["Peso total", f"{calculo['peso_total']}%"],
        ["Peso decidido", f"{calculo['peso_decidido']}%"],
        ["Numerador", calculo["numerador"]],
        ["Avance esperado", f"{calculo['esperado']}%"],
        ["Avance del sistema", f"{resumen['avance_pct']}%"],
        ["¿Coincide?", "sí" if calculo["esperado"] == resumen["avance_pct"] else "no"],
    ],
)}

## Métricas finales

{_tabla(["Métrica", "Valor"], [[clave, valor] for clave, valor in metricas.items()])}

## Estado final por requisito

{_tabla_requisitos(resumen)}

## Criterio de salida cubierto

- [x] El contador de validados cambió realmente: 0 → 4 decisiones.
- [x] El avance se recalcula y coincide con la fórmula documentada.
- [x] Los cinco estados siguen disponibles; la ausencia no se vuelve incumplimiento.
"""


def _reporte_persistencia(
    resumen_original: dict[str, Any],
    resumen_nuevo: dict[str, Any],
    historial_nuevo: list[dict[str, Any]],
    vigentes_nuevo: dict[str, dict[str, Any]],
) -> str:
    claves = ["cobertura_revision_pct", "avance_pct", "cumplimiento_pct", "decisiones_registradas"]
    return f"""# Evidencia 04 — Persistencia tras recarga

Se cerró la instancia del analizador y se abrió una **instancia nueva** sobre la
misma base SQLite, simulando recargar la aplicación.

{_tabla(
    ["Métrica", "Instancia original", "Instancia nueva", "¿Coincide?"],
    [
        [
            clave,
            resumen_original[clave],
            resumen_nuevo[clave],
            "sí" if resumen_original[clave] == resumen_nuevo[clave] else "no",
        ]
        for clave in claves
    ],
)}

## Decisiones leídas desde la instancia nueva

{_tabla(
    ["Req.", "Decisión", "Estado final", "Responsable", "Fecha"],
    [
        [
            requisito_id,
            registro["decision"],
            registro["estado_final"],
            registro["actor"],
            registro["creado_en"],
        ]
        for requisito_id, registro in sorted(vigentes_nuevo.items())
    ],
)}

## Historial leído desde la instancia nueva

{_tabla(
    ["ID", "Req.", "Decisión", "Final", "Vigente"],
    [
        [
            registro["id"],
            registro["requisito_id"],
            registro["decision"],
            registro["estado_final"],
            "sí" if registro["es_vigente"] else "no",
        ]
        for registro in historial_nuevo
    ],
)}

## Criterio de salida cubierto

- [x] Al recargar la aplicación, las decisiones persisten.
- [x] El historial muestra propuesta, decisión, motivo, fecha y responsable.
"""


def _reporte_reejecucion(
    propuestas_antes: int,
    propuestas_despues: int,
    decisiones_antes: dict[str, dict[str, Any]],
    decisiones_despues: dict[str, dict[str, Any]],
    duplicadas: int,
    huellas_unicas: int,
) -> str:
    return f"""# Evidencia 05 — Reejecución sin duplicar hallazgos

Se volvió a ejecutar el análisis completo con el mismo proveedor determinista.

{_tabla(
    ["Métrica", "Antes", "Después"],
    [
        ["Propuestas persistidas", propuestas_antes, propuestas_despues],
        ["Decisiones vigentes", len(decisiones_antes), len(decisiones_despues)],
    ],
)}

- Propuestas nuevas creadas en la reejecución: **{propuestas_despues - propuestas_antes}**.
- Propuestas con la misma huella reutilizadas: **{duplicadas}**.
- Huellas únicas registradas: **{huellas_unicas}**.

## Decisiones conservadas

{_tabla(
    ["Req.", "Decisión antes", "Decisión después", "Estado final"],
    [
        [
            requisito_id,
            decisiones_antes.get(requisito_id, {}).get("decision", "—"),
            registro["decision"],
            registro["estado_final"],
        ]
        for requisito_id, registro in sorted(decisiones_despues.items())
    ],
)}

## Criterio de salida cubierto

- [x] Reejecutar no duplica hallazgos: la huella canónica reutiliza la propuesta.
- [x] Las decisiones humanas y su historial se conservan.
"""


# --- Flujo principal ------------------------------------------------------


def main() -> int:
    config.preparar_directorios()
    config.DIR_EVIDENCIA_ETAPA4.mkdir(parents=True, exist_ok=True)

    if RUTA_BD.exists():
        RUTA_BD.unlink()
    for sufijo in ("-wal", "-shm"):
        sobrante = Path(str(RUTA_BD) + sufijo)
        if sobrante.exists():
            sobrante.unlink()

    print("1/7 Generando corpus propio de la Etapa 4...")
    corpus = generar_corpus_etapa3(config.DIR_MUESTRAS_ETAPA4)

    procesador = ProcesadorDocumental(RUTA_BD)
    procesador.registrar_expediente(
        EXPEDIENTE,
        "Carretera Central Tramo 2 · Km 42–78",
        especialidad="Pavimentos",
        version="v4",
        actor="equipo-mvp",
    )
    procesador.registrar_expediente(
        EXPEDIENTE_CONTROL,
        "Control sin evidencia",
        especialidad="Pavimentos",
        version="v4",
        actor="equipo-mvp",
    )

    print("2/7 Ingestando el corpus y corrigiendo el documento ambiguo...")
    resultados = procesador.ingestar_carpeta(
        EXPEDIENTE, corpus["carpeta_caso"], actor="equipo-mvp"
    )
    eett = next(
        documento
        for documento in procesador.listar_documentos(EXPEDIENTE)
        if documento["nombre_archivo"] == "EETT_General_v2.docx"
    )
    procesador.corregir_clasificacion(
        eett["id"],
        "Especificaciones técnicas",
        "EETT",
        actor=ACTOR,
        motivo="El contenido corresponde a EETT aunque el nombre del archivo es genérico.",
    )
    assert len(resultados) == 8 and all(resultado.ok for resultado in resultados)

    analizador = AnalizadorExpediente(RUTA_BD)
    evaluador = EvaluadorExpediente(RUTA_BD)

    print("3/7 Analizando los 7 requisitos...")
    analizador.recuperar(EXPEDIENTE)
    analisis = analizador.analizar_expediente(EXPEDIENTE)
    resumen_antes = analizador.resumen(EXPEDIENTE)
    _escribir("01_reporte_antes.md", _reporte_antes(resumen_antes))

    assert resumen_antes["avance_pct"] == 0.0
    assert resumen_antes["decisiones_registradas"] == 0
    assert resumen_antes["cobertura_revision_pct"] == 100.0

    print("4/7 Registrando decisiones: aceptar, modificar y descartar...")
    decisiones = []
    # Aceptar dos conclusiones con fuente directa.
    for requisito_id, motivo in (
        (
            "RQ-04",
            "El presupuesto contiene partidas, metrados y precios unitarios "
            "coherentes; la fuente y el hash fueron verificados.",
        ),
        (
            "RQ-07",
            "El plan de manejo ambiental está vigente y corresponde al componente "
            "ambiental del tramo; se acepta la conclusión automática.",
        ),
    ):
        decisiones.append(
            evaluador.decidir(
                EXPEDIENTE, requisito_id, "aceptar", actor=ACTOR, motivo=motivo
            )
        )

    # Modificar una conclusión que exige juicio de ingeniería.
    decisiones.append(
        evaluador.decidir(
            EXPEDIENTE,
            "RQ-06",
            "modificar",
            estado_final="Cumple parcialmente",
            actor=ACTOR,
            motivo=(
                "La curva S es coherente, pero el cronograma no cubre dos partidas "
                "del plazo contractual; se valida parcialmente."
            ),
        )
    )

    # Descartar una propuesta que no acredita el requisito.
    decisiones.append(
        evaluador.decidir(
            EXPEDIENTE,
            "RQ-05",
            "descartar",
            actor=ACTOR,
            motivo=(
                "Los planos localizados no permiten verificar la coherencia con la "
                "hoja de metrados; se descarta la propuesta y no se asume "
                "incumplimiento."
            ),
        )
    )

    # Historial acumulativo: una modificación temporal seguida de la aceptación.
    decisiones.append(
        evaluador.decidir(
            EXPEDIENTE,
            "RQ-04",
            "modificar",
            estado_final="Cumple parcialmente",
            actor=ACTOR,
            motivo="Revisión intermedia: se detectó una partida sin metrado detallado.",
        )
    )
    decisiones.append(
        evaluador.decidir(
            EXPEDIENTE,
            "RQ-04",
            "aceptar",
            actor=ACTOR,
            motivo=(
                "Tras revisar el detalle, la partida observada sí cuenta con metrado; "
                "se restituye y acepta la conclusión."
            ),
        )
    )

    historial_caso = evaluador.historial(EXPEDIENTE)
    vigentes = evaluador.vigentes(EXPEDIENTE)
    resumen_despues = analizador.resumen(EXPEDIENTE)

    # Verificación manual de la fórmula: RQ-04 21 + RQ-07 13 + RQ-06 5 + RQ-05 0.
    numerador = Decimal("21") * Decimal("1.0")
    numerador += Decimal("13") * Decimal("1.0")
    numerador += Decimal("10") * Decimal("0.5")
    peso_decidido = 21 + 13 + 10 + 14
    esperado = float(
        (numerador / Decimal("100") * Decimal("100")).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )
    )
    calculo = {
        "peso_total": 100,
        "peso_decidido": peso_decidido,
        "numerador": float(numerador),
        "esperado": esperado,
    }

    _escribir(
        "02_reporte_decisiones.md",
        _reporte_decisiones(decisiones, historial_caso, vigentes),
    )
    _escribir(
        "03_reporte_despues.md",
        _reporte_despues(resumen_despues, resumen_antes, calculo),
    )

    assert resumen_despues["avance_pct"] == 39.0
    assert resumen_despues["peso_decidido_pct"] == 58.0
    assert resumen_despues["cumplimiento_pct"] == 88.6
    assert resumen_despues["decisiones_registradas"] == 4
    assert resumen_despues["aceptadas"] == 2
    assert resumen_despues["modificadas"] == 1
    assert resumen_despues["descartadas"] == 1
    assert resumen_despues["sin_informacion"] == 1
    assert resumen_despues["parcial"] == 1
    assert resumen_despues["no_cumple"] == 0
    assert resumen_despues["requiere_revision"] == 3
    assert vigentes["RQ-05"]["estado_final"] == "No se encontró información"
    assert vigentes["RQ-06"]["estado_final"] == "Cumple parcialmente"
    assert len([item for item in historial_caso if item["requisito_id"] == "RQ-04"]) == 3
    assert sum(1 for item in historial_caso if item["es_vigente"]) == 4

    print("5/7 Verificando ausencia de evidencia y persistencia...")
    control = analizador.analizar_requisito(EXPEDIENTE_CONTROL, "RQ-01")
    assert control.estado == "No se encontró información"
    control_decision = evaluador.decidir(
        EXPEDIENTE_CONTROL,
        "RQ-01",
        "aceptar",
        actor=ACTOR,
        motivo="No hay documentos en el expediente; se confirma la ausencia de información.",
    )
    assert control_decision["estado_final"] == "No se encontró información"
    resumen_control = analizador.resumen(EXPEDIENTE_CONTROL)
    assert resumen_control["no_cumple"] == 0

    analizador_nuevo = AnalizadorExpediente(RUTA_BD)
    evaluador_nuevo = EvaluadorExpediente(RUTA_BD)
    resumen_nuevo = analizador_nuevo.resumen(EXPEDIENTE)
    historial_nuevo = evaluador_nuevo.historial(EXPEDIENTE)
    vigentes_nuevo = evaluador_nuevo.vigentes(EXPEDIENTE)
    _escribir(
        "04_reporte_persistencia.md",
        _reporte_persistencia(
            resumen_despues, resumen_nuevo, historial_nuevo, vigentes_nuevo
        ),
    )
    assert _metricas(resumen_despues) == _metricas(resumen_nuevo)
    assert historial_nuevo == historial_caso
    assert {clave: valor["id"] for clave, valor in vigentes.items()} == {
        clave: valor["id"] for clave, valor in vigentes_nuevo.items()
    }

    print("6/7 Reejecutando el análisis para probar idempotencia...")
    propuestas_antes = len(analizador.propuestas(EXPEDIENTE, limite=1000))
    decisiones_antes = evaluador.vigentes(EXPEDIENTE)
    analizador.analizar_expediente(EXPEDIENTE)
    propuestas_despues = len(analizador.propuestas(EXPEDIENTE, limite=1000))
    decisiones_despues = evaluador.vigentes(EXPEDIENTE)
    with db.conectar(RUTA_BD) as conexion:
        duplicadas = int(
            conexion.execute(
                "SELECT COUNT(*) FROM ("
                "SELECT expediente_id, requisito_id, huella, valida, COUNT(*) AS n "
                "FROM propuestas_ia WHERE huella IS NOT NULL "
                "GROUP BY expediente_id, requisito_id, huella, valida HAVING n > 1)"
            ).fetchone()[0]
        )
        huellas_unicas = int(
            conexion.execute(
                "SELECT COUNT(DISTINCT huella) FROM propuestas_ia WHERE huella IS NOT NULL"
            ).fetchone()[0]
        )
    assert propuestas_despues == propuestas_antes, (propuestas_antes, propuestas_despues)
    assert duplicadas == 0
    assert decisiones_despues == decisiones_antes
    _escribir(
        "05_reporte_reejecucion.md",
        _reporte_reejecucion(
            propuestas_antes,
            propuestas_despues,
            decisiones_antes,
            decisiones_despues,
            duplicadas,
            huellas_unicas,
        ),
    )

    print("7/7 Exportando métricas, historial y auditoría...")
    metricas = {
        "caso": {
            "antes": _metricas(resumen_antes),
            "despues": _metricas(resumen_despues),
            "calculo_manual": calculo,
            "decisiones": [
                {
                    "id": registro["id"],
                    "requisito_id": registro["requisito_id"],
                    "decision": registro["decision"],
                    "estado_propuesto": registro["estado_propuesto"],
                    "estado_final": registro["estado_final"],
                    "actor": registro["actor"],
                    "motivo": registro["motivo"],
                    "version_kb": registro["version_kb"],
                    "creado_en": registro["creado_en"],
                }
                for registro in decisiones
            ],
            "historial": historial_caso,
        },
        "control_sin_evidencia": {
            "estado": control.estado,
            "decision": control_decision,
            "resumen": resumen_control,
        },
        "persistencia": {
            "metricas_iguales": _metricas(resumen_despues) == _metricas(resumen_nuevo),
            "historial_igual": historial_nuevo == historial_caso,
            "decisiones_vigentes": len(vigentes_nuevo),
        },
        "reejecucion": {
            "propuestas_antes": propuestas_antes,
            "propuestas_despues": propuestas_despues,
            "duplicadas": duplicadas,
            "huellas_unicas": huellas_unicas,
            "decisiones_conservadas": decisiones_despues == decisiones_antes,
        },
    }
    _escribir("06_metricas.json", json.dumps(metricas, indent=2, ensure_ascii=False))
    _escribir("00_entorno.json", json.dumps(_entorno(), indent=2, ensure_ascii=False))

    analizador.exportar_decisiones_csv(
        EXPEDIENTE, config.DIR_EVIDENCIA_ETAPA4 / "07_historial_decisiones.csv"
    )
    analizador.exportar_resultados_csv(
        EXPEDIENTE, config.DIR_EVIDENCIA_ETAPA4 / "08_resultados.csv"
    )
    analizador.exportar_propuestas_csv(
        EXPEDIENTE, config.DIR_EVIDENCIA_ETAPA4 / "09_propuestas.csv"
    )
    ruta_auditoria = config.DIR_EVIDENCIA_ETAPA4 / "10_auditoria.csv"
    with ruta_auditoria.open("w", encoding="utf-8", newline="") as manejador:
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

    print("\nEtapa 4 ejecutada correctamente.")
    print(f"Evidencia: {config.DIR_EVIDENCIA_ETAPA4}")
    print(
        f"Avance: {resumen_antes['avance_pct']}% -> {resumen_despues['avance_pct']}% | "
        f"Decisiones: {resumen_despues['decisiones_registradas']} | "
        f"Cumplimiento: {resumen_despues['cumplimiento_pct']}%"
    )
    print(
        f"Propuestas: {propuestas_antes} -> {propuestas_despues} | "
        f"duplicadas={duplicadas} | decisiones conservadas="
        f"{'si' if decisiones_despues == decisiones_antes else 'no'}"
    )
    print(
        f"Persistencia: metricas iguales="
        f"{'si' if _metricas(resumen_despues) == _metricas(resumen_nuevo) else 'no'} | "
        f"historial igual={'si' if historial_nuevo == historial_caso else 'no'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
