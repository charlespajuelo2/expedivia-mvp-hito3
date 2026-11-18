# Evidencia 03 — Análisis con IA y validación del contrato

Proveedor por defecto: `reglas` (determinista, sin red). La conclusión automática
solo se emite cuando el tipo documental es prueba directa, el puntaje alcanza el
umbral y el requisito no exige juicio de ingeniería.

## Resultados del caso principal

| Req. | Estado | Válida | Proveedor | Intentos | Duración | Fuente |
|---|---|---|---|---|---|---|
| RQ-01 | Requiere revisión especializada | sí | reglas | 1 | 13 ms | TDR_Carretera_Central_v3.pdf · p. 1 |
| RQ-02 | Requiere revisión especializada | sí | reglas | 1 | 15 ms | TDR_Carretera_Central_v3.pdf · p. 1 |
| RQ-03 | Requiere revisión especializada | sí | reglas | 1 | 16 ms | TDR_Carretera_Central_v3.pdf · p. 1 |
| RQ-04 | Cumple | sí | reglas | 1 | 8 ms | Presupuesto.xlsx · Hoja:Resumen!A3:E3 |
| RQ-05 | Requiere revisión especializada | sí | reglas | 1 | 8 ms | Planos_PL-01_PL-08.pdf · p. 2 |
| RQ-06 | Requiere revisión especializada | sí | reglas | 1 | 8 ms | Cronograma_Valorizado.xlsx · Hoja:Cronograma!A2:A2 |
| RQ-07 | Cumple | sí | reglas | 1 | 7 ms | PMA_Ambiental.pdf · p. 1 |

## Métricas agregadas

| Métrica | Valor |
|---|---|
| Cobertura de revisión | 100.0% |
| Cumplimiento ponderado | 100.0% |
| Propuestas válidas | 7/7 |
| Requieren revisión | 5 |
| Cumple | 2 |
| Cumple parcialmente | 0 |
| No cumple | 0 |
| Contingencias | 0 |
| Alertas de integridad | 0 |

> La cobertura de revisión (peso con propuesta registrada) es distinta del
> cumplimiento ponderado (peso concluyente). La ausencia de evidencia **no** se
> contabiliza como “No cumple”.

## Detalle por requisito


### RQ-01 · Requiere revisión especializada

| Campo | Valor |
|---|---|
| ¿Propuesta válida? | sí |
| Proveedor | reglas |
| Modelo | determinista-v1 |
| Intentos | 1 |
| Duración | 13 ms |
| Fuente | TDR_Carretera_Central_v3.pdf |
| Ubicación | p. 1 |
| Cita | contratos, facturas o constancias de facturación. |
| Observación | Se localizó evidencia en TDR_Carretera_Central_v3.pdf · p. 1 (puntaje 33). El fragmento menciona el requisito, pero no es una prueba directa del cumplimiento. |
| Motivo | La evidencia localizada es de tipo 'TDR / Bases', que no acredita por sí misma el requisito. Se requiere revisión especializada. |

### RQ-02 · Requiere revisión especializada

| Campo | Valor |
|---|---|
| ¿Propuesta válida? | sí |
| Proveedor | reglas |
| Modelo | determinista-v1 |
| Intentos | 1 |
| Duración | 15 ms |
| Fuente | TDR_Carretera_Central_v3.pdf |
| Ubicación | p. 1 |
| Cita | El residente de obra debe ser ingeniero civil colegiado con ocho años de experiencia. |
| Observación | Se localizó evidencia en TDR_Carretera_Central_v3.pdf · p. 1 (puntaje 38). El fragmento menciona el requisito, pero no es una prueba directa del cumplimiento. |
| Motivo | La evidencia localizada es de tipo 'TDR / Bases', que no acredita por sí misma el requisito. Se requiere revisión especializada. |

### RQ-03 · Requiere revisión especializada

| Campo | Valor |
|---|---|
| ¿Propuesta válida? | sí |
| Proveedor | reglas |
| Modelo | determinista-v1 |
| Intentos | 1 |
| Duración | 16 ms |
| Fuente | TDR_Carretera_Central_v3.pdf |
| Ubicación | p. 1 |
| Cita | El postor debe presentar una lista de quince equipos propios o alquilados, con inventario, facturas |
| Observación | Se localizó evidencia en TDR_Carretera_Central_v3.pdf · p. 1 (puntaje 35). El fragmento menciona el requisito, pero no es una prueba directa del cumplimiento. |
| Motivo | La evidencia localizada es de tipo 'TDR / Bases', que no acredita por sí misma el requisito. Se requiere revisión especializada. |

