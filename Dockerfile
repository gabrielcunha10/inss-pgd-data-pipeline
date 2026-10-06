FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Garante quebras de linha LF no script (evita erro se vier com CRLF do Windows)
RUN sed -i 's/\r$//' run_pipeline.sh

CMD ["sh", "run_pipeline.sh"]
