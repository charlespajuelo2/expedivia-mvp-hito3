# Evidencia 04 — Error de archivo, avance conservado y reintento

Se intentó cargar un PDF corrupto en el expediente principal. El lote no se
abortó: el archivo quedó rechazado con una causa explícita y el estado anterior
se conservó.

## Error registrado

- Motivo: `ARCHIVO_DANADO`.
- Mensaje: El PDF está dañado o no es un PDF válido. Detalle: Stream has ended unexpectedly.

## Conservación y reintento

| Indicador | Antes del error | Tras el error | Tras el reintento |
|---|---|---|---|
| Documentos válidos | 8 | 8 | 9 |
| Avance ponderado | 39.0% | 39.0% | 39.0% |
| Decisiones vigentes | 4 | — | 4 |

El reintento reemplazó el archivo corrupto por un DOCX válido y se procesó
correctamente. El avance y las decisiones no cambiaron: el error nunca borra
trabajo previo.

## Criterio de salida cubierto

- [x] El error muestra causa y no bloquea el resto del expediente.
- [x] El avance y las decisiones ya registradas se conservan.
- [x] El reintento funciona y agrega el documento válido.
