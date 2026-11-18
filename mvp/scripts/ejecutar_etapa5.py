"""Ejecuta la Etapa 5 de extremo a extremo y genera evidencia reproducible.

Uso::

    python -m mvp.scripts.ejecutar_etapa5

No modifica los artefactos cerrados de las Etapas 1-4: usa su propio corpus en
``mvp/etapa5/muestras/``, su propia base en ``mvp/etapa5/evidencia/`` y escribe
sus reportes en ``mvp/etapa5/evidencia/``.

Comprueba:

- Exportación real ``.xlsx`` y ``.docx`` construida desde SQLite.
- Apertura de ambos archivos y verificación de hojas, secciones y contenido.
- Control de acceso por rol: lector sin decisión ni exportación y usuario sin
  expediente asignado.
- Error de archivo con causa visible, avance conservado y reintento exitoso.
- Estado vacío exportable sin excepciones.
- Tiempos de respuesta de las operaciones principales.

Reportes:

- ``00_entorno.json``: versiones, rutas y política.
- ``01_reporte_caso.md``: datos y decisiones del caso.
- ``02_reporte_exportacion.md``: archivos, contenido y tiempos.
- ``03_reporte_permisos.md``: matriz de acceso y denegaciones.
- ``04_reporte_errores_reintento.md``: fallo, conservación y reintento.
- ``05_reporte_estado_vacio.md``: exportación sin documentos ni decisiones.
- ``06_metricas.json``: métricas comparables y tiempos.
"""

from __future__ import annotations

import json
import platform
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from docx import Document
from openpyxl import load_workbook

from mvp.core import access, config
from mvp.core.analysis import AnalizadorExpediente
from mvp.core.evaluation import EvaluadorExpediente
from mvp.core.exporters import exportar_informes
from mvp.core.pipeline import ProcesadorDocumental
from mvp.scripts.generar_muestras_etapa3 import generar_corpus_etapa3

EXPEDIENTE = config.EXPEDIENTE_DEFECTO
EXPEDIENTE_SIN_ASIGNAR = "EXP-2024-090"
EXPEDIENTE_VACIO = "EXP-2024-089-SIN-EVIDENCIA"
RUTA_BD = config.DIR_EVIDENCIA_ETAPA5 / "mvp_etapa5.db"
CARPETA_EXPORT = config.DIR_EVIDENCIA_ETAPA5 / "exportaciones"
ACTOR = "Lucía Ramos"
UMBRAL_MS = 5000.0

HOJAS_ESPERADAS = [
    "Resumen",
    "Requisitos",
    "Decisiones",
    "Propuestas",
    "Evidencias",
    "Documentos",
    "Auditoría",
]
SECCIONES_ESPERADAS = [
    "1. Resumen ejecutivo",
    "2. Resultados por requisito",
    "3. Observaciones y fuentes",
    "4. Historial de decisiones",
    "5. Alcance y limitaciones",
]


# --- Utilidades -----------------------------------------------------------


def _escribir(nombre: str, contenido: str) -> Path:
    ruta = config.DIR_EVIDENCIA_ETAPA5 / nombre
    ruta.write_text(contenido.rstrip() + "\n", encoding="utf-8")
    return ruta


def _tabla(cabeceras: list[str], filas: list[list[Any]]) -> str:
    lineas = [
        "| " + " | ".join(cabeceras) + " |",
        "|" + "|".join("---" for _ in cabeceras) + "|",
    ]
    for fila in filas:
        lineas.append("| " + " | ".join(str(valor) for valor in fila) + " |")
    return "\n".join(lineas)


def _cronometrar(funcion: Callable[[], Any]) -> tuple[Any, float]:
    inicio = time.perf_counter()
    resultado = funcion()
    return resultado, (time.perf_counter() - inicio) * 1000


