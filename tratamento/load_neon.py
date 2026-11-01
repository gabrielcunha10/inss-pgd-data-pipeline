import hashlib
import logging
import os
import sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.types import BigInteger, Date, DateTime, Float, Integer, Text

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent.parent
PARQUET_FILE = PROJECT_DIR / "tests" / "pgd_designacoes_inss_2023_2026.parquet"
INSIGHTS_CSV_FILE = PROJECT_DIR / "dashboard" / "insights_historico_powerbi.csv"
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


def construir_dtype_mapping(colunas: list) -> dict:
    colunas_data = [
        "dt_inicio_designacao",
        "dt_fim_designacao",
        "dt_criacao_designacao",
        "dt_alteracao_designacao",
    ]
    colunas_id = ["id_designacao"]

    dtype_mapping = {}
    for col in colunas:
        if col == "competencia":
            dtype_mapping[col] = Date()
        elif col in colunas_data:
            dtype_mapping[col] = DateTime()
        elif col in colunas_id:
            dtype_mapping[col] = BigInteger()
        else:
            dtype_mapping[col] = Text()
    return dtype_mapping


def calcular_hash_competencia(df_particao: pd.DataFrame) -> str:
    """Calcula hash SHA-256 determinístico e agnóstico à versão do Pandas sobre o conteúdo da partição."""
    colunas_ordenadas = sorted(df_particao.columns)
    df_norm = df_particao[colunas_ordenadas].copy()
    for col in colunas_ordenadas:
        df_norm[col] = df_norm[col].astype(str)
        df_norm[col] = df_norm[col].replace({"nan": "", "None": "", "<NA>": "", "NaT": ""})
    df_norm = df_norm.sort_values(by=colunas_ordenadas).reset_index(drop=True)
    payload_csv = df_norm.to_csv(index=False, lineterminator="\n").encode("utf-8")
    return hashlib.sha256(payload_csv).hexdigest()


MESES_PT_BR = {
    1: ("Janeiro", "Jan"),
    2: ("Fevereiro", "Fev"),
    3: ("Março", "Mar"),
    4: ("Abril", "Abr"),
    5: ("Maio", "Mai"),
    6: ("Junho", "Jun"),
    7: ("Julho", "Jul"),
    8: ("Agosto", "Ago"),
    9: ("Setembro", "Set"),
    10: ("Outubro", "Out"),
    11: ("Novembro", "Nov"),
    12: ("Dezembro", "Dez"),
}


