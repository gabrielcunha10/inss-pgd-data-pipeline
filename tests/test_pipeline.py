import os
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
import requests
from sqlalchemy.types import BigInteger, Date, DateTime, Text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("HMAC_SECRET_KEY", "chave_secreta_padrao_inss_pgd")

from tratamento.download_sgp import (
    API_URL,
    extrair_competencia,
    baixar_arquivos_padronizados,
)
from tratamento.etl_sgp_inss import (
    enriquecer_cadastros_e_pontes,
    gerar_hash_usuario,
    limpar_e_inferir_status,
    normalizar_id_lotacao,
    preencher_por_ponte,
    ler_csv,
    carregar_e_consolidar_brutos,
    anonimizar_e_tipar,
    salvar_artefatos,
    main as etl_main,
)
from tratamento.load_neon import (
    construir_dtype_mapping,
    calcular_hash_competencia,
    construir_star_schema,
    sincronizar_insights_neon,
    main as load_neon_main,
)

def test_ingestao_extrair_competencia_por_nome():
    nome = "Programa de Gestão e Desempenho - PGD - Maio 2024"
    url = "https://dadosabertos.inss.gov.br/recurso.csv"
    resultado = extrair_competencia(nome, url, None)
    assert resultado == "pgd_inss_202405.csv", f"Esperado pgd_inss_202405.csv, obtido: {resultado}"


def test_ingestao_extrair_competencia_por_url():
    nome = "recurso_generico"
    url = "https://dadosabertos.inss.gov.br/arquivos/pgd_inss_outubro_2023.csv"
    resultado = extrair_competencia(nome, url, None)
    assert resultado == "pgd_inss_202310.csv", f"Esperado pgd_inss_202310.csv, obtido: {resultado}"


def test_ingestao_extrair_competencia_por_data_criacao():
    nome = "dados_pgd"
    url = "https://dadosabertos.inss.gov.br/download.csv"
    data_criacao = "2025-08-15T10:30:00"
    resultado = extrair_competencia(nome, url, data_criacao)
    assert resultado == "pgd_inss_202508.csv", f"Esperado pgd_inss_202508.csv, obtido: {resultado}"


def test_ingestao_extrair_competencia_fallback_limpeza_nome():
    nome = "Relatório Especial @ 2022 / INSS!"
    url = "https://dadosabertos.inss.gov.br/arquivo.csv"
    resultado = extrair_competencia(nome, url, None)
    assert resultado == "Relat_rio_Especial___2022___INSS.csv", f"Esperado nome higienizado, obtido: {resultado}"


def test_ingestao_extrair_competencia_variacoes_mes_marco():
    res1 = extrair_competencia("PGD Março 2025", "", None)
    res2 = extrair_competencia("PGD Marco 2025", "", None)
    assert res1 == "pgd_inss_202503.csv"
    assert res2 == "pgd_inss_202503.csv"


def test_ingestao_baixar_arquivos_padronizados_fluxo_mock(tmp_path):
    mock_resources = {
        "result": {
            "resources": [
                {
                    "name": "PGD Janeiro 2025",
                    "url": "http://mock.inss.gov.br/pgd_jan_2025.csv",
                    "format": "CSV",
                    "created": "2025-01-10T00:00:00",
                }
            ]
        }
    }
    mock_csv_content = b"competencia,matricula,nome\n202501,1234567,Servidor Teste\n"

    def mock_requests_get(url, **kwargs):
        resp = MagicMock()
        if "package_show" in url:
            resp.json.return_value = mock_resources
            resp.raise_for_status = MagicMock()
        else:
            resp.iter_content.return_value = [mock_csv_content]
            resp.raise_for_status = MagicMock()
            resp.encoding = "utf-8"
        return resp

    with patch("requests.get", side_effect=mock_requests_get):
        with patch("tratamento.download_sgp.os.path.abspath") as mock_abs:
            mock_abs.return_value = str(tmp_path / "tratamento" / "download_sgp.py")
            data_dir = tmp_path / "data"
            data_dir.mkdir(parents=True, exist_ok=True)

            with patch("tratamento.download_sgp.os.path.dirname") as mock_dir:
                mock_dir.side_effect = lambda p: str(Path(p).parent)
                baixar_arquivos_padronizados()

    arquivo_esperado = data_dir / "pgd_inss_202501.csv"
    assert arquivo_esperado.exists(), "O arquivo baixado deveria ter sido salvo com nome padronizado."
    with open(arquivo_esperado, "rb") as f:
        conteudo = f.read()
    assert conteudo == mock_csv_content, "O conteudo salvo no arquivo deve corresponder ao stream baixado."


def test_ingestao_baixar_arquivos_padronizados_pula_existente(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    arquivo_ja_existente = data_dir / "pgd_inss_202501.csv"
    arquivo_ja_existente.write_text("conteudo_antigo", encoding="utf-8")

    mock_resources = {
        "result": {
            "resources": [
                {
                    "name": "PGD Janeiro 2025",
                    "url": "http://mock.inss.gov.br/pgd_jan_2025.csv",
                    "format": "CSV",
                    "created": "2025-01-10T00:00:00",
                }
            ]
        }
    }
    mock_api_resp = MagicMock()
    mock_api_resp.json.return_value = mock_resources
    mock_api_resp.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_api_resp) as mock_get:
        with patch("tratamento.download_sgp.os.path.abspath") as mock_abs:
            mock_abs.return_value = str(tmp_path / "tratamento" / "download_sgp.py")
            with patch("tratamento.download_sgp.os.path.dirname") as mock_dir:
                mock_dir.side_effect = lambda p: str(Path(p).parent)
                baixar_arquivos_padronizados()

    assert mock_get.call_count == 1, "Arquivo existente nao deve acionar novo download via HTTP."
    assert arquivo_ja_existente.read_text(encoding="utf-8") == "conteudo_antigo", "Conteudo original deve ser preservado."


