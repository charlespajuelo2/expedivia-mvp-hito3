# Evidencia 03 — Control de acceso mínimo por rol

La política vive en `mvp/etapa5/config/usuarios.json`. Los roles son
`administrador`, `especialista` y `lector`; las asignaciones son datos de
demostración.

## Matriz de permisos sobre el expediente principal

| Usuario | Rol | Ver | Cargar | Analizar | Decidir | Exportar | Administrar |
|---|---|---|---|---|---|---|---|
| Admin MVP | administrador | sí | sí | sí | sí | sí | sí |
| Carlos Méndez | lector | sí | no | no | no | no | no |
| Lucía Ramos | especialista | sí | sí | sí | sí | sí | no |

## Denegaciones verificadas

| Caso | Resultado | Causa |
|---|---|---|
| Lector intenta decidir | denegado | El rol «lector» no tiene el permiso «decidir». |
| Lector intenta exportar | denegado | El rol «lector» no tiene el permiso «exportar». |
| Especialista sin expediente asignado | denegado | El usuario «Lucía Ramos» no tiene asignado el expediente «EXP-2024-090». |

## Criterio de salida cubierto

- [x] Un lector puede consultar, pero no decidir ni exportar.
- [x] Un especialista puede decidir y exportar solo sus expedientes asignados.
- [x] Un usuario sin expediente asignado no accede ni siquiera a la lectura.
- [x] La denegación explica la causa y no genera archivos.
