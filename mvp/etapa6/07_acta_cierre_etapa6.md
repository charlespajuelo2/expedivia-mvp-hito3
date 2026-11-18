# Acta de cierre — Etapa 6

**Proyecto:** Asistente IA para revisión y evaluación de perfiles y expedientes técnicos de proyectos viales
**Etapa:** 6 — Integración, pruebas, métricas y entrega del Hito 3
**Fecha:** 12/11/2026
**Estado:** `CERRADA — HITO 3 CERRADO` (con dos acciones externas declaradas)

---

## 1. Aprobación de inicio

| Campo | Valor |
|---|---|
| Solicitada | 12/11/2026 |
| Aprobada por | Usuario |
| Medio | Instrucción en chat: “inicia la etapa 6” |
| Fecha | 12/11/2026 |
| Alcance aprobado | Flujo completo de extremo a extremo, al menos 10 casos de prueba mapeados a criterios de aceptación, registro de errores y correcciones, medición línea base vs. sistema, retroalimentación de un especialista, PPT final de 10–15 diapositivas con 9 secciones, video demo de 3–5 minutos, ficha técnica reproducible, enlaces de respaldo y ensayo de sustentación |

---

## 2. Tareas ejecutadas

- [x] Integrar el flujo completo: ingesta, extracción, evidencia, análisis, decisión, evaluación y exportación.
- [x] Crear un comando único de reproducción con corpus y base propios de la etapa.
- [x] Diseñar y ejecutar 16 casos de prueba mapeados a los criterios de aceptación.
- [x] Aislar los casos de resiliencia en un expediente de pruebas para no contaminar el caso principal.
- [x] Medir los tiempos reales del flujo y compararlos con una línea base declarada.
- [x] Registrar 7 errores reales con causa, corrección y caso de verificación.
- [x] Generar 10 capturas reales de la app, sin errores de consola.
- [x] Generar la presentación final de 14 diapositivas y 9 secciones en PPTX y PDF.
- [x] Grabar el video demo de 3:03 sobre la app real, con narración sintética en español.
- [x] Escribir la ficha técnica reproducible y la guía de la etapa.
- [x] Preparar el guion y el acta de ensayo de sustentación.
- [x] Actualizar la app, el README general y el plan maestro.
- [x] Ejecutar y documentar 12 pruebas nuevas (73 en total).

---

## 3. Evidencia entregada

| Evidencia | Ruta | Estado |
|---|---|---|
| Flujo de extremo a extremo | `mvp/scripts/ejecutar_etapa6.py` | ✅ |
| Reportes 00–10 | `mvp/etapa6/evidencia/` | ✅ |
| Base SQLite del caso | `mvp/etapa6/evidencia/mvp_etapa6.db` | ✅ |
| Exportaciones Excel/Word | `mvp/etapa6/evidencia/exportaciones/` | ✅ |
| 16 casos mapeados a CA | `mvp/etapa6/evidencia/02_casos_prueba.md` / `.json` | ✅ 16/16 |
| Errores y correcciones | `mvp/etapa6/evidencia/03_errores_correcciones.md` | ✅ |
| Métricas línea base vs. sistema | `mvp/etapa6/evidencia/04_metricas_linea_base.md` | ✅ |
| Revisión técnica y formulario | `mvp/etapa6/evidencia/05_revision_tecnica.md` | ✅ revisión / ☐ feedback |
| Checklist de entrega y respaldos | `mvp/etapa6/evidencia/06_checklist_entrega.md` | ✅ |
| Guion del video | `mvp/etapa6/evidencia/07_guion_video.md` | ✅ |
| Guion y acta de ensayo | `mvp/etapa6/evidencia/08_acta_ensayo.md` | ✅ guion / ☐ ensayo |
| Ficha técnica | `mvp/etapa6/FICHA_TECNICA.md` | ✅ |
| Guía de la etapa | `mvp/etapa6/README.md` | ✅ |
| PPT editable y PDF | `mvp/etapa6/entrega/PPT_Expedivia_Hito3.pptx` / `.pdf` | ✅ 14 diapositivas |
| Video demo | `mvp/etapa6/entrega/video_demo.mp4` | ✅ 3:03 |
| Capturas reales | `mvp/etapa6/entrega/capturas/` | ✅ 10 |
| Pruebas de aceptación | `mvp/tests/test_etapa6.py` | ✅ |

---

## 4. Verificación de criterios de salida

