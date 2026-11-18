"""Interfaz Streamlit del MVP — Etapas 2 y 3: documentos, evidencia y análisis.

Ejecutar desde la raíz del proyecto::

    streamlit run mvp/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

import streamlit as st  # noqa: E402

from mvp.core import access, classifier, config  # noqa: E402
from mvp.core.ai_service import ProveedorOpenAICompatible, ProveedorReglas  # noqa: E402
from mvp.core.analysis import AnalizadorExpediente  # noqa: E402
from mvp.core.evaluation import EvaluadorExpediente  # noqa: E402
from mvp.core.exporters import exportar_informes  # noqa: E402
from mvp.core.integrity import (  # noqa: E402
    listar_eventos_integridad,
    verificar_expediente,
)
from mvp.core.pipeline import ProcesadorDocumental  # noqa: E402


@st.cache_resource(show_spinner=False)
def cargar_procesador(ruta_bd: str) -> ProcesadorDocumental:
    return ProcesadorDocumental(ruta_bd)


@st.cache_resource(show_spinner=False)
def cargar_analizador(ruta_bd: str) -> AnalizadorExpediente:
    return AnalizadorExpediente(ruta_bd)


def _filas_documentos(documentos: list[dict]) -> list[dict]:
    filas = []
    for documento in documentos:
        filas.append(
            {
                "ID": documento["id"],
                "Archivo": documento["nombre_archivo"],
                "Formato": documento["formato"],
                "Estado": documento["estado"],
                "Texto": documento.get("texto_recuperable") or "—",
                "Tipo documental": documento.get("tipo_documental") or "—",
                "Componente": documento.get("componente") or "—",
                "Confianza": documento.get("confianza"),
                "Clasificación": documento.get("estado_clasificacion"),
                "Origen": documento.get("clasificacion_origen") or "—",
                "Caché": "sí" if documento.get("cache_hit") else "no",
                "Fragmentos": documento.get("fragmentos"),
                "ms": documento.get("duracion_ms"),
            }
        )
    return filas


def _guardar_subida(expediente: str, archivo) -> Path:
    destino = config.DIR_UPLOADS / expediente
    destino.mkdir(parents=True, exist_ok=True)
    nombre = Path(archivo.name).name
    ruta = destino / nombre
    ruta.write_bytes(archivo.getbuffer())
    return ruta


def _mostrar_resultados(resultados: list[dict]) -> None:
    if not resultados:
        return
    st.subheader("Resultado de la carga")
    st.dataframe(
        [
            {
                "Archivo": r["nombre_archivo"],
                "Resultado": "Procesado" if r["ok"] else "Rechazado",
                "Motivo": r.get("motivo_rechazo") or "—",
                "Tipo": r.get("tipo_documental") or "—",
                "Confianza": r.get("confianza"),
                "Texto": r.get("texto_recuperable") or "—",
                "Fragmentos": r.get("fragmentos"),
                "Caché": "sí" if r.get("cache_hit") else "no",
                "ms": r.get("duracion_ms"),
            }
            for r in resultados
        ],
        use_container_width=True,
        hide_index=True,
    )
    for resultado in resultados:
        if resultado["ok"]:
            for advertencia in resultado.get("advertencias", []):
                st.warning(f"{resultado['nombre_archivo']}: {advertencia}")
        else:
            st.error(
                f"{resultado['nombre_archivo']} — {resultado['motivo_rechazo']}: "
                f"{resultado['mensaje']}"
            )


def _resultado_error(nombre_archivo: str, error: Exception) -> dict:
    """Convierte un error inesperado en un resultado trazable, sin abortar el lote."""

    return {
        "nombre_archivo": nombre_archivo,
        "ok": False,
        "motivo_rechazo": "ERROR_INESPERADO",
        "mensaje": str(error) or error.__class__.__name__,
        "tipo_documental": None,
        "confianza": None,
        "texto_recuperable": None,
        "fragmentos": 0,
        "cache_hit": False,
        "duracion_ms": 0,
        "advertencias": [],
    }


def tab_carga(
    procesador: ProcesadorDocumental,
    expediente: str,
    actor: str,
    puede_cargar: bool = True,
) -> None:
    st.markdown(
        "Carga documentos **PDF con texto, DOCX o XLSX**. El sistema valida el formato, "
        "calcula el SHA-256, reutiliza la extracción en caché y clasifica el documento."
    )
    if not puede_cargar:
        st.info(
            "Tu rol permite consultar el expediente, pero no cargar documentos. "
            "Las pestañas de lectura siguen disponibles."
        )
        return

    archivos = st.file_uploader(
        "Selecciona uno o varios archivos",
        type=["pdf", "docx", "xlsx"],
        accept_multiple_files=True,
        help=f"Tamaño máximo por archivo: {config.TAMANO_MAXIMO_MB} MB.",
    )

    if st.button("Procesar archivos cargados", type="primary", disabled=not archivos):
        resultados = []
        rutas = []
        for archivo in archivos or []:
            ruta = _guardar_subida(expediente, archivo)
            rutas.append(str(ruta))
            try:
                resultado = procesador.ingestar_archivo(expediente, ruta, actor=actor)
                resultados.append(resultado.a_dict())
            except Exception as error:  # un archivo no debe bloquear el lote
                resultados.append(_resultado_error(archivo.name, error))
        st.session_state["ultimos_resultados"] = resultados
        st.session_state["ultima_carga"] = {"tipo": "archivos", "rutas": rutas}

    _mostrar_resultados(st.session_state.get("ultimos_resultados", []))

    st.divider()
    with st.expander("Procesar una carpeta local (demo / lote)"):
        st.caption(
            "Útil para la demostración con el corpus de `mvp/etapa3/muestras/`. "
            "La ruta se interpreta en el equipo donde corre la aplicación."
        )
        ruta_texto = st.text_input(
            "Ruta de carpeta",
            value=str(config.DIR_MUESTRAS_ETAPA3 / "caso"),
            key="ruta_carpeta_demo",
        )
        if st.button("Procesar carpeta"):
            carpeta = Path(ruta_texto)
            if not carpeta.is_dir():
                st.error(f"No existe la carpeta: {carpeta}")
            else:
                try:
                    resultados = [
                        r.a_dict()
                        for r in procesador.ingestar_carpeta(
                            expediente, carpeta, actor=actor
                        )
                    ]
                except Exception as error:
                    resultados = [_resultado_error(carpeta.name, error)]
                st.session_state["ultimos_resultados"] = resultados
                st.session_state["ultima_carga"] = {
                    "tipo": "carpeta",
                    "rutas": [str(carpeta)],
                }
                st.rerun()

    resultados = st.session_state.get("ultimos_resultados", [])
    rechazados = [resultado for resultado in resultados if not resultado.get("ok")]
    ultima = st.session_state.get("ultima_carga")
    if rechazados and ultima:
        st.warning(
            f"{len(rechazados)} archivo(s) no se pudieron procesar. El inventario, "
            "las propuestas y las decisiones ya registradas **se conservan**."
        )
        with st.expander("Errores y recuperación", expanded=True):
            for resultado in rechazados:
                st.error(
                    f"**{resultado['nombre_archivo']}** — "
                    f"`{resultado.get('motivo_rechazo')}`: {resultado.get('mensaje')}"
                )
            st.caption(
                "Reintentar vuelve a procesar el mismo lote. Los documentos que ya "
                "estaban válidos se reutilizan desde la caché por SHA-256."
            )
            if st.button("Reintentar procesamiento"):
                nuevos = []
                if ultima["tipo"] == "archivos":
                    for ruta in ultima["rutas"]:
                        try:
                            nuevo = procesador.ingestar_archivo(
                                expediente, ruta, actor=actor
                            )
                            nuevos.append(nuevo.a_dict())
                        except Exception as error:
                            nuevos.append(_resultado_error(Path(ruta).name, error))
                else:
                    carpeta = Path(ultima["rutas"][0])
                    try:
                        nuevos = [
                            r.a_dict()
                            for r in procesador.ingestar_carpeta(
                                expediente, carpeta, actor=actor
                            )
                        ]
                    except Exception as error:
                        nuevos = [_resultado_error(carpeta.name, error)]
                st.session_state["ultimos_resultados"] = nuevos
                st.rerun()


def tab_documentos(
    procesador: ProcesadorDocumental,
    expediente: str,
    actor: str,
    puede_editar: bool = True,
) -> None:
    documentos = procesador.listar_documentos(expediente)
    if not documentos:
        st.info("Aún no hay documentos procesados para este expediente.")
        return

    resumen = procesador.resumen_procesamiento(expediente)
    columnas = st.columns(5)
    columnas[0].metric("Documentos", resumen["documentos_total"])
    columnas[1].metric("Válidos", resumen["validos"])
    columnas[2].metric("Rechazados", resumen["rechazados"])
    columnas[3].metric("Clasificados", resumen["clasificados"])
    columnas[4].metric("Caché", resumen["cache_hits"])

    st.dataframe(
        _filas_documentos(documentos),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Confianza": st.column_config.ProgressColumn(
                "Confianza", min_value=0, max_value=100, format="%d"
            )
        },
    )

    rechazados = [d for d in documentos if d["estado"] == "RECHAZADO"]
    if rechazados:
        with st.expander(f"Documentos rechazados ({len(rechazados)})"):
            for documento in rechazados:
                st.error(
                    f"**{documento['nombre_archivo']}** — {documento['motivo_rechazo']}: "
                    f"{documento['mensaje']}"
                )

    st.divider()
    st.subheader("Corrección humana de la clasificación")
    st.caption(
        "La corrección se guarda vinculada al SHA-256 del archivo: si se vuelve a cargar "
        "el mismo documento (aunque la extracción venga de caché), la corrección se conserva."
    )

    if not puede_editar:
        st.info(
            "Tu rol permite consultar el inventario y la clasificación, pero no "
            "modificarla. La corrección queda reservada a especialistas y administradores."
        )
        return

    validos = [d for d in documentos if d["estado"] == "VALIDO"]
    if not validos:
        st.info("No hay documentos válidos para corregir.")
        return

    etiquetas = {
        f"{d['id']} · {d['nombre_archivo']}": d
        for d in validos
    }
    seleccion = st.selectbox("Documento", list(etiquetas), key="doc_corregir")
    documento = etiquetas[seleccion]

    opciones = [f"{tipo} | {componente}" for tipo, componente in classifier.TIPOS_DOCUMENTALES]
    actual = f"{documento.get('tipo_documental')} | {documento.get('componente')}"
    indice = opciones.index(actual) if actual in opciones else 0

    with st.form("form_correccion"):
        elegido = st.selectbox("Tipo documental y componente", opciones, index=indice)
        actor_correccion = st.text_input("Responsable de la corrección", value=actor)
        motivo = st.text_area(
            "Motivo de la corrección (obligatorio)",
            placeholder="Ej.: el contenido corresponde a EETT aunque el nombre del archivo es genérico.",
        )
        enviado = st.form_submit_button("Registrar corrección", type="primary")

    if enviado:
        tipo, componente = elegido.split(" | ", 1)
        try:
            actualizado = procesador.corregir_clasificacion(
                documento["id"],
                tipo,
                componente,
                actor=actor_correccion,
                motivo=motivo,
            )
            st.success(
                f"Corrección registrada: {actualizado['nombre_archivo']} → "
                f"{actualizado['tipo_documental']} / {actualizado['componente']}."
            )
            st.rerun()
        except ValueError as error:
            st.error(str(error))


def tab_extraccion(procesador: ProcesadorDocumental, expediente: str) -> None:
    documentos = [
        d
        for d in procesador.listar_documentos(expediente)
        if d["estado"] == "VALIDO"
    ]
    if not documentos:
        st.info("No hay documentos válidos con extracción disponible.")
        return

    etiquetas = {f"{d['id']} · {d['nombre_archivo']}": d for d in documentos}
    seleccion = st.selectbox("Documento", list(etiquetas), key="doc_extraccion")
    documento = etiquetas[seleccion]

    columnas = st.columns(4)
    columnas[0].metric("Texto recuperable", documento.get("texto_recuperable") or "—")
    columnas[1].metric("Páginas", documento.get("paginas") or "—")
    columnas[2].metric("Caracteres", f"{documento.get('caracteres') or 0:,}")
    columnas[3].metric("Fragmentos", documento.get("fragmentos") or 0)

    st.code(documento.get("sha256") or "sin hash", language=None)
    for advertencia in documento.get("advertencias", []):
        st.warning(advertencia)

    fragmentos = procesador.fragmentos_de(documento["id"])
    st.dataframe(
        [
            {
                "Orden": fragmento["orden"],
                "Ubicación": fragmento["ubicacion"],
                "Tipo": fragmento["tipo"],
                "Texto": fragmento["texto"],
            }
            for fragmento in fragmentos
        ],
        use_container_width=True,
        hide_index=True,
    )


def tab_metricas(procesador: ProcesadorDocumental, expediente: str) -> None:
    resumen = procesador.resumen_procesamiento(expediente)
    columnas = st.columns(4)
    columnas[0].metric("Documentos", resumen["documentos_total"])
    columnas[1].metric("Válidos", resumen["validos"])
    columnas[2].metric("Rechazados", resumen["rechazados"])
    columnas[3].metric("Fragmentos", resumen["fragmentos_total"])

    columnas = st.columns(4)
    columnas[0].metric("Texto completo", resumen["texto_si"])
    columnas[1].metric("Texto parcial", resumen["texto_parcial"])
    columnas[2].metric("Clasificados", resumen["clasificados"])
    columnas[3].metric("Corregidos", resumen["corregidos"])

    if resumen["tipos_documentales"]:
        st.subheader("Tipos documentales detectados")
        st.bar_chart(resumen["tipos_documentales"])

    if resumen["motivos_rechazo"]:
        st.subheader("Motivos de rechazo")
        st.dataframe(
            [
                {"Motivo": motivo, "Cantidad": cantidad}
                for motivo, cantidad in resumen["motivos_rechazo"].items()
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Bitácora de auditoría")
    auditoria = procesador.listar_auditoria(200)
    st.dataframe(
        [
            {
                "Fecha": registro["ts"],
                "Actor": registro["actor"],
                "Acción": registro["accion"],
                "Entidad": f"{registro['entidad']}#{registro['entidad_id']}",
                "Detalle": str(registro["detalle"])[:300],
            }
            for registro in auditoria
        ],
        use_container_width=True,
        hide_index=True,
    )


def tab_analisis(
    ruta_bd: str,
    expediente: str,
    actor: str,
    puede_analizar: bool = True,
    puede_decidir: bool = True,
) -> None:
    analizador = cargar_analizador(ruta_bd)
    st.markdown(
        "Recupera **evidencia verificable** por requisito, analiza con IA bajo un "
        "**contrato JSON estricto**, comprueba la **integridad** de las fuentes y "
        "permite la **evaluación manual** cuando la IA no responde."
    )

    documentos = analizador.procesador.listar_documentos(expediente)
    if not documentos:
        st.info(
            "Este expediente aún no tiene documentos. Cárgalos en la pestaña "
            "«1. Carga» para poder recuperar evidencia."
        )
        return

    if not puede_analizar:
        st.info(
            "Tu rol permite consultar la evidencia y los resultados, pero no "
            "ejecutar la recuperación ni el análisis automático."
        )

    col_acciones = st.columns(3)
    if puede_analizar and col_acciones[0].button(
        "Recuperar evidencia", type="primary"
    ):
        with st.spinner("Recuperando evidencia..."):
            evidencias = analizador.recuperar(expediente)
        total = sum(len(items) for items in evidencias.values())
        st.success(
            f"Evidencia recuperada: {total} fragmentos en "
            f"{len(evidencias)} requisitos."
        )

    opciones_proveedor = ["Reglas (determinista, sin red)"]
    if config.IA_API_KEY:
        opciones_proveedor.append("OpenAI compatible")
    proveedor_elegido = col_acciones[1].selectbox(
        "Proveedor de IA",
        opciones_proveedor,
        key="proveedor_analisis",
        disabled=not puede_analizar,
    )
    if puede_analizar and col_acciones[1].button("Analizar requisitos"):
        if proveedor_elegido == "OpenAI compatible":
            proveedor = ProveedorOpenAICompatible()
        else:
            proveedor = ProveedorReglas()
        with st.spinner("Analizando..."):
            resultados = analizador.analizar_expediente(
                expediente, proveedor=proveedor
            )
        validas = sum(1 for resultado in resultados if resultado.valida)
        st.success(
            f"Análisis completado: {validas}/{len(resultados)} propuestas válidas."
        )
        errores = {
            resultado.requisito_id: resultado.errores
            for resultado in resultados
            if resultado.errores
        }
        if errores:
            with st.expander("Errores y contingencias detectadas"):
                for requisito_id, mensajes in errores.items():
                    st.warning(f"{requisito_id}: " + " | ".join(mensajes[:4]))

    if puede_analizar and col_acciones[2].button("Verificar integridad"):
        with st.spinner("Verificando hashes..."):
            integridad = verificar_expediente(ruta_bd, expediente)
        if integridad["requiere_atencion"]:
            st.error(
                f"{integridad['FUENTE_MODIFICADA']} fuentes modificadas y "
                f"{integridad['FUENTE_NO_DISPONIBLE']} no disponibles."
            )
        else:
            st.success(
                f"Integridad correcta: {integridad['VIGENTE']} documentos vigentes."
            )

    resumen = analizador.resumen(expediente)
    columnas = st.columns(5)
    columnas[0].metric("Cobertura de revisión", f"{resumen['cobertura_revision_pct']}%")
    columnas[1].metric(
        "Cumplimiento ponderado",
        f"{resumen['cumplimiento_pct']}%" if resumen["cumplimiento_pct"] is not None else "—",
    )
    columnas[2].metric(
        "Propuestas válidas",
        f"{resumen['con_propuesta_valida']}/{resumen['requisitos_total']}",
    )
    columnas[3].metric("Contingencias", resumen["contingencias"])
    columnas[4].metric("Alertas de integridad", resumen["integridad_alertas"])

    st.caption(
        "La cobertura de revisión es el peso con propuesta registrada; el cumplimiento "
        "ponderado solo considera estados concluyentes. La ausencia de evidencia no "
        "equivale a «No cumple»."
    )

    st.subheader("Resultado por requisito")
    st.dataframe(
        [
            {
                "Req.": detalle["requisito_id"],
                "Requisito": detalle["requisito"],
                "Peso": f"{detalle['peso_pct']}%",
                "Evidencias": detalle["evidencias"],
                "Estado efectivo": detalle["estado_efectivo"],
                "Origen": detalle["origen"],
                "Propuesta válida": "sí" if detalle["propuesta_valida"] else "no",
                "Evaluación manual": "sí" if detalle["evaluacion_manual"] else "no",
                "Integridad": "alerta" if detalle["integridad_alerta"] else "vigente",
                "Motivo": detalle["motivo"] or "—",
            }
            for detalle in resumen["requisitos"]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.subheader("Evidencia recuperada")
    requisitos = analizador.perfiles.ids()
    requisito_evidencia = st.selectbox(
        "Requisito", requisitos, key="requisito_evidencia"
    )
    evidencias = analizador.evidencias(expediente, requisito_evidencia)
    if not evidencias:
        st.info("Sin evidencia persistida para este requisito. Ejecuta «Recuperar evidencia».")
    else:
        st.dataframe(
            [
                {
                    "Puntaje": evidencia["puntaje"],
                    "Archivo": evidencia["archivo"],
                    "Ubicación": evidencia["ubicacion"],
                    "Tipo": evidencia["tipo_documental"],
                    "SHA-256": evidencia["sha256_fuente"][:16] + "…",
                    "Integridad": evidencia["integridad"],
                    "Texto": evidencia["texto"][:240],
                }
                for evidencia in evidencias
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
    st.subheader("Propuestas de IA")
    propuestas = analizador.propuestas(expediente, limite=30)
    if not propuestas:
        st.info("Aún no hay propuestas registradas.")
    else:
        st.dataframe(
            [
                {
                    "ID": propuesta["id"],
                    "Req.": propuesta["requisito_id"],
                    "Proveedor": propuesta["proveedor"],
                    "Estado": propuesta["estado_propuesto"],
                    "Válida": "sí" if propuesta["valida"] else "no",
                    "Archivo": propuesta.get("archivo") or "—",
                    "Ubicación": propuesta.get("ubicacion") or "—",
                    "Cita": (propuesta.get("cita") or "—")[:120],
                    "Integridad": propuesta.get("integridad"),
                }
                for propuesta in propuestas
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
    st.subheader("Integridad de las fuentes")
    eventos = listar_eventos_integridad(ruta_bd, expediente, limite=20)
    if not eventos:
        st.caption("Sin verificaciones registradas.")
    else:
        st.dataframe(
            [
                {
                    "Fecha": evento["ts"],
                    "Documento": evento["documento_id"],
                    "Archivo": evento["archivo"],
                    "Estado": evento["estado"],
                    "Detalle": (evento.get("detalle") or "")[:160],
                }
                for evento in eventos
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
    st.subheader("Modo de contingencia")
    st.caption(
        "Un requisito entra en contingencia cuando la IA no responde, cuando la "
        "propuesta automática es inválida o cuando la fuente cambió. El flujo no "
        "se detiene: el requisito se marca para revisión y puede resolverse con "
        "una evaluación manual motivada."
    )
    contingentes = [
        detalle
        for detalle in resumen["requisitos"]
        if detalle["contingencia"] or detalle["integridad_alerta"]
    ]
    if not contingentes:
        st.success(
            "No hay requisitos en contingencia ni alertas de integridad en este "
            "expediente."
        )
    else:
        st.warning(
            f"{len(contingentes)} requisito(s) requieren atención humana. "
            "El avance y las decisiones ya registradas se conservan."
        )
        st.dataframe(
            [
                {
                    "Req.": detalle["requisito_id"],
                    "Requisito": detalle["requisito"],
                    "Peso": f"{detalle['peso_pct']}%",
                    "Origen": detalle["origen"],
                    "Estado actual": detalle["estado_efectivo"],
                    "Integridad": (
                        "alerta" if detalle["integridad_alerta"] else "vigente"
                    ),
                    "Motivo": detalle["motivo"] or "—",
                }
                for detalle in contingentes
            ],
            use_container_width=True,
            hide_index=True,
        )
        if not puede_decidir:
            st.info(
                "Tu rol permite consultar la contingencia, pero no resolverla. "
                "La evaluación manual requiere permiso de decisión."
            )
        else:
            ids_contingentes = [detalle["requisito_id"] for detalle in contingentes]
            indice_contingencia = (
                config.ESTADOS_REQUISITO.index("Requiere revisión especializada")
                if "Requiere revisión especializada" in config.ESTADOS_REQUISITO
                else 0
            )
            with st.form("form_contingencia"):
                requisito_contingencia = st.selectbox(
                    "Requisito en contingencia",
                    ids_contingentes,
                    key="requisito_contingencia",
                )
                estado_contingencia = st.selectbox(
                    "Estado manual",
                    config.ESTADOS_REQUISITO,
                    index=indice_contingencia,
                    key="estado_contingencia",
                )
                motivo_contingencia = st.text_area(
                    "Motivo de la resolución (obligatorio)",
                    placeholder=(
                        "Ej.: la IA no respondió; se revisó el expediente y se "
                        "verificó el certificado en la página 12."
                    ),
                )
                actor_contingencia = st.text_input(
                    "Responsable", value=actor, key="actor_contingencia"
                )
                resolver_contingencia = st.form_submit_button(
                    "Resolver contingencia con evaluación manual", type="primary"
                )
            if resolver_contingencia:
                try:
                    evaluacion = analizador.registrar_evaluacion_manual(
                        expediente,
                        requisito_contingencia,
                        estado_contingencia,
                        motivo_contingencia,
                        actor=actor_contingencia,
                    )
                    st.success(
                        f"Contingencia resuelta: {evaluacion['requisito_id']} → "
                        f"{evaluacion['estado']}."
                    )
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

    st.divider()
    st.subheader("Evaluación manual")
    st.caption(
        "Se usa cuando la IA no responde o la evidencia requiere juicio de ingeniería. "
        "La evaluación queda auditada y prevalece sobre la propuesta automática."
    )
    if not puede_decidir:
        st.info(
            "Tu rol permite consultar la evaluación manual registrada, pero no "
            "crear ni modificar evaluaciones."
        )
    else:
        with st.form("form_evaluacion_manual"):
            requisito_manual = st.selectbox(
                "Requisito", requisitos, key="requisito_manual"
            )
            estado_manual = st.selectbox(
                "Estado", config.ESTADOS_REQUISITO, key="estado_manual"
            )
            motivo_manual = st.text_area(
                "Motivo de la evaluación (obligatorio)",
                placeholder="Ej.: falta el CV y la constancia de colegiatura del residente.",
            )
            actor_manual = st.text_input("Responsable", value=actor)
            enviado = st.form_submit_button("Registrar evaluación", type="primary")

        if enviado:
            try:
                evaluacion = analizador.registrar_evaluacion_manual(
                    expediente,
                    requisito_manual,
                    estado_manual,
                    motivo_manual,
                    actor=actor_manual,
                )
                st.success(
                    f"Evaluación registrada: {evaluacion['requisito_id']} → "
                    f"{evaluacion['estado']}."
                )
                st.rerun()
            except ValueError as error:
                st.error(str(error))

    st.divider()
    with st.expander("Exportar resultados y propuestas (CSV)"):
        if st.button("Generar exportaciones"):
            carpeta = config.DIR_DATOS / "export"
            carpeta.mkdir(parents=True, exist_ok=True)
            ruta_resultados = analizador.exportar_resultados_csv(
                expediente, carpeta / "resultados.csv"
            )
            ruta_propuestas = analizador.exportar_propuestas_csv(
                expediente, carpeta / "propuestas.csv"
            )
            st.session_state["export_resultados"] = str(ruta_resultados)
            st.session_state["export_propuestas"] = str(ruta_propuestas)
        if st.session_state.get("export_resultados"):
            st.download_button(
                "Descargar resultados.csv",
                data=Path(st.session_state["export_resultados"]).read_bytes(),
                file_name="resultados.csv",
                mime="text/csv",
            )
        if st.session_state.get("export_propuestas"):
            st.download_button(
                "Descargar propuestas.csv",
                data=Path(st.session_state["export_propuestas"]).read_bytes(),
                file_name="propuestas.csv",
                mime="text/csv",
            )


def tab_evaluacion(
    ruta_bd: str,
    expediente: str,
    actor: str,
    puede_decidir: bool = True,
) -> None:
    analizador = cargar_analizador(ruta_bd)
    evaluador = EvaluadorExpediente(ruta_bd)
    st.markdown(
        "Registra la **decisión humana** sobre la propuesta vigente: aceptar, "
        "modificar o descartar. Cada decisión exige **motivo, responsable y fecha**, "
        "conserva la propuesta original y recalcula el **avance ponderado**."
    )

    resumen = analizador.resumen(expediente)
    columnas = st.columns(5)
    columnas[0].metric("Cobertura de revisión", f"{resumen['cobertura_revision_pct']}%")
    columnas[1].metric("Avance ponderado", f"{resumen['avance_pct']}%")
    columnas[2].metric(
        "Cumplimiento ponderado",
        f"{resumen['cumplimiento_pct']}%"
        if resumen["cumplimiento_pct"] is not None
        else "—",
    )
    columnas[3].metric(
        "Decisiones", f"{resumen['decisiones_registradas']}/{resumen['requisitos_total']}"
    )
    columnas[4].metric(
        "Aceptar / Modificar / Descartar",
        f"{resumen['aceptadas']} / {resumen['modificadas']} / {resumen['descartadas']}",
    )
    st.caption(
        f"Avance = {resumen['avance_formula']}. Solo los requisitos con decisión "
        "aportan; descartar deja el requisito en «No se encontró información»."
    )

    st.subheader("Estado por requisito")
    st.dataframe(
        [
            {
                "Req.": detalle["requisito_id"],
                "Requisito": detalle["requisito"],
                "Peso": f"{detalle['peso_pct']}%",
                "Estado propuesto": detalle["estado_propuesto"] or "—",
                "Estado efectivo": detalle["estado_efectivo"],
                "Decisión": detalle["decision"] or "sin decidir",
                "Responsable": detalle["decision_actor"] or "—",
                "Fecha": detalle["decision_fecha"] or "—",
                "Motivo": detalle["motivo"] or "—",
            }
            for detalle in resumen["requisitos"]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.subheader("Decidir sobre una propuesta")
    requisitos = analizador.perfiles.ids()
    requisito = st.selectbox("Requisito", requisitos, key="requisito_decision")
    propuesta = analizador.ultima_propuesta(expediente, requisito)
    vigente = evaluador.vigentes(expediente).get(requisito)

    if propuesta is None:
        st.info(
            "No hay propuesta válida para este requisito. Ejecuta el análisis en la "
            "pestaña «4. Evidencia y análisis»."
        )
        return

    columnas = st.columns(3)
    columnas[0].metric("Estado propuesto", propuesta["estado_propuesto"] or "—")
    columnas[1].metric("Proveedor", propuesta["proveedor"])
    columnas[2].metric(
        "Integridad", propuesta.get("integridad") or "VIGENTE"
    )

    with st.expander("Propuesta original y fuente", expanded=True):
        st.write(f"**Cita:** {propuesta.get('cita') or '—'}")
        st.write(f"**Observación:** {propuesta.get('observacion') or '—'}")
        st.write(f"**Motivo:** {propuesta.get('motivo') or '—'}")
        st.write(
            f"**Fuente:** {propuesta.get('archivo') or '—'} · "
            f"{propuesta.get('ubicacion') or '—'}"
        )
        st.caption(f"Huella: {propuesta.get('huella') or '—'}")

    if vigente:
        st.success(
            f"Decisión vigente: **{vigente['decision']}** → "
            f"{vigente['estado_final']} ({vigente['actor']}, {vigente['creado_en']})."
        )

    if not puede_decidir:
        st.info(
            "Tu rol permite consultar el estado, la propuesta y el historial, pero "
            "no registrar decisiones. Solicita el rol «especialista» o "
            "«administrador» para decidir."
        )
    else:
        with st.form("form_decision"):
            decision = st.radio(
                "Decisión",
                ("aceptar", "modificar", "descartar"),
                horizontal=True,
                key="decision_tipo",
            )
            estado_final = st.selectbox(
                "Estado final (solo para modificar)",
                config.ESTADOS_REQUISITO,
                index=config.ESTADOS_REQUISITO.index("Cumple parcialmente"),
                key="decision_estado_final",
            )
            motivo = st.text_area(
                "Motivo de la decisión (obligatorio)",
                placeholder=(
                    "Ej.: el cronograma no cubre el plazo total; se acepta parcialmente "
                    "con observación."
                ),
            )
            actor_decision = st.text_input("Responsable", value=actor)
            enviado = st.form_submit_button("Registrar decisión", type="primary")

        if enviado:
            try:
                registro = evaluador.decidir(
                    expediente,
                    requisito,
                    decision,
                    actor=actor_decision,
                    motivo=motivo,
                    estado_final=estado_final if decision == "modificar" else None,
                    propuesta_id=int(propuesta["id"]),
                )
                st.success(
                    f"Decisión registrada: {registro['requisito_id']} → "
                    f"{registro['estado_final']}."
                )
                st.rerun()
            except ValueError as error:
                st.error(str(error))

    st.divider()
    st.subheader("Historial de decisiones")
    registros = evaluador.historial(expediente, requisito)
    if not registros:
        st.caption("Sin decisiones registradas para este requisito.")
    else:
        st.dataframe(
            [
                {
                    "Fecha": registro["creado_en"],
                    "Decisión": registro["decision"],
                    "Propuesto": registro["estado_propuesto"],
                    "Final": registro["estado_final"],
                    "Responsable": registro["actor"],
                    "Motivo": registro["motivo"],
                    "Versión": registro.get("version_kb") or "—",
                    "Vigente": "sí" if registro["es_vigente"] else "no",
                    "Fuente": registro.get("archivo") or "—",
                    "Cita": (registro.get("cita") or "—")[:140],
                }
                for registro in registros
            ],
            use_container_width=True,
            hide_index=True,
        )

    if puede_decidir:
        with st.expander("Reejecutar el análisis sin duplicar hallazgos"):
            st.caption(
                "Vuelve a analizar todos los requisitos con el proveedor determinista. "
                "Las propuestas idénticas se reutilizan por huella y las decisiones "
                "se conservan."
            )
            if st.button("Reanalizar expediente"):
                antes = len(analizador.propuestas(expediente, limite=1000))
                with st.spinner("Reanalizando..."):
                    analizador.analizar_expediente(expediente)
                despues = len(analizador.propuestas(expediente, limite=1000))
                persistidas = evaluador.vigentes(expediente)
                st.success(
                    f"Análisis reejecutado. Propuestas: {antes} → {despues}. "
                    f"Decisiones vigentes conservadas: {len(persistidas)}."
                )


def tab_exportacion(
    ruta_bd: str,
    expediente: str,
    actor: str,
    puede_exportar: bool = True,
) -> None:
    analizador = cargar_analizador(ruta_bd)
    st.markdown(
        "Genera el **informe real en Excel y Word** a partir de la base SQLite: "
        "métricas, requisitos, decisiones, propuestas, evidencias, documentos y "
        "auditoría. No se usan datos fijos de demostración."
    )

    resumen = analizador.resumen(expediente)
    columnas = st.columns(4)
    columnas[0].metric("Requisitos", resumen["requisitos_total"])
    columnas[1].metric("Avance ponderado", f"{resumen['avance_pct']}%")
    columnas[2].metric("Decisiones", resumen["decisiones_registradas"])
    columnas[3].metric(
        "Evidencias",
        sum(detalle["evidencias"] for detalle in resumen["requisitos"]),
    )

    if not puede_exportar:
        st.info(
            "Tu rol permite consultar los resultados, pero no exportarlos. "
            "La descarga de informes requiere el permiso «exportar»."
        )
        return

    if st.button("Generar informe Excel y Word", type="primary"):
        # Los informes se guardan junto a la base activa: nunca dentro de la
        # evidencia cerrada de otra etapa.
        carpeta = Path(ruta_bd).resolve().parent / "exportaciones"
        try:
            rutas = exportar_informes(ruta_bd, expediente, carpeta)
        except Exception as error:  # la UI informa la causa y conserva los datos
            st.error(
                "No se pudo generar el informe. La base de datos y las decisiones "
                f"se conservan. Causa: `{error.__class__.__name__}`: {error}"
            )
        else:
            st.session_state[f"exportacion_{expediente}"] = {
                "xlsx": str(rutas["xlsx"]),
                "docx": str(rutas["docx"]),
            }
            st.success(
                f"Informe generado para {expediente}: Excel y Word actualizados "
                "desde SQLite."
            )
            st.rerun()

    rutas = st.session_state.get(f"exportacion_{expediente}")
    if rutas:
        st.subheader("Descargas disponibles")
        st.caption(f"Generado por {actor}. Los archivos se regeneran desde la base.")
        columnas = st.columns(2)
        for columna, clave, etiqueta, mime in (
            (columnas[0], "xlsx", "Descargar Excel (.xlsx)", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            (columnas[1], "docx", "Descargar Word (.docx)", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ):
            ruta = Path(rutas[clave])
            if not ruta.exists():
                columna.warning(f"El archivo {ruta.name} ya no está disponible.")
                continue
            columna.download_button(
                etiqueta,
                data=ruta.read_bytes(),
                file_name=ruta.name,
                mime=mime,
                key=f"descarga_{clave}_{expediente}",
            )
            columna.caption(f"{ruta.name} · {ruta.stat().st_size:,} bytes")
    else:
        st.info(
            "Todavía no se generó un informe en esta sesión. Usa el botón superior "
            "para construirlo desde los datos persistidos."
        )


def tab_guia() -> None:
    st.markdown(
        """
