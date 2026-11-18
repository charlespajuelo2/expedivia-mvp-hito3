# Expedivia — Asistente IA para revisión de expedientes técnicos viales

MVP del **Hito 3** del proyecto: un asistente que apoya la revisión de
expedientes técnicos viales. Ingesta documentos PDF, DOCX y XLSX, recupera
evidencia por requisito, propone un estado con fuente y cita, y exige una
decisión humana trazable antes de calcular el avance.

**Caso de demostración:** `EXP-2024-089` — Carretera Central Tramo 2 · Km 42–78
(Pavimentos, datos sintéticos representativos).

## Qué incluye

- Ingesta validada, hash SHA-256 y caché de extracción.
- Clasificación documental explicable y corrección humana persistente.
- Recuperación de evidencia y contrato JSON estricto para la IA.
- Decisión humana aceptar / modificar / descartar con historial inmutable.
- Avance y cumplimiento ponderados con redondeo definido.
- Control de acceso por rol y expediente asignado.
- Exportación real a Excel (7 hojas) y Word (5 secciones) desde SQLite.
- 16 casos de prueba de extremo a extremo y evidencia reproducible.

## Inicio rápido

```powershell
python -m pip install -r mvp/requirements.txt
python -m mvp.scripts.ejecutar_etapa6
python -m streamlit run mvp/app.py
```

Pruebas:

```powershell
python -m pytest mvp/tests -q
```

Resultado esperado: **73 passed** (las pruebas de la Etapa 6 leen la evidencia
generada por `ejecutar_etapa6`).

## Documentación

| Documento | Contenido |
|---|---|
| [`mvp/README.md`](mvp/README.md) | Guía completa: uso, CLI, base de datos y reglas |
| [`mvp/etapa6/FICHA_TECNICA.md`](mvp/etapa6/FICHA_TECNICA.md) | Ficha técnica del MVP y resultados del caso |
| [`mvp/etapa6/README.md`](mvp/etapa6/README.md) | Reproducción de la entrega y material audiovisual |
| [`MVP_HITO3_PLAN_Y_CHECKLIST.md`](MVP_HITO3_PLAN_Y_CHECKLIST.md) | Plan y estado por etapa |

## Demo en Streamlit Community Cloud

**App publicada:** <https://expedivia-mvp.streamlit.app>

| Ajuste | Valor |
|---|---|
| Repositorio | `charlespajuelo2/expedivia-mvp-hito3` |
| Rama | `main` |
| Archivo principal | `mvp/app.py` |
| Python | 3.12 |

Pasos:

1. Entrar a <https://share.streamlit.io> con la cuenta de GitHub.
2. **Create app** → **Yup, I have an app**.
3. Completar repositorio, rama y archivo principal con los valores de la tabla.
4. En **Advanced settings**, elegir Python 3.12.
5. **Deploy**.

La app arranca con el caso `EXP-2024-089` precargado desde
`mvp/etapa6/evidencia/mvp_etapa6.db`: si la base de trabajo no existe, se copia
una sola vez. El almacenamiento de Community Cloud es efímero, así que los
cambios que hagan los visitantes se pierden al reiniciar la app.

## Estructura

```
mvp/
├── app.py          # Interfaz Streamlit
├── cli.py          # Línea de comandos
├── core/           # Ingesta, evidencia, IA, evaluación, acceso, exportación
├── scripts/        # Flujos reproducibles de cada etapa
├── tests/          # 73 pruebas automatizadas
└── etapa1..etapa6/ # Documentación, corpus y evidencia por etapa
```

## Limitaciones declaradas

- Sin OCR: un PDF escaneado se rechaza y se informa.
- El proveedor por defecto es determinista (reglas); la IA real es opcional.
- Los datos del caso son sintéticos/representativos.
- La política de acceso es una demostración, sin autenticación corporativa.
- El informe exportado no reemplaza la plantilla oficial firmada.

## Requisitos

Python 3.11 o superior. Dependencias en
[`mvp/requirements.txt`](mvp/requirements.txt); las capturas y el video usan
[`mvp/requirements-media.txt`](mvp/requirements-media.txt) (opcional).
