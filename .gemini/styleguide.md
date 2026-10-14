# Guia de Revisão de Código — SGP-INSS (inss-pgd-data-pipeline)

Responda **sempre em português (PT-BR)**.

Este repositório é um pipeline de dados ponta a ponta:
**API CKAN do INSS → `download_sgp.py` → `etl_sgp_inss.py` (Parquet) → `pytest` → `load_neon.py` (PostgreSQL Neon) → Power BI**,
orquestrado por GitHub Actions (`.github/workflows/database_sync.yml`) e executável via Docker.

Priorize, nesta ordem: **privacidade (LGPD) → integridade dos dados → idempotência da carga → robustez do pipeline → legibilidade**.

---

## 1. Privacidade e LGPD (CRÍTICO)

- Matrículas/identificadores de servidores **nunca** podem sair do ETL sem pseudonimização via **HMAC-SHA256** com a chave `HMAC_SECRET_KEY`, no formato `USR-XXXXXXXX`.
- Sinalize como **CRITICAL** qualquer mudança que:
  - grave, logue (`logging`, `print`) ou exporte matrícula, CPF, nome ou e-mail em texto claro;
  - troque HMAC por hash simples sem chave (ex.: `hashlib.sha256(valor)`), que é vulnerável a ataque de dicionário;
  - altere o formato `USR-` sem atualizar a validação regex em `tests/test_pipeline.py`;
  - inclua dados reais não anonimizados em arquivos versionados (CSV de amostra, notebooks, fixtures).
- Segredos (`NEON_DATABASE_URL`, `HMAC_SECRET_KEY`, webhooks do Power Automate) devem vir de variáveis de ambiente / GitHub Secrets. Nunca hardcoded, nunca no `.env.example` com valor real.

## 2. Integridade e Qualidade dos Dados

- Toda nova coluna criada no ETL deve:
  - ter tipo explícito (evitar `object` quando for data, inteiro ou categoria);
  - ser refletida no schema da tabela `tb_pgd_inss` no Neon (lembrar o `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`), senão a carga quebra por *schema drift*;
  - ter ao menos um teste em `tests/test_pipeline.py` quando carregar regra de negócio.
- Imputação de `programa` / `sigla_programa` é feita por `id_designacao` (ffill/bfill). A **sigla do programa pode mudar entre competências para a mesma designação** (ex.: 2023-10 vs 2024-04) — questione mudanças que agrupem só por sigla ou que propaguem valores entre designações diferentes.
- Registros com status **"Não Designado"** têm programa legitimamente vazio: não devem ser preenchidos artificialmente.
- Desconfie de `dropna()`, `drop_duplicates()` ou `fillna()` sem `subset` explícito — podem apagar/alterar dados silenciosamente.
- Datas de competência devem ser normalizadas para o primeiro dia do mês (`YYYY-MM-01`).

## 3. Carga Idempotente no Neon (`load_neon.py`)

- A carga segue o padrão **Delete & Insert por competência** dentro de **uma única transação**. Sinalize:
  - `if_exists="replace"` no `to_sql` (derruba índices e causa downtime no Power BI);
  - delete e insert em transações separadas;
  - remoção do `chunksize` ou inserção linha a linha.
- Só competências presentes no lote atual devem ser apagadas — nunca `DELETE` sem `WHERE`.
- Use queries parametrizadas (SQLAlchemy `text()` com bind params). Nunca f-string com valores em SQL.

## 4. Ingestão (`download_sgp.py`)

- Requisições HTTP devem ter `timeout` e tratamento de erro (`raise_for_status`).
- A extração de competência a partir do nome/URL do recurso é frágil: mudanças nos regex de mês/ano exigem teste ou justificativa.
- O download deve continuar idempotente (não baixar novamente arquivos já existentes sem necessidade).

## 5. Pipeline, CI/CD e Docker

- `run_pipeline.sh` usa `set -e` no download/ETL e captura o exit code do pytest — mudanças não podem mascarar falhas de teste.
- No workflow do GitHub Actions: não expor secrets em `echo`, manter versões de actions fixadas, e o webhook do Power Automate só deve disparar **após** carga bem-sucedida.
- Dockerfile: manter imagem `python:3.12-slim`, sem copiar `.env` para a imagem.

## 6. Estilo Python

- Siga PEP 8; nomes de variáveis e funções em `snake_case`, preferencialmente em português, coerentes com o restante do código.
- Prefira operações vetorizadas do pandas a `apply`/loops linha a linha em DataFrames grandes (~650 mil linhas).
- Use `logging` em vez de `print`.
- Não comente sobre formatação trivial (espaços, aspas simples vs duplas) — isso não é prioridade.

## 7. Documentação

- Mudanças de comportamento do pipeline, novas colunas ou novas variáveis de ambiente devem refletir no `README.md` e/ou `.env.example`.
