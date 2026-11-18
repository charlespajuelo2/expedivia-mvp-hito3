# 00 — Alcance, supuestos y decisiones de la Etapa 1

**Proyecto:** Asistente IA para revisión y evaluación de perfiles y expedientes técnicos de proyectos viales  
**Etapa:** 1 — Preparación del caso y la base de conocimiento  
**Fecha:** 11/11/2026  
**Versión del documento:** 1.0

---

## 1. Alcance de la etapa

Esta etapa prepara el insumo mínimo para construir y probar el MVP:

1. Un expediente de prueba.
2. Un inventario documental con versiones y estado de clasificación.
3. Una base de conocimiento versionada (checklist, TDR, normativa y ponderaciones).
4. Un conjunto de requisitos evaluables con criterio, evidencia esperada y peso.
5. Reglas de evaluación, estados y fórmulas.
6. Datos semilla para la aplicación.

**No incluye:** carga real de archivos, extracción, IA, persistencia ni exportación. Eso corresponde a las Etapas 2 a 5.

---

## 2. Caso de prueba

| Campo | Valor |
|---|---|
| Código | `EXP-2024-089` |
| Nombre | Carretera Central Tramo 2 · Km 42–78 |
| Especialidad prioritaria | Pavimentos |
| Versión del expediente | v3 |
| Responsable | Lucía Ramos |
| Fecha de referencia | 14/09/2024 |
| Documentos | 6 |
| Requisitos | 7 (subconjunto representativo) |
| Tipo de datos | Sintéticos / representativos |

### Justificación

- Es el caso que ya usa el prototipo y permite comparar la demo visual con el MVP real.
- Cubre documentos típicos de un expediente vial: TDR, presupuesto, memoria, planos, especificaciones y estudio de suelos.
- Permite demostrar los cinco estados y la regla de ausencia de evidencia sin exponer datos sensibles.

---

## 3. Decisiones tomadas

### D1 — Subconjunto representativo de requisitos

Se usan **7 requisitos** del prototipo como subconjunto representativo del checklist de 23 ítems. El checklist oficial completo se incorporará cuando el especialista lo entregue.

**Impacto:** permite construir y demostrar el flujo completo sin inventar criterios normativos.

### D2 — Normalización de ponderaciones

Las ponderaciones del prototipo sumaban **71%** (10+12+8+15+10+7+9). Se normalizaron a **100%** preservando el orden relativo:

| Requisito | Peso original | Peso normalizado |
|---|---:|---:|
| RQ-01 | 10% | 14% |
| RQ-02 | 12% | 17% |
| RQ-03 | 8% | 11% |
| RQ-04 | 15% | 21% |
| RQ-05 | 10% | 14% |
| RQ-06 | 7% | 10% |
| RQ-07 | 9% | 13% |
| **Total** | **71%** | **100%** |

**Impacto:** el cálculo de avance es verificable. Las ponderaciones definitivas deben ser aprobadas por el especialista.

### D3 — Separación de métricas

Se definen dos métricas distintas:

- **Cobertura de revisión:** porcentaje del peso total que ya tiene decisión humana.
- **Cumplimiento ponderado:** porcentaje de cumplimiento calculado solo sobre los requisitos con decisión concluyente.

**Impacto:** la ausencia de evidencia no se trata como incumplimiento ni distorsiona el indicador de cumplimiento.

### D4 — Datos sintéticos

Se usan datos sintéticos o representativos. Si se usa un expediente real, debe estar autorizado o anonimizado.

**Impacto:** se evita exponer información sensible y se cumple la política del Hito 2.

### D5 — Tiempo máximo del caso

Se fija un máximo de **10 minutos** para procesar 6 documentos y 7 requisitos en un equipo estándar, con un objetivo de **5 minutos**.

**Impacto:** da un criterio verificable para CA-22 y para la demo del Hito 3.

### D6 — Hash pendiente

Los hashes SHA-256 se calcularán en la Etapa 2. En el inventario figuran como `PENDIENTE`.

**Impacto:** no se simula un hash; se calcula con el archivo real.

---

## 4. Supuestos

1. El especialista validará los criterios y las ponderaciones antes de la Etapa 3.
2. Los documentos del expediente son legibles y, en su mayoría, tienen texto recuperable.
3. El servicio de IA puede no estar disponible; el flujo debe funcionar en contingencia.
4. El MVP se ejecutará en un entorno local o académico, sin integración institucional.
5. El caso de prueba no requiere OCR en el MVP; si un PDF no tiene texto, se marca como limitación.

---

## 5. Política de datos

- Usar únicamente documentación autorizada, pública, de prueba o anonimizada.
- No incluir nombres, DNI, montos reales sensibles ni credenciales en el repositorio.
- Mantener las credenciales del servicio de IA en variables de entorno.
- Registrar toda carga, análisis, decisión y exportación.
- Eliminar archivos temporales y caché según la política que se defina en la Etapa 2.
- Aplicar permisos por rol: especialista, coordinador, desarrollador y administrador.

---

## 6. Criterios de salida verificados

| Criterio | Evidencia | Estado |
|---|---|---|
| Expediente documentado | `01_inventario_expediente.csv` | ✅ |
| Base de conocimiento versionada | `03_base_conocimiento/metadata.json` | ✅ |
| Pesos suman 100% | `02_requisitos_ponderaciones.csv` | ✅ |
| Requisitos con criterio, evidencia y norma | `02_requisitos_ponderaciones.csv` | ✅ |
| Cinco estados definidos | `04_estados_y_reglas.md` | ✅ |
| Fórmula y redondeo definidos | `04_estados_y_reglas.md` | ✅ |
| Tiempo máximo definido | Este documento, D5 | ✅ |
| Política de datos definida | Este documento, sección 5 | ✅ |

---

## 7. Aprobación

| Campo | Valor |
|---|---|
| Solicitada | 11/11/2026 |
| Aprobada por | Usuario |
| Medio | Instrucción en chat: “continua con la Etapa 1” |
| Fecha | 11/11/2026 |
| Alcance | Caso representativo `EXP-2024-089`, 6 documentos, 7 requisitos |

---

## 8. Próximo paso

Solicitar aprobación para iniciar la **Etapa 2 — Procesamiento documental**.
