"""Pipeline de Documentação e Captura de Telas — Dashboard Power BI
Orquestrador visual e governança de documentação construído com Prefect.
"""

import logging
import sys
from pathlib import Path
import pytest
from prefect import flow, task

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

LOGS_DIR = PROJECT_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "pipeline.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)


@task(
    name="1. Captura de Prints do Dashboard (Playwright)",
    description="Navega pelas 9 páginas do relatório no Power BI e captura screenshots em alta resolução.",
    retries=2,
    retry_delay_seconds=30,
)
def task_capturar_prints():
    logging.info("[Prefect] Iniciando captura automatizada dos prints do Power BI...")
    from dashboard.capturar_prints import capturar_todas_as_paginas
    capturar_todas_as_paginas()
    logging.info("[Prefect] Captura dos 9 prints e atualização de timestamp concluídas com sucesso.")


@task(
    name="2. Validação de Documentação e Integridade Visual (Pytest)",
    description="Garante que todos os 9 prints existem, têm cabeçalho PNG válido, tamanho adequado, são únicos e referenciados.",
)
def task_validar_documentacao_insights():
    logging.info("[Prefect] Executando validação de integridade dos prints e documentação com Pytest...")
    caminho_testes = str(PROJECT_DIR / "tests" / "test_documentacao_insights.py")
    exit_code = pytest.main(["-q", caminho_testes])
    if exit_code != 0:
        msg = f"[Prefect] Falha na validação de documentação/prints: Pytest retornou código {exit_code}."
        logging.error(msg)
        raise RuntimeError(msg)
    logging.info("[Prefect] Suíte de documentação e prints aprovada com 100% de sucesso.")


@flow(
    name="Atualização de Prints e Documentação",
    description="Fluxo orquestrado para captura em alta resolução das 9 páginas do Power BI e validação de QA.",
    log_prints=True,
)
def prints_flow():
    """Orquestra a captura dos prints e validação de integridade visual."""
    logging.info("==================================================")
    logging.info("Iniciando fluxo de Prints e Documentação no Prefect")
    logging.info("==================================================")

    # 1. Captura via Playwright com retries em caso de lentidão da web
    task_capturar_prints()

    # 2. Gate de Qualidade com Pytest
    task_validar_documentacao_insights()

    logging.info("==================================================")
    logging.info("Fluxo de Prints e Documentação finalizado com êxito")
    logging.info("==================================================")


if __name__ == "__main__":
    prints_flow()
