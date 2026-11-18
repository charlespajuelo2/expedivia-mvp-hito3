"""Genera el video demo narrado de la Etapa 6.

El video se graba con Playwright sobre la app real y la narración se sintetiza
con la voz española de Windows. No sustituye una grabación humana: el guion y
las limitaciones quedan declarados en ``07_guion_video.md``.

Uso::

    python -m mvp.scripts.grabar_video_etapa6

Requiere la app en ``http://localhost:8511`` con la base de la Etapa 6.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

RAIZ = Path(__file__).resolve().parents[2]
ENTREGA = RAIZ / "mvp" / "etapa6" / "entrega"
VIDEO = ENTREGA / "video_demo.mp4"
NARRACION = ENTREGA / "narracion_demo.wav"
GUION_JSON = ENTREGA / "video_timeline.json"
URL = "http://localhost:8511"

ESCENAS = [
    {
        "id": "intro",
        "titulo": "Apertura",
        "texto": (
            "Este es Expedivia, el MVP para revisar expedientes técnicos viales. "
            "Trabajamos con el caso EXP 2024 089: una carretera con ocho documentos "
            "y siete requisitos. La meta no es reemplazar al especialista, sino darle "
            "evidencia verificable y un rastro claro de cada decisión."
        ),
    },
    {
        "id": "carga",
        "titulo": "Carga y clasificación",
        "texto": (
            "Empezamos por la carga. El sistema valida el formato, calcula el hash de "
            "cada archivo y reutiliza la extracción si el documento ya existe. Después "
            "clasifica el documento. Si el nombre no describe el contenido, el especialista "
            "corrige la clasificación y esa corrección queda vinculada al hash."
        ),
    },
    {
        "id": "extraccion",
        "titulo": "Extracción con ubicación",
        "texto": (
            "La extracción conserva la ubicación exacta. En un PDF, la página; en Word, "
            "el párrafo; en Excel, la hoja y la fila. Cada fragmento se puede abrir y "
            "contrastar. Esto es lo que convierte una cita en evidencia verificable y no "
            "en una afirmación sin respaldo."
        ),
    },
    {
        "id": "evidencia",
        "titulo": "Evidencia y contrato",
        "texto": (
            "En la pestaña de evidencia, el sistema recupera fragmentos para cada requisito "
            "y los somete a un contrato JSON estricto: archivo, ubicación, cita, hash y "
            "estado. Si una fuente cambia después del análisis, la integridad se marca y la "
            "propuesta deja de ser confiable. La persona puede revisar o registrar una "
            "evaluación manual."
        ),
    },
    {
        "id": "decision",
        "titulo": "Decisión y avance",
        "texto": (
            "Aquí está el corazón del MVP: la decisión es humana. El especialista acepta, "
            "modifica o descarta con un motivo obligatorio. El historial es inmutable y solo "
            "una decisión por requisito queda vigente. El avance ponderado se calcula "
            "únicamente con esas decisiones: en este caso, treinta y nueve por ciento, con "
            "cuatro de siete requisitos decididos."
        ),
    },
    {
        "id": "exportacion",
        "titulo": "Informes",
        "texto": (
            "Con los datos ya persistidos, se generan los informes. El Excel y el Word se "
            "construyen desde SQLite, no desde una plantilla con datos fijos. El informe "
            "conserva las fuentes, las decisiones y las métricas. El resultado queda "
            "disponible para descargar y volver a auditar."
        ),
    },
    {
        "id": "auditoria",
        "titulo": "Auditoría",
        "texto": (
            "La auditoría muestra el rastro de cada acción: documentos, propuestas, "
            "decisiones y verificaciones de integridad. También permite explicar cómo se "
            "llegó a un resultado y qué cambió entre una versión y otra. Sin ese rastro, "
            "la revisión no sería defendible."
        ),
    },
    {
        "id": "permisos",
        "titulo": "Control de acceso",
        "texto": (
            "El acceso también se controla. Un lector puede consultar el expediente, pero no "
            "decidir ni exportar. El bloqueo se explica en pantalla, con el rol y el permiso "
            "que falta. No es un error silencioso: es una regla visible."
        ),
    },
    {
        "id": "cierre",
        "titulo": "Cierre",
        "texto": (
            "Quedan límites claros: no hay OCR para documentos escaneados, la IA real es "
            "opcional, los datos son sintéticos y falta el feedback formal de un especialista. "
            "Expedivia no decide por la persona: le da evidencia para decidir mejor. Ese es "
            "el siguiente paso antes de un piloto."
        ),
    },
]

PAUSA = 1.35
RATE = 20


def _tts(texto: str, destino: Path) -> None:
    script = destino.with_suffix(".ps1")
    contenido = f"""Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('Microsoft Helena Desktop')
