# Pipeline de Dados e Analytics — Programa de Gestão de Desempenho (PGD) INSS

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL Neon](https://img.shields.io/badge/Database-PostgreSQL%20(Neon)-4169E1?logo=postgresql&logoColor=white)](https://neon.tech/)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Power BI](https://img.shields.io/badge/Dashboard-Power%20BI-F2C811?logo=power-bi&logoColor=black)](https://powerbi.microsoft.com/)
[![Power Automate](https://img.shields.io/badge/Automation-Power%20Automate-0066FF?logo=power-automate&logoColor=white)](https://powerautomate.microsoft.com/)
[![LGPD](https://img.shields.io/badge/Compliance-LGPD%20Anonymized-008080)](#privacidade-e-conformidade-com-a-lgpd)

Pipeline de Engenharia de Dados e Analytics ponta a ponta que automatiza a ingestão contínua de dados abertos do governo federal via API pública, executa limpeza, enriquecimento e padronização com Python/Pandas, carrega a base consolidada em um banco relacional em nuvem (**PostgreSQL no Neon Tech**) e mantém um dashboard interativo no **Power BI** atualizado de forma autônoma via **GitHub Actions** e **Power Automate**.

O projeto analisa o histórico do **Programa de Gestão e Desempenho (PGD)** aplicado ao quadro de atendimento do INSS (ACSINSS), cobrindo de **outubro/2023 em diante** (mais de 500 mil registros consolidados).

---

## 🏛️ Contexto e Motivação

Este projeto foi desenvolvido como peça de portfólio em Engenharia e Análise de Dados, inspirado pelo processo seletivo de estágio da **Dataprev**. Durante a preparação para a seleção, surgiu o interesse pela atuação estratégica da empresa no processamento, governança e gestão de dados que sustentam a previdência, seguridade social e políticas públicas no Brasil.

Lidar com dados governamentais reais impõe desafios práticos como:
- Mudanças de layout ao longo do tempo (sistemas exportadores com cabeçalhos e formatos mutáveis);
- Arquivos com múltiplos encodings (`utf-8`, `latin1`);
- Campos ausentes decorrentes de migrações estruturais de sistemas legados;
- Necessidade de conciliar transparência de dados públicos com **conformidade à LGPD**.

A solução foi concebida para simular a maturidade técnica exigida em ambientes de dados do setor público e corporativo: automação, rastreabilidade, tipagem estrita, banco de dados relacional em nuvem e atualização programada.

---

## 📐 Arquitetura da Solução

![Arquitetura da Solução](dashboard/imagens/arquitetura.svg)

<details>
<summary><b>Visualizar diagrama em formato de código Mermaid</b></summary>

```mermaid
flowchart TD
    API["Portal de Dados Abertos INSS<br/>(API CKAN Pública)"]
    SCRIPT_IN["download_sgp.py<br/>(Ingestão Incremental)"]
    RAW["Arquivos Brutos CSV<br/>(data/pgd_inss_AAAAMM.csv)"]
    SCRIPT_ETL["etl_sgp_inss.py<br/>(Limpeza, Tipagem e Ponte)"]
    SAMPLE["Amostra Sample 5k<br/>(sample.csv)"]
    NEON[("PostgreSQL Serverless<br/>Neon: tb_pgd_inss")]

    subgraph GH_ACTIONS ["Orquestração e CI/CD (GitHub Actions)"]
        CRON["Cron Mensal / Manual"]
        BOT["Commit Bot Automático"]
        HOOK["Webhook Trigger (cURL POST)"]
    end

    POWER_AUTO["Power Automate<br/>(Gatilho HTTP)"]
    PBI["Power BI Service / Desktop<br/>(Atualização Automática)"]
    DASH["Dashboard Executivo<br/>(Métricas DAX + LGPD)"]

    CRON --> API
    API -->|"Download Idempotente"| SCRIPT_IN
    SCRIPT_IN --> RAW
    RAW --> SCRIPT_ETL
    SCRIPT_ETL --> NEON
    SCRIPT_ETL --> SAMPLE
    SAMPLE -->|"Versionamento"| BOT
    NEON -->|"Carga Finalizada"| HOOK
    HOOK -->|"Requisição POST"| POWER_AUTO
    POWER_AUTO -->|"Refresh Dataset"| PBI
    NEON -.->|"Conexão Nativa SQL"| PBI
    PBI --> DASH
```

</details>

### Componentes da Arquitetura:

1. **Ingestão Automatizada via API (`download_sgp.py`)**:
   - Consome a API pública CKAN do portal oficial do INSS (`dadosabertos.inss.gov.br`).
   - Identifica novos meses publicados, extrai competências de forma determinística e padroniza a nomenclatura local dos arquivos (`pgd_inss_AAAAMM.csv`).
   - Operação idempotente: apenas arquivos inéditos são baixados, otimizando rede e tempo de execução.

2. **Pipeline de ETL e Higienização (`etl_sgp_inss.py`)**:
   - Tratamento de encodings variáveis (`utf-8` e `latin1`).
   - Mapeamento dinâmico de cabeçalhos (~30 variantes para 19 colunas canônicas).
   - Reconstrução de dados ausentes usando técnica de **ponte temporal determinística** entre meses adjacentes.
   - Enriquecimento cadastral de siglas e programas com validação em portarias normativas do INSS.
   - Geração de amostra estatística (`sample`) de 5.000 registros para versionamento auditável no Git.
   - Tipagem rigorosa com SQLAlchemy (`Date`, `DateTime`, `BigInteger`, `Text`) e normalização universal de valores nulos.

3. **Camada de Armazenamento (PostgreSQL no Neon Tech)**:
   - Armazenamento em nuvem serverless sob a tabela `tb_pgd_inss`.
   - Substituição transacional estruturada (`to_sql` com schema validado), garantindo prontidão para consultas analíticas complexas e consumo direto pelo Power BI.

4. **Orquestração e CI/CD (GitHub Actions — `database_sync.yml`)**:
   - Execução mensal automatizada via CRON (`0 9 1 * *`, no 1º dia de cada mês às 06:00 UTC-3) ou acionamento sob demanda (`workflow_dispatch`).
   - Execução sequencial da ingestão e do ETL em ambiente isolado (Python 3.12).
   - Versionamento automático de artefatos no repositório com usuário `github-actions[bot]`.

5. **Notificação e Atualização do BI (Power Automate & Power BI)**:
   - Disparo de Webhook via requisição HTTP POST autenticada para o **Power Automate**.
   - O fluxo do Power Automate aciona a atualização automática do modelo semântico do Power BI assim que a nova carga do banco é finalizada.
   - Implementação de camada de segurança e privacidade via DAX para mascaramento/anonimização de servidores (LGPD).

---

## 📂 Estrutura do Repositório

```text
├── .github/
│   └── workflows/
│       └── database_sync.yml                      # Orquestração CI/CD (cron, ETL, sync e webhook)
├── dashboard/
│   ├── Dash_INSS_Acompanhamento_PGD.pbix          # Relatório Power BI conectado ao PostgreSQL
│   ├── dashboard_README.md                        # Documentação dos componentes visuais e KPIs
│   ├── insights_README.md                         # Análise executiva de negócio e padrões temporais
│   └── imagens/                                   # Diretório com os recursos visuais e diagramas
│       ├── dashboard.png                          # Prévia visual atualizada do dashboard
│       ├── arquitetura.svg                        # Diagrama vetorial da arquitetura da solução
│       ├── evolucao_status.svg                    # Gráfico vetorial da evolução temporal por status
│       ├── tabela_total_designacoes.png           # Visão da tabela ordenada por volume de designações
│       └── tabela_designacoes_mes.png             # Visão da tabela ordenada por frequência mensal
├── data/                                          # Armazenamento local dos CSVs brutos (não versionados)
│   └── pgd_inss_*.csv
├── tratamento/
│   ├── download_sgp.py                            # Ingestor automatizado via API CKAN do INSS
│   ├── etl_sgp_inss.py                            # Pipeline completo de ETL e carga no Neon DB
│   └── pgd_designacoes_inss_2023_2026_sample.csv  # Amostra tratada (5.000 linhas) para consulta rápida
├── .env.example                                   # Modelo de variáveis de ambiente
├── requirements.txt                               # Dependências Python do projeto
├── LICENSE                                        # Licença do projeto (MIT)
└── README.md                                      # Documentação principal
```

---

## ⚙️ Decisões de Engenharia e Tratamento de Dados

Os dados públicos de origem apresentavam inconsistências de histórico: colunas com nomenclaturas diferentes entre anos (`Matricula`, `Matrícula`, `siape2`), meses inteiros sem identificadores estruturais e fusão de conceitos operacionais.

Todas as intervenções foram pautadas em validação empírica e rigor metodológico:

| Situação Encontrada | Decisão Técnica | Nível de Confiança / Justificativa |
| :--- | :--- | :--- |
| `regime` (2023) e `Modalidade` (2024+) representam o mesmo conceito sob nomes distintos | Campos unificados com recodificação semântica (`Integral` → `Remoto`, `Parcial` → `Semipresencial`) | **97,9%** de concordância validada em cruzamento de meses consecutivos |
| `sigla_programa` e `programa` possuem correspondência biunívoca quando preenchidos | Preenchimento bidirecional cruzado (`fillna`) complementado por dicionário de portarias normativas do INSS | **100%** determinístico |
| `id_designacao` e `dt_criacao_designacao` ausentes em meses específicos por falha de exportação original (ex: 03/2024 e 05/2024) | Reconstrução via **ponte temporal** entre meses vizinhos (preenchimento condicionado à estabilidade das demais chaves do servidor antes e depois) | **~96%**, com limitação residual documentada em campos sem estabilidade |
| `status` numérico (`1`, `2`) ou ausente | Mapeamento estruturado (`1` → `Designado`, `2` → `Desligado`) e inferência por intervalo de vigência (`dt_inicio` e `dt_fim` versus competência) | **100%** auditável por regras de negócio |
| `flag_pgd` com valores nulos | Preenchimento exclusivo para programas com enquadramento oficial comprovado nos dados e normativos; demais mantidos como `NaN` | Decisão conservadora para evitar falsos positivos regulatórios |
| `dt_alteracao_designacao`, `motivo_desligamento`, `id_lotacao` ausentes | Mantidos como valores nulos de banco (`NULL` / `None`) | Preservação da fidelidade do fato: ausência genuína de registro na fonte |
| Variabilidade de nomes de colunas e caracteres especiais | Normalização em *snake_case* e remoção de caracteres não alfanuméricos | Padronização para compatibilidade com ANSI SQL e PostgreSQL |

---

## 🗄️ Esquema do Banco de Dados (`tb_pgd_inss`)

A tabela final carregada no PostgreSQL via SQLAlchemy possui a seguinte estrutura de tipos:

| Coluna | Tipo SQL | Descrição |
| :--- | :--- | :--- |
| `competencia` | `DATE` | Data correspondente ao primeiro dia do mês de competência |
| `id_matricula` | `BIGINT` | Matrícula funcional unificada do servidor |
| `id_designacao` | `BIGINT` | Código identificador da designação no SGP |
| `id_lotacao` | `TEXT` | Código da unidade organizacional de lotação |
| `lotacao` | `TEXT` | Nome descritivo da unidade de lotação |
| `nome` | `TEXT` | Nome do profissional / servidor |
| `sigla_programa` | `TEXT` | Sigla do programa de gestão associado |
| `programa` | `TEXT` | Nome por extenso do programa de gestão |
| `sigla_linha_trabalho`| `TEXT` | Sigla da linha de trabalho executada |
| `linha_trabalho` | `TEXT` | Nome completo da linha de trabalho |
| `status` | `TEXT` | Situação funcional (`Designado`, `Desligado`, `Não Designado`) |
| `modalidade` | `TEXT` | Modalidade de trabalho (`Remoto`, `Semipresencial`, `Presencial`) |
| `flag_pgd` | `TEXT` | Indicador de adesão ao PGD (`Sim`, `Não`) |
| `tipo_entrega` | `TEXT` | Classificação do modelo de entrega |
| `motivo_desligamento` | `TEXT` | Motivação registrada do desligamento |
| `dt_inicio_designacao`| `TIMESTAMP`| Data e hora do início da vigência da designação |
| `dt_fim_designacao` | `TIMESTAMP`| Data e hora de encerramento da designação |
| `dt_criacao_designacao`| `TIMESTAMP`| Data e hora de criação do registro no sistema |
| `dt_alteracao_designacao`| `TIMESTAMP`| Data e hora da última alteração do registro |

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
- Python 3.12+
- Gerenciador de pacotes `pip`
- Acesso a uma instância PostgreSQL (ex: [Neon Tech](https://neon.tech/))

### 1. Clonar e Configurar o Ambiente

```bash
# Clonar o repositório
git clone https://github.com/gabrielcunha10/inss-pgd-data-pipeline.git
cd inss-pgd-data-pipeline

# Criar e ativar o ambiente virtual
python -m venv .venv

# No Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# No Linux / macOS / Git Bash:
source .venv/bin/activate

# Instalar as dependências
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Copie o arquivo de exemplo e preencha com a sua string de conexão:

```bash
cp .env.example .env
```

Edite o arquivo `.env`:
```env
DATABASE_URL=postgresql://usuario:senha@ep-exemplo.us-east-2.aws.neon.tech/neondb?sslmode=require
```

### 3. Executar o Pipeline Localmente

```bash
# 1. Ingestão automática: consulta a API do INSS e baixa os arquivos em data/
python tratamento/download_sgp.py

# 2. Processamento e Carga: limpa os dados e carrega na tabela tb_pgd_inss no Neon DB
python tratamento/etl_sgp_inss.py
```

---

## 🔄 Automação CI/CD no GitHub Actions

O fluxo de atualização contínua está configurado em [`.github/workflows/database_sync.yml`](file:///c:/Users/Ranie/OneDrive/Documents/sgp_inss/inss-pgd-data-pipeline/.github/workflows/database_sync.yml).

### Segredos Necessários no Repositório (Settings > Secrets and variables > Actions):
- `NEON_DATABASE_URL`: URL de conexão ao banco PostgreSQL do Neon.
- `POWER_AUTOMATE_WEBHOOK_URL`: URL do gatilho HTTP do fluxo no Power Automate.

### Ciclo de Execução:
1. Disparo agendado via Cron (`0 9 1 * *`) todo dia 1º de cada mês ou sob demanda pelo botão **Run workflow**;
2. Setup do ambiente Python 3.12 e instalação dos requisitos;
3. Execução de `download_sgp.py` (download das novas competências publicadas pelo INSS);
4. Execução de `etl_sgp_inss.py` (transformação e sincronização com o banco PostgreSQL);
5. Commit automático de artefatos e da amostra CSV atualizada com a mensagem `chore(data): atualiza amostra e artefatos [skip ci]`;
6. Disparo do Webhook para o Power Automate atualizar o relatório no Power BI Service.

---

## 📊 Visualização de Dados e Business Intelligence

O modelo analítico foi desenvolvido no **Power BI Desktop** e está armazenado no arquivo [`dashboard/Dash_INSS_Acompanhamento_PGD.pbix`](file:///c:/Users/Ranie/OneDrive/Documents/sgp_inss/inss-pgd-data-pipeline/dashboard/Dash_INSS_Acompanhamento_PGD.pbix).

![Preview do Dashboard](dashboard/imagens/dashboard.png)

> [!TIP]
> **Formas de Acesso:** O relatório pode ser aberto e explorado diretamente pelo arquivo [`dashboard/Dash_INSS_Acompanhamento_PGD.pbix`](file:///c:/Users/Ranie/OneDrive/Documents/sgp_inss/inss-pgd-data-pipeline/dashboard/Dash_INSS_Acompanhamento_PGD.pbix) (já conectado nativamente ao PostgreSQL Neon), ou manualmente via dataset do Kaggle. A publicação online pública no Power BI Service está em fase final de homologação (previsão até **22/09/2026** devido à liberação de licença na conta estudantil Microsoft). Consulte o [Guia do Dashboard](dashboard/dashboard_README.md) para detalhes.

### Principais Indicadores Monitorados:
- **45,40 Mil Designações:** Volume total acumulado de registros de designação no histórico monitorado.
- **22,13 Mil Matrículas Ativas:** Total da força de trabalho e servidores ativos mapeados no sistema.
- **15,75 Mil Média Mensal:** Volume médio de designações ativas mantidas a cada mês.
- **30 Programas Monitorados:** Diversidade de programas e modalidades de gestão cadastrados no PGD.
- **Retenção Temporal (Dias):** Tempo médio de permanência das designações no sistema por programa.
- **Detalhamento Anonimizado (LGPD):** Ranking por servidor identificado via código seguro (`USR-xxxxx`).
- **Sazonalidade e Curva de Status:** Identificação de picos operacionais (ex: março de 2025) e repactuação de teletrabalho.

Para mais detalhes sobre a modelagem e os achados de negócio, consulte a documentação específica:
- 📖 [Documentação Técnica do Dashboard](dashboard/dashboard_README.md)
- 💡 [Relatório de Insights e Análise Executiva](dashboard/insights_README.md)

---

## 🔒 Privacidade e Conformidade com a LGPD

Considerando que os dados de origem envolvem nomes e matrículas de servidores públicos, o projeto implementou salvaguardas de conformidade com a **Lei Geral de Proteção de Dados (Lei nº 13.709/2018)**:

1. **Anonimização em Nível de Modelo (DAX)**:
   - Criação de coluna calculada no modelo semântico do Power BI que mascara os identificadores nominais e substitui a identificação direta por códigos ou versões pseudonimizadas em relatórios compartilháveis.
2. **Dados Sensíveis Fora do Versionamento**:
   - Os arquivos brutos da pasta `data/` e arquivos `.env` são estritamente ignorados pelo `.gitignore`.
   - Apenas uma amostra (`sample`) estatisticamente reduzida (5.000 linhas) é versionada no repositório para permitir a validação da estrutura sem exposição desnecessária.

---

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologias |
| :--- | :--- |
| **Linguagem & Core** | Python 3.12, Pandas, NumPy, Requests, Pathlib |
| **Engenharia de Banco de Dados** | PostgreSQL, SQLAlchemy, Psycopg2, Neon Tech (Serverless DB) |
| **Orquestração & CI/CD** | GitHub Actions, Git, Cron Scheduling |
| **Integração & Webhooks** | cURL, Microsoft Power Automate |
| **Business Intelligence & Analytics** | Microsoft Power BI Desktop & Service, DAX |
| **Governança & Qualidade** | Conformidade LGPD, Type Casting Estrito, Tratamento de Nulos |

---

## 📄 Licença

Este projeto está sob a licença [MIT](LICENSE).
