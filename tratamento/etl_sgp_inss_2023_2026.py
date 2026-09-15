#%%
import pandas as pd
import os
import numpy as np
import re
from pathlib import Path
#%%
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_FILE = PROJECT_DIR / "pgd_designacoes_inss_2023_2026.csv"

files = os.listdir(DATA_DIR)
colunas = set()

def ler_csv(caminho):
    try:
        return pd.read_csv(caminho, sep=";", dtype="str", encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(caminho, sep=";", dtype="str", encoding="latin1")

#%%
for i in files:
    df = ler_csv(DATA_DIR / i)
    colunas.update(df.columns)
# %%
colunas
# %%
rename_map = {"Data Alteração Designação" : "dt_alteracao_designacao",
              "Data Criação Designação" : "dt_criacao_designacao",
              "Data Fim Designação" : "dt_fim_designacao",
              "Data Início Designação": "dt_inicio_designacao",
              "Matricula" : "id_matricula",
              "Matrícula" : "id_matricula",
              "siape2" : "id_matricula",
              "Código Designação" : "id_designacao",
              "sgp_id" : "id_designacao",
              "Competência" : "competencia",
              "compet": "competencia",
              "Código UO" : "id_lotacao",
              "Lotação" : "lotacao",
              "Profissional" : "nome",
              "Sigla Programa" : "sigla_programa",
              "Programa" : "programa",
              "programa" : "codigo_regime_2023",
              "sigla" : "sigla_programa",
              "Sigla Linha de Trabalho" : "sigla_linha_trabalho",
              "Linha de Trabalho" : "linha_trabalho",
              "Situação" : "status",
              "regime" : "modalidade",
              "Modalidade" : "modalidade",
              "tipo_acao" : "status",
              "PGD" : "flag_pgd",
              "Motivo Desligamento" : "motivo_desligamento",
              "sgp_dt_alteracao" : "dt_alteracao_designacao",
              "sgp_dt_inclusao" : "dt_criacao_designacao",
              "Tipo de Entrega" : "tipo_entrega",
              "data_inicio" : "dt_inicio_designacao",
              "data_termino" : "dt_fim_designacao",
              "produto" : "flag_produto"
              }

rename_valores_regime = {"Integral" : "Remoto",
                         "Parcial" : "Semipresencial",
                         "Presencial": "Presencial"}

#%%
## Colunas para dropar: documento, registro_data, Motivo Desligamento
drop_colunas = ["documento", "registro_data", "codigo_regime_2023", "flag_produto"]
colunas.clear()
#%%
dfs = []

for i in files:
    df = ler_csv(DATA_DIR / i)
    df = df.rename(columns=rename_map)
    df = df.drop(columns=[c for c in drop_colunas if c in df.columns])
    match = re.search(r'\d{6}', i)
    data = match.group() if match else i
    df["competencia"] = data
    if "modalidade" in df.columns:
        df["modalidade"] = df["modalidade"].replace(rename_valores_regime)
    colunas.update(df.columns)
    dfs.append(df)
#%%
df_total = pd.concat(dfs, ignore_index=True, sort=False)
df_total = df_total.replace("-", np.nan)
#%%
df_total.isna().sum()
#%%
lista_datas = []
for i in files:
    match = re.search(r'\d{6}', i)
    data = match.group() if match else i
    lista_datas.append(data)

#%%
lista_datas
#%%
df_total["competencia"] = pd.to_datetime(df_total["competencia"], format="%Y%m").dt.to_period("M")
df_total
# %%
df_total
#%%
condicoes_status1 = [
    df_total["status"] == "1",
    df_total["status"] == "2"
]
resultados_status1 = ["Designado", "Desligado"]
df_total["status"] = np.select(condicoes_status1, resultados_status1, default=df_total["status"])

dt_inicio = pd.to_datetime(df_total["dt_inicio_designacao"], format="%d/%m/%Y", errors="coerce")
dt_fim = pd.to_datetime(df_total["dt_fim_designacao"], format="%d/%m/%Y", errors="coerce")

comp_fim_mes = df_total["competencia"].dt.to_timestamp() + pd.offsets.MonthEnd(0)

condicoes_status2 = [
    df_total["status"].isna() & dt_inicio.isna(),
    df_total["status"].isna() & dt_inicio.notna() & (dt_fim.isna() | (dt_fim >= comp_fim_mes)),
    df_total["status"].isna() & dt_inicio.notna() & dt_fim.notna() & (dt_fim < comp_fim_mes),
]
resultados_status2 = ["Não Designado", "Designado", "Desligado"]

df_total["status"] = np.select(condicoes_status2, resultados_status2, default=df_total["status"])
# %%

mapa_sigla_para_programa = (
    df_total.dropna(subset=['sigla_programa', 'programa'])
    [['sigla_programa', 'programa']]
    .drop_duplicates()
    .set_index('sigla_programa')['programa']
    .to_dict()
)

mapa_programa_para_sigla = (
    df_total.dropna(subset=['sigla_programa', 'programa'])
    [['programa', 'sigla_programa']]
    .drop_duplicates()
    .set_index('programa')['sigla_programa']
    .to_dict()
)

df_total['programa'] = df_total['programa'].fillna(
    df_total['sigla_programa'].map(mapa_sigla_para_programa)
)

df_total['sigla_programa'] = df_total['sigla_programa'].fillna(
    df_total['programa'].map(mapa_programa_para_sigla)
)
#%%
programas_nao_pgd = [
    'PACTUAÇÃO DE 6H PELO ACORDO DE GREVE',
    'PROFISSIONAIS SEM PROGAMA DE GESTÃO E DESEMPENHO',
    'PROGRAMA DAS UNIDADES - ACORDO DE GREVE',
]

sugestao_flag_pgd = df_total['programa'].apply(
    lambda x: 'Não' if x in programas_nao_pgd else ('Sim' if pd.notna(x) else None)
)

df_total['flag_pgd'] = df_total['flag_pgd'].fillna(sugestao_flag_pgd)
#%%
dt_filtro = df_total["dt_criacao_designacao"].isna()

df_total[dt_filtro]

#%%
df_total
# %%
df_total.dtypes
# %%
df_total.isna().sum()
# %%
filtro_modalidade = df_total["modalidade"].isna()
#%%
series_filtro = df_total[filtro_modalidade].groupby(["competencia"]).size()
#%%
df_total[filtro_modalidade]["dt_inicio_designacao"].isna().sum()
#%%
df_total[filtro_modalidade]["dt_fim_designacao"].isna().sum()
#%%
df_total["dt_criacao_designacao"] = pd.to_datetime(df_total["dt_criacao_designacao"], format="mixed")
#%%
df_total["dt_alteracao_designacao"] = pd.to_datetime(df_total["dt_alteracao_designacao"], format="mixed")
#%%
df_total["dt_inicio_designacao"] = pd.to_datetime(df_total["dt_inicio_designacao"], format="%d/%m/%Y", errors="coerce")
#%%
df_total["dt_fim_designacao"] = pd.to_datetime(df_total["dt_fim_designacao"], format="%d/%m/%Y", errors="coerce")
#%%
df_total.isna().sum()
# %%
def preencher_por_ponte(df_total, colunas, competencia_alvo, competencia_antes, competencia_depois):
    cols_id = ['id_matricula'] + colunas
    antes = df_total[df_total['competencia'] == competencia_antes][cols_id]
    depois = df_total[df_total['competencia'] == competencia_depois][cols_id]

    ponte = antes.merge(depois, on='id_matricula', suffixes=('_antes', '_depois'))
    condicao = pd.Series(True, index=ponte.index)
    for col in colunas:
        condicao &= (ponte[f'{col}_antes'] == ponte[f'{col}_depois'])
    ponte_confiavel = ponte[condicao]

    mask_alvo = df_total['competencia'] == competencia_alvo
    for col in colunas:
        mapa = ponte_confiavel.set_index('id_matricula')[f'{col}_antes'].to_dict()
        df_total.loc[mask_alvo, col] = df_total.loc[mask_alvo, col].fillna(
            df_total.loc[mask_alvo, 'id_matricula'].map(mapa)
        )
    return df_total

#%%
colunas_para_preencher = ['id_designacao', 'dt_criacao_designacao']
df_total = preencher_por_ponte(df_total, colunas_para_preencher, '202403', '202402', '202404')
df_total = preencher_por_ponte(df_total, colunas_para_preencher, '202405', '202404', '202406')
# %%
dicionario = (
    df_total.dropna(subset=["sigla_programa", "programa"])
    [["sigla_programa", "programa"]]
    .drop_duplicates()
    .set_index("sigla_programa")["programa"]
    .to_dict()
)

dicionario_externo = {
    "PG-DIRBEN": "PROGRAMA DE GESTÃO - DIRETORIA DE BENEFÍCIOS E RELACIONAMENTO COM O CIDADÃO",
    "PGRP": "PROGRAMA DE GESTÃO EM REGIME DE EXECUÇÃO PARCIAL",
    "CEAP": "CENTRAL ESPECIALIZADA DE ALTA PERFORMANCE",
    "PGD-GABGEX": "PROGRAMA DE GESTÃO E DESEMPENHO - GABINETE DA GERÊNCIA EXECUTIVA",
    "PG-AUDGER": "PROGRAMA DE GESTÃO - AUDITORIA-GERAL",
    "PG-DIROFL": "PROGRAMA DE GESTÃO - DIRETORIA DE ORÇAMENTO, FINANÇAS E LOGÍSTICA",
    "PG-DTI": "PROGRAMA DE GESTÃO - DIRETORIA DE TECNOLOGIA DA INFORMAÇÃO",
    "PGD-DGP": "PROGRAMA DE GESTÃO E DESEMPENHO - DIRETORIA DE GESTÃO DE PESSOAS",
    "PGD-PFE": "PROGRAMA DE GESTÃO E DESEMPENHO - PROCURADORIA FEDERAL ESPECIALIZADA",
    "PG-CORREG": "PROGRAMA DE GESTÃO - CORREGEDORIA-GERAL",
    "PGD-GERGEX": "PROGRAMA DE GESTÃO E DESEMPENHO - GERÊNCIA EXECUTIVA",
    "PGD-GABSR": "PROGRAMA DE GESTÃO E DESEMPENHO - GABINETE DA SUPERINTENDÊNCIA REGIONAL",
    "PGD-PGARP": "PROGRAMA DE GESTÃO DA REABILITAÇÃO PROFISSIONAL",
    "PG-DIGOV": "PROGRAMA DE GESTÃO - DIRETORIA DE GOVERNANÇA, PLANEJAMENTO E INOVAÇÃO",
    "PGD-GABPRE": "PROGRAMA DE GESTÃO E DESEMPENHO - GABINETE DA PRESIDÊNCIA",
    "PG-ACS": "PROGRAMA DE GESTÃO - ASSESSORIA DE COMUNICAÇÃO SOCIAL",
}

dicionario.update(dicionario_externo)
#%%
df_total["programa"] = df_total["programa"].fillna(
    df_total["sigla_programa"].map(dicionario)
)
#%%
df_total
#%%
dicionario_programa_para_sigla = (
    df_total.dropna(subset=["programa", "sigla_programa"])
    [["programa","sigla_programa"]].drop_duplicates()
    .set_index("programa")["sigla_programa"].to_dict()
)
#%%
df_total["sigla_programa"] = df_total["sigla_programa"].fillna(
    df_total["programa"].map(dicionario_programa_para_sigla)
)

# %%
df_total.isna().sum()
# %%
programas_nao_pgd_confirmados = [
    'PACTUAÇÃO DE 6H PELO ACORDO DE GREVE',
    'PROFISSIONAIS SEM PROGAMA DE GESTÃO E DESEMPENHO',
    'PROGRAMA DAS UNIDADES - ACORDO DE GREVE',
]

programas_com_flag_pgd_conhecida = [
    'PACTUAÇÃO DE 6H PELO ACORDO DE GREVE', 'PROFISSIONAIS SEM PROGAMA DE GESTÃO E DESEMPENHO',
    'PROG. PRESENCIAL 6H + PONTUAÇÃO', 'PROGRAMA DA CEAB I', 'PROGRAMA DA REABILITAÇÃO PROFISSIONAL',
    'PROGRAMA DA REABILITAÇÃO PROFISSIONAL - REMOTO', 'PROGRAMA DA REABILITAÇÃO PROFISSIONAL PT 1800',
    'PROGRAMA DAS CENTRAIS DE SUPORTE', 'PROGRAMA DAS GERÊNCIAS EXECUTIVAS - PGD',
    'PROGRAMA DAS SUPERINTENDÊNCIAS - PGD', 'PROGRAMA DAS UNIDADES - ACORDO DE GREVE',
    'PROGRAMA DAS UNIDADES DE ATENDIMENTO - PT 1800', 'PROGRAMA DAS ÁREAS DA DIREÇÃO CENTRAL',
]

def inferir_flag_pgd(programa):
    if pd.isna(programa) or programa not in programas_com_flag_pgd_conhecida:
        return None
    return 'Não' if programa in programas_nao_pgd_confirmados else 'Sim'

sugestao = df_total['programa'].apply(inferir_flag_pgd)
df_total['flag_pgd'] = df_total['flag_pgd'].fillna(sugestao)
#%%
df_sample = df_total.sample(n=5000, random_state=42)
#%%
# Salva a amostra em UTF-8 com separador ';'
df_sample.to_csv(
    PROJECT_DIR / "tratamento" / "pgd_designacoes_inss_2023_2026_sample.csv", 
    index=False, 
    sep=";"
)