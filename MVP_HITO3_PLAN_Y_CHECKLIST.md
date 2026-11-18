# Plan para convertir el prototipo en MVP — Hito 3
## Checklist de comprobación en 6 etapas con puertas de aprobación

| Campo | Valor |
|---|---|
| Proyecto | Asistente IA para revisión y evaluación de perfiles y expedientes técnicos de proyectos viales |
| Documento base | `Desarrollo_Asistente IA-Rev ET_Hito02_Plan.pdf` |
| Rúbrica aplicada | `hito3.pdf` — HITO 3 (50 puntos) |
| Artefacto evaluado | Prototipo navegable: https://react-expedivia.vercel.app/ |
| Versión del plan | 1.0 |
| Fecha de creación | 11/11/2026 |
| Estado general | `ETAPA 1 — COMPLETADA · ETAPA 2 — COMPLETADA · ETAPA 3 — COMPLETADA · ETAPA 4 — COMPLETADA · ETAPA 5 — COMPLETADA · ETAPA 6 — COMPLETADA · HITO 3 — CERRADO` |

---

## 0. Cómo se usa este documento

Este archivo es **vivo**: se actualiza al cierre de cada etapa.

### Protocolo obligatorio por etapa

1. **Al inicio de cada etapa:** el responsable (o el agente) debe **pedir aprobación explícita** antes de ejecutar tareas. Sin un “Aprobado” registrado, la etapa no comienza.
2. **Aprobación:** se anota en la sección *Registro de aprobaciones* (quién aprueba, fecha y alcance).
3. **Durante la etapa:** se marcan las casillas `[x]` solo cuando exista evidencia verificable (archivo, enlace, captura, log o prueba ejecutada).
4. **Al cierre de la etapa:** se verifican los *criterios de salida*, se agrega la evidencia, se actualiza el *Tablero de etapas* y se anota en la *Bitácora*.
5. **Transición:** se pide aprobación para la siguiente etapa. No se avanza por inercia.

### Regla de oro

> Una casilla solo se marca si otra persona puede reproducir la evidencia.
> “Está en el código” o “funciona en mi máquina” **no** es evidencia válida.

### Estados permitidos

| Estado | Significado |
|---|---|
| `PENDIENTE` | No iniciada o sin aprobación |
| `APROBADA` | Aprobada para inicio, aún sin ejecutar |
| `EN CURSO` | Tareas ejecutándose |
| `COMPLETADA` | Criterios de salida cumplidos y evidencia registrada |
| `OBSERVADA` | Cierre rechazado; requiere corrección |

---

## 1. Diagnóstico actual: prototipo vs. MVP

Lo revisado es un **prototipo navegable sin backend**. Evidencia recogida al probarlo:

| Aspecto | Estado actual | Evidencia | Brecha para el MVP |
|---|---|---|---|
| Carga de archivos | No existe | No hay `input[type=file]`; “Seleccionar carpeta” no abre selector | Implementar carga real de PDF/DOCX/XLSX |
| Backend / API | No existe | Solo 1 petición de red (documento HTML) | Implementar API y persistencia |
| Servicio de IA | No existe | Ninguna llamada a modelo | Integrar IA con salida JSON validada |
| Procesamiento | Simulado | Progreso fijo en 58%, ETA fija 02:14 | Procesamiento real por documento |
| Clasificación | Hardcodeada | “Corregir clasificación” cambia un texto fijo | Clasificación real + corrección humana |
| Evidencia | Decorativa | Texto y hash de ejemplo | Extracción y recuperación verificable |
| Validación humana | Simulada | Aceptar/Modificar/Descartar muestran aviso, pero el contador sigue 3/7 | Persistir decisión, motivo, responsable y fecha |
| Avance ponderado | Fijo | 62% y 3/7 no cambian | Cálculo real con ponderaciones |
| Exportación | No funciona | “Generar matriz/informe” no descarga ni genera archivo | Exportar `.xlsx` y `.docx` reales |
| Caché / integridad | Decorativos | Texto “cache hit” sin lógica | Implementar hash SHA-256 y comparación |
| Contingencia sin IA | Ausente | No hay flujo alterno | Implementar modo manual con reintento |
| Persistencia | Ausente | Al recargar vuelve al estado inicial | Base de datos o almacenamiento persistente |
| Roles / permisos | Ausentes | Usuario “SR” estático | Control de acceso mínimo |
| Manejo de errores | Ausente | No hay casos de PDF escaneado/protegido | Validaciones y mensajes trazables |

**Conclusión:** el prototipo sirve para demostrar UX, no para cumplir el criterio de **MVP funcional (16 pts)**. La rúbrica lo ubicaría en nivel 1–2 de ese criterio.

---

## 2. Meta frente a la rúbrica

