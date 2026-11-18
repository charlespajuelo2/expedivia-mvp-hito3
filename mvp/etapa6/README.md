# Etapa 6 — Integración, pruebas, métricas y entrega

**Estado:** cerrada — Hito 3 cerrado (con dos acciones externas declaradas).
**Caso:** `EXP-2024-089` — Carretera Central Tramo 2 · Km 42–78 (Pavimentos).
**Fecha de cierre:** 12/11/2026.

---

## 1. Qué se entrega

| Artefacto | Ruta | Estado |
|---|---|---|
| Flujo de extremo a extremo | `mvp/scripts/ejecutar_etapa6.py` | ✅ |
| 16 casos de prueba mapeados a CA | `mvp/etapa6/evidencia/02_casos_prueba.md` | ✅ 16/16 |
| Registro de errores y correcciones | `mvp/etapa6/evidencia/03_errores_correcciones.md` | ✅ |
| Línea base vs. sistema | `mvp/etapa6/evidencia/04_metricas_linea_base.md` | ✅ |
| Revisión técnica y formulario de feedback | `mvp/etapa6/evidencia/05_revision_tecnica.md` | ✅ revisión / ☐ feedback |
| Checklist de entrega | `mvp/etapa6/evidencia/06_checklist_entrega.md` | ✅ |
| Guion del video | `mvp/etapa6/evidencia/07_guion_video.md` | ✅ |
| Ensayo de sustentación | `mvp/etapa6/evidencia/08_acta_ensayo.md` | ✅ guion / ☐ ensayo presencial |
| Ficha técnica | `mvp/etapa6/FICHA_TECNICA.md` | ✅ |
| PPT editable y PDF | `mvp/etapa6/entrega/PPT_Expedivia_Hito3.pptx` / `.pdf` | ✅ 14 diapositivas |
| Video demo | `mvp/etapa6/entrega/video_demo.mp4` | ✅ 3:03, narración sintética |
| Capturas reales de la app | `mvp/etapa6/entrega/capturas/` | ✅ 10 |
| Base y exportaciones | `mvp/etapa6/evidencia/` | ✅ |
| Acta de cierre | `mvp/etapa6/07_acta_cierre_etapa6.md` | ✅ |

> **Pendiente externo:** el feedback firmado de un especialista y el ensayo
> presencial cronometrado requieren una persona. No se declaran como recibidos.

---

## 2. Reproducción

```powershell
cd ruta\al\proyecto\hito2-3
python -m pip install -r mvp/requirements.txt
python -m mvp.scripts.ejecutar_etapa6
python -m pytest mvp/tests -q
```

El primer comando regenera el corpus, la base, las decisiones, las
exportaciones y todos los reportes de la etapa. La app se abre con:

```powershell
$env:MVP_DB_PATH = "$PWD\mvp\etapa6\evidencia\mvp_etapa6.db"
python -m streamlit run mvp/app.py
```

Material audiovisual:

```powershell
python -m mvp.scripts.capturar_pantallas_etapa6   # capturas reales
python -m mvp.scripts.grabar_video_etapa6         # video narrado
python -m mvp.scripts.generar_ppt_etapa6          # PPT editable
```

El PPT se convierte a PDF con LibreOffice:

```powershell
& "C:\Program Files\LibreOffice\program\soffice.exe" --headless `
  --convert-to pdf --outdir mvp\etapa6\entrega `
  mvp\etapa6\entrega\PPT_Expedivia_Hito3.pptx
```

---

## 3. Resultado del caso

| Métrica | Valor |
|---|---:|
| Documentos válidos | 8/8 |
| Requisitos con propuesta | 7/7 |
| Cobertura de revisión | 100.0% |
| Peso decidido | 58.0% |
| Avance ponderado | 39.0% |
| Cumplimiento ponderado | 88.6% |
| Decisiones vigentes | 4 |
| Registros de historial | 6 |
| «No cumple» | 0 |
| «No se encontró información» | 1 |
| Casos de prueba | 16/16 PASA |
| Tiempo E2E medido | ~1 s (equipo de demostración) |

La línea base de 260 minutos es una **estimación declarada**. De ellos, 90
minutos corresponden al juicio técnico y siguen siendo humanos; la reducción de
99.99% se refiere solo al trabajo mecánico (170 minutos estimados).

---

## 4. Casos de prueba

| Grupo | Casos | Qué cubre |
|---|---|---|
| Carga y extracción | CP-01 a CP-04 | 8/8 válidos, rechazo, clasificación, ubicación |
| Evidencia y contrato | CP-05 a CP-07 | fuente, cita, hash, 7/7 propuestas |
| Decisión e historial | CP-08 a CP-09 | 6 registros, 4 vigentes, 39.0% |
| Informes | CP-10 a CP-11 | Excel 7 hojas, Word 5 secciones |
| Resiliencia | CP-12, CP-15, CP-16 | reintento, caché, fuente modificada |
| Seguridad y control | CP-13, CP-14 | denegaciones y contingencia |

Detalle y evidencia: `mvp/etapa6/evidencia/02_casos_prueba.md`.

---

## 5. Usuarios de demostración

| Usuario | Rol | Permisos | Expediente |
|---|---|---|---|
| Lucía Ramos | especialista | ver, cargar, analizar, decidir, exportar | `EXP-2024-089` |
| Carlos Méndez | lector | ver | `EXP-2024-089` |
| Admin MVP | administrador | todos (`*`) | todos |

---

## 6. Límites declarados

1. Sin OCR: un PDF escaneado se rechaza.
2. IA real opcional: sin `MVP_IA_API_KEY` se usa el proveedor de reglas.
3. Datos sintéticos: no hay expedientes reales ni información sensible.
4. Acceso de demostración: sin autenticación corporativa ni firma digital.
5. Plantilla oficial pendiente: los informes no sustituyen el formato firmado.
6. Feedback externo y ensayo presencial pendientes de una persona.

---

## 7. Estructura de la etapa

```
mvp/etapa6/
├── README.md
├── FICHA_TECNICA.md
├── config/
│   └── linea_base.json
├── muestras/
│   ├── caso/                 # 8 documentos sintéticos
│   └── error_reintento/      # casos CP-02 y CP-12
├── evidencia/
│   ├── 00_entorno.json
│   ├── 01_flujo_extremo_a_extremo.md
│   ├── 02_casos_prueba.md / .json
│   ├── 03_errores_correcciones.md
│   ├── 04_metricas_linea_base.md
│   ├── 05_revision_tecnica.md
│   ├── 06_checklist_entrega.md
│   ├── 07_guion_video.md
│   ├── 08_acta_ensayo.md
│   ├── 09_ficha_tecnica.md
│   ├── 10_metricas.json
│   ├── mvp_etapa6.db
│   └── exportaciones/
└── entrega/
    ├── PPT_Expedivia_Hito3.pptx / .pdf
    ├── video_demo.mp4
    ├── video_timeline.json
    └── capturas/
```
