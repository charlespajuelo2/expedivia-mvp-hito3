# Evidencia 03 — Avance ponderado después de decidir

## Antes / después

| Métrica | Antes | Después |
|---|---|---|
| Cobertura de revisión | 100.0% | 100.0% |
| Avance ponderado | 0.0% | 39.0% |
| Cumplimiento ponderado | 100.0% | 88.6% |
| Decisiones registradas | 0 | 4 |
| Cumple | 2 | 2 |
| Cumple parcialmente | 0 | 1 |
| No se encontró información | 0 | 1 |
| Requiere revisión | 5 | 3 |

## Verificación manual de la fórmula

Fórmula documentada: `Σ(peso × factor_avance) / peso_total × 100`, con
`ROUND_HALF_UP` a 1 decimal. `descartar` aporta factor 0.

| Concepto | Valor |
|---|---|
| Peso total | 100% |
| Peso decidido | 58% |
| Numerador | 39.0 |
| Avance esperado | 39.0% |
| Avance del sistema | 39.0% |
| ¿Coincide? | sí |

## Métricas finales

| Métrica | Valor |
|---|---|
| requisitos_total | 7 |
| peso_total_pct | 100 |
| cobertura_revision_pct | 100.0 |
| peso_concluyente_pct | 44 |
| cumplimiento_pct | 88.6 |
| peso_decidido_pct | 58.0 |
| avance_pct | 39.0 |
| decisiones_registradas | 4 |
| aceptadas | 2 |
| modificadas | 1 |
| descartadas | 1 |
| cumple | 2 |
| parcial | 1 |
| no_cumple | 0 |
| sin_informacion | 1 |
| requiere_revision | 3 |
| integridad_alertas | 0 |

## Estado final por requisito

| Req. | Peso | Estado propuesto | Estado efectivo | Decisión | Responsable | Motivo (recortado) |
|---|---|---|---|---|---|---|
| RQ-01 | 14% | Requiere revisión especializada | Requiere revisión especializada | sin decidir | — | La evidencia localizada es de tipo 'TDR / Bases', que no acredita por  |
| RQ-02 | 17% | Requiere revisión especializada | Requiere revisión especializada | sin decidir | — | La evidencia localizada es de tipo 'TDR / Bases', que no acredita por  |
| RQ-03 | 11% | Requiere revisión especializada | Requiere revisión especializada | sin decidir | — | La evidencia localizada es de tipo 'TDR / Bases', que no acredita por  |
| RQ-04 | 21% | Cumple | Cumple | aceptar | Lucía Ramos | Tras revisar el detalle, la partida observada sí cuenta con metrado; s |
| RQ-05 | 14% | Requiere revisión especializada | No se encontró información | descartar | Lucía Ramos | Los planos localizados no permiten verificar la coherencia con la hoja |
| RQ-06 | 10% | Requiere revisión especializada | Cumple parcialmente | modificar | Lucía Ramos | La curva S es coherente, pero el cronograma no cubre dos partidas del  |
| RQ-07 | 13% | Cumple | Cumple | aceptar | Lucía Ramos | El plan de manejo ambiental está vigente y corresponde al componente a |

## Criterio de salida cubierto

- [x] El contador de validados cambió realmente: 0 → 4 decisiones.
- [x] El avance se recalcula y coincide con la fórmula documentada.
- [x] Los cinco estados siguen disponibles; la ausencia no se vuelve incumplimiento.