### RQ-04 · Cumple

| Campo | Valor |
|---|---|
| ¿Propuesta válida? | sí |
| Proveedor | reglas |
| Modelo | determinista-v1 |
| Intentos | 1 |
| Duración | 8 ms |
| Fuente | Presupuesto.xlsx |
| Ubicación | Hoja:Resumen!A3:E3 |
| Cita | A3=Ítem | B3=Partida | C3=Metrado | D3=Precio unitario | E3=Parcial |
| Observación | Se localizó evidencia directa en Presupuesto.xlsx · Hoja:Resumen!A3:E3 (puntaje 17). Términos encontrados: partida, metrado, precio unitario. La conclusión es preliminar y queda sujeta a validación humana. |
| Motivo | La evidencia de tipo 'Presupuesto por partidas' contiene los elementos del criterio y alcanza 17 puntos (umbral 12). |

### RQ-05 · Requiere revisión especializada

| Campo | Valor |
|---|---|
| ¿Propuesta válida? | sí |
| Proveedor | reglas |
| Modelo | determinista-v1 |
| Intentos | 1 |
| Duración | 8 ms |
| Fuente | Planos_PL-01_PL-08.pdf |
| Ubicación | p. 2 |
| Cita | PERFIL LONGITUDINAL |
| Observación | Se localizó evidencia en Planos_PL-01_PL-08.pdf · p. 2 (puntaje 12). El fragmento menciona el requisito, pero no es una prueba directa del cumplimiento. |
| Motivo | La evidencia localizada es de tipo 'Planos', que no acredita por sí misma el requisito. Se requiere revisión especializada. |

### RQ-06 · Requiere revisión especializada

| Campo | Valor |
|---|---|
| ¿Propuesta válida? | sí |
| Proveedor | reglas |
| Modelo | determinista-v1 |
| Intentos | 1 |
| Duración | 8 ms |
| Fuente | Cronograma_Valorizado.xlsx |
| Ubicación | Hoja:Cronograma!A2:A2 |
| Cita | El cronograma valorizado se vincula con el presupuesto por partidas. |
| Observación | Se localizó evidencia directa en Cronograma_Valorizado.xlsx · Hoja:Cronograma!A2:A2 (puntaje 30). La coherencia técnica debe validarla una persona. |
| Motivo | El tipo documental es el esperado, pero el criterio exige juicio de ingeniería (coherencia o trazabilidad) que el MVP no automatiza. |

### RQ-07 · Cumple

| Campo | Valor |
|---|---|
| ¿Propuesta válida? | sí |
| Proveedor | reglas |
| Modelo | determinista-v1 |
| Intentos | 1 |
| Duración | 7 ms |
| Fuente | PMA_Ambiental.pdf |
| Ubicación | p. 1 |
| Cita | El Plan de Manejo Ambiental (PMA) establece las medidas de mitigación, seguimiento y control para las |
| Observación | Se localizó evidencia directa en PMA_Ambiental.pdf · p. 1 (puntaje 48). Términos encontrados: plan de manejo ambiental, instrumento ambiental, certificacion ambiental, medidas de mitigacion, pma, impacto ambiental, vigente. La conclusión es preliminar y queda sujeta a validación humana. |
| Motivo | La evidencia de tipo 'Estudio ambiental' contiene los elementos del criterio y alcanza 48 puntos (umbral 20). |


## Control sin documentos

Se registró el expediente `EXP-2024-089-CONTROL` sin documentos y se analizó RQ-01.

| Req. | Estado | Válida | Proveedor | Intentos | Duración | Fuente |
|---|---|---|---|---|---|---|
| RQ-01 | No se encontró información | sí | reglas | 1 | 20 ms | — · — |

## Criterio de salida cubierto

- [x] RQ-04 y RQ-07 concluyen `Cumple` con fuente y cita verificables.
- [x] RQ-01/02/03/05/06 escalan a `Requiere revisión especializada`.
- [x] Sin documentos, el sistema responde `No se encontró información` (no “No cumple”).
