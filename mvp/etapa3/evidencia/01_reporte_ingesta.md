# Evidencia 01 — Ingesta del caso EXP-2024-089

**Comando reproducible:** `python -m mvp.scripts.ejecutar_etapa3`
**Base de datos:** `mvp/etapa3/evidencia/mvp_etapa3.db`
**Corpus:** `mvp/etapa3/muestras/caso` (8 documentos; no altera el corpus cerrado de la Etapa 2)

## Resumen

| Métrica | Valor |
|---|---|
| Documentos | 8 |
| Válidos | 8 |
| Rechazados | 0 |
| Fragmentos | 98 |
| Clasificados | 8 |
| Sin clasificar | 0 |
| Tiempo total | 545 ms |

## Inventario procesado

| ID | Archivo | Formato | Estado | Tipo (confianza) | Clasificación | SHA-256 | Frag. | ms |
|---|---|---|---|---|---|---|---|---|
| 1 | Cronograma_Valorizado.xlsx | XLSX | VALIDO | Cronograma valorizado (82) | Clasificado | 0144f4a1d133 | 36 | 32 |
| 2 | EETT_General_v2.docx | DOCX | VALIDO | Especificaciones técnicas (64) | Sin clasificar | 823329c1c3fc | 4 | 25 |
| 3 | Estudio_Suelos_Lab.xlsx | XLSX | VALIDO | Estudio de suelos (96) | Clasificado | 589b66ede550 | 14 | 49 |
| 4 | Memoria_Calculo_Pavimentos.docx | DOCX | VALIDO | Memoria técnica (88) | Clasificado | b6a75c06af2e | 12 | 41 |
| 5 | Planos_PL-01_PL-08.pdf | PDF | VALIDO | Planos (96) | Clasificado | 22f4da2dd171 | 5 | 211 |
| 6 | PMA_Ambiental.pdf | PDF | VALIDO | Estudio ambiental (89) | Clasificado | be2fb060167d | 1 | 98 |
| 7 | Presupuesto.xlsx | XLSX | VALIDO | Presupuesto por partidas (94) | Clasificado | 97caacf2815c | 24 | 36 |
| 8 | TDR_Carretera_Central_v3.pdf | PDF | VALIDO | TDR / Bases (90) | Clasificado | 91a935b79c36 | 2 | 53 |

## Corrección humana que habilita la evidencia

El documento `EETT_General_v2.docx` obtiene confianza automática 64 (< 70) y queda
`Sin clasificar`. Se aplica la corrección del especialista:

| Campo | Valor |
|---|---|
| Tipo documental | Especificaciones técnicas |
| Componente | EETT |
| Estado de clasificación | Clasificado |
| Origen | correccion_humana |
| Confianza | 100 |

Solo los documentos `VALIDO` y `Clasificado` pueden aportar evidencia, de modo que
esta corrección es un requisito previo para el análisis.

## Criterio de salida cubierto

- [x] Los 8 documentos del caso se procesan sin rechazos.
- [x] El documento ambiguo se corrige por un humano y queda auditable.
- [x] El corpus de la Etapa 2 permanece intacto.
