# Etapa 2 — Procesamiento documental

**Estado:** `COMPLETADA`  
**Fecha de cierre:** 11/11/2026  
**Aprobación de inicio:** Usuario — “confirmo el caso representativo, inicia la etapa 2” (11/11/2026)  
**Responsable:** Equipo del proyecto / Especialista vial senior (por designar)

---

## 1. Objetivo

Implementar el **procesamiento documental real** del MVP: carga de archivos,
validación, clasificación, extracción con ubicación, hash SHA-256, caché y
corrección humana persistente, sobre el caso representativo `EXP-2024-089`.

---

## 2. Entregables

### 2.1 Código

| Archivo | Función |
|---|---|
| `mvp/core/config.py` | Rutas, límites, versión del extractor y umbral |
| `mvp/core/hashing.py` | SHA-256 por archivo y por texto |
| `mvp/core/db.py` | Esquema SQLite, conexión y auditoría |
| `mvp/core/extractors.py` | Extracción PDF/DOCX/XLSX con ubicación |
| `mvp/core/classifier.py` | Clasificación determinista y confianza |
| `mvp/core/pipeline.py` | Ingesta, caché, corrección y métricas |
| `mvp/cli.py` | Operación por línea de comandos |
| `mvp/app.py` | Interfaz Streamlit (5 pestañas) |
| `mvp/scripts/generar_muestras.py` | Corpus del caso y casos borde |
| `mvp/scripts/ejecutar_etapa2.py` | Evidencia reproducible |
| `mvp/tests/test_core.py` | 20 pruebas automatizadas |

### 2.2 Corpus de prueba

`mvp/etapa2/muestras/`

| Carpeta | Archivo | Propósito |
|---|---|---|
| `caso/` | `TDR_Carretera_Central_v3.pdf` | PDF con texto y tabla |
| `caso/` | `Presupuesto.xlsx` | Fórmulas con valor en caché; celda `F18` |
| `caso/` | `Memoria_Calculo_Pavimentos.docx` | Párrafos, secciones y tabla |
| `caso/` | `Planos_PL-01_PL-08.pdf` | PDF parcial: páginas 3–5 sin texto |
| `caso/` | `EETT_General_v2.docx` | Documento ambiguo (confianza 64) |
| `caso/` | `Estudio_Suelos_Lab.xlsx` | Dos hojas con ensayos |
| `casos_borde/` | `PDF_Escaneado.pdf` | Sin capa de texto |
| `casos_borde/` | `PDF_Protegido.pdf` | Cifrado con contraseña |
| `casos_borde/` | `PDF_Corrupto.pdf` | PDF truncado |
| `casos_borde/` | `Documento_General.pdf` | Sin señales clasificables |
| `casos_borde/` | `notas.txt` | Formato no soportado |

### 2.3 Evidencia

`mvp/etapa2/evidencia/`

| Archivo | Contenido |
|---|---|
| `00_entorno.json` | Versiones de librerías y rutas |
| `01_reporte_ingesta_caso.md` | Carga de los 6 documentos |
| `02_reporte_casos_borde.md` | Rechazos y documento ambiguo |
| `03_reporte_cache.md` | Primera vs. segunda carga |
| `04_reporte_correccion.md` | Corrección humana y persistencia |
| `05_metricas.json` | Métricas agregadas |
| `06_auditoria.csv` | Bitácora completa |
| `07_resultados_pruebas.txt` | Salida de pytest (20 passed) |
| `08_inventario_procesado.csv` | Inventario final con hash |
| `mvp_etapa2.db` | Base SQLite con los resultados |

---

## 3. Resultados verificados

| Criterio de salida | Resultado | Evidencia |
|---|---|---|
| Se cargan los 6 archivos del caso sin errores | ✅ 6/6 válidos | `01_reporte_ingesta_caso.md` |
| Un PDF escaneado se rechaza con mensaje claro y registro | ✅ `PDF_ESCANEADO` | `02_reporte_casos_borde.md` |
| La clasificación se puede corregir y queda registrada | ✅ EETT 64 → 100 | `04_reporte_correccion.md` |
| La extracción devuelve ubicación verificable por fragmento | ✅ 61 fragmentos | `01_reporte_ingesta_caso.md` |
| Dos cargas del mismo archivo producen el mismo hash y reutilizan caché | ✅ 6/6, 298 → 47 ms | `03_reporte_cache.md` |

