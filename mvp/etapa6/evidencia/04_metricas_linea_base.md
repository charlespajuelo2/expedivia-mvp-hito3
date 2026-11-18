# Evidencia 04 — Línea base vs. sistema

La línea base es una **estimación declarada** para el mismo expediente
(8 documentos y 7 requisitos), no un cronometraje con un especialista. El tiempo
del sistema sí se mide en esta ejecución.

## Tiempo

| Actividad manual | Minutos estimados |
|---|---|
| Recepción, validación de formato y registro de 8 documentos | 20 |
| Lectura y extracción manual de texto, tablas y ubicaciones | 60 |
| Búsqueda de evidencia para los 7 requisitos | 50 |
| Revisión técnica, contraste de fuentes y decisión | 90 |
| Elaboración manual del informe Excel y Word | 40 |
| **Total manual** | **260** |

| Indicador | Manual | Sistema |
|---|---:|---:|
| Trabajo mecánico (carga, extracción, búsqueda y formato) | 170 min | 1.08 s |
| Reducción del trabajo mecánico | — | 99.99% |
| Revisión técnica y decisión | 90 min | sigue siendo humana |
| Documentos procesados | 8 | 8 |
| Requisitos cubiertos | 7 | 7 |
| Informe Excel/Word | manual | automático desde SQLite |

> La reducción porcentual se refiere **solo a tareas mecánicas**. Es alta porque
> el sistema automatiza lectura, extracción, búsqueda, cálculo y formato, pero la
> cifra **no** es comparable con el juicio técnico: los 90 minutos
> de revisión y decisión siguen en manos del especialista.

## Aciertos

| Indicador | Resultado |
|---|---|
| Clasificación inicial | 7 de 8 documentos correctos sin intervención (87.5%) |
| Clasificación final | 8 de 8 tras la corrección humana (100%) |
| Requisitos cubiertos | 7 de 7 con propuesta registrada (100%) |
| Propuestas válidas | 7 de 7 propuestas válidas (100%) |
| Coincidencia con la decisión final | 2 de 4 decisiones aceptadas sin cambio (50%); 1 modificada y 1 descartada |

| Métrica del caso | Valor |
|---|---:|
| Propuestas válidas | 7/7 |
| Decisiones vigentes | 4 |
| Aceptadas / modificadas / descartadas | 2 / 1 / 1 |
| Cumplimiento ponderado | 88.6% |
| No cumple | 0 |
| Casos de prueba | 16/16 PASA |

## Supuestos

- Un especialista conoce el expediente y el checklist.
- No se incluye espera por terceros ni reuniones.
- El tiempo del sistema se mide de extremo a extremo en el equipo de demostración.
- La revisión humana sigue siendo necesaria; el sistema reduce el trabajo mecánico, no el juicio técnico.

## Criterio de salida cubierto

- [x] Se declara la línea base y sus supuestos.
- [x] Se mide el sistema de extremo a extremo.
- [x] Se comparan tiempo, requisitos y aciertos.
- [x] No se presenta la estimación como medición real.
