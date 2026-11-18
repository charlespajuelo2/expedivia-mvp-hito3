"""Servicio de IA y proveedores del MVP (Etapa 3).

Proveedores incluidos:

- ``ProveedorReglas``: determinista, sin red. Es el modo por defecto y sirve
  como línea base reproducible y como contingencia.
- ``ProveedorOpenAICompatible``: cliente mínimo para APIs compatibles con
  ``/chat/completions``. Las credenciales se leen de variables de entorno.
- ``ProveedorGuionizado`` y ``ProveedorFallido``: utilidades de prueba para
  validar rechazos, reintentos y contingencia sin llamar a un servicio externo.

Ningún proveedor decide por sí mismo: la respuesta siempre pasa por
``ai_contract.validar_propuesta`` antes de mostrarse o persistirse.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from . import config
from .ai_contract import MIN_CITA
from .evidence import Evidencia, PerfilEvidencia, puntuar_texto


# --- Errores y respuestas -------------------------------------------------


class ErrorIA(Exception):
    """Error controlado de un proveedor de IA."""

    def __init__(
        self,
        codigo: str,
        mensaje: str,
        *,
        reintentable: bool = False,
        detalle: str | None = None,
    ) -> None:
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje
        self.reintentable = reintentable
        self.detalle = detalle

    def a_dict(self) -> dict[str, Any]:
        return {
            "codigo": self.codigo,
            "mensaje": self.mensaje,
            "reintentable": self.reintentable,
            "detalle": self.detalle or "",
        }


@dataclass
class RespuestaIA:
    """Respuesta cruda de un proveedor, antes de validar el contrato."""

    texto_crudo: str
    proveedor: str
    modelo: str
    contenido: dict[str, Any] | None = None
    tokens_entrada: int = 0
    tokens_salida: int = 0
    duracion_ms: int = 0


@dataclass
class ContextoAnalisis:
    """Contexto mínimo enviado al proveedor."""

    expediente_id: str
    perfil: PerfilEvidencia
    evidencias: list[Evidencia]
    max_caracteres: int = config.IA_MAX_CARACTERES_EVIDENCIA
    max_evidencias: int = config.IA_MAX_EVIDENCIAS

    def evidencias_para_prompt(self) -> list[dict[str, Any]]:
        return [
            {
                "documento_id": evidencia.documento_id,
                "archivo": evidencia.archivo,
                "tipo_documental": evidencia.tipo_documental,
                "ubicacion": evidencia.ubicacion,
                "sha256": evidencia.sha256_fuente,
                "puntaje": evidencia.puntaje,
                "texto": evidencia.texto[: self.max_caracteres],
            }
            for evidencia in self.evidencias[: self.max_evidencias]
        ]


# --- Extracción de cita ---------------------------------------------------


def _patron_acentos(termino: str) -> re.Pattern[str]:
    """Patrón que localiza un término aunque el texto original lleve tildes."""

    mapa = {
        "a": "[aáàäâ]",
        "e": "[eéèëê]",
        "i": "[iíìïî]",
        "o": "[oóòöô]",
        "u": "[uúùüû]",
        "n": "[nñ]",
    }
    piezas = [mapa.get(caracter, re.escape(caracter)) for caracter in termino.lower()]
    return re.compile(r"(?<![a-z0-9])" + "".join(piezas) + r"(?:s|es)?(?![a-z0-9])")


def _candidatos_cita(texto: str) -> list[str]:
    candidatos: list[str] = []
    for linea in texto.split("\n"):
        linea = linea.strip()
        if not linea:
            continue
        partes = re.split(r"(?<=[.;:])\s+", linea)
        candidatos.extend(parte.strip() for parte in partes if parte.strip())
    return candidatos


def _ventana_alrededor(texto: str, terminos: list[str], maximo: int) -> str:
    posicion = -1
    for termino in sorted(terminos, key=len, reverse=True):
        coincidencia = _patron_acentos(termino).search(texto)
        if coincidencia and (posicion < 0 or coincidencia.start() < posicion):
            posicion = coincidencia.start()
    if posicion < 0:
        return texto[:maximo].strip()
    inicio = max(0, posicion - 80)
    fin = min(len(texto), inicio + maximo)
    if fin - inicio < maximo:
        inicio = max(0, fin - maximo)
    return texto[inicio:fin].strip()


def _recortar_por_celdas(texto: str, terminos: list[str], maximo: int) -> str:
    segmentos = texto.split(" | ")
    if len(segmentos) == 1:
        return _ventana_alrededor(texto, terminos, maximo)
    indices = [
        indice
        for indice, segmento in enumerate(segmentos)
        if puntuar_texto(segmento, {termino: 1 for termino in terminos})[1]
    ]
    if not indices:
        return _ventana_alrededor(texto, terminos, maximo)
    inicio = max(0, indices[0] - 1)
    fin = min(len(segmentos), indices[-1] + 2)
    recorte = " | ".join(segmentos[inicio:fin])
    if len(recorte) <= maximo:
        return recorte
    return _ventana_alrededor(recorte, terminos, maximo)


def extraer_cita(texto: str, terminos: list[str], maximo: int = 360) -> str:
    """Selecciona una cita literal y representativa del fragmento.

    La cita devuelta siempre es una subcadena continua del texto original.
    """

    candidatos = _candidatos_cita(texto)
    if not candidatos:
        candidatos = [texto]

    mejor = max(
        candidatos,
        key=lambda candidato: (
            puntuar_texto(candidato, {termino: 1 for termino in terminos})[0],
            len(candidato),
        ),
    )
    if len(mejor) > maximo:
        mejor = _recortar_por_celdas(mejor, terminos, maximo)

    cita = mejor.strip()
    if len(cita) < MIN_CITA:
        # Un fragmento muy corto no sirve como cita; se toma una ventana mayor.
        cita = _ventana_alrededor(texto, terminos, min(maximo, max(MIN_CITA, len(texto))))
    return cita


# --- Proveedores ----------------------------------------------------------


class ProveedorIA:
    """Interfaz mínima de un proveedor de IA."""

    nombre = "base"
    modelo = ""

    def generar(self, contexto: ContextoAnalisis) -> RespuestaIA:
        raise NotImplementedError


class ProveedorReglas(ProveedorIA):
    """Proveedor determinista basado en perfiles y evidencia recuperada.

    No sustituye el juicio del especialista: solo concluye cuando el tipo
    documental es prueba directa, el puntaje alcanza el umbral y el requisito no
    exige juicio de ingeniería. En los demás casos escala a revisión.
    """

    nombre = "reglas"
    modelo = "determinista-v1"

    def generar(self, contexto: ContextoAnalisis) -> RespuestaIA:
        perfil = contexto.perfil
        evidencias = contexto.evidencias

        if not evidencias:
            propuesta = {
                "requisito_id": perfil.id,
                "estado_propuesto": "No se encontró información",
                "evidencia_encontrada": False,
                "fuente": None,
                "cita": None,
                "observacion_preliminar": (
                    "No se localizaron fragmentos con los términos del requisito por "
                    "encima del puntaje mínimo. La ausencia de evidencia no equivale a "
                    "incumplimiento."
                ),
                "requiere_revision_especializada": False,
                "motivo": (
                    "Sin evidencia recuperada en los documentos válidos y clasificados "
                    "del expediente."
                ),
            }
            return RespuestaIA(
                texto_crudo=json.dumps(propuesta, ensure_ascii=False),
                proveedor=self.nombre,
                modelo=self.modelo,
                contenido=propuesta,
            )

        pruebas = [
            evidencia
            for evidencia in evidencias
            if evidencia.tipo_documental in perfil.tipos_que_prueban
        ]
        mejor = max(pruebas or evidencias, key=lambda evidencia: evidencia.puntaje)
        es_prueba = mejor.tipo_documental in perfil.tipos_que_prueban
        cita = extraer_cita(mejor.texto, mejor.terminos)

        if not es_prueba:
            estado = "Requiere revisión especializada"
            revision = True
            motivo = (
                f"La evidencia localizada es de tipo '{mejor.tipo_documental}', que no "
                "acredita por sí misma el requisito. Se requiere revisión especializada."
            )
            observacion = (
                f"Se localizó evidencia en {mejor.archivo} · {mejor.ubicacion} "
                f"(puntaje {mejor.puntaje}). El fragmento menciona el requisito, pero "
                "no es una prueba directa del cumplimiento."
            )
        elif perfil.requiere_juicio:
            estado = "Requiere revisión especializada"
            revision = True
            motivo = (
                "El tipo documental es el esperado, pero el criterio exige juicio de "
                "ingeniería (coherencia o trazabilidad) que el MVP no automatiza."
            )
            observacion = (
                f"Se localizó evidencia directa en {mejor.archivo} · {mejor.ubicacion} "
                f"(puntaje {mejor.puntaje}). La coherencia técnica debe validarla una "
                "persona."
            )
        elif mejor.puntaje >= perfil.puntaje_cumple:
            estado = "Cumple"
            revision = False
            motivo = (
                f"La evidencia de tipo '{mejor.tipo_documental}' contiene los elementos "
                f"del criterio y alcanza {mejor.puntaje} puntos (umbral "
                f"{perfil.puntaje_cumple})."
            )
            observacion = (
                f"Se localizó evidencia directa en {mejor.archivo} · {mejor.ubicacion} "
                f"(puntaje {mejor.puntaje}). Términos encontrados: "
                f"{', '.join(mejor.terminos)}. La conclusión es preliminar y queda "
                "sujeta a validación humana."
            )
        else:
            estado = "Cumple parcialmente"
            revision = False
            motivo = (
                f"La evidencia de tipo '{mejor.tipo_documental}' cubre solo parte de "
                f"los elementos del criterio ({mejor.puntaje} de "
                f"{perfil.puntaje_cumple} puntos)."
            )
            observacion = (
                f"Se localizó evidencia en {mejor.archivo} · {mejor.ubicacion} "
                f"(puntaje {mejor.puntaje}). Faltan elementos para una conclusión "
                "completa."
            )

        propuesta = {
            "requisito_id": perfil.id,
            "estado_propuesto": estado,
            "evidencia_encontrada": True,
            "fuente": mejor.fuente(),
            "cita": cita,
            "observacion_preliminar": observacion,
            "requiere_revision_especializada": revision,
            "motivo": motivo,
        }
        return RespuestaIA(
            texto_crudo=json.dumps(propuesta, ensure_ascii=False),
            proveedor=self.nombre,
            modelo=self.modelo,
            contenido=propuesta,
        )


def _transporte_urllib(
    url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int
) -> dict[str, Any]:
    datos = json.dumps(payload).encode("utf-8")
    solicitud = urllib.request.Request(url, data=datos, headers=headers, method="POST")
    with urllib.request.urlopen(solicitud, timeout=timeout) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


class ProveedorOpenAICompatible(ProveedorIA):
    """Cliente mínimo para APIs compatibles con ``/chat/completions``."""

    nombre = "openai-compatible"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        modelo: str | None = None,
        timeout: int | None = None,
        max_intentos: int | None = None,
        espera_reintento: float | None = None,
        transporte: Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]]
        | None = None,
    ) -> None:
        self.base_url = (base_url or config.IA_BASE_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else config.IA_API_KEY
        self.modelo = modelo or config.IA_MODELO
        self.timeout = timeout or config.IA_TIMEOUT
        self.max_intentos = max_intentos or config.IA_MAX_INTENTOS
        self.espera_reintento = (
            config.IA_ESPERA_REINTENTO if espera_reintento is None else espera_reintento
        )
        self.transporte = transporte or _transporte_urllib

    def generar(self, contexto: ContextoAnalisis) -> RespuestaIA:
        if not self.api_key:
            raise ErrorIA(
                "IA_NO_CONFIGURADA",
                "No hay API key configurada. Defina MVP_IA_API_KEY o use el proveedor "
                "de reglas.",
                reintentable=False,
            )

        payload = self._payload(contexto)
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        ultimo_error: ErrorIA | None = None
        for intento in range(1, self.max_intentos + 1):
            inicio = time.perf_counter()
            try:
                datos = self.transporte(url, headers, payload, self.timeout)
                duracion = int((time.perf_counter() - inicio) * 1000)
                return self._parsear(datos, duracion)
            except urllib.error.HTTPError as exc:
                detalle = ""
                try:
                    detalle = exc.read().decode("utf-8", errors="replace")[:500]
                except Exception:
                    pass
                reintentable = exc.code == 429 or exc.code >= 500
                ultimo_error = ErrorIA(
                    "IA_ERROR_HTTP",
                    f"El servicio de IA respondió HTTP {exc.code}.",
                    reintentable=reintentable,
                    detalle=detalle,
                )
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                ultimo_error = ErrorIA(
                    "IA_NO_DISPONIBLE",
                    "No se pudo conectar con el servicio de IA.",
                    reintentable=True,
                    detalle=str(exc),
                )
            except ValueError as exc:
                ultimo_error = ErrorIA(
                    "IA_RESPUESTA_INVALIDA",
                    "El servicio de IA devolvió una respuesta que no es JSON.",
                    reintentable=True,
                    detalle=str(exc),
                )

            if not ultimo_error.reintentable or intento >= self.max_intentos:
                break
            if self.espera_reintento:
                time.sleep(self.espera_reintento * (2 ** (intento - 1)))

        assert ultimo_error is not None
        raise ultimo_error

    def _payload(self, contexto: ContextoAnalisis) -> dict[str, Any]:
        sistema = (
            "Eres un asistente que evalúa requisitos de expedientes técnicos viales. "
            "Devuelve EXCLUSIVAMENTE un objeto JSON con estas claves exactas: "
            "requisito_id, estado_propuesto, evidencia_encontrada, fuente, cita, "
            "observacion_preliminar, requiere_revision_especializada, motivo. "
            "estado_propuesto debe ser uno de: Cumple, Cumple parcialmente, No cumple, "
            "No se encontró información, Requiere revisión especializada. "
            "Si hay evidencia, fuente debe ser un objeto con documento_id, archivo, "
            "ubicacion y sha256, y cita debe ser una subcadena literal del texto del "
            "fragmento. No inventes fuentes, hashes ni citas. Si no hay evidencia "
            "suficiente, usa 'No se encontró información' con fuente y cita nulas. "
            "Si la evidencia no acredita el requisito o requiere juicio de ingeniería, "
            "usa 'Requiere revisión especializada' con "
            "requiere_revision_especializada=true. No agregues claves adicionales."
        )
        contexto_usuario = {
            "expediente_id": contexto.expediente_id,
            "requisito_id": contexto.perfil.id,
            "requisito": contexto.perfil.requisito,
            "criterio": contexto.perfil.criterio,
            "evidencia_esperada": contexto.perfil.evidencia_esperada,
            "tipos_que_prueban": list(contexto.perfil.tipos_que_prueban),
            "requiere_juicio_ingenieria": contexto.perfil.requiere_juicio,
            "evidencias": contexto.evidencias_para_prompt(),
        }
        return {
            "model": self.modelo,
            "temperature": 0.0,
            "max_tokens": 700,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": sistema},
                {
                    "role": "user",
                    "content": json.dumps(contexto_usuario, ensure_ascii=False),
                },
            ],
        }

    def _parsear(self, datos: dict[str, Any], duracion_ms: int) -> RespuestaIA:
        if not isinstance(datos, dict):
            raise ErrorIA(
                "IA_RESPUESTA_INVALIDA",
                "La respuesta del servicio no es un objeto JSON.",
                reintentable=True,
            )
        if "error" in datos:
            raise ErrorIA(
                "IA_ERROR_SERVICIO",
                "El servicio de IA devolvió un error.",
                reintentable=False,
                detalle=json.dumps(datos["error"], ensure_ascii=False)[:500],
            )
        try:
            contenido = datos["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ErrorIA(
                "IA_RESPUESTA_INVALIDA",
                "La respuesta no contiene 'choices[0].message.content'.",
                reintentable=True,
                detalle=str(exc),
            ) from exc
        if not isinstance(contenido, str) or not contenido.strip():
            raise ErrorIA(
                "IA_RESPUESTA_VACIA",
                "El servicio de IA devolvió contenido vacío.",
                reintentable=True,
            )
        uso = datos.get("usage") or {}
        return RespuestaIA(
            texto_crudo=contenido,
            proveedor=self.nombre,
            modelo=str(datos.get("model") or self.modelo),
            tokens_entrada=int(uso.get("prompt_tokens") or 0),
            tokens_salida=int(uso.get("completion_tokens") or 0),
            duracion_ms=duracion_ms,
        )


class ProveedorGuionizado(ProveedorIA):
    """Proveedor de prueba que devuelve respuestas predefinidas en orden."""

    nombre = "guionizado"

    def __init__(
        self,
        respuestas: list[Any],
        *,
        modelo: str = "guion-v1",
        nombre: str | None = None,
    ) -> None:
        self.respuestas = list(respuestas)
        self.modelo = modelo
        self.nombre = nombre or self.nombre
        self.llamadas = 0

    def generar(self, contexto: ContextoAnalisis) -> RespuestaIA:
        self.llamadas += 1
        if not self.respuestas:
            raise ErrorIA(
                "GUION_AGOTADO",
                "El proveedor guionizado no tiene más respuestas.",
                reintentable=False,
            )
        respuesta = self.respuestas.pop(0)
        if isinstance(respuesta, BaseException):
            if isinstance(respuesta, ErrorIA):
                raise respuesta
            raise ErrorIA(
                "GUION_ERROR",
                str(respuesta),
                reintentable=False,
                detalle=type(respuesta).__name__,
            )
        if isinstance(respuesta, dict):
            texto = json.dumps(respuesta, ensure_ascii=False)
            contenido = respuesta
        else:
            texto = str(respuesta)
            contenido = None
        return RespuestaIA(
            texto_crudo=texto,
            proveedor=self.nombre,
            modelo=self.modelo,
            contenido=contenido,
        )


class ProveedorFallido(ProveedorIA):
    """Proveedor que siempre falla, para demostrar la contingencia."""

    nombre = "fallido"

    def __init__(
        self,
        *,
        codigo: str = "IA_NO_DISPONIBLE",
        mensaje: str = "El servicio de IA no está disponible.",
        reintentable: bool = True,
        modelo: str = "sin-servicio",
    ) -> None:
        self.codigo = codigo
        self.mensaje = mensaje
        self.reintentable = reintentable
        self.modelo = modelo

    def generar(self, contexto: ContextoAnalisis) -> RespuestaIA:
        raise ErrorIA(
            self.codigo,
            self.mensaje,
            reintentable=self.reintentable,
            detalle="Proveedor de contingencia para pruebas.",
        )
