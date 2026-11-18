# Acta de cierre — Etapa 3

**Proyecto:** Asistente IA para revisión y evaluación de perfiles y expedientes técnicos de proyectos viales  
**Etapa:** 3 — Evidencia e inteligencia artificial  
**Fecha:** 11/11/2026  
**Estado:** `COMPLETADA`

---

## 1. Aprobación de inicio

| Campo | Valor |
|---|---|
| Solicitada | 11/11/2026 |
| Aprobada por | Usuario |
| Medio | Instrucción en chat: “continua con la etapa 3” |
| Fecha | 11/11/2026 |
| Alcance aprobado | Recuperación de evidencia por requisito, contrato JSON validado, integridad de fuente e integración de IA con contingencia y registro de consumo/errores |

---

## 2. Tareas ejecutadas

- [x] Definir perfiles de evidencia para los 7 requisitos representativos.
- [x] Implementar recuperación determinista por términos ponderados y tipo documental.
- [x] Guardar archivo, página/hoja/celda, fragmento y SHA-256 de cada evidencia.
- [x] Definir el contrato JSON de 8 campos y validarlo contra la evidencia real.
- [x] Rechazar respuestas con fuente, hash o cita inconsistentes.
- [x] Implementar proveedor de reglas, cliente OpenAI compatible y proveedores de prueba.
- [x] Registrar intentos, duración, tokens y errores de cada ejecución.
- [x] Verificar la integridad de las fuentes y propagar el estado a evidencias y propuestas.
- [x] Bloquear conclusiones automáticas cuando la fuente cambió o no está disponible.
- [x] Implementar contingencia y evaluación manual motivada.
- [x] Separar cobertura de revisión y cumplimiento ponderado.
- [x] Ampliar el CLI con `evidence`, `analyze`, `integrity`, `manual`, `proposals` y `eventos`.
- [x] Agregar la pestaña «4. Evidencia y análisis» a la interfaz Streamlit.
- [x] Generar el corpus de 8 documentos en `mvp/etapa3/muestras/`.
- [x] Ejecutar y documentar 17 pruebas nuevas (37 en total).

---

## 3. Evidencia entregada

| Evidencia | Ruta | Estado |
|---|---|---|
| Perfiles de evidencia | `mvp/etapa3/config/requisitos_evidencia.json` | ✅ |
| Recuperación de evidencia | `mvp/core/evidence.py` | ✅ |
| Contrato JSON | `mvp/core/ai_contract.py` | ✅ |
| Servicio de IA | `mvp/core/ai_service.py` | ✅ |
| Integridad de fuente | `mvp/core/integrity.py` | ✅ |
| Orquestación y contingencia | `mvp/core/analysis.py` | ✅ |
| CLI ampliado | `mvp/cli.py` | ✅ |
| Interfaz con análisis | `mvp/app.py` | ✅ |
| Generador del corpus | `mvp/scripts/generar_muestras_etapa3.py` | ✅ |
| Ejecución reproducible | `mvp/scripts/ejecutar_etapa3.py` | ✅ |
| Corpus del caso (8 documentos) | `mvp/etapa3/muestras/caso/` | ✅ |
| Reportes 00–13 | `mvp/etapa3/evidencia/` | ✅ |
| Base SQLite | `mvp/etapa3/evidencia/mvp_etapa3.db` | ✅ |
| Pruebas | `mvp/tests/test_etapa3.py` | ✅ |

---

## 4. Verificación de criterios de salida

| Criterio | Resultado |
|---|---|
| Cada requisito recupera evidencia con fuente verificable | ✅ 7/7, 15 fragmentos |
| El contrato acepta solo respuestas coherentes | ✅ 8 campos, fuente, hash y cita |
| Una cita o hash falsos se rechazan | ✅ `HASH_NO_COINCIDE` + `CITA_NO_ENCONTRADA` |
| Los reintentos se registran y se detienen al validar | ✅ válida en intento 2 |
| Al agotar intentos se activa contingencia | ✅ 3 intentos, propuesta no válida |
| Una fuente modificada bloquea la conclusión | ✅ `FUENTE_MODIFICADA` → revisión |
| Sin documentos no se marca “No cumple” | ✅ «No se encontró información» |
| La evaluación manual prevalece y queda auditada | ✅ estado y motivo persistidos |
| Se registra consumo y error de cada ejecución | ✅ `ejecuciones_ia` + CSV |
| Cobertura y cumplimiento se informan por separado | ✅ 100.0% vs. 34% concluyente |

---

## 5. Resultado de la ejecución

```text
Caso: 8 documentos válidos, 7 propuestas válidas
Estados: RQ-04 y RQ-07 Cumple; RQ-01/02/03/05/06 Requiere revisión especializada
Cobertura de revisión: 100.0%
Cumplimiento ponderado: 100.0% sobre el 34% concluyente
Contrato: rechazo en 3 intentos; reintento válido en 2
Integridad: FUENTE_MODIFICADA → Requiere revisión especializada
Contingencia: 3 intentos y evaluación manual registrada
Pruebas: 37 passed
```

### Escenarios de control

| Escenario | Expediente | Resultado |
|---|---|---|
| Sin documentos | `EXP-2024-089-CONTROL` | «No se encontró información» |
| Contrato inválido | `EXP-2024-089-VALIDACION` | Rechazo y contingencia |
| Reintento corregido | `EXP-2024-089-VALIDACION` | Válida en intento 2 |
| Proveedor caído | `EXP-2024-089-VALIDACION` | Contingencia + evaluación manual |
| Fuente modificada | `EXP-2024-089-INTEGRIDAD` | Escalamiento por integridad |

---

## 6. Decisiones registradas

1. El proveedor por defecto es **`ProveedorReglas`**: determinista, sin red y
   reproducible; la IA externa es opcional.
2. Una conclusión automática solo se emite con **prueba directa**, puntaje sobre
   el umbral y sin juicio de ingeniería pendiente.
3. La ausencia de evidencia produce **«No se encontró información»**, nunca
   «No cumple».
4. El contrato es **estricto**: campos exactos, estados aprobados y fuente
   verificable; se rechazan campos desconocidos o faltantes.
5. La integridad se comprueba **antes** de llamar a la IA y también bajo demanda.
6. Una fuente modificada invalida la conclusión anterior y **escala** el requisito.
7. La contingencia conserva la evidencia y habilita la **evaluación manual**.
8. La **cobertura de revisión** y el **cumplimiento ponderado** son métricas
   distintas y se muestran por separado.

---

## 7. Limitaciones y pendientes

- [ ] Validar el cliente OpenAI compatible contra un proveedor real con credenciales.
- [ ] Incorporar OCR para la lámina PL-04 y otros PDF sin capa de texto.
- [ ] Consolidar los 23 requisitos del checklist oficial en la Etapa 4.
- [ ] Exportación formal a Excel y Word en la Etapa 5.
- [ ] Validación de ponderaciones y perfiles por el especialista.

No bloquean la Etapa 4. La evidencia, las propuestas, la integridad y las
evaluaciones manuales ya están persistidas y auditadas.

---

## 8. Decisión de cierre

La Etapa 3 se declara **COMPLETADA**. Se solicita aprobación para iniciar la
**Etapa 4 — Evaluación y ponderaciones**.

| Campo | Valor |
|---|---|
| Solicitada | 11/11/2026 |
| Aprobada por | Pendiente |
| Fecha | Pendiente |
| Observaciones | Pendiente |
