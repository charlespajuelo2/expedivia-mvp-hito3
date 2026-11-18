# Ficha técnica — Expedivia MVP (Hito 3)

**Producto:** Expedivia — asistente de revisión de expedientes técnicos viales.
**Versión:** MVP Hito 3 · cierre de Etapa 6.
**Fecha:** 12/11/2026.
**Caso de demostración:** `EXP-2024-089` — Carretera Central Tramo 2 · Km 42–78
(Pavimentos, datos sintéticos representativos).
**Responsable:** equipo del proyecto.

---

## 1. Qué resuelve

La revisión de un expediente técnico vial exige leer documentos dispersos
(PDF, DOCX, XLSX), ubicar evidencia para cada requisito del checklist, decidir y
dejar trazabilidad. Expedivia:

1. ingesta y valida los documentos;
2. extrae texto conservando página, párrafo o fila;
3. recupera evidencia y propone un estado con fuente y cita;
4. exige que una persona acepte, modifique o descarte la propuesta;
5. calcula avance y cumplimiento solo con decisiones humanas;
6. exporta informes Excel y Word construidos desde SQLite.

La IA **no decide**. La ausencia de evidencia nunca se convierte en
«No cumple»: se registra como «No se encontró información».

## 2. Requisitos del entorno

| Elemento | Versión / valor |
|---|---|
| Sistema operativo | Windows 10/11 (probado en el equipo de demostración) |
| Python | 3.13 |
| Interfaz | Streamlit 1.65.0 |
| Base de datos | SQLite (incluida con Python) |
| Dependencias | `mvp/requirements.txt` |

Dependencias principales: `pypdf 7.0.1`, `pdfplumber 0.11.10`,
`python-docx 1.2.0`, `openpyxl 3.1.5`, `streamlit 1.65.0`,
`reportlab 5.1.0`, `xlsxwriter 3.3.1`, `python-pptx 1.0.2`, `pytest`.
Las capturas y el video requieren además `playwright` e `imageio-ffmpeg`
(`mvp/requirements-media.txt`, opcional).

## 3. Instalación reproducible

```powershell
cd ruta\al\proyecto\hito2-3
python -m pip install -r mvp/requirements.txt
```

Verificación rápida:

```powershell
python -c "import streamlit, pypdf, docx, openpyxl; print('entorno OK')"
```

## 4. Datos de demostración

| Ruta | Contenido |
|---|---|
| `mvp/etapa6/muestras/caso/` | 8 documentos sintéticos: 2 PDF, 2 DOCX, 4 XLSX |
| `mvp/etapa6/evidencia/mvp_etapa6.db` | Base con expedientes, documentos, propuestas, decisiones y auditoría |
| `mvp/etapa6/evidencia/exportaciones/` | Informes XLSX y DOCX generados desde SQLite |

Expedientes:

- `EXP-2024-089`: caso principal, 8 documentos y 7 requisitos.
- `EXP-2024-089-SIN-EVIDENCIA`: control de ausencia de evidencia.
- `EXP-2024-089-PRUEBAS`: aislamiento de los casos de resiliencia CP-02 y CP-12.
- `EXP-2024-090`: expediente reservado al rol administrador.

## 5. Ejecución

### 5.1 Flujo completo desde cero (recomendado)

```powershell
python -m mvp.scripts.ejecutar_etapa6
```

Este comando:

- regenera el corpus y la base de la Etapa 6;
- ejecuta ingesta, clasificación, evidencia, análisis, decisiones y exportación;
- ejecuta los 16 casos de prueba mapeados a criterios de aceptación;
- escribe los reportes `00` a `10` en `mvp/etapa6/evidencia/`.

Resultado esperado: `16/16 casos PASA`, avance `39.0%`, cumplimiento `88.6%`.

### 5.2 Interfaz

```powershell
$env:MVP_DB_PATH = "$PWD\mvp\etapa6\evidencia\mvp_etapa6.db"
python -m streamlit run mvp/app.py
```

Abrir `http://localhost:8501`. La barra lateral permite elegir usuario, rol y
expediente. La base de datos puede cambiarse en el campo «Base de datos SQLite».

Demo pública: <https://expedivia-mvp.streamlit.app>. Al primer arranque copia el
caso `EXP-2024-089` desde la evidencia de la Etapa 6 si la base de trabajo no
existe; el almacenamiento de Community Cloud es efímero.

### 5.3 Pruebas automatizadas

```powershell
python -m pytest mvp/tests -q
```

## 6. Usuarios y roles de demostración

| Usuario | Rol | Permisos | Expediente |
|---|---|---|---|
| Lucía Ramos | especialista | ver, cargar, analizar, decidir, exportar | `EXP-2024-089` |
| Carlos Méndez | lector | ver | `EXP-2024-089` |
| Admin MVP | administrador | todos (`*`) | todos |

La política vive en `mvp/etapa5/config/usuarios.json`. Es una política de
demostración: no sustituye autenticación real ni identidad corporativa.

## 7. Flujo de uso en la interfaz

