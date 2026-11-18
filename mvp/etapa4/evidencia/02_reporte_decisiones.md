# Evidencia 02 — Decisiones humanas y trazabilidad

Se registraron las tres decisiones posibles sobre propuestas reales del caso:

| Req. | Decisión | Propuesto | Final | Responsable | Fecha | Motivo |
|---|---|---|---|---|---|---|
| RQ-04 | aceptar | Cumple | Cumple | Lucía Ramos | 2026-11-11T22:39:10 | El presupuesto contiene partidas, metrados y precios unitarios coherentes; la fu |
| RQ-07 | aceptar | Cumple | Cumple | Lucía Ramos | 2026-11-11T22:39:10 | El plan de manejo ambiental está vigente y corresponde al componente ambiental d |
| RQ-06 | modificar | Requiere revisión especializada | Cumple parcialmente | Lucía Ramos | 2026-11-11T22:39:10 | La curva S es coherente, pero el cronograma no cubre dos partidas del plazo cont |
| RQ-05 | descartar | Requiere revisión especializada | No se encontró información | Lucía Ramos | 2026-11-11T22:39:10 | Los planos localizados no permiten verificar la coherencia con la hoja de metrad |
| RQ-04 | modificar | Cumple | Cumple parcialmente | Lucía Ramos | 2026-11-11T22:39:10 | Revisión intermedia: se detectó una partida sin metrado detallado. |
| RQ-04 | aceptar | Cumple | Cumple | Lucía Ramos | 2026-11-11T22:39:10 | Tras revisar el detalle, la partida observada sí cuenta con metrado; se restituy |

## Propuesta original conservada

La tabla `decisiones` guarda `estado_propuesto` y la huella de la propuesta; la
tabla `propuestas_ia` no se modifica. El historial se une con la propuesta para
mostrar archivo, ubicación y cita:

| ID | Req. | Decisión | Propuesto | Final | Responsable | Vigente | Archivo | Cita |
|---|---|---|---|---|---|---|---|---|
| 6 | RQ-04 | aceptar | Cumple | Cumple | Lucía Ramos | sí | Presupuesto.xlsx | A3=Ítem | B3=Partida | C3=Metrado | D3=Precio unit |
| 5 | RQ-04 | modificar | Cumple | Cumple parcialmente | Lucía Ramos | no | Presupuesto.xlsx | A3=Ítem | B3=Partida | C3=Metrado | D3=Precio unit |
| 4 | RQ-05 | descartar | Requiere revisión especializada | No se encontró información | Lucía Ramos | sí | Planos_PL-01_PL-08.pdf | PERFIL LONGITUDINAL |
| 3 | RQ-06 | modificar | Requiere revisión especializada | Cumple parcialmente | Lucía Ramos | sí | Cronograma_Valorizado.xlsx | El cronograma valorizado se vincula con el presupu |
| 2 | RQ-07 | aceptar | Cumple | Cumple | Lucía Ramos | sí | PMA_Ambiental.pdf | El Plan de Manejo Ambiental (PMA) establece las me |
| 1 | RQ-04 | aceptar | Cumple | Cumple | Lucía Ramos | no | Presupuesto.xlsx | A3=Ítem | B3=Partida | C3=Metrado | D3=Precio unit |

## Historial, no sobrescritura

Para demostrar que el historial es acumulativo, RQ-04 se decidió tres veces:
aceptación inicial, modificación temporal y aceptación definitiva. Las tres
filas se conservan y solo la última queda vigente:

| Req. | Decisiones registradas | Decisión vigente | Estado final vigente |
|---|---|---|---|
| RQ-04 | 3 | aceptar | Cumple |
| RQ-05 | 1 | descartar | No se encontró información |
| RQ-06 | 1 | modificar | Cumple parcialmente |
| RQ-07 | 1 | aceptar | Cumple |

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
