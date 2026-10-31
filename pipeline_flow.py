"""Pipeline de Dados e Analytics — Programa de Gestão de Desempenho (PGD) INSS
Orquestrador central construído com Prefect.
"""

import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pytest
from prefect import flow, task

PROJECT_DIR = Path(__file__).resolve().parent
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

load_dotenv()


@task(
    name="1. Ingestão de Dados (API CKAN INSS)",
    description="Baixa incrementalmente os arquivos mensais do Portal de Dados Abertos do INSS.",
    retries=3,
    retry_delay_seconds=30,
)
def task_download_dados():
    logging.info("[Prefect] Iniciando tarefa de download de microdados do INSS...")
    from tratamento.download_sgp import main as download_main
    download_main()
    logging.info("[Prefect] Ingestão concluída com sucesso.")


@task(
    name="2. Processamento ETL & Anonimização LGPD",
    description="Limpa, aplica pontes temporais, anonimiza matrículas via HMAC-SHA256 e gera Parquet/CSV.",
    retries=2,
    retry_delay_seconds=15,
)
def task_etl_lgpd():
    logging.info("[Prefect] Iniciando processamento e saneamento ETL...")
    from tratamento.etl_sgp_inss import main as etl_main
    etl_main()
    logging.info("[Prefect] ETL e anonimização LGPD finalizados com sucesso.")


@task(
    name="3. Guardião de Qualidade e Integridade (Pytest)",
    description="Executa 29 testes automatizados do pipeline no padrão Write-Audit-Publish antes da carga no banco.",
)
def task_validar_qualidade():
    logging.info("[Prefect] Executando suíte de testes de integridade do pipeline...")
    caminho_testes = str(PROJECT_DIR / "tests" / "test_pipeline.py")
    exit_code = pytest.main(["-q", caminho_testes])
    if exit_code != 0:
        msg = f"[Prefect] Falha crítica de qualidade: Pytest retornou código {exit_code}. Carga abortada para proteger o banco."
        logging.error(msg)
        raise RuntimeError(msg)
    logging.info("[Prefect] Todos os testes de qualidade foram aprovados com 100% de sucesso.")


@task(
    name="4. Carga Idempotente no PostgreSQL (Neon Tech)",
    description="Executa a carga transacional particionada e idempotente dos dados no banco em nuvem.",
    retries=2,
    retry_delay_seconds=30,
)
def task_carga_neon():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logging.warning("[Prefect] DATABASE_URL não configurada no ambiente. Pulando carga no banco.")
        return

    logging.info("[Prefect] Iniciando sincronização idempotente com o PostgreSQL Neon Tech...")
    try:
        from tratamento.load_neon import main as load_neon_main
        load_neon_main()
        logging.info("[Prefect] Carga no Neon Tech finalizada com sucesso.")
    except Exception as e:
        logging.error(f"[Prefect] Erro durante a carga no banco: {e}")
        raise e


@task(
    name="5. Diagnósticos Executivos de IA (Google Gemini)",
    description="Gera diagnóstico analítico mensal via IA generativa e atualiza histórico do Power BI.",
    retries=2,
    retry_delay_seconds=20,
)
def task_gerar_insights():
    logging.info("[Prefect] Iniciando geração autônoma de insights executivos...")
    from tratamento.gerar_insights import main as insights_main
    insights_main()
    logging.info("[Prefect] Relatórios e histórico analítico do Power BI atualizados com sucesso.")


@flow(
    name="Pipeline PGD INSS",
    description="Fluxo ponta a ponta de engenharia e governança de dados do INSS orquestrado com Prefect.",
    log_prints=True,
)
def pipeline_flow(executar_carga_banco: bool = True):
    """Orquestra a sequência completa do pipeline de dados com garantias de qualidade e retries."""
    logging.info("==================================================")
    logging.info("Iniciando execução orquestrada do Pipeline PGD INSS")
    logging.info("==================================================")

    # 1. Download
    task_download_dados()

    # 2. ETL & LGPD
    task_etl_lgpd()

    # 3. Barreira de Qualidade
    task_validar_qualidade()

    # 4. Carga no Neon DB (se habilitada)
    if executar_carga_banco:
        task_carga_neon()

    # 5. Geração de Insights de IA
    task_gerar_insights()

    logging.info("==================================================")
    logging.info("Pipeline PGD INSS finalizado com êxito pelo Prefect")
    logging.info("==================================================")


if __name__ == "__main__":
    sem_banco = "--sem-banco" in sys.argv
    pipeline_flow(executar_carga_banco=not sem_banco)
