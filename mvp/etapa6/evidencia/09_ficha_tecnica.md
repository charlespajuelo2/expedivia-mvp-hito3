# Ficha técnica — Expedivia MVP

## 1. Acceso

```powershell
cd ruta\al\proyecto\hito2-3
python -m pip install -r mvp/requirements.txt
streamlit run mvp/app.py
```

Abrir `http://localhost:8501`.

## 2. Datos de demostración

- Caso: `EXP-2024-089` — Carretera Central Tramo 2 · Km 42–78.
- Especialidad: Pavimentos.
- Datos sintéticos/representativos.
- Corpus: `mvp/etapa6/muestras/caso/` (8 documentos).
- Base: `mvp/etapa6/evidencia/mvp_etapa6.db`.

## 3. Usuarios

| Usuario | Rol | Expediente |
|---|---|---|
| Lucía Ramos | especialista | `EXP-2024-089` |
| Carlos Méndez | lector | `EXP-2024-089` |
| Admin MVP | administrador | `*` |

## 4. Flujo reproducible

```powershell
python -m mvp.scripts.ejecutar_etapa6
python -m pytest mvp/tests -q
```

## 5. Artefactos

- `mvp/etapa6/evidencia/` — reportes, métricas, exportaciones.
- `mvp/etapa6/entrega/PPT_Expedivia_Hito3.pptx` — presentación editable.
- `mvp/etapa6/entrega/PPT_Expedivia_Hito3.pdf` — versión PDF.
- `mvp/etapa6/evidencia/07_guion_video.md` — guion del video.
- `mvp/etapa6/README.md` — guía de la etapa.

## 6. Dependencias

Python 3.11+, `pypdf`, `pdfplumber`, `python-docx`, `openpyxl`, `streamlit`,
`reportlab`, `xlsxwriter`, `pytest`, `python-pptx` (solo para generar el PPT).

## 7. Restricciones

- No hay OCR: PDF escaneado se rechaza.
- La IA real requiere `MVP_IA_API_KEY`; por defecto se usa el proveedor de reglas.
- La política de acceso es de demostración.
- Los datos son sintéticos.
- El feedback de especialista y el video final son acciones del equipo.