| Criterio | Peso | Meta mínima (nivel 3) | Meta recomendada (nivel 4) | Qué exige |
|---|---:|---:|---:|---|
| MVP funcional | 16 | 12.8 | 16 | Flujo principal de extremo a extremo con datos reales o representativos |
| Calidad técnica y robustez | 10 | 8 | 10 | Lógica consistente, manejo de errores, cuidado de datos, reproducibilidad |
| Validación y resultados | 9 | 7.2 | 9 | Pruebas definidas, línea base, resultados interpretados y feedback |
| Valor AEC y posibilidad de escala | 8 | 6.4 | 8 | Impacto sustentado, adopción, limitaciones y ruta de escalamiento |
| Documentación, demo y sustentación | 7 | 5.6 | 7 | PPT clara, demo verificable, decisiones justificadas, evidencias trazables |
| **Total** | **50** | **40.0** | **50.0** | |

**Meta realista del equipo:** 40–44 / 50, priorizando llegar a nivel 4 en *MVP funcional*.

---

## 3. Qué hace falta para que sea MVP (requisitos P0)

Estos requisitos son **imprescindibles** para que el criterio de 16 puntos suba a nivel 3–4.

### 3.1 Flujo funcional de extremo a extremo
- [ ] **R1. Carga real** de una carpeta o archivos PDF/DOCX/XLSX.
- [ ] **R2. Validación real** de formato, legibilidad y texto recuperable; rechazo trazable de PDF escaneado, protegido o dañado.
- [ ] **R3. Clasificación documental** por tipo/componente, con confirmación o corrección humana.
- [ ] **R4. Extracción** de texto y tablas con ubicación (página, sección, hoja, celda).
- [ ] **R5. Hash SHA-256** por documento y caché documental.
- [ ] **R6. Base de conocimiento versionada** (checklist, TDR, normativa, ponderaciones).
- [ ] **R7. Recuperación de evidencia** por requisito, con fuente exacta.
- [ ] **R8. Análisis con IA** sobre contexto controlado y **salida JSON validada**.
- [ ] **R9. Cinco estados** y regla “No se encontró información” ≠ “No cumple”.
- [ ] **R10. Validación humana real** (aceptar / modificar / descartar) con persistencia.
- [ ] **R11. Avance ponderado** calculado con ponderaciones aprobadas.
- [ ] **R12. Exportación real** a Excel (`.xlsx`) y Word (`.docx`).
- [ ] **R13. Modo de contingencia sin IA** con evaluación manual y reintento.
- [ ] **R14. Persistencia** de revisiones, decisiones y auditoría.
- [ ] **R15. Demo reproducible** con un expediente real o anonimizado y datos semilla.

### 3.2 Calidad y robustez (P1)
- [ ] Manejo de errores y mensajes accionables.
- [ ] Registro de auditoría (usuario, fecha, expediente, versión, decisión).
- [ ] Credenciales fuera del código (variables de entorno).
- [ ] Validación de esquema JSON antes de mostrar resultados.
- [ ] Pruebas automatizadas mínimas (unitarias + E2E del flujo).
- [ ] README con instalación, ejecución y datos de prueba.
- [ ] Rendimiento aceptable para el caso de prueba (tiempo máximo acordado).

### 3.3 Validación y resultados (P2)
- [ ] 10–15 casos de prueba mapeados a los CA del Hito 2.
- [ ] Línea base: tiempo y esfuerzo de revisión manual vs. sistema.
- [ ] Métricas: requisitos procesados, evidencia correcta, aciertos/errores, tiempo ahorrado.
- [ ] Retroalimentación de un especialista vial (aunque sea simulada y documentada).
- [ ] Lectura crítica de hallazgos y limitaciones.

### 3.4 Documentación y demo (P3)
- [ ] PPT final de 10–15 diapositivas con las 9 secciones mínimas.
- [ ] Video continuo de 3–5 minutos sin edición que oculte pasos críticos.
- [ ] Ficha técnica / README con acceso, dependencias, datos y restricciones.
- [ ] Enlace o archivo del MVP con acceso operativo y de respaldo.
- [ ] Verificación de todos los enlaces sin solicitud de autorización.

### 3.5 Fuera de alcance (evitar scope creep)
- OCR de documentos escaneados.
- Análisis automatizado de planos complejos.
- Validación definitiva de cálculos o diseños de ingeniería.
- Consulta autónoma de normativa en Internet.
- Envío de correos a especialistas.
- Multiempresa, facturación o integración institucional.

---

## 4. Arquitectura mínima recomendada

### Opción A — Recomendada para el plazo: Streamlit + Python
```
ui/ (Streamlit)
  └── pantallas: inicio, carga, procesamiento, revisión, resultados, criterios
core/
  ├── ingesta.py        (PDF/DOCX/XLSX, hash SHA-256)
  ├── clasificacion.py  (tipo, componente, confianza)
  ├── extraccion.py     (texto/tablas + ubicación)
  ├── evidencia.py      (recuperación por requisito)
  ├── ia.py             (Gemini API + JSON schema + reintentos)
  ├── reglas.py         (5 estados, ponderaciones, integridad)
  ├── contingencia.py   (modo manual + cola de reintento)
  └── exportacion.py    (openpyxl, python-docx)
data/
  ├── conocimiento/     (checklist, TDR, normativa, ponderaciones versionadas)
  ├── expedientes/      (caso de prueba)
  └── app.db            (SQLite: revisiones, evidencias, decisiones, auditoría)
```

