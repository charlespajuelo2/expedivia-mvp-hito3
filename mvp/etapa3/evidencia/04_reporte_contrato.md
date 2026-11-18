# Evidencia 04 — Contrato rechazado y reintento

Escenario sobre `EXP-2024-089-VALIDACION` con una copia de `Presupuesto.xlsx`.
La propuesta inválida declara un SHA-256 falso y una cita inventada.

## Respuesta inválida presentada al contrato

```json
{
  "requisito_id": "RQ-04",
  "estado_propuesto": "Cumple",
  "evidencia_encontrada": true,
  "fuente": {
    "documento_id": 9,
    "archivo": "Presupuesto.xlsx",
    "ubicacion": "Hoja:Resumen!A3:E3",
    "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "cita": "Cita inventada que no aparece en el fragmento citado.",
  "observacion_preliminar": "Propuesta construida desde la evidencia recuperada.",
  "requiere_revision_especializada": false,
  "motivo": "La evidencia directa cubre el criterio con fuente y cita verificables."
}
```

## Rechazo con reintentos agotados

| Campo | Valor |
|---|---|
| Estado | Requiere revisión especializada |
| ¿Válida? | no |
| Intentos | 3 |
| Contingencia | sí |
| Proveedor | guionizado-rechazo |

Errores registrados:

```text
Intento 1 · HASH_NO_COINCIDE [fuente.sha256]: El SHA-256 no coincide con el documento fuente registrado.
Intento 1 · CITA_NO_ENCONTRADA [cita]: La cita no aparece textualmente en el fragmento citado.
Intento 2 · HASH_NO_COINCIDE [fuente.sha256]: El SHA-256 no coincide con el documento fuente registrado.
Intento 2 · CITA_NO_ENCONTRADA [cita]: La cita no aparece textualmente en el fragmento citado.
Intento 3 · HASH_NO_COINCIDE [fuente.sha256]: El SHA-256 no coincide con el documento fuente registrado.
Intento 3 · CITA_NO_ENCONTRADA [cita]: La cita no aparece textualmente en el fragmento citado.
```

## Respuesta válida aceptada

```json
{
  "requisito_id": "RQ-04",
  "estado_propuesto": "Cumple",
  "evidencia_encontrada": true,
  "fuente": {
    "documento_id": 9,
    "archivo": "Presupuesto.xlsx",
    "ubicacion": "Hoja:Resumen!A3:E3",
    "sha256": "97caacf2815ce2b63afd16f7ff3dabcc57fde3f408dc61e343374bbdd965ec2a"
  },
  "cita": "A3=Ítem | B3=Partida | C3=Metrado | D3=Precio unitario | E3=Parcial",
  "observacion_preliminar": "Propuesta construida desde la evidencia recuperada.",
  "requiere_revision_especializada": false,
  "motivo": "La evidencia directa cubre el criterio con fuente y cita verificables."
}
```

## Reintento con respuesta corregida

Se usó un proveedor guionizado con `[respuesta inválida, respuesta válida]`.

| Campo | Valor |
|---|---|
| Estado | Cumple |
| ¿Válida? | sí |
| Intentos | 2 |
| Proveedor | guionizado-reintento |
| Fuente | Presupuesto.xlsx |

## Criterio de salida cubierto

- [x] Una respuesta con hash o cita falsos nunca se acepta como conclusión.
- [x] Los errores del contrato se conservan para auditoría.
- [x] El reintento se detiene en cuanto la respuesta cumple el contrato.
