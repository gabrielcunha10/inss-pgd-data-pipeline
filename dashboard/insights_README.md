# Insights Executivos do Dashboard - Acompanhamento PGD / INSS

> **Relatório Analítico Gerado Automaticamente por Inteligência Artificial (Google Gemini - gemini-3.8-flash)**  
> **Última Atualização:** 02/11/2026 às 00:03  
> *Diagnóstico executivo sintetizado de forma autônoma a partir dos microdados oficiais tratados do PGD/INSS.*

---

> **Nota Metodológica & Governança**  
> Este relatório executivo consolida dados extraídos da base transacional oficial em formato colunar Parquet, abrangendo a série histórica de outubro de 2023 a agosto de 2026 (35 competências mensais). Em observância estrita à Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018 - LGPD), todas as identificações individuais de servidores foram submetidas ao protocolo de anonimização irreversível via função criptográfica de dispersão HMAC-SHA256, assegurando a rastreabilidade estatística e a total preservação da privacidade funcional.

---

## Resumo Rápido da Série Histórica

Ao longo de 35 competências consecutivas, o Programa de Gestão e Desempenho (PGD) do INSS demonstrou consolidação técnica e institucional, monitorando um efetivo acumulado de **22.200 servidores**. O volume consolidado alcançou **652.788 atos de designação**, resultando em uma média mensal de **18.651 designações** ativas e pactuadas.

A governança do programa conta atualmente com **26 programas de gestão ativos**, desenhados para acomodar diferentes perfis institucionais, desde atividades de alta complexidade regulatória e suporte estratégico até demandas finalísticas e de produção em massa. A densidade de designações registra média de **2,06 vínculos por servidor**, com teto observado de 12 vínculos individuais, evidenciando dinâmica contínua de repactuação, adaptação a novos planos de trabalho ou alocações cumulativas transitórias devidamente monitoradas.

---

## Destaques da Última Competência (08/2026 vs. 07/2026)

A transição da competência de julho de 2026 para agosto de 2026 reflete estabilidade operacional e avanço gradual da cobertura dos planos de trabalho:

- **Efetivo com Plano Ativo (Designados):** Registrou acréscimo de 0,23% no mês (MoM), passando de 17.545 para **17.585 servidores**. A taxa de adesão ao PGD mantém-se superior a 79% do efetivo histórico total monitorado.
- **Servidores Não Designados:** Passaram de 4.592 para **4.615 servidores** (+0,50% MoM), demandando atenção gerencial sobre eventuais represamentos operacionais, transições de equipe ou descontinuidade de pactuações.
- **Movimentação de Desligamentos:** Verificou-se **zero desligamento** registrado na competência 08/2026, contra 42 desligamentos observados em 07/2026 (-100,00% MoM), indicando estabilização nos quadros funcionais pactuados no fechamento do ciclo.
- **Equilíbrio de Modalidades:** O teletrabalho total (somatório do trabalho integralmente remoto e semipresencial) atingiu **9.311 servidores** (52,9% do efetivo pactuado), com expansão de +0,62% MoM. Por sua vez, a modalidade presencial congregou **8.274 servidores** (47,1%), assegurando a manutenção ininterrupta da força de trabalho nas dependências físicas de atendimento e suporte.

---

## Análise Detalhada dos 6 Eixos do Painel

### Eixo 1: Visão Geral e Indicadores de Cobertura

![Visão Geral](imagens/visao_geral_dashboard.png)

O panorama global de cobertura revela maturidade do PGD como o instrumento basilar da gestão da força de trabalho da autarquia. A manutenção de um volume médio superior a 18 mil atos mensais confirma a sustentabilidade do fluxo de monitoramento e pactuação. O crescimento contínuo de designados (+0,23% MoM) coincide com a queda a zero de desligamentos, sugerindo um momento de consolidação dos quadros antes do planejamento do próximo ciclo semestral.

### Eixo 2: Distribuição por Modalidades de Execução

![Modalidades de Trabalho](imagens/modalidades_dashboard.png)

A distribuição das modalidades de trabalho em agosto de 2026 atesta uma divisão estratégica entre o atendimento presencial contínuo e a produtividade baseada em entregas remotas. A composição das designações do mês consolidou-se da seguinte forma:

| Modalidade | Designações no Mês | Proporção no Mês |
| :--- | :---: | :---: |
| **Presencial** | 8.286 | 47,1% |
| **Remoto** | 8.067 | 45,8% |
| **Semipresencial** | 1.245 | 7,1% |

O contingente em regime remoto (45,8%) e semipresencial (7,1%) totaliza 52,9% da força ativa pactuada. Essa estrutura sustenta a capacidade analítica da autarquia em processos eletrônicos e fluxos digitais, enquanto o contingente presencial (47,1%) salvaguarda o suporte às agências da previdência social e às rotinas administrativas locais.

### Eixo 3: Duração Média e Ciclos Temporais por Programa

![Programas de Gestão](imagens/programas_dashboard.png)

A análise da duração média dos atos de designação categoriza nitidamente os programas de gestão entre aqueles com perfil de controle contínuo/estratégico (ciclos dilatados) e aqueles focados na operação padronizada de curto e médio prazo (ciclos periódicos):

| Sigla do Programa | Duração Média (Dias) | Perfil de Gestão |
| :--- | :---: | :--- |
| **PG-ACS** | **1101 dias** | Governança / Controle / Estratégico |
| **PG-DTI** | **911 dias** | Governança / Controle / Estratégico |
| **CES1** | **887 dias** | Governança / Controle / Estratégico |
| **ATEND_ACGREVE** | **870 dias** | Governança / Controle / Estratégico |
| **DIR_CENTRAL1** | **729 dias** | Operacional / Ciclos Periódicos |
| **CEAB1** | **706 dias** | Operacional / Ciclos Periódicos |

Programas como PG-ACS (1.101 dias) e PG-DTI (911 dias) demandam prazos estendidos de planejamento decorrentes da natureza de projetos de infraestrutura tecnológica e governança setorial. Em contrapartida, CEAB1 (706 dias) e DIR_CENTRAL1 (729 dias) refletem ciclos estruturados para monitoramento periódico e repactuações baseadas em metas quantitativas de entrega de processos.

### Eixo 4: Concentração Operacional de Servidores por Programa

O detalhamento da alocação de servidores confirma a centralidade das Centrais de Análise de Benefícios e das estruturas regionais na alocação da capacidade produtiva institucional:

| Programa | Volume |
| :--- | :---: |
| **PROGRAMA DA CEAB I** | 6.777 servidores |
| **PROGRAMA DAS SUPERINTENDÊNCIAS - PGD** | 4.573 servidores |
| **PROGRAMA DAS UNIDADES DE ATENDIMENTO - PT 1800** | 3.079 servidores |
| **PROG. PRESENCIAL 6H + PONTUAÇÃO** | 1.976 servidores |
| **PROGRAMA DAS ÁREAS DA DIREÇÃO CENTRAL** | 995 servidores |

O Programa da CEAB I responde isoladamente pela maior concentração de servidores (6.777), operando como a linha de frente analítica do INSS na redução de estoques de processos de concessão. Somadas, a CEAB I e as Superintendências congregam mais de 11.350 servidores, evidenciando foco direto nas atribuições operacionais descentralizadas.

### Eixo 5: Demanda de Força de Trabalho por Lotação

![Lotações](imagens/lotacoes_dashboard.png)

As áreas com maior densidade de servidores demonstram que as unidades corporativas e as seções finalísticas de reconhecimento de direitos representam os polos de maior necessidade de alocação de pessoal:

| Lotação | Volume |
| :--- | :---: |
| **COORDENACAO DE GESTAO DE ORCAMENTO, FINANCAS E LOGISTICA** | 749 servidores |
| **COORDENACAO DE GESTAO DE PESSOAS** | 747 servidores |
| **SECAO DE ANALISE DE RECONHECIMENTO DE DIREITOS** | 656 servidores |
| **SECAO DE ATENDIMENTO DE DEMANDAS JUDICIAIS** | 607 servidores |
| **SERVICO DE GERENCIAMENTO DE BENEFICIOS** | 552 servidores |

A coordenação orçamentária e a de gestão de pessoas figuram no topo das lotações (749 e 747 servidores, respectivamente), sublinhando a intensidade de trabalho técnico demandada na governança interna do órgão. No âmbito finalístico, destacam-se a Análise de Reconhecimento de Direitos (656 servidores) e o Atendimento de Demandas Judiciais (607 servidores), áreas críticas para a mitigação de passivos e cumprimento de prazos judiciais.

