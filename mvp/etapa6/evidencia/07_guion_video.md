# Evidencia 07 — Guion del video demo (3–5 minutos)

**Archivo:** `mvp/etapa6/entrega/video_demo.mp4`
**Duración real:** 3:03.
**Formato:** grabación de pantalla de la app real con narración sintetizada en
español (voz `Microsoft Helena Desktop`, es-ES). No es una locución humana.
**Reproducción:** `python -m mvp.scripts.grabar_video_etapa6` regenera la
grabación y la narración sobre la base de la Etapa 6.

| Tiempo | Escena | Acción en pantalla | Narración |
|---:|---|---|---|
| 0:00–0:21 | Apertura | Portada de la app y caso `EXP-2024-089` | Qué es Expedivia y qué problema resuelve. |
| 0:21–0:44 | Carga | Pestaña 2: 8 documentos, hash y clasificación | Validación, caché y corrección humana. |
| 0:44–1:04 | Extracción | Pestaña 3 con `TDR_Carretera_Central_v3.pdf` | Página, párrafo, hoja y fila como ubicación. |
| 1:04–1:27 | Evidencia | Pestaña 4: cobertura, propuestas e integridad | Contrato JSON, fuente, cita y hash. |
| 1:27–1:52 | Decisión | Pestaña 5: métricas, RQ-04 e historial | Aceptar, modificar, descartar y avance 39.0%. |
| 1:52–2:12 | Exportación | Pestaña 6: informes generados y descargas | Excel/Word construidos desde SQLite. |
| 2:12–2:30 | Auditoría | Pestaña 7: eventos y verificaciones | Trazabilidad de cada acción. |
| 2:30–2:47 | Permisos | Usuario lector y bloqueo explicado | Un lector no decide ni exporta. |
| 2:47–3:07 | Cierre | Pestaña 8: límites y pendientes | Sin OCR, IA opcional, datos sintéticos y feedback pendiente. |

## Reglas de grabación

1. Se muestran los estados reales de la base, sin ocultar bloqueos ni límites.
2. La narración se genera con síntesis de voz; debe declararse así en la
   sustentación.
3. El video se produce con `mvp/scripts/grabar_video_etapa6.py`; no se editan
   saltos que oculten pasos.
4. La línea de tiempo y los textos están en `mvp/etapa6/entrega/video_timeline.json`.

## Criterio de salida cubierto

- [x] Video de 3:03 con las nueve escenas del flujo.
- [x] Narración en español y acciones reales sobre la app.
- [x] Se explican limitaciones y pendientes.
- [ ] Locución humana y grabación con cámara del equipo (opcional, no requerido).