| Pestaña | Qué hace |
|---|---|
| 1. Carga | Sube PDF/DOCX/XLSX, valida formato, tamaño, hash y caché |
| 2. Documentos y clasificación | Muestra estado, tipo, componente y corrección humana |
| 3. Extracción | Consulta fragmentos con página, párrafo o fila |
| 4. Evidencia y análisis | Recupera evidencia, valida contrato JSON, muestra integridad |
| 5. Evaluación y avance | Acepta, modifica o descarta; historial inmutable y métricas |
| 6. Exportación e informes | Genera y descarga XLSX/DOCX desde SQLite |
| 7. Métricas y auditoría | Consulta eventos, integridad y estado del expediente |
| 8. Guía | Explica criterios, límites y reproducción |

## 8. Resultados del caso

| Métrica | Valor |
|---|---:|
| Documentos válidos | 8/8 |
| Requisitos con propuesta válida | 7/7 |
| Cobertura de revisión | 100.0% |
| Peso decidido | 58.0% |
| Avance ponderado | 39.0% |
| Cumplimiento ponderado | 88.6% |
| Decisiones vigentes | 4 |
| Registros de historial | 6 |
| Estado «No cumple» | 0 |
| Estado «No se encontró información» | 1 |

Fórmula del avance: `Σ(peso del requisito × factor_avance) / Σ(pesos) × 100`,
donde `factor_avance` es 0 si el requisito no tiene decisión o si la decisión es
`descartar`; en caso contrario es el factor del estado final vigente
(`Cumple = 1`, `Cumple parcialmente = 0.5`, `No cumple = 0`). Aceptar y
modificar usan el mismo factor: lo determina el estado final, no la decisión.

Cobertura de revisión: peso de los requisitos ya analizados (con propuesta o
evaluación manual) sobre el peso total. Peso decidido: peso de los requisitos
con decisión humana vigente.

## 9. Casos de prueba

16 casos (`CP-01` a `CP-16`) mapeados a los criterios de aceptación del Hito 2.
Cubren carga, rechazo, clasificación, extracción, evidencia, contrato JSON,
ausencia de información, historial, avance, exportación, error/reintento,
permisos, contingencia, caché e integridad.

Detalle: `mvp/etapa6/evidencia/02_casos_prueba.md`.

## 10. Artefactos de entrega

| Artefacto | Ruta |
|---|---|
| Aplicación | `mvp/app.py` |
| Flujo reproducible | `mvp/scripts/ejecutar_etapa6.py` |
| Evidencia completa | `mvp/etapa6/evidencia/` |
| Presentación editable | `mvp/etapa6/entrega/PPT_Expedivia_Hito3.pptx` |
| Presentación PDF | `mvp/etapa6/entrega/PPT_Expedivia_Hito3.pdf` |
| Guion del video | `mvp/etapa6/evidencia/07_guion_video.md` |
| Video demo | `mvp/etapa6/entrega/video_demo.mp4` (3:03, narración sintética) |
| Guía de la etapa | `mvp/etapa6/README.md` |
| Acta de cierre | `mvp/etapa6/07_acta_cierre_etapa6.md` |

## 11. Registro de errores

Las incidencias de integración y sus correcciones están en
`mvp/etapa6/evidencia/03_errores_correcciones.md`. No quedan errores
bloqueantes para la demostración.

## 12. Límites conocidos

1. **Sin OCR:** un PDF escaneado se rechaza como no recuperable.
2. **IA real opcional:** sin `MVP_IA_API_KEY` se usa el proveedor determinista
   de reglas; el contrato JSON y la contingencia están probados.
3. **Datos sintéticos:** no se usan expedientes reales ni información sensible.
4. **Acceso de demostración:** sin autenticación real, sin SSO y sin firma
   digital.
5. **Plantilla oficial pendiente:** el Excel/Word es usable, pero no reemplaza
   el formato institucional firmado.
6. **Feedback externo y ensayo presencial:** requieren una persona; su estado se
   declara en `06_checklist_entrega.md`. El video demo existe y usa narración
   sintética en español, declarada como tal.

## 13. Respaldos

| Respaldo | Ubicación |
|---|---|
| Código y datos | carpeta del proyecto `hito2-3` |
| Evidencia generada | `mvp/etapa6/evidencia/` |
| Base SQLite | `mvp/etapa6/evidencia/mvp_etapa6.db` |
| Presentación | `mvp/etapa6/entrega/` |

Para respaldar: copiar la carpeta `hito2-3` completa. Para restaurar: copiarla en
otro equipo con Python 3.11+ e instalar `mvp/requirements.txt`. El comando
`python -m mvp.scripts.ejecutar_etapa6` reconstruye toda la evidencia desde el
código, sin depender de la base previa.

## 14. Reproducción mínima en 4 comandos

```powershell
cd ruta\al\proyecto\hito2-3
python -m pip install -r mvp/requirements.txt
python -m mvp.scripts.ejecutar_etapa6
python -m streamlit run mvp/app.py
```