def test_ingestao_baixar_arquivos_padronizados_erro_api():
    with patch("requests.get", side_effect=Exception("Erro de conexao")):
        with pytest.raises(RuntimeError, match="Erro fatal na consulta a API do INSS"):
            baixar_arquivos_padronizados()


def test_ingestao_api_inss_real_disponibilidade_e_contrato():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(API_URL, headers=headers, timeout=20)
    except requests.exceptions.RequestException as e:
        pytest.skip(f"Portal de dados abertos do INSS temporariamente inacessivel: {e}")

    if response.status_code == 403:
        pytest.skip("Acesso a API do INSS bloqueado por WAF/Geo-IP no ambiente de execucao (HTTP 403).")

    assert response.status_code == 200, f"Status code esperado 200, recebido: {response.status_code}"
    dados = response.json()
    assert dados.get("success") is True, "API CKAN do INSS deve retornar 'success: true'."

    resultado = dados.get("result", {})
    assert resultado.get("name") == "sistema-de-gerenciamento-de-produtividade-sgp", (
        f"Nome do pacote incorreto: {resultado.get('name')}"
    )


def test_ingestao_api_inss_real_recursos_disponiveis():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(API_URL, headers=headers, timeout=20)
    except requests.exceptions.RequestException as e:
        pytest.skip(f"Portal de dados abertos do INSS temporariamente inacessivel: {e}")

    if response.status_code == 403:
        pytest.skip("Acesso a API do INSS bloqueado por WAF/Geo-IP no ambiente de execucao (HTTP 403).")

    dados = response.json()
    recursos = dados.get("result", {}).get("resources", [])
    assert len(recursos) >= 30, f"Esperado ao menos 30 recursos historicos, encontrados: {len(recursos)}"

    recursos_dados = [
        r for r in recursos
        if (
            r.get("format", "").upper() in ("CSV", "XLSX", "XLS")
            or r.get("url", "").lower().endswith((".csv", ".xlsx", ".xls"))
        )
        and r.get("url", "").startswith("http")
    ]
    assert len(recursos_dados) >= 30, (
        f"Esperados ao menos 30 recursos de dados (CSV/Excel) com URLs validas, encontrados: {len(recursos_dados)}"
    )

    primeiro_recurso = recursos_dados[0]
    assert "name" in primeiro_recurso and len(primeiro_recurso["name"]) > 0, "Recurso deve conter atributo 'name'."
    assert "url" in primeiro_recurso and primeiro_recurso["url"].startswith("http"), "Recurso deve conter URL valida."

#%%
@pytest.fixture(scope="module")
def df_inss():
  caminho_csv = Path(__file__).parent / "pgd_designacoes_inss_2023_2026.parquet"
  if not caminho_csv.exists():
    pytest.fail(f"Arquivo de dados não encontrado em: {caminho_csv}")
  print(f"\nCarregando dados de: {caminho_csv}")
  return pd.read_parquet(caminho_csv)
#%%
def test_tipos_datas(df_inss):
    assert pd.api.types.is_datetime64_any_dtype(df_inss["dt_inicio_designacao"])
    assert pd.api.types.is_datetime64_any_dtype(df_inss["dt_fim_designacao"])
#%%
def test_consistencia_temporal_designacao(df_inss):
    datas_preenchidas = df_inss.dropna(subset=["dt_inicio_designacao", "dt_fim_designacao"])
    anacronismos = datas_preenchidas["dt_fim_designacao"] < datas_preenchidas["dt_inicio_designacao"]
    total_erros = anacronismos.sum()
    assert total_erros == 0, f"Encontrados {total_erros} registros com data final anterior à data inicial."
#%%
def test_conformidade_lgpd_identificador(df_inss):
  coluna = "id_usuario"
  linha_com_erro = df_inss[df_inss[coluna].isna()]
  print(linha_com_erro)
  assert coluna in df_inss.columns, f"A coluna '{coluna}' não foi encontrada."

  nulos = df_inss[coluna].isna().sum()
  assert (
      nulos == 0
  ), f"Existem {nulos} registros com identificador de usuário nulo."
  padrao_lgpd = r"^USR-[A-F0-9]{8}$"
  mascara_valida = df_inss[coluna].astype(str).str.match(padrao_lgpd)
  
  inconformidades = (~mascara_valida).sum()
  assert inconformidades == 0, (
      f"Risco de conformidade LGPD: {inconformidades} registros fora do padrão"
      " 'USR-XXXXXXXX'."
  )
#%%
def test_valores_nulos_criticos(df_inss):
    colunas_criticas = ["competencia", "status", "id_usuario"]
    for col in colunas_criticas:
        nulos = df_inss[col].isna().sum()
        assert nulos == 0, f"A coluna crítica '{col}' possui {nulos} valores nulos!"

    designados = df_inss[df_inss["status"] == "Designado"]
    nulos_modalidade = designados["modalidade"].isna().sum()
    assert nulos_modalidade == 0, f"Foram encontrados {nulos_modalidade} registros com status 'Designado' mas sem 'modalidade' informada!"

#%%
def test_dominios_esperados(df_inss):
    modalidades_validas = {"Remoto", "Semipresencial", "Presencial"}
    modalidades_encontradas = set(df_inss["modalidade"].dropna().unique())
    assert modalidades_encontradas.issubset(modalidades_validas), f"Modalidades inválidas encontradas: {modalidades_encontradas - modalidades_validas}"

    status_validos = {"Designado", "Desligado", "Não Designado"}
    status_encontrados = set(df_inss["status"].dropna().unique())
    assert status_encontrados.issubset(status_validos), f"Status inválidos encontrados: {status_encontrados - status_validos}"
    
    flags_validas = {"Sim", "Não"}
    flags_encontradas = set(df_inss["flag_pgd"].dropna().unique())
    assert flags_encontradas.issubset(flags_validas), f"Flags PGD inválidas encontradas: {flags_encontradas - flags_validas}"