### Opción B — Conservar la UI React
- Mantener `react-expedivia` como front-end.
- Agregar **FastAPI** con los mismos módulos del núcleo Python.
- Mayor esfuerzo de integración; solo si el equipo domina frontend.

**Recomendación:** si el tiempo es limitado, usar **Opción A**. La rúbrica premia ejecución real, no acabado visual.

---

## 5. Las 6 etapas

> Recordatorio: **cada etapa comienza con una solicitud de aprobación**. No marcar tareas sin evidencia.

---

### ETAPA 1 — Preparación del caso y la base de conocimiento

**Estado:** `COMPLETADA (caso representativo)`
**Criterios de rúbrica impactados:** MVP funcional; Validación y resultados.
**CA/CP del Hito 2:** CA-05, CA-19; CP-18.

#### Puerta de aprobación (inicio)
- [x] Se solicitó aprobación explícita para iniciar la Etapa 1.
- [x] Aprobación registrada en la sección *Registro de aprobaciones*.
- **Aprobado por:** Usuario (instrucción “continua con la Etapa 1”)
- **Fecha:** 11/11/2026
- **Alcance aprobado:** Caso representativo `EXP-2024-089`; 6 documentos; 7 requisitos; pesos normalizados a 100%.

#### Tareas
- [x] Seleccionar **un expediente de prueba** real o anonimizado. → `EXP-2024-089` (sintético/representativo).
- [x] Definir la **especialidad prioritaria** (p. ej., pavimentos). → Pavimentos.
- [x] Inventariar documentos del expediente y sus versiones. → 6 documentos en `01_inventario_expediente.csv`.
- [x] Convertir checklist, TDR, normativa y ponderaciones en **base de conocimiento versionada**. → `KB-EXP2024-089-v1`.
- [x] Definir los **requisitos evaluables** y su peso (suma 100%). → 7 requisitos; 14+17+11+21+14+10+13 = 100.
- [x] Definir los **cinco estados** y la regla de ausencia de evidencia. → `04_estados_y_reglas.md`.
- [x] Acordar el **tiempo máximo** de procesamiento del caso. → 10 min (objetivo 5 min).
- [x] Definir datos semilla y política de datos sintéticos/anonimizados. → `05_datos_semilla.json` y sección 5 del alcance.

#### Criterios de salida (Definition of Done)
- [x] Existe un expediente de prueba accesible y documentado.
- [x] La base de conocimiento tiene versión, vigencia y responsable.
- [x] Los pesos suman exactamente 100%.
- [x] Cada requisito tiene criterio, evidencia esperada y norma/fuente.
- [x] Los cinco estados, las fórmulas y el redondeo están definidos.
- [x] El tiempo máximo y la política de datos están definidos.

#### Evidencia a registrar
- Ruta del expediente: `mvp/etapa1/01_inventario_expediente.csv`
- Versión del checklist / TDR / normativa: `KB-EXP2024-089-v1` — checklist v2, TDR v1, normativa MTC v5, ponderaciones v3.
- Archivo de ponderaciones: `mvp/etapa1/02_requisitos_ponderaciones.csv`
- Base de conocimiento: `mvp/etapa1/03_base_conocimiento/`
- Reglas y estados: `mvp/etapa1/04_estados_y_reglas.md`
- Datos semilla: `mvp/etapa1/05_datos_semilla.json`
- Acta de cierre: `mvp/etapa1/06_acta_cierre_etapa1.md`

#### Al completar
- [x] Verificar criterios de salida.
- [x] Registrar evidencia y fecha.
- [x] Actualizar el *Tablero de etapas*.
- [x] Anotar en la *Bitácora*.
- [x] **Solicitar aprobación para la Etapa 2.** → aprobada el 11/11/2026.

---

### ETAPA 2 — Procesamiento documental

**Estado:** `COMPLETADA`
**Criterios de rúbrica impactados:** MVP funcional; Calidad técnica.
**CA/CP del Hito 2:** CA-01, CA-02, CA-03, CA-04, CA-19, CA-23; CP-16, CP-17, CP-25.

#### Puerta de aprobación (inicio)
- [x] Se solicitó aprobación explícita para iniciar la Etapa 2.
- [x] Aprobación registrada.
- **Aprobado por:** Usuario (instrucción “confirmo el caso representativo, inicia la etapa 2”)
- **Fecha:** 11/11/2026
- **Alcance aprobado:** Caso representativo `EXP-2024-089`; procesamiento documental de PDF/DOCX/XLSX con validación, clasificación, extracción, hash SHA-256, caché y corrección humana.

