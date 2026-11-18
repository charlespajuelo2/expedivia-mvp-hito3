# Etapa 1 — Preparación del caso y la base de conocimiento

**Estado:** `COMPLETADA (caso representativo)`  
**Fecha de cierre:** 11/11/2026  
**Aprobación de inicio:** Usuario — instrucción “continua con la Etapa 1” (11/11/2026)  
**Responsable:** Equipo del proyecto / Especialista vial senior (por designar)

---

## 1. Objetivo de la etapa

Dejar listo el **caso de prueba**, el **inventario documental**, la **base de conocimiento versionada**, las **ponderaciones** y las **reglas de evaluación** para que las etapas 2 a 5 construyan el MVP sobre una base única y trazable.

---

## 2. Caso de prueba seleccionado

| Campo | Valor |
|---|---|
| Expediente | `EXP-2024-089` |
| Nombre | Carretera Central Tramo 2 · Km 42–78 |
| Especialidad | Pavimentos |
| Versión | v3 |
| Responsable | Lucía Ramos (rol: especialista revisor) |
| Documentos | 6 |
| Requisitos evaluables | 7 (subconjunto representativo del checklist de 23) |
| Tipo de datos | Sintéticos / representativos |
| Fecha de referencia | 14/09/2024 (datos de demo) |

> **Nota:** el caso es representativo y no contiene datos personales reales. Si el equipo dispone de un expediente real o anonimizado, se reemplazan los archivos manteniendo la misma estructura.

---

## 3. Entregables de la etapa

| # | Archivo | Contenido |
|---|---|---|
| 1 | `00_alcance_y_decisiones.md` | Alcance, supuestos, decisiones y política de datos |
| 2 | `01_inventario_expediente.csv` | Inventario de los 6 documentos, versión, formato y estado de clasificación |
| 3 | `02_requisitos_ponderaciones.csv` | 7 requisitos, criterios, evidencia esperada, norma y peso |
| 4 | `03_base_conocimiento/metadata.json` | Metadatos y fuentes de la base de conocimiento |
| 5 | `03_base_conocimiento/checklist_v1.json` | Checklist versionado legible por la aplicación |
| 6 | `03_base_conocimiento/normativa_v1.md` | Fuentes normativas y reglas de vigencia |
| 7 | `04_estados_y_reglas.md` | 5 estados, regla de ausencia, fórmulas y redondeo |
| 8 | `05_datos_semilla.json` | Datos iniciales para el MVP |
| 9 | `06_acta_cierre_etapa1.md` | Acta de cierre y solicitud de aprobación de la Etapa 2 |

---

## 4. Verificación de criterios de salida

- [x] Existe un expediente de prueba accesible y documentado.
- [x] La base de conocimiento tiene versión, vigencia y responsable.
- [x] Los pesos suman exactamente 100%.
- [x] Cada requisito tiene criterio, evidencia esperada y norma/fuente.
- [x] Están definidos los 5 estados y la regla de ausencia de evidencia.
- [x] Está definida la fórmula de avance, el redondeo y un ejemplo de cálculo.
- [x] Está definido el tiempo máximo de procesamiento del caso.
- [x] Está definida la política de datos y el uso de datos sintéticos/anonimizados.

---

## 5. Decisiones clave

1. Se usa el **subconjunto de 7 requisitos** visible en el prototipo como caso representativo del MVP. El checklist oficial de 23 ítems se cargará cuando el especialista lo entregue.
2. Las ponderaciones originales del prototipo sumaban 71%; se **normalizaron a 100%** preservando el orden relativo, para que el cálculo sea verificable.
3. Se separan dos métricas: **cobertura de revisión** (avance) y **cumplimiento ponderado** (resultado), para no sancionar la ausencia de evidencia.
4. El tiempo máximo del caso se fija en **10 minutos** para 6 documentos y 7 requisitos en un equipo estándar.
5. Los hashes SHA-256 se calcularán en la Etapa 2; en esta etapa quedan como `PENDIENTE`.

---

## 6. Pendientes antes de la Etapa 3

- [ ] Reemplazar el caso representativo por el expediente real o anonimizado definitivo, si corresponde.
- [ ] Cargar el checklist oficial de 23 ítems, el TDR y la normativa vigente en PDF.
- [ ] Validar las ponderaciones normalizadas con el especialista vial senior.
- [ ] Designar formalmente al responsable de aprobar la base de conocimiento.

> Estos pendientes **no bloquean** las Etapas 2 y 3; la estructura ya está preparada para recibir los documentos definitivos.

---

## 7. Evidencia

- Carpeta: `mvp/etapa1/`
- Inventario: `01_inventario_expediente.csv`
- Requisitos y pesos: `02_requisitos_ponderaciones.csv`
- Base de conocimiento: `03_base_conocimiento/`
- Reglas: `04_estados_y_reglas.md`
- Datos semilla: `05_datos_semilla.json`
- Acta: `06_acta_cierre_etapa1.md`

---

## 8. Próximo paso

La Etapa 1 queda cerrada con un caso representativo. La **Etapa 2 — Procesamiento documental** requiere aprobación explícita para comenzar.
