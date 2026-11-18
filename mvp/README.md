# MVP — Asistente IA para revisión de expedientes técnicos viales

**Estado actual:** Hito 3 cerrado — Etapa 6 completada: flujo de extremo a extremo, 16 casos, métricas, PPT, video demo y ficha técnica.
**Caso de prueba:** `EXP-2024-089` — Carretera Central Tramo 2 · Km 42–78 (Pavimentos).
**Datos:** sintéticos/representativos.

---

## 1. Qué funciona hoy

| Capacidad | Estado | Dónde |
|---|---|---|
| Carga real de PDF, DOCX y XLSX | ✅ | `mvp/app.py`, `mvp/cli.py` |
| Validación de formato, tamaño, legibilidad | ✅ | `core/pipeline.py` |
| Rechazo trazable de PDF escaneado, protegido o dañado | ✅ | `core/extractors.py` |
| Extracción de texto y tablas con ubicación | ✅ | `core/extractors.py` |
| Hash SHA-256 por documento | ✅ | `core/hashing.py` |
| Caché de extracción por hash | ✅ | `core/pipeline.py` |
| Clasificación documental con confianza explicable | ✅ | `core/classifier.py` |
| Corrección humana persistente | ✅ | `core/pipeline.py` |
| Recuperación de evidencia por requisito | ✅ | `core/evidence.py` |
| Contrato JSON estricto y validación de fuente/cita/hash | ✅ | `core/ai_contract.py` |
| Proveedor de reglas y cliente OpenAI compatible | ✅ | `core/ai_service.py` |
| Integridad de fuente y propagación de alertas | ✅ | `core/integrity.py` |
| Contingencia y evaluación manual | ✅ | `core/analysis.py` |
| Decisión humana aceptar / modificar / descartar | ✅ | `core/evaluation.py` |
| Historial inmutable y propuesta original conservada | ✅ | `core/db.py`, `core/evaluation.py` |
| Avance ponderado con redondeo definido | ✅ | `core/evaluation.py`, `core/analysis.py` |
| Reejecución idempotente por huella | ✅ | `core/analysis.py` |
| Persistencia SQLite + auditoría | ✅ | `core/db.py` |
| Interfaz Streamlit | ✅ | `mvp/app.py` |
| Control de acceso por rol y expediente asignado | ✅ | `core/access.py`, `mvp/app.py` |
| Exportación real Excel (7 hojas) y Word (5 secciones) | ✅ | `core/exporters.py` |
| Contingencia visible y resoluble manualmente | ✅ | `mvp/app.py`, `core/analysis.py` |
| Errores con causa, avance conservado y reintento | ✅ | `mvp/app.py` |
| Flujo de extremo a extremo reproducible | ✅ | `scripts/ejecutar_etapa6.py` |
| 16 casos de prueba mapeados a CA | ✅ | `etapa6/evidencia/02_casos_prueba.md` |
| PPT editable/PDF y video demo | ✅ | `etapa6/entrega/` |

---

## 2. Instalación

```powershell
python -m pip install -r mvp/requirements.txt
```

Requisitos: Python 3.11 o superior.

Para regenerar capturas y video (opcional):

```powershell
python -m pip install -r mvp/requirements-media.txt
python -m playwright install chromium
```

---

## 3. Ejecución

### 3.1 Interfaz

```powershell
streamlit run mvp/app.py
```

La app permite:

1. Registrar el expediente.
2. Cargar archivos o procesar una carpeta local.
3. Ver el inventario, la clasificación y las advertencias.
4. Corregir la clasificación con motivo y responsable.
5. Consultar los fragmentos con su ubicación exacta.
6. Recuperar evidencia y analizar requisitos con contrato JSON.
7. Verificar la integridad de las fuentes y registrar evaluación manual.
8. Decidir aceptar / modificar / descartar con motivo y responsable.
9. Consultar el historial de decisiones y el avance ponderado.
10. Reejecutar el análisis sin duplicar hallazgos ni perder decisiones.
11. Resolver contingencias con evaluación manual motivada.
12. Exportar el informe real a Excel y Word desde la base.
13. Cambiar de usuario para demostrar los permisos por rol.
14. Revisar métricas, propuestas y bitácora de auditoría.

> La sesión inicia con **Lucía Ramos** (especialista). Al elegir **Carlos Méndez**
> (lector) se deshabilitan carga, decisión y exportación con un mensaje que
> explica el motivo.

