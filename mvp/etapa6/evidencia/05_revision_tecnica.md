# Evidencia 05 — Revisión técnica y feedback

## Revisión interna ejecutada

| Aspecto | Resultado |
|---|---|
| Flujo de extremo a extremo | ✅ ejecutado desde cero |
| Casos de prueba | ✅ 16/16 PASA |
| Exportación | ✅ XLSX y DOCX reabiertos y verificados |
| Seguridad mínima | ✅ 3 denegaciones con causa |
| Contingencia | ✅ resuelta manualmente |
| Integridad | ✅ fuente modificada bloquea decisión |
| Tiempos | ✅ medidos y bajo el umbral de 5000 ms |
| Video demo | ✅ 3:03, grabado sobre la app real |
| Documentación | ✅ README, ficha, PPT, guion y video |

## Hallazgos de la revisión interna

1. La validación humana sigue siendo el cuello de botella; el sistema acelera el
   trabajo mecánico, no la decisión técnica.
2. La política de acceso es de demostración; antes de producción requiere
   autenticación e identidad reales.
3. El proveedor determinista es suficiente para demostrar el contrato y la
   contingencia, pero no sustituye una evaluación semántica con IA real.
4. La exportación funciona con datos sintéticos; falta plantilla oficial y firma.

## Feedback de especialista externo

**Estado:** pendiente de una persona con rol de especialista.

Formulario preparado para la sesión:

| Pregunta | Respuesta |
|---|---|
| ¿La evidencia mostrada es suficiente para decidir? | |
| ¿Las fuentes y ubicaciones son verificables? | |
| ¿El estado «Requiere revisión especializada» está bien usado? | |
| ¿El avance ponderado refleja el trabajo real? | |
| ¿El informe Excel/Word es usable? | |
| ¿Qué cambiaría antes de producción? | |
| Nombre / rol / fecha | |

> No se registra un feedback ficticio. La sesión con el especialista debe
> completar esta tabla antes de la sustentación final.

## Criterio de salida cubierto

- [x] Existe revisión técnica interna documentada.
- [x] Existe formulario de feedback listo para el especialista.
- [ ] Feedback externo firmado (pendiente de una persona).
