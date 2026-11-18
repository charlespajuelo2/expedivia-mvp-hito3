# Acta de cierre — Etapa 5

**Proyecto:** Asistente IA para revisión y evaluación de perfiles y expedientes técnicos de proyectos viales
**Etapa:** 5 — Interfaz, exportación y contingencia visible
**Fecha:** 12/11/2026
**Estado:** `COMPLETADA`

---

## 1. Aprobación de inicio

| Campo | Valor |
|---|---|
| Solicitada | 12/11/2026 |
| Aprobada por | Usuario |
| Medio | Instrucción en chat: “inicia la etapa 5” |
| Fecha | 12/11/2026 |
| Alcance aprobado | Conexión de pantallas al flujo real, exportación `.xlsx` y `.docx`, contingencia visible y operable, errores con avance conservado y reintento, control de acceso mínimo por rol, estados vacíos, accesibilidad básica y medición de tiempos |

---

## 2. Tareas ejecutadas

- [x] Implementar la política de acceso por rol y expedientes asignados.
- [x] Integrar la sesión, el usuario y los permisos en la barra lateral.
- [x] Bloquear con causa las acciones no autorizadas en cada pestaña.
- [x] Implementar la exportación real a Excel con 7 hojas.
- [x] Implementar la exportación real a Word con 5 secciones.
- [x] Agregar la pestaña «6. Exportación e informes» con descargas.
- [x] Hacer visible el modo de contingencia y su resolución manual.
- [x] Manejar errores por archivo sin abortar el lote.
- [x] Conservar el lote y ofrecer «Reintentar procesamiento».
- [x] Validar el estado vacío en pantalla y en ambos formatos.
- [x] Ampliar el CLI con `access` y `export`.
- [x] Medir tiempos de resumen y exportación.
- [x] Generar corpus y base propios en `mvp/etapa5/`, sin alterar las etapas cerradas.
- [x] Ejecutar y documentar 10 pruebas nuevas (61 en total).

---

## 3. Evidencia entregada

| Evidencia | Ruta | Estado |
|---|---|---|
| Política de acceso | `mvp/core/access.py` | ✅ |
| Usuarios y roles | `mvp/etapa5/config/usuarios.json` | ✅ |
| Exportadores Excel/Word | `mvp/core/exporters.py` | ✅ |
| Interfaz con roles y exportación | `mvp/app.py` | ✅ |
| CLI ampliado | `mvp/cli.py` | ✅ |
| Ejecución reproducible | `mvp/scripts/ejecutar_etapa5.py` | ✅ |
| Corpus y base de la etapa | `mvp/etapa5/muestras/`, `mvp/etapa5/evidencia/mvp_etapa5.db` | ✅ |
| Reportes 00–06 y exportaciones | `mvp/etapa5/evidencia/` | ✅ |
| Pruebas | `mvp/tests/test_etapa5.py` | ✅ |
| Guía de la etapa | `mvp/etapa5/README.md` | ✅ |

---

## 4. Verificación de criterios de salida

| Criterio | Resultado |
|---|---|
| Pantallas conectadas al flujo real | ✅ datos desde SQLite; sin resultados fijos |
| Exportación `.xlsx` real | ✅ 7 hojas, 7 requisitos, 6 decisiones |
| Exportación `.docx` real | ✅ 5 secciones, 3 tablas, fuentes e historial |
| Contenido verificado tras escribir | ✅ ambos archivos se reabren con `openpyxl` y `python-docx` |
| Contingencia visible | ✅ bloque dedicado y evaluación manual |
| Error con causa y avance conservado | ✅ `ARCHIVO_DANADO`, avance 39.0% sin cambios |
| Reintento operativo | ✅ 8 → 9 documentos válidos |
| Control de acceso por rol | ✅ 3 denegaciones con causa; lector sin decisión ni exportación |
| Estado vacío | ✅ informes válidos con 0 decisiones y avance 0.0% |
| Tiempos de respuesta | ✅ resumen 24.9 ms; exportación 138.0 ms (< 5000 ms) |
| Pruebas | ✅ 61 passed |

---

## 5. Resultado de la ejecución

```text
Caso: 8 documentos válidos, 7 propuestas válidas
Decisiones: 4 vigentes, 6 registros de historial (RQ-04 con 3)
Avance: 39.0% | Cumplimiento: 88.6% | No cumple: 0 | Sin información: 1
Excel: 7 hojas, 22 349 bytes
Word: 5 secciones, 3 tablas, 39 876 bytes
Tiempos: resumen 24.9 ms | exportación 138.0 ms
Permisos: 3 denegaciones verificadas
Error/reintento: archivo corrupto rechazado; 8 → 9 documentos válidos
Estado vacío: 0 decisiones, avance 0.0%, exportación válida
Pruebas: 61 passed
```

---

## 6. Decisiones registradas

1. La política de acceso es un **JSON de demostración**: roles, permisos y
   asignaciones explícitas, sin autenticación corporativa.
2. La sesión se identifica por usuario; el actor de las decisiones y auditoría es
   el usuario seleccionado, no un campo libre.
3. Las acciones no permitidas se **explican** y se deshabilitan; no se ocultan los
   datos de solo lectura.
4. La exportación se construye **solo desde SQLite** y se valida reabriendo los
   archivos, no confiando en que la escritura terminó sin error.
5. El error de un archivo no revierte el lote: se conserva el avance, las
   decisiones y la caché por SHA-256 para el reintento.
6. El expediente vacío es un caso de prueba de primera clase, no una excepción.
7. La base y el corpus de la Etapa 5 son independientes para no alterar las
   etapas cerradas.

---

## 7. Limitaciones y pendientes

- [ ] Consolidar los 23 requisitos oficiales del checklist.
- [ ] Sustituir el JSON de demostración por autenticación e identidad reales.
- [ ] Validar el cliente OpenAI compatible con credenciales reales.
- [ ] Incorporar firma digital y plantilla oficial del informe.
- [ ] Ejecutar la validación de usabilidad y accesibilidad con usuarios finales.

No bloquean el cierre de la Etapa 5: el flujo completo, la exportación, los roles
y la contingencia están implementados y verificados.

---

## 8. Decisión de cierre

La Etapa 5 se declara **COMPLETADA**. Se solicita aprobación para iniciar la
**Etapa 6 — Validación integral y preparación de la demostración**.

| Campo | Valor |
|---|---|
| Solicitada | 12/11/2026 |
| Aprobada por | Pendiente |
| Fecha | Pendiente |
| Observaciones | Pendiente |
