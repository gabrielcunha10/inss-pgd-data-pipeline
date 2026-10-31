import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("HMAC_SECRET_KEY", "chave_secreta_padrao_inss_pgd")

from pipeline_flow import (
    task_download_dados,
    task_etl_lgpd,
    task_validar_qualidade,
    task_carga_neon,
    task_gerar_insights,
    pipeline_flow,
)
from dashboard.prints_flow import (
    task_capturar_prints,
    task_validar_documentacao_insights,
    prints_flow,
)


def test_tarefas_importaveis():
    assert callable(task_download_dados.fn)
    assert callable(task_etl_lgpd.fn)
    assert callable(task_validar_qualidade.fn)
    assert callable(task_carga_neon.fn)
    assert callable(task_gerar_insights.fn)
    assert callable(pipeline_flow.fn)
    assert callable(task_capturar_prints.fn)
    assert callable(task_validar_documentacao_insights.fn)
    assert callable(prints_flow.fn)


def test_carga_neon_pula_quando_sem_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    task_carga_neon.fn()


def test_validar_qualidade_sucesso():
    with patch("pytest.main", return_value=0):
        task_validar_qualidade.fn()


def test_validar_qualidade_falha():
    with patch("pytest.main", return_value=1):
        with pytest.raises(RuntimeError, match="Falha crítica de qualidade"):
            task_validar_qualidade.fn()


def test_fluxo_orquestrado_mock():
    with patch("tratamento.download_sgp.main") as mock_down:
        with patch("tratamento.etl_sgp_inss.main") as mock_etl:
            with patch("pytest.main", return_value=0) as mock_pytest:
                with patch("tratamento.load_neon.main") as mock_load:
                    with patch("tratamento.gerar_insights.main") as mock_insights:
                        pipeline_flow.fn(executar_carga_banco=True)

                        assert mock_down.called
                        assert mock_etl.called
                        assert mock_pytest.called
                        assert mock_insights.called


def test_fluxo_orquestrado_sem_banco():
    with patch("tratamento.download_sgp.main") as mock_down:
        with patch("tratamento.etl_sgp_inss.main") as mock_etl:
            with patch("pytest.main", return_value=0) as mock_pytest:
                with patch("tratamento.load_neon.main") as mock_load:
                    with patch("tratamento.gerar_insights.main") as mock_insights:
                        pipeline_flow.fn(executar_carga_banco=False)

                        assert mock_down.called
                        assert mock_etl.called
                        assert mock_pytest.called
                        assert not mock_load.called
                        assert mock_insights.called


def test_validar_documentacao_insights_sucesso():
    with patch("pytest.main", return_value=0):
        task_validar_documentacao_insights.fn()


def test_validar_documentacao_insights_falha():
    with patch("pytest.main", return_value=1):
        with pytest.raises(RuntimeError, match="Falha na validação de documentação/prints"):
            task_validar_documentacao_insights.fn()


def test_prints_flow_mock():
    with patch("dashboard.capturar_prints.capturar_todas_as_paginas") as mock_cap:
        with patch("pytest.main", return_value=0) as mock_pytest:
            prints_flow.fn()
            assert mock_cap.called
            assert mock_pytest.called

