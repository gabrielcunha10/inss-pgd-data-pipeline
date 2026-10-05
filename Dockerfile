FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["sh", "-c", "python tratamento/download_sgp.py && python tratamento/etl_sgp_inss.py && pytest tests/ && rm -f tests/pgd_designacoes_inss_2023_2026.parquet"]
