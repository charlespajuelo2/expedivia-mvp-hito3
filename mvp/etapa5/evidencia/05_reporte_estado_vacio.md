# Evidencia 05 — Estado vacío operable

Se exportó un expediente sin documentos y sin decisiones para comprobar que las
pantallas y los informes no fallan cuando no hay datos.

## Métricas del expediente vacío

| Métrica | Valor |
|---|---|
| Requisitos | 7 |
| Cobertura de revisión | 0.0% |
| Avance ponderado | 0.0% |
| Decisiones vigentes | 0 |
| No se encontró información | 0 |

## Exportación del estado vacío

- Excel: Resumen, Requisitos, Decisiones, Propuestas, Evidencias, Documentos, Auditoría (15378 bytes).
- Word: 2 tablas y secciones 1. Resumen ejecutivo, 2. Resultados por requisito, 3. Observaciones y fuentes, 4. Historial de decisiones, 5. Alcance y limitaciones.
- El Word explica que no hay decisiones y que el avance validado es 0%.

## Criterio de salida cubierto

- [x] Un expediente sin datos genera informes sin excepciones.
- [x] El estado vacío se comunica como «sin decisiones», no como error.
- [x] La ausencia de evidencia no se convierte en «No cumple».