$s.Rate = {RATE}
$s.SetOutputToWaveFile('{destino}')
$s.Speak('{texto}')
$s.Dispose()
"""
    script.write_text(contenido, encoding="utf-8-sig")
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        check=True,
        capture_output=True,
    )


def _duracion_wav(ruta: Path) -> float:
    with wave.open(str(ruta), "rb") as archivo:
        return archivo.getnframes() / archivo.getframerate()


def _preparar_narracion(carpeta: Path, lead_in: float) -> tuple[Path, list[float]]:
    duraciones: list[float] = []
    for escena in ESCENAS:
        destino = carpeta / f"{escena['id']}.wav"
        _tts(escena["texto"], destino)
        duraciones.append(_duracion_wav(destino))
        print(f"  narración {escena['id']}: {duraciones[-1]:.1f} s")

    with wave.open(str(carpeta / f"{ESCENAS[0]['id']}.wav"), "rb") as primero:
        canales = primero.getnchannels()
        ancho = primero.getsampwidth()
        tasa = primero.getframerate()

    silencio = b"\x00" * int(tasa * ancho * canales)
    salida = wave.open(str(NARRACION), "wb")
    salida.setnchannels(canales)
    salida.setsampwidth(ancho)
    salida.setframerate(tasa)
    salida.writeframes(silencio * int(lead_in))
    for indice, escena in enumerate(ESCENAS):
        with wave.open(str(carpeta / f"{escena['id']}.wav"), "rb") as archivo:
            salida.writeframes(archivo.readframes(archivo.getnframes()))
        salida.writeframes(silencio * int(PAUSA))
    salida.close()
    return NARRACION, [d + PAUSA for d in duraciones]


def _esperar_hasta(inicio: float, objetivo: float) -> None:
    restante = objetivo - (time.monotonic() - inicio)
    if restante > 0:
        time.sleep(restante)


def _ir_pestana(pagina: Page, indice: int) -> None:
    pagina.locator("[role=tab]").nth(indice).click()
    pagina.wait_for_timeout(1200)


def _cambiar_usuario(pagina: Page, nombre: str) -> None:
    combo = pagina.get_by_role("combobox", name="Usuario").first
    combo.click()
    combo.fill(nombre)
    pagina.wait_for_timeout(400)
    pagina.keyboard.press("Enter")
    pagina.wait_for_timeout(2200)


def _medir_carga() -> float:
    with sync_playwright() as p:
        navegador = p.chromium.launch(channel="msedge", headless=True)
        pagina = navegador.new_page(viewport={"width": 1440, "height": 900})
        inicio = time.monotonic()
        pagina.goto(URL, wait_until="load", timeout=60000)
        pagina.get_by_text("Expedivia MVP").first.wait_for(timeout=60000)
        medido = time.monotonic() - inicio
        navegador.close()
    return medido


def _grabar(carpeta_video: Path, lead_in: float, duraciones: list[float]) -> Path:
    with sync_playwright() as p:
        navegador = p.chromium.launch(channel="msedge", headless=True)
        contexto = navegador.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir=str(carpeta_video),
            record_video_size={"width": 1440, "height": 900},
        )
        pagina = contexto.new_page()
        video = pagina.video
        inicio = time.monotonic()
        pagina.goto(URL, wait_until="load", timeout=60000)
        pagina.get_by_text("Expedivia MVP").first.wait_for(timeout=60000)
        pagina.wait_for_timeout(1500)
        medido = time.monotonic() - inicio
        print(f"  carga real: {medido:.2f} s; lead-in de audio: {lead_in:.2f} s")

        acumulado = lead_in
        objetivos = []
        for duracion in duraciones:
            objetivos.append(acumulado)
            acumulado += duracion

        # Escena 1: apertura.
        _esperar_hasta(inicio, objetivos[0])
        pagina.mouse.move(720, 430)
        pagina.wait_for_timeout(1000)

        # Escena 2: documentos y clasificación.
        _esperar_hasta(inicio, objetivos[1])
        _ir_pestana(pagina, 1)
        pagina.evaluate("document.querySelector('section.stMain').scrollTop = 260")
        pagina.wait_for_timeout(1000)

        # Escena 3: extracción de un PDF real.
        _esperar_hasta(inicio, objetivos[2])
        _ir_pestana(pagina, 2)
        combo = pagina.get_by_role("combobox", name="Documento").first
        combo.click()
        combo.fill("TDR")
        pagina.wait_for_timeout(400)
        pagina.keyboard.press("Enter")
        pagina.wait_for_timeout(1500)
        pagina.evaluate("document.querySelector('section.stMain').scrollTop = 220")

        # Escena 4: evidencia y contrato.
        _esperar_hasta(inicio, objetivos[3])
        _ir_pestana(pagina, 3)
        pagina.evaluate("document.querySelector('section.stMain').scrollTop = 260")

        # Escena 5: decisión, historial y avance.
        _esperar_hasta(inicio, objetivos[4])
        _ir_pestana(pagina, 4)
        pagina.evaluate("document.querySelector('section.stMain').scrollTop = 0")
        pagina.wait_for_timeout(9000)
        combo = pagina.get_by_role("combobox", name="Requisito").last
        combo.click()
        combo.fill("RQ-04")
        pagina.wait_for_timeout(400)
        pagina.keyboard.press("Enter")
        pagina.wait_for_timeout(1600)
        pagina.evaluate("document.querySelector('section.stMain').scrollTop = 980")

        # Escena 6: exportación real.
        _esperar_hasta(inicio, objetivos[5])
        _ir_pestana(pagina, 5)
        pagina.get_by_role("button", name="Generar informe Excel y Word").click()
        pagina.get_by_text("Descargar").first.wait_for(timeout=60000)
        pagina.wait_for_timeout(1200)
        pagina.evaluate("document.querySelector('section.stMain').scrollTop = 190")

        # Escena 7: auditoría.
        _esperar_hasta(inicio, objetivos[6])
        _ir_pestana(pagina, 6)
        pagina.evaluate("document.querySelector('section.stMain').scrollTop = 260")

        # Escena 8: bloqueo por rol.
        _esperar_hasta(inicio, objetivos[7])
        _cambiar_usuario(pagina, "Carlos")
        _ir_pestana(pagina, 4)
        pagina.evaluate("document.querySelector('section.stMain').scrollTop = 1000")
        pagina.wait_for_timeout(8000)
        _cambiar_usuario(pagina, "Lucía")

        # Escena 9: guía y cierre.
        _esperar_hasta(inicio, objetivos[8])
        _ir_pestana(pagina, 7)
        pagina.evaluate(
            "() => { const h = [...document.querySelectorAll('h3')]"
            ".find(e => e.innerText.includes('Etapa 6'));"
            "if (h) h.scrollIntoView({block: 'start'}); }"
        )
        pagina.wait_for_timeout(1800)
        pagina.evaluate("document.querySelector('section.stMain').scrollTop += 380")
        _esperar_hasta(inicio, acumulado + 0.6)

        contexto.close()
        ruta = video.path()
        navegador.close()
    return Path(ruta)


def _ffmpeg() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError):
        base = Path(os.environ["LOCALAPPDATA"]) / "ms-playwright"
        candidatos = sorted(base.glob("ffmpeg-*/ffmpeg-win64.exe"))
        if not candidatos:
            raise FileNotFoundError("No se encontró ffmpeg (imageio-ffmpeg ni Playwright).")
        return str(candidatos[-1])


def _unir(video: Path, audio: Path) -> None:
    comando = [
        _ffmpeg(),
        "-y",
        "-i",
        str(video),
        "-i",
        str(audio),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(VIDEO),
    ]
    resultado = subprocess.run(comando, capture_output=True, text=True)
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr[-3000:])
    print(f"  video final: {VIDEO} ({VIDEO.stat().st_size / 1_048_576:.1f} MB)")


def main() -> int:
    ENTREGA.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="expedivia_video_") as temporal:
        carpeta = Path(temporal)
        print("1/5 Midiendo la carga real...")
        carga = _medir_carga()
        lead_in = round(max(3.0, carga + 1.2), 1)
        print(f"  carga: {carga:.2f} s; lead-in elegido: {lead_in:.1f} s")

        print("2/5 Sintetizando narración...")
        narracion, duraciones = _preparar_narracion(carpeta, lead_in=lead_in)

        print("3/5 Grabando la app...")
        video = _grabar(carpeta / "video", lead_in=lead_in, duraciones=duraciones)

        print("4/5 Ajustando audio y video...")
        _unir(video, narracion)

        print("5/5 Guardando guion y línea de tiempo...")
        GUION_JSON.write_text(
            json.dumps(
                {
                    "formato": "video demo narrado con capturas reales de la app",
                    "voz": "Microsoft Helena Desktop (es-ES), síntesis",
                    "escenas": [
                        {
                            "id": escena["id"],
                            "titulo": escena["titulo"],
                            "texto": escena["texto"],
                            "segundos": round(duracion, 1),
                        }
                        for escena, duracion in zip(ESCENAS, duraciones)
                    ],
                    "duracion_estimada_s": round(sum(duraciones) + lead_in, 1),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    print("Video demo generado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
