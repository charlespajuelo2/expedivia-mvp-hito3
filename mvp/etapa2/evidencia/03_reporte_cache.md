# Evidencia 03 — Caché documental por SHA-256

**Comando reproducible:** `python -m mvp.scripts.ejecutar_etapa2`

La caché usa la clave `SHA-256 + versión del extractor`. Si el archivo no cambia,
la segunda carga reutiliza la extracción y no vuelve a leer el contenido.

| Archivo | SHA-256 | Caché 1.ª | ms 1.ª | Caché 2.ª | ms 2.ª | Hash igual |
|---|---|---|---|---|---|---|
| EETT_General_v2.docx | 88f3898403e5 | no | 32 | sí | 8 | sí |
| Estudio_Suelos_Lab.xlsx | 7dfe84d108a5 | no | 25 | sí | 7 | sí |
| Memoria_Calculo_Pavimentos.docx | 7195e48bf866 | no | 26 | sí | 8 | sí |
| Planos_PL-01_PL-08.pdf | 82594d969d3a | no | 148 | sí | 8 | sí |
| Presupuesto.xlsx | 36985746738b | no | 22 | sí | 8 | sí |
| TDR_Carretera_Central_v3.pdf | 227583f65356 | no | 45 | sí | 8 | sí |

## Comparación

| Métrica | Primera carga | Segunda carga |
|---|---:|---:|
| Archivos | 6 | 6 |
| Aciertos de caché | 0 | 6 |
| Tiempo total | 298 ms | 47 ms |
| Reducción de tiempo | — | 84.2% |

## Criterio de salida cubierto

- [x] Dos cargas del mismo archivo producen el mismo hash y reutilizan caché.