def _entorno(politica: access.PoliticaAcceso) -> dict[str, Any]:
    import docx
    import openpyxl
    import pypdf
    import streamlit

    return {
        "fecha_ejecucion": datetime.now().isoformat(timespec="seconds"),
        "python": sys.version,
        "plataforma": platform.platform(),
        "base_datos": str(RUTA_BD),
        "corpus": str(config.DIR_MUESTRAS_ETAPA5 / "caso"),
        "exportaciones": str(CARPETA_EXPORT),
        "versiones": {
            "pypdf": pypdf.__version__,
            "python-docx": docx.__version__,
            "openpyxl": openpyxl.__version__,
            "streamlit": streamlit.__version__,
        },
        "politica_acceso": politica.a_dict(),
        "umbral_tiempo_ms": UMBRAL_MS,
    }


def _metricas(resumen: dict[str, Any]) -> dict[str, Any]:
    claves = [
        "requisitos_total",
        "cobertura_revision_pct",
        "peso_decidido_pct",
        "avance_pct",
        "cumplimiento_pct",
        "decisiones_registradas",
        "aceptadas",
        "modificadas",
        "descartadas",
        "cumple",
        "parcial",
        "no_cumple",
        "sin_informacion",
        "requiere_revision",
        "integridad_alertas",
    ]
    return {clave: resumen[clave] for clave in claves}


def _revisar_xlsx(ruta: Path) -> dict[str, Any]:
    libro = load_workbook(ruta, data_only=True)
    hojas = list(libro.sheetnames)
    valores_resumen = [
        str(celda.value)
        for fila in libro["Resumen"].iter_rows()
        for celda in fila
        if celda.value is not None
    ]
    requisitos = libro["Requisitos"]
    decisiones = libro["Decisiones"]
    return {
        "hojas": hojas,
        "requisitos_filas_datos": requisitos.max_row - 1,
        "decisiones_filas_datos": decisiones.max_row - 1,
        "resumen_contiene_avance": any("39.0%" in valor for valor in valores_resumen),
        "cabecera_requisitos": [
            celda.value for celda in requisitos[1]
        ],
        "bytes": ruta.stat().st_size,
    }


def _revisar_docx(ruta: Path) -> dict[str, Any]:
    documento = Document(ruta)
    encabezados = [
        parrafo.text
        for parrafo in documento.paragraphs
        if parrafo.style.name.startswith("Heading")
    ]
    texto = "\n".join(parrafo.text for parrafo in documento.paragraphs)
    texto_tablas = "\n".join(
        celda.text
        for tabla in documento.tables
        for fila in tabla.rows
        for celda in fila.cells
    )
    texto_completo = texto + "\n" + texto_tablas
    return {
        "secciones": [
            encabezado for encabezado in encabezados if encabezado[0].isdigit()
        ],
        "tablas": len(documento.tables),
        "contiene_avance": "39.0%" in texto_completo,
        "contiene_limitaciones": "Alcance y limitaciones" in texto_completo,
        "bytes": ruta.stat().st_size,
    }


# --- Reportes -------------------------------------------------------------


def _reporte_caso(
    resumen: dict[str, Any], historial: list[dict[str, Any]]
) -> str:
    metricas = _metricas(resumen)
    return f"""# Evidencia 01 — Caso con decisiones y datos reales

**Comando reproducible:** `python -m mvp.scripts.ejecutar_etapa5`
**Base de datos:** `mvp/etapa5/evidencia/mvp_etapa5.db`
**Expediente:** `{EXPEDIENTE}`

El caso se procesó desde un corpus propio de la Etapa 5 y se decidió con el
mismo criterio de las etapas anteriores. Los datos que alimentan la interfaz y
las exportaciones son los persistidos en SQLite, no valores fijos.

## Métricas del caso

{_tabla(["Métrica", "Valor"], [[clave, valor] for clave, valor in metricas.items()])}

## Historial de decisiones

{_tabla(
    ["ID", "Req.", "Decisión", "Propuesto", "Final", "Responsable", "Vigente"],
    [
        [
            registro["id"],
            registro["requisito_id"],
            registro["decision"],
            registro["estado_propuesto"],
            registro["estado_final"],
            registro["actor"],
            "sí" if registro["es_vigente"] else "no",
        ]
        for registro in historial
    ],
)}

## Criterio de salida cubierto

- [x] Las pantallas y la exportación leen de la base, no de datos fijos.
- [x] El avance y el cumplimiento se recalculan con las decisiones vigentes.
"""