#### Tareas
- [x] Implementar **carga real** de archivos (selector/drag & drop funcional). → Streamlit + CLI.
- [x] Validar formatos y límites (PDF con texto, DOCX, XLSX). → 25 MB; `core/pipeline.py`.
- [x] Detectar y rechazar PDF escaneado, protegido o dañado con mensaje trazable. → 4 motivos verificados.
- [x] Implementar **clasificación documental** (tipo, componente, confianza). → `core/classifier.py`.
- [x] Permitir **corrección humana** de la clasificación. → Persistida por SHA-256.
- [x] Implementar **extracción** de texto y tablas con ubicación. → página, párrafo, tabla, hoja/celda.
- [x] Calcular **hash SHA-256** por documento. → `core/hashing.py`.
- [x] Implementar **caché documental** por hash. → clave `sha256 + extractor_version`.
- [x] Persistir inventario, estado y metadatos. → SQLite + auditoría.

#### Criterios de salida
- [x] Se cargan los 6 archivos del caso sin errores. → 6/6 válidos.
- [x] Un PDF escaneado se rechaza con mensaje claro y registro. → `PDF_ESCANEADO`, 0 fragmentos.
- [x] La clasificación se puede corregir y queda registrada. → EETT 64 → 100, motivo y actor.
- [x] La extracción devuelve ubicación verificable por fragmento. → 61 fragmentos.
- [x] Dos cargas del mismo archivo producen el mismo hash y reutilizan caché. → 6/6; 298 → 47 ms (84.2%).

#### Evidencia a registrar
- Captura o log de carga: `mvp/etapa2/evidencia/01_reporte_ingesta_caso.md`
- Resultado de hash: `mvp/etapa2/evidencia/03_reporte_cache.md` y `08_inventario_procesado.csv`
- Prueba de rechazo de PDF inválido: `mvp/etapa2/evidencia/02_reporte_casos_borde.md`
- Corrección humana: `mvp/etapa2/evidencia/04_reporte_correccion.md`
- Métricas y auditoría: `mvp/etapa2/evidencia/05_metricas.json`, `06_auditoria.csv`
- Pruebas automatizadas: `mvp/etapa2/evidencia/07_resultados_pruebas.txt` (20 passed)
- Código y guía: `mvp/core/`, `mvp/app.py`, `mvp/cli.py`, `mvp/README.md`

#### Al completar
- [x] Verificar criterios de salida.
- [x] Registrar evidencia y fecha.
- [x] Actualizar el *Tablero de etapas*.
- [x] **Solicitar aprobación para la Etapa 3.** (aprobada el 11/11/2026)

---

### ETAPA 3 — Evidencia e inteligencia artificial

**Estado:** `COMPLETADA`
**Criterios de rúbrica impactados:** MVP funcional; Calidad técnica.
**CA/CP del Hito 2:** CA-06, CA-07, CA-20, CA-24; CP-19, CP-26.

#### Puerta de aprobación (inicio)
- [x] Se solicitó aprobación explícita para iniciar la Etapa 3.
- [x] Aprobación registrada.
- **Aprobado por:** Usuario (instrucción “continua con la etapa 3”)
- **Fecha:** 11/11/2026
- **Alcance aprobado:** Recuperación de evidencia por requisito, contrato JSON validado, integridad de fuente, integración de IA con contingencia y registro de consumo/errores.

#### Tareas
- [x] Implementar **recuperación de evidencia** por requisito.
- [x] Guardar fragmento, archivo, página/hoja/celda y hash de fuente.
- [x] Integrar **servicio de IA** con contexto mínimo (requisito, criterio, evidencia, fuente).
- [x] Definir y validar **contrato JSON** (`requisito_id`, `estado_propuesto`, `evidencia_encontrada`, `fuente`, `observación_preliminar`, `requiere_revision_especializada`, `motivo`).
- [x] Rechazar respuestas sin esquema o sin fuente.
- [x] Implementar **hash de integridad** y alerta de “fuente modificada”.
- [x] Implementar **modo de contingencia** si la IA no responde.
- [x] Registrar consumo, reintentos y errores.

#### Criterios de salida
- [x] Cada requisito del caso tiene evidencia con fuente verificable.
- [x] Una respuesta de IA inválida se rechaza o escala, nunca se muestra como conclusión.
- [x] Se detecta un archivo modificado después de la revisión.
- [x] Con la IA apagada, el flujo permite continuar manualmente sin perder avance.

