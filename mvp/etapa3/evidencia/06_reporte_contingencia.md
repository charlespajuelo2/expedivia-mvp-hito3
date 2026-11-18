# Evidencia 06 — Contingencia y evaluación manual

Se forzó un proveedor no disponible (`ProveedorFallido`) sobre RQ-04 de
`EXP-2024-089-VALIDACION` para comprobar que el flujo no pierde la evidencia ni
inventa una conclusión.

## Resultado de la contingencia

| Campo | Valor |
|---|---|
| Estado | Requiere revisión especializada |
| ¿Válida? | no |
| Intentos | 3 |
| Contingencia | sí |
| Proveedor | fallido |

Errores:

```text
IA_NO_DISPONIBLE: El servicio de IA no está disponible.
IA_NO_DISPONIBLE: El servicio de IA no está disponible.
IA_NO_DISPONIBLE: El servicio de IA no está disponible.
```

La propuesta de contingencia se guarda como **no válida** y la evidencia recuperada
permanece disponible para revisión manual.

## Evaluación manual registrada

| Campo | Valor |
|---|---|
| Requisito | RQ-04 |
| Estado | Requiere revisión especializada |
| Responsable | Lucía Ramos |
| Motivo | La fuente fue modificada y el servicio de IA no está disponible; se revisará el presupuesto actualizado. |
| Fecha | 2026-11-11T22:30:28 |

## Estado efectivo del expediente de validación

| Métrica | Valor |
|---|---|
| Cobertura de revisión | 21.0% |
| Evaluaciones manuales | 1 |
| Contingencias | 0 |
| Alertas de integridad | 0 |

## Criterio de salida cubierto

- [x] Ante un fallo de IA se activa la contingencia y se conserva la evidencia.
- [x] El especialista puede registrar una evaluación manual motivada.
- [x] La evaluación manual prevalece en el resultado efectivo y queda auditada.
