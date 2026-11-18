# Evidencia 01 — Caso con decisiones y datos reales

**Comando reproducible:** `python -m mvp.scripts.ejecutar_etapa5`
**Base de datos:** `mvp/etapa5/evidencia/mvp_etapa5.db`
**Expediente:** `EXP-2024-089`

El caso se procesó desde un corpus propio de la Etapa 5 y se decidió con el
mismo criterio de las etapas anteriores. Los datos que alimentan la interfaz y
las exportaciones son los persistidos en SQLite, no valores fijos.

## Métricas del caso

| Métrica | Valor |
|---|---|
| requisitos_total | 7 |
| cobertura_revision_pct | 100.0 |
| peso_decidido_pct | 58.0 |
| avance_pct | 39.0 |
| cumplimiento_pct | 88.6 |
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

## Historial de decisiones

| ID | Req. | Decisión | Propuesto | Final | Responsable | Vigente |
|---|---|---|---|---|---|---|
| 6 | RQ-04 | aceptar | Cumple | Cumple | Lucía Ramos | sí |
| 5 | RQ-04 | modificar | Cumple | Cumple parcialmente | Lucía Ramos | no |
| 4 | RQ-05 | descartar | Requiere revisión especializada | No se encontró información | Lucía Ramos | sí |
| 3 | RQ-06 | modificar | Requiere revisión especializada | Cumple parcialmente | Lucía Ramos | sí |
| 2 | RQ-07 | aceptar | Cumple | Cumple | Lucía Ramos | sí |
| 1 | RQ-04 | aceptar | Cumple | Cumple | Lucía Ramos | no |

## Criterio de salida cubierto

- [x] Las pantallas y la exportación leen de la base, no de datos fijos.
- [x] El avance y el cumplimiento se recalculan con las decisiones vigentes.
