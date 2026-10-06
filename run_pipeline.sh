#!/bin/sh

# Interrompe a execução se houver erro no download ou no ETL
set -e

echo "Iniciando download dos dados..."
python tratamento/download_sgp.py

echo "Executando ETL..."
python tratamento/etl_sgp_inss.py

# Desativa a interrupção imediata para podermos capturar o resultado dos testes
set +e

echo "Executando testes..."
pytest tests/
TEST_EXIT_CODE=$?

echo "Limpando arquivo parquet temporário..."
rm -f tests/pgd_designacoes_inss_2023_2026.parquet

# Retorna o código de saída dos testes (se for 0 = sucesso, se > 0 = falha)
exit $TEST_EXIT_CODE
