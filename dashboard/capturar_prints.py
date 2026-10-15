import hashlib
import logging
import re
import time
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
IMAGENS_DIR = PROJECT_DIR / "dashboard" / "imagens"
POWERBI_URL = (
    "https://app.powerbi.com/view?r=eyJrIjoiMjNlNzBmOWQtMzVlNC00MjBhLTk0MDEtYTBhZThiZWYyNTAwIiwidCI6IjhjODgwZTJhLTM2MDAtNDVmZi1hZDM5LWJhMDRlZGM4MWYyNSJ9"
)

PAGINAS = [
    {"ordem": 1, "nome": "Menu Inicial", "arquivo": "menu_inicial.png"},
    {"ordem": 2, "nome": "Visão Geral", "arquivo": "visao_geral_dashboard.png"},
    {"ordem": 3, "nome": "Programas", "arquivo": "programas_dashboard.png"},
    {"ordem": 4, "nome": "Linhas de Trabalho", "arquivo": "linhas_trabalho_dashboard.png"},
    {"ordem": 5, "nome": "Modalidades", "arquivo": "modalidades_dashboard.png"},
    {"ordem": 6, "nome": "Lotações", "arquivo": "lotacoes_dashboard.png"},
    {"ordem": 7, "nome": "Transparência & LGPD", "arquivo": "lgpd_dashboard.png"},
    {"ordem": 8, "nome": "Informações do Projeto", "arquivo": "informacoes_projeto.png"},
]


def garantir_pagina_inicial(page):
    try:
        indicador = page.locator("a.middleText")
        if indicador.is_visible(timeout=3000):
            texto = indicador.inner_text().lower()
            if not texto.startswith("1"):
                logging.info(f"Dashboard abriu na posição '{texto}'. Retornando à Página 1 (Menu Inicial)...")
                indicador.click()
                page.wait_for_timeout(1000)
                page.locator("button.sectionItem", has_text="Menu Inicial").click()
                page.wait_for_timeout(4000)
                logging.info("Página 1 (Menu Inicial) selecionada com sucesso.")
    except Exception as e:
        logging.warning(f"Tentativa de validação da página inicial: {e}")


def avancar_proxima_pagina(page, idx: int) -> bool:
    try:
        next_btn = page.locator(
            "button[aria-label='Next Page'], "
            "button[aria-label='Próxima página'], "
            "button[aria-label='Página seguinte']"
        ).first
        if next_btn.is_visible(timeout=2000) and not next_btn.is_disabled():
            next_btn.click()
            return True
    except Exception as e:
        logging.warning(f"Clique na seta falhou: {e}")

    try:
        logging.info("Executando fallback: selecionando próxima página pelo menu...")
        indicador = page.locator("a.middleText")
        if indicador.is_visible(timeout=2000):
            indicador.click()
            page.wait_for_timeout(1000)
            nome_alvo = PAGINAS[idx]["nome"].split()[0]
            page.locator(f"button.sectionItem:has-text('{nome_alvo}')").click()
            return True
    except Exception as e:
        logging.error(f"Fallback pelo menu falhou: {e}")

    return False


def navegar_para_pagina_especifica(page, nome_pagina: str) -> bool:
    try:
        indicador = page.locator("a.middleText")
        if indicador.is_visible(timeout=2000):
            indicador.click()
            page.wait_for_timeout(800)
            palavra_chave = nome_pagina.split()[0]
            item = page.locator("button.sectionItem", has_text=palavra_chave).first
            if item.is_visible(timeout=2000):
                item.click()
                page.wait_for_timeout(3000)
                return True
    except Exception as e:
        logging.warning(f"Tentativa de navegacao direta para '{nome_pagina}' falhou: {e}")
    return False


def capturar_todas_as_paginas():
    if sync_playwright is None:
        raise ImportError(
            "O Playwright não está instalado neste ambiente. "
            "Instale com 'pip install playwright && playwright install chromium'."
        )
    IMAGENS_DIR.mkdir(parents=True, exist_ok=True)
    logging.info("Iniciando captura automatizada com Playwright...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1.25,
        )

        page = context.new_page()
        logging.info(f"Navegando para o relatório no Power BI: {POWERBI_URL}")
        page.goto(POWERBI_URL, wait_until="networkidle", timeout=60000)

        page.wait_for_timeout(6000)

        garantir_pagina_inicial(page)

        total = len(PAGINAS)
        ultimo_hash = None

        for idx, info in enumerate(PAGINAS, start=1):
            nome = info["nome"]
            arquivo = info["arquivo"]
            destino = IMAGENS_DIR / arquivo

            logging.info(f"[{idx}/{total}] Preparando captura de '{nome}'...")
            sucesso_captura = False

            for tentativa in range(1, 4):
                page.wait_for_timeout(3500)

                page.mouse.move(0, 0)
                page.evaluate("""() => {
                    if (document.activeElement && document.activeElement.blur) {
                        document.activeElement.blur();
                    }
                    document.querySelectorAll('.cdk-overlay-pane, .pbi-tooltip, .tooltip-container, [role="tooltip"]').forEach(el => {
                        el.remove();
                    });
                }""")
                page.wait_for_timeout(500)

                host = page.locator(".visualContainerHost").first
                if host.is_visible():
                    img_bytes = host.screenshot()
                else:
                    img_bytes = page.screenshot(clip={"x": 0, "y": 0, "width": 1920, "height": 1040})

                digest = hashlib.sha256(img_bytes).hexdigest()

                if idx == 1 or digest != ultimo_hash:
                    destino.write_bytes(img_bytes)
                    ultimo_hash = digest
                    sucesso_captura = True
                    logging.info(f"[{idx}/{total}] Imagem '{nome}' salva com sucesso em: {destino}")
                    break
                else:
                    logging.warning(
                        f"[{idx}/{total}] Tentativa {tentativa}/3: Print idêntico ao da página anterior. "
                        f"Acionando recuperação direta para '{nome}'..."
                    )
                    navegou = navegar_para_pagina_especifica(page, nome)
                    if not navegou:
                        avancar_proxima_pagina(page, idx - 1)
                    page.wait_for_timeout(3000)

            if not sucesso_captura:
                destino.write_bytes(img_bytes)
                ultimo_hash = digest
                logging.error(f"[{idx}/{total}] Falha de unicidade persistente após 3 tentativas para '{nome}'.")

            if idx < total:
                logging.info(f"Avançando da página {idx} para a página {idx + 1}...")
                avancou = avancar_proxima_pagina(page, idx)
                if not avancou:
                    logging.warning(
                        f"Não foi possível avançar para a página {idx + 1}."
                    )
                page.wait_for_timeout(3000)

        browser.close()
        logging.info("Captura de todas as páginas finalizada com sucesso!")

    atualizar_timestamp_dashboard_readme()


def atualizar_timestamp_dashboard_readme():
    readme_path = PROJECT_DIR / "dashboard" / "dashboard_README.md"
    if not readme_path.exists():
        return
    agora_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
    conteudo = readme_path.read_text(encoding="utf-8")
    novo_conteudo = re.sub(
        r">\s*\*\*Última Atualização:\*\*.*",
        f"> **Última Atualização:** {agora_str}  ",
        conteudo,
    )
    readme_path.write_text(novo_conteudo, encoding="utf-8")
    logging.info(f"Timestamp do dashboard_README.md atualizado para: {agora_str}")


if __name__ == "__main__":
    capturar_todas_as_paginas()
