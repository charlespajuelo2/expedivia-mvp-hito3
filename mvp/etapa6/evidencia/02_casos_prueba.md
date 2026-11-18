# Evidencia 02 — Casos de prueba mapeados a criterios de aceptación

Se ejecutaron **16 casos** sobre el flujo real. Resultado:
**16/16 PASA**.

| ID | CA | Caso | Esperado | Obtenido | Estado | ms |
|---|---|---|---|---|---|---|
| CP-01 | CA-01/02 | Carga de 8 documentos válidos | 8/8 válidos con SHA-256 | 8/8 documentos válidos con SHA-256 | PASA | 0.6 |
| CP-02 | CA-02 | Rechazo de PDF corrupto | ARCHIVO_DANADO sin evidencia | motivo=ARCHIVO_DANADO; válidos 0→0 | PASA | 12.6 |
| CP-03 | CA-03/04 | Clasificación y corrección persistente | EETT corregido y persistido | Especificaciones técnicas / EETT (correccion_humana) | PASA | 0.6 |
| CP-04 | CA-04 | Extracción con ubicación verificable | PDF, DOCX y XLSX con ubicación | {"XLSX": "Hoja:Resumen!A1:A1", "DOCX": "párr. 1", "PDF": "p. 1"} | PASA | 5.4 |
| CP-05 | CA-06 | Evidencia con fuente, cita y hash | RQ-04 con evidencia completa | 5 evidencias; primera=Presupuesto.xlsx | PASA | 0.5 |
| CP-06 | CA-07 | Contrato JSON y propuesta válida | 7/7 propuestas válidas | 7 propuestas válidas; RQ-04 con fuente y cita | PASA | 1.1 |
| CP-07 | CA-08/09 | Ausencia de evidencia no es incumplimiento | sin información y no_cumple=0 | estado=No se encontró información; sin_informacion=1; no_cumple=0 | PASA | 50.1 |
| CP-08 | CA-10/11 | Historial humano inmutable | 6 registros y 4 vigentes | 6 registros; RQ-04=3; vigentes=4 | PASA | 0.6 |
| CP-09 | CA-12 | Avance ponderado verificable | 39.0% y 88.6% | avance=39.0%; peso decidido=58.0%; cumplimiento=88.6% | PASA | 0.0 |
| CP-10 | CA-13 | Exportación Excel real | 7 hojas y filas reales | 7 hojas; requisitos=7; decisiones=6 | PASA | 18.1 |
| CP-11 | CA-14 | Exportación Word real | 5 secciones y fuentes | 5 secciones; 3 tablas | PASA | 31.1 |
| CP-12 | CA-16 | Error y reintento sin pérdida | avance y decisiones conservados | válidos 0→1; avance 39.0%→39.0% | PASA | 74.4 |
| CP-13 | CA-17 | Control de acceso por rol | 3 denegaciones con causa | 3 denegaciones con causa | PASA | 0.2 |
| CP-14 | CA-25 | Contingencia y evaluación manual | contingencia resuelta | contingencia visible=True; origen final=manual | PASA | 117.8 |
| CP-15 | CA-23 | Caché documental por hash | cache_hit sin duplicar | cache_hit=True; documentos 8→8 | PASA | 16.8 |
| CP-16 | CA-20/24 | Integridad de fuente bloquea decisión | fuente modificada detectada | requiere_atencion=1; decisión bloqueada=True | PASA | 114.9 |

## Detalle de evidencia

- **CP-01 · Carga de 8 documentos válidos** (CA-01/02): Se cargaron los 8 documentos del corpus y todos tienen hash.
- **CP-02 · Rechazo de PDF corrupto** (CA-02): El rechazo no agrega documentos válidos ni evidencia.
- **CP-03 · Clasificación y corrección persistente** (CA-03/04): La corrección humana persiste vinculada al hash del documento.
- **CP-04 · Extracción con ubicación verificable** (CA-04): Cada formato conserva una ubicación verificable.
- **CP-05 · Evidencia con fuente, cita y hash** (CA-06): La evidencia incluye archivo, ubicación, cita y hash.
- **CP-06 · Contrato JSON y propuesta válida** (CA-07): El contrato JSON exige y conserva los 8 campos.
- **CP-07 · Ausencia de evidencia no es incumplimiento** (CA-08/09): La ausencia de evidencia no se convierte en incumplimiento.
- **CP-08 · Historial humano inmutable** (CA-10/11): El historial es acumulativo y solo una decisión por requisito es vigente.
- **CP-09 · Avance ponderado verificable** (CA-12): Fórmula: Σ(peso × factor_avance) / peso_total × 100, ROUND_HALF_UP 1 decimal
- **CP-10 · Exportación Excel real** (CA-13): Archivo: informe_EXP-2024-089.xlsx
- **CP-11 · Exportación Word real** (CA-14): Archivo: informe_EXP-2024-089.docx
- **CP-12 · Error y reintento sin pérdida** (CA-16): El reintento agrega el documento sin perder decisiones ni avance.
- **CP-13 · Control de acceso por rol** (CA-17): Lector sin decisión/exportación; especialista limitado a su expediente.
- **CP-14 · Contingencia y evaluación manual** (CA-25): La evaluación manual resuelve la contingencia sin perder trazabilidad.
- **CP-15 · Caché documental por hash** (CA-23): La extracción se reutiliza por SHA-256 sin duplicar el inventario.
- **CP-16 · Integridad de fuente bloquea decisión** (CA-20/24): Una fuente modificada invalida la propuesta y bloquea aceptar.

## Criterio de salida cubierto

- [x] Hay más de 10 casos, cada uno mapeado a CA.
- [x] Los casos usan la base y el corpus reales, no mocks.
- [x] Un fallo de caso no aborta la suite; queda registrado.
- [x] Se cubren carga, evidencia, IA, estados, decisiones, exportación,
      seguridad, contingencia, caché e integridad.