#%%
def test_unicidade_chave_primaria(df_inss):
    duplicados = df_inss.duplicated(subset=["id_usuario", "competencia", "id_designacao"], keep=False)
    qtd_duplicados = duplicados.sum()
    
    assert qtd_duplicados == 0, f"Encontrados {qtd_duplicados} registros duplicados na mesma competência para o mesmo usuário e designação."

#%%
def test_correspondencia_sigla_programa(df_inss):
    sigla_nula = df_inss["sigla_programa"].isna()
    programa_nulo = df_inss["programa"].isna()
    inconsistencias = df_inss[(sigla_nula & ~programa_nulo) | (~sigla_nula & programa_nulo)]
    
    total_erros = len(inconsistencias)
    if total_erros > 0:
        amostra = inconsistencias[['sigla_programa', 'programa']].drop_duplicates().to_dict('records')
        pytest.fail(f"Falha de integridade: encontrados {total_erros} registros com sigla ou programa órfãos! Amostra: {amostra}")

#%%
def test_correspondencia_linha_trabalho(df_inss):
    sigla_nula = df_inss["sigla_linha_trabalho"].isna()
    linha_nula = df_inss["linha_trabalho"].isna()
    inconsistencias = df_inss[(sigla_nula & ~linha_nula) | (~sigla_nula & linha_nula)]
    
    total_erros = len(inconsistencias)
    if total_erros > 0:
        amostra = inconsistencias[['sigla_linha_trabalho', 'linha_trabalho']].drop_duplicates().to_dict('records')
        pytest.fail(f"Falha de integridade: encontrados {total_erros} registros com sigla ou linha de trabalho órfãos! Amostra: {amostra}")

#%%
def test_funcao_anonimizacao_determinismo():
    matricula = "1234567"
    hash_1 = gerar_hash_usuario(matricula)
    hash_2 = gerar_hash_usuario(matricula)
    hash_int = gerar_hash_usuario(1234567)
    hash_diff = gerar_hash_usuario("1234568")

    assert hash_1 == hash_2, "A anonimização deve ser determinística para a mesma matrícula."
    assert hash_1 == hash_int, "A função deve tratar strings e inteiros de forma equivalente."
    assert hash_1 != hash_diff, "Matrículas distintas não podem colidir no mesmo hash."
    assert re.match(r"^USR-[A-F0-9]{8}$", hash_1), f"Formato inválido: '{hash_1}'"


def test_funcao_normalizacao_lotacao():
    df_raw = pd.DataFrame({
        "competencia": ["202602", "202602"],
        "id_matricula": ["M01", "M02"],
        "lotacao": [
            "GERÊNCIA EXECUTIVA JOÃO PESSOA",
            "AGÊNCIA DA PREVIDÊNCIA SOCIAL SÃO PAULO",
        ],
        "sigla_programa": ["ATENDIMENT0", "PGD"],
        "programa": ["PROG 1", "PROG 2"],
        "status": ["Designado", "Designado"],
        "dt_inicio_designacao": [None, None],
        "dt_fim_designacao": [None, None],
        "dt_criacao_designacao": [None, None],
        "dt_alteracao_designacao": [None, None],
    })

    df_limpo = limpar_e_inferir_status(df_raw)
    lotacoes = df_limpo["lotacao"].tolist()

    assert lotacoes[0] == "GEX JOAO PESSOA", f"Falha ao normalizar GEX e acentos: {lotacoes[0]}"
    assert lotacoes[1] == "APS SAO PAULO", f"Falha ao normalizar APS e acentos: {lotacoes[1]}"
    assert df_limpo["sigla_programa"].iloc[0] == "ATENDIMENTO", "Falha na correção de typo em sigla_programa."


def test_funcao_inferencia_status_temporal():
    df_raw = pd.DataFrame({
        "competencia": ["202601", "202601", "202601", "202601"],
        "id_matricula": ["M01", "M02", "M03", "M04"],
        "lotacao": ["GEX CENTRAL"] * 4,
        "sigla_programa": ["PGD"] * 4,
        "programa": ["PROG"] * 4,
        "status": [None, None, None, "2"],
        "dt_inicio_designacao": [None, "01/01/2026", "01/01/2026", None],
        "dt_fim_designacao": [None, "20/01/2026", "28/02/2026", None],
        "dt_criacao_designacao": [None] * 4,
        "dt_alteracao_designacao": [None] * 4,
    })

    df_limpo = limpar_e_inferir_status(df_raw)
    status_resultado = df_limpo["status"].tolist()

    assert status_resultado[0] == "Não Designado", "Sem data e sem status deve inferir 'Não Designado'."
    assert status_resultado[1] == "Desligado", "Plano com término antes do fim da competência deve inferir 'Desligado'."
    assert status_resultado[2] == "Designado", "Plano com término após o fim da competência deve inferir 'Designado'."
    assert status_resultado[3] == "Desligado", "Código '2' deve mapear diretamente para 'Desligado'."


