# Etapa 4 — Evaluación, trazabilidad y persistencia

**Estado:** `COMPLETADA`
**Caso:** `EXP-2024-089` — Carretera Central Tramo 2 · Km 42–78 (Pavimentos, datos sintéticos)
**Fecha de cierre:** 11/11/2026
**Alcance aprobado:** cinco estados, regla de ausencia de evidencia, decisión humana
aceptar / modificar / descartar, conservación de la propuesta original, avance
ponderado, persistencia, auditoría y reejecución sin duplicar hallazgos.

---

## 1. Qué se construyó

| Componente | Archivo | Responsabilidad |
|---|---|---|
| Esquema | `core/db.py` | Tabla `decisiones`, huella en `propuestas_ia`, migración e índice único |
| Evaluación | `core/evaluation.py` | Decisión validada, historial, decisión vigente y avance ponderado |
| Orquestación | `core/analysis.py` | Huella canónica, deduplicación y estado efectivo con decisión |
| CLI | `cli.py` | `decide`, `history`, `progress` |
| Interfaz | `app.py` | Pestaña «5. Evaluación y avance» |
| Evidencia reproducible | `scripts/ejecutar_etapa4.py` | Base y corpus propios, reportes 00–10 y aserciones |
| Pruebas | `tests/test_etapa4.py` | 14 pruebas nuevas (51 en total) |

---

## 2. Los cinco estados

| Estado | ¿Concluyente? | Factor | Uso |
|---|---|---|---|
| `Cumple` | Sí | 1.0 | Evidencia directa verificada |
| `Cumple parcialmente` | Sí | 0.5 | Cumplimiento parcial motivado |
| `No cumple` | Sí | 0.0 | Incumplimiento con evidencia |
| `No se encontró información` | No | — | Ausencia de evidencia; **nunca** se convierte en “No cumple” |
| `Requiere revisión especializada` | No | — | Juicio de ingeniería o fuente alterada |

La regla de ausencia se refuerza en dos capas: el contrato de la Etapa 3 no
permite concluir sin evidencia y `descartar` fija el estado final en
`No se encontró información`.

---

## 3. Decisiones y trazabilidad

| Decisión | Estado final | Validaciones |
|---|---|---|
| `aceptar` | El estado propuesto | Debe existir propuesta válida y fuente vigente |
| `modificar` | El estado indicado | Debe ser del catálogo y distinto del propuesto |
| `descartar` | `No se encontró información` | No admite otro estado final |

Toda decisión exige **motivo**, **responsable** y **versión del expediente**; la
fecha se sella al registrar. La tabla `decisiones` es un historial inmutable:

- `estado_propuesto`: se copia de la propuesta original y nunca se sobrescribe.
- `estado_final`: resultado decidido por la persona.
- `propuesta_id` y `huella_propuesta`: enlazan con la evidencia original.
- La decisión vigente es la de mayor `id` por requisito.

---

## 4. Avance ponderado

```text
avance_pct = Σ(peso × factor_avance) / peso_total × 100
factor_avance = 0                       si no hay decisión o se descartó
              = factor del estado final si se aceptó o modificó
redondeo = ROUND_HALF_UP a 1 decimal
```

El avance no premia propuestas automáticas: exige una decisión humana. Es
distinto de la **cobertura de revisión** (peso con propuesta) y del
**cumplimiento ponderado** (peso concluyente).

---

## 5. Resultado del caso

| Req. | Peso | Estado propuesto | Decisión | Estado final | Aporte |
|---|---:|---|---|---|---:|
| RQ-01 | 14% | Requiere revisión especializada | sin decidir | Requiere revisión especializada | 0 |
| RQ-02 | 17% | Requiere revisión especializada | sin decidir | Requiere revisión especializada | 0 |
| RQ-03 | 11% | Requiere revisión especializada | sin decidir | Requiere revisión especializada | 0 |
| RQ-04 | 21% | Cumple | aceptar | Cumple | 21.0 |
| RQ-05 | 14% | Requiere revisión especializada | descartar | No se encontró información | 0 |
| RQ-06 | 10% | Requiere revisión especializada | modificar | Cumple parcialmente | 5.0 |
| RQ-07 | 13% | Cumple | aceptar | Cumple | 13.0 |

