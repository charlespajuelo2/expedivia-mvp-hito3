"""Orquestación del análisis de evidencia e IA (Etapas 3-4).

Flujo por requisito::

    recuperar evidencia → verificar integridad → construir contexto mínimo
    → llamar al proveedor → validar contrato → persistir propuesta/ejecución
    → decisión humana → estado efectivo y avance ponderado

Reglas de seguridad:

- Una respuesta inválida **nunca** se guarda como propuesta válida.
- Si la IA no responde, se registra una **contingencia** y se habilita la
  evaluación manual; no se pierde la evidencia recuperada.
- Si una fuente cambió, no se emite una conclusión automática: se escala.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from time import perf_counter
from typing import Any

from . import config, db
from .ai_contract import validar_propuesta
from .ai_service import (
    ContextoAnalisis,
    ErrorIA,
    ProveedorIA,
    ProveedorReglas,
    RespuestaIA,
    extraer_cita,
)
from .evaluation import (
    avance_ponderado,
    calcular_huella,
    decisiones_vigentes,
)
from .evidence import (
    Evidencia,
    PerfilesEvidencia,
    RecuperadorEvidencia,
    cargar_perfiles,
    listar_evidencias,
)
from .integrity import (
    ESTADO_MODIFICADA,
    ESTADO_NO_DISPONIBLE,
    ESTADO_VIGENTE,
    aplicar_estado_integridad,
    verificar_documento,
)
from .pipeline import ProcesadorDocumental

FACTORES = {"Cumple": 1.0, "Cumple parcialmente": 0.5, "No cumple": 0.0}
ESTADOS_CONCLUYENTES = tuple(FACTORES)
PROVEEDORES_CONTINGENCIA = {"contingencia", "fallido", "integridad"}


@dataclass
class ResultadoAnalisis:
    """Resultado de analizar un requisito, exitoso o escalado."""

    expediente_id: str
    requisito_id: str
    estado: str
    valida: bool
    propuesta: dict[str, Any] | None
    errores: list[str] = field(default_factory=list)
    intentos: int = 0
    proveedor: str = ""
    modelo: str = ""
    duracion_ms: int = 0
    tokens_entrada: int = 0
    tokens_salida: int = 0
    evidencias: list[dict[str, Any]] = field(default_factory=list)
    contingencia: bool = False

    def a_dict(self) -> dict[str, Any]:
        return {
            "expediente_id": self.expediente_id,
            "requisito_id": self.requisito_id,
            "estado": self.estado,
            "valida": self.valida,
            "propuesta": self.propuesta,
            "errores": list(self.errores),
            "intentos": self.intentos,
            "proveedor": self.proveedor,
            "modelo": self.modelo,
            "duracion_ms": self.duracion_ms,
            "tokens_entrada": self.tokens_entrada,
            "tokens_salida": self.tokens_salida,
            "evidencias": list(self.evidencias),
            "contingencia": self.contingencia,
        }


class AnalizadorExpediente:
    """Servicio de recuperación, análisis, integridad y contingencia."""

    def __init__(
        self,
        ruta_bd: str | Path | None = None,
        *,
        perfiles: PerfilesEvidencia | None = None,
        proveedor: ProveedorIA | None = None,
        max_intentos: int | None = None,
        actor: str = "analista-ia",
    ) -> None:
        self.ruta_bd = db.inicializar(ruta_bd or config.RUTA_BD)
        self.procesador = ProcesadorDocumental(self.ruta_bd)
        self.perfiles = perfiles or cargar_perfiles()
        self.recuperador = RecuperadorEvidencia(self.procesador, self.perfiles)
        self.proveedor = proveedor or ProveedorReglas()
        self.max_intentos = max_intentos or config.IA_MAX_INTENTOS
        self.actor = actor

    # -- Evidencia -------------------------------------------------------

    def recuperar(
        self, expediente_id: str, requisito_id: str | None = None
    ) -> Any:
        if requisito_id:
            return self.recuperador.recuperar(expediente_id, requisito_id)
        return self.recuperador.recuperar_todas(expediente_id)

    def evidencias(
        self,
        expediente_id: str,
        requisito_id: str | None = None,
        *,
        solo_vigentes: bool = True,
    ) -> list[dict[str, Any]]:
        return listar_evidencias(
            self.ruta_bd,
            expediente_id,
            requisito_id,
            solo_vigentes=solo_vigentes,
        )

    # -- Análisis --------------------------------------------------------

    def analizar_requisito(
        self,
        expediente_id: str,
        requisito_id: str,
        *,
        proveedor: ProveedorIA | None = None,
        recuperar: bool = True,
        max_intentos: int | None = None,
        cache_integridad: dict[int, dict[str, Any]] | None = None,
    ) -> ResultadoAnalisis:
        perfil = self.perfiles.requisito(requisito_id)
        proveedor = proveedor or self.proveedor
        max_intentos = max_intentos or self.max_intentos

        if recuperar:
            evidencias = self.recuperador.recuperar(expediente_id, requisito_id)
        else:
            evidencias = self._cargar_evidencias(expediente_id, requisito_id)

        # 1. Integridad de las fuentes antes de emitir cualquier conclusión.
        resultados_integridad = self._verificar_evidencias(
            evidencias, cache_integridad=cache_integridad
        )
        fuentes_invalidas = [
            resultado
            for resultado in resultados_integridad
            if resultado["estado"] in {ESTADO_MODIFICADA, ESTADO_NO_DISPONIBLE}
        ]
        if fuentes_invalidas:
            detalle = "; ".join(
                f"{item['archivo']} ({item['estado']})" for item in fuentes_invalidas
            )
            propuesta = self._escalamiento(
                perfil.id,
                evidencias,
                motivo=(
                    "Se detectó una fuente modificada o no disponible después de la "
                    f"revisión: {detalle}. No se emite conclusión automática."
                ),
                observacion=(
                    "La integridad de la evidencia no se pudo confirmar. El especialista "
                    "debe revisar la fuente y volver a analizar el requisito."
                ),
                proveedor="integridad",
            )
            propuesta_id = self._persistir_propuesta(
                expediente_id=expediente_id,
                requisito_id=requisito_id,
                propuesta=propuesta,
                evidencias=evidencias,
                valida=True,
                proveedor="integridad",
                modelo="verificador-integridad",
                errores=[],
                integridad=ESTADO_MODIFICADA,
            )
            self._persistir_ejecucion(
                expediente_id=expediente_id,
                requisito_id=requisito_id,
                proveedor="integridad",
                modelo="verificador-integridad",
                estado="ESCALADA",
                intentos=0,
                duracion_ms=0,
                error=detalle,
            )
            self._auditar(
                expediente_id,
                "INTEGRIDAD_BLOQUEA_ANALISIS",
                "requisito",
                f"{expediente_id}:{requisito_id}",
                {"fuentes_invalidas": fuentes_invalidas, "propuesta_id": propuesta_id},
            )
            return ResultadoAnalisis(
                expediente_id=expediente_id,
                requisito_id=requisito_id,
                estado="Requiere revisión especializada",
                valida=True,
                propuesta=propuesta,
                errores=[detalle],
                intentos=0,
                proveedor="integridad",
                modelo="verificador-integridad",
                evidencias=[evidencia.a_dict() for evidencia in evidencias],
                contingencia=False,
            )

        # Solo se envía a la IA evidencia cuya fuente sigue vigente.
        evidencias_vigentes = [
            evidencia
            for evidencia in evidencias
            if evidencia.integridad == ESTADO_VIGENTE
        ]
        contexto = ContextoAnalisis(
            expediente_id=expediente_id,
            perfil=perfil,
            evidencias=evidencias_vigentes,
        )

        # 2. Llamadas al proveedor con reintentos y validación del contrato.
        inicio = perf_counter()
        errores: list[str] = []
        tokens_entrada = 0
        tokens_salida = 0
        ultimo_error_ia: ErrorIA | None = None
        intentos = 0

        for intento in range(1, max_intentos + 1):
            intentos = intento
            respuesta: RespuestaIA | None = None
            try:
                respuesta = proveedor.generar(contexto)
            except ErrorIA as exc:
                ultimo_error_ia = exc
                errores.append(f"{exc.codigo}: {exc.mensaje}")
                if not exc.reintentable or intento >= max_intentos:
                    break
                continue
            except Exception as exc:  # defensa ante proveedores externos
                ultimo_error_ia = ErrorIA(
                    "IA_ERROR_INESPERADO",
                    "El proveedor de IA produjo un error inesperado.",
                    reintentable=False,
                    detalle=str(exc),
                )
                errores.append(f"IA_ERROR_INESPERADO: {exc}")
                break

            tokens_entrada += respuesta.tokens_entrada
            tokens_salida += respuesta.tokens_salida
            validacion = validar_propuesta(
                respuesta.texto_crudo,
                requisito_id=requisito_id,
                evidencias=evidencias_vigentes,
            )
            if validacion.valida and validacion.propuesta is not None:
                propuesta = validacion.propuesta
                propuesta_id = self._persistir_propuesta(
                    expediente_id=expediente_id,
                    requisito_id=requisito_id,
                    propuesta=propuesta.a_dict(),
                    evidencias=evidencias_vigentes,
                    valida=True,
                    proveedor=respuesta.proveedor,
                    modelo=respuesta.modelo,
                    errores=[],
                    integridad=ESTADO_VIGENTE,
                )
                duracion_ms = int((perf_counter() - inicio) * 1000)
                self._persistir_ejecucion(
                    expediente_id=expediente_id,
                    requisito_id=requisito_id,
                    proveedor=respuesta.proveedor,
                    modelo=respuesta.modelo,
                    estado="VALIDA",
                    intentos=intento,
                    duracion_ms=duracion_ms,
                    tokens_entrada=tokens_entrada,
                    tokens_salida=tokens_salida,
                    error=None,
                )
                self._auditar(
                    expediente_id,
                    "PROPUESTA_IA_VALIDA",
                    "propuesta",
                    propuesta_id,
                    {
                        "requisito_id": requisito_id,
                        "estado": propuesta.estado_propuesto,
                        "proveedor": respuesta.proveedor,
                        "intentos": intento,
                    },
                )
                return ResultadoAnalisis(
                    expediente_id=expediente_id,
                    requisito_id=requisito_id,
                    estado=propuesta.estado_propuesto,
                    valida=True,
                    propuesta=propuesta.a_dict(),
                    errores=[],
                    intentos=intento,
                    proveedor=respuesta.proveedor,
                    modelo=respuesta.modelo,
                    duracion_ms=duracion_ms,
                    tokens_entrada=tokens_entrada,
                    tokens_salida=tokens_salida,
                    evidencias=[evidencia.a_dict() for evidencia in evidencias_vigentes],
                    contingencia=False,
                )

            # Respuesta inválida: se conserva para auditoría, nunca como conclusión.
            mensajes = validacion.mensajes()
            errores.extend(
                f"Intento {intento} · {mensaje}" for mensaje in mensajes
            )
            self._persistir_propuesta(
                expediente_id=expediente_id,
                requisito_id=requisito_id,
                propuesta=validacion.propuesta.a_dict()
                if validacion.propuesta
                else self._propuesta_cruda(respuesta, requisito_id),
                evidencias=evidencias_vigentes,
                valida=False,
                proveedor=respuesta.proveedor,
                modelo=respuesta.modelo,
                errores=mensajes,
                integridad=ESTADO_VIGENTE,
            )
            self._auditar(
                expediente_id,
                "PROPUESTA_IA_RECHAZADA",
                "requisito",
                f"{expediente_id}:{requisito_id}",
                {
                    "intento": intento,
                    "proveedor": respuesta.proveedor,
                    "errores": mensajes,
                },
            )
            if intento < max_intentos:
                continue
            break

        # 3. Contingencia: se escala y se conserva la evidencia para revisión manual.
        duracion_ms = int((perf_counter() - inicio) * 1000)
        motivo = (
            "La respuesta de IA fue rechazada por el contrato o el proveedor no está "
            "disponible. Se escala a revisión especializada y se conserva la evidencia."
        )
        if ultimo_error_ia is not None:
            motivo = (
                f"El proveedor de IA no respondió ({ultimo_error_ia.codigo}: "
                f"{ultimo_error_ia.mensaje}). Se escala a revisión especializada."
            )
        propuesta = self._escalamiento(
            perfil.id,
            evidencias_vigentes,
            motivo=motivo,
            observacion=(
                "No se emite conclusión automática. La evidencia recuperada queda "
                "disponible para la evaluación manual del especialista."
            ),
            proveedor="contingencia",
            intento_fallido=ultimo_error_ia is not None,
        )
        propuesta_id = self._persistir_propuesta(
            expediente_id=expediente_id,
            requisito_id=requisito_id,
            propuesta=propuesta,
            evidencias=evidencias_vigentes,
            valida=False,
            proveedor="contingencia",
            modelo="contingencia-manual",
            errores=errores,
            integridad=ESTADO_VIGENTE,
        )
        estado_ejecucion = (
            "ERROR" if ultimo_error_ia is not None else "RECHAZADA"
        )
        self._persistir_ejecucion(
            expediente_id=expediente_id,
            requisito_id=requisito_id,
            proveedor=proveedor.nombre,
            modelo=proveedor.modelo,
            estado=estado_ejecucion,
            intentos=intentos,
            duracion_ms=duracion_ms,
            tokens_entrada=tokens_entrada,
            tokens_salida=tokens_salida,
            error=" | ".join(errores)[:4000] if errores else motivo,
        )
        self._auditar(
            expediente_id,
            "CONTINGENCIA_ACTIVADA",
            "requisito",
            f"{expediente_id}:{requisito_id}",
            {
                "propuesta_id": propuesta_id,
                "errores": errores,
                "intentos": intentos,
                "estado_ejecucion": estado_ejecucion,
            },
        )
        return ResultadoAnalisis(
            expediente_id=expediente_id,
            requisito_id=requisito_id,
            estado="Requiere revisión especializada",
            valida=False,
            propuesta=propuesta,
            errores=errores,
            intentos=intentos,
            proveedor=proveedor.nombre,
            modelo=proveedor.modelo,
            duracion_ms=duracion_ms,
            tokens_entrada=tokens_entrada,
            tokens_salida=tokens_salida,
            evidencias=[evidencia.a_dict() for evidencia in evidencias_vigentes],
            contingencia=True,
        )

    def analizar_expediente(
        self,
        expediente_id: str,
        *,
        proveedor: ProveedorIA | None = None,
        requisitos: list[str] | None = None,
        recuperar: bool = True,
    ) -> list[ResultadoAnalisis]:
        cache_integridad: dict[int, dict[str, Any]] = {}
        return [
            self.analizar_requisito(
                expediente_id,
                requisito_id,
                proveedor=proveedor,
                recuperar=recuperar,
                cache_integridad=cache_integridad,
            )
            for requisito_id in (requisitos or self.perfiles.ids())
        ]

    # -- Integridad ------------------------------------------------------

    def _verificar_evidencias(
        self,
        evidencias: list[Evidencia],
        *,
        cache_integridad: dict[int, dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        resultados: list[dict[str, Any]] = []
        vistos: set[int] = set()
        for evidencia in evidencias:
            if evidencia.documento_id in vistos:
                continue
            vistos.add(evidencia.documento_id)
            if cache_integridad is not None and evidencia.documento_id in cache_integridad:
                resultado = cache_integridad[evidencia.documento_id]
                # La evidencia de este requisito se acaba de recuperar y debe
                # recibir el estado ya calculado, sin volver a leer el archivo.
                aplicar_estado_integridad(
                    self.ruta_bd, evidencia.documento_id, resultado["estado"]
                )
            else:
                resultado = verificar_documento(self.ruta_bd, evidencia.documento_id)
                if cache_integridad is not None:
                    cache_integridad[evidencia.documento_id] = resultado
            resultados.append(resultado)
            estado = resultado["estado"]
            for item in evidencias:
                if item.documento_id == evidencia.documento_id:
                    item.integridad = (
                        ESTADO_VIGENTE if estado == ESTADO_VIGENTE else estado
                    )
        return resultados

    # -- Persistencia ----------------------------------------------------

    def _persistir_propuesta(
        self,
        *,
        expediente_id: str,
        requisito_id: str,
        propuesta: dict[str, Any],
        evidencias: list[Evidencia],
        valida: bool,
        proveedor: str,
        modelo: str,
        errores: list[str],
        integridad: str,
    ) -> int:
        fuente = propuesta.get("fuente") if isinstance(propuesta, dict) else None
        fuente = fuente if isinstance(fuente, dict) else None
        evidencia_id = None
        if fuente:
            for evidencia in evidencias:
                if (
                    evidencia.documento_id == fuente.get("documento_id")
                    and evidencia.ubicacion == fuente.get("ubicacion")
                ):
                    evidencia_id = evidencia.id
                    break

        with db.conectar(self.ruta_bd) as conexion:
            huella = calcular_huella(propuesta)
            existente = conexion.execute(
                "SELECT id FROM propuestas_ia WHERE expediente_id = ? AND "
                "requisito_id = ? AND huella = ? AND valida = ? ORDER BY id LIMIT 1",
                (expediente_id, requisito_id, huella, 1 if valida else 0),
            ).fetchone()
            if existente is not None:
                # Reejecutar el análisis no duplica el mismo hallazgo ni altera
                # las decisiones humanas que ya lo referencian.
                existente_id = int(existente["id"])
                db.auditar(
                    conexion,
                    actor=self.actor,
                    accion="PROPUESTA_IA_REUTILIZADA",
                    entidad="propuesta",
                    entidad_id=existente_id,
                    detalle={
                        "requisito_id": requisito_id,
                        "estado": propuesta.get("estado_propuesto"),
                        "proveedor": proveedor,
                        "huella": huella,
                    },
                )
                return existente_id

            cursor = conexion.execute(
                "INSERT INTO propuestas_ia "
                "(expediente_id, requisito_id, evidencia_id, proveedor, modelo, "
                "estado_propuesto, evidencia_encontrada, documento_id, archivo, "
                "ubicacion, sha256_fuente, cita, observacion, requiere_revision, "
                "motivo, valida, errores, integridad, huella, creado_en) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    expediente_id,
                    requisito_id,
                    evidencia_id,
                    proveedor,
                    modelo,
                    propuesta.get("estado_propuesto"),
                    1 if propuesta.get("evidencia_encontrada") else 0,
                    fuente.get("documento_id") if fuente else None,
                    fuente.get("archivo") if fuente else None,
                    fuente.get("ubicacion") if fuente else None,
                    fuente.get("sha256") if fuente else None,
                    propuesta.get("cita"),
                    propuesta.get("observacion_preliminar"),
                    1 if propuesta.get("requiere_revision_especializada") else 0,
                    propuesta.get("motivo"),
                    1 if valida else 0,
                    json.dumps(errores, ensure_ascii=False) if errores else None,
                    integridad,
                    huella,
                    db.ahora(),
                ),
            )
            propuesta_id = int(cursor.lastrowid)
            db.auditar(
                conexion,
                actor=self.actor,
                accion="PROPUESTA_IA_VALIDA" if valida else "PROPUESTA_IA_RECHAZADA",
                entidad="propuesta",
                entidad_id=propuesta_id,
                detalle={
                    "requisito_id": requisito_id,
                    "estado": propuesta.get("estado_propuesto"),
                    "proveedor": proveedor,
                    "errores": errores,
                },
            )
        return propuesta_id

    def _persistir_ejecucion(
        self,
        *,
        expediente_id: str,
        requisito_id: str,
        proveedor: str,
        modelo: str,
        estado: str,
        intentos: int,
        duracion_ms: int,
        tokens_entrada: int = 0,
        tokens_salida: int = 0,
        error: str | None = None,
    ) -> int:
        with db.conectar(self.ruta_bd) as conexion:
            cursor = conexion.execute(
                "INSERT INTO ejecuciones_ia "
                "(expediente_id, requisito_id, proveedor, modelo, estado, intentos, "
                "duracion_ms, tokens_entrada, tokens_salida, error, creado_en) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    expediente_id,
                    requisito_id,
                    proveedor,
                    modelo,
                    estado,
                    intentos,
                    duracion_ms,
                    tokens_entrada,
                    tokens_salida,
                    error,
                    db.ahora(),
                ),
            )
            ejecucion_id = int(cursor.lastrowid)
            db.auditar(
                conexion,
                actor=self.actor,
                accion="EJECUCION_IA_REGISTRADA",
                entidad="ejecucion_ia",
                entidad_id=ejecucion_id,
                detalle={
                    "requisito_id": requisito_id,
                    "estado": estado,
                    "intentos": intentos,
                    "proveedor": proveedor,
                },
            )
        return ejecucion_id

    def _auditar(
        self,
        expediente_id: str,
        accion: str,
        entidad: str,
        entidad_id: str,
        detalle: dict[str, Any],
    ) -> None:
        with db.conectar(self.ruta_bd) as conexion:
            db.auditar(
                conexion,
                actor=self.actor,
                accion=accion,
                entidad=entidad,
                entidad_id=entidad_id,
                detalle={"expediente_id": expediente_id, **detalle},
            )

    # -- Escalamiento y utilidades ---------------------------------------

    def _cargar_evidencias(
        self, expediente_id: str, requisito_id: str
    ) -> list[Evidencia]:
        registros = listar_evidencias(
            self.ruta_bd, expediente_id, requisito_id, solo_vigentes=False
        )
        return [
            Evidencia(
                id=registro.get("id"),
                expediente_id=registro["expediente_id"],
                requisito_id=registro["requisito_id"],
                documento_id=int(registro["documento_id"]),
                fragmento_orden=int(registro.get("fragmento_orden") or 0),
                archivo=registro["archivo"],
                tipo_documental=registro.get("tipo_documental") or "",
                ubicacion=registro["ubicacion"],
                sha256_fuente=registro["sha256_fuente"],
                texto=registro["texto"],
                puntaje=int(registro.get("puntaje") or 0),
                terminos=list(registro.get("terminos") or []),
                integridad=registro.get("integridad") or ESTADO_VIGENTE,
                creado_en=registro.get("creado_en"),
            )
            for registro in registros
        ]

    def _escalamiento(
        self,
        requisito_id: str,
        evidencias: list[Evidencia],
        *,
        motivo: str,
        observacion: str,
        proveedor: str,
        intento_fallido: bool = False,
    ) -> dict[str, Any]:
        mejor: Evidencia | None = None
        perfil = self.perfiles.requisito(requisito_id)
        if evidencias:
            pruebas = [
                evidencia
                for evidencia in evidencias
                if evidencia.tipo_documental in perfil.tipos_que_prueban
            ]
            mejor = max(pruebas or evidencias, key=lambda item: item.puntaje)

        if mejor is not None:
            cita = extraer_cita(mejor.texto, mejor.terminos)
            propuesta = {
                "requisito_id": requisito_id,
                "estado_propuesto": "Requiere revisión especializada",
                "evidencia_encontrada": True,
                "fuente": mejor.fuente(),
                "cita": cita,
                "observacion_preliminar": observacion,
                "requiere_revision_especializada": True,
                "motivo": motivo,
            }
            # La propuesta de contingencia también debe cumplir el contrato.
            validacion = validar_propuesta(
                propuesta, requisito_id=requisito_id, evidencias=[mejor]
            )
            if validacion.valida:
                return propuesta

        return {
            "requisito_id": requisito_id,
            "estado_propuesto": "Requiere revisión especializada",
            "evidencia_encontrada": False,
            "fuente": None,
            "cita": None,
            "observacion_preliminar": observacion,
            "requiere_revision_especializada": True,
            "motivo": motivo,
        }

    @staticmethod
    def _propuesta_cruda(
        respuesta: RespuestaIA, requisito_id: str
    ) -> dict[str, Any]:
        """Conserva una respuesta inválida sin convertirla en conclusión."""

        return {
            "requisito_id": requisito_id,
            "estado_propuesto": "Requiere revisión especializada",
            "evidencia_encontrada": False,
            "fuente": None,
            "cita": None,
            "observacion_preliminar": (
                "La respuesta del proveedor no cumplió el contrato y fue descartada."
            ),
            "requiere_revision_especializada": True,
            "motivo": "Respuesta inválida; se conserva solo para auditoría.",
        }

    # -- Consultas y evaluación manual -----------------------------------

    def propuestas(
        self,
        expediente_id: str,
        requisito_id: str | None = None,
        *,
        solo_validas: bool = False,
        limite: int = 200,
    ) -> list[dict[str, Any]]:
        consulta = "SELECT * FROM propuestas_ia WHERE expediente_id = ?"
        parametros: list[Any] = [expediente_id]
        if requisito_id:
            consulta += " AND requisito_id = ?"
            parametros.append(requisito_id)
        if solo_validas:
            consulta += " AND valida = 1"
        consulta += " ORDER BY id DESC LIMIT ?"
        parametros.append(limite)

        with db.conectar(self.ruta_bd) as conexion:
            filas = conexion.execute(consulta, parametros).fetchall()
        propuestas = []
        for fila in filas:
            datos = db.fila_a_dict(fila) or {}
            datos["valida"] = bool(datos.get("valida"))
            datos["evidencia_encontrada"] = bool(datos.get("evidencia_encontrada"))
            datos["requiere_revision"] = bool(datos.get("requiere_revision"))
            datos["errores"] = (
                json.loads(datos["errores"]) if datos.get("errores") else []
            )
            propuestas.append(datos)
        return propuestas

    def ultima_propuesta(
        self,
        expediente_id: str,
        requisito_id: str,
        *,
        solo_valida: bool = True,
    ) -> dict[str, Any] | None:
        propuestas = self.propuestas(
            expediente_id,
            requisito_id,
            solo_validas=solo_valida,
            limite=1,
        )
        return propuestas[0] if propuestas else None

    def registrar_evaluacion_manual(
        self,
        expediente_id: str,
        requisito_id: str,
        estado: str,
        motivo: str,
        *,
        actor: str,
        evidencia_id: int | None = None,
    ) -> dict[str, Any]:
        if estado not in config.ESTADOS_REQUISITO:
            raise ValueError(
                f"Estado inválido: {estado}. Use uno de: "
                + ", ".join(config.ESTADOS_REQUISITO)
            )
        if not motivo.strip():
            raise ValueError("El motivo de la evaluación manual es obligatorio.")
        if not actor.strip():
            raise ValueError("El responsable de la evaluación es obligatorio.")

        with db.conectar(self.ruta_bd) as conexion:
            conexion.execute(
                "INSERT INTO evaluaciones_manuales "
                "(expediente_id, requisito_id, estado, motivo, actor, evidencia_id, "
                "creado_en) VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT (expediente_id, requisito_id) DO UPDATE SET "
                "estado = excluded.estado, motivo = excluded.motivo, "
                "actor = excluded.actor, evidencia_id = excluded.evidencia_id, "
                "creado_en = excluded.creado_en",
                (
                    expediente_id,
                    requisito_id,
                    estado,
                    motivo.strip(),
                    actor.strip(),
                    evidencia_id,
                    db.ahora(),
                ),
            )
            db.auditar(
                conexion,
                actor=actor.strip(),
                accion="EVALUACION_MANUAL_REGISTRADA",
                entidad="requisito",
                entidad_id=f"{expediente_id}:{requisito_id}",
                detalle={"estado": estado, "motivo": motivo.strip()},
            )
            fila = conexion.execute(
                "SELECT * FROM evaluaciones_manuales "
                "WHERE expediente_id = ? AND requisito_id = ?",
                (expediente_id, requisito_id),
            ).fetchone()
        return db.fila_a_dict(fila) or {}

    def evaluaciones(self, expediente_id: str) -> list[dict[str, Any]]:
        with db.conectar(self.ruta_bd) as conexion:
            filas = conexion.execute(
                "SELECT * FROM evaluaciones_manuales WHERE expediente_id = ? "
                "ORDER BY requisito_id",
                (expediente_id,),
            ).fetchall()
        return [db.fila_a_dict(fila) or {} for fila in filas]

    def ejecuciones(self, expediente_id: str, limite: int = 200) -> list[dict[str, Any]]:
        with db.conectar(self.ruta_bd) as conexion:
            filas = conexion.execute(
                "SELECT * FROM ejecuciones_ia WHERE expediente_id = ? "
                "ORDER BY id DESC LIMIT ?",
                (expediente_id, limite),
            ).fetchall()
        return [db.fila_a_dict(fila) or {} for fila in filas]

    # -- Resumen ---------------------------------------------------------

    def resumen(self, expediente_id: str) -> dict[str, Any]:
        evaluaciones = {
            evaluacion["requisito_id"]: evaluacion
            for evaluacion in self.evaluaciones(expediente_id)
        }
        decisiones = decisiones_vigentes(self.ruta_bd, expediente_id)
        detalles = []
        for perfil in self.perfiles.requisitos:
            evidencias = self.evidencias(expediente_id, perfil.id, solo_vigentes=False)
            alerta_integridad = any(
                evidencia.get("integridad") != ESTADO_VIGENTE
                for evidencia in evidencias
            )
            valida = self.ultima_propuesta(expediente_id, perfil.id, solo_valida=True)
            ultima = self.ultima_propuesta(expediente_id, perfil.id, solo_valida=False)
            manual = evaluaciones.get(perfil.id)
            decision = decisiones.get(perfil.id)
            referencia = decision or valida or ultima or {}

            if decision:
                estado_efectivo = decision["estado_final"]
                origen = "decision"
            elif manual:
                estado_efectivo = manual["estado"]
                origen = "manual"
            elif valida:
                estado_efectivo = valida["estado_propuesto"] or "Pendiente"
                origen = (
                    "integridad"
                    if valida.get("proveedor") == "integridad"
                    else "ia_valida"
                )
            elif ultima and ultima.get("proveedor") in PROVEEDORES_CONTINGENCIA:
                estado_efectivo = (
                    ultima.get("estado_propuesto") or "Requiere revisión especializada"
                )
                origen = "contingencia"
                alerta_integridad = alerta_integridad or (
                    ultima.get("integridad") != ESTADO_VIGENTE
                )
            else:
                estado_efectivo = "Pendiente"
                origen = "sin_analisis"

            if ultima and ultima.get("integridad") != ESTADO_VIGENTE:
                alerta_integridad = True

            if decision:
                motivo = decision.get("motivo")
            elif manual:
                motivo = manual.get("motivo")
            else:
                motivo = (valida or ultima or {}).get("motivo")

            detalles.append(
                {
                    "requisito_id": perfil.id,
                    "requisito": perfil.requisito,
                    "peso_pct": perfil.peso_pct,
                    "criterio": perfil.criterio,
                    "evidencias": len(evidencias),
                    "estado_efectivo": estado_efectivo,
                    "estado_propuesto": referencia.get("estado_propuesto"),
                    "origen": origen,
                    "propuesta_valida": bool(valida),
                    "evaluacion_manual": bool(manual),
                    "decision": decision.get("decision") if decision else None,
                    "decision_id": decision.get("id") if decision else None,
                    "decision_actor": decision.get("actor") if decision else None,
                    "decision_fecha": decision.get("creado_en") if decision else None,
                    "propuesta_id": (
                        decision.get("propuesta_id") if decision else None
                    )
                    or (valida or {}).get("id"),
                    "contingencia": origen in {"contingencia", "integridad"},
                    "integridad_alerta": alerta_integridad,
                    "motivo": motivo,
                }
            )

        peso_revisado = sum(
            detalle["peso_pct"]
            for detalle in detalles
            if detalle["origen"] != "sin_analisis"
        )
        peso_concluyente = sum(
            detalle["peso_pct"]
            for detalle in detalles
            if detalle["estado_efectivo"] in ESTADOS_CONCLUYENTES
        )
        numerador = sum(
            detalle["peso_pct"] * FACTORES[detalle["estado_efectivo"]]
            for detalle in detalles
            if detalle["estado_efectivo"] in ESTADOS_CONCLUYENTES
        )
        cumplimiento = (
            float(
                (Decimal(numerador) / Decimal(peso_concluyente) * Decimal(100)).quantize(
                    Decimal("0.1"), rounding=ROUND_HALF_UP
                )
            )
            if peso_concluyente
            else None
        )
        avance = avance_ponderado(self.perfiles, detalles)
        conteo_decisiones = {"aceptar": 0, "modificar": 0, "descartar": 0}
        for detalle in detalles:
            if detalle["decision"] in conteo_decisiones:
                conteo_decisiones[detalle["decision"]] += 1

        return {
            "expediente_id": expediente_id,
            "requisitos_total": len(detalles),
            "peso_total_pct": self.perfiles.peso_total,
            "peso_revisado_pct": peso_revisado,
            "cobertura_revision_pct": float(
                Decimal(peso_revisado).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            ),
            "peso_concluyente_pct": peso_concluyente,
            "cumplimiento_pct": cumplimiento,
            "peso_decidido_pct": avance["peso_decidido_pct"],
            "avance_pct": avance["avance_pct"],
            "avance_formula": avance["formula"],
            "con_propuesta_valida": sum(
                1 for detalle in detalles if detalle["propuesta_valida"]
            ),
            "con_evaluacion_manual": sum(
                1 for detalle in detalles if detalle["evaluacion_manual"]
            ),
            "contingencias": sum(
                1 for detalle in detalles if detalle["contingencia"]
            ),
            "decisiones_registradas": sum(
                1 for detalle in detalles if detalle["decision"]
            ),
            "aceptadas": conteo_decisiones["aceptar"],
            "modificadas": conteo_decisiones["modificar"],
            "descartadas": conteo_decisiones["descartar"],
            "requiere_revision": sum(
                1
                for detalle in detalles
                if detalle["estado_efectivo"] == "Requiere revisión especializada"
            ),
            "sin_informacion": sum(
                1
                for detalle in detalles
                if detalle["estado_efectivo"] == "No se encontró información"
            ),
            "cumple": sum(
                1 for detalle in detalles if detalle["estado_efectivo"] == "Cumple"
            ),
            "parcial": sum(
                1
                for detalle in detalles
                if detalle["estado_efectivo"] == "Cumple parcialmente"
            ),
            "no_cumple": sum(
                1 for detalle in detalles if detalle["estado_efectivo"] == "No cumple"
            ),
            "pendientes": sum(
                1 for detalle in detalles if detalle["estado_efectivo"] == "Pendiente"
            ),
            "integridad_alertas": sum(
                1 for detalle in detalles if detalle["integridad_alerta"]
            ),
            "requisitos": detalles,
        }

    # -- Exportación -----------------------------------------------------

    def exportar_resultados_csv(
        self, expediente_id: str, destino: str | Path
    ) -> Path:
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        resumen = self.resumen(expediente_id)
        columnas = [
            "requisito_id",
            "requisito",
            "peso_pct",
            "evidencias",
            "estado_propuesto",
            "estado_efectivo",
            "decision",
            "origen",
            "propuesta_valida",
            "evaluacion_manual",
            "decision_actor",
            "decision_fecha",
            "contingencia",
            "integridad_alerta",
            "motivo",
        ]
        with destino.open("w", encoding="utf-8", newline="") as manejador:
            escritor = csv.DictWriter(manejador, fieldnames=columnas)
            escritor.writeheader()
            for detalle in resumen["requisitos"]:
                escritor.writerow({clave: detalle.get(clave) for clave in columnas})
        return destino

    def exportar_propuestas_csv(
        self, expediente_id: str, destino: str | Path
    ) -> Path:
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        columnas = [
            "id",
            "requisito_id",
            "proveedor",
            "modelo",
            "estado_propuesto",
            "evidencia_encontrada",
            "archivo",
            "ubicacion",
            "sha256_fuente",
            "cita",
            "requiere_revision",
            "valida",
            "integridad",
            "huella",
            "errores",
            "creado_en",
        ]
        with destino.open("w", encoding="utf-8", newline="") as manejador:
            escritor = csv.DictWriter(manejador, fieldnames=columnas)
            escritor.writeheader()
            for propuesta in self.propuestas(expediente_id, limite=1000):
                fila = {clave: propuesta.get(clave) for clave in columnas}
                fila["errores"] = json.dumps(
                    propuesta.get("errores", []), ensure_ascii=False
                )
                escritor.writerow(fila)
        return destino

    def exportar_decisiones_csv(
        self, expediente_id: str, destino: str | Path
    ) -> Path:
        """Exporta el historial completo de decisiones con la propuesta original."""

        from .evaluation import historial

        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        columnas = [
            "id",
            "requisito_id",
            "decision",
            "estado_propuesto",
            "estado_final",
            "motivo",
            "actor",
            "version_kb",
            "propuesta_id",
            "huella_propuesta",
            "archivo",
            "ubicacion",
            "cita",
            "es_vigente",
            "creado_en",
        ]
        with destino.open("w", encoding="utf-8", newline="") as manejador:
            escritor = csv.DictWriter(manejador, fieldnames=columnas)
            escritor.writeheader()
            for registro in historial(self.ruta_bd, expediente_id, limite=2000):
                escritor.writerow({clave: registro.get(clave) for clave in columnas})
        return destino
