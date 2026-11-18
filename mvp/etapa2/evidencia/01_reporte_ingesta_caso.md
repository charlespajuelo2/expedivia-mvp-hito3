# Evidencia 01 — Ingesta del caso EXP-2024-089

**Comando reproducible:** `python -m mvp.scripts.ejecutar_etapa2`
**Base de datos:** `mvp/etapa2/evidencia/mvp_etapa2.db`

## Resumen

| Indicador | Valor |
|---|---|
| Documentos procesados | 6 |
| Válidos | 6 |
| Rechazados | 0 |
| Texto completo | 5 |
| Texto parcial (requiere OCR en algunas páginas) | 1 |
| Clasificados automáticamente | 5 |
| Pendientes de corrección humana | 1 |
| Fragmentos almacenados | 61 |
| Tiempo total de la primera carga | 298 ms |

## Detalle por documento

| ID | Archivo | Estado | Texto | Frags | Tipo (confianza) | Clasificación | SHA-256 | ms |
|---|---|---|---|---|---|---|---|---|
| 1 | EETT_General_v2.docx | VALIDO | si | 4 | Especificaciones técnicas (64) | Sin clasificar | 88f3898403e5 | 32 |
| 2 | Estudio_Suelos_Lab.xlsx | VALIDO | si | 14 | Estudio de suelos (96) | Clasificado | 7dfe84d108a5 | 25 |
| 3 | Memoria_Calculo_Pavimentos.docx | VALIDO | si | 12 | Memoria técnica (88) | Clasificado | 7195e48bf866 | 26 |
| 4 | Planos_PL-01_PL-08.pdf | VALIDO | parcial | 5 | Planos (96) | Clasificado | 82594d969d3a | 148 |
| 5 | Presupuesto.xlsx | VALIDO | si | 24 | Presupuesto por partidas (94) | Clasificado | 36985746738b | 22 |
| 6 | TDR_Carretera_Central_v3.pdf | VALIDO | si | 2 | TDR / Bases (90) | Clasificado | 227583f65356 | 45 |

## Ubicaciones verificables (muestra)

Cada fragmento queda asociado a una página, párrafo, tabla o celda. Ejemplos:

| Archivo | Ubicación | Tipo | Texto (recorte) |
|---|---|---|---|
| EETT_General_v2.docx | párr. 1 | parrafo | DOCUMENTO COMPLEMENTARIO DEL EXPEDIENTE |
| EETT_General_v2.docx | párr. 2 · sección: DOCUMENTO COMPLEMENTARIO DEL EXPEDIENTE | parrafo | El presente documento reúne información general del proyecto. Incluye referencia |
| Estudio_Suelos_Lab.xlsx | Hoja:Ensayos!A1:A1 | fila | A1=ESTUDIO DE SUELOS - ENSAYOS DE LABORATORIO |
| Estudio_Suelos_Lab.xlsx | Hoja:Ensayos!A3:F3 | fila | A3=Calicata | B3=Profundidad (m) | C3=Granulometría | D3=Límite líquido | E3=Pro |
| Memoria_Calculo_Pavimentos.docx | párr. 1 | parrafo | MEMORIA DE CÁLCULO DE PAVIMENTOS |
| Memoria_Calculo_Pavimentos.docx | párr. 2 · sección: MEMORIA DE CÁLCULO DE PAVIMENTOS | parrafo | El presente documento sustenta el diseño estructural del pavimento flexible para |
| Planos_PL-01_PL-08.pdf | p. 1 | texto | PLANO PL-01 PLANTA GENERAL DEL TRAZO ESCALA 1:1000 Proyecto: Carretera Central T |
| Planos_PL-01_PL-08.pdf | p. 2 | texto | PLANO PL-02 PERFIL LONGITUDINAL ESCALA H 1:1000 / V 1:100 Proyecto: Carretera Ce |
| Presupuesto.xlsx | Hoja:Resumen!A1:A1 | fila | A1=PRESUPUESTO DE OBRA - CARRETERA CENTRAL TRAMO 2 |
| Presupuesto.xlsx | Hoja:Resumen!A3:E3 | fila | A3=Ítem | B3=Partida | C3=Metrado | D3=Precio unitario | E3=Parcial |
| TDR_Carretera_Central_v3.pdf | p. 1 | texto | TÉRMINOS DE REFERENCIA (TDR) Contratación pública para la ejecución de la obra:  |
| TDR_Carretera_Central_v3.pdf | p. 1 · tabla 1 | tabla | Requisito | Criterio | Peso Experiencia del postor | Facturación > S/ 5 MM en 5  |

## Advertencias registradas

- **Planos_PL-01_PL-08.pdf**: Páginas sin capa de texto: 3, 4, 5. Requieren OCR o reemplazo antes de usarlas como evidencia.

## Criterios de salida cubiertos

- [x] Se cargan los 6 archivos del caso sin errores.
- [x] La extracción devuelve ubicación verificable por fragmento.
- [x] El inventario, el estado y los metadatos quedan persistidos.
