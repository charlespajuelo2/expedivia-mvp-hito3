# Acta de cierre — Etapa 2

**Proyecto:** Asistente IA para revisión y evaluación de perfiles y expedientes técnicos de proyectos viales  
**Etapa:** 2 — Procesamiento documental  
**Fecha:** 11/11/2026  
**Estado:** `COMPLETADA`

---

## 1. Aprobación de inicio

| Campo | Valor |
|---|---|
| Solicitada | 11/11/2026 |
| Aprobada por | Usuario |
| Medio | Instrucción en chat: “confirmo el caso representativo, inicia la etapa 2” |
| Fecha | 11/11/2026 |
| Alcance aprobado | Caso representativo `EXP-2024-089`; procesamiento PDF/DOCX/XLSX con validación, clasificación, extracción, SHA-256, caché y corrección humana |

---

## 2. Tareas ejecutadas

- [x] Implementar carga real de archivos (selector múltiple y carpeta local).
- [x] Validar formatos y límites (PDF con texto, DOCX, XLSX; 25 MB).
- [x] Detectar y rechazar PDF escaneado, protegido o dañado con mensaje trazable.
- [x] Implementar clasificación documental (tipo, componente, confianza).
- [x] Permitir corrección humana de la clasificación con motivo y responsable.
- [x] Implementar extracción de texto y tablas con ubicación.
- [x] Calcular hash SHA-256 por documento.
- [x] Implementar caché documental por `sha256 + extractor_version`.
- [x] Persistir inventario, estado y metadatos en SQLite.
- [x] Registrar auditoría de cargas, rechazos, caché y correcciones.
- [x] Construir interfaz Streamlit y CLI.
- [x] Generar corpus del caso y casos borde.
- [x] Ejecutar y documentar 20 pruebas automatizadas.

---

## 3. Evidencia entregada

| Evidencia | Ruta | Estado |
|---|---|---|
| Código del núcleo | `mvp/core/` | ✅ |
| Interfaz Streamlit | `mvp/app.py` | ✅ |
| CLI | `mvp/cli.py` | ✅ |
| Generador de corpus | `mvp/scripts/generar_muestras.py` | ✅ |
| Ejecución reproducible | `mvp/scripts/ejecutar_etapa2.py` | ✅ |
| Corpus del caso | `mvp/etapa2/muestras/caso/` | ✅ |
| Casos borde | `mvp/etapa2/muestras/casos_borde/` | ✅ |
| Reporte de ingesta | `mvp/etapa2/evidencia/01_reporte_ingesta_caso.md` | ✅ |
| Reporte de casos borde | `mvp/etapa2/evidencia/02_reporte_casos_borde.md` | ✅ |
| Reporte de caché | `mvp/etapa2/evidencia/03_reporte_cache.md` | ✅ |
| Reporte de corrección | `mvp/etapa2/evidencia/04_reporte_correccion.md` | ✅ |
| Métricas | `mvp/etapa2/evidencia/05_metricas.json` | ✅ |
| Auditoría | `mvp/etapa2/evidencia/06_auditoria.csv` | ✅ |
| Resultados de pruebas | `mvp/etapa2/evidencia/07_resultados_pruebas.txt` | ✅ |
| Inventario procesado | `mvp/etapa2/evidencia/08_inventario_procesado.csv` | ✅ |
| Base SQLite | `mvp/etapa2/evidencia/mvp_etapa2.db` | ✅ |

---

## 4. Verificación de criterios de salida

| Criterio | Resultado |
|---|---|
| Se cargan los 6 archivos del caso sin errores | ✅ 6/6 válidos |
| Un PDF escaneado se rechaza con mensaje claro y registro | ✅ `PDF_ESCANEADO` |
| La clasificación se puede corregir y queda registrada | ✅ EETT 64 → 100, motivo y actor |
| La extracción devuelve ubicación verificable por fragmento | ✅ 61 fragmentos con página/párrafo/celda |
| Dos cargas del mismo archivo producen el mismo hash y reutilizan caché | ✅ 6/6, 298 → 47 ms (84.2%) |

---

## 5. Resultado de la ejecución

```text
Caso: 6 válidos, 5 clasificados automáticamente, 1 corregido por humano
Casos borde: 4 rechazados con motivo distinto, 1 ambiguo aceptado y pendiente
Caché: 6/6 documentos reutilizados en la segunda carga
Pruebas: 20 passed
```

### Rechazos verificados

| Archivo | Motivo | Resultado |
|---|---|---|
| `PDF_Escaneado.pdf` | `PDF_ESCANEADO` | Rechazado, 0 fragmentos |
| `PDF_Protegido.pdf` | `PDF_PROTEGIDO` | Rechazado, 0 fragmentos |
| `PDF_Corrupto.pdf` | `ARCHIVO_DANADO` | Rechazado, 0 fragmentos |
| `notas.txt` | `FORMATO_NO_SOPORTADO` | Rechazado, 0 fragmentos |

---

## 6. Decisiones registradas

1. La clasificación es **determinista y explicable** (reglas + confianza).
2. El umbral de confianza es **70**; por debajo, el documento queda *Sin clasificar*.
3. La caché se indexa por **SHA-256 + versión del extractor**.
4. Las correcciones humanas se indexan por **SHA-256** y sobreviven a la caché.
5. Un documento rechazado **no genera evidencia** ni se convierte en “No cumple”.
6. El MVP **no incluye OCR**: el PDF escaneado se rechaza con mensaje accionable.

---

## 7. Limitaciones y pendientes

- [ ] OCR para PDF sin capa de texto.
- [ ] Clasificación semántica asistida por IA (Etapa 3).
- [ ] Checklist oficial de 23 ítems y expediente definitivo.
- [ ] Validación de ponderaciones por el especialista.
- [ ] Recuperación de evidencia por requisito y contrato JSON (Etapa 3).

No bloquean la Etapa 3. La base de datos ya conserva hash, ubicación,
clasificación y auditoría, que son los insumos de la siguiente etapa.

---

## 8. Decisión de cierre

La Etapa 2 se declara **COMPLETADA**. Se solicita aprobación para iniciar la
**Etapa 3 — Evidencia e inteligencia artificial**.

| Campo | Valor |
|---|---|
| Solicitada | 11/11/2026 |
| Aprobada por | Pendiente |
| Fecha | Pendiente |
| Observaciones | Pendiente |
