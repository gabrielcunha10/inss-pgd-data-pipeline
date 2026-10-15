# Pipeline de Dados e Analytics — Programa de Gestão de Desempenho (PGD) INSS

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL Neon](<https://img.shields.io/badge/Database-PostgreSQL%20(Neon)-4169E1?logo=postgresql&logoColor=white>)](https://neon.tech/)
[![GitHub Actions](<https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white>)](https://github.com/features/actions)
[![Power BI](<https://img.shields.io/badge/Dashboard-Power%20BI-F2C811?logo=power-bi&logoColor=black>)](https://powerbi.microsoft.com/)
[![Power Automate](<https://img.shields.io/badge/Automation-Power%20Automate-0066FF?logo=power-automate&logoColor=white>)](https://powerautomate.microsoft.com/)
[![Pytest](https://img.shields.io/badge/QA-Pytest-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org/)
[![LGPD](<https://img.shields.io/badge/Compliance-LGPD%20Anonymized-008080>)](#privacidade-e-conformidade-com-a-lgpd)

**[Acessar o Dashboard Online no Power BI (Link Público)](https://app.powerbi.com/view?r=eyJrIjoiMjNlNzBmOWQtMzVlNC00MjBhLTk0MDEtYTBhZThiZWYyNTAwIiwidCI6IjhjODgwZTJhLTM2MDAtNDVmZi1hZDM5LWJhMDRlZGM4MWYyNSJ9&pageName=bcd18bc650e27d173dae)**

Pipeline de Engenharia de Dados e Analytics ponta a ponta que automatiza a ingestão contínua de dados abertos do governo federal via API pública, executa limpeza, enriquecimento e padronização com Python/Pandas, carrega a base consolidada em um banco relacional em nuvem (**PostgreSQL no Neon Tech**) e mantém um dashboard interativo no **Power BI** atualizado de forma autônoma via **GitHub Actions** e **Power Automate**.

Neste projeto, eu analiso o histórico do **Programa de Gestão e Desempenho (PGD)** aplicado ao quadro de atendimento do INSS (ACSINSS), cobrindo de **outubro/2023 em diante** (mais de 500 mil registros consolidados).

---

## Contexto e Motivação

### Da Preparação para a Dataprev ao Desafio Público

Desenvolvi este projeto como peça central de portfólio em Engenharia e Análise de Dados, inspirado pelo processo seletivo de estágio da **Dataprev** (Empresa de Tecnologia e Informações da Previdência). Durante a preparação e aprofundamento sobre a atuação da empresa pública — responsável pelo processamento mensal da folha de pagamento de mais de 39 milhões de benefícios previdenciários e assistenciais (*Fonte: Dataprev / Secretaria de Regime Geral de Previdência Social - MPS*) —, passei a pesquisar intensamente sobre o ecossistema da previdência social e me deparei com um dos temas mais críticos da administração pública brasileira: o **gargalo operacional e as filas de espera do INSS**.

### O Cenário Real: O Desafio Estrutural das Filas do INSS

A fila de requerimentos represados no Instituto Nacional do Seguro Social é um desafio histórico e multifatorial com impacto direto na vida de milhões de cidadãos que aguardam a concessão de aposentadorias, pensões, auxílios e Benefício de Prestação Continuada (BPC):

1. **Volume Expressivo da Demanda Acumulada**:

   - O estoque nacional de requerimentos em análise administrativa tem oscilado historicamente na faixa de **1,3 milhão a 1,8 milhão de pedidos represados** (*Fontes: Ministério da Previdência Social — Portal da Transparência Previdenciária e Tribunal de Contas da União - TCU, Processo TC 011.026/2023-0*).
   - O Tempo Médio de Concessão (TMC) frequentemente alcançou **60 a 85 dias** em períodos de sobrecarga, superando o prazo regulamentar pactuado (*Fontes: Boletim Estatístico da Previdência Social - BEPS/MPS e Acordo homologado pelo Supremo Tribunal Federal no RE 1.171.152/SC - Tema 1.066, que fixou meta de 45 dias para a conclusão de processos administrativos*).
2. **Déficit Histórico da Força de Trabalho**:

   - O corpo funcional efetivo do INSS, que ultrapassava 33 mil servidores em 2016, sofreu redução contínua em razão de aposentadorias em massa sem reposição proporcional, recuando para a faixa de **19 mil a 22 mil servidores ativos** (*Fontes: Painel Estatístico de Pessoal - PEP/MGI e Relatórios de Fiscalização de Pessoal do TCU*).
3. **O PGD como Resposta Estratégica Institucional**:

   - Diante da impossibilidade de recomposição imediata do quadro físico, o governo federal regulamentou o **Programa de Gestão e Desempenho (PGD)** (disciplinado pelas Instruções Normativas SGP/SEDGG/ME nº 65/2020 e SGP/MGI nº 24/2023, bem como pela Portaria PRES/INSS nº 1.488/2022).
   - O PGD estabeleceu uma mudança de paradigma: a transição do controle tradicional de ponto por horas presenciais para uma gestão orientada estritamente a **metas, entregas e resultados mensuráveis**, estipulando inclusive meta de produtividade até 30% superior para servidores em teletrabalho integral em relação à modalidade presencial (*Fonte: Art. 12, § 1º da IN SGP/ME nº 65/2020 e Portaria INSS nº 1.488/2022*).
   - Nesse contexto, a alocação de servidores nas **Centrais de Análise de Benefícios (CEABs)** — estrutura que lidera a volumetria analisada neste repositório — representa a frente de trabalho prioritária do Estado para acelerar a análise de processos e reduzir o represamento.

### O Desafio Técnico na Engenharia de Dados

Para responder com transparência e precisão se essa política pública de pactuação de metas está sendo cumprida, onde os servidores estão alocados e como o teletrabalho se distribui geograficamente, é imperativo que os dados sejam contínuos, auditáveis e confiáveis. Contudo, trabalhar com os microdados abertos do governo impõe barreiras severas de engenharia:

- **Instabilidade de Esquemas**: Mudanças frequentes de layout ao longo dos anos nas extrações do Sistema de Gestão de Pessoas (SGP), totalizando cerca de 30 variantes de cabeçalhos que exigem mapeamento canônico dinâmico;
- **Heterogeneidade de Encodings**: Arquivos mensais alternando entre codificações `utf-8` e `latin1`, gerando potenciais quebras de caracteres acentuados;
- **Descontinuidade Temporal e Nulos**: Lacunas cadastrais geradas por migrações sistêmicas em anos anteriores, resolvidas neste pipeline pela modelagem de **pontes temporais determinísticas** entre competências adjacentes;
- **Privacidade Rigorosa (LGPD)**: Imperativo legal de anonimizar dados pessoais sensíveis (nomes e matrículas) através de criptografia irreversível por chave secreta (**HMAC-SHA256**) antes que qualquer dado transite para a nuvem.

Projetei esta solução para conectar essas duas pontas: a complexidade real da gestão pública e a maturidade da engenharia de dados moderna (automação via GitHub Actions, banco em nuvem PostgreSQL Serverless no Neon Tech, testes rigorosos com Pytest e monitoramento visual no Power BI).

---

## Arquitetura da Solução

![Arquitetura da Solução](dashboard/imagens/arquitetura.svg)

<details>
<summary><b>Visualizar diagrama em formato de código Mermaid</b></summary>

```mermaid
flowchart TD
    subgraph WF1 ["Workflow 1: Pipeline Principal (database_sync.yml — Mensalmente, todo dia 01 às 06:00 BRT)"]
        API["Portal de Dados Abertos INSS<br/>(API CKAN Pública)"]
        SCRIPT_IN["download_sgp.py<br/>(Ingestão Incremental)"]
        SCRIPT_ETL["etl_sgp_inss.py<br/>(Tratamento, Pontes & Parquet)"]
        LGPD["Anonimização LGPD<br/>(HMAC-SHA256)"]
        TESTS_DATA["test_pipeline.py<br/>(13 Testes de Integridade)"]
        SCRIPT_LOAD["load_neon.py<br/>(Carga em Lotes)"]
        NEON[("PostgreSQL Serverless<br/>Neon: tb_pgd_inss")]
        INSIGHTS["gerar_insights.py<br/>(Google Gemini IA + Métricas MoM)"]
        HOOK["Webhook Trigger<br/>(cURL POST)"]
        POWER_AUTO["Power Automate<br/>(Gatilho HTTP)"]
        PBI["Power BI Service<br/>(Painel Executivo)"]

        API --> SCRIPT_IN --> SCRIPT_ETL --> LGPD --> TESTS_DATA
        TESTS_DATA -->|"Aprovação"| SCRIPT_LOAD --> NEON
        NEON --> INSIGHTS
        NEON -->|"Conexão Nativa SQL"| PBI
        NEON --> HOOK --> POWER_AUTO -->|"Refresh Dataset"| PBI
    end

    subgraph WF2 ["Workflow 2: Prints do Dashboard & Documentação (atualizar_documentacao_prints.yml — Mensalmente, todo dia 01 às 07:30 BRT)"]
        PRINTS["capturar_prints.py<br/>(Prints das 8 Telas do Dashboard Power BI)"]
        TESTS_DOCS["test_documentacao_insights.py<br/>(8 Testes de QA)"]
        DOCS["Publicação de Artefatos & Markdown<br/>(dashboard_README.md & imagens)"]

        PBI -->|"+1h30 (Aguarda Refresh do Power BI)"| PRINTS
        PRINTS --> TESTS_DOCS
        TESTS_DOCS -->|"Aprovação"| DOCS
    end
```

</details>

### Componentes da Arquitetura

A solução é orquestrada por dois workflows desacoplados e complementares no GitHub Actions, garantindo que o ciclo principal de engenharia de dados seja blindado contra eventuais instabilidades de renderização visual ou de interfaces web:

#### Workflow 1: Pipeline Principal (`database_sync.yml` — Mensalmente, todo dia 01 às 06:00 BRT)

1. **Fonte de Dados (API de Dados Abertos do INSS)**:

   - Consome a API pública CKAN do portal oficial (`dadosabertos.inss.gov.br`).
   - Cobertura da série histórica de designações do PGD (2023–2026), identificando e baixando de forma incremental apenas arquivos mensais inéditos (`pgd_inss_AAAAMM.csv`).
2. **Ingestão Automatizada (`download_sgp.py`)**:

   - Rotina em Python com requisições resilientes (timeout, retries e validação de cabeçalhos HTTP).
   - Extração determinística de competências e padronização da nomenclatura local dos arquivos na pasta `data/`.
3. **Pipeline de ETL e Enriquecimento (`etl_sgp_inss.py`)**:

   - Tratamento de múltiplos encodings (`utf-8` e `latin1`).
   - Mapeamento dinâmico de mais de 30 variantes de cabeçalhos do SGP para 19 colunas canônicas tipadas.
   - Reconstrução de dados ausentes e saneamento de histórico através de **pontes temporais determinísticas** entre competências adjacentes.
   - Enriquecimento cadastral de siglas e linhas de trabalho fundamentado em portarias normativas do INSS.
   - Geração da base consolidada e tipada em formato colunar `.parquet` para validação de integridade.
4. **Anonimização Criptográfica LGPD (HMAC-SHA256)**:

   - Criptografia irreversível de mão única aplicada às matrículas e identificadores dos servidores com salt privado (`HMAC_SECRET_KEY`).
   - Geração de pseudônimos seguros (`USR-XXXXXXXX`), impedindo o tráfego ou armazenamento de dados pessoais identificáveis (PII) no banco em nuvem e nos dashboards públicos.
5. **Qualidade de Dados e Guardião do Banco (`test_pipeline.py`)**:

   - Execução de malha fina via `pytest` com 13 testes automatizados cobrindo tipagem estrita, consistência temporal, não nulidade, regras de negócio e validação da máscara LGPD.
   - Atuação no padrão *Write-Audit-Publish (WAP)*: a carga no banco de dados só é autorizada se 100% dos testes forem aprovados.
6. **Carga Transacional e Armazenamento em Nuvem (`load_neon.py` e PostgreSQL Neon)**:

   - Carga transacional em lotes (`chunksize=10.000`) na tabela `tb_pgd_inss` no PostgreSQL Serverless da Neon Tech.
   - Operação idempotente por partição de competência (`Delete & Insert`), garantindo zero duplicidades, integridade de índices e nenhuma indisponibilidade (*zero downtime*) para consultas analíticas.
   - Geração de amostra versionada (`sample.csv` com 5.000 linhas) para auditoria rápida no repositório.
7. **Geração de Insights Executivos com IA (`gerar_insights.py`)**:

   - Processamento estatístico comparativo mês a mês (Month-over-Month - MoM) e diagnóstico dos 6 eixos de gestão.
   - Integração com a API do Google Gemini (com fallback automático para motor analítico local em Python), gerando relatório executivo autônomo.
   - Arquivamento histórico automático das versões mensais na pasta `dashboard/relatorios/` (`insights_AAAA_MM.md`) antes da substituição do relatório vigente (`insights_README.md`).
8. **Visualização Executiva e Disparo de Atualização (Power Automate & Power BI Service)**:

   - Disparo de Webhook via requisição HTTP POST para o **Power Automate**, que aciona o gatilho de atualização assíncrona do modelo semântico no **Power BI Service**.
   - Painel executivo interativo composto por 8 telas analíticas conectadas nativamente ao banco relacional Neon.

---

#### Intervalo de Sincronização (+1h30 de Margem Operacional)

- O intervalo programado de 1 hora e 30 minutos entre os workflows permite que o fluxo do Power Automate processe a solicitação e o Power BI Service conclua o processamento (*dataset refresh*) em nuvem, garantindo que os novos dados já estejam integralmente renderizados no painel online antes da execução do Workflow 2.

---

#### Workflow 2: Prints do Dashboard & Documentação (`atualizar_documentacao_prints.yml` — Mensalmente, todo dia 01 às 07:30 BRT)

1. **Captura Automatizada das Telas do Dashboard (`capturar_prints.py`)**:

   - Automação headless via **Playwright** que navega pelo relatório público do Power BI Service, estabiliza os seletores visuais e captura as 8 telas analíticas em alta resolução na pasta `dashboard/imagens/`.
   - Mecanismo de auto-recuperação com validação de hash criptográfico SHA-256 e até 3 tentativas de retry, prevenindo telas duplicadas ou capturas incompletas.
2. **Testes de Qualidade de Documentação & QA (`test_documentacao_insights.py`)**:

   - Suíte isolada de 11 testes automatizados via `pytest` que verifica a integridade binária dos prints (cabeçalho mágico PNG, tamanho mínimo e unicidade visual por SHA-256).
   - Validação da integridade de todos os links de imagens nos arquivos Markdown e consistência dos relatórios históricos arquivados em `dashboard/relatorios/`.
3. **Orquestração de Documentação (GitHub Actions)**:

   - Execução isolada em container Ubuntu com setup de navegadores Playwright.
   - Desacoplamento arquitetural: eventuais instabilidades na renderização visual do Power BI jamais travam a sincronização da base de dados no Neon nem interrompem o pipeline principal.
4. **Publicação Contínua de Artefatos no Git (`dashboard_README.md`, `README.md` e `dashboard/relatorios/`)**:

   - Commit automatizado das capturas visuais atualizadas e dos relatórios analíticos, mantendo a documentação do repositório sempre fiel e demonstrando a evolução viva do projeto.

---

## Estrutura do Repositório

```text
├── .github/
│   └── workflows/
│       ├── database_sync.yml                      # Workflow 1: Ingestão, ETL, carga no Neon, insights e webhook
│       └── atualizar_documentacao_prints.yml      # Workflow 2: Automação Playwright, QA e publicação de prints
├── dashboard/
│   ├── Dash_INSS_Acompanhamento_PGD.pbix          # Relatório Power BI conectado nativamente ao PostgreSQL Neon
│   ├── capturar_prints.py                         # Automação Playwright para captura de prints das 8 telas
│   ├── dashboard_README.md                        # Documentação detalhada das 8 telas analíticas e catálogo de KPIs
│   ├── insights_README.md                         # Relatório executivo de negócio e padrões temporais (versão vigente)
│   ├── relatorios/                                # Histórico mensal dos relatórios de insights (projeto vivo)
│   │   └── insights_AAAA_MM.md                    # Versões mensais arquivadas automaticamente a cada ciclo
│   └── imagens/                                   # Recursos visuais, diagramas e capturas do painel (8 telas)
│       ├── arquitetura.svg                        # Diagrama vetorial da arquitetura da solução
│       ├── arquitetura_pipeline_completa.png      # Diagrama visual consolidado dos workflows
│       ├── menu_inicial.png                       # Prévia visual da tela inicial de navegação
│       ├── visao_geral_dashboard.png              # Painel de evolução histórica e KPIs
│       ├── modalidades_dashboard.png              # Painel de análise por modalidade de trabalho
│       ├── programas_dashboard.png                # Painel de análise por programas de gestão
│       ├── linhas_trabalho_dashboard.png          # Painel de análise por linhas de trabalho
│       ├── lotacoes_dashboard.png                 # Painel de análise por unidades de lotação
│       ├── informacoes_projeto.png                # Painel de regras de negócio e governança
│       └── lgpd_dashboard.png                     # Painel de privacidade e conformidade LGPD
├── data/                                          # Armazenamento local dos CSVs brutos (não versionados)
│   └── pgd_inss_*.csv                             # Arquivos mensais baixados da API CKAN do INSS
├── tests/                                         # Testes automatizados e base tratada de saída
│   ├── pgd_designacoes_inss_2023_2026.parquet     # Base tratada consolidada após o ETL (não versionado)
│   ├── test_pipeline.py                           # Suíte de 13 testes de engenharia, tipagem e regras de negócio
│   └── test_documentacao_insights.py              # Suíte de 11 testes de QA de documentação, relatórios e prints
├── tratamento/
│   ├── download_sgp.py                            # Ingestor automatizado via API CKAN pública do INSS
│   ├── etl_sgp_inss.py                            # Transformação de dados, pontes temporais e anonimização LGPD
│   ├── gerar_insights.py                          # Geração autônoma de insights (Gemini/local) e arquivamento mensal
│   ├── load_neon.py                               # Script isolado para carga idempotente no PostgreSQL Neon
│   └── pgd_designacoes_inss_2023_2026_sample.csv  # Amostra tratada (5.000 linhas) para consulta e auditoria
├── Dockerfile                                     # Configuração de container para execução isolada do pipeline
├── docker-compose.yml                             # Orquestração de serviços do ambiente containerizado
├── run_pipeline.sh                                # Script utilitário em shell para execução local do pipeline
├── .env.example                                   # Modelo de variáveis de ambiente
├── requirements.txt                               # Dependências Python do projeto
├── LICENSE                                        # Licença do projeto (MIT)
└── README.md                                      # Documentação principal da solução
```

---

## Decisões de Engenharia e Tratamento de Dados

Os dados públicos de origem apresentavam inconsistências de histórico: colunas com nomenclaturas diferentes entre anos (`Matricula`, `Matrícula`, `siape2`), meses inteiros sem identificadores estruturais e fusão de conceitos operacionais.

Todas as minhas decisões e intervenções de dados foram pautadas em validação empírica e rigor metodológico:

| Situação Encontrada                                                                                                                   | Decisão Técnica                                                                                                                                                 | Nível de Confiança / Justificativa                                            |
| :-------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------ |
| `regime` (2023) e `Modalidade` (2024+) representam o mesmo conceito sob nomes distintos                                             | Campos unificados com recodificação semântica (`Integral` → `Remoto`, `Parcial` → `Semipresencial`)                                                  | **97,9%** de concordância validada em cruzamento de meses consecutivos   |
| `sigla_programa` e `programa` possuem correspondência biunívoca quando preenchidos                                                | Preenchimento bidirecional cruzado (`fillna`) complementado por dicionário de portarias normativas do INSS                                                     | **100%** determinístico                                                  |
| `id_designacao` e `dt_criacao_designacao` ausentes em meses específicos por falha de exportação original (ex: 03/2024 e 05/2024) | Reconstrução via **ponte temporal** entre meses vizinhos (preenchimento condicionado à estabilidade das demais chaves do servidor antes e depois)       | **~96%**, com limitação residual documentada em campos sem estabilidade |
| `status` numérico (`1`, `2`) ou ausente                                                                                          | Mapeamento estruturado (`1` → `Designado`, `2` → `Desligado`) e inferência por intervalo de vigência (`dt_inicio` e `dt_fim` versus competência) | **100%** auditável por regras de negócio                                |
| `flag_pgd` com valores nulos                                                                                                          | Preenchimento exclusivo para programas com enquadramento oficial comprovado nos dados e normativos; demais mantidos como`NaN`                                   | Decisão conservadora para evitar falsos positivos regulatórios                |
| `dt_alteracao_designacao`, `motivo_desligamento`, `id_lotacao` ausentes                                                           | Mantidos como valores nulos de banco (`NULL` / `None`)                                                                                                        | Preservação da fidelidade do fato: ausência genuína de registro na fonte    |
| Variabilidade de nomes de colunas e caracteres especiais                                                                                | Normalização em *snake_case* e remoção de caracteres não alfanuméricos                                                                                   | Padronização para compatibilidade com ANSI SQL e PostgreSQL                   |

---

## Esquema do Banco de Dados (`tb_pgd_inss`)

A tabela consolidada `tb_pgd_inss` no PostgreSQL Serverless (Neon Tech) é alimentada diretamente a partir do arquivo colunar otimizado [`tests/pgd_designacoes_inss_2023_2026.parquet`](tests/pgd_designacoes_inss_2023_2026.parquet) via SQLAlchemy (`load_neon.py`), contendo **20 colunas canônicas padronizadas, tipadas e auditadas**.

Abaixo está o dicionário de dados detalhado, refletindo fielmente a ordem física, os tipos de dados no Parquet/Pandas, os tipos relacionais no PostgreSQL (Neon), o status de nulidade e a semântica de negócio de cada atributo:

| Coluna | Tipo SQL (Neon) | Tipo Parquet | Nullable | Descrição e Regras de Negócio |
| :--- | :--- | :--- | :---: | :--- |
| `id_usuario` | `TEXT` | `string` | Não | Identificador pseudonimizado do servidor público via hash criptográfico irreversível (HMAC-SHA256 com chave privada), mascarado no formato `USR-XXXXXXXX` (8 caracteres hexadecimais) em conformidade rigorosa com a LGPD. |
| `sigla_programa` | `TEXT` | `string` | Sim | Sigla identificadora do programa de gestão e desempenho cadastrado no SGP (ex: `CEAP`, `CEAB1`, `PG-DIRBEN`, `ATENDIMENTO`). Nulo apenas para servidores sem designação ativa. |
| `modalidade` | `TEXT` | `string` | Sim | Modalidade de execução do trabalho regulamentada pelo PGD, padronizada canonicamente nos domínios `Remoto`, `Semipresencial` ou `Presencial`. |
| `status` | `TEXT` | `string` | Não | Situação cadastral do servidor em relação ao PGD na competência, classificada estritamente em `Designado`, `Desligado` ou `Não Designado`. |
| `dt_inicio_designacao` | `TIMESTAMP` | `datetime64[ns]` | Sim | Data e hora do início da vigência da designação ou plano de trabalho pactuado. |
| `dt_fim_designacao` | `TIMESTAMP` | `datetime64[ns]` | Sim | Data e hora de encerramento da designação. Preenchimento esparso (nulo em vínculos com vigência aberta ou prazo indeterminado). |
| `competencia` | `DATE` | `datetime64[ns]` | Não | Primeiro dia do mês de referência dos dados (série histórica de `2023-10-01` a `2026-08-01`). Atua como partição temporal de carga e garantia de idempotência (`DELETE & INSERT`). |
| `id_designacao` | `BIGINT` | `Int64` | Sim | Código identificador numérico único do ato de designação gerado pelo Sistema de Gestão de Pessoas (SGP). |
| `dt_criacao_designacao` | `TIMESTAMP` | `datetime64[ns]` | Sim | Carimbo de data/hora do momento em que o registro de designação foi cadastrado no sistema de origem. |
| `dt_alteracao_designacao` | `TIMESTAMP` | `datetime64[ns]` | Sim | Carimbo de data/hora da última alteração, renovação ou repactuação cadastrada para a designação. |
| `linha_trabalho` | `TEXT` | `string` | Não | Nome descritivo por extenso da linha de atuação institucional (ex: `Central de Análise de Benefícios de Reconhecimento de Direitos SRNE`). |
| `sigla_linha_trabalho` | `TEXT` | `string` | Não | Sigla canônica correspondente à linha de trabalho (ex: `CEABRD_SR_NE`, `CEABMAN_SRNE`, `APS_SRNCO`), padronizada via de-para determinístico. |
| `tipo_entrega` | `TEXT` | `string` | Não | Modelo de pactuação de resultados aplicável à designação (`Meta`, `Jornada e Meta`, `Produto` ou `Jornada`). |
| `motivo_desligamento` | `TEXT` | `string` | Sim | Motivação administrativa registrada para o término da designação (ex: `Necessidade do serviço`, `A pedido`, `Aposentadoria`). Preenchido exclusivamente em casos de rescisão. |
| `lotacao` | `TEXT` | `string` | Não | Descrição textual padronizada da unidade de lotação física ou administrativa do servidor (ex: agências `APS`, gerências `GEX` e superintendências `SR`). |
| `programa` | `TEXT` | `string` | Sim | Nome por extenso do programa de gestão e desempenho associado à designação (ex: `CENTRAL ESPECIALIZADA DE ALTA PERFORMANCE`). |
| `flag_pgd` | `TEXT` | `string` | Sim | Indicador binário (`Sim` / `Não`) atestando se a designação está formalmente enquadrada nas diretrizes normativas do PGD (IN 65/2020 e IN 24/2023). |
| `id_lotacao` | `TEXT` | `string` | Não | Código estrutural identificador da unidade organizacional / UPAG no sistema de gestão de pessoas (SIAPE). |
| `filtro_programa` | `TEXT` | `string` | Sim | Campo composto gerado no ETL (`sigla_programa - programa`) para enriquecer segmentações visuais, seletores analíticos e hierarquias no Power BI. |
| `filtro_linha_trabalho` | `TEXT` | `string` | Não | Campo composto gerado no ETL (`sigla_linha_trabalho - linha_trabalho`) para otimizar pesquisas e filtros cruzados nas telas do dashboard. |

---

## Testes e Qualidade de Dados (Pytest)

Para garantir a confiabilidade, a integridade das cargas contínuas e a fidelidade da documentação visual, estruturei duas suítes de testes automatizados com **`pytest`**, totalizando **24 testes unitários e de integração**:

1. **Testes de Engenharia e Integridade de Dados ([`tests/test_pipeline.py`](tests/test_pipeline.py) — 13 testes):**

   - Atuam como guardião do banco de dados no padrão *Write-Audit-Publish (WAP)*: a carga no PostgreSQL só ocorre se 100% dos testes forem aprovados.
   - **Integridade de Siglas e Nomes:** Verifica a ausência de registros órfãos entre siglas e nomes de programas e linhas de trabalho.
   - **Consistência Temporal:** Garante que nenhuma data de fim (`dt_fim_designacao`) seja anterior à data de início (`dt_inicio_designacao`).
   - **Validação de Nulos Críticos:** Impede que chaves primárias e colunas essenciais para regras de negócio (como a `modalidade` em casos de status "Designado") fiquem vazias.
   - **Checagem de Domínios Restritos:** Assegura que colunas categóricas (`status`, `modalidade`, `flag_pgd`) contenham apenas os domínios normatizados.
   - **Unicidade e Deduplicação:** Analisa chaves compostas (`id_usuario` + `competencia` + `id_designacao`) para barrar duplicações de registros transacionais.
   - **Auditoria de Máscara LGPD:** Confere via *Regex* se todos os usuários da base foram devidamente anonimizados no padrão rigoroso `USR-XXXXXXXX`.
2. **Testes de QA de Documentação e Artefatos ([`tests/test_documentacao_insights.py`](tests/test_documentacao_insights.py) — 11 testes):**

   - **Integridade Binária dos Prints:** Valida cabeçalho mágico PNG (`\x89PNG\r\n\x1a\n`), tamanho mínimo e resolução das 8 telas capturadas.
   - **Unicidade Visual por Hash SHA-256:** Assegura que cada tela capturada possui hash criptográfico único, prevenindo falhas de navegação e prints duplicados.
   - **Links e Referências de Imagens:** Percorre todos os arquivos Markdown (`dashboard_README.md`, `insights_README.md` e relatórios arquivados) certificando que todas as imagens apontadas existem no disco.
   - **Motor de Insights e Arquivamento:** Testa o cálculo matemático Month-over-Month (MoM), extração de competências e o versionamento histórico de relatórios em `dashboard/relatorios/`.

---

## Como Executar o Projeto

### Pré-requisitos

- Python 3.12+ (para execução local manual)
- Docker e Docker Compose (para execução em container)
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

Copie o arquivo de exemplo e crie o seu `.env`:

```bash
cp .env.example .env
```

Configure as variáveis no `.env` (para execução local) ou cadastre-as em **Settings > Secrets and variables > Actions** do repositório no GitHub (para os workflows automatizados):

```env
# 1. Conexão com o PostgreSQL Neon (OBRIGATÓRIA para carga no banco)
# No GitHub Actions: configure como secret 'NEON_DATABASE_URL'
DATABASE_URL=postgresql://usuario:senha@ep-exemplo.us-east-2.aws.neon.tech/neondb?sslmode=require

# 2. Chave da API do Google Gemini (OPCIONAL)
# No GitHub Actions: configure como secret 'GEMINI_API_KEY'
# Caso ausente, o script 'gerar_insights.py' ativa automaticamente o motor analítico local em Python
GEMINI_API_KEY=sua_chave_do_google_ai_studio_aqui

# 3. Webhook do Power Automate para Atualização do Power BI (OPCIONAL)
# No GitHub Actions: configure como secret 'POWER_AUTOMATE_WEBHOOK_URL'
# Necessária apenas se desejar disparar o refresh automático do dataset no Power BI Service
POWER_AUTOMATE_WEBHOOK_URL=https://prod-xx.brazilsouth.logic.azure.com:443/workflows/...
```

> [!NOTE]
> **Detalhamento das Variáveis:**
> - `DATABASE_URL` (ou `NEON_DATABASE_URL` no GitHub): **Obrigatória** para a sincronização relacional da tabela `tb_pgd_inss` via [`tratamento/load_neon.py`](tratamento/load_neon.py).
> - `GEMINI_API_KEY`: **Opcional**. Quando fornecida, habilita o Google Gemini para redigir o diagnóstico executivo. Se não informada, o script [`tratamento/gerar_insights.py`](tratamento/gerar_insights.py) ativa automaticamente o motor analítico determinístico local, gerando o relatório Markdown sem qualquer dependência externa ou interrupção.
> - `POWER_AUTOMATE_WEBHOOK_URL`: **Opcional**. Utilizada para enviar o gatilho HTTP cURL POST ao Power Automate para refresh no Power BI Service. Na execução local, pode ser omitida.

### 3. Executar o Pipeline

Você pode rodar o pipeline de duas formas: usando Docker (recomendado) ou executando os scripts Python diretamente na sua máquina.

#### Opção A: Executar via Docker (Recomendado)

Esta é a forma mais simples e isolada, pois resolve automaticamente as dependências e orquestra a execução via `run_pipeline.sh`:

```bash
docker-compose up --build
```

O container executará todo o fluxo em ordem: ingestão, tratamento (ETL), testes automatizados (pytest) e carga no banco de dados.

#### Opção B: Executar Manualmente (Local)

Se preferir rodar passo a passo:

```bash
# 1. Ingestão automática: consulta a API do INSS e baixa os arquivos em data/
python tratamento/download_sgp.py

# 2. Processamento (ETL): limpa os dados e gera o arquivo Parquet e o CSV sample
python tratamento/etl_sgp_inss.py

# 3. Qualidade de Dados: roda a suíte com os 24 testes automatizados (Pytest)
pytest tests/

# 4. Carga no Banco (Load): insere os dados validados na tabela tb_pgd_inss no Neon DB
python tratamento/load_neon.py

# 5. Geração de Insights (Opcional): arquiva a versão anterior e gera relatório executivo
python tratamento/gerar_insights.py

# 6. Captura de Prints (Opcional): executa o Playwright headless para capturar as 8 telas
python dashboard/capturar_prints.py
```

---

## Automação CI/CD no GitHub Actions

A automação da solução é estruturada em dois workflows independentes e agendados no GitHub Actions:

### Workflow 1: Pipeline Principal de Dados ([`.github/workflows/database_sync.yml`](.github/workflows/database_sync.yml))

- **Agendamento:** Todo dia 01 de cada mês às 06:00 BRT (`0 9 1 * *`) ou sob demanda (**workflow_dispatch**).
- **Segredos no Repositório (Settings > Secrets and variables > Actions):**
  - `NEON_DATABASE_URL`: String de conexão ao PostgreSQL Serverless do Neon Tech.
  - `POWER_AUTOMATE_WEBHOOK_URL`: URL do gatilho HTTP do fluxo no Power Automate.
  - `GEMINI_API_KEY`: Chave de API do Google Gemini para geração autônoma de insights (com fallback local automático se ausente).
- **Ciclo de Execução:**
  1. Setup do ambiente Python 3.12 e instalação dos requisitos;
  2. Execução de `download_sgp.py` (download incremental das novas competências publicadas pelo INSS);
  3. Execução de `etl_sgp_inss.py` (saneamento, pontes temporais, mascaramento LGPD e geração do Parquet);
  4. Execução dos testes automatizados via `pytest tests/test_pipeline.py` (guardião do banco no padrão WAP);
  5. Execução de `load_neon.py` (carga transacional idempotente por partição no banco PostgreSQL);
  6. Execução de `gerar_insights.py` (arquivamento do relatório anterior e geração de novos insights executivos);
  7. Commit automático dos artefatos atualizados com `[skip ci]`;
  8. Disparo de Webhook via cURL POST para o Power Automate iniciar a atualização assíncrona do Power BI Service.

---

### Workflow 2: Prints do Dashboard & Documentação ([`.github/workflows/atualizar_documentacao_prints.yml`](.github/workflows/atualizar_documentacao_prints.yml))

- **Agendamento:** Todo dia 01 de cada mês às 07:30 BRT (`30 10 1 * *` — intervalo de +1h30 para conclusão do refresh no Power BI Service) ou sob demanda.
- **Ciclo de Execução:**
  1. Setup do ambiente Python 3.12 e instalação do Chromium headless via Playwright;
  2. Execução de `dashboard/capturar_prints.py` (captura automatizada das 8 telas do relatório online);
  3. Execução da suíte de QA via `pytest tests/test_documentacao_insights.py` (validação de hash SHA-256 e integridade de links);
  4. Commit automatizado dos novos prints na pasta `dashboard/imagens/`, mantendo a documentação viva e auditável.

---

## Visualização de Dados e Business Intelligence

Desenvolvi todo o modelo analítico no **Power BI Desktop** e está armazenado no arquivo [`dashboard/Dash_INSS_Acompanhamento_PGD.pbix`](dashboard/Dash_INSS_Acompanhamento_PGD.pbix).

![Preview do Dashboard](dashboard/imagens/menu_inicial.png)

> [!TIP]
> **Formas de Acesso:** O relatório pode ser acessado de forma interativa diretamente pelo navegador via **[Power BI Service (Link Público)](https://app.powerbi.com/view?r=eyJrIjoiMjNlNzBmOWQtMzVlNC00MjBhLTk0MDEtYTBhZThiZWYyNTAwIiwidCI6IjhjODgwZTJhLTM2MDAtNDVmZi1hZDM5LWJhMDRlZGM4MWYyNSJ9&pageName=bcd18bc650e27d173dae)**, ou baixado e explorado localmente pelo arquivo [`dashboard/Dash_INSS_Acompanhamento_PGD.pbix`](dashboard/Dash_INSS_Acompanhamento_PGD.pbix) (já conectado nativamente ao PostgreSQL Neon). Consulte o [Guia do Dashboard](dashboard/dashboard_README.md) para detalhes.

### Principais Indicadores Monitorados:

- **45,81 Mil Designações:** Volume total acumulado de registros de designação no histórico monitorado.
- **22,20 Mil Matrículas Ativas:** Total da força de trabalho e servidores ativos mapeados no sistema.
- **15,80 Mil Média Mensal:** Volume médio de designações ativas mantidas a cada mês.
- **30 Programas Monitorados:** Diversidade de programas e modalidades de gestão cadastrados no PGD.
- **Retenção Temporal (Dias):** Tempo médio de permanência das designações no sistema por programa.
- **Detalhamento Anonimizado (LGPD):** Ranking por servidor identificado via código seguro criptografado por hash (`USR-XXXXXXXX`).
- **Sazonalidade e Curva de Status:** Identificação de picos operacionais (ex: março de 2025) e repactuação de teletrabalho.

Para mais detalhes sobre a modelagem e os achados de negócio, consulte a documentação específica:

- [Documentação Técnica do Dashboard](dashboard/dashboard_README.md)
- [Relatório de Insights e Análise Executiva](dashboard/insights_README.md): Relatório executivo da competência vigente gerado por Inteligência Artificial (Google Gemini) via [`tratamento/gerar_insights.py`](tratamento/gerar_insights.py).
- [Histórico Mensal de Relatórios](dashboard/relatorios/): Repositório dos relatórios de insights preservados mensalmente a cada novo ciclo de processamento (`insights_AAAA_MM.md`).

---

## Privacidade e Conformidade com a LGPD

Considerando que os dados de origem envolvem nomes e matrículas de servidores públicos, implementei salvaguardas rigorosas de conformidade com a **Lei Geral de Proteção de Dados (Lei nº 13.709/2018)**:

1. **Anonimização Criptográfica via HMAC (SHA-256)**:
   - As matrículas originais dos servidores são mascaradas estruturalmente logo na etapa de ETL em Python. Utilizando `hashlib` e `hmac`, o pipeline gera um hash irreversível de 8 caracteres a partir de uma chave secreta (`HMAC_SECRET_KEY`), resultando em identificadores como `USR-A1B2C3D4`. Isso garante que as informações sensíveis originais jamais transitem ou cheguem ao banco de dados em nuvem e ao Power BI.
2. **Dados Sensíveis Fora do Versionamento**:
   - Os arquivos brutos da pasta `data/` e arquivos `.env` são estritamente ignorados pelo `.gitignore`.
   - Apenas uma amostra (`sample`) estatisticamente reduzida (5.000 linhas) é versionada no repositório para permitir a validação da estrutura sem exposição desnecessária.

---

## Tecnologias Utilizadas

| Camada                                      | Tecnologias                                                                          |
| :------------------------------------------ | :----------------------------------------------------------------------------------- |
| **Linguagem & Core**                  | Python 3.12, Pandas, NumPy, Requests, Pathlib                                        |
| **Engenharia de Banco de Dados**      | PostgreSQL, SQLAlchemy, Psycopg2, Neon Tech (Serverless DB)                          |
| **Inteligência Artificial & GenAI**  | Google Gemini API (google-genai SDK), Script Automatizado de Insights                |
| **Ambiente & Containerização**      | Docker, Docker Compose                                                               |
| **Orquestração & CI/CD**            | GitHub Actions, Git, Cron Scheduling                                                 |
| **Integração & Webhooks**           | cURL, Microsoft Power Automate                                                       |
| **Business Intelligence & Analytics** | Microsoft Power BI Desktop & Service, DAX                                            |
| **Governança & Qualidade**           | Pytest, Conformidade LGPD (HMAC, Hashlib), Type Casting Estrito, Tratamento de Nulos |

---

## Licença

Este projeto está sob a licença [MIT](LICENSE).