| Métrica | Antes | Después |
|---|---:|---:|
| Cobertura de revisión | 100.0% | 100.0% |
| Peso decidido | 0.0% | 58.0% |
| **Avance ponderado** | **0.0%** | **39.0%** |
| Cumplimiento ponderado | 100.0% | 88.6% |
| Decisiones vigentes | 0 | 4 |
| Cumple / Parcial / No cumple | 2 / 0 / 0 | 2 / 1 / 0 |
| No se encontró información | 0 | 1 |
| Requiere revisión | 5 | 3 |

RQ-04 se decidió tres veces (aceptar, modificar y aceptar) para demostrar que el
historial se acumula y solo la última decisión queda vigente.

---

## 6. Evidencia reproducible

```powershell
python -m mvp.scripts.ejecutar_etapa4
```

Genera en `mvp/etapa4/evidencia/`:

| Archivo | Contenido |
|---|---|
| `00_entorno.json` | Versiones, rutas y configuración |
| `01_reporte_antes.md` | Métricas antes de decidir (avance 0%) |
| `02_reporte_decisiones.md` | Decisiones, propuesta original e historial |
| `03_reporte_despues.md` | Antes/después y verificación manual de la fórmula |
| `04_reporte_persistencia.md` | Lectura desde una instancia nueva |
| `05_reporte_reejecucion.md` | Reanálisis sin duplicar hallazgos |
| `06_metricas.json` | Métricas comparables y cálculo manual |
| `07_historial_decisiones.csv` | Historial completo con fuente y cita |
| `08_resultados.csv` | Resultado efectivo por requisito |
| `09_propuestas.csv` | Propuestas con huella e integridad |
| `10_auditoria.csv` | Bitácora completa |
| `mvp_etapa4.db` | Base SQLite de la etapa |

El script termina con aserciones sobre avance, cumplimiento, estados, historial,
persistencia e idempotencia.

---

## 7. Pruebas

```powershell
python -m pytest mvp/tests -q
```

Resultado: **51 passed** (20 de Etapa 2 + 17 de Etapa 3 + 14 de Etapa 4).

Cobertura nueva:

- Catálogo de cinco estados, factores y redondeo `ROUND_HALF_UP`.
- Aceptar conserva el estado propuesto y actualiza contadores.
- Modificar exige estado válido y distinto.
- Descartar no se convierte en “No cumple”.
- Motivo, responsable y tipo de decisión obligatorios.
- No se decide sin propuesta o con fuente modificada.
- Historial acumulativo con una sola decisión vigente.
- Persistencia en una instancia nueva.
- Reejecución sin propuestas duplicadas y con decisiones conservadas.
- Avance sobre peso total y migración de bases anteriores.

---

## 8. Limitaciones conocidas

- Los 7 requisitos representativos siguen siendo la base; la consolidación de los
  23 requisitos oficiales queda pendiente.
- La decisión humana no implementa roles ni permisos; el control de acceso
  corresponde a la Etapa 5.
- La exportación formal a Excel y Word corresponde a la Etapa 5.
- No se valida el cliente OpenAI compatible contra un servicio real por falta de
  credenciales; el flujo usa el proveedor determinista de reglas.

---

## 9. Criterios de salida

- [x] El contador de validados cambia realmente al decidir (0 → 4).
- [x] El avance se recalcula y coincide con la fórmula documentada (39.0%).
- [x] Al recargar la aplicación, las decisiones persisten.
- [x] El historial muestra propuesta, decisión, motivo, fecha y responsable.
- [x] Reejecutar no duplica hallazgos (7 → 7 propuestas, 0 duplicadas).
- [x] Los cinco estados están implementados y la ausencia no es incumplimiento.