### Qué hace la Etapa 2

1. **Valida** el archivo (extensión, tamaño, legibilidad).
2. Calcula el **SHA-256** y busca la extracción en la **caché**.
3. **Extrae** texto y tablas con ubicación verificable.
4. **Clasifica** por tipo documental y componente, con confianza explicable.
5. Permite **corregir** la clasificación; la corrección se vincula al hash.
6. **Persiste** inventario, fragmentos y auditoría en SQLite.

### Qué agrega la Etapa 3

1. **Recupera evidencia** por requisito con puntaje determinista y fuente exacta
   (documento, página/hoja/celda y SHA-256).
2. **Analiza con IA** enviando solo el contexto mínimo; la respuesta se valida
   contra un **contrato JSON** de 8 campos.
3. **Rechaza** respuestas con fuente, hash o cita que no coincidan con el
   expediente; nunca convierte una respuesta inválida en conclusión.
4. **Verifica integridad**: si el archivo cambió, la conclusión anterior deja de
   ser válida y el requisito se escala.
5. Activa **contingencia** y permite **evaluación manual** motivada cuando la IA
   no responde.
6. Separa **cobertura de revisión** de **cumplimiento ponderado**. La ausencia de
   evidencia no se registra como “No cumple”.

### Qué agrega la Etapa 4