| Criterio | Resultado |
|---|---|
| Flujo completo reproducible | ✅ `python -m mvp.scripts.ejecutar_etapa6`, desde cero |
| Casos de prueba ≥ 10 mapeados a CA | ✅ 16/16 PASA, con CA y evidencia por caso |
| Caso principal sin contaminación | ✅ 8/8 documentos válidos; resiliencia aislada en `EXP-2024-089-PRUEBAS` |
| Evidencia con fuente, cita y hash | ✅ 7/7 propuestas válidas |
| Decisión humana e historial inmutable | ✅ 4 vigentes, 6 registros, RQ-04 con 3 |
| Avance y cumplimiento verificables | ✅ 39.0% y 88.6%; `no_cumple=0`, `sin_informacion=1` |
| Exportación real desde SQLite | ✅ Excel 7 hojas; Word 5 secciones; archivos reabiertos |
| Errores documentados | ✅ 7 incidencias con causa, corrección y verificación |
| Línea base vs. sistema | ✅ 1081.3 ms medidos; reducción mecánica 99.99% |
| PPT de 10–15 diapositivas y 9 secciones | ✅ 14 diapositivas, 9 secciones, PPTX y PDF |
| Video demo de 3–5 minutos | ✅ 3:03, app real, narración sintética declarada |
| Ficha técnica reproducible | ✅ `mvp/etapa6/FICHA_TECNICA.md` |
| Enlaces de respaldo | ✅ checklist y README de la etapa |
| Pruebas automatizadas | ✅ 73 passed |

---

## 5. Resultado de la ejecución

```text
Caso: 8 documentos válidos, 7 propuestas válidas
Decisiones: 4 vigentes, 6 registros de historial (RQ-04 con 3)
Avance: 39.0% | Cumplimiento: 88.6% | No cumple: 0 | Sin información: 1
Casos de prueba: 16/16 PASA
Tiempo E2E: 1081.3 ms
Línea base mecánica: 170 min | Reducción mecánica: 99.99%
Excel: 7 hojas, 21 967 bytes
Word: 5 secciones, 3 tablas, 39 770 bytes
PPT: 14 diapositivas, 348 029 bytes (PPTX) / 845 952 bytes (PDF)
Video: 3:03, 6 044 388 bytes
Pruebas: 73 passed
```

---

## 6. Decisiones registradas

1. La **ausencia de evidencia no se convierte en incumplimiento**: el caso queda en
   «No se encontró información» y así se informa.
2. El avance pondera **solo decisiones humanas**; el cumplimiento solo considera
   estados concluyentes. Se reportan como métricas distintas.
3. El historial es **inmutable**: cada decisión agrega un registro y la vigente es
   la de mayor `id`.
4. Los casos de resiliencia (CP-02 y CP-12) se ejecutan en un **expediente de
   pruebas** para no alterar el caso principal.
5. La línea base es una **estimación declarada**, no un cronometraje; la reducción
   de 99.99% se refiere solo al trabajo mecánico.
6. El video y las capturas se generan con **scripts reproducibles** sobre la app
   real; la narración es sintética y se declara como tal.
7. El PPT y su PDF se regeneran desde el código; las cifras de tiempo se leen de
   `10_metricas.json` para no quedar desactualizadas.

---

## 7. Limitaciones y pendientes

- [ ] Obtener el **feedback firmado de un especialista** y adjuntarlo al formulario
      de `05_revision_tecnica.md`.
- [ ] Ejecutar el **ensayo presencial cronometrado** con el equipo; el guion está
      listo en `08_acta_ensayo.md`.
- [ ] Incorporar OCR para PDF escaneado.
- [ ] Validar el proveedor de IA real con credenciales y cuota.
- [ ] Sustituir la política de acceso de demostración por autenticación real.
- [ ] Adoptar la plantilla oficial firmada de los informes.
- [ ] Validar la usabilidad con usuarios finales.

Ninguno de estos puntos bloquea el cierre técnico de la Etapa 6: el flujo, los
casos, las métricas y los materiales de entrega están implementados y verificados.
El feedback y el ensayo requieren personas y no se declaran como recibidos.

---

## 8. Decisión de cierre

La Etapa 6 se declara **COMPLETADA** y el **Hito 3 se da por CERRADO**. El
usuario revisó y aceptó el paquete final. Las dos acciones externas pendientes
(feedback firmado y ensayo presencial) quedan declaradas para completarse antes
de la sustentación; no bloquean el cierre técnico.

| Campo | Valor |
|---|---|
| Solicitada | 12/11/2026 |
| Aprobada por | Usuario |
| Medio | Instrucción en chat: “da por cerrado el paquete” |
| Fecha | 12/11/2026 |
| Observaciones | Paquete de la Etapa 6 aceptado; Hito 3 cerrado con pendientes externos declarados |