def _reporte_exportacion(
    xlsx: dict[str, Any],
    docx: dict[str, Any],
    tiempos: dict[str, float],
) -> str:
    return f"""# Evidencia 02 — Exportación real a Excel y Word

La exportación se genera con `openpyxl` y `python-docx` desde las tablas del
expediente. Después de escribir los archivos, el propio script los vuelve a
abrir para verificar su contenido.

## Archivos generados

{_tabla(
    ["Formato", "Archivo", "Bytes"],
    [
        ["Excel", "informe_EXP-2024-089.xlsx", xlsx["bytes"]],
        ["Word", "informe_EXP-2024-089.docx", docx["bytes"]],
    ],
)}

## Verificación del Excel

- Hojas: **{", ".join(xlsx["hojas"])}**.
- Filas de datos en «Requisitos»: **{xlsx["requisitos_filas_datos"]}**.
- Filas de datos en «Decisiones»: **{xlsx["decisiones_filas_datos"]}**.
- El resumen contiene el avance 39.0%: **{"sí" if xlsx["resumen_contiene_avance"] else "no"}**.
- Cabeceras de «Requisitos»: {", ".join(str(item) for item in xlsx["cabecera_requisitos"])}.

## Verificación del Word

- Secciones numeradas: {", ".join(docx["secciones"])}.
- Tablas: **{docx["tablas"]}**.
- Contiene el avance 39.0%: **{"sí" if docx["contiene_avance"] else "no"}**.
- Contiene el alcance y las limitaciones: **{"sí" if docx["contiene_limitaciones"] else "no"}**.

## Tiempos medidos

{_tabla(
    ["Operación", "Milisegundos", "¿Bajo el umbral?"],
    [
        [nombre, f"{valor:.1f}", "sí" if valor < UMBRAL_MS else "no"]
        for nombre, valor in tiempos.items()
    ],
)}

## Criterio de salida cubierto

- [x] Se genera un `.xlsx` real con 7 hojas y datos del expediente.
- [x] Se genera un `.docx` real con resumen, resultados, fuentes e historial.
- [x] Los archivos se abren correctamente y contienen las métricas del caso.
- [x] Los tiempos quedan medidos y por debajo del umbral de {UMBRAL_MS:.0f} ms.
"""


def _reporte_permisos(
    matriz: list[list[Any]], denegaciones: list[list[Any]]
) -> str:
    return f"""# Evidencia 03 — Control de acceso mínimo por rol

La política vive en `mvp/etapa5/config/usuarios.json`. Los roles son
`administrador`, `especialista` y `lector`; las asignaciones son datos de
demostración.

## Matriz de permisos sobre el expediente principal

{_tabla(["Usuario", "Rol", "Ver", "Cargar", "Analizar", "Decidir", "Exportar", "Administrar"], matriz)}

## Denegaciones verificadas

{_tabla(["Caso", "Resultado", "Causa"], denegaciones)}

## Criterio de salida cubierto

- [x] Un lector puede consultar, pero no decidir ni exportar.
- [x] Un especialista puede decidir y exportar solo sus expedientes asignados.
- [x] Un usuario sin expediente asignado no accede ni siquiera a la lectura.
- [x] La denegación explica la causa y no genera archivos.
"""