#### Evidencia a registrar
- Ejemplo de JSON válido: `mvp/etapa3/evidencia/04_reporte_contrato.md`
- Ejemplo de JSON rechazado: `mvp/etapa3/evidencia/04_reporte_contrato.md` (`HASH_NO_COINCIDE`, `CITA_NO_ENCONTRADA`)
- Prueba de contingencia: `mvp/etapa3/evidencia/06_reporte_contingencia.md`
- Prueba de fuente modificada: `mvp/etapa3/evidencia/05_reporte_integridad.md`
- Evidencia por requisito: `mvp/etapa3/evidencia/02_reporte_evidencia.md`
- Propuestas y métricas: `mvp/etapa3/evidencia/03_reporte_analisis.md`, `07_metricas.json`
- Consumo y errores: `mvp/etapa3/evidencia/11_ejecuciones.csv`
- Código y guía: `mvp/core/evidence.py`, `ai_contract.py`, `ai_service.py`, `integrity.py`, `analysis.py`, `mvp/etapa3/README.md`

#### Al completar
- [x] Verificar criterios de salida.
- [x] Registrar evidencia y fecha.
- [x] Actualizar el *Tablero de etapas*.
- [x] **Solicitar aprobación para la Etapa 4.** (solicitud enviada; pendiente de respuesta)

---

### ETAPA 4 — Evaluación, trazabilidad y persistencia

**Estado:** `COMPLETADA`
**Criterios de rúbrica impactados:** MVP funcional; Calidad técnica; Validación.
**CA/CP del Hito 2:** CA-08, CA-09, CA-10, CA-11, CA-12, CA-18, CA-21; CP-20, CP-23.

#### Puerta de aprobación (inicio)
- [x] Se solicitó aprobación explícita para iniciar la Etapa 4.
- [x] Aprobación registrada.
- **Aprobado por:** Usuario (chat: “ejecuta la etapa 4”)  **Fecha:** 11/11/2026
- **Alcance aprobado:** cinco estados, ausencia de evidencia → “No se encontró información”, aceptar/modificar/descartar con motivo, fecha y responsable, propuesta original + decisión final, avance ponderado, persistencia, auditoría y reejecución sin duplicar hallazgos.

#### Tareas
- [x] Implementar los **cinco estados** del catálogo.
- [x] Aplicar la regla: ausencia de evidencia → “No se encontró información”.
- [x] Implementar **aceptar / modificar / descartar** con motivo, fecha y responsable.
- [x] Conservar propuesta original + decisión final.
- [x] Implementar **cálculo de avance ponderado** y redondeo definido.
- [x] Persistir todo en base de datos.
- [x] Implementar **auditoría** (usuario, fecha, expediente, versión, decisión).
- [x] Implementar **reejecución** sin duplicar hallazgos ni perder decisiones.

#### Criterios de salida
- [x] El contador de validados cambia realmente al decidir (0 → 4).
- [x] El avance se recalcula y coincide con la fórmula documentada (39.0%).
- [x] Al recargar la aplicación, las decisiones persisten.
- [x] El historial muestra propuesta, decisión, motivo, fecha y responsable.
- [x] Reejecutar no duplica hallazgos (7 → 7 propuestas, 0 duplicadas).

#### Evidencia a registrar
- Captura antes/después del avance: `mvp/etapa4/evidencia/01_reporte_antes.md`, `03_reporte_despues.md`, `06_metricas.json`
- Consulta o export de auditoría: `mvp/etapa4/evidencia/10_auditoria.csv` (`DECISION_REGISTRADA`)
- Prueba de persistencia tras recarga: `mvp/etapa4/evidencia/04_reporte_persistencia.md`
- Reejecución idempotente: `mvp/etapa4/evidencia/05_reporte_reejecucion.md`

#### Al completar
- [x] Verificar criterios de salida.
- [x] Registrar evidencia y fecha.
- [x] Actualizar el *Tablero de etapas*.
- [x] **Solicitar aprobación para la Etapa 5.** (solicitud enviada; aprobada el 12/11/2026)

---

### ETAPA 5 — Interfaz, exportación y contingencia visible

**Estado:** `COMPLETADA`
**Criterios de rúbrica impactados:** MVP funcional; Calidad técnica; Documentación/demo.
**CA/CP del Hito 2:** CA-13, CA-14, CA-15, CA-16, CA-17, CA-22, CA-25; CP-21, CP-22, CP-24, CP-27.

#### Puerta de aprobación (inicio)
- [x] Se solicitó aprobación explícita para iniciar la Etapa 5.
- [x] Aprobación registrada.
- **Aprobado por:** Usuario (chat: “inicia la etapa 5”)  **Fecha:** 12/11/2026
- **Alcance aprobado:** conexión de pantallas al flujo real, exportación `.xlsx` y `.docx`, modo de contingencia visible y operable, manejo de errores con avance conservado y reintento, control de acceso mínimo por rol y revisión de estados vacíos/accesibilidad.

