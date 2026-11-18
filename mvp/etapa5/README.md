# Etapa 5 — Interfaz, exportación y contingencia visible

**Estado:** `COMPLETADA`
**Caso:** `EXP-2024-089` — Carretera Central Tramo 2 · Km 42–78 (Pavimentos, datos sintéticos)
**Fecha de cierre:** 12/11/2026
**Alcance aprobado:** conectar las pantallas al flujo real sin datos fijos, exportación
`.xlsx` y `.docx`, modo de contingencia visible y operable, manejo de errores con
avance conservado y reintento, control de acceso mínimo por rol, estados vacíos,
accesibilidad básica y medición de tiempos.

---

## 1. Qué se construyó

| Componente | Archivo | Responsabilidad |
|---|---|---|
| Política de acceso | `core/access.py` | Roles, permisos, expedientes asignados y `AccesoDenegado` |
| Configuración de usuarios | `etapa5/config/usuarios.json` | `administrador`, `especialista`, `lector` |
| Exportación real | `core/exporters.py` | Excel de 7 hojas y Word de 5 secciones desde SQLite |
| Rutas de la etapa | `core/config.py` | `DIR_ETAPA5`, evidencia, muestras y `RUTA_USUARIOS` |
| Interfaz | `app.py` | Sesión por rol, bloqueos explicados, pestaña «6. Exportación e informes» |
| Contingencia visible | `app.py` | Lista de requisitos afectados y resolución manual motivada |
| Manejo de errores | `app.py` | Error por archivo, avance conservado y «Reintentar procesamiento» |
| CLI | `cli.py` | `access` y `export` con verificación de permisos |
| Evidencia reproducible | `scripts/ejecutar_etapa5.py` | Base, corpus, reportes 00–06 y aserciones |
| Pruebas | `tests/test_etapa5.py` | 10 pruebas nuevas (61 en total) |

---

## 2. Control de acceso mínimo

La política es un JSON de demostración, no un sistema de identidad:

| Rol | Permisos | Alcance |
|---|---|---|
| `administrador` | ver, cargar, analizar, decidir, exportar, administrar | Todos los expedientes (`*`) |
| `especialista` | ver, cargar, analizar, decidir, exportar | Solo expedientes asignados |
| `lector` | ver | Solo expedientes asignados |

Reglas aplicadas en la interfaz y el CLI:

- Sin permiso `ver` o sin expediente asignado se detiene la sesión con causa.
- El lector ve resultados, pero no carga, corrige, analiza, decide ni exporta.
- Las acciones bloqueadas muestran un mensaje que explica el motivo; no se
  ocultan los datos de solo lectura.
- La exportación exige `exportar` **y** expediente asignado antes de crear
  archivos.

Usuarios de demostración:

| Usuario | Rol | Expedientes |
|---|---|---|
| Admin MVP | administrador | `*` |
| Lucía Ramos | especialista | `EXP-2024-089` |
| Carlos Méndez | lector | `EXP-2024-089` |

---

## 3. Exportación real

Ambos formatos se construyen consultando SQLite, no desde valores fijos.

### Excel (`openpyxl`)

| Hoja | Contenido |
|---|---|
| `Resumen` | Metadatos, métricas, fórmula de avance |
| `Requisitos` | Peso, criterio, estado propuesto/final, decisión, fuente y cita |
| `Decisiones` | Historial inmutable con propuesta original y vigencia |
| `Propuestas` | Proveedor, validez, integridad, SHA-256 y huella |
| `Evidencias` | Fuente, ubicación, tipo documental, puntaje y texto |
| `Documentos` | Inventario, clasificación, texto recuperable y hash |
| `Auditoría` | Bitácora completa |

### Word (`python-docx`)

1. Resumen ejecutivo con tabla de métricas y fórmula.
2. Resultados por requisito.
3. Observaciones y fuentes con archivo, ubicación, SHA-256 y cita.
4. Historial de decisiones.
5. Alcance y limitaciones, con espacio de firma.

La descarga se ofrece desde la pestaña «6. Exportación e informes» y desde el CLI
(`python -m mvp.cli export`).

---

## 4. Contingencia visible

La pestaña «4. Evidencia y análisis» incorpora un bloque **Modo de contingencia**:

- Detecta requisitos con `contingencia` o `integridad_alerta`.
- Muestra origen, estado actual, integridad y motivo.
- Permite resolver con evaluación manual obligatoria (estado, motivo y
  responsable).
- Deja el avance y las decisiones previas intactos.
- Si el usuario no puede decidir, el bloque es de solo lectura y lo explica.

---

## 5. Errores, reintento y estados vacíos

