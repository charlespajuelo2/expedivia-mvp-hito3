# Evidencia 04 — Persistencia tras recarga

Se cerró la instancia del analizador y se abrió una **instancia nueva** sobre la
misma base SQLite, simulando recargar la aplicación.

| Métrica | Instancia original | Instancia nueva | ¿Coincide? |
|---|---|---|---|
| cobertura_revision_pct | 100.0 | 100.0 | sí |
| avance_pct | 39.0 | 39.0 | sí |
| cumplimiento_pct | 88.6 | 88.6 | sí |
| decisiones_registradas | 4 | 4 | sí |

## Decisiones leídas desde la instancia nueva

| Req. | Decisión | Estado final | Responsable | Fecha |
|---|---|---|---|---|
| RQ-04 | aceptar | Cumple | Lucía Ramos | 2026-11-11T22:39:10 |
| RQ-05 | descartar | No se encontró información | Lucía Ramos | 2026-11-11T22:39:10 |
| RQ-06 | modificar | Cumple parcialmente | Lucía Ramos | 2026-11-11T22:39:10 |
| RQ-07 | aceptar | Cumple | Lucía Ramos | 2026-11-11T22:39:10 |

## Historial leído desde la instancia nueva

| ID | Req. | Decisión | Final | Vigente |
|---|---|---|---|---|
| 6 | RQ-04 | aceptar | Cumple | sí |
| 5 | RQ-04 | modificar | Cumple parcialmente | no |
| 4 | RQ-05 | descartar | No se encontró información | sí |
| 3 | RQ-06 | modificar | Cumple parcialmente | sí |
| 2 | RQ-07 | aceptar | Cumple | sí |
| 1 | RQ-04 | aceptar | Cumple | no |

## Criterio de salida cubierto

- [x] Al recargar la aplicación, las decisiones persisten.
- [x] El historial muestra propuesta, decisión, motivo, fecha y responsable.