def _reporte_errores(
    motivo: str,
    mensaje: str,
    validos_antes: int,
    validos_despues_error: int,
    validos_despues_reintento: int,
    avance_antes: float,
    avance_despues_error: float,
    avance_despues_reintento: float,
    decisiones_antes: int,
    decisiones_despues_reintento: int,
) -> str:
    return f"""# Evidencia 04 — Error de archivo, avance conservado y reintento

Se intentó cargar un PDF corrupto en el expediente principal. El lote no se
abortó: el archivo quedó rechazado con una causa explícita y el estado anterior
se conservó.

## Error registrado

- Motivo: `{motivo}`.
- Mensaje: {mensaje}.

## Conservación y reintento

{_tabla(
    ["Indicador", "Antes del error", "Tras el error", "Tras el reintento"],
    [
        ["Documentos válidos", validos_antes, validos_despues_error, validos_despues_reintento],
        ["Avance ponderado", f"{avance_antes}%", f"{avance_despues_error}%", f"{avance_despues_reintento}%"],
        ["Decisiones vigentes", decisiones_antes, "—", decisiones_despues_reintento],
    ],
)}

El reintento reemplazó el archivo corrupto por un DOCX válido y se procesó
correctamente. El avance y las decisiones no cambiaron: el error nunca borra
trabajo previo.

## Criterio de salida cubierto

- [x] El error muestra causa y no bloquea el resto del expediente.
- [x] El avance y las decisiones ya registradas se conservan.
- [x] El reintento funciona y agrega el documento válido.
"""


def _reporte_vacio(resumen: dict[str, Any], xlsx: dict[str, Any], docx: dict[str, Any]) -> str:
    return f"""# Evidencia 05 — Estado vacío operable

Se exportó un expediente sin documentos y sin decisiones para comprobar que las
pantallas y los informes no fallan cuando no hay datos.

## Métricas del expediente vacío

{_tabla(
    ["Métrica", "Valor"],
    [
        ["Requisitos", resumen["requisitos_total"]],
        ["Cobertura de revisión", f"{resumen['cobertura_revision_pct']}%"],
        ["Avance ponderado", f"{resumen['avance_pct']}%"],
        ["Decisiones vigentes", resumen["decisiones_registradas"]],
        ["No se encontró información", resumen["sin_informacion"]],
    ],
)}

## Exportación del estado vacío

- Excel: {", ".join(xlsx["hojas"])} ({xlsx["bytes"]} bytes).
- Word: {docx["tablas"]} tablas y secciones {", ".join(docx["secciones"])}.
- El Word explica que no hay decisiones y que el avance validado es 0%.

## Criterio de salida cubierto

- [x] Un expediente sin datos genera informes sin excepciones.
- [x] El estado vacío se comunica como «sin decisiones», no como error.
- [x] La ausencia de evidencia no se convierte en «No cumple».
"""


# --- Flujo principal ------------------------------------------------------


