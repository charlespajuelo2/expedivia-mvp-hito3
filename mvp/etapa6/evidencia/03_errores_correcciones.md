# Evidencia 03 — Errores encontrados y correcciones aplicadas

Se registran incidencias reales detectadas durante la integración y las etapas
previas. Ninguna queda abierta como bloqueante.

| ID | Severidad | Incidencia | Causa | Corrección | Verificación |
|---|---|---|---|---|---|
| E-01 | Alto | `EETT_General_v2.docx` se clasificó como documento genérico. | El nombre del archivo no describe su contenido. | Corrección humana a `Especificaciones técnicas / EETT`, vinculada al SHA-256. | CP-03 |
| E-02 | Medio | La verificación del Word solo leía párrafos y no veía el avance en tablas. | El script de aceptación inspeccionaba `document.paragraphs`. | Se amplió la verificación a las celdas de todas las tablas. | CP-11 |
| E-03 | Medio | La pestaña de exportación usaba `total_evidencias`, campo inexistente. | Se asumió una clave que el resumen no expone. | Se sumó `detalle['evidencias']` de los requisitos. | CP-10/CP-11 |
| E-04 | Medio | El especialista no podía registrar el expediente al iniciar la app. | El alta automática exigía `administrar`. | Se habilitó el alta para roles con permiso `cargar`. | CP-13 |
| E-05 | Bajo | La prueba de contingencia quedaba oculta por una propuesta válida previa. | El resumen prioriza propuesta válida sobre contingencia. | La prueba aísla el requisito invalidando la propuesta previa en una copia. | CP-14 |
| E-06 | Bajo | El mensaje de éxito de exportación se pierde al hacer `st.rerun()`. | La descarga se renderiza después del rerun. | Se conserva la confirmación mediante las descargas disponibles. | CP-10/CP-11 |
| E-07 | Medio | Los casos de resiliencia dejaban 10 documentos en el expediente principal. | CP-02 y CP-12 ingestaban el PDF corrupto y el reintento en `EXP-2024-089`. | Se aislaron en un expediente de pruebas; el caso principal vuelve a 8/8 válidos. | CP-02/CP-12 |

## Criterio de salida cubierto

- [x] Cada error tiene causa, corrección y caso de verificación.
- [x] Las correcciones se reflejan en el código y en las pruebas.
- [x] No quedan errores bloqueantes para la demostración.
