#%%
import pandas as pd
import os
import numpy as np
#%%
files = os.listdir("data")
colunas = set()
#%%
for i in files:
    df = pd.read_csv(f"data/{i}", sep=";")
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
df_regime = pd.read_csv("data/D.SRF.FQS.005.ACSINSS.PGD.202310.csv", sep=";")
df_regime
colunas.clear()
#%%
dfs = []

for i in files:
    df = pd.read_csv(f"data/{i}", sep=";")
    df = df.rename(columns=rename_map)
    df = df.drop(columns=[c for c in drop_colunas if c in df.columns])
    data = i.split(sep=".")[-2]
    df["competencia"] = data
    if "modalidade" in df.columns:
        df["modalidade"] = df["modalidade"].replace(rename_valores_regime)
    colunas.update(df.columns)
    dfs.append(df)
#%%
df_total = pd.concat(dfs, ignore_index=True, sort=False)
#%%
df_total.isna().sum()
#%%
lista_datas = []
for i in files:
    data = i.split(sep=".")[-2]
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
    df_total["status"] == 1,
    df_total["status"] == 2
]
resultados_status1 = ["Designado", "Desligado"]
df_total["status"] = np.select(condicoes_status1, resultados_status1, default=df_total["status"])

# converter datas uma vez, fora do np.select
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
df_total
# %%