#### Tareas
- [x] Conectar las pantallas existentes y la nueva de exportación al flujo real (sin datos fijos).
- [x] Implementar **exportación real** a Excel con resultados validados.
- [x] Implementar **exportación real** a Word con observaciones y fuentes.
- [x] Implementar **modo de contingencia** visible y operable.
- [x] Implementar **manejo de errores** con causa, avance conservado y reintento.
- [x] Implementar **control de acceso mínimo** por rol.
- [x] Revisar estados vacíos, mensajes y accesibilidad básica.
- [x] Validar tiempos de respuesta del caso.

#### Criterios de salida
- [x] Los archivos `.xlsx` y `.docx` se generan, abren y contienen datos reales.
- [x] La contingencia se activa y permite completar estados manualmente.
- [x] Un error de archivo no bloquea ni pierde avance.
- [x] Un usuario sin permiso no accede a expedientes no autorizados.

#### Evidencia a registrar
- Archivos exportados: `mvp/etapa5/evidencia/exportaciones/` (caso y estado vacío).
- Captura del modo contingencia: `mvp/app.py` (pestaña 4) y prueba automatizada.
- Prueba de permisos: `mvp/etapa5/evidencia/03_reporte_permisos.md`.

#### Al completar
- [x] Verificar criterios de salida.
- [x] Registrar evidencia y fecha.
- [x] Actualizar el *Tablero de etapas*.
- [x] **Solicitar aprobación para la Etapa 6.**

---

### ETAPA 6 — Integración, pruebas, métricas y entrega

**Estado:** `COMPLETADA`
**Criterios de rúbrica impactados:** Todos.
**CA/CP del Hito 2:** Todos los CA/CP; foco en CP-21 a CP-27.

#### Puerta de aprobación (inicio)
- [x] Se solicitó aprobación explícita para iniciar la Etapa 6.
- [x] Aprobación registrada.
- **Aprobado por:** Usuario (chat: “inicia la etapa 6”)  **Fecha:** 12/11/2026
- **Alcance aprobado:** flujo completo de extremo a extremo, al menos 10 casos de prueba mapeados a CA, registro de errores y correcciones, medición línea base vs. sistema, retroalimentación de especialista, PPT final, video demo, ficha técnica reproducible y ensayo de sustentación.

#### Tareas
- [x] Ejecutar el **flujo completo de extremo a extremo** con el expediente de prueba.
- [x] Ejecutar al menos **10 casos de prueba** mapeados a CA (16/16 PASA).
- [x] Registrar errores encontrados y correcciones aplicadas (7 incidencias).
- [x] Medir **línea base vs. sistema** (tiempo, requisitos, aciertos).
- [ ] Recoger **retroalimentación** de un especialista (requiere una persona).
- [x] Preparar **PPT final** (10–15 diapositivas, 9 secciones): 14 diapositivas.
- [x] Grabar **video demo** continuo (3–5 min): 3:03.
- [x] Redactar **ficha técnica / README** reproducible.
- [x] Verificar enlaces y accesos de respaldo.
- [x] Preparar el **guion del ensayo** de sustentación (10 min + preguntas).
- [ ] Ejecutar el **ensayo presencial cronometrado** (requiere el equipo).

#### Criterios de salida
- [x] El flujo completo se reproduce desde cero con instrucciones.
- [x] Existe evidencia de pruebas, métricas y revisión técnica.
- [x] PPT, video y ficha técnica están completos y accesibles.
- [x] Todos los enlaces y accesos de respaldo son locales y abren sin autorización.
- [x] El equipo puede explicar decisiones, limitaciones y próximos pasos (guion listo).
- [ ] Feedback firmado de un especialista (acción externa declarada).

#### Evidencia a registrar
- Enlace del MVP: `mvp/app.py` — `http://localhost:8501` con `MVP_DB_PATH=mvp/etapa6/evidencia/mvp_etapa6.db`
- Enlace del video: `mvp/etapa6/entrega/video_demo.mp4` (3:03, narración sintética)
- PPT final: `mvp/etapa6/entrega/PPT_Expedivia_Hito3.pptx` / `.pdf`
- Ficha técnica: `mvp/etapa6/FICHA_TECNICA.md`
- Registro de pruebas: `mvp/etapa6/evidencia/02_casos_prueba.md` (16/16)
- Acta de cierre: `mvp/etapa6/07_acta_cierre_etapa6.md`

#### Al completar
- [x] Verificar criterios de salida.
- [x] Registrar evidencia y fecha (12/11/2026).
- [x] Actualizar el *Tablero de etapas*.
- [x] **Cerrar el hito y solicitar revisión final.**

> **Pendientes externos:** el feedback firmado de un especialista y el ensayo
> presencial cronometrado requieren personas. Están declarados y no bloquean el
> cierre técnico; deben completarse antes de la sustentación.

---

## 6. Tablero de etapas

Se actualiza **solo al cierre** de cada etapa.