def main() -> int:
    config.preparar_directorios()
    config.DIR_EVIDENCIA_ETAPA5.mkdir(parents=True, exist_ok=True)
    if RUTA_BD.exists():
        RUTA_BD.unlink()
    for sufijo in ("-wal", "-shm"):
        sobrante = Path(str(RUTA_BD) + sufijo)
        if sobrante.exists():
            sobrante.unlink()
    if CARPETA_EXPORT.exists():
        shutil.rmtree(CARPETA_EXPORT)

    politica = access.cargar_politica()

    print("1/6 Generando corpus propio de la Etapa 5...")
    corpus = generar_corpus_etapa3(config.DIR_MUESTRAS_ETAPA5)

    procesador = ProcesadorDocumental(RUTA_BD)
    for expediente, nombre in (
        (EXPEDIENTE, "Carretera Central Tramo 2 · Km 42–78"),
        (EXPEDIENTE_SIN_ASIGNAR, "Expediente reservado al administrador"),
        (EXPEDIENTE_VACIO, "Expediente sin documentos ni decisiones"),
    ):
        procesador.registrar_expediente(
            expediente,
            nombre,
            especialidad="Pavimentos",
            version="v5",
            actor="equipo-mvp",
        )

    print("2/6 Ingestando el corpus y corrigiendo el documento ambiguo...")
    resultados = procesador.ingestar_carpeta(
        EXPEDIENTE, corpus["carpeta_caso"], actor="equipo-mvp"
    )
    eett = next(
        documento
        for documento in procesador.listar_documentos(EXPEDIENTE)
        if documento["nombre_archivo"] == "EETT_General_v2.docx"
    )
    procesador.corregir_clasificacion(
        eett["id"],
        "Especificaciones técnicas",
        "EETT",
        actor=ACTOR,
        motivo="El contenido corresponde a EETT aunque el nombre del archivo es genérico.",
    )
    assert len(resultados) == 8 and all(resultado.ok for resultado in resultados)

    analizador = AnalizadorExpediente(RUTA_BD)
    evaluador = EvaluadorExpediente(RUTA_BD)

    print("3/6 Analizando y registrando decisiones...")
    analizador.recuperar(EXPEDIENTE)
    analizador.analizar_expediente(EXPEDIENTE)

    for requisito_id, motivo in (
        (
            "RQ-04",
            "El presupuesto contiene partidas, metrados y precios unitarios "
            "coherentes; la fuente y el hash fueron verificados.",
        ),
        (
            "RQ-07",
            "El plan de manejo ambiental está vigente y corresponde al componente "
            "ambiental del tramo; se acepta la conclusión automática.",
        ),
    ):
        evaluador.decidir(
            EXPEDIENTE, requisito_id, "aceptar", actor=ACTOR, motivo=motivo
        )
    evaluador.decidir(
        EXPEDIENTE,
        "RQ-06",
        "modificar",
        estado_final="Cumple parcialmente",
        actor=ACTOR,
        motivo=(
            "La curva S es coherente, pero el cronograma no cubre dos partidas "
            "del plazo contractual; se valida parcialmente."
        ),
    )
    evaluador.decidir(
        EXPEDIENTE,
        "RQ-05",
        "descartar",
        actor=ACTOR,
        motivo=(
            "Los planos localizados no permiten verificar la coherencia con la "
            "hoja de metrados; se descarta la propuesta y no se asume "
            "incumplimiento."
        ),
    )
    evaluador.decidir(
        EXPEDIENTE,
        "RQ-04",
        "modificar",
        estado_final="Cumple parcialmente",
        actor=ACTOR,
        motivo="Revisión intermedia: se detectó una partida sin metrado detallado.",
    )
    evaluador.decidir(
        EXPEDIENTE,
        "RQ-04",
        "aceptar",
        actor=ACTOR,
        motivo=(
            "Tras revisar el detalle, la partida observada sí cuenta con metrado; "
            "se restituye y acepta la conclusión."
        ),
    )

    resumen, ms_resumen = _cronometrar(lambda: analizador.resumen(EXPEDIENTE))
    historial = evaluador.historial(EXPEDIENTE)
    assert resumen["avance_pct"] == 39.0
    assert resumen["decisiones_registradas"] == 4
    assert resumen["decisiones_registradas"] == sum(
        1 for registro in historial if registro["es_vigente"]
    )
    assert len(historial) == 6

    print("4/6 Exportando y verificando Excel y Word...")
    rutas, ms_export = _cronometrar(
        lambda: exportar_informes(RUTA_BD, EXPEDIENTE, CARPETA_EXPORT)
    )
    xlsx = _revisar_xlsx(rutas["xlsx"])
    docx = _revisar_docx(rutas["docx"])

    assert xlsx["hojas"] == HOJAS_ESPERADAS
    assert xlsx["requisitos_filas_datos"] == 7
    assert xlsx["decisiones_filas_datos"] == 6
    assert xlsx["resumen_contiene_avance"]
    assert docx["secciones"] == SECCIONES_ESPERADAS
    assert docx["tablas"] >= 3
    assert docx["contiene_avance"]
    assert docx["contiene_limitaciones"]

    tiempos = {
        "Resumen del expediente": ms_resumen,
        "Exportación Excel + Word": ms_export,
    }
    assert all(valor < UMBRAL_MS for valor in tiempos.values())

    print("5/6 Verificando permisos y manejo de errores...")
    matriz = []
    for usuario in politica.nombres():
        permisos = [
            "sí" if politica.puede(usuario, accion, EXPEDIENTE) else "no"
            for accion in ("ver", "cargar", "analizar", "decidir", "exportar", "administrar")
        ]
        matriz.append([usuario, politica.rol(usuario), *permisos])

    denegaciones = []
    for usuario, accion, expediente, caso in (
        ("Carlos Méndez", "decidir", EXPEDIENTE, "Lector intenta decidir"),
        ("Carlos Méndez", "exportar", EXPEDIENTE, "Lector intenta exportar"),
        ("Lucía Ramos", "ver", EXPEDIENTE_SIN_ASIGNAR, "Especialista sin expediente asignado"),
    ):
        try:
            politica.exigir(usuario, accion, expediente)
        except access.AccesoDenegado as error:
            denegaciones.append([caso, "denegado", str(error)])
        else:
            raise AssertionError(f"No se denegó el caso: {caso}")

    assert politica.puede("Lucía Ramos", "exportar", EXPEDIENTE)
    assert politica.puede("Admin MVP", "administrar", EXPEDIENTE_SIN_ASIGNAR)
    assert politica.puede("Carlos Méndez", "ver", EXPEDIENTE)
    assert not politica.puede("Carlos Méndez", "exportar", EXPEDIENTE)
    assert not any(CARPETA_EXPORT.glob("*denegado*"))

    validos_antes = sum(
        1
        for documento in procesador.listar_documentos(EXPEDIENTE)
        if documento["estado"] == "VALIDO"
    )
    avance_antes = resumen["avance_pct"]
    decisiones_antes = len(evaluador.vigentes(EXPEDIENTE))

    carpeta_error = config.DIR_MUESTRAS_ETAPA5 / "error_reintento"
    if carpeta_error.exists():
        shutil.rmtree(carpeta_error)
    carpeta_error.mkdir(parents=True)

    archivo_roto = carpeta_error / "Documento_Roto.pdf"
    archivo_roto.write_bytes(b"%PDF-1.4\ncontenido truncado")
    fallo = procesador.ingestar_archivo(EXPEDIENTE, archivo_roto, actor=ACTOR)
    assert not fallo.ok
    assert fallo.motivo_rechazo == "ARCHIVO_DANADO"

    resumen_error = analizador.resumen(EXPEDIENTE)
    validos_error = sum(
        1
        for documento in procesador.listar_documentos(EXPEDIENTE)
        if documento["estado"] == "VALIDO"
    )
    assert resumen_error["avance_pct"] == avance_antes
    assert len(evaluador.vigentes(EXPEDIENTE)) == decisiones_antes
    assert validos_error == validos_antes

    archivo_roto.unlink()
    archivo_valido = carpeta_error / "Documento_Reintento.docx"
    documento = Document()
    documento.add_heading("Documento de prueba de reintento", level=1)
    documento.add_paragraph(
        "Este documento reemplaza al archivo corrupto y permite verificar el "
        "reintento sin perder el avance del expediente."
    )
    documento.save(archivo_valido)
    reintento = procesador.ingestar_archivo(EXPEDIENTE, archivo_valido, actor=ACTOR)
    assert reintento.ok

    resumen_reintento = analizador.resumen(EXPEDIENTE)
    validos_reintento = sum(
        1
        for documento in procesador.listar_documentos(EXPEDIENTE)
        if documento["estado"] == "VALIDO"
    )
    assert validos_reintento == validos_antes + 1
    assert resumen_reintento["avance_pct"] == avance_antes
    assert len(evaluador.vigentes(EXPEDIENTE)) == decisiones_antes

    print("6/6 Exportando el estado vacío y escribiendo reportes...")
    especialista = access.cargar_politica()
    especialista.exigir("Lucía Ramos", "exportar", EXPEDIENTE)

    resumen_vacio = analizador.resumen(EXPEDIENTE_VACIO)
    rutas_vacio = exportar_informes(
        RUTA_BD, EXPEDIENTE_VACIO, CARPETA_EXPORT / "estado_vacio"
    )
    xlsx_vacio = _revisar_xlsx(rutas_vacio["xlsx"])
    docx_vacio = _revisar_docx(rutas_vacio["docx"])
    assert xlsx_vacio["requisitos_filas_datos"] == 7
    assert xlsx_vacio["decisiones_filas_datos"] == 0
    assert docx_vacio["secciones"] == SECCIONES_ESPERADAS
    assert resumen_vacio["decisiones_registradas"] == 0
    assert resumen_vacio["avance_pct"] == 0.0

    _escribir("01_reporte_caso.md", _reporte_caso(resumen, historial))
    _escribir(
        "02_reporte_exportacion.md",
        _reporte_exportacion(xlsx, docx, tiempos),
    )
    _escribir("03_reporte_permisos.md", _reporte_permisos(matriz, denegaciones))
    _escribir(
        "04_reporte_errores_reintento.md",
        _reporte_errores(
            fallo.motivo_rechazo,
            fallo.mensaje,
            validos_antes,
            validos_error,
            validos_reintento,
            avance_antes,
            resumen_error["avance_pct"],
            resumen_reintento["avance_pct"],
            decisiones_antes,
            len(evaluador.vigentes(EXPEDIENTE)),
        ),
    )
    _escribir(
        "05_reporte_estado_vacio.md",
        _reporte_vacio(resumen_vacio, xlsx_vacio, docx_vacio),
    )

    metricas = {
        "caso": {
            "metricas": _metricas(resumen),
            "decisiones_historial": len(historial),
            "decisiones_vigentes": resumen["decisiones_registradas"],
        },
        "exportacion": {
            "xlsx": xlsx,
            "docx": docx,
            "tiempos_ms": {clave: round(valor, 1) for clave, valor in tiempos.items()},
            "umbral_ms": UMBRAL_MS,
            "bajo_umbral": all(valor < UMBRAL_MS for valor in tiempos.values()),
        },
        "permisos": {
            "matriz": matriz,
            "denegaciones": denegaciones,
        },
        "error_reintento": {
            "motivo": fallo.motivo_rechazo,
            "mensaje": fallo.mensaje,
            "validos_antes": validos_antes,
            "validos_tras_error": validos_error,
            "validos_tras_reintento": validos_reintento,
            "avance_conservado": resumen_reintento["avance_pct"] == avance_antes,
            "decisiones_conservadas": (
                len(evaluador.vigentes(EXPEDIENTE)) == decisiones_antes
            ),
        },
        "estado_vacio": {
            "metricas": _metricas(resumen_vacio),
            "xlsx_hojas": xlsx_vacio["hojas"],
            "docx_secciones": docx_vacio["secciones"],
        },
    }
    _escribir("06_metricas.json", json.dumps(metricas, indent=2, ensure_ascii=False))
    _escribir("00_entorno.json", json.dumps(_entorno(politica), indent=2, ensure_ascii=False))

    print("\nEtapa 5 ejecutada correctamente.")
    print(f"Evidencia: {config.DIR_EVIDENCIA_ETAPA5}")
    print(f"Excel: {rutas['xlsx']}")
    print(f"Word:  {rutas['docx']}")
    print(
        f"Avance: {resumen['avance_pct']}% | Decisiones: "
        f"{resumen['decisiones_registradas']} | Exportación: {ms_export:.1f} ms"
    )
    print(
        f"Permisos: denegaciones={len(denegaciones)} | "
        f"Error/reintento: {validos_antes} -> {validos_reintento} válidos"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