### 3.2 CLI

```powershell
python -m mvp.cli init
python -m mvp.cli seed
python -m mvp.cli ingest --expediente EXP-2024-089 --carpeta mvp/etapa3/muestras/caso
python -m mvp.cli list --expediente EXP-2024-089
python -m mvp.cli extract --documento 1
python -m mvp.cli correct --documento 2 --tipo "Especificaciones técnicas" --componente EETT --motivo "Revisión del especialista"
python -m mvp.cli evidence --expediente EXP-2024-089
python -m mvp.cli analyze --expediente EXP-2024-089 --proveedor reglas
python -m mvp.cli integrity --expediente EXP-2024-089
python -m mvp.cli proposals --expediente EXP-2024-089
python -m mvp.cli eventos --expediente EXP-2024-089
python -m mvp.cli manual --expediente EXP-2024-089 --requisito RQ-02 --estado "Requiere revisión especializada" --motivo "Falta CV" --actor "Lucía Ramos"
python -m mvp.cli decide --expediente EXP-2024-089 --requisito RQ-04 --decision aceptar --motivo "Fuente verificada" --actor "Lucía Ramos"
python -m mvp.cli decide --expediente EXP-2024-089 --requisito RQ-06 --decision modificar --estado-final "Cumple parcialmente" --motivo "El cronograma no cubre todo el plazo" --actor "Lucía Ramos"
python -m mvp.cli decide --expediente EXP-2024-089 --requisito RQ-05 --decision descartar --motivo "Los planos no permiten verificar los metrados" --actor "Lucía Ramos"
python -m mvp.cli history --expediente EXP-2024-089
python -m mvp.cli progress --expediente EXP-2024-089
python -m mvp.cli metrics --expediente EXP-2024-089
python -m mvp.cli audit
python -m mvp.cli access
python -m mvp.cli access --usuario "Carlos Méndez" --accion exportar --expediente EXP-2024-089
python -m mvp.cli export --expediente EXP-2024-089 --usuario "Lucía Ramos" --salida mvp/etapa6/evidencia/exportaciones
```

Sin `--salida`, los informes se escriben en una carpeta `exportaciones/` junto a
la base de datos activa.

Se puede usar otra base con `--bd ruta\alternativa.db` antes del subcomando.

### 3.3 Reproducir toda la evidencia

```powershell
python -m mvp.scripts.ejecutar_etapa2
python -m mvp.scripts.ejecutar_etapa3
python -m mvp.scripts.ejecutar_etapa4
python -m mvp.scripts.ejecutar_etapa5
python -m mvp.scripts.ejecutar_etapa6
```

La primera genera el corpus y los reportes de la Etapa 2; la segunda usa
`mvp/etapa3/muestras/` y escribe en `mvp/etapa3/evidencia/` (8 documentos, sin
alterar el corpus cerrado de la Etapa 2). La tercera usa su propio corpus y su
propia base en `mvp/etapa4/`, y demuestra el avance antes/después de decidir,
la persistencia y la reejecución idempotente. La cuarta valida la exportación
real, la política de acceso, el error con reintento, el estado vacío y los
tiempos en `mvp/etapa5/evidencia/`. La quinta ejecuta el flujo completo de la
Etapa 6, los 16 casos y genera los reportes, exportaciones y métricas en
`mvp/etapa6/evidencia/`.

### 3.4 Pruebas

```powershell
python -m mvp.scripts.ejecutar_etapa6
python -m pytest mvp/tests -q
```

Resultado esperado: **73 passed**. Las pruebas de la Etapa 6 leen la evidencia
generada por `ejecutar_etapa6`, así que ese comando debe ejecutarse primero.

---

## 4. Flujo de procesamiento

```
archivo
  → validar ruta, extensión, tamaño y legibilidad
  → SHA-256
  → ¿existe en caché (hash + versión del extractor)?
        sí → reutilizar extracción
        no → extraer y guardar en caché
  → clasificar (nombre + texto)
  → ¿existe corrección humana para ese hash?
        sí → aplicar corrección
  → persistir documento, fragmentos y auditoría
```

Los documentos rechazados se guardan con su motivo y **no generan fragmentos
ni conclusiones**.