### Eixo 6: Alocação Estratégica em Linhas de Trabalho

![Linhas de Trabalho](imagens/linhas_trabalho_dashboard.png)

O mapeamento por linhas de trabalho revela a distribuição espacial do esforço operacional, com expressiva predominância das Superintendências Regionais Nordeste (SRNE) e Sudeste I (SRSE1):

| Linha de Trabalho | Volume |
| :--- | :---: |
| **Linha de Trabalho - Unidades de Atendimento SRNE** | 1.873 servidores |
| **Central de Análise de Benefícios de Reconhecimento de Direitos SRNE** | 1.695 servidores |
| **Superintendência Regional Nordeste** | 1.640 servidores |
| **Linha de Trabalho - Unidades de Atendimento SRSE1** | 1.390 servidores |
| **Central de Análise de Benefícios de Reconhecimento de Direitos SRSE1** | 1.173 servidores |

A Região Nordeste lidera a alocação de capacidade de produção, agregando mais de 5.200 servidores entre unidades de atendimento, reconhecimento de direitos e gestão regional. A SRSE1 configura-se como o segundo maior núcleo de produção analítica, demonstrando a priorização do enfrentamento de demandas represadas nos principais eixos demográficos do país.

---

## Auditoria de Vínculos & Conformidade LGPD

![Auditoria LGPD](imagens/lgpd_dashboard.png)

A auditoria contínua de integridade do PGD identifica servidores com volumes atípicos de designações ao longo do histórico observado. A tabela a seguir relaciona os servidores que atingiram ou se aproximaram do teto máximo de vínculos (12 designações):

| Servidor (Código LGPD) | Total Designações | Designações / Mês | Meses Observados |
| :---: | :---: | :---: | :---: |
| `USR-FFB5C436` | **12** | 0,36 | 33 |
| `USR-AAD51E3A` | **12** | 0,35 | 34 |
| `USR-79379680` | **10** | 0,29 | 35 |
| `USR-EE5D9946` | **9** | 0,28 | 32 |
| `USR-360E60E9` | **9** | 0,26 | 35 |
| `USR-DDAE3965` | **9** | 0,26 | 34 |
| `USR-A81A7AAA` | **9** | 0,28 | 32 |
| `USR-2F46A017` | **8** | 0,26 | 31 |

Embora a média geral da autarquia seja de 2,06 vínculos, os casos destacados representam agentes atuantes em múltiplos grupos de trabalho, forças-tarefa consecutivas ou readequações sucessivas de planos de entrega. A métrica de designações por mês varia entre 0,26 e 0,36, o que comprova que as renovações ocorreram ao longo de janelas temporais de 31 a 35 meses, descartando sobreposição anômala concentrada em único intervalo restrito.

---

## Recomendações Executivas para o Próximo Ciclo

Com esteio nas constatações técnicas e nas tendências observadas no encerramento da competência 08/2026, propõem-se as seguintes ações para a Diretoria e as chefias imediatas:

1. **Plano de Regularização dos Servidores Não Designados:**  
   Instaurar monitoramento focalizado sobre o contingente de 4.615 servidores não designados (que apresentou expansão de +0,50% MoM). Recomenda-se que as unidades regionais elaborem plano de regularização funcional em até 30 dias para enquadramento destes servidores em planos de entrega formalizados ou justificativa de incompatibilidade funcional.

2. **Revisão e Homologação de Múltiplos Vínculos:**  
   Notificar preventivamente as chefias dos servidores que acumularam 10 ou mais designações no período histórico (casos exemplificados por `USR-FFB5C436`, `USR-AAD51E3A` e `USR-79379680`), a fim de averiguar se os múltiplos registros refletem substituições regulares de planos operacionais ou duplicidade ativa de metas, preservando a coerência da carga horária legal de trabalho.

3. **Adequação Temporal dos Ciclos de Planos Operacionais:**  
   Promover revisão nos prazos de vigência dos programas operacionais, a exemplo de DIR_CENTRAL1 (729 dias) e CEAB1 (706 dias). Recomenda-se alinhar a periodicidade dessas designações a ciclos avaliativos mais curtos (preferencialmente anuais ou semestrais), mantendo prazos estendidos (superiores a 800 dias) prioritariamente para áreas finalísticas de projetos de governança e tecnologia da informação (PG-ACS e PG-DTI).