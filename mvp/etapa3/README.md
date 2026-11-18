# Etapa 3 — Evidencia e inteligencia artificial

**Estado:** `COMPLETADA`
**Caso:** `EXP-2024-089` — Carretera Central Tramo 2 · Km 42–78 (Pavimentos, datos sintéticos)
**Fecha de cierre:** 11/11/2026
**Alcance aprobado:** recuperación de evidencia por requisito, contrato JSON validado,
integridad de fuente e integración de IA con contingencia y registro de consumo/errores.

---

## 1. Qué se construyó

| Componente | Archivo | Responsabilidad |
|---|---|---|
| Perfiles de evidencia | `etapa3/config/requisitos_evidencia.json` | 7 requisitos, términos ponderados, tipos que prueban, umbrales |
| Recuperación | `core/evidence.py` | Puntuación determinista, ranking, persistencia idempotente |
| Contrato JSON | `core/ai_contract.py` | 8 campos estrictos, fuente/hash/cita, estados válidos |
| Servicio de IA | `core/ai_service.py` | Reglas, OpenAI compatible, guionizado, fallido, reintentos |
| Integridad | `core/integrity.py` | Hash actual vs. registrado, propagación y eventos |
| Orquestación | `core/analysis.py` | Recuperar → verificar → analizar → validar → persistir |
| CLI | `cli.py` | `evidence`, `analyze`, `integrity`, `manual`, `proposals`, `eventos` |
| Interfaz | `app.py` | Pestaña «4. Evidencia y análisis» |
| Corpus | `scripts/generar_muestras_etapa3.py` | 8 documentos, sin tocar el corpus de Etapa 2 |
| Evidencia reproducible | `scripts/ejecutar_etapa3.py` | Reportes 00–13 y aserciones de salida |

---

## 2. Corpus de la etapa

El corpus parte del caso cerrado de la Etapa 2 y agrega dos documentos
complementarios en `mvp/etapa3/muestras/caso/`:

| Documento | Tipo | Aporte |
|---|---|---|
| `Cronograma_Valorizado.xlsx` | Cronograma valorizado | Cronograma, curva S y ruta crítica (RQ-06) |
| `PMA_Ambiental.pdf` | Estudio ambiental | Instrumento ambiental vigente y medidas de mitigación (RQ-07) |

Los otros seis documentos son los mismos de la Etapa 2. La base de datos de la
etapa es independiente: `mvp/etapa3/evidencia/mvp_etapa3.db`.

---

## 3. Reglas implementadas

1. Solo documentos `VALIDO` y `Clasificado` pueden aportar evidencia.
2. La puntuación es la suma de términos ponderados más un bonus por tipo
   documental esperado; el umbral es global o por requisito.
3. La IA recibe únicamente requisito, criterio, evidencia y fuente.
4. Una respuesta solo es válida si cumple **exactamente** los 8 campos del contrato
   y si documento, archivo, ubicación, SHA-256 y cita coinciden con la evidencia.
5. Una respuesta inválida se guarda como no válida y se reintenta; al agotar los
   intentos se activa la contingencia.
6. Si la fuente cambió o no está disponible, **no** se emite conclusión: se escala
   a «Requiere revisión especializada».
7. La ausencia de evidencia produce «No se encontró información», nunca «No cumple».
8. La evaluación manual motivada prevalece sobre la propuesta automática y queda
   auditada.
9. La cobertura de revisión (peso con propuesta) se informa por separado del
   cumplimiento ponderado (peso concluyente).

---

## 4. Resultados del caso principal

| Req. | Requisito | Peso | Estado | Evidencias |
|---|---|---|---|---|
| RQ-01 | Experiencia del postor | 14% | Requiere revisión especializada | TDR, p. 1 |
| RQ-02 | Personal clave - Residente | 17% | Requiere revisión especializada | TDR, p. 1 |
| RQ-03 | Equipamiento mínimo | 11% | Requiere revisión especializada | TDR, p. 1 |
| RQ-04 | Presupuesto por partidas | 21% | **Cumple** | `Presupuesto.xlsx`, Resumen!A3:E3 |
| RQ-05 | Metrados y sustento | 14% | Requiere revisión especializada | Planos, p. 2 |
| RQ-06 | Cronograma valorizado | 10% | Requiere revisión especializada | `Cronograma_Valorizado.xlsx` |
| RQ-07 | Plan de manejo ambiental | 13% | **Cumple** | `PMA_Ambiental.pdf`, p. 1 |

