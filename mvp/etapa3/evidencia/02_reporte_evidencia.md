# Evidencia 02 — Recuperación de evidencia por requisito

La puntuación es determinista: suma de términos ponderados más un bonus por tipo
documental esperado. Solo se usan documentos `VALIDO` y `Clasificado`.

## Resumen por requisito

| Req. | Requisito | Peso | Evidencias | Mejor puntaje | Mejor fuente | Tipo |
|---|---|---|---|---|---|---|
| RQ-01 | Experiencia del postor | 14% | 2 | 33 | TDR_Carretera_Central_v3.pdf · p. 1 | TDR / Bases |
| RQ-02 | Personal clave - Residente | 17% | 1 | 38 | TDR_Carretera_Central_v3.pdf · p. 1 | TDR / Bases |
| RQ-03 | Equipamiento mínimo | 11% | 2 | 35 | TDR_Carretera_Central_v3.pdf · p. 1 | TDR / Bases |
| RQ-04 | Presupuesto por partidas | 21% | 5 | 17 | Presupuesto.xlsx · Hoja:Resumen!A3:E3 | Presupuesto por partidas |
| RQ-05 | Metrados y sustento | 14% | 2 | 12 | Planos_PL-01_PL-08.pdf · p. 2 | Planos |
| RQ-06 | Cronograma valorizado | 10% | 2 | 30 | Cronograma_Valorizado.xlsx · Hoja:Cronograma!A2:A2 | Cronograma valorizado |
| RQ-07 | Plan de manejo ambiental | 13% | 1 | 48 | PMA_Ambiental.pdf · p. 1 | Estudio ambiental |

## Detalle


### RQ-01 · Experiencia del postor
**Criterio:** Facturación mayor a S/ 5 MM en los últimos 5 años

| Puntaje | Archivo | Ubicación | Tipo | Términos | SHA-256 |
|---|---|---|---|---|---|
| 33 | TDR_Carretera_Central_v3.pdf | p. 1 | TDR / Bases | experiencia del postor, facturacion, constancias de facturacion, contratos, facturas, s/ 5 000 000 | 91a935b79c36 |
| 14 | TDR_Carretera_Central_v3.pdf | p. 1 · tabla 1 | TDR / Bases | experiencia del postor, facturacion | 91a935b79c36 |

### RQ-02 · Personal clave - Residente
**Criterio:** Ing. Civil colegiado con 8 años de experiencia

| Puntaje | Archivo | Ubicación | Tipo | Términos | SHA-256 |
|---|---|---|---|---|---|
| 38 | TDR_Carretera_Central_v3.pdf | p. 1 | TDR / Bases | personal clave, residente de obra, ingeniero civil colegiado, constancia de colegiatura, ocho anos de experiencia, cv, certificados | 91a935b79c36 |

### RQ-03 · Equipamiento mínimo
**Criterio:** Lista de 15 equipos propios o alquilados

| Puntaje | Archivo | Ubicación | Tipo | Términos | SHA-256 |
|---|---|---|---|---|---|
| 35 | TDR_Carretera_Central_v3.pdf | p. 1 | TDR / Bases | equipamiento minimo, quince equipos, equipos propios o alquilados, inventario, contratos de alquiler | 91a935b79c36 |
| 11 | TDR_Carretera_Central_v3.pdf | p. 1 · tabla 1 | TDR / Bases | equipos propios o alquilados | 91a935b79c36 |

### RQ-04 · Presupuesto por partidas
**Criterio:** Partidas, metrados y precios unitarios coherentes; ponderación 21%

| Puntaje | Archivo | Ubicación | Tipo | Términos | SHA-256 |
|---|---|---|---|---|---|
| 17 | Presupuesto.xlsx | Hoja:Resumen!A3:E3 | Presupuesto por partidas | partida, metrado, precio unitario | 97caacf2815c |
| 16 | Presupuesto.xlsx | Hoja:Resumen!A18:F18 | Presupuesto por partidas | presupuesto, total presupuesto | 97caacf2815c |
| 9 | Cronograma_Valorizado.xlsx | Hoja:Cronograma!A2:A2 | Cronograma valorizado | presupuesto, partida | 0144f4a1d133 |
| 9 | TDR_Carretera_Central_v3.pdf | p. 1 | TDR / Bases | presupuesto, partida | 91a935b79c36 |
| 9 | TDR_Carretera_Central_v3.pdf | p. 1 · tabla 1 | TDR / Bases | presupuesto, partida | 91a935b79c36 |

### RQ-05 · Metrados y sustento
**Criterio:** Coherencia entre planos y hoja de metrados

| Puntaje | Archivo | Ubicación | Tipo | Términos | SHA-256 |
|---|---|---|---|---|---|
| 12 | Planos_PL-01_PL-08.pdf | p. 2 | Planos | plano, perfil longitudinal | 22f4da2dd171 |
| 12 | Planos_PL-01_PL-08.pdf | p. 6 | Planos | plano, seccion transversal | 22f4da2dd171 |

### RQ-06 · Cronograma valorizado
**Criterio:** Curva S y ruta crítica coherentes

| Puntaje | Archivo | Ubicación | Tipo | Términos | SHA-256 |
|---|---|---|---|---|---|
| 30 | Cronograma_Valorizado.xlsx | Hoja:Cronograma!A2:A2 | Cronograma valorizado | cronograma valorizado, cronograma, plazo de ejecucion, valorizado | 0144f4a1d133 |
| 25 | Cronograma_Valorizado.xlsx | Hoja:Cronograma!A1:A1 | Cronograma valorizado | cronograma valorizado, cronograma, valorizado | 0144f4a1d133 |

### RQ-07 · Plan de manejo ambiental
**Criterio:** Instrumento ambiental vigente

| Puntaje | Archivo | Ubicación | Tipo | Términos | SHA-256 |
|---|---|---|---|---|---|
| 48 | PMA_Ambiental.pdf | p. 1 | Estudio ambiental | plan de manejo ambiental, instrumento ambiental, certificacion ambiental, medidas de mitigacion, pma, impacto ambiental, vigente | be2fb060167d |


## Criterio de salida cubierto

- [x] Cada requisito recupera al menos una evidencia con archivo, ubicación y hash.
- [x] La evidencia queda persistida para auditoría y reutilización.
- [x] RQ-01/02/03 solo encuentran la exigencia del TDR, no la prueba del cumplimiento.
