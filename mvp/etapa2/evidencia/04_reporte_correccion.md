# Evidencia 04 — Corrección humana y persistencia

**Documento:** `EETT_General_v2.docx`
**SHA-256:** `88f3898403e5ecb93cfc463c89380d12fec76918ae951d63fe14d1eb231358bd`

## Antes de la corrección

| Campo | Valor |
|---|---|
| Tipo propuesto | Especificaciones técnicas |
| Componente | EETT |
| Confianza | 64 |
| Estado de clasificación | Sin clasificar |
| Origen | automatico |

## Después de la corrección

| Campo | Valor |
|---|---|
| Tipo final | Especificaciones técnicas |
| Componente | EETT |
| Confianza | 100 |
| Estado de clasificación | Clasificado |
| Origen | correccion_humana |

Motivo registrado en auditoría: *“El contenido corresponde a EETT aunque el nombre del archivo es genérico.”*

## Recarga del mismo archivo (acierto de caché)

| Campo | Valor |
|---|---|
| Caché reutilizada | sí |
| Tipo conservado | Especificaciones técnicas |
| Confianza | 100 |
| Origen | correccion_humana |
| Estado | Clasificado |

La corrección se guarda en `correcciones_clasificacion` indexada por SHA-256, por
lo que **no se pierde** al reutilizar la caché de extracción.

## Criterio de salida cubierto

- [x] La clasificación se puede corregir y queda registrada.
- [x] La corrección sobrevive a una nueva carga con caché.
