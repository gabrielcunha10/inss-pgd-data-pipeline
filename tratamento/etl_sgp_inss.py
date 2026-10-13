import hashlib
import hmac
import logging
import os
import re
import unicodedata
from pathlib import Path
from dotenv import load_dotenv
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()
HMAC_SECRET_KEY = os.getenv(
    "HMAC_SECRET_KEY", "chave_secreta_padrao_inss_pgd"
).encode("utf-8")

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_CSV = PROJECT_DIR / "tratamento" / "pgd_designacoes_inss_2023_2026.csv"
OUTPUT_SAMPLE = (
    PROJECT_DIR / "tratamento" / "pgd_designacoes_inss_2023_2026_sample.csv"
)
OUTPUT_PARQUET = (
    PROJECT_DIR / "tests" / "pgd_designacoes_inss_2023_2026.parquet"
)

RENAME_MAP = {
    "Data Alteração Designação": "dt_alteracao_designacao",
    "Data Criação Designação": "dt_criacao_designacao",
    "Data Fim Designação": "dt_fim_designacao",
    "Data Início Designação": "dt_inicio_designacao",
    "Matricula": "id_matricula",
    "Matrícula": "id_matricula",
    "siape2": "id_matricula",
    "Código Designação": "id_designacao",
    "sgp_id": "id_designacao",
    "Competência": "competencia",
    "compet": "competencia",
    "Código UO": "id_lotacao",
    "Lotação": "lotacao",
    "Profissional": "nome",
    "Sigla Programa": "sigla_programa",
    "Programa": "programa",
    "programa": "codigo_regime_2023",
    "sigla": "sigla_programa",
    "Sigla Linha de Trabalho": "sigla_linha_trabalho",
    "Linha de Trabalho": "linha_trabalho",
    "Situação": "status",
    "regime": "modalidade",
    "Modalidade": "modalidade",
    "tipo_acao": "status",
    "PGD": "flag_pgd",
    "Motivo Desligamento": "motivo_desligamento",
    "sgp_dt_alteracao": "dt_alteracao_designacao",
    "sgp_dt_inclusao": "dt_criacao_designacao",
    "Tipo de Entrega": "tipo_entrega",
    "data_inicio": "dt_inicio_designacao",
    "data_termino": "dt_fim_designacao",
    "produto": "flag_produto",
}

RENAME_VALORES_REGIME = {
    "Integral": "Remoto",
    "Parcial": "Semipresencial",
    "Presencial": "Presencial",
}

DROP_COLUNAS = [
    "documento",
    "registro_data",
    "codigo_regime_2023",
    "flag_produto",
]

DICIONARIO_PROGRAMAS_EXTERNO = {
    "PG-DIRBEN": (
        "PROGRAMA DE GESTÃO - DIRETORIA DE BENEFÍCIOS E RELACIONAMENTO COM O"
        " CIDADÃO"
    ),
    "PGRP": "PROGRAMA DE GESTÃO EM REGIME DE EXECUÇÃO PARCIAL",
    "CEAP": "CENTRAL ESPECIALIZADA DE ALTA PERFORMANCE",
    "PGD-GABGEX": (
        "PROGRAMA DE GESTÃO E DESEMPENHO - GABINETE DA GERÊNCIA EXECUTIVA"
    ),
    "PG-AUDGER": "PROGRAMA DE GESTÃO - AUDITORIA-GERAL",
    "PG-DIROFL": (
        "PROGRAMA DE GESTÃO - DIRETORIA DE ORÇAMENTO, FINANÇAS E LOGÍSTICA"
    ),
    "PG-DTI": "PROGRAMA DE GESTÃO - DIRETORIA DE TECNOLOGIA DA INFORMAÇÃO",
    "PGD-DGP": (
        "PROGRAMA DE GESTÃO E DESEMPENHO - DIRETORIA DE GESTÃO DE PESSOAS"
    ),
    "PGD-PFE": (
        "PROGRAMA DE GESTÃO E DESEMPENHO - PROCURADORIA FEDERAL ESPECIALIZADA"
    ),
    "PG-CORREG": "PROGRAMA DE GESTÃO - CORREGEDORIA-GERAL",
    "PGD-GERGEX": "PROGRAMA DE GESTÃO E DESEMPENHO - GERÊNCIA EXECUTIVA",
    "PGD-GABSR": (
        "PROGRAMA DE GESTÃO E DESEMPENHO - GABINETE DA SUPERINTENDÊNCIA"
        " REGIONAL"
    ),
    "PGD-PGARP": "PROGRAMA DE GESTÃO DA REABILITAÇÃO PROFISSIONAL",
    "PG-DIGOV": (
        "PROGRAMA DE GESTÃO - DIRETORIA DE GOVERNANÇA, PLANEJAMENTO E INOVAÇÃO"
    ),
    "PGD-GABPRE": "PROGRAMA DE GESTÃO E DESEMPENHO - GABINETE DA PRESIDÊNCIA",
    "PG-ACS": "PROGRAMA DE GESTÃO - ASSESSORIA DE COMUNICAÇÃO SOCIAL",
    "CEABSEMPGD": "PROFISSIONAIS SEM PROGRAMA DE GESTÃO E DESEMPENHO",
}