def test_funcao_preenchimento_por_ponte():
    comp1 = pd.Period("2024-01", freq="M")
    comp2 = pd.Period("2024-02", freq="M")
    comp3 = pd.Period("2024-03", freq="M")

    df_ponte = pd.DataFrame({
        "competencia": [comp1, comp2, comp3, comp1, comp2, comp3],
        "id_matricula": ["M01", "M01", "M01", "M02", "M02", "M02"],
        "id_designacao": ["100", None, "100", "200", None, "300"],
    })

    resultado = preencher_por_ponte(df_ponte, ["id_designacao"], comp2, comp1, comp3)
    val_m1 = resultado.loc[(resultado["id_matricula"] == "M01") & (resultado["competencia"] == comp2), "id_designacao"].values[0]
    val_m2 = resultado.loc[(resultado["id_matricula"] == "M02") & (resultado["competencia"] == comp2), "id_designacao"].values[0]

    assert val_m1 == "100", "A ponte deve preencher valores idênticos entre competências adjacentes."
    assert pd.isna(val_m2), "A ponte não deve imputar valores quando houver divergência entre as pontas."


def test_funcao_regras_flag_pgd():
    df_cadastros = pd.DataFrame({
        "competencia": [pd.Period("2025-01", freq="M")] * 3,
        "id_matricula": ["M01", "M02", "M03"],
        "nome": ["Servidor 1", "Servidor 2", "Servidor 3"],
        "id_designacao": [1, 2, 3],
        "sigla_programa": ["PG-DIRBEN", None, None],
        "programa": [
            "PROGRAMA DA CEAB I",
            "PACTUAÇÃO DE 6H PELO ACORDO DE GREVE",
            "OUTRO PROGRAMA",
        ],
        "id_lotacao": ["L1", "L2", "L3"],
        "lotacao": ["GEX 1", "GEX 2", "GEX 3"],
        "tipo_entrega": ["Meta e Produto"] * 3,
        "linha_trabalho": ["LT1", "LT2", "LT3"],
        "sigla_linha_trabalho": ["SLT1", "SLT2", "SLT3"],
        "status": ["Designado", "Designado", "Não Designado"],
        "dt_criacao_designacao": [None] * 3,
    })

    res = enriquecer_cadastros_e_pontes(df_cadastros)
    flags = res["flag_pgd"].tolist()

    assert flags[0] == "Sim", "Programas institucionais regulares devem receber flag_pgd = 'Sim'."
    assert flags[1] == "Não", "Programas de acordo de greve devem receber flag_pgd = 'Não'."
    assert pd.isna(flags[2]), "Status 'Não Designado' deve permanecer com flag_pgd nula."


def test_funcao_normalizar_id_lotacao():
    serie_teste = pd.Series([
        "4025060",
        "2315032",
        "1800",
        "1800.0",
        "04025060",
        "20001",
        "12001",
        "-",
        None,
        "nan",
    ])
    codigos_6 = {"012001", "110264"}
    codigos_8 = {"04025060", "07001120"}
    resultado = normalizar_id_lotacao(
        serie_teste,
        codigos_6_conhecidos=codigos_6,
        codigos_8_conhecidos=codigos_8,
    )

    assert resultado.iloc[0] == "04025060", "Codigo de 7 digitos com par em conhecidos_8 deve receber padding para 8 digitos."
    assert resultado.iloc[1] == "2315032", "Codigo de 7 digitos sem par em conhecidos_8 deve ser preservado."
    assert resultado.iloc[2] == "01800", "Codigo de 4 digitos deve receber padding para 5 digitos."
    assert resultado.iloc[3] == "01800", "Float string de 4 digitos deve ser limpa e receber padding."
    assert resultado.iloc[4] == "04025060", "Codigo ja com 8 digitos deve ser preservado."
    assert resultado.iloc[5] == "20001", "Codigo de 5 digitos sem par em conhecidos_6 deve ser preservado."
    assert resultado.iloc[6] == "012001", "Codigo de 5 digitos com par em conhecidos_6 deve receber zero a esquerda."
    assert resultado.iloc[7] == "-", "Strings nao numericas devem ser mantidas."
    assert pd.isna(resultado.iloc[8]), "Valores nulos devem retornar NaN/None."
    assert pd.isna(resultado.iloc[9]), "Strings 'nan' devem retornar NaN/None."


def test_isolamento_propagacao_designacao_nula():
    df_teste = pd.DataFrame({
        "competencia": [pd.Period("2025-01", freq="M"), pd.Period("2025-01", freq="M")],
        "id_matricula": ["M_CORREG", "M_APS"],
        "nome": ["Servidor Corregedoria", "Servidor APS"],
        "id_designacao": [None, None],
        "sigla_programa": [None, None],
        "programa": [None, None],
        "id_lotacao": ["01800", "04025060"],
        "lotacao": ["CORREGEDORIA-GERAL", "APS FEIRA DE SANTANA"],
        "tipo_entrega": [None, None],
        "linha_trabalho": [None, None],
        "sigla_linha_trabalho": [None, None],
        "status": ["Não Designado", "Não Designado"],
        "dt_criacao_designacao": [None, None],
    })

    res = enriquecer_cadastros_e_pontes(df_teste)
    lotacoes = res.set_index("id_matricula")["id_lotacao"].to_dict()

    assert lotacoes["M_CORREG"] == "01800", "Corregedoria deve manter seu id_lotacao."
    assert lotacoes["M_APS"] == "04025060", "APS nao pode ter seu id_lotacao sobrescrito por Corregedoria."

def test_carga_validacao_database_url_ausente(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValueError, match="DATABASE_URL não encontrada"):
        load_neon_main()


