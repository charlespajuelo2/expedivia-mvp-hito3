# Evidencia 05 — Integridad de la fuente

Se analizó una copia de `Presupuesto.xlsx` en `EXP-2024-089-INTEGRIDAD`, se emitió
una propuesta `Cumple` y después se modificó el archivo. El SHA-256 registrado ya no
coincide con el archivo actual. El escenario se mantiene separado del expediente de
validación para no interferir con las pruebas de contingencia.

## Análisis previo a la modificación

| Req. | Estado | Válida | Proveedor | Intentos | Duración | Fuente |
|---|---|---|---|---|---|---|
| RQ-04 | Cumple | sí | reglas | 1 | 13 ms | Presupuesto_integridad.xlsx · Hoja:Resumen!A3:E3 |

## Verificación del documento

| Campo | Valor |
|---|---|
| Documento | 10 |
| Archivo | Presupuesto_integridad.xlsx |
| Estado | FUENTE_MODIFICADA |
| SHA-256 registrado | 97caacf2815c |
| SHA-256 actual | 5abfcb8f002b |
| Evidencias afectadas | 2 |
| Propuestas afectadas | 1 |

## Reanálisis tras la modificación

| Req. | Estado | Válida | Proveedor | Intentos | Duración | Fuente |
|---|---|---|---|---|---|---|
| RQ-04 | Requiere revisión especializada | sí | integridad | 0 | 0 ms | Presupuesto_integridad.xlsx · Hoja:Resumen!A3:E3 |

El sistema **no emite una conclusión automática** con una fuente alterada: escala a
`Requiere revisión especializada` y deja la evidencia marcada como
`FUENTE_MODIFICADA`.

## Eventos de integridad

| Fecha | Doc. | Archivo | Estado | Detalle |
|---|---|---|---|---|
| 2026-11-11T22:30:28 | 10 | Presupuesto_integridad.xlsx | FUENTE_MODIFICADA | El archivo cambió después de la revisión. |
| 2026-11-11T22:30:28 | 10 | Presupuesto_integridad.xlsx | FUENTE_MODIFICADA | El archivo cambió después de la revisión. |
| 2026-11-11T22:30:28 | 10 | Presupuesto_integridad.xlsx | VIGENTE | El hash actual coincide con el registrado. |

## Criterio de salida cubierto

- [x] La modificación se detecta comparando hashes.
- [x] La conclusión anterior deja de mostrarse como válida.
- [x] El evento queda registrado y es visible en la interfaz y el CLI.
