# Evidencia 01 — Estado antes de decidir

**Comando reproducible:** `python -m mvp.scripts.ejecutar_etapa4`
**Base de datos:** `mvp/etapa4/evidencia/mvp_etapa4.db`

El análisis automático terminó y todavía **no existe ninguna decisión humana**.
Por eso el avance validado es 0%: el sistema no se autoaprueba.

## Métricas iniciales

| Métrica | Valor |
|---|---|
| requisitos_total | 7 |
| peso_total_pct | 100 |
| cobertura_revision_pct | 100.0 |
| peso_concluyente_pct | 34 |
| cumplimiento_pct | 100.0 |
| peso_decidido_pct | 0.0 |
| avance_pct | 0.0 |
| decisiones_registradas | 0 |
| aceptadas | 0 |
| modificadas | 0 |
| descartadas | 0 |
| cumple | 2 |
| parcial | 0 |
| no_cumple | 0 |
| sin_informacion | 0 |
| requiere_revision | 5 |
| integridad_alertas | 0 |

> La cobertura de revisión (100%) indica que los 7 requisitos tienen propuesta.
> El avance ponderado (0%) indica que ninguno ha sido validado por una persona.
> El cumplimiento ponderado (100%) se calcula solo sobre el 34% concluyente.

## Estado por requisito

| Req. | Peso | Estado propuesto | Estado efectivo | Decisión | Responsable | Motivo (recortado) |
|---|---|---|---|---|---|---|
| RQ-01 | 14% | Requiere revisión especializada | Requiere revisión especializada | sin decidir | — | La evidencia localizada es de tipo 'TDR / Bases', que no acredita por  |
| RQ-02 | 17% | Requiere revisión especializada | Requiere revisión especializada | sin decidir | — | La evidencia localizada es de tipo 'TDR / Bases', que no acredita por  |
| RQ-03 | 11% | Requiere revisión especializada | Requiere revisión especializada | sin decidir | — | La evidencia localizada es de tipo 'TDR / Bases', que no acredita por  |
| RQ-04 | 21% | Cumple | Cumple | sin decidir | — | La evidencia de tipo 'Presupuesto por partidas' contiene los elementos |
| RQ-05 | 14% | Requiere revisión especializada | Requiere revisión especializada | sin decidir | — | La evidencia localizada es de tipo 'Planos', que no acredita por sí mi |
| RQ-06 | 10% | Requiere revisión especializada | Requiere revisión especializada | sin decidir | — | El tipo documental es el esperado, pero el criterio exige juicio de in |
| RQ-07 | 13% | Cumple | Cumple | sin decidir | — | La evidencia de tipo 'Estudio ambiental' contiene los elementos del cr |

## Criterio de salida cubierto

- [x] El contador de decisiones inicia en 0 y el avance en 0%.
- [x] La propuesta automática no se muestra como decisión validada.