| Situación | Comportamiento |
|---|---|
| Archivo corrupto | Se rechaza con `ARCHIVO_DANADO` y mensaje; el lote continúa |
| Error inesperado | Se registra por archivo y no aborta el resto |
| Reintento | Vuelve a procesar el lote; reutiliza la caché por SHA-256 |
| Avance y decisiones | Se conservan durante el error y el reintento |
| Expediente vacío | Métricas en 0, exportación válida y mensaje «sin decisiones» |
| Sin evidencia | `No se encontró información`; nunca `No cumple` |

La interfaz conserva el último lote en `st.session_state` para ofrecer el
reintento sin volver a seleccionar archivos.

---

## 6. Resultado del caso

| Métrica | Valor |
|---|---:|
| Documentos válidos | 8 → 9 tras el reintento |
| Requisitos | 7 |
| Cobertura de revisión | 100.0% |
| Peso decidido | 58.0% |
| **Avance ponderado** | **39.0%** |
| Cumplimiento ponderado | 88.6% |
| Decisiones vigentes | 4 |
| Historial de decisiones | 6 registros (RQ-04 con 3) |
| No cumple | 0 |
| No se encontró información | 1 |

### Exportación verificada

| Artefacto | Verificación |
|---|---|
| `informe_EXP-2024-089.xlsx` | 7 hojas, 7 requisitos, 6 decisiones, avance 39.0% |
| `informe_EXP-2024-089.docx` | 5 secciones, 3 tablas, fuentes, historial y limitaciones |
| `estado_vacio/informe_...xlsx` | 7 hojas, 0 decisiones |
| `estado_vacio/informe_...docx` | «Sin decisiones registradas», avance 0.0% |

### Tiempos medidos

| Operación | Milisegundos | Umbral |
|---|---:|---:|
| Resumen del expediente | 24.9 | 5000 |
| Exportación Excel + Word | 138.0 | 5000 |

---

## 7. Evidencia reproducible

```powershell
python -m mvp.scripts.ejecutar_etapa5
```

Genera en `mvp/etapa5/evidencia/`:

| Archivo | Contenido |
|---|---|
| `00_entorno.json` | Versiones, rutas, política y umbral |
| `01_reporte_caso.md` | Métricas e historial del caso |
| `02_reporte_exportacion.md` | Hojas, secciones, contenido y tiempos |
| `03_reporte_permisos.md` | Matriz de acceso y denegaciones |
| `04_reporte_errores_reintento.md` | Error, conservación y reintento |
| `05_reporte_estado_vacio.md` | Exportación sin documentos ni decisiones |
| `06_metricas.json` | Métricas comparables, permisos y tiempos |
| `exportaciones/` | Informes XLSX/DOCX del caso y del estado vacío |
| `mvp_etapa5.db` | Base SQLite de la etapa |

El script termina con aserciones sobre permisos, contenido de los archivos,
conservación del avance, reintento, estado vacío y umbral de tiempo.

---

## 8. Pruebas

```powershell
python -m pytest mvp/tests -q
```

Resultado: **61 passed** (20 de Etapa 2 + 17 de Etapa 3 + 14 de Etapa 4 + 10 de
Etapa 5).

Cobertura nueva:

- Roles, permisos, asignaciones y denegaciones con causa.
- Validación de políticas incompletas o con permisos desconocidos.
- Excel con 7 hojas, filas y avance reales.
- Word con 5 secciones, tablas, fuentes e historial.
- Exportación dinámica: una nueva decisión cambia el archivo.
- Contingencia visible y resolución manual.
- Error de archivo sin pérdida de avance ni decisiones.
- Reintento exitoso que agrega el documento válido.
- Estado vacío exportable sin excepciones.
- Arranque de la interfaz y bloqueo de acciones para el rol lector.

---

## 9. Limitaciones conocidas

- La política de acceso es un JSON de demostración; no hay autenticación real,
  sesiones firmadas ni integración con directorio corporativo.
- Las asignaciones usan el identificador del expediente, no reglas organizativas.
- No se valida el cliente OpenAI compatible contra un servicio real por falta de
  credenciales; el flujo usa el proveedor determinista de reglas.
- La exportación incluye datos sintéticos del caso; no sustituye el informe
  oficial firmado.
- Los 7 requisitos representativos siguen pendientes de consolidarse con los 23
  requisitos oficiales.

---

## 10. Criterios de salida

- [x] Las pantallas consumen datos persistidos; no hay resultados fijos.
- [x] Se generan `.xlsx` y `.docx` reales y se verifica su contenido.
- [x] La contingencia es visible y operable con evaluación manual.
- [x] Los errores muestran causa, conservan avance y permiten reintentar.
- [x] El control de acceso por rol bloquea lectura, decisión y exportación no
      autorizadas.
- [x] Los estados vacíos se comunican sin excepciones.
- [x] Los tiempos de respuesta quedan medidos y bajo el umbral definido.
