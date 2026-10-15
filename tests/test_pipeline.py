import re
import sys
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tratamento.etl_sgp_inss import (
    enriquecer_cadastros_e_pontes,
    gerar_hash_usuario,
    limpar_e_inferir_status,
    preencher_por_ponte,
)

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