```
requisito
  → recuperar fragmentos de documentos válidos y clasificados
  → puntuar términos + bonus por tipo documental
  → verificar integridad de cada fuente
        fuente modificada o ausente → escalar, sin conclusión automática
  → enviar contexto mínimo al proveedor de IA
  → validar contrato JSON (8 campos, fuente, hash y cita)
        inválido → reintentar
        agotado o proveedor caído → contingencia + evaluación manual
  → persistir propuesta, ejecución (consumo/errores) y auditoría
  → decisión humana: aceptar / modificar / descartar (motivo, actor, fecha)
  → estado efectivo y avance ponderado
```

La reejecución del análisis calcula una **huella canónica** de la propuesta. Si
ya existe una propuesta con la misma huella, se reutiliza: no se duplican
hallazgos y las decisiones que la referencian se conservan.

---

## 5. Estructura

```
mvp/
├── app.py                    # Interfaz Streamlit
├── cli.py                    # Línea de comandos
├── core/
│   ├── config.py             # Rutas, límites, versiones, parámetros IA
│   ├── hashing.py            # SHA-256
│   ├── db.py                 # Esquema y conexión SQLite
│   ├── extractors.py         # PDF / DOCX / XLSX con ubicación
│   ├── classifier.py         # Clasificación y confianza
│   ├── pipeline.py           # Ingesta, caché, corrección, métricas
│   ├── evidence.py           # Perfiles, puntuación y recuperación
│   ├── ai_contract.py        # Contrato JSON y validación de fuente
│   ├── ai_service.py         # Proveedores de IA y reintentos
│   ├── integrity.py          # Verificación de hashes y propagación
│   ├── evaluation.py         # Decisión humana, historial y avance ponderado
│   ├── access.py             # Roles, permisos y expedientes asignados
│   ├── exporters.py          # Informes reales XLSX y DOCX desde SQLite
│   └── analysis.py           # Orquestación, contingencia y métricas
├── scripts/
│   ├── generar_muestras.py   # Corpus del caso + casos borde (Etapa 2)
│   ├── generar_muestras_etapa3.py # Corpus ampliado (8 documentos)
│   ├── ejecutar_etapa2.py    # Evidencia reproducible de Etapa 2
│   ├── ejecutar_etapa3.py    # Evidencia reproducible de Etapa 3
│   ├── ejecutar_etapa4.py    # Evidencia reproducible de Etapa 4
│   ├── ejecutar_etapa5.py    # Evidencia reproducible de Etapa 5
│   ├── ejecutar_etapa6.py    # Flujo completo, 16 casos y entrega
│   ├── capturar_pantallas_etapa6.py # Capturas reales de la app
│   ├── generar_ppt_etapa6.py # PPT de 14 diapositivas
│   └── grabar_video_etapa6.py # Video demo narrado
├── tests/                    # 73 pruebas automatizadas
├── etapa1/                   # Caso y base de conocimiento
├── etapa2/                   # Evidencia y cierre de la Etapa 2
├── etapa3/                   # Perfiles, corpus, evidencia y cierre
├── etapa4/                   # Corpus, base SQLite, reportes y cierre
├── etapa5/                   # Usuarios, corpus, informes, reportes y cierre
├── etapa6/                   # Integración, entrega, PPT, video y ficha
└── data/                     # Generado en ejecución (BD y uploads)
```

---

## 6. Base de datos

| Tabla | Contenido |
|---|---|
| `expedientes` | Caso en revisión |
| `documentos` | Inventario procesado, hash, estado y clasificación |
| `fragmentos` | Texto extraído con ubicación verificable |
| `cache_extraccion` | Extracción reutilizable por SHA-256 |
| `correcciones_clasificacion` | Corrección humana por SHA-256 |
| `evidencias` | Fragmentos recuperados por requisito, con fuente e integridad |
| `propuestas_ia` | Respuestas validadas o rechazadas, con errores, integridad y huella |
| `decisiones` | Historial de aceptar / modificar / descartar con propuesta original |
| `ejecuciones_ia` | Consumo, intentos, duración y estado de cada llamada |
| `evaluaciones_manuales` | Decisión del especialista cuando la IA no concluye |
| `integridad_eventos` | Historial de verificación de hashes |
| `auditoria` | Bitácora de acciones |

La caché usa la clave `sha256 + extractor_version`. Las correcciones se guardan
aparte y también por `sha256`, por lo que **sobreviven** a una recarga o a un
acierto de caché.

---

## 7. Reglas de la etapa

- **Umbral de confianza:** 70. Por debajo, el documento queda *Sin clasificar* y
  requiere corrección humana.
