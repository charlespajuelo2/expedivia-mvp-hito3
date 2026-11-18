"""Captura pantallas reales de la app para la entrega del Hito 3.

Requiere la app en ``http://localhost:8511`` con la base de la Etapa 6::

    $env:MVP_DB_PATH = "...\\mvp\\etapa6\\evidencia\\mvp_etapa6.db"
    python -m streamlit run mvp/app.py --server.port 8511 --server.headless true

Luego::

    python -m mvp.scripts.capturar_pantallas_etapa6
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

URL = "http://localhost:8511"
DESTINO = Path(__file__).resolve().parents[1] / "etapa6" / "entrega" / "capturas"


def _pestana(pagina: Page, indice: int, texto: str) -> None:
    pagina.locator("[role=tab]").nth(indice).click()
    pagina.get_by_text(texto).first.wait_for(timeout=20000)


def _arriba(pagina: Page) -> None:
    pagina.evaluate("document.querySelector('section.stMain').scrollTop = 0")
    pagina.wait_for_timeout(500)


def _capturar(pagina: Page, nombre: str) -> None:
    _arriba(pagina)
    ruta = DESTINO / f"{nombre}.png"
    pagina.screenshot(path=str(ruta), full_page=False)
    print(f"capturada {ruta.name}")


def _elegir_requisito(pagina: Page, requisito: str) -> None:
    combo = pagina.get_by_role("combobox", name="Requisito").last
    combo.click()
    combo.fill(requisito)
    pagina.wait_for_timeout(400)
    pagina.keyboard.press("Enter")
    pagina.wait_for_timeout(1800)


def main() -> int:
    DESTINO.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        navegador = p.chromium.launch(channel="msedge", headless=True)
        pagina = navegador.new_page(viewport={"width": 1440, "height": 950})
        errores: list[str] = []
        pagina.on(
            "console",
            lambda m: errores.append(m.text) if m.type == "error" else None,
        )
        pagina.goto(URL, wait_until="networkidle", timeout=60000)
        pagina.get_by_text("Expedivia MVP").first.wait_for(timeout=60000)
        pagina.wait_for_timeout(2000)

        pestanas = [
            (0, "1. Carga", "01_carga"),
            (1, "2. Documentos y clasificación", "02_documentos"),
            (2, "3. Extracción", "03_extraccion"),
            (3, "4. Evidencia y análisis", "04_evidencia"),
            (4, "5. Evaluación y avance", "05_evaluacion"),
        ]
        for indice, texto, nombre in pestanas:
            _pestana(pagina, indice, texto)
            if nombre == "03_extraccion":
                combo = pagina.get_by_role("combobox", name="Documento").first
                combo.click()
                combo.fill("TDR")
                pagina.wait_for_timeout(400)
                pagina.keyboard.press("Enter")
                pagina.wait_for_timeout(1600)
            _capturar(pagina, nombre)

        # Historial real de RQ-04 (3 registros: aceptar, modificar, aceptar).
        _elegir_requisito(pagina, "RQ-04")
        pagina.get_by_text("Historial de decisiones").scroll_into_view_if_needed()
        pagina.wait_for_timeout(800)
        ruta = DESTINO / "05b_historial.png"
        pagina.screenshot(path=str(ruta), full_page=False)
        print(f"capturada {ruta.name}")

        # Exportación generada desde SQLite.
        _pestana(pagina, 5, "Exportación e informes")
        pagina.get_by_role("button", name="Generar informe Excel y Word").click()
        pagina.get_by_text("Descargar").first.wait_for(timeout=60000)
        pagina.wait_for_timeout(1200)
        _capturar(pagina, "06_exportacion")
        ruta = DESTINO / "06b_exportacion_generada.png"
        pagina.screenshot(path=str(ruta), full_page=False)
        print(f"capturada {ruta.name}")

        _pestana(pagina, 6, "Métricas y auditoría")
        _capturar(pagina, "07_auditoria")

        # Demostración de bloqueo por rol: Carlos Méndez es lector.
        usuario = pagina.get_by_role("combobox", name="Usuario").first
        usuario.click()
        usuario.fill("Carlos")
        pagina.wait_for_timeout(400)
        pagina.keyboard.press("Enter")
        pagina.wait_for_timeout(2000)
        _pestana(pagina, 4, "5. Evaluación y avance")
        pagina.wait_for_timeout(800)
        pagina.evaluate("document.querySelector('section.stMain').scrollTop = 1000")
        pagina.wait_for_timeout(800)
        ruta = DESTINO / "08_permiso_lector.png"
        pagina.screenshot(path=str(ruta), full_page=False)
        print(f"capturada {ruta.name}")

        print("errores de consola:", errores or "ninguno")
        navegador.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