### 3.1 Métricas de la etapa

| Indicador | Valor |
|---|---:|
| Documentos del caso | 6 |
| Válidos | 6 |
| Clasificados automáticamente | 5 |
| Corregidos por humano | 1 |
| Fragmentos almacenados | 61 |
| Texto completo / parcial | 5 / 1 |
| Tiempo primera carga | 298 ms |
| Tiempo segunda carga (caché) | 47 ms |
| Reducción por caché | 84.2% |
| Casos borde rechazados | 4 de 4 esperados |
| Documento ambiguo aceptado y pendiente de corrección | 1 |
| Pruebas automatizadas | 20 passed |

> Los tiempos corresponden a un equipo de desarrollo estándar y a archivos
> pequeños de demostración; sirven como línea base reproducible, no como
> benchmark de producción.

---

## 4. Decisiones de diseño

### D1 — Clasificación determinista, no IA

La clasificación usa señales del nombre y del texto (palabras clave ponderadas)
y devuelve las coincidencias que la sustentan. Es reproducible y auditable. La
IA se incorpora en la Etapa 3 para el análisis de requisitos, no para esta
clasificación.

### D2 — Confianza explicable

```
densidad  = mejor / (mejor + segundo + 1)
cobertura = min(1, mejor / 65)
confianza = round(100 × (0.5 × densidad + 0.5 × cobertura))
```

Con umbral 70. Un documento por debajo del umbral queda **Sin clasificar** y
exige corrección humana. Un documento sin ninguna señal es `No reconocido` con
confianza 0.

### D3 — Caché por hash y versión del extractor

La clave es `sha256 + extractor_version`. Si cambia la lógica de extracción, la
caché se invalida de forma controlada. La caché guarda solo extracciones
exitosas; los rechazos se reproducen y se registran.

### D4 — Correcciones separadas de la caché

Las correcciones humanas viven en `correcciones_clasificacion`, indexadas por
SHA-256. Así, una recarga con acierto de caché **no pierde** la decisión humana.

### D5 — Rechazo ≠ incumplimiento

Un documento rechazado no genera fragmentos ni evidencia. Nunca se convierte en
“No cumple”. Esta regla se aplicará en la evaluación de requisitos (Etapa 4).

### D6 — Sin OCR en el MVP

Un PDF escaneado se rechaza con mensaje accionable. Se documenta como limitación
y se deja la ruta de mejora (OCR) para una versión posterior.

---

## 5. Pruebas

```powershell
python -m pytest mvp/tests -q
```

Cobertura funcional:

- Hash estable y distinto por contenido.
- Extracción de PDF, PDF parcial, DOCX y XLSX con ubicación.
- Rechazo de PDF escaneado, protegido, corrupto y formato no soportado.
- Clasificación de alta confianza, ambigua y no reconocida.
- Umbral de confianza configurable.
- Ingesta completa del caso.
- Caché en la segunda carga con hashes idénticos.
- Corrección humana que sobrevive a la caché.
- Rechazos con motivo y sin fragmentos.
- Auditoría y exportación del inventario.

Resultado: **20 passed** (`07_resultados_pruebas.txt`).

---

## 6. Limitaciones y pendientes

- [ ] OCR para PDF sin capa de texto (hoy se rechaza).
- [ ] Clasificación semántica asistida por IA (Etapa 3).
- [ ] Checklist oficial de 23 ítems y expediente definitivo.
- [ ] Validación de las ponderaciones por el especialista.
- [ ] Evaluación de requisitos, exportación y contingencia (Etapas 3–5).

Estos pendientes **no bloquean** la Etapa 3: la estructura de datos ya conserva
hash, ubicación, clasificación y auditoría.

---

## 7. Próximo paso

Solicitar aprobación para iniciar la **Etapa 3 — Evidencia e inteligencia
artificial**.
