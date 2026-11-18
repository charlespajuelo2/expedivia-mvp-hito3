# Acta de cierre — Etapa 1

**Proyecto:** Asistente IA para revisión y evaluación de perfiles y expedientes técnicos de proyectos viales  
**Etapa:** 1 — Preparación del caso y la base de conocimiento  
**Fecha:** 11/11/2026  
**Estado:** `COMPLETADA (caso representativo)`

---

## 1. Aprobación de inicio

| Campo | Valor |
|---|---|
| Solicitada | 11/11/2026 |
| Aprobada por | Usuario |
| Medio | Instrucción en chat: “continua con la Etapa 1” |
| Fecha | 11/11/2026 |
| Alcance aprobado | Caso representativo `EXP-2024-089`; 6 documentos; 7 requisitos; pesos normalizados a 100% |

---

## 2. Tareas ejecutadas

- [x] Seleccionar el expediente de prueba: `EXP-2024-089`.
- [x] Definir la especialidad prioritaria: Pavimentos.
- [x] Inventariar los 6 documentos y sus versiones.
- [x] Crear la base de conocimiento versionada (`KB-EXP2024-089-v1`).
- [x] Definir 7 requisitos evaluables con criterio, evidencia y norma.
- [x] Normalizar las ponderaciones para que sumen 100%.
- [x] Definir los cinco estados y la regla de ausencia de evidencia.
- [x] Definir las fórmulas de cobertura y cumplimiento, con redondeo.
- [x] Definir el tiempo máximo del caso: 10 minutos (objetivo: 5 minutos).
- [x] Definir la política de datos y el uso de datos sintéticos/anonimizados.
- [x] Crear los datos semilla para el MVP.

---

## 3. Evidencia entregada

| Evidencia | Ruta | Estado |
|---|---|---|
| Alcance y decisiones | `mvp/etapa1/00_alcance_y_decisiones.md` | ✅ |
| Inventario documental | `mvp/etapa1/01_inventario_expediente.csv` | ✅ |
| Requisitos y ponderaciones | `mvp/etapa1/02_requisitos_ponderaciones.csv` | ✅ |
| Metadatos de la KB | `mvp/etapa1/03_base_conocimiento/metadata.json` | ✅ |
| Checklist versionado | `mvp/etapa1/03_base_conocimiento/checklist_v1.json` | ✅ |
| Normativa y fuentes | `mvp/etapa1/03_base_conocimiento/normativa_v1.md` | ✅ |
| Estados y reglas | `mvp/etapa1/04_estados_y_reglas.md` | ✅ |
| Datos semilla | `mvp/etapa1/05_datos_semilla.json` | ✅ |
| README de la etapa | `mvp/etapa1/README.md` | ✅ |

---

## 4. Verificación de criterios de salida

| Criterio | Resultado |
|---|---|
| Expediente de prueba accesible y documentado | ✅ |
| Base de conocimiento con versión, vigencia y responsable | ✅ |
| Pesos suman exactamente 100% | ✅ (14+17+11+21+14+10+13) |
| Cada requisito tiene criterio, evidencia y norma | ✅ |
| Cinco estados definidos | ✅ |
| Fórmulas y redondeo definidos | ✅ |
| Tiempo máximo definido | ✅ (10 min; objetivo 5 min) |
| Política de datos definida | ✅ |

---

## 5. Resultado del cálculo inicial

Con las decisiones semilla (RQ-01, RQ-04 y RQ-07):

- **Cobertura de revisión:** 48.0% (peso 14 + 21 + 13 = 48).
- **Cumplimiento ponderado:** 86.5% (41.5 / 48 × 100).
- **Pendientes:** RQ-02, RQ-03, RQ-05 y RQ-06.

> El cálculo es reproducible y reemplaza el 62% fijo del prototipo.

---

## 6. Pendientes documentados

- [ ] Reemplazar el caso representativo por el expediente definitivo, si corresponde.
- [ ] Cargar el checklist oficial de 23 ítems, el TDR y la normativa en PDF.
- [ ] Validar las ponderaciones normalizadas con el especialista vial senior.
- [ ] Designar formalmente al responsable de aprobar la base de conocimiento.

Estos pendientes no bloquean las Etapas 2 y 3; la estructura está lista para recibir los documentos definitivos.

---

## 7. Decisión de cierre

La Etapa 1 se declara **COMPLETADA (caso representativo)**. Se solicita aprobación para iniciar la **Etapa 2 — Procesamiento documental**.

| Campo | Valor |
|---|---|
| Solicitada | 11/11/2026 |
| Aprobada por | Pendiente |
| Fecha | Pendiente |
| Observaciones | Pendiente |
