# Evidencia 02 — Exportación real a Excel y Word

La exportación se genera con `openpyxl` y `python-docx` desde las tablas del
expediente. Después de escribir los archivos, el propio script los vuelve a
abrir para verificar su contenido.

## Archivos generados

| Formato | Archivo | Bytes |
|---|---|---|
| Excel | informe_EXP-2024-089.xlsx | 22349 |
| Word | informe_EXP-2024-089.docx | 39876 |

## Verificación del Excel

- Hojas: **Resumen, Requisitos, Decisiones, Propuestas, Evidencias, Documentos, Auditoría**.
- Filas de datos en «Requisitos»: **7**.
- Filas de datos en «Decisiones»: **6**.
- El resumen contiene el avance 39.0%: **sí**.
- Cabeceras de «Requisitos»: Req., Requisito, Peso %, Criterio, Evidencias, Estado propuesto, Decisión, Estado final, Origen, Responsable, Fecha decisión, Motivo, Fuente, Ubicación, Cita.

## Verificación del Word

- Secciones numeradas: 1. Resumen ejecutivo, 2. Resultados por requisito, 3. Observaciones y fuentes, 4. Historial de decisiones, 5. Alcance y limitaciones.
- Tablas: **3**.
- Contiene el avance 39.0%: **sí**.
- Contiene el alcance y las limitaciones: **sí**.

## Tiempos medidos

| Operación | Milisegundos | ¿Bajo el umbral? |
|---|---|---|
| Resumen del expediente | 24.9 | sí |
| Exportación Excel + Word | 138.0 | sí |

## Criterio de salida cubierto

- [x] Se genera un `.xlsx` real con 7 hojas y datos del expediente.
- [x] Se genera un `.docx` real con resumen, resultados, fuentes e historial.
- [x] Los archivos se abren correctamente y contienen las métricas del caso.
- [x] Los tiempos quedan medidos y por debajo del umbral de 5000 ms.
