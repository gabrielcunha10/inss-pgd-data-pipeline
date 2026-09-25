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
  return pd.read_csv(caminho_csv)
#%%
def test_consistencia_datas(df_inss):
    df_inss["dt_inicio_designacao"].dtype()
#%%