1. **Cinco estados** del catálogo, incluidos “No se encontró información” y
   “Requiere revisión especializada”.
2. **Decisión humana real**: aceptar, modificar o descartar con motivo,
   responsable y fecha; la propuesta original se conserva.
3. **Historial inmutable**: cada decisión es una fila nueva; la vigente es la
   última y puede auditarse.
4. **Avance ponderado** calculado sobre el peso total, con redondeo
   `ROUND_HALF_UP` a 1 decimal. Solo los requisitos decididos aportan.
5. **Idempotencia**: reejecutar el análisis reutiliza propuestas idénticas por
   huella y no pierde decisiones.
6. **Persistencia** de decisiones y auditoría en SQLite: al recargar la
   aplicación, todo se mantiene.

### Qué agrega la Etapa 5

1. **Exportación real** a `.xlsx` (7 hojas) y `.docx` (resumen, resultados,
   fuentes, historial y limitaciones), construida desde SQLite.
2. **Control de acceso mínimo** por rol (`administrador`, `especialista`,
   `lector`) y expedientes asignados; las acciones no permitidas se explican.
3. **Modo de contingencia visible**: lista los requisitos afectados y permite
   resolverlos con evaluación manual motivada.
4. **Errores con causa y reintento**: un archivo inválido no aborta el lote ni
   borra el avance; el reintento reutiliza la caché por SHA-256.
