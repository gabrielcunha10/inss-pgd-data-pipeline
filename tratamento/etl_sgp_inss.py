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

PROJECT_DIR = Path(__file__).resolve().parent.parent
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
_raw_hmac_key = os.getenv("HMAC_SECRET_KEY")
if not _raw_hmac_key:
    raise ValueError(
        "A variável de ambiente 'HMAC_SECRET_KEY' é obrigatória para conformidade LGPD. "
        "Defina-a no arquivo .env ou nos Secrets do GitHub Actions."
    )
HMAC_SECRET_KEY = _raw_hmac_key.encode("utf-8")
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



def normalizar_id_lotacao(
    serie: pd.Series,
    codigos_6_conhecidos: set = None,
    codigos_8_conhecidos: set = None,
) -> pd.Series:
    """Normaliza codigos de UORG/lotacao SIAPE do INSS.

    Corrige truncamento de zeros a esquerda gerados por exportacao numerica:
    - 4 digitos -> 5 digitos (ex: '1800' -> '01800' para Corregedoria e GEX sedes)
    - 7 digitos -> 8 digitos (ex: '4025060' -> '04025060' para APS conhecidas de 8 digitos)
    - 5 digitos -> 6 digitos caso coincida com subunidade conhecida do INSS
    """
    def _norm(val):
        if pd.isna(val):
            return None
        s = str(val).strip()
        if s.endswith(".0"):
            s = s[:-2]
        if not s or s.lower() in ("nan", "none", "null", "<na>"):
            return None
        if not s.isdigit():
            return s
        n = len(s)
        if n == 4:
            return s.zfill(5)
        elif n == 7 and (codigos_8_conhecidos is None or ("0" + s) in codigos_8_conhecidos):
            return s.zfill(8)
        elif n == 5 and codigos_6_conhecidos and ("0" + s) in codigos_6_conhecidos:
            return "0" + s
        return s

    return serie.map(_norm)


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

    if "id_lotacao" in df.columns:
        codigos_raw = set(
            df["id_lotacao"]
            .dropna()
            .astype(str)
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
        )
        conhecidos_6 = {c for c in codigos_raw if len(c) == 6}
        conhecidos_8 = {c for c in codigos_raw if len(c) == 8}
        df["id_lotacao"] = normalizar_id_lotacao(
            df["id_lotacao"], conhecidos_6, conhecidos_8
        )

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
        df["dt_criacao_designacao"], format="mixed", dayfirst=True
    )
    df["dt_alteracao_designacao"] = pd.to_datetime(
        df["dt_alteracao_designacao"], format="mixed", dayfirst=True
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

    # Mapeamento deterministico 1-para-1 entre lotacao e id_lotacao (apenas pares univocos)
    pares_validos = (
        df.dropna(subset=["lotacao", "id_lotacao"])[["lotacao", "id_lotacao"]]
        .drop_duplicates()
    )
    contagem_ids_por_lot = pares_validos.groupby("lotacao")["id_lotacao"].nunique()
    lotacoes_univocas = contagem_ids_por_lot[contagem_ids_por_lot == 1].index
    mapa_lotacao_para_id = (
        pares_validos[pares_validos["lotacao"].isin(lotacoes_univocas)]
        .set_index("lotacao")["id_lotacao"]
        .to_dict()
    )
    df["id_lotacao"] = df["id_lotacao"].fillna(df["lotacao"].map(mapa_lotacao_para_id))

    contagem_lots_por_id = pares_validos.groupby("id_lotacao")["lotacao"].nunique()
    ids_univocos = contagem_lots_por_id[contagem_lots_por_id == 1].index
    mapa_id_para_lotacao = (
        pares_validos[pares_validos["id_lotacao"].isin(ids_univocos)]
        .set_index("id_lotacao")["lotacao"]
        .to_dict()
    )
    df["lotacao"] = df["lotacao"].fillna(df["id_lotacao"].map(mapa_id_para_lotacao))

    cols_propagar_desig = [
        "programa",
        "sigla_programa",
        "id_lotacao",
        "lotacao",
        "tipo_entrega",
        "linha_trabalho",
        "sigla_linha_trabalho",
    ]
    # Isolamento de NaN: apenas propaga entre registros com id_designacao preenchido
    mask_desig = df["id_designacao"].notna()
    df_desig_sorted = df[mask_desig].sort_values(["id_designacao", "competencia"])
    df.loc[mask_desig, cols_propagar_desig] = (
        df_desig_sorted.groupby("id_designacao")[cols_propagar_desig].ffill().bfill()
    )

    cols_propagar_serv = [
        "id_lotacao",
        "lotacao",
        "tipo_entrega",
        "linha_trabalho",
        "sigla_linha_trabalho",
    ]
    # Agrupamento seguro por matricula (evita colisao de homonimos com 'nome')
    col_agrupador_serv = "id_matricula" if "id_matricula" in df.columns else "nome"
    df = df.sort_values([col_agrupador_serv, "competencia"])
    df[cols_propagar_serv] = (
        df.groupby(col_agrupador_serv)[cols_propagar_serv].ffill().bfill()
    )

    mapa_pgd = {prog: "Sim" for prog in df["programa"].dropna().unique()}
    for prog in PROGRAMAS_NAO_PGD:
        mapa_pgd[prog] = "Não"

    df["flag_pgd"] = df["programa"].map(mapa_pgd)
    df.loc[df["status"] == "Não Designado", "flag_pgd"] = np.nan

    cond_prog = df["sigla_programa"].notna() & df["programa"].notna()
    df["filtro_programa"] = np.where(
        cond_prog,
        df["sigla_programa"].astype(str) + " - " + df["programa"].astype(str),
        None,
    )

    cond_linha = df["sigla_linha_trabalho"].notna() & df["linha_trabalho"].notna()
    df["filtro_linha_trabalho"] = np.where(
        cond_linha,
        df["sigla_linha_trabalho"].astype(str)
        + " - "
        + df["linha_trabalho"].astype(str),
        None,
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