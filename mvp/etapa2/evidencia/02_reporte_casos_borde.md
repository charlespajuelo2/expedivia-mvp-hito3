# Evidencia 02 — Casos borde

**Expediente:** `EXP-2024-089-BORDES`
**Regla aplicada:** un documento rechazado no genera fragmentos ni conclusiones.
No se convierte en “No cumple”.

## Resultados

| Archivo | Resultado | Motivo esperado | Motivo obtenido | ¿Coincide? | Mensaje |
|---|---|---|---|---|---|
| Documento_General.pdf | Válido | — | — | n/a | Documento procesado correctamente. |
| notas.txt | Rechazado | FORMATO_NO_SOPORTADO | FORMATO_NO_SOPORTADO | sí | Formato '.txt' no soportado. Use: .docx, .pdf, .xlsx. |
| PDF_Corrupto.pdf | Rechazado | ARCHIVO_DANADO | ARCHIVO_DANADO | sí | El PDF está dañado o no es un PDF válido. Detalle: Stream has ended unexpectedly |
| PDF_Escaneado.pdf | Rechazado | PDF_ESCANEADO | PDF_ESCANEADO | sí | El PDF no contiene capa de texto (probablemente es un documento escaneado). Se rechaza par |
| PDF_Protegido.pdf | Rechazado | PDF_PROTEGIDO | PDF_PROTEGIDO | sí | El PDF está protegido con contraseña; no se puede extraer su contenido. |

## Resumen

| Indicador | Valor |
|---|---|
| Documentos evaluados | 5 |
| Válidos | 1 |
| Rechazados | 4 |
| Fragmentos generados | 1 |

El archivo `Documento_General.pdf` es un **documento ambiguo**: se acepta porque
tiene texto recuperable, pero queda **Sin clasificar** (tipo “No reconocido”,
confianza 0) hasta que una persona lo corrija. Esto demuestra que “no se pudo
clasificar” no se confunde con “documento inválido”.

## Criterios de salida cubiertos

- [x] Un PDF escaneado se rechaza con mensaje claro y registro.
- [x] Un PDF protegido y un PDF corrupto se rechazan con motivos distintos.
- [x] Un formato no soportado se rechaza de forma trazable.
- [x] Un documento ambiguo queda pendiente de corrección, no rechazado.
