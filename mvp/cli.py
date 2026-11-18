"""CLI del MVP para las Etapas 2, 3 y 4.

Ejemplos::

    python -m mvp.cli init
    python -m mvp.cli seed
    python -m mvp.cli ingest --expediente EXP-2024-089 --carpeta mvp/etapa3/muestras/caso
    python -m mvp.cli list --expediente EXP-2024-089
    python -m mvp.cli extract --documento 1
    python -m mvp.cli correct --documento 5 --tipo "Especificaciones técnicas" --componente EETT --motivo "Revisión del especialista"
    python -m mvp.cli evidence --expediente EXP-2024-089
    python -m mvp.cli analyze --expediente EXP-2024-089 --proveedor reglas
    python -m mvp.cli integrity --expediente EXP-2024-089
    python -m mvp.cli manual --expediente EXP-2024-089 --requisito RQ-02 --estado "Requiere revisión especializada" --motivo "Falta CV" --actor "Lucía Ramos"
    python -m mvp.cli decide --expediente EXP-2024-089 --requisito RQ-04 --decision aceptar --motivo "Fuente verificada" --actor "Lucía Ramos"
    python -m mvp.cli decide --expediente EXP-2024-089 --requisito RQ-06 --decision modificar --estado-final "Cumple parcialmente" --motivo "El cronograma no cubre todo el plazo" --actor "Lucía Ramos"
    python -m mvp.cli history --expediente EXP-2024-089
    python -m mvp.cli progress --expediente EXP-2024-089
    python -m mvp.cli proposals --expediente EXP-2024-089
    python -m mvp.cli metrics --expediente EXP-2024-089
    python -m mvp.cli audit
    python -m mvp.cli access
    python -m mvp.cli access --usuario "Carlos Méndez" --accion decidir --expediente EXP-2024-089
    python -m mvp.cli export --expediente EXP-2024-089 --usuario "Lucía Ramos"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .core import access, config, db
from .core.ai_service import (
    ProveedorFallido,
    ProveedorOpenAICompatible,
    ProveedorReglas,
)
from .core.analysis import AnalizadorExpediente
from .core.evaluation import EvaluadorExpediente, historial
from .core.exporters import exportar_informes
from .core.integrity import (
    listar_eventos_integridad,
    verificar_documento,
    verificar_expediente,
)
from .core.pipeline import ProcesadorDocumental


def _ancho(valor: object, limite: int) -> str:
    texto = "" if valor is None else str(valor)
    return texto if len(texto) <= limite else texto[: limite - 1] + "~"


def _imprimir_tabla(filas: list[dict], columnas: list[tuple[str, str, int]]) -> None:
    if not filas:
        print("(sin registros)")
        return
    cabecera = " | ".join(titulo.ljust(ancho) for _, titulo, ancho in columnas)
    print(cabecera)
    print("-" * len(cabecera))
    for fila in filas:
        print(
            " | ".join(
                _ancho(fila.get(clave), ancho).ljust(ancho)
                for clave, _, ancho in columnas
            )
        )


def _registrar_si_falta(procesador: ProcesadorDocumental, expediente: str) -> None:
    existentes = {e["id"] for e in procesador.listar_expedientes()}
    if expediente not in existentes:
        procesador.registrar_expediente(
            expediente, f"Expediente {expediente}", actor="cli"
        )


def _comando_init(args: argparse.Namespace) -> int:
    config.preparar_directorios()
    ruta = db.inicializar(args.bd or config.RUTA_BD)
    print(f"Base de datos inicializada: {ruta}")
    print(json.dumps(config.rutas_datos(), indent=2, ensure_ascii=False))
    return 0


def _comando_seed(args: argparse.Namespace) -> int:
    procesador = ProcesadorDocumental(args.bd)
    if not config.RUTA_SEMILLA.exists():
        print(f"No se encontró la semilla: {config.RUTA_SEMILLA}")
        return 1
    datos = json.loads(config.RUTA_SEMILLA.read_text(encoding="utf-8"))
    expediente = datos["expediente"]
    procesador.registrar_expediente(
        expediente["id"],
        expediente["nombre"],
        especialidad=expediente.get("especialidad", ""),
        version=expediente.get("version", ""),
        actor=args.actor,
    )
    print(f"Expediente registrado: {expediente['id']} - {expediente['nombre']}")
    return 0


def _comando_ingest(args: argparse.Namespace) -> int:
    procesador = ProcesadorDocumental(args.bd)
    _registrar_si_falta(procesador, args.expediente)

    resultados = []
    if args.carpeta:
        resultados.extend(
            procesador.ingestar_carpeta(args.expediente, args.carpeta, actor=args.actor)
        )
    for archivo in args.archivo or []:
        resultados.append(procesador.ingestar_archivo(args.expediente, archivo, actor=args.actor))

    if not resultados:
        print("No se indicó --carpeta ni --archivo.")
        return 1

    for resultado in resultados:
        clasificacion = resultado.clasificacion
        print(
            f"[{'OK' if resultado.ok else 'RECHAZO'}] {resultado.nombre_archivo} "
            f"({resultado.formato}, {resultado.duracion_ms} ms, caché={'sí' if resultado.cache_hit else 'no'})"
        )
        if clasificacion:
            print(
                f"    tipo={clasificacion.tipo_documental} | componente={clasificacion.componente} "
                f"| confianza={clasificacion.confianza} | {clasificacion.estado}"
            )
        if not resultado.ok:
            print(f"    motivo={resultado.motivo_rechazo} | {resultado.mensaje}")
        for advertencia in resultado.advertencias:
            print(f"    aviso: {advertencia}")

    validos = sum(1 for r in resultados if r.ok)
    print(f"\nTotal: {len(resultados)} | válidos: {validos} | rechazados: {len(resultados) - validos}")
    return 0 if validos == len(resultados) else 2


def _comando_list(args: argparse.Namespace) -> int:
    procesador = ProcesadorDocumental(args.bd)
    documentos = procesador.listar_documentos(args.expediente)
    _imprimir_tabla(
        documentos,
        [
            ("id", "ID", 4),
            ("nombre_archivo", "Archivo", 34),
            ("estado", "Estado", 9),
            ("texto_recuperable", "Texto", 7),
            ("tipo_documental", "Tipo", 26),
            ("confianza", "Conf.", 5),
            ("estado_clasificacion", "Clasif.", 14),
            ("cache_hit", "Caché", 5),
        ],
    )
    resumen = procesador.resumen_procesamiento(args.expediente)
    print(
        f"\nDocumentos: {resumen['documentos_total']} | válidos: {resumen['validos']} | "
        f"rechazados: {resumen['rechazados']} | caché: {resumen['cache_hits']}"
    )
    return 0


def _comando_extract(args: argparse.Namespace) -> int:
    procesador = ProcesadorDocumental(args.bd)
    documento = procesador.obtener_documento(args.documento)
    if documento is None:
        print(f"No existe el documento {args.documento}.")
        return 1
    print(
        f"{documento['nombre_archivo']} | {documento['estado']} | "
        f"texto={documento.get('texto_recuperable')} | fragmentos={documento.get('fragmentos')}"
    )
    print(f"SHA-256: {documento.get('sha256')}")
    for advertencia in documento.get("advertencias", []):
        print(f"Aviso: {advertencia}")
    print()
    for fragmento in procesador.fragmentos_de(args.documento):
        print(f"[{fragmento['ubicacion']}] ({fragmento['tipo']})")
        print(fragmento["texto"][: args.limite])
        print()
    return 0


def _comando_correct(args: argparse.Namespace) -> int:
    procesador = ProcesadorDocumental(args.bd)
    documento = procesador.corregir_clasificacion(
        args.documento,
        args.tipo,
        args.componente,
        actor=args.actor,
        motivo=args.motivo,
    )
    print(
        f"Documento {documento['id']} corregido: "
        f"{documento['tipo_documental']} / {documento['componente']} "
        f"(confianza {documento['confianza']}, origen {documento['clasificacion_origen']})"
    )
    return 0


def _comando_metrics(args: argparse.Namespace) -> int:
    procesador = ProcesadorDocumental(args.bd)
    resumen = procesador.resumen_procesamiento(args.expediente)
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    return 0


def _comando_audit(args: argparse.Namespace) -> int:
    procesador = ProcesadorDocumental(args.bd)
    for registro in procesador.listar_auditoria(args.limite):
        print(
            f"{registro['ts']} | {registro['actor']} | {registro['accion']} | "
            f"{registro['entidad']}#{registro['entidad_id']} | "
            f"{json.dumps(registro['detalle'], ensure_ascii=False)[:160]}"
        )
    return 0


def _comando_report(args: argparse.Namespace) -> int:
    procesador = ProcesadorDocumental(args.bd)
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    csv_ruta = procesador.exportar_inventario_csv(
        args.expediente, salida / f"inventario_{args.expediente}.csv"
    )
    metricas = procesador.resumen_procesamiento(args.expediente)
    json_ruta = salida / f"metricas_{args.expediente}.json"
    json_ruta.write_text(
        json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Inventario: {csv_ruta}")
    print(f"Métricas:   {json_ruta}")
    return 0


def _comando_evidence(args: argparse.Namespace) -> int:
    analizador = AnalizadorExpediente(args.bd)
    requisitos = [args.requisito] if args.requisito else analizador.perfiles.ids()
    for requisito_id in requisitos:
        evidencias = analizador.recuperar(args.expediente, requisito_id)
        perfil = analizador.perfiles.requisito(requisito_id)
        print(
            f"\n{requisito_id} · {perfil.requisito} "
            f"(peso {perfil.peso_pct}%, {len(evidencias)} evidencias)"
        )
        _imprimir_tabla(
            [evidencia.a_dict() for evidencia in evidencias],
            [
                ("puntaje", "Puntaje", 7),
                ("archivo", "Archivo", 32),
                ("ubicacion", "Ubicación", 30),
                ("tipo_documental", "Tipo", 24),
                ("terminos", "Términos", 36),
            ],
        )
    return 0


def _proveedor_desde_args(args: argparse.Namespace):
    if args.proveedor == "openai":
        proveedor = ProveedorOpenAICompatible(max_intentos=args.max_intentos)
        if not proveedor.api_key:
            print(
                "No hay API key configurada. Defina MVP_IA_API_KEY o use "
                "--proveedor reglas."
            )
            return None
        return proveedor
    if args.proveedor == "fallido":
        return ProveedorFallido()
    return ProveedorReglas()


def _comando_analyze(args: argparse.Namespace) -> int:
    proveedor = _proveedor_desde_args(args)
    if proveedor is None:
        return 1
    analizador = AnalizadorExpediente(
        args.bd, proveedor=proveedor, max_intentos=args.max_intentos
    )
    if args.requisito:
        resultados = [
            analizador.analizar_requisito(
                args.expediente,
                args.requisito,
                proveedor=proveedor,
                recuperar=not args.sin_recuperar,
            )
        ]
    else:
        resultados = analizador.analizar_expediente(
            args.expediente,
            proveedor=proveedor,
            recuperar=not args.sin_recuperar,
        )

    for resultado in resultados:
        fuente = (resultado.propuesta or {}).get("fuente") or {}
        print(
            f"\n{resultado.requisito_id} · {resultado.estado} "
            f"| válida={'sí' if resultado.valida else 'no'} "
            f"| proveedor={resultado.proveedor} | intentos={resultado.intentos} "
            f"| {resultado.duracion_ms} ms"
        )
        if fuente:
            print(
                f"    fuente: {fuente.get('archivo')} · {fuente.get('ubicacion')} "
                f"| sha256={str(fuente.get('sha256'))[:12]}…"
            )
        cita = (resultado.propuesta or {}).get("cita")
        if cita:
            print(f"    cita: {cita[:180]}")
        for error in resultado.errores:
            print(f"    error: {error[:220]}")

    resumen = analizador.resumen(args.expediente)
    print(
        f"\nCobertura de revisión: {resumen['cobertura_revision_pct']}% | "
        f"Cumplimiento ponderado: {resumen['cumplimiento_pct']}% | "
        f"Propuestas válidas: {resumen['con_propuesta_valida']}/{resumen['requisitos_total']} | "
        f"Contingencias: {resumen['contingencias']} | "
        f"Alertas de integridad: {resumen['integridad_alertas']}"
    )
    return 0


def _comando_integrity(args: argparse.Namespace) -> int:
    if args.documento:
        resultado = verificar_documento(args.bd or config.RUTA_BD, args.documento)
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        return 0
    resumen = verificar_expediente(args.bd or config.RUTA_BD, args.expediente)
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    return 0 if resumen["requiere_atencion"] == 0 else 2


def _comando_manual(args: argparse.Namespace) -> int:
    analizador = AnalizadorExpediente(args.bd)
    evaluacion = analizador.registrar_evaluacion_manual(
        args.expediente,
        args.requisito,
        args.estado,
        args.motivo,
        actor=args.actor,
        evidencia_id=args.evidencia_id,
    )
    print(
        f"Evaluación manual registrada: {evaluacion['requisito_id']} → "
        f"{evaluacion['estado']} ({evaluacion['actor']})"
    )
    return 0


def _comando_proposals(args: argparse.Namespace) -> int:
    analizador = AnalizadorExpediente(args.bd)
    propuestas = analizador.propuestas(
        args.expediente,
        args.requisito,
        solo_validas=not args.todas,
    )
    _imprimir_tabla(
        propuestas,
        [
            ("id", "ID", 4),
            ("requisito_id", "Req.", 7),
            ("proveedor", "Proveedor", 16),
            ("estado_propuesto", "Estado", 30),
            ("archivo", "Archivo", 28),
            ("ubicacion", "Ubicación", 26),
            ("valida", "Válida", 7),
            ("integridad", "Integridad", 18),
        ],
    )
    return 0


def _comando_eventos(args: argparse.Namespace) -> int:
    eventos = listar_eventos_integridad(args.bd or config.RUTA_BD, args.expediente)
    _imprimir_tabla(
        eventos,
        [
            ("ts", "Fecha", 20),
            ("documento_id", "Doc.", 4),
            ("archivo", "Archivo", 30),
            ("estado", "Estado", 22),
            ("detalle", "Detalle", 40),
        ],
    )
    return 0


def _comando_decide(args: argparse.Namespace) -> int:
    evaluador = EvaluadorExpediente(args.bd)
    try:
        decision = evaluador.decidir(
            args.expediente,
            args.requisito,
            args.decision,
            actor=args.actor,
            motivo=args.motivo,
            estado_final=args.estado_final,
            propuesta_id=args.propuesta_id,
        )
    except ValueError as error:
        print(f"Error: {error}")
        return 1
    print(
        f"Decisión registrada: {decision['requisito_id']} · {decision['decision']} "
        f"| {decision['estado_propuesto']} → {decision['estado_final']} "
        f"| {decision['actor']} | {decision['creado_en']}"
    )
    return 0


def _comando_history(args: argparse.Namespace) -> int:
    registros = historial(args.bd, args.expediente, args.requisito, limite=args.limite)
    _imprimir_tabla(
        registros,
        [
            ("creado_en", "Fecha", 20),
            ("requisito_id", "Req.", 7),
            ("decision", "Decisión", 11),
            ("estado_propuesto", "Propuesto", 30),
            ("estado_final", "Final", 30),
            ("actor", "Responsable", 16),
            ("motivo", "Motivo", 44),
            ("es_vigente", "Vigente", 7),
        ],
    )
    return 0


def _comando_progress(args: argparse.Namespace) -> int:
    analizador = AnalizadorExpediente(args.bd)
    resumen = analizador.resumen(args.expediente)
    metricas = {
        clave: resumen[clave]
        for clave in (
            "expediente_id",
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
            "avance_formula",
        )
    }
    print(json.dumps(metricas, indent=2, ensure_ascii=False))
    print()
    _imprimir_tabla(
        resumen["requisitos"],
        [
            ("requisito_id", "Req.", 7),
            ("peso_pct", "Peso", 5),
            ("estado_propuesto", "Propuesto", 30),
            ("estado_efectivo", "Efectivo", 30),
            ("decision", "Decisión", 11),
            ("origen", "Origen", 14),
        ],
    )
    return 0


def _comando_access(args: argparse.Namespace) -> int:
    politica = access.cargar_politica(args.politica)
    if args.usuario:
        permitido = politica.puede(args.usuario, args.accion, args.expediente)
        print(
            json.dumps(
                {
                    "usuario": args.usuario,
                    "rol": politica.rol(args.usuario),
                    "accion": args.accion,
                    "expediente": args.expediente,
                    "permitido": permitido,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        if not permitido:
            try:
                politica.exigir(args.usuario, args.accion, args.expediente)
            except access.AccesoDenegado as error:
                print(f"Denegado: {error}")
        return 0 if permitido else 2
    print(json.dumps(politica.a_dict(), indent=2, ensure_ascii=False))
    return 0


def _comando_export(args: argparse.Namespace) -> int:
    politica = access.cargar_politica(args.politica)
    try:
        politica.exigir(args.usuario, "exportar", args.expediente)
    except access.AccesoDenegado as error:
        print(f"Acceso denegado: {error}")
        return 2
    if args.salida:
        salida = Path(args.salida)
    else:
        base = Path(args.bd) if args.bd else config.RUTA_BD
        salida = base.resolve().parent / "exportaciones"
    rutas = exportar_informes(args.bd, args.expediente, salida)
    print(f"Excel: {rutas['xlsx']}")
    print(f"Word:  {rutas['docx']}")
    return 0


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m mvp.cli",
        description="Procesamiento documental, evidencia, análisis y evaluación del MVP (Etapas 2-4).",
    )
    parser.add_argument("--bd", default=None, help="Ruta alternativa de la base SQLite.")
    sub = parser.add_subparsers(dest="comando", required=True)

    init = sub.add_parser("init", help="Crea directorios y base de datos.")
    init.set_defaults(func=_comando_init)

    seed = sub.add_parser("seed", help="Registra el expediente de la Etapa 1.")
    seed.add_argument("--actor", default="cli")
    seed.set_defaults(func=_comando_seed)

    ingest = sub.add_parser("ingest", help="Procesa una carpeta o archivos.")
    ingest.add_argument("--expediente", default=config.EXPEDIENTE_DEFECTO)
    ingest.add_argument("--carpeta")
    ingest.add_argument("--archivo", action="append", nargs="+")
    ingest.add_argument("--actor", default="cli")
    ingest.set_defaults(func=_comando_ingest)

    listar = sub.add_parser("list", help="Lista el inventario procesado.")
    listar.add_argument("--expediente", default=config.EXPEDIENTE_DEFECTO)
    listar.set_defaults(func=_comando_list)

    extract = sub.add_parser("extract", help="Muestra los fragmentos de un documento.")
    extract.add_argument("--documento", type=int, required=True)
    extract.add_argument("--limite", type=int, default=500)
    extract.set_defaults(func=_comando_extract)

    correct = sub.add_parser("correct", help="Corrige la clasificación de un documento.")
    correct.add_argument("--documento", type=int, required=True)
    correct.add_argument("--tipo", required=True)
    correct.add_argument("--componente", required=True)
    correct.add_argument("--motivo", required=True)
    correct.add_argument("--actor", default="especialista")
    correct.set_defaults(func=_comando_correct)

    metrics = sub.add_parser("metrics", help="Muestra métricas de procesamiento.")
    metrics.add_argument("--expediente", default=config.EXPEDIENTE_DEFECTO)
    metrics.set_defaults(func=_comando_metrics)

    audit = sub.add_parser("audit", help="Muestra la bitácora de auditoría.")
    audit.add_argument("--limite", type=int, default=40)
    audit.set_defaults(func=_comando_audit)

    report = sub.add_parser("report", help="Exporta inventario y métricas.")
    report.add_argument("--expediente", default=config.EXPEDIENTE_DEFECTO)
    report.add_argument("--salida", default=str(config.DIR_EVIDENCIA))
    report.set_defaults(func=_comando_report)

    # --- Etapa 3 -------------------------------------------------------
    evidence = sub.add_parser(
        "evidence", help="Recupera evidencia por requisito y la persiste."
    )
    evidence.add_argument("--expediente", default=config.EXPEDIENTE_DEFECTO)
    evidence.add_argument("--requisito", help="Limita la recuperación a un requisito.")
    evidence.set_defaults(func=_comando_evidence)

    analyze = sub.add_parser(
        "analyze", help="Analiza requisitos con el proveedor de IA y valida el contrato."
    )
    analyze.add_argument("--expediente", default=config.EXPEDIENTE_DEFECTO)
    analyze.add_argument("--requisito", help="Limita el análisis a un requisito.")
    analyze.add_argument(
        "--proveedor",
        choices=("reglas", "openai", "fallido"),
        default="reglas",
        help="Proveedor de IA (por defecto 'reglas', determinista y sin red).",
    )
    analyze.add_argument("--max-intentos", type=int, default=config.IA_MAX_INTENTOS)
    analyze.add_argument(
        "--sin-recuperar",
        action="store_true",
        help="Reutiliza la evidencia ya persistida en lugar de volver a recuperarla.",
    )
    analyze.set_defaults(func=_comando_analyze)

    integrity = sub.add_parser(
        "integrity", help="Verifica el hash de las fuentes y propaga el resultado."
    )
    integrity.add_argument("--expediente", default=config.EXPEDIENTE_DEFECTO)
    integrity.add_argument("--documento", type=int, help="Verifica un solo documento.")
    integrity.set_defaults(func=_comando_integrity)

    manual = sub.add_parser(
        "manual", help="Registra la evaluación manual de un requisito."
    )
    manual.add_argument("--expediente", default=config.EXPEDIENTE_DEFECTO)
    manual.add_argument("--requisito", required=True)
    manual.add_argument("--estado", required=True, choices=config.ESTADOS_REQUISITO)
    manual.add_argument("--motivo", required=True)
    manual.add_argument("--actor", required=True)
    manual.add_argument("--evidencia-id", type=int, default=None)
    manual.set_defaults(func=_comando_manual)

    proposals = sub.add_parser(
        "proposals", help="Lista las propuestas de IA registradas."
    )
    proposals.add_argument("--expediente", default=config.EXPEDIENTE_DEFECTO)
    proposals.add_argument("--requisito")
    proposals.add_argument(
        "--todas", action="store_true", help="Incluye también las propuestas inválidas."
    )
    proposals.set_defaults(func=_comando_proposals)

    eventos = sub.add_parser(
        "eventos", help="Lista los eventos de integridad de las fuentes."
    )
    eventos.add_argument("--expediente", default=config.EXPEDIENTE_DEFECTO)
    eventos.set_defaults(func=_comando_eventos)

    # --- Etapa 4 -------------------------------------------------------
    decide = sub.add_parser(
        "decide",
        help="Registra aceptar / modificar / descartar sobre la propuesta vigente.",
    )
    decide.add_argument("--expediente", default=config.EXPEDIENTE_DEFECTO)
    decide.add_argument("--requisito", required=True)
    decide.add_argument(
        "--decision", required=True, choices=("aceptar", "modificar", "descartar")
    )
    decide.add_argument(
        "--estado-final",
        help="Obligatorio al modificar; al aceptar se conserva el propuesto.",
    )
    decide.add_argument("--motivo", required=True)
    decide.add_argument("--actor", required=True)
    decide.add_argument(
        "--propuesta-id",
        type=int,
        default=None,
        help="Propuesta concreta; por defecto, la última propuesta válida.",
    )
    decide.set_defaults(func=_comando_decide)

    history = sub.add_parser(
        "history", help="Muestra el historial de decisiones con la propuesta original."
    )
    history.add_argument("--expediente", default=config.EXPEDIENTE_DEFECTO)
    history.add_argument("--requisito")
    history.add_argument("--limite", type=int, default=100)
    history.set_defaults(func=_comando_history)

    progress = sub.add_parser(
        "progress", help="Muestra cobertura, avance ponderado y estado por requisito."
    )
    progress.add_argument("--expediente", default=config.EXPEDIENTE_DEFECTO)
    progress.set_defaults(func=_comando_progress)

    # --- Etapa 5 -------------------------------------------------------
    acceso = sub.add_parser(
        "access", help="Muestra la política de acceso o verifica un permiso."
    )
    acceso.add_argument("--politica", default=None, help="Ruta del JSON de usuarios.")
    acceso.add_argument("--usuario", help="Usuario a verificar.")
    acceso.add_argument(
        "--accion", choices=access.ACCIONES, default="ver", help="Acción a verificar."
    )
    acceso.add_argument("--expediente", default=config.EXPEDIENTE_DEFECTO)
    acceso.set_defaults(func=_comando_access)

    export = sub.add_parser(
        "export", help="Genera el informe real en Excel y Word desde SQLite."
    )
    export.add_argument("--expediente", default=config.EXPEDIENTE_DEFECTO)
    export.add_argument("--usuario", default="Admin MVP")
    export.add_argument("--politica", default=None, help="Ruta del JSON de usuarios.")
    export.add_argument(
        "--salida",
        default=None,
        help="Carpeta de salida; por defecto, «exportaciones» junto a la base.",
    )
    export.set_defaults(func=_comando_export)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    # La consola de Windows suele usar cp1252; la salida del MVP es UTF-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:  # pragma: no cover - flujos sin ``reconfigure``
        pass
    parser = construir_parser()
    args = parser.parse_args(argv)
    if getattr(args, "archivo", None):
        args.archivo = [ruta for grupo in args.archivo for ruta in grupo]
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
