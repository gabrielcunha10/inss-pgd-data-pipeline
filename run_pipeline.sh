#!/bin/sh
set -e

echo "Iniciando execução orquestrada do pipeline via Prefect..."
python pipeline_flow.py "$@"
EXIT_CODE=$?

echo "Limpando arquivo parquet temporário de testes..."
rm -f tests/pgd_designacoes_inss_2023_2026.parquet

exit $EXIT_CODE