| # | Etapa | Aprobación de inicio | Estado | Fecha de cierre | Evidencia principal | Rúbrica impactada |
|---|---|---|---|---|---|---|
| 1 | Preparación del caso y base de conocimiento | ☑ | `COMPLETADA (caso representativo)` | 11/11/2026 | `mvp/etapa1/` | MVP / Validación |
| 2 | Procesamiento documental | ☑ | `COMPLETADA` | 11/11/2026 | `mvp/etapa2/` | MVP / Calidad |
| 3 | Evidencia e IA | ☑ | `COMPLETADA` | 11/11/2026 | `mvp/etapa3/` | MVP / Calidad |
| 4 | Evaluación, trazabilidad y persistencia | ☑ | `COMPLETADA` | 11/11/2026 | `mvp/etapa4/` | MVP / Validación |
| 5 | Interfaz, exportación y contingencia | ☑ | `COMPLETADA` | 12/11/2026 | `mvp/etapa5/` | MVP / Calidad |
| 6 | Integración, pruebas y entrega | ☑ | `COMPLETADA` | 12/11/2026 | `mvp/etapa6/` | Todos |

---

## 7. Registro de aprobaciones

| Etapa | Solicitada el | Aprobada por | Fecha | Alcance / observaciones |
|---|---|---|---|---|
| 1 | 11/11/2026 | Usuario (chat: “continua con la Etapa 1”) | 11/11/2026 | Caso representativo `EXP-2024-089`; 6 documentos; 7 requisitos; pesos normalizados a 100% |
| 2 | 11/11/2026 | Usuario (chat: “confirmo el caso representativo, inicia la etapa 2”) | 11/11/2026 | Caso `EXP-2024-089`; carga real, validación, clasificación, extracción con ubicación, SHA-256, caché y corrección humana |
| 3 | 11/11/2026 | Usuario (chat: “continua con la etapa 3”) | 11/11/2026 | Recuperación de evidencia por requisito, contrato JSON validado, integridad de fuente e IA con contingencia y registro de consumo/errores |
| 4 | 11/11/2026 | Usuario (chat: “ejecuta la etapa 4”) | 11/11/2026 | Cinco estados, decisión humana aceptar/modificar/descartar, propuesta original + decisión final, avance ponderado, persistencia, auditoría y reejecución idempotente |
| 5 | 12/11/2026 | Usuario (chat: “inicia la etapa 5”) | 12/11/2026 | Exportación real XLSX/DOCX, contingencia visible y operable, manejo de errores con avance conservado, control de acceso mínimo por rol y revisión de estados vacíos/accesibilidad |
| 6 | 12/11/2026 | Usuario (chat: “inicia la etapa 6”) | 12/11/2026 | Flujo completo de extremo a extremo, 10+ casos mapeados a CA, errores y correcciones, línea base vs. sistema, feedback, PPT, video demo, ficha técnica y ensayo |
| Cierre Hito 3 | 12/11/2026 | Usuario (chat: “da por cerrado el paquete”) | 12/11/2026 | Paquete de la Etapa 6 revisado y aceptado; se cierra el Hito 3 con los pendientes externos declarados |

---

## 8. Bitácora de actualización

| Fecha | Etapa | Cambio realizado | Responsable | Evidencia |
|---|---|---|---|---|
| 11/11/2026 | 1 | Se creó el caso, inventario, requisitos, base de conocimiento, estados/reglas y datos semilla | Agente | `mvp/etapa1/` |
| 11/11/2026 | 2 | Se implementó el procesamiento documental, el corpus, la app, el CLI y 20 pruebas; se generó la evidencia de ingesta, caché y corrección | Agente | `mvp/etapa2/` |
| 11/11/2026 | 3 | Se implementó la recuperación de evidencia, el contrato JSON, la integridad de fuente, la contingencia y la evaluación manual; se amplió el CLI y la app; se generaron 13 reportes y 37 pruebas | Agente | `mvp/etapa3/` |
| 11/11/2026 | 4 | Se implementaron los cinco estados, la decisión humana con historial inmutable, el avance ponderado, la auditoría y la reejecución idempotente por huella; se generaron 11 reportes y 14 pruebas nuevas (51 en total) | Agente | `mvp/etapa4/` |
| 12/11/2026 | 5 | Se implementaron la política de acceso por rol, la exportación real XLSX/DOCX, la contingencia visible, el manejo de errores con reintento y los estados vacíos; se generaron 7 reportes, informes del caso y 10 pruebas nuevas (61 en total) | Agente | `mvp/etapa5/` |
| 12/11/2026 | 6 | Se ejecutó el flujo completo, 16/16 casos mapeados a CA, 7 errores corregidos, métricas línea base vs. sistema, PPT de 14 diapositivas, video de 3:03, 10 capturas, ficha técnica y 12 pruebas nuevas (73 en total); feedback externo y ensayo presencial quedan declarados | Agente | `mvp/etapa6/` |

---

## 9. Checklist de entregables del Hito 3

