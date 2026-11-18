# Evidencia 08 — Ensayo de sustentación (10 minutos)

## Estructura

| Minuto | Bloque | Idea clave | Diapositiva |
|---:|---|---|---|
| 0–1 | Problema y usuario | Revisión manual, dispersa y difícil de auditar | 2 |
| 1–2 | Solución y valor | Evidencia verificable + decisión humana + avance | 3 |
| 2–3 | Arquitectura | Streamlit, SQLite, extractores, contrato, exportadores | 4 |
| 3–5 | Demo | Carga, evidencia, decisión, exportación | 5–6 |
| 5–6 | Pruebas | 16 casos mapeados a CA | 7 |
| 6–7 | Resultados | 39% de avance, 88.6% de cumplimiento, 0 «No cumple» | 8 |
| 7–8 | Métricas | Línea base estimada vs. sistema | 9 |
| 8–9 | Seguridad y límites | Roles demo, sin IA real, feedback pendiente | 10–11 |
| 9–10 | Cierre | Próximos pasos y preguntas | 12–14 |

## Preguntas esperadas y respuesta breve

1. **¿La IA decide?** No. Propone; la persona acepta, modifica o descarta.
2. **¿Qué pasa si no hay evidencia?** «No se encontró información», nunca «No cumple».
3. **¿Cómo se evita inventar fuentes?** Contrato JSON con archivo, hash y cita;
   una respuesta que no coincide se rechaza.
4. **¿Cómo se mide el avance?** `Σ(peso × factor) / peso total`, solo con decisión.
5. **¿Qué falta para producción?** Identidad real, plantilla oficial, feedback y
   validación con especialistas.

## Checklist de ensayo

- [x] Guion y tiempos definidos.
- [x] PPT de 14 diapositivas y 9 secciones.
- [x] Demo reproducible con un comando.
- [x] Preguntas difíciles preparadas.
- [ ] Ensayo cronometrado con el equipo (pendiente de ejecución presencial).

## Criterio de salida cubierto

- [x] El equipo puede explicar decisiones, límites y próximos pasos.
- [x] La sustentación cabe en 10 minutos.
- [ ] Ensayo presencial cronometrado (acción del equipo).
