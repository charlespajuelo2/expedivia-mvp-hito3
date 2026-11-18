# Acta de cierre — Etapa 4

**Proyecto:** Asistente IA para revisión y evaluación de perfiles y expedientes técnicos de proyectos viales
**Etapa:** 4 — Evaluación, trazabilidad y persistencia
**Fecha:** 11/11/2026
**Estado:** `COMPLETADA`

---

## 1. Aprobación de inicio

| Campo | Valor |
|---|---|
| Solicitada | 11/11/2026 |
| Aprobada por | Usuario |
| Medio | Instrucción en chat: “ejecuta la etapa 4” |
| Fecha | 11/11/2026 |
| Alcance aprobado | Cinco estados, ausencia de evidencia, aceptar/modificar/descartar con motivo, fecha y responsable, propuesta original + decisión final, avance ponderado, persistencia, auditoría y reejecución sin duplicar hallazgos |

---

## 2. Tareas ejecutadas

- [x] Implementar los cinco estados del catálogo y sus factores.
- [x] Aplicar la regla: ausencia de evidencia → “No se encontró información”.
- [x] Implementar aceptar / modificar / descartar con motivo, fecha y responsable.
- [x] Conservar la propuesta original y la decisión final por separado.
- [x] Implementar el avance ponderado con `ROUND_HALF_UP` a 1 decimal.
- [x] Persistir decisiones, propuestas y auditoría en SQLite.
- [x] Auditar usuario, fecha, expediente, versión y decisión.
- [x] Implementar reejecución idempotente mediante huella canónica.
- [x] Ampliar el CLI con `decide`, `history` y `progress`.
- [x] Agregar la pestaña «5. Evaluación y avance» a Streamlit.
- [x] Generar corpus y base propios en `mvp/etapa4/`, sin alterar las etapas cerradas.
- [x] Ejecutar y documentar 14 pruebas nuevas (51 en total).

---

## 3. Evidencia entregada

| Evidencia | Ruta | Estado |
|---|---|---|
| Esquema y migración | `mvp/core/db.py` | ✅ |
| Evaluación e historial | `mvp/core/evaluation.py` | ✅ |
| Deduplicación y estado efectivo | `mvp/core/analysis.py` | ✅ |
| CLI ampliado | `mvp/cli.py` | ✅ |
| Pestaña de evaluación | `mvp/app.py` | ✅ |
| Ejecución reproducible | `mvp/scripts/ejecutar_etapa4.py` | ✅ |
| Corpus y base de la etapa | `mvp/etapa4/muestras/`, `mvp/etapa4/evidencia/mvp_etapa4.db` | ✅ |
| Reportes 00–10 | `mvp/etapa4/evidencia/` | ✅ |
| Pruebas | `mvp/tests/test_etapa4.py` | ✅ |
| Guía de la etapa | `mvp/etapa4/README.md` | ✅ |

---

## 4. Verificación de criterios de salida

| Criterio | Resultado |
|---|---|
| El contador de validados cambia al decidir | ✅ 0 → 4 decisiones vigentes |
| El avance coincide con la fórmula documentada | ✅ 39.0% (21 + 13 + 5 + 0) |
| Las decisiones persisten tras recargar | ✅ instancia nueva con métricas e historial idénticos |
| El historial muestra propuesta, decisión, motivo, fecha y responsable | ✅ `02_reporte_decisiones.md` |
| Reejecutar no duplica hallazgos | ✅ 7 → 7 propuestas, 0 duplicadas |
| Cinco estados implementados | ✅ catálogo, factores y validaciones |
| Ausencia de evidencia ≠ “No cumple” | ✅ `sin_informacion=1`, `no_cumple=0` |
| Decisión auditada con expediente y versión | ✅ `DECISION_REGISTRADA` con `version_kb=v4` |

---

## 5. Resultado de la ejecución

```text
Caso: 8 documentos válidos, 7 propuestas válidas
Antes: cobertura 100.0%, avance 0.0%, cumplimiento 100.0%, decisiones 0
Después: cobertura 100.0%, avance 39.0%, cumplimiento 88.6%, decisiones 4
Decisiones: 2 aceptar, 1 modificar, 1 descartar
Estados: Cumple 2, Cumple parcialmente 1, No se encontró información 1,
         Requiere revisión especializada 3, No cumple 0
Historial: RQ-04 con 3 registros y una sola decisión vigente
Persistencia: métricas e historial idénticos en instancia nueva
Reejecución: 7 → 7 propuestas, 0 duplicadas, decisiones conservadas
Pruebas: 51 passed
```

---

## 6. Decisiones registradas

1. La decisión humana es una **fila nueva**, no una actualización: el historial es
   inmutable y la decisión vigente es la última.
2. `aceptar` conserva el estado propuesto; `modificar` exige un estado distinto;
   `descartar` fija “No se encontró información”.
3. El avance ponderado se calcula sobre el **peso total**, no sobre el peso
   concluyente, y solo suma requisitos con decisión humana.
4. La reejecución reutiliza propuestas idénticas por **huella canónica**; no se
   insertan duplicados ni se pierden decisiones.
5. Una fuente modificada **bloquea** aceptar o modificar hasta reanalizar.
6. La base y el corpus de la Etapa 4 son independientes para no alterar las
   etapas cerradas.

---

## 7. Limitaciones y pendientes

- [ ] Consolidar los 23 requisitos oficiales del checklist.
- [ ] Implementar roles y permisos (Etapa 5).
- [ ] Exportar `.xlsx` y `.docx` con resultados validados (Etapa 5).
- [ ] Validar el cliente OpenAI compatible con credenciales reales.

No bloquean la Etapa 5. Las decisiones, el historial y el avance ya están
persistidos y auditados.

---

## 8. Decisión de cierre

La Etapa 4 se declara **COMPLETADA**. Se solicita aprobación para iniciar la
**Etapa 5 — Interfaz, exportación y contingencia visible**.

| Campo | Valor |
|---|---|
| Solicitada | 11/11/2026 |
| Aprobada por | Pendiente |
| Fecha | Pendiente |
| Observaciones | Pendiente |