PROGRAMAS_NAO_PGD = [
    "PACTUAÇÃO DE 6H PELO ACORDO DE GREVE",
    "PROFISSIONAIS SEM PROGRAMA DE GESTÃO E DESEMPENHO",
    "PROGRAMA DAS UNIDADES - ACORDO DE GREVE",
]


def ler_csv(caminho: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(
            caminho, sep=None, engine="python", dtype="str", encoding="utf-8"
        )
    except UnicodeDecodeError:
        return pd.read_csv(
            caminho, sep=None, engine="python", dtype="str", encoding="latin1"
        )


def carregar_e_consolidar_brutos(diretorio: Path) -> pd.DataFrame:
    arquivos = sorted(diretorio.glob("*.csv"))
    logging.info(
        f"Carregando {len(arquivos)} arquivos brutos de '{diretorio}'..."
    )

    dfs = []
    for caminho in arquivos:
        df = ler_csv(caminho)
        df = df.rename(columns=RENAME_MAP)
        df = df.drop(columns=[c for c in DROP_COLUNAS if c in df.columns])

        match = re.search(r"\d{6}", caminho.name)
        df["competencia"] = match.group() if match else caminho.name

        if "modalidade" in df.columns:
            df["modalidade"] = df["modalidade"].replace(RENAME_VALORES_REGIME)
        dfs.append(df)

    df_total = pd.concat(dfs, ignore_index=True, sort=False)
    return df_total


def limpar_e_inferir_status(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Limpando strings e inferindo status funcional...")
    df = df.replace("-", np.nan)

    df["sigla_programa"] = df["sigla_programa"].replace(
        {"ATENDIMENT0": "ATENDIMENTO"}
    )
    df["programa"] = df["programa"].replace({
        "PROFISSIONAIS SEM PROGAMA DE GESTÃO E DESEMPENHO": (
            "PROFISSIONAIS SEM PROGRAMA DE GESTÃO E DESEMPENHO"
        )
    })
    df["lotacao"] = df["lotacao"].str.replace(
        r"\bAG[EÊ]NCIA D[AE] PREVID[EÊ]NCIA SOCIAL\b",
        "APS",
        regex=True,
        case=False,
    )
    df["lotacao"] = df["lotacao"].str.replace(
        r"\bGER[EÊ]NCIA EXECUTIVA\b",
        "GEX",
        regex=True,
        case=False,
    )
    mapa_lotacao_sem_acento = {
        val: "".join(
            c for c in unicodedata.normalize("NFKD", val)
            if not unicodedata.combining(c)
        )
        for val in df["lotacao"].dropna().unique()
    }
    df["lotacao"] = df["lotacao"].map(mapa_lotacao_sem_acento)

    df = df.dropna(subset=["id_matricula"]).copy()
    df["competencia"] = pd.to_datetime(
        df["competencia"], format="%Y%m"
    ).dt.to_period("M")

    condicoes_status1 = [df["status"] == "1", df["status"] == "2"]
    df["status"] = np.select(
        condicoes_status1, ["Designado", "Desligado"], default=df["status"]
    )

    dt_inicio = pd.to_datetime(
        df["dt_inicio_designacao"], format="%d/%m/%Y", errors="coerce"
    )
    dt_fim = pd.to_datetime(
        df["dt_fim_designacao"], format="%d/%m/%Y", errors="coerce"
    )
    comp_fim_mes = df["competencia"].dt.to_timestamp() + pd.offsets.MonthEnd(0)

    condicoes_status2 = [
        df["status"].isna() & dt_inicio.isna(),
        df["status"].isna()
        & dt_inicio.notna()
        & (dt_fim.isna() | (dt_fim >= comp_fim_mes)),
        df["status"].isna()
        & dt_inicio.notna()
        & dt_fim.notna()
        & (dt_fim < comp_fim_mes),
    ]
    df["status"] = np.select(
        condicoes_status2,
        ["Não Designado", "Designado", "Desligado"],
        default=df["status"],
    )

    df["dt_criacao_designacao"] = pd.to_datetime(
        df["dt_criacao_designacao"], format="mixed"
    )
    df["dt_alteracao_designacao"] = pd.to_datetime(
        df["dt_alteracao_designacao"], format="mixed"
    )
    df["dt_inicio_designacao"] = dt_inicio
    df["dt_fim_designacao"] = dt_fim

    return df


def preencher_por_ponte(
    df: pd.DataFrame,
    colunas: list,
    comp_alvo,
    comp_antes,
    comp_depois,
) -> pd.DataFrame:
    cols_id = ["id_matricula"] + colunas
    antes = df[df["competencia"] == comp_antes][cols_id]
    depois = df[df["competencia"] == comp_depois][cols_id]

    ponte = antes.merge(depois, on="id_matricula", suffixes=("_antes", "_depois"))
    condicao = pd.Series(True, index=ponte.index)
    for col in colunas:
        condicao &= ponte[f"{col}_antes"] == ponte[f"{col}_depois"]
    ponte_confiavel = ponte[condicao]

    mask_alvo = df["competencia"] == comp_alvo
    for col in colunas:
        mapa = ponte_confiavel.set_index("id_matricula")[
            f"{col}_antes"
        ].to_dict()
        df.loc[mask_alvo, col] = df.loc[mask_alvo, col].fillna(
            df.loc[mask_alvo, "id_matricula"].map(mapa)
        )
    return df


def enriquecer_cadastros_e_pontes(df: pd.DataFrame) -> pd.DataFrame:
    logging.info(
        "Executando ponte temporal e enriquecimento de programas/linhas..."
    )

    colunas_ponte = ["id_designacao", "dt_criacao_designacao"]
    comps_ordenadas = sorted(df["competencia"].dropna().unique())
    for i in range(1, len(comps_ordenadas) - 1):
        df = preencher_por_ponte(
            df,
            colunas_ponte,
            comps_ordenadas[i],
            comps_ordenadas[i - 1],
            comps_ordenadas[i + 1],
        )

    dicionario_prog = (
        df.dropna(subset=["sigla_programa", "programa"])[
            ["sigla_programa", "programa"]
        ]
        .drop_duplicates()
        .set_index("sigla_programa")["programa"]
        .to_dict()
    )
    dicionario_prog.update(DICIONARIO_PROGRAMAS_EXTERNO)
    df["programa"] = (
        df["sigla_programa"].map(dicionario_prog).fillna(df["programa"])
    )

    dicionario_prog_para_sigla = (
        df.dropna(subset=["programa", "sigla_programa"])[
            ["programa", "sigla_programa"]
        ]
        .drop_duplicates()
        .set_index("programa")["sigla_programa"]
        .to_dict()
    )
    df["sigla_programa"] = df["sigla_programa"].fillna(
        df["programa"].map(dicionario_prog_para_sigla)
    )

    mapa_sigla_linha = (
        df.dropna(subset=["sigla_linha_trabalho", "linha_trabalho"])[
            ["sigla_linha_trabalho", "linha_trabalho"]
        ]
        .drop_duplicates()
        .set_index("sigla_linha_trabalho")["linha_trabalho"]
        .to_dict()
    )
    mapa_linha_sigla = (
        df.dropna(subset=["sigla_linha_trabalho", "linha_trabalho"])[
            ["linha_trabalho", "sigla_linha_trabalho"]
        ]
        .drop_duplicates()
        .set_index("linha_trabalho")["sigla_linha_trabalho"]
        .to_dict()
    )
    df["linha_trabalho"] = df["linha_trabalho"].fillna(
        df["sigla_linha_trabalho"].map(mapa_sigla_linha)
    )
    df["sigla_linha_trabalho"] = df["sigla_linha_trabalho"].fillna(
        df["linha_trabalho"].map(mapa_linha_sigla)
    )

    cols_propagar_desig = [
        "programa",
        "sigla_programa",
        "id_lotacao",
        "lotacao",
        "tipo_entrega",
        "linha_trabalho",
        "sigla_linha_trabalho",
    ]
    df = df.sort_values(["id_designacao", "competencia"])
    df[cols_propagar_desig] = (
        df.groupby("id_designacao")[cols_propagar_desig].ffill().bfill()
    )

    cols_propagar_serv = [
        "id_lotacao",
        "lotacao",
        "tipo_entrega",
        "linha_trabalho",
        "sigla_linha_trabalho",
    ]
    df = df.sort_values(["nome", "competencia"])
    df[cols_propagar_serv] = (
        df.groupby("nome")[cols_propagar_serv].ffill().bfill()
    )

    mapa_pgd = {prog: "Sim" for prog in df["programa"].dropna().unique()}
    for prog in PROGRAMAS_NAO_PGD:
        mapa_pgd[prog] = "Não"

    df["flag_pgd"] = df["programa"].map(mapa_pgd)
    df.loc[df["status"] == "Não Designado", "flag_pgd"] = np.nan

    df["filtro_programa"] = df["sigla_programa"] + " - " + df["programa"]
    df["filtro_linha_trabalho"] = (
        df["sigla_linha_trabalho"] + " - " + df["linha_trabalho"]
    )

    return df


def gerar_hash_usuario(mat: str) -> str:
    hash_obj = hmac.new(
        HMAC_SECRET_KEY, str(mat).encode("utf-8"), hashlib.sha256
    )
    return f"USR-{hash_obj.hexdigest()[:8].upper()}"


def anonimizar_e_tipar(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Aplicando anonimização LGPD, deduplicação e tipagem final...")

    unique_matriculas = df["id_matricula"].dropna().unique()
    mapa_anonimizacao = {
        mat: gerar_hash_usuario(mat) for mat in unique_matriculas
    }
    df["id_usuario"] = df["id_matricula"].map(mapa_anonimizacao)

    df = df.drop(columns=["nome", "id_matricula"], errors="ignore")

    df = df.sort_values(
        by=[
            "id_usuario",
            "competencia",
            "id_designacao",
            "dt_alteracao_designacao",
        ]
    )
    df = df.drop_duplicates(
        subset=["id_usuario", "competencia", "id_designacao"], keep="last"
    )

    cols = ["id_usuario"] + [col for col in df.columns if col != "id_usuario"]
    df = df[cols]
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("[^a-z0-9_]", "", regex=True)
    )

    if "competencia" in df.columns:
        df["competencia"] = df["competencia"].dt.to_timestamp()

    colunas_data = [
        "dt_inicio_designacao",
        "dt_fim_designacao",
        "dt_criacao_designacao",
        "dt_alteracao_designacao",
    ]
    for col in colunas_data:
        if col in df.columns:
            df[col] = (
                df[col].astype(str).str.replace("2203", "2023", regex=False)
            )
            df[col] = pd.to_datetime(df[col], errors="coerce")

    inconsistentes = (
        df["dt_inicio_designacao"].notna()
        & df["dt_fim_designacao"].notna()
        & (df["dt_fim_designacao"] < df["dt_inicio_designacao"])
    )
    df.loc[inconsistentes, "dt_fim_designacao"] = pd.NaT

    if "id_designacao" in df.columns:
        df["id_designacao"] = pd.to_numeric(
            df["id_designacao"], errors="coerce"
        ).astype("Int64")

    colunas_texto = [
        col
        for col in df.select_dtypes(include=["object", "string"]).columns
        if col not in ["competencia"]
    ]
    for col in colunas_texto:
        df[col] = (
            df[col]
            .astype(str)
            .replace({
                "nan": None,
                "NaN": None,
                "None": None,
                "null": None,
                "NULL": None,
                "Null": None,
                "": None,
                "<NA>": None,
                "NaT": None,
            })
        )

    return df


def salvar_artefatos(df: pd.DataFrame) -> None:
    logging.info(f"Exportando artefatos ({len(df)} registros processados)...")
    OUTPUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)

    df.to_parquet(OUTPUT_PARQUET, index=False)

    df_sample = df.sample(n=min(5000, len(df)), random_state=42)
    df_sample.to_csv(OUTPUT_SAMPLE, index=False, sep=";")
    df.to_csv(OUTPUT_CSV, index=False, sep=";")
    logging.info("Pipeline ETL concluído com sucesso!")


def main():
    df_final = (
        carregar_e_consolidar_brutos(DATA_DIR)
        .pipe(limpar_e_inferir_status)
        .pipe(enriquecer_cadastros_e_pontes)
        .pipe(anonimizar_e_tipar)
    )
    salvar_artefatos(df_final)


if __name__ == "__main__":
    main()