5. **Estados vacíos operables**: un expediente sin documentos genera informes
   sin excepciones y comunica «sin decisiones», no un error.

### Qué agrega la Etapa 6

1. **Flujo de extremo a extremo** reproducible con un comando y una base propia:
   `python -m mvp.scripts.ejecutar_etapa6`.
2. **16 casos de prueba** mapeados a criterios de aceptación; los 16 pasan sobre
   el corpus y la base reales.
3. **Métricas comparables**: línea base declarada frente a tiempos medidos, con
   aciertos de clasificación, cobertura y decisiones.
4. **Errores y correcciones** documentados con su caso de verificación.
5. **Material de entrega**: PPT editable y PDF, ficha técnica, guion y video demo
   narrado, más el acta de ensayo.
6. **Límites explícitos**: sin OCR, IA real opcional, datos sintéticos, acceso de
   demostración y feedback externo pendiente.

### Límites y pendientes

- Un PDF escaneado se rechaza: no hay OCR en este MVP.
- Sin `MVP_IA_API_KEY` se usa el proveedor determinista de reglas.
- La política de acceso es de demostración; falta autenticación real.
- Los informes son usables, pero no sustituyen la plantilla oficial firmada.

### Rechazos previstos

| Código | Significado |
|---|---|
| `FORMATO_NO_SOPORTADO` | No es PDF, DOCX ni XLSX |
| `ARCHIVO_VACIO` | 0 bytes |
| `PDF_PROTEGIDO` | Requiere contraseña |
| `PDF_ESCANEADO` | Sin capa de texto (requiere OCR) |
| `ARCHIVO_DANADO` | Archivo corrupto o inválido |
| `SIN_TEXTO_RECUPERABLE` | DOCX/XLSX sin contenido textual |