| Entregable | Formato | Requisito de la rúbrica | Estado |
|---|---|---|---|
| Presentación final | PDF + editable | 10–15 diapositivas, 9 secciones | ☑ 14 diapositivas |
| MVP funcional | Enlace o archivo | Flujo operativo + instrucciones + datos | ☑ `mvp/app.py` |
| Video de respaldo | MP4 o enlace | 3–5 min continuos, sin ocultar pasos | ☑ 3:03 |
| Ficha técnica | PDF o README | Acceso, uso, dependencias, datos, restricciones | ☑ `FICHA_TECNICA.md` |
| Evidencias | Capturas/logs/métricas | Respaldan las afirmaciones | ☑ 10 capturas + reportes |
| Acceso de respaldo | Enlace alterno | Demo disponible si falla el principal | ☑ local + base + exportaciones |

### Secciones mínimas del PPT

- [x] 1. Problema y usuario
- [x] 2. Solución y valor AEC
- [x] 3. Arquitectura final
- [x] 4. Demostración
- [x] 5. Pruebas
- [x] 6. Resultados
- [x] 7. Evolución del proyecto
- [x] 8. Limitaciones
- [x] 9. Próximos pasos

---

## 10. Criterios de aceptación críticos a demostrar

| ID | Criterio | Etapa donde se demuestra | Estado |
|---|---|---|---|
| CA-01/02 | Carga y validación de formatos | 2 | ☑ |
| CA-03/04 | Clasificación y extracción con ubicación | 2 | ☑ |
| CA-05/19 | Criterios versionados y vigentes | 1 | ☑ |
| CA-06/07 | Evidencia y propuesta IA estructurada | 3 | ☑ |
| CA-08/09 | Cinco estados y ausencia ≠ incumplimiento | 4 | ☑ |
| CA-10/11 | Trazabilidad y validación humana | 4 | ☑ |
| CA-12 | Cálculo de avance ponderado | 4 | ☑ |
| CA-13/14 | Exportación Excel y Word | 5 | ☑ |
| CA-15/16 | Flujo completo y manejo de errores | 5–6 | ☑ |
| CA-17/18 | Seguridad y auditoría | 5 | ☑ |
| CA-20/24 | Calidad IA e integridad de evidencia | 3 | ☑ |
| CA-23 | Caché documental por hash | 2 | ☑ |
| CA-25 | Contingencia sin IA | 5 | ☑ |

---

## 11. Riesgos de no cumplir y mitigación

| Riesgo | Impacto en la rúbrica | Mitigación |
|---|---|---|
| Quedarse en el prototipo visual | MVP funcional nivel 1–2 | Priorizar backend y flujo real desde la Etapa 2 |
| Intentar todo el alcance | Baja calidad y entregas incompletas | Respetar el “fuera de alcance” de la sección 3.5 |
| Depender de la IA para todo | Bloqueo si falla el servicio | Modo de contingencia obligatorio (Etapa 3) |
| No medir resultados | Validación y resultados nivel 1 | Definir línea base y métricas en Etapa 1, medir en Etapa 6 |
| Documentación al final | Pérdida de puntos por demo/sustentación | Generar evidencias durante cada etapa |
| Datos reales sensibles | Riesgo de privacidad | Usar datos anonimizados o sintéticos |

---

## 12. Estado actual y cierre del Hito 3

Las **Etapas 1 a 6** están **COMPLETADAS**. Sus entregables están en `mvp/etapa1/`, `mvp/etapa2/`, `mvp/etapa3/`, `mvp/etapa4/`, `mvp/etapa5/` y `mvp/etapa6/`; las actas de cierre son `mvp/etapa1/06_acta_cierre_etapa1.md`, `mvp/etapa2/07_acta_cierre_etapa2.md`, `mvp/etapa3/07_acta_cierre_etapa3.md`, `mvp/etapa4/07_acta_cierre_etapa4.md`, `mvp/etapa5/07_acta_cierre_etapa5.md` y `mvp/etapa6/07_acta_cierre_etapa6.md`.

**Resultado final del caso `EXP-2024-089`:** 8/8 documentos válidos, 7/7 propuestas válidas, cobertura 100.0%, avance 39.0%, cumplimiento 88.6%, 4 decisiones vigentes y 6 registros de historial. Los 16 casos de prueba pasan y las 73 pruebas automatizadas también.

**Material de entrega:** PPT de 14 diapositivas y 9 secciones (`.pptx` y `.pdf`), video demo de 3:03, 10 capturas reales, ficha técnica, guion de video y guion de ensayo. Todo se regenera con los scripts de `mvp/scripts/`.

**Pendientes externos declarados:** feedback firmado de un especialista y ensayo presencial cronometrado. Requieren personas; no se declaran como recibidos y deben completarse antes de la sustentación.

> **Cierre:** el usuario revisó el paquete de la Etapa 6 y confirmó en chat:
> “da por cerrado el paquete”. El **Hito 3 queda cerrado**; los pendientes
> externos siguen declarados para la sustentación.
