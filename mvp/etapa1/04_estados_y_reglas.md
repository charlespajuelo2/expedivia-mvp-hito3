# 04 — Estados, reglas de evaluación y fórmulas

**KB:** `KB-EXP2024-089-v1`  
**Versión:** 1.0  
**Fecha:** 11/11/2026

---

## 1. Catálogo de estados

| Estado | Definición | Factor de cumplimiento | ¿Cuenta como conclusión? |
|---|---|---:|---|
| **Cumple** | La evidencia satisface el criterio en su totalidad. | 1.0 | Sí |
| **Cumple parcialmente** | La evidencia satisface el criterio solo en parte o con observaciones menores. | 0.5 | Sí |
| **No cumple** | La evidencia demuestra que el criterio no se satisface. | 0.0 | Sí |
| **No se encontró información** | No se localizó evidencia suficiente. **No equivale a incumplimiento.** | — | No |
| **Requiere revisión especializada** | El caso requiere juicio de ingeniería o la evidencia es ambigua. | — | No |

---

## 2. Regla de ausencia de evidencia

> **La ausencia de evidencia nunca se convierte automáticamente en “No cumple”.**

- Si no se encuentra evidencia, el estado es **“No se encontró información”**.
- El sistema puede proponer ese estado, pero el especialista decide.
- “No se encontró información” se muestra con una alerta neutra, distinta de un error o de un incumplimiento.
- Si la evidencia existe pero es ambigua o requiere juicio de ingeniería, el estado es **“Requiere revisión especializada”**.

---

## 3. Decisiones del especialista

| Decisión | Efecto |
|---|---|
| **Aceptar** | El estado final es el estado propuesto por la IA. |
| **Modificar** | El especialista cambia el estado y registra el motivo. |
| **Descartar** | Se descarta la propuesta de la IA: el requisito queda en **“No se encontró información”** y no aporta al avance. |

El MVP implementa estas **tres decisiones**. El estado “Requiere revisión
especializada” no es una cuarta decisión: se registra como **estado final** al
modificar la propuesta (por ejemplo, cuando falta juicio de ingeniería).

Toda decisión registra: propuesta original, decisión final, motivo, fecha y responsable.

---

## 4. Fórmulas

### 4.1 Cobertura de revisión

Mide cuánto del peso total ya fue **analizado** (tiene propuesta de la IA o
evaluación manual registrada).

```
cobertura = Σ peso de requisitos analizados / Σ peso total × 100
```

### 4.2 Peso decidido

Mide cuánto del peso total tiene una **decisión humana vigente**.

```
peso_decidido = Σ peso de requisitos con decisión vigente / Σ peso total × 100
```

### 4.3 Cumplimiento ponderado

Mide el cumplimiento solo sobre los requisitos con decisión concluyente. Excluye “No se encontró información” y “Requiere revisión especializada” para no sancionar la falta de evidencia.

```
cumplimiento = Σ (peso × factor) / Σ peso de requisitos concluyentes × 100
```

Donde `factor` es 1.0 (Cumple), 0.5 (Cumple parcialmente) o 0.0 (No cumple).

### 4.4 Avance ponderado

Mide el avance validado sobre el **peso total** del catálogo. Aceptar y modificar
usan el factor del estado final; descartar aporta 0.

```
avance = Σ (peso × factor_avance) / Σ peso total × 100

factor_avance = 0                          si no hay decisión
factor_avance = 0                          si la decisión es descartar
factor_avance = factor del estado final    en los demás casos
```

### 4.5 Redondeo

- Un decimal.
- Redondeo **half-up** (0.05 sube).
- Ejemplo: 84.2105 → **84.2**.

---

## 5. Ejemplo de cálculo con el caso representativo

Pesos: RQ-01=14, RQ-02=17, RQ-03=11, RQ-04=21, RQ-05=14, RQ-06=10, RQ-07=13. Total = 100.

Estados iniciales:

| RQ | Peso | Estado | Factor |
|---|---:|---|---:|
| RQ-01 | 14 | Cumple | 1.0 |
| RQ-02 | 17 | Cumple | 1.0 |
| RQ-03 | 11 | Cumple parcialmente | 0.5 |
| RQ-04 | 21 | Cumple | 1.0 |
| RQ-05 | 14 | No se encontró información | — |
| RQ-06 | 10 | Requiere revisión especializada | — |
| RQ-07 | 13 | Cumple parcialmente | 0.5 |

### Escenario A — todos con decisión humana

- Cobertura = 100 / 100 × 100 = **100.0%** (los 7 requisitos fueron analizados)
- Peso decidido = 100 / 100 × 100 = **100.0%**
- Requisitos concluyentes: RQ-01, RQ-02, RQ-03, RQ-04, RQ-07
- Peso concluyente = 14 + 17 + 11 + 21 + 13 = **76**
- Numerador = (14×1.0) + (17×1.0) + (11×0.5) + (21×1.0) + (13×0.5) = **64.0**
- Cumplimiento = 64.0 / 76 × 100 = 84.2105 → **84.2%**
- Avance = 64.0 / 100 × 100 = **64.0%**

### Escenario B — RQ-05 y RQ-06 aún pendientes

- Cobertura = 100 / 100 × 100 = **100.0%** (ambos tienen propuesta, pero no decisión)
- Peso decidido = 76 / 100 × 100 = **76.0%**
- Cumplimiento = 64.0 / 76 × 100 = **84.2%** (no cambia, porque los pendientes no son concluyentes)
- Avance = 64.0 / 100 × 100 = **64.0%** (los pendientes no aportan)

> Este cálculo reemplaza el 62% fijo del prototipo por un indicador verificable y explicable.

---

## 6. Reglas de integridad

1. Cada documento se carga con un **hash SHA-256**.
2. Cada evidencia registra el hash del documento fuente al momento de la revisión.
3. Si el documento cambia después de la decisión, la evidencia se marca como **“fuente modificada”**.
4. La alerta de “fuente modificada” es visualmente distinta de “No cumple”.
5. El especialista debe revalidar la evidencia afectada.

---

## 7. Reglas de contingencia

1. Si el servicio de IA no está disponible, el flujo **no se bloquea**.
2. El especialista puede evaluar manualmente los requisitos.
3. El sistema reintenta el análisis en segundo plano.
4. Cuando la IA responde, muestra su propuesta para contrastarla con la evaluación manual.
5. No se generan conclusiones artificiales ni estados automáticos.

---

## 8. Reglas de auditoría

Se registra, como mínimo:

- Usuario y rol.
- Fecha y hora.
- Expediente y versión.
- Requisito y criterio.
- Evidencia y fuente.
- Hash de integridad.
- Propuesta de la IA.
- Decisión humana y motivo.
- Versión de la base de conocimiento aplicada.

---

## 9. Verificación

- [x] Cinco estados definidos.
- [x] Regla de ausencia de evidencia definida.
- [x] Decisiones humanas definidas.
- [x] Fórmulas de cobertura y cumplimiento definidas.
- [x] Redondeo definido.
- [x] Ejemplo de cálculo verificable.
- [x] Reglas de integridad, contingencia y auditoría definidas.