- Cobertura de revisión: **100.0%** (7/7 requisitos con propuesta válida).
- Cumplimiento ponderado: **100.0%** sobre el 34% concluyente (RQ-04 + RQ-07).
- Alertas de integridad en el caso principal: **0**.

La diferencia entre 100% de cobertura y 34% de peso concluyente es deliberada:
los otros cinco requisitos quedan a juicio del especialista y no se contabilizan
como incumplimiento.

---

## 5. Escenarios de control

| Escenario | Expediente | Resultado |
|---|---|---|
| Sin documentos | `EXP-2024-089-CONTROL` | «No se encontró información» |
| Contrato inválido (hash y cita falsos) | `EXP-2024-089-VALIDACION` | 3 intentos, rechazo y contingencia |
| Reintento con respuesta corregida | `EXP-2024-089-VALIDACION` | Válida en el intento 2 |
| Proveedor no disponible | `EXP-2024-089-VALIDACION` | 3 intentos, contingencia y evaluación manual |
| Fuente modificada tras concluir | `EXP-2024-089-INTEGRIDAD` | `FUENTE_MODIFICADA` → revisión especializada |

---

## 6. Evidencia reproducible

```powershell
python -m mvp.scripts.ejecutar_etapa3
```

Genera en `mvp/etapa3/evidencia/`:

| Archivo | Contenido |
|---|---|
| `00_entorno.json` | Versiones, rutas y configuración de IA |
| `01_reporte_ingesta.md` | 8 documentos, clasificación y corrección humana |
| `02_reporte_evidencia.md` | Evidencia recuperada por requisito |
| `03_reporte_analisis.md` | Propuestas, métricas y control sin documentos |
| `04_reporte_contrato.md` | Contrato rechazado y reintento |
| `05_reporte_integridad.md` | Fuente modificada y escalamiento |
| `06_reporte_contingencia.md` | Contingencia y evaluación manual |
| `07_metricas.json` | Métricas agregadas y de consumo |
| `08_auditoria.csv` | Bitácora completa |
| `09_propuestas.csv` | Propuestas válidas e inválidas |
| `10_resultados.csv` | Resultado efectivo por requisito |
| `11_ejecuciones.csv` | Intentos, duración y errores por llamada |
| `12_inventario_procesado.csv` | Inventario final del caso |
| `13_resultados_pruebas.txt` | Salida de la suite de pruebas |
| `mvp_etapa3.db` | Base SQLite de la etapa |

El script termina con aserciones que verifican los estados, los rechazos, el
reintento, la integridad y la evaluación manual.

---

## 7. Pruebas

```powershell
python -m pytest mvp/tests -q
```

Resultado: **37 passed** (20 de Etapa 2 + 17 de Etapa 3).

Cobertura de las pruebas nuevas:

- Perfiles: 7 requisitos y pesos que suman 100.
- Evidencia: recuperación, fuente completa y solo documentos válidos/clasificados.
- Contrato: aceptación coherente, rechazo de hash/cita falsos, campos faltantes o
  desconocidos, fuente nula obligatoria y prohibición de concluir sin evidencia.
- Reglas: `Cumple` solo con prueba directa; escalamiento cuando falta.
- Control sin documentos.
- Reintento, rechazo con contingencia y evaluación manual.
- Integridad: fuente modificada bloquea la conclusión.

---

## 8. Limitaciones conocidas

- El proveedor por defecto (`reglas`) es determinista; no sustituye el juicio de
  ingeniería y no se ejecutó contra un LLM externo por falta de credenciales.
- El cliente OpenAI compatible está implementado y probado con transporte
  simulado, pero no se validó contra un proveedor real.
- La lámina PL-04 del corpus está escaneada; se informa como advertencia y no
  aporta evidencia textual.
- La consolidación de los 23 requisitos y la exportación formal corresponden a
  las Etapas 4 y 5.

---

## 9. Criterios de salida

- [x] Recuperación de evidencia por requisito con fuente verificable.
- [x] Contrato JSON estricto y validación contra la evidencia real.
- [x] Rechazo de respuestas sin fuente, con hash o cita inconsistentes.
- [x] Integridad de fuente con propagación y bloqueo de conclusiones.
- [x] Integración de IA con reintentos, consumo y errores registrados.
- [x] Contingencia operativa y evaluación manual auditada.
- [x] Reportes reproducibles, pruebas automatizadas y actualización de la interfaz.