### Criterio clave

Un documento rechazado **no genera evidencia ni conclusiones**. No se marca
como “No cumple”: simplemente se excluye y se informa el motivo. Una fuente
modificada tampoco produce una conclusión automática.
"""
    )


def main() -> None:
    st.set_page_config(
        page_title="Expedivia MVP · Hito 3",
        page_icon="📄",
        layout="wide",
    )
    config.preparar_directorios()

    try:
        politica = access.cargar_politica()
    except (FileNotFoundError, ValueError) as error:
        st.error(f"No se pudo cargar la política de acceso: {error}")
        st.stop()

    st.title("Expedivia MVP — Documentos, evidencia y evaluación")
    st.caption(
        "MVP del Hito 3: carga y clasificación documental, recuperación de evidencia, "
        "contrato JSON, integridad de fuente, decisión humana, avance ponderado, "
        "exportación real y control de acceso por rol. Caso EXP-2024-089."
    )

    nombres = politica.nombres()
    indice_usuario = (
        nombres.index("Lucía Ramos") if "Lucía Ramos" in nombres else 0
    )

    with st.sidebar:
        st.header("Sesión y configuración")
        ruta_bd = st.text_input("Base de datos SQLite", value=str(config.RUTA_BD))
        usuario = st.selectbox("Usuario", nombres, index=indice_usuario)
        rol = politica.rol(usuario) or "sin rol"
        permisos = ", ".join(sorted(politica.permisos(usuario))) or "ninguno"
        asignados = ", ".join(politica.expedientes(usuario)) or "ninguno"
        st.caption(f"**Rol:** {rol}")
        st.caption(f"**Permisos:** {permisos}")
        st.caption(f"**Expedientes asignados:** {asignados}")

        expediente = st.text_input("Expediente", value=config.EXPEDIENTE_DEFECTO)

        if not politica.puede(usuario, "ver", expediente):
            st.error(
                f"El usuario «{usuario}» no tiene acceso al expediente "
                f"«{expediente}». Cambia de usuario o usa un expediente asignado."
            )
            st.stop()

        puede_cargar = politica.puede(usuario, "cargar", expediente)
        puede_analizar = politica.puede(usuario, "analizar", expediente)
        puede_decidir = politica.puede(usuario, "decidir", expediente)
        puede_exportar = politica.puede(usuario, "exportar", expediente)
        puede_administrar = politica.puede(usuario, "administrar", expediente)

        if puede_administrar:
            with st.expander("Registrar o actualizar expediente"):
                nombre = st.text_input(
                    "Nombre", value="Carretera Central Tramo 2 · Km 42–78"
                )
                especialidad = st.text_input("Especialidad", value="Pavimentos")
                version = st.text_input("Versión", value="v3")
                if st.button("Guardar expediente"):
                    procesador = cargar_procesador(ruta_bd)
                    procesador.registrar_expediente(
                        expediente,
                        nombre,
                        especialidad=especialidad,
                        version=version,
                        actor=usuario,
                    )
                    st.success(f"Expediente {expediente} registrado.")

        st.divider()
        st.caption("Los archivos se guardan en:")
        st.code(str(config.DIR_UPLOADS / expediente), language=None)

    actor = usuario
    st.caption(
        f"Sesión: **{actor}** · rol `{rol}` · expediente `{expediente}`. "
        "Las acciones no permitidas quedan deshabilitadas y explicadas."
    )

    procesador = cargar_procesador(ruta_bd)
    existentes = {e["id"] for e in procesador.listar_expedientes()}
    if expediente not in existentes:
        if not puede_cargar:
            st.error(
                f"El expediente «{expediente}» no está registrado y el rol "
                f"«{rol}» no puede crearlo."
            )
            st.stop()
        procesador.registrar_expediente(
            expediente,
            f"Expediente {expediente}",
            actor=actor,
        )

    pestanas = st.tabs(
        [
            "1. Carga",
            "2. Documentos y clasificación",
            "3. Extracción",
            "4. Evidencia y análisis",
            "5. Evaluación y avance",
            "6. Exportación e informes",
            "7. Métricas y auditoría",
            "8. Guía",
        ]
    )

    with pestanas[0]:
        tab_carga(procesador, expediente, actor, puede_cargar=puede_cargar)
    with pestanas[1]:
        tab_documentos(
            procesador, expediente, actor, puede_editar=puede_analizar
        )
    with pestanas[2]:
        tab_extraccion(procesador, expediente)
    with pestanas[3]:
        tab_analisis(
            ruta_bd,
            expediente,
            actor,
            puede_analizar=puede_analizar,
            puede_decidir=puede_decidir,
        )
    with pestanas[4]:
        tab_evaluacion(
            ruta_bd, expediente, actor, puede_decidir=puede_decidir
        )
    with pestanas[5]:
        tab_exportacion(
            ruta_bd, expediente, actor, puede_exportar=puede_exportar
        )
    with pestanas[6]:
        tab_metricas(procesador, expediente)
    with pestanas[7]:
        tab_guia()


if __name__ == "__main__":
    main()
