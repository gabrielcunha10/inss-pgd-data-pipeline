import hashlib
import logging
import os
import sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.types import BigInteger, Date, DateTime, Text

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent.parent
PARQUET_FILE = PROJECT_DIR / "tests" / "pgd_designacoes_inss_2023_2026.parquet"
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
    colunas_ordenadas = sorted(df_particao.columns)
    df_norm = df_particao[colunas_ordenadas].copy()
    for col in colunas_ordenadas:
        df_norm[col] = df_norm[col].astype(str).fillna("")
    df_norm = df_norm.sort_values(by=colunas_ordenadas).reset_index(drop=True)
    row_hashes = pd.util.hash_pandas_object(df_norm, index=False).values.tobytes()
    schema_sig = ",".join(colunas_ordenadas).encode("utf-8")
    return hashlib.sha256(schema_sig + row_hashes).hexdigest()


def main(full_refresh: bool = False):
    logging.info("Iniciando a carga dos dados para o Neon DB...")

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("Variável de ambiente DATABASE_URL não encontrada.")

    logging.info(f"Lendo dados do arquivo: {PARQUET_FILE}")
    if not PARQUET_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {PARQUET_FILE}. Rode o ETL antes.")

    df_total = pd.read_parquet(PARQUET_FILE)
    dtype_mapping = construir_dtype_mapping(df_total.columns)

    resumo_local = {}
    for comp_ts, df_part in df_total.groupby("competencia", dropna=True):
        comp_str = comp_ts.strftime("%Y-%m-%d")
        resumo_local[comp_str] = {
            "qtd": len(df_part),
            "hash": calcular_hash_competencia(df_part),
        }

    engine = create_engine(db_url)
    try:
        with engine.begin() as conn:
            inspector = inspect(conn)
            tabela_existe = inspector.has_table("tb_pgd_inss")
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

            if not tabela_existe:
                logging.info("Tabela 'tb_pgd_inss' não existe. Criando estrutura inicial no banco...")
                df_total.head(0).to_sql(
                    "tb_pgd_inss",
                    con=conn,
                    if_exists="append",
                    index=False,
                    dtype=dtype_mapping,
                )
                competencias_para_carregar = sorted(resumo_local.keys())
            elif full_refresh:
                logging.info("Modo full_refresh ativado: todas as competências serão recarregadas.")
                competencias_para_carregar = sorted(resumo_local.keys())
            else:
                colunas_banco = {c["name"] for c in inspector.get_columns("tb_pgd_inss")}
                colunas_locais = set(df_total.columns)

                if colunas_banco and colunas_banco != colunas_locais:
                    logging.info(
                        "Mudança de schema detectada nas colunas do ETL. Recarregando tabela completa..."
                    )
                    conn.execute(text("DROP TABLE tb_pgd_inss"))
                    df_total.head(0).to_sql(
                        "tb_pgd_inss",
                        con=conn,
                        if_exists="append",
                        index=False,
                        dtype=dtype_mapping,
                    )
                    competencias_para_carregar = sorted(resumo_local.keys())
                else:
                    contagem_banco = {}
                    rows_cnt = conn.execute(
                        text("SELECT CAST(competencia AS TEXT), COUNT(*) FROM tb_pgd_inss GROUP BY competencia")
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
                logging.info(
                    "Banco já está 100% sincronizado com o ETL atual (hashes idênticos). "
                    "Nenhum registro precisou ser reenviado."
                )
                return

            if tabela_existe:
                logging.info(
                    f"Executando exclusão preventiva de {len(competencias_para_carregar)} competência(s) "
                    "novas ou alteradas para carga idempotente..."
                )
                conn.execute(
                    text("DELETE FROM tb_pgd_inss WHERE competencia = ANY(CAST(:comps AS date[]))"),
                    {"comps": list(competencias_para_carregar)},
                )

            datas_alvo = pd.to_datetime(competencias_para_carregar)
            df_carga = df_total[df_total["competencia"].isin(datas_alvo)]

            logging.info(
                f"Inserindo {len(df_carga)} registros ({len(competencias_para_carregar)} competência(s)) "
                "na tabela 'tb_pgd_inss' em lotes (chunksize=10.000)..."
            )
            df_carga.to_sql(
                "tb_pgd_inss",
                con=conn,
                if_exists="append",
                index=False,
                dtype=dtype_mapping,
                chunksize=10000,
            )

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
            f"({len(competencias_para_carregar)} competência(s)) na tabela 'tb_pgd_inss' no Neon Tech."
        )
    except Exception as e:
        logging.error(f"Erro ao enviar dados de forma incremental: {e}")
        raise e


if __name__ == "__main__":
    forcar = "--full-refresh" in sys.argv
    main(full_refresh=forcar)
