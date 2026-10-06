import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.types import BigInteger, Date, DateTime, Text

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent.parent
PARQUET_FILE = PROJECT_DIR / "tests" / "pgd_designacoes_inss_2023_2026.parquet"

def main():
    print("Iniciando a carga dos dados para o Neon DB...")
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("Variável de ambiente DATABASE_URL não encontrada.")

    print(f"Lendo dados do arquivo: {PARQUET_FILE}")
    if not PARQUET_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {PARQUET_FILE}. Rode o ETL antes.")
        
    df_total = pd.read_parquet(PARQUET_FILE)

    colunas_data = [
        'dt_inicio_designacao',
        'dt_fim_designacao',
        'dt_criacao_designacao',
        'dt_alteracao_designacao',
    ]
    colunas_id = ['id_designacao']

    dtype_mapping = {}
    for col in df_total.columns:
        if col == 'competencia':
            dtype_mapping[col] = Date()
        elif col in colunas_data:
            dtype_mapping[col] = DateTime()
        elif col in colunas_id:
            dtype_mapping[col] = BigInteger()
        else:
            dtype_mapping[col] = Text()

    engine = create_engine(db_url)
    try:
        competencias_datas = [
            d.strftime('%Y-%m-%d')
            for d in df_total['competencia'].dropna().unique()
        ]

        with engine.begin() as conn:
            inspector = inspect(conn)
            tabela_existe = inspector.has_table('tb_pgd_inss')

            if not tabela_existe:
                print("Tabela 'tb_pgd_inss' não existe. Criando estrutura inicial no banco...")
                df_total.head(0).to_sql(
                    'tb_pgd_inss',
                    con=conn,
                    if_exists='append',
                    index=False,
                    dtype=dtype_mapping,
                )
            elif competencias_datas:
                print(f"Executando exclusão preventiva de {len(competencias_datas)} competência(s) para carga idempotente...")
                conn.execute(
                    text("DELETE FROM tb_pgd_inss WHERE competencia = ANY(CAST(:comps AS date[]))"),
                    {"comps": list(competencias_datas)}
                )

            print(f"Inserindo {len(df_total)} registros na tabela 'tb_pgd_inss' em lotes (chunksize=10.000)...")
            df_total.to_sql(
                'tb_pgd_inss',
                con=conn,
                if_exists='append',
                index=False,
                dtype=dtype_mapping,
                chunksize=10000,
            )

        print(
            f"[SUCCESS] Carga incremental concluída: {len(df_total)} linhas sincronizadas "
            f"({len(competencias_datas)} competência(s)) na tabela 'tb_pgd_inss' no Neon Tech."
        )
    except Exception as e:
        print(f"Erro ao enviar dados de forma incremental: {e}")
        raise e

if __name__ == "__main__":
    main()
