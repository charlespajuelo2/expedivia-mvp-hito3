# Evidencia 01 — Flujo completo de extremo a extremo

**Comando reproducible:** `python -m mvp.scripts.ejecutar_etapa6`
**Base de datos:** `mvp/etapa6/evidencia/mvp_etapa6.db`
**Caso:** `EXP-2024-089`

## Secuencia ejecutada

1. Generación del corpus propio (8 documentos).
2. Registro de 4 expedientes (caso, control vacío, reservado y pruebas de resiliencia).
3. Ingesta, validación, hash, caché y clasificación.
4. Corrección humana del documento ambiguo `EETT_General_v2.docx`.
5. Recuperación de evidencia para los 7 requisitos.
6. Análisis con el proveedor determinista y contrato JSON.
7. Decisiones humanas: aceptar, modificar, descartar e historial.
8. Verificación de avance, cumplimiento y estados.
9. Exportación Excel/Word desde SQLite y reapertura para validar.
10. Ejecución de los 16 casos de prueba mapeados a CA.

## Tiempos medidos

| Etapa del flujo | Milisegundos |
|---|---|
| Ingesta de 8 documentos | 331.3 |
| Recuperación de evidencia | 143.2 |
| Análisis de 7 requisitos | 367.8 |
| Decisiones humanas | 43.3 |
| Exportación Excel + Word | 195.7 |
| **Total de extremo a extremo** | **1081.3** |

## Resultado del flujo

| Métrica | Valor |
|---|---:|
| Documentos válidos | 8 |
| Requisitos con propuesta | 7/7 |
| Cobertura de revisión | 100.0% |
| Decisiones vigentes | 4 |
| Avance ponderado | 39.0% |
| Cumplimiento ponderado | 88.6% |
| No cumple | 0 |
| No se encontró información | 1 |

## Criterio de salida cubierto

- [x] El flujo completo se ejecuta desde cero con un comando.
- [x] Cada etapa deja datos persistidos y auditables.
- [x] La exportación se verifica reabriendo los archivos.
- [x] Los 16 casos de prueba se ejecutan sobre el flujo real.
