#%%
from pathlib import Path
import pandas as pd
import pytest
#%%
@pytest.fixture(scope="module")
def df_inss():
  caminho_csv = Path(__file__).parent / "pgd_designacoes_inss_2023_2026.csv"
  if not caminho_csv.exists():
    pytest.fail(f"Arquivo de dados não encontrado em: {caminho_csv}")
  print(f"\nCarregando dados de: {caminho_csv}")
  return pd.read_csv(caminho_csv, sep=";", parse_dates=["dt_inicio_designacao", "dt_fim_designacao"])
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
  padrao_lgpd = r"^USR-\d{5}$"
  mascara_valida = df_inss[coluna].astype(str).str.match(padrao_lgpd)
  
  inconformidades = (~mascara_valida).sum()
  assert inconformidades == 0, (
      f"Risco de conformidade LGPD: {inconformidades} registros fora do padrão"
      " 'USR-XXXXX'."
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