def test_carga_validacao_arquivo_parquet_ausente(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost:5432/mock")
    arquivo_inexistente = tmp_path / "inexistente.parquet"
    with patch("tratamento.load_neon.PARQUET_FILE", arquivo_inexistente):
        with pytest.raises(FileNotFoundError, match="Arquivo não encontrado"):
            load_neon_main()


def test_carga_construir_dtype_mapping():
    colunas = [
        "competencia",
        "dt_inicio_designacao",
        "dt_fim_designacao",
        "dt_criacao_designacao",
        "dt_alteracao_designacao",
        "id_designacao",
        "id_usuario",
        "lotacao",
        "status",
    ]
    mapping = construir_dtype_mapping(colunas)

    assert isinstance(mapping["competencia"], Date)
    assert isinstance(mapping["dt_inicio_designacao"], DateTime)
    assert isinstance(mapping["dt_fim_designacao"], DateTime)
    assert isinstance(mapping["dt_criacao_designacao"], DateTime)
    assert isinstance(mapping["dt_alteracao_designacao"], DateTime)
    assert isinstance(mapping["id_designacao"], BigInteger)
    assert isinstance(mapping["id_usuario"], Text)
    assert isinstance(mapping["lotacao"], Text)
    assert isinstance(mapping["status"], Text)


def test_carga_execucao_transacional_mock(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost:5432/mock")

    df_mock = pd.DataFrame({
        "competencia": [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-02-01")],
        "id_usuario": ["USR-11111111", "USR-22222222"],
        "id_designacao": [101, 102],
        "dt_inicio_designacao": [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-02-01")],
        "dt_fim_designacao": [pd.Timestamp("2025-01-31"), pd.Timestamp("2025-02-28")],
        "dt_criacao_designacao": [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-02-01")],
        "dt_alteracao_designacao": [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-02-01")],
        "lotacao": ["GEX CENTRAL", "APS NORTE"],
        "status": ["Designado", "Designado"],
    })
    caminho_parquet = tmp_path / "mock_test.parquet"
    df_mock.to_parquet(caminho_parquet, index=False)

    mock_conn = MagicMock()
    mock_engine = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn

    mock_inspector = MagicMock()
    mock_inspector.has_table.return_value = True

    with patch("tratamento.load_neon.PARQUET_FILE", caminho_parquet):
        with patch("tratamento.load_neon.create_engine", return_value=mock_engine):
            with patch("tratamento.load_neon.inspect", return_value=mock_inspector):
                with patch.object(pd.DataFrame, "to_sql") as mock_to_sql:
                    load_neon_main()

    assert mock_conn.execute.called, "conn.execute deveria ter sido chamado para o DELETE preventivo."
    delete_calls = [c for c in mock_conn.execute.call_args_list if "DELETE FROM tb_pgd_inss" in str(c[0][0])]
    assert len(delete_calls) == 1
    call_args, _ = delete_calls[0]
    assert "DELETE FROM tb_pgd_inss" in str(call_args[0])
    comps_executadas = call_args[1]["comps"]
    assert "2025-01-01" in comps_executadas
    assert "2025-02-01" in comps_executadas

    assert mock_to_sql.called, "to_sql deveria ter sido chamado para inserir os dados."
    to_sql_args, to_sql_kwargs = mock_to_sql.call_args
    assert to_sql_args[0] == "tb_pgd_inss"
    assert to_sql_kwargs["chunksize"] == 10000
    assert to_sql_kwargs["if_exists"] == "append"


def test_carga_pula_competencias_com_hash_identico_mock(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost:5432/mock")

    df_mock = pd.DataFrame({
        "competencia": [pd.Timestamp("2025-01-01")],
        "id_usuario": ["USR-11111111"],
        "id_designacao": [101],
        "lotacao": ["GEX CENTRAL"],
        "status": ["Designado"],
    })
    caminho_parquet = tmp_path / "mock_skip.parquet"
    df_mock.to_parquet(caminho_parquet, index=False)

    hash_esperado = calcular_hash_competencia(df_mock)

    mock_conn = MagicMock()

    def side_effect_execute(stmt, params=None):
        s = str(stmt)
        res = MagicMock()
        if "GROUP BY competencia" in s:
            res.fetchall.return_value = [("2025-01-01", 1)]
        elif "FROM tb_controle_carga" in s:
            res.fetchall.return_value = [("2025-01-01", 1, hash_esperado)]
        else:
            res.fetchall.return_value = []
        return res

    mock_conn.execute.side_effect = side_effect_execute
    mock_engine = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn

    mock_inspector = MagicMock()
    mock_inspector.has_table.return_value = True
    mock_inspector.get_columns.return_value = [{"name": c} for c in df_mock.columns]

    with patch("tratamento.load_neon.PARQUET_FILE", caminho_parquet):
        with patch("tratamento.load_neon.create_engine", return_value=mock_engine):
            with patch("tratamento.load_neon.inspect", return_value=mock_inspector):
                with patch.object(pd.DataFrame, "to_sql") as mock_to_sql:
                    load_neon_main()

    assert not mock_to_sql.called, "Não deveria reenviar dados quando o hash e contagem no banco são idênticos."


def test_etl_ler_csv_encodings(tmp_path):
    f_utf8 = tmp_path / "teste_utf8.csv"
    f_utf8.write_text("col1;col2\nvalor1;Atenção", encoding="utf-8")
    df_u = ler_csv(f_utf8)
    assert len(df_u) == 1

    f_latin = tmp_path / "teste_latin1.csv"
    f_latin.write_bytes("col1;col2\nvalor1;Atenção".encode("latin1"))
    df_l = ler_csv(f_latin)
    assert len(df_l) == 1


def test_etl_carregar_e_consolidar_brutos(tmp_path):
    pasta_data = tmp_path / "data"
    pasta_data.mkdir(parents=True, exist_ok=True)
    f1 = pasta_data / "pgd_inss_202501.csv"
    f1.write_text("Código UO;Lotação;Modalidade\n1234;GEX SP;Integral", encoding="utf-8")
    f2 = pasta_data / "pgd_inss_202502.csv"
    f2.write_text("Código UO;Lotação;Modalidade\n5678;GEX RJ;Parcial", encoding="utf-8")

    df_total = carregar_e_consolidar_brutos(pasta_data)
    assert len(df_total) == 2
    assert "competencia" in df_total.columns
    assert set(df_total["modalidade"]) == {"Remoto", "Semipresencial"}


def test_etl_salvar_artefatos(tmp_path, monkeypatch):
    df_mini = pd.DataFrame({
        "competencia": [pd.Timestamp("2025-01-01")],
        "id_usuario": ["USR-12345678"],
        "id_designacao": [101],
        "status": ["Designado"],
    })
    p_parquet = tmp_path / "out.parquet"
    p_csv = tmp_path / "out.csv"
    p_sample = tmp_path / "out_sample.csv"
    monkeypatch.setattr("tratamento.etl_sgp_inss.OUTPUT_PARQUET", p_parquet)
    monkeypatch.setattr("tratamento.etl_sgp_inss.OUTPUT_CSV", p_csv)
    monkeypatch.setattr("tratamento.etl_sgp_inss.OUTPUT_SAMPLE", p_sample)

    salvar_artefatos(df_mini)
    assert p_parquet.exists()
    assert p_csv.exists()
    assert p_sample.exists()


def test_etl_main_mock(monkeypatch):
    mock_df = MagicMock()
    mock_df.pipe.return_value = mock_df
    monkeypatch.setattr("tratamento.etl_sgp_inss.carregar_e_consolidar_brutos", lambda d: mock_df)
    monkeypatch.setattr("tratamento.etl_sgp_inss.salvar_artefatos", MagicMock())
    etl_main()


def test_star_schema_decomposicao_e_integridade_referencial():
    df_flat = pd.DataFrame({
        "competencia": [pd.Timestamp("2026-07-01"), pd.Timestamp("2026-08-01"), pd.Timestamp("2026-08-01")],
        "id_usuario": ["USR-11111111", "USR-11111111", "USR-22222222"],
        "id_designacao": [1001, 1001, 1002],
        "sigla_programa": ["CEAP", "CEAP", "PG-DTI"],
        "programa": [
            "CENTRAL ESPECIALIZADA DE ALTA PERFORMANCE",
            "CENTRAL ESPECIALIZADA DE ALTA PERFORMANCE",
            "PROGRAMA DE GESTÃO - DIRETORIA DE TECNOLOGIA DA INFORMAÇÃO",
        ],
        "flag_pgd": ["Sim", "Sim", "Sim"],
        "filtro_programa": ["CEAP - CENTRAL...", "CEAP - CENTRAL...", "PG-DTI - PROGRAMA..."],
        "sigla_linha_trabalho": ["CEABRD_SR_NE", "CEABRD_SR_NE", "APS_SRSE"],
        "linha_trabalho": ["Central Nordeste", "Central Nordeste", "Agência Sudeste"],
        "filtro_linha_trabalho": ["CEABRD_SR_NE - Central...", "CEABRD_SR_NE - Central...", "APS_SRSE - Agência..."],
        "id_lotacao": ["01800", "01800", "04025060"],
        "lotacao": ["CORREGEDORIA", "CORREGEDORIA", "APS FEIRA DE SANTANA"],
        "status": ["Designado", "Designado", "Designado"],
        "modalidade": ["Remoto", "Remoto", "Semipresencial"],
        "tipo_entrega": ["Meta", "Meta", "Produto"],
        "motivo_desligamento": [None, None, None],
        "dt_inicio_designacao": [pd.Timestamp("2026-01-01")] * 3,
        "dt_fim_designacao": [pd.Timestamp("2026-12-31")] * 3,
        "dt_criacao_designacao": [pd.Timestamp("2026-01-01")] * 3,
        "dt_alteracao_designacao": [pd.Timestamp("2026-01-01")] * 3,
    })

    star = construir_star_schema(df_flat)

    tabelas_esperadas = {
        "dim_programa",
        "dim_linha_trabalho",
        "dim_lotacao",
        "dim_servidor",
        "dim_calendario",
        "fato_designacoes",
    }
    assert set(star.keys()) == tabelas_esperadas

    # Deduplicação das dimensões
    assert len(star["dim_programa"]) == 2
    assert len(star["dim_linha_trabalho"]) == 2
    assert len(star["dim_lotacao"]) == 2
    assert len(star["dim_servidor"]) == 2
    assert len(star["dim_calendario"]) == 2
    assert len(star["fato_designacoes"]) == 3

    # Integridade referencial das Surrogate Keys na tabela fato
    fato = star["fato_designacoes"]
    assert set(fato["sk_programa"].dropna()).issubset(set(star["dim_programa"]["sk_programa"]))
    assert set(fato["sk_linha_trabalho"].dropna()).issubset(set(star["dim_linha_trabalho"]["sk_linha_trabalho"]))
    assert set(fato["sk_lotacao"].dropna()).issubset(set(star["dim_lotacao"]["sk_lotacao"]))

    # Nenhum texto descritivo longo deve ficar duplicado na tabela fato
    for col_redundante in ["programa", "linha_trabalho", "lotacao", "filtro_programa", "filtro_linha_trabalho"]:
        assert col_redundante not in fato.columns


def test_sincronizar_insights_neon_sqlite(tmp_path):
    from sqlalchemy import create_engine, inspect

    csv_fake = tmp_path / "insights_historico_powerbi.csv"
    pd.DataFrame({
        "competencia": ["2026-03-01", "2026-04-01"],
        "competencia_mes_ano": ["03/2026", "04/2026"],
        "servidores_plano_ativo": [10658, 10672],
        "servidores_plano_ativo_fmt": ["10.658", "10.672"],
        "variacao_mensal_mom": [0.5, 0.13],
        "variacao_mensal_mom_fmt": ["+0,50%", "+0,13%"],
        "adesao_teletrabalho_pct": [19.4, 19.2],
        "adesao_teletrabalho_fmt": ["19,4%", "19,2%"],
        "adesao_remoto_pct": [72.1, 72.6],
        "adesao_remoto_fmt": ["72,1%", "72,6%"],
        "motor_analise_ia": ["Google Gemini Flash (3.8)"] * 2,
        "diagnostico_executivo": ["Diagnóstico 03/2026", "Diagnóstico 04/2026"],
        "principais_movimentacoes_mom": ["Mov 03/2026", "Mov 04/2026"],
        "matriz_alertas_recomendacoes": ["Alerta 03/2026", "Alerta 04/2026"],
    }).to_csv(csv_fake, index=False, encoding="utf-8")

    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        qtd = sincronizar_insights_neon(conn=conn, caminho_csv=csv_fake)
        assert qtd == 2
        insp = inspect(conn)
        assert insp.has_table("insights_historico_powerbi")
        df_lido = pd.read_sql_table("insights_historico_powerbi", con=conn)
        assert len(df_lido) == 2
        assert list(df_lido["competencia_mes_ano"]) == ["03/2026", "04/2026"]


def test_catalogo_s3_dinamico_e_candidatos():
    from tratamento.download_sgp import construir_catalogo_s3_historico, gerar_candidatos_s3

    cat = construir_catalogo_s3_historico()
    assert len(cat) == 35
    assert cat[0]["name"] == "SGP - outubro 2023"
    assert cat[-1]["name"] == "SGP - agosto 2026"
    assert cat[-1]["format"] == "XLSX"

    cands = gerar_candidatos_s3(2026, 9)
    assert len(cands) >= 24
    formatos = {fmt for fmt, _ in cands}
    assert {"CSV", "XLSX", "XLS"}.issubset(formatos)


def test_precisa_baixar_recurso_detecta_republicacao(tmp_path):
    from tratamento.download_sgp import precisa_baixar_recurso

    arq = tmp_path / "pgd_inss_202607.csv"
    arq.write_text("col1,col2\n1,2\n", encoding="utf-8")

    manifest = {
        "pgd_inss_202607.csv": {
            "last_modified": "2026-07-05T10:00:00",
            "etag": "abc123",
            "size": 14,
        }
    }
    # Mesmo last_modified e etag -> não baixa de novo
    res_igual = {"last_modified": "2026-07-05T10:00:00", "etag": "abc123", "size": 14}
    assert precisa_baixar_recurso(str(arq), "pgd_inss_202607.csv", res_igual, manifest) is False

    # INSS republicou com novo last_modified -> deve baixar de novo
    res_republicado = {"last_modified": "2026-07-20T15:30:00", "etag": "def456", "size": 250}
    assert precisa_baixar_recurso(str(arq), "pgd_inss_202607.csv", res_republicado, manifest) is True


def test_verificar_atualizacao_dados_alerta_defasagem(tmp_path):
    from datetime import datetime
    from tratamento.download_sgp import verificar_atualizacao_dados

    (tmp_path / "pgd_inss_202601.csv").write_text("a,b\n1,2\n", encoding="utf-8")

    # Data de referência 2 meses depois -> OK
    res_ok = verificar_atualizacao_dados(str(tmp_path), max_meses_defasagem=3, data_ref=datetime(2026, 3, 1))
    assert res_ok["ok"] is True
    assert res_ok["ultima_competencia"] == "2026-01"

    # Data de referência 6 meses depois -> Alerta de defasagem
    res_stale = verificar_atualizacao_dados(str(tmp_path), max_meses_defasagem=3, data_ref=datetime(2026, 7, 1))
    assert res_stale["ok"] is False
    assert res_stale["meses_defasagem"] == 6

    # Diretório vazio -> Alerta de dados ausentes
    res_empty = verificar_atualizacao_dados(str(tmp_path / "inexistente"))
    assert res_empty["ok"] is False
    assert res_empty["ultima_competencia"] is None


def test_precisa_baixar_recurso_head_remoto_etag_e_content_length(tmp_path):
    from tratamento.download_sgp import precisa_baixar_recurso

    arq = tmp_path / "pgd_inss_202608.csv"
    arq.write_bytes(b"col1,col2\n1,2\n")

    manifest = {
        "pgd_inss_202608.csv": {
            "last_modified": "2026-08-01",
            "etag": "etag_antigo",
            "size": 14,
        }
    }
    res_item = {
        "url": "https://s3.mock/D.SRF.FQS.005.PGD.ACSINSS.202608.csv",
        "last_modified": "2026-08-01",
        "etag": "etag_antigo",
        "size": 14,
    }

    # Caso 1: HEAD retorna ETag diferente -> True
    resp_etag = MagicMock(status_code=200, headers={"ETag": '"etag_novo"', "Content-Length": "14"})
    with patch("requests.head", return_value=resp_etag):
        assert precisa_baixar_recurso(
            str(arq), "pgd_inss_202608.csv", res_item, manifest, verificar_head_remoto=True
        ) is True

    # Caso 2: HEAD retorna Content-Length diferente -> True
    resp_len = MagicMock(status_code=200, headers={"ETag": '"etag_antigo"', "Content-Length": "999"})
    with patch("requests.head", return_value=resp_len):
        assert precisa_baixar_recurso(
            str(arq), "pgd_inss_202608.csv", res_item, manifest, verificar_head_remoto=True
        ) is True


def test_descobrir_recursos_s3_direto_descobre_novas_competencias():
    from tratamento.download_sgp import descobrir_recursos_s3_direto

    def fake_head(url, headers=None, timeout=10):
        resp = MagicMock()
        resp.status_code = 200 if "202609.csv" in url else 404
        return resp

    with patch("requests.head", side_effect=fake_head):
        recursos = descobrir_recursos_s3_direto()

    nomes = [r["name"] for r in recursos]
    assert "SGP - setembro 2026" in nomes


def test_baixar_arquivos_padronizados_fallback_403_e_conversao_xlsx(tmp_path):
    import io

    # Cria um arquivo XLSX real em memória
    buf_xlsx = io.BytesIO()
    pd.DataFrame({"matricula": ["1234567"], "regime": ["Integral"]}).to_excel(buf_xlsx, index=False)
    xlsx_bytes = buf_xlsx.getvalue()

    resp_403 = MagicMock(status_code=403)
    http_err_403 = requests.exceptions.HTTPError(response=resp_403)
    resp_403.raise_for_status.side_effect = http_err_403

    mock_session = MagicMock()
    mock_session.get.return_value = resp_403

    resp_xlsx = MagicMock(status_code=200, content=xlsx_bytes, headers={"ETag": '"etag_xlsx"'})
    resp_xlsx.raise_for_status = MagicMock()

    def fake_get(url, **kwargs):
        if "package_show" in url:
            return resp_403
        return resp_xlsx

    s3_fake_list = [
        {
            "name": "SGP - agosto 2026",
            "format": "XLSX",
            "url": "https://s3.mock/D.SRF.FQS.005.PGD.ACSINSS.202608.xlsx",
        }
    ]

    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    with patch("requests.get", side_effect=fake_get):
        with patch("requests.Session", return_value=mock_session):
            with patch("tratamento.download_sgp.descobrir_recursos_s3_direto", return_value=s3_fake_list):
                with patch("tratamento.download_sgp.os.path.abspath", return_value=str(tmp_path / "tratamento" / "download_sgp.py")):
                    with patch("tratamento.download_sgp.os.path.dirname", side_effect=lambda p: str(Path(p).parent)):
                        baixar_arquivos_padronizados()

    csv_gerado = data_dir / "pgd_inss_202608.csv"
    assert csv_gerado.exists()
    assert "1234567" in csv_gerado.read_text(encoding="utf-8")
    assert (data_dir / ".download_manifest.json").exists()


def test_sincronizar_star_schema_neon_sqlite_real():
    from sqlalchemy import create_engine, inspect
    from tratamento.load_neon import sincronizar_star_schema_neon

    df_flat = pd.DataFrame({
        "competencia": [pd.Timestamp("2026-01-01"), pd.Timestamp("2026-02-01")],
        "id_usuario": ["USR-AAAAAAAA", "USR-BBBBBBBB"],
        "id_designacao": [1001, 1002],
        "sigla_programa": ["CEAP", "PG-DTI"],
        "programa": ["CENTRAL ESPECIALIZADA", "DIRETORIA DE TI"],
        "flag_pgd": ["Sim", "Sim"],
        "filtro_programa": ["CEAP - CENTRAL", "PG-DTI - DIRETORIA"],
        "sigla_linha_trabalho": ["CEABRD_SR_NE", "APS_SRSE"],
        "linha_trabalho": ["Central Nordeste", "Agência Sudeste"],
        "filtro_linha_trabalho": ["CEABRD_SR_NE - Central", "APS_SRSE - Agência"],
        "id_lotacao": ["01800", "04025060"],
        "lotacao": ["CORREGEDORIA", "APS FEIRA DE SANTANA"],
        "status": ["Designado", "Designado"],
        "modalidade": ["Remoto", "Semipresencial"],
        "tipo_entrega": ["Meta", "Produto"],
        "motivo_desligamento": [None, None],
        "dt_inicio_designacao": [pd.Timestamp("2026-01-01")] * 2,
        "dt_fim_designacao": [pd.Timestamp("2026-12-31")] * 2,
        "dt_criacao_designacao": [pd.Timestamp("2026-01-01")] * 2,
        "dt_alteracao_designacao": [pd.Timestamp("2026-01-01")] * 2,
    })

    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        insp = inspect(conn)
        sincronizar_star_schema_neon(
            conn=conn,
            inspector=insp,
            df_total=df_flat,
            competencias_para_carregar=["2026-01-01", "2026-02-01"],
            full_refresh=True,
        )
        # Segunda chamada com tabela já existente e full_refresh=True (cobre o ramo DROP TABLE fato_designacoes)
        insp2 = inspect(conn)
        sincronizar_star_schema_neon(
            conn=conn,
            inspector=insp2,
            df_total=df_flat,
            competencias_para_carregar=["2026-01-01", "2026-02-01"],
            full_refresh=True,
        )
        df_fato_db = pd.read_sql_table("fato_designacoes", con=conn)
        df_prog_db = pd.read_sql_table("dim_programa", con=conn)
        assert len(df_fato_db) == 2
        assert len(df_prog_db) == 2


def test_construir_star_schema_fallbacks_colunas_ausentes():
    df_minimo = pd.DataFrame({
        "lotacao": ["APS CENTRO", "GEX NORTE"],
        "status": ["Designado", "Desligado"],
    })
    star = construir_star_schema(df_minimo)
    assert len(star["dim_lotacao"]) == 2
    assert len(star["dim_programa"]) == 0
    assert len(star["dim_calendario"]) == 0
    assert len(star["fato_designacoes"]) == 2


def test_normalizar_id_lotacao_casos_borda():
    serie = pd.Series(["1800.0", "4025060", "51234", "nan", "", None, "APS-01"])
    res = normalizar_id_lotacao(
        serie,
        codigos_6_conhecidos={"051234"},
        codigos_8_conhecidos={"04025060"},
    )
    assert res.iloc[0] == "01800"
    assert res.iloc[1] == "04025060"
    assert res.iloc[2] == "051234"
    assert pd.isna(res.iloc[3])
    assert pd.isna(res.iloc[4])
    assert pd.isna(res.iloc[5])
    assert res.iloc[6] == "APS-01"