- **Ausencia de evidencia:** un documento rechazado, no clasificado o ausente
  **no** se convierte en “No cumple”. El estado es “No se encontró información”
  o “Requiere revisión especializada”.
- **Integridad:** cada documento y cada corrección quedan vinculados a su hash.
  Si la fuente cambia, la conclusión anterior deja de mostrarse como válida.
- **Contrato:** una respuesta de IA solo se acepta si cumple los 8 campos y su
  fuente, hash y cita coinciden con la evidencia recuperada.
- **Decisión humana:** aceptar conserva el estado propuesto; modificar exige un
  estado final distinto; descartar deja el requisito en “No se encontró
  información”. Las tres exigen motivo y responsable.
- **Historial:** cada decisión es una fila nueva. La propuesta original no se
  sobrescribe y la decisión vigente es la última del requisito.
- **Avance ponderado:** `Σ(peso × factor_avance) / peso_total × 100`, con
  `ROUND_HALF_UP` a 1 decimal. Solo los requisitos decididos aportan; descartar
  aporta 0.
- **Idempotencia:** una propuesta con la misma huella no se inserta dos veces.
- **Acceso:** cada usuario tiene un rol y expedientes asignados; sin permiso o
  sin asignación, la acción se bloquea con causa. El administrador usa `*`.
- **Errores:** un archivo inválido se rechaza con causa sin abortar el lote; el
  avance, las decisiones y la caché por SHA-256 se conservan para el reintento.
- **Exportación:** Excel y Word se construyen desde SQLite y se verifican
  reabriendo el archivo; un rol sin permiso `exportar` no genera descargas.
- **Auditoría:** toda carga, rechazo, acierto de caché, corrección, propuesta,
  decisión y verificación se registra con actor y fecha.

### Códigos de rechazo

| Código | Significado |
|---|---|
| `FORMATO_NO_SOPORTADO` | No es PDF, DOCX ni XLSX |
| `ARCHIVO_VACIO` | 0 bytes |
| `ARCHIVO_NO_ENCONTRADO` | Ruta inexistente |
| `ARCHIVO_INVALIDO` | La ruta no es un archivo |
| `ARCHIVO_ILEGIBLE` | Error de lectura |
| `TAMANO_EXCEDIDO` | Supera 25 MB |
| `PDF_PROTEGIDO` | Requiere contraseña |
| `PDF_ESCANEADO` | Sin capa de texto |
| `ARCHIVO_DANADO` | PDF/DOCX/XLSX corrupto |
| `SIN_TEXTO_RECUPERABLE` | DOCX/XLSX sin contenido |

---

## 8. Limitaciones conocidas

- No se implementa OCR: un PDF escaneado se rechaza y se informa.
- La clasificación es determinista (reglas), no semántica; se refuerza con la
  corrección humana.
- DOCX no tiene paginación real: se usa número de párrafo y sección.
- XLSX se procesa hasta 2 000 filas por hoja.
- El proveedor por defecto (`reglas`) es determinista y no sustituye el juicio
  de ingeniería; los requisitos que lo exigen escalan a revisión.
- El cliente OpenAI compatible requiere `MVP_IA_API_KEY` y no se ejecutó contra
  un servicio externo durante la validación (sin credenciales disponibles).
- La consolidación de los 23 requisitos oficiales sigue pendiente; el caso usa
  los 7 requisitos representativos con pesos que suman 100%.
- La política de acceso es un JSON de demostración (`mvp/etapa5/config/usuarios.json`);
  no incluye autenticación corporativa, sesiones firmadas ni directorio real.
- El informe exportado usa datos sintéticos y no sustituye el documento oficial
  firmado.
- El video demo usa narración sintetizada (voz es-ES) y capturas reales de la
  app; no es una locución humana.
- El feedback firmado de un especialista y el ensayo presencial cronometrado
  quedan como acciones del equipo antes de la sustentación.

---

## 9. Cierre del Hito 3

La Etapa 6 deja el MVP integrado y reproducible:

- flujo completo con un comando y base propia;
- 16 casos de prueba mapeados a criterios de aceptación (16/16 PASA);
- métricas de línea base vs. sistema, con supuestos explícitos;
- registro de errores y correcciones;
- PPT de 14 diapositivas y 9 secciones, en PPTX y PDF;
- video demo de 3:03 con narración en español;
- ficha técnica y README reproducibles.

Pendientes externos declarados: feedback firmado de un especialista, ensayo
presencial y validación de la plantilla oficial.
