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
  coluna = "id_matricula"
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