def construir_star_schema(df_total: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Decompõe o DataFrame consolidado em modelo dimensional Star Schema (1 Fato + 5 Dimensões)."""
    df = df_total.copy()

    # 1. dim_programa
    cols_prog = ["sigla_programa", "programa", "flag_pgd", "filtro_programa"]
    cols_prog_exist = [c for c in cols_prog if c in df.columns]
    if "sigla_programa" in df.columns:
        df_prog = (
            df[cols_prog_exist]
            .dropna(subset=["sigla_programa"])
            .drop_duplicates(subset=["sigla_programa"])
            .sort_values("sigla_programa")
            .reset_index(drop=True)
        )
    else:
        df_prog = pd.DataFrame(columns=cols_prog)
    for c in cols_prog:
        if c not in df_prog.columns:
            df_prog[c] = None
    df_prog.insert(0, "sk_programa", range(1, len(df_prog) + 1))

    # 2. dim_linha_trabalho
    cols_linha = ["sigla_linha_trabalho", "linha_trabalho", "filtro_linha_trabalho"]
    cols_linha_exist = [c for c in cols_linha if c in df.columns]
    if "sigla_linha_trabalho" in df.columns:
        df_linha = (
            df[cols_linha_exist]
            .dropna(subset=["sigla_linha_trabalho"])
            .drop_duplicates(subset=["sigla_linha_trabalho"])
            .sort_values("sigla_linha_trabalho")
            .reset_index(drop=True)
        )
    else:
        df_linha = pd.DataFrame(columns=cols_linha)
    for c in cols_linha:
        if c not in df_linha.columns:
            df_linha[c] = None
    df_linha.insert(0, "sk_linha_trabalho", range(1, len(df_linha) + 1))

    # 3. dim_lotacao
    cols_lot = ["id_lotacao", "lotacao"]
    cols_lot_exist = [c for c in cols_lot if c in df.columns]
    if "id_lotacao" in df.columns:
        df_lot = (
            df[cols_lot_exist]
            .dropna(subset=["id_lotacao"])
            .drop_duplicates(subset=["id_lotacao"])
            .sort_values("id_lotacao")
            .reset_index(drop=True)
        )
    elif "lotacao" in df.columns:
        df_lot = (
            df[["lotacao"]]
            .dropna(subset=["lotacao"])
            .drop_duplicates(subset=["lotacao"])
            .sort_values("lotacao")
            .reset_index(drop=True)
        )
        df_lot["id_lotacao"] = df_lot["lotacao"]
    else:
        df_lot = pd.DataFrame(columns=cols_lot)
    for c in cols_lot:
        if c not in df_lot.columns:
            df_lot[c] = None
    df_lot = df_lot[["id_lotacao", "lotacao"]]
    df_lot.insert(0, "sk_lotacao", range(1, len(df_lot) + 1))

    # 4. dim_servidor
    if "id_usuario" in df.columns and "competencia" in df.columns:
        df_serv = (
            df.dropna(subset=["id_usuario"])
            .groupby("id_usuario", as_index=False)
            .agg(
                primeira_competencia=("competencia", "min"),
                ultima_competencia=("competencia", "max"),
            )
            .sort_values("id_usuario")
            .reset_index(drop=True)
        )
    else:
        df_serv = pd.DataFrame(columns=["id_usuario", "primeira_competencia", "ultima_competencia"])

    # 5. dim_calendario
    if "competencia" in df.columns:
        datas_unicas = sorted(pd.to_datetime(df["competencia"].dropna().unique()))
        registros_cal = []
        for dt in datas_unicas:
            ts = pd.Timestamp(dt)
            nome_mes, abrev_mes = MESES_PT_BR.get(ts.month, ("", ""))
            registros_cal.append({
                "competencia": ts,
                "ano": int(ts.year),
                "mes": int(ts.month),
                "nome_mes": nome_mes,
                "mes_abrev": abrev_mes,
                "competencia_fmt": ts.strftime("%m/%Y"),
                "trimestre": f"{(ts.month - 1) // 3 + 1}º Tri",
            })
        df_cal = pd.DataFrame(registros_cal)
    else:
        df_cal = pd.DataFrame(
            columns=["competencia", "ano", "mes", "nome_mes", "mes_abrev", "competencia_fmt", "trimestre"]
        )

    # 6. fato_designacoes (mapeando textos para Surrogate Keys sk_*)
    mapa_prog = df_prog.set_index("sigla_programa")["sk_programa"].to_dict()
    mapa_linha = df_linha.set_index("sigla_linha_trabalho")["sk_linha_trabalho"].to_dict()
    mapa_lot = df_lot.set_index("id_lotacao")["sk_lotacao"].to_dict() if "id_lotacao" in df.columns else df_lot.set_index("lotacao")["sk_lotacao"].to_dict()

    df_fato = pd.DataFrame(index=df.index)
    df_fato["competencia"] = df["competencia"] if "competencia" in df.columns else None
    df_fato["id_usuario"] = df["id_usuario"] if "id_usuario" in df.columns else None
    df_fato["id_designacao"] = df["id_designacao"] if "id_designacao" in df.columns else None
    df_fato["sk_programa"] = (
        df["sigla_programa"].map(mapa_prog).astype("Int64")
        if "sigla_programa" in df.columns
        else pd.Series([pd.NA] * len(df), dtype="Int64")
    )
    df_fato["sk_linha_trabalho"] = (
        df["sigla_linha_trabalho"].map(mapa_linha).astype("Int64")
        if "sigla_linha_trabalho" in df.columns
        else pd.Series([pd.NA] * len(df), dtype="Int64")
    )
    if "id_lotacao" in df.columns:
        df_fato["sk_lotacao"] = df["id_lotacao"].map(mapa_lot).astype("Int64")
    elif "lotacao" in df.columns:
        df_fato["sk_lotacao"] = df["lotacao"].map(mapa_lot).astype("Int64")
    else:
        df_fato["sk_lotacao"] = pd.Series([pd.NA] * len(df), dtype="Int64")

    for col_atrib in [
        "status",
        "modalidade",
        "tipo_entrega",
        "motivo_desligamento",
        "dt_inicio_designacao",
        "dt_fim_designacao",
        "dt_criacao_designacao",
        "dt_alteracao_designacao",
    ]:
        df_fato[col_atrib] = df[col_atrib] if col_atrib in df.columns else None

    return {
        "dim_programa": df_prog,
        "dim_linha_trabalho": df_linha,
        "dim_lotacao": df_lot,
        "dim_servidor": df_serv,
        "dim_calendario": df_cal,
        "fato_designacoes": df_fato,
    }


def sincronizar_star_schema_neon(
    conn,
    inspector,
    df_total: pd.DataFrame,
    competencias_para_carregar: list[str],
    full_refresh: bool = False,
) -> None:
    """Sincroniza as 5 dimensões e a tabela fato_designacoes de forma idempotente no PostgreSQL."""
    logging.info("Sincronizando modelo Star Schema (fato_designacoes + 5 dimensões) no PostgreSQL...")
    star = construir_star_schema(df_total)

    dimensoes_dtypes = {
        "dim_programa": {
            "sk_programa": Integer(),
            "sigla_programa": Text(),
            "programa": Text(),
            "flag_pgd": Text(),
            "filtro_programa": Text(),
        },
        "dim_linha_trabalho": {
            "sk_linha_trabalho": Integer(),
            "sigla_linha_trabalho": Text(),
            "linha_trabalho": Text(),
            "filtro_linha_trabalho": Text(),
        },
        "dim_lotacao": {
            "sk_lotacao": Integer(),
            "id_lotacao": Text(),
            "lotacao": Text(),
        },
        "dim_servidor": {
            "id_usuario": Text(),
            "primeira_competencia": Date(),
            "ultima_competencia": Date(),
        },
        "dim_calendario": {
            "competencia": Date(),
            "ano": Integer(),
            "mes": Integer(),
            "nome_mes": Text(),
            "mes_abrev": Text(),
            "competencia_fmt": Text(),
            "trimestre": Text(),
        },
    }

    for nome_dim, df_dim in star.items():
        if nome_dim == "fato_designacoes":
            continue
        df_dim.to_sql(
            nome_dim,
            con=conn,
            if_exists="replace",
            index=False,
            dtype=dimensoes_dtypes[nome_dim],
            chunksize=10000,
        )

    dtype_fato = {
        "competencia": Date(),
        "id_usuario": Text(),
        "id_designacao": BigInteger(),
        "sk_programa": Integer(),
        "sk_linha_trabalho": Integer(),
        "sk_lotacao": Integer(),
        "status": Text(),
        "modalidade": Text(),
        "tipo_entrega": Text(),
        "motivo_desligamento": Text(),
        "dt_inicio_designacao": DateTime(),
        "dt_fim_designacao": DateTime(),
        "dt_criacao_designacao": DateTime(),
        "dt_alteracao_designacao": DateTime(),
    }

    df_fato = star["fato_designacoes"]
    fato_existe = inspector.has_table("fato_designacoes")

    if not fato_existe or full_refresh:
        if fato_existe:
            conn.execute(text("DROP TABLE fato_designacoes"))
        df_fato.head(0).to_sql(
            "fato_designacoes",
            con=conn,
            if_exists="append",
            index=False,
            dtype=dtype_fato,
        )
        df_fato_carga = df_fato
    else:
        conn.execute(
            text("DELETE FROM fato_designacoes WHERE competencia = ANY(CAST(:comps AS date[]))"),
            {"comps": list(competencias_para_carregar)},
        )
        datas_alvo = {pd.to_datetime(c).date() for c in competencias_para_carregar}
        df_fato_carga = df_fato[df_fato["competencia"].isin(datas_alvo)]

    df_fato_carga.to_sql(
        "fato_designacoes",
        con=conn,
        if_exists="append",
        index=False,
        dtype=dtype_fato,
        chunksize=10000,
    )
    logging.info(
        f"Star Schema atualizado: {len(df_fato_carga)} registros em 'fato_designacoes' e 5 dimensões sincronizadas."
    )


def sincronizar_insights_neon(conn, caminho_csv: Path = INSIGHTS_CSV_FILE) -> int:
    """Sincroniza o histórico de insights executivos de IA (CSV) para a tabela insights_historico_powerbi no PostgreSQL."""
    if not caminho_csv.exists():
        logging.warning(f"Arquivo de insights não encontrado em {caminho_csv}. Pulando sincronização de insights.")
        return 0

    df_insights = pd.read_csv(caminho_csv, encoding="utf-8")
    if df_insights.empty:
        logging.warning("Arquivo de insights está vazio. Pulando sincronização de insights.")
        return 0

    df_insights = df_insights.copy()
    if "competencia" in df_insights.columns:
        df_insights["competencia"] = pd.to_datetime(df_insights["competencia"]).dt.date

    dtype_insights = {
        "competencia": Date(),
        "competencia_mes_ano": Text(),
        "servidores_plano_ativo": BigInteger(),
        "servidores_plano_ativo_fmt": Text(),
        "variacao_mensal_mom": Float(),
        "variacao_mensal_mom_fmt": Text(),
        "adesao_teletrabalho_pct": Float(),
        "adesao_teletrabalho_fmt": Text(),
        "adesao_remoto_pct": Float(),
        "adesao_remoto_fmt": Text(),
        "motor_analise_ia": Text(),
        "diagnostico_executivo": Text(),
        "principais_movimentacoes_mom": Text(),
        "matriz_alertas_recomendacoes": Text(),
    }

    df_insights.to_sql(
        "insights_historico_powerbi",
        con=conn,
        if_exists="replace",
        index=False,
        dtype={k: v for k, v in dtype_insights.items() if k in df_insights.columns},
    )
    logging.info(
        f"Tabela 'insights_historico_powerbi' sincronizada no PostgreSQL com {len(df_insights)} competências."
    )
    return len(df_insights)


def main(full_refresh: bool = False):
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("Variável de ambiente DATABASE_URL não encontrada.")

    if not PARQUET_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {PARQUET_FILE}. Rode o ETL antes.")

    logging.info(f"Lendo base tratada de {PARQUET_FILE}...")
    df_total = pd.read_parquet(PARQUET_FILE)
    df_total["competencia"] = pd.to_datetime(df_total["competencia"]).dt.date

    # Resumo local por competência
    resumo_local = {}
    for comp, df_part in df_total.groupby("competencia"):
        comp_str = str(comp)
        resumo_local[comp_str] = {
            "qtd": len(df_part),
            "hash": calcular_hash_competencia(df_part),
        }

    engine = create_engine(db_url)
    try:
        with engine.begin() as conn:
            inspector = inspect(conn)
            fato_existe = inspector.has_table("fato_designacoes")
            controle_existe = inspector.has_table("tb_controle_carga")

            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS tb_controle_carga (
                        competencia DATE PRIMARY KEY,
                        qtd_registros BIGINT NOT NULL,
                        hash_dados TEXT NOT NULL,
                        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )

            if not fato_existe or full_refresh:
                if full_refresh:
                    logging.info("Modo full_refresh ativado: todas as competências do Star Schema serão recarregadas.")
                else:
                    logging.info("Tabela 'fato_designacoes' não existe. Criando modelo Star Schema inicial no banco...")
                competencias_para_carregar = sorted(resumo_local.keys())
            else:
                contagem_banco = {}
                rows_cnt = conn.execute(
                    text("SELECT CAST(competencia AS TEXT), COUNT(*) FROM fato_designacoes GROUP BY competencia")
                ).fetchall()
                for r in rows_cnt:
                    if r[0] is not None:
                        contagem_banco[str(r[0])[:10]] = int(r[1])

                hashes_banco = {}
                if controle_existe:
                    rows_ctrl = conn.execute(
                        text("SELECT CAST(competencia AS TEXT), qtd_registros, hash_dados FROM tb_controle_carga")
                    ).fetchall()
                    for r in rows_ctrl:
                        if r[0] is not None:
                            hashes_banco[str(r[0])[:10]] = (int(r[1]), str(r[2]))

                competencias_para_carregar = []
                competencias_bootstrap = []

                for comp_str, info in sorted(resumo_local.items()):
                    qtd_local = info["qtd"]
                    hash_local = info["hash"]
                    qtd_db = contagem_banco.get(comp_str)

                    if comp_str not in hashes_banco:
                        if qtd_db == qtd_local:
                            competencias_bootstrap.append(comp_str)
                        else:
                            competencias_para_carregar.append(comp_str)
                    else:
                        qtd_ctrl, hash_ctrl = hashes_banco[comp_str]
                        if qtd_db != qtd_local or qtd_ctrl != qtd_local or hash_ctrl != hash_local:
                            competencias_para_carregar.append(comp_str)

                if competencias_bootstrap:
                    logging.info(
                        f"Registrando hashes iniciais de {len(competencias_bootstrap)} competência(s) "
                        "já presentes no banco (sem reenvio de dados)..."
                    )
                    for comp_str in competencias_bootstrap:
                        info = resumo_local[comp_str]
                        conn.execute(
                            text(
                                """
                                INSERT INTO tb_controle_carga (competencia, qtd_registros, hash_dados, atualizado_em)
                                VALUES (CAST(:comp AS DATE), :qtd, :hash, CURRENT_TIMESTAMP)
                                ON CONFLICT (competencia) DO UPDATE
                                SET qtd_registros = EXCLUDED.qtd_registros,
                                    hash_dados = EXCLUDED.hash_dados,
                                    atualizado_em = CURRENT_TIMESTAMP
                                """
                            ),
                            {"comp": comp_str, "qtd": info["qtd"], "hash": info["hash"]},
                        )

            if not competencias_para_carregar:
                if not inspector.has_table("insights_historico_powerbi"):
                    sincronizar_insights_neon(conn=conn)
                else:
                    logging.info(
                        "Banco já está 100% sincronizado com o ETL atual (hashes idênticos). "
                        "Nenhum registro precisou ser reenviado."
                    )
                return

            datas_alvo = {pd.to_datetime(c).date() for c in competencias_para_carregar}
            df_carga = df_total[df_total["competencia"].isin(datas_alvo)]

            logging.info(
                f"Sincronizando {len(df_carga)} registros ({len(competencias_para_carregar)} competência(s)) "
                "no modelo Star Schema (fato_designacoes + 5 dimensões)..."
            )
            sincronizar_star_schema_neon(
                conn=conn,
                inspector=inspector,
                df_total=df_total,
                competencias_para_carregar=competencias_para_carregar,
                full_refresh=full_refresh or (not fato_existe),
            )
            sincronizar_insights_neon(conn=conn)

            for comp_str in competencias_para_carregar:
                info = resumo_local[comp_str]
                conn.execute(
                    text(
                        """
                        INSERT INTO tb_controle_carga (competencia, qtd_registros, hash_dados, atualizado_em)
                        VALUES (CAST(:comp AS DATE), :qtd, :hash, CURRENT_TIMESTAMP)
                        ON CONFLICT (competencia) DO UPDATE
                        SET qtd_registros = EXCLUDED.qtd_registros,
                            hash_dados = EXCLUDED.hash_dados,
                            atualizado_em = CURRENT_TIMESTAMP
                        """
                    ),
                    {"comp": comp_str, "qtd": info["qtd"], "hash": info["hash"]},
                )

        logging.info(
            f"Carga incremental concluída com sucesso: {len(df_carga)} linhas sincronizadas "
            f"({len(competencias_para_carregar)} competência(s)) no Star Schema (Neon Tech)."
        )
    except Exception as e:
        logging.error(f"Erro ao enviar dados de forma incremental: {e}")
        raise e


if __name__ == "__main__":
    forcar = "--full-refresh" in sys.argv
    main(full_refresh=forcar)
