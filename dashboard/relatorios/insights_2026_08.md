# Insights Executivos do Dashboard — Acompanhamento PGD / INSS

> **Relatório Analítico Gerado Automaticamente por Inteligência Artificial (Google Gemini — gemini-3.8-flash)**  
> **Última Atualização:** 14/10/2026 às 22:42  
> *Diagnóstico executivo sintetizado de forma autônoma a partir dos microdados oficiais tratados do PGD/INSS.*

---

> **Nota Metodológica & Governança:**  
> Este relatório consolidado fundamenta-se na extração direta da base de dados histórica do Programa de Gestão e Desempenho (PGD) em formato colunar Parquet, garantindo integridade transacional e alta performance de processamento. Em estrita observância à Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018 - LGPD), todas as chaves identificadoras de servidores foram descaracterizadas por criptografia de mão única via algoritmo HMAC-SHA256, inviabilizando a reidentificação direta e assegurando conformidade com os princípios da finalidade, necessidade e segurança da informação na administração pública.

---

## Resumo Rápido da Série Histórica

O acompanhamento longitudinal do PGD no Instituto Nacional do Seguro Social (INSS), compreendendo o intervalo de outubro de 2023 a agosto de 2026 (35 competências avaliadas), evidencia a consolidação dos planos de trabalho baseados em entregas e metas pactuadas.

- **Universo Histórico Monitorado:** 22.200 servidores públicos federais vinculados à base de acompanhamento.
- **Volume Total de Atos de Designação:** 652.788 registros formais de planos pactuados ao longo da série histórica.
- **Média Mensal de Designações:** 18.651 atos/mês, denotando a perenidade operacional dos planos de gestão.
- **Diversidade de Programas:** 26 programas de gestão parametrizados e ativos no portfólio institucional.
- **Índice de Vinculação Múltipla:** Média institucional de 2,06 vínculos por servidor, com teto máximo registrado de 12 designações acumuladas no período.

---

## Destaques da Última Competência (08/2026 vs. 07/2026)

A transição entre julho e agosto de 2026 demonstrou estabilidade nos pactos firmados, com ligeira expansão no efetivo mobilizado em planos ativos:

- **Efetivo com Plano Ativo (Designados):** Passou de 17.545 para 17.585 servidores, representando um incremento marginal de **+0,23%** MoM (Month-over-Month).
- **Servidores Não Designados:** Variou de 4.592 para 4.615 servidores (**+0,50%** MoM), mantendo o contingente residual fora de planos de gestão em patamar estável frente ao dimensionamento da força de trabalho.
- **Desligamentos Registrados:** Redução de 42 desligamentos observados em 07/2026 para zero registro formal na competência 08/2026 (**-100,00%** MoM).
- **Regimes de Trabalho em Teletrabalho:** A soma das modalidades Remoto e Semipresencial atingiu 9.311 servidores, o que equivale a **52,9%** do efetivo total pactuado no mês. O modelo registrou expansão de **+0,62%** MoM, consolidando a predominância de regimes flexíveis orientados a resultados.
- **Regime Presencial:** Contabilizou 8.274 servidores pactuados (**47,1%** do efetivo ativo no mês).

---

## Análise Detalhada dos 6 Eixos do Painel

### Eixo 1: Visão Geral e Cobertura Institucional

O primeiro eixo analisa a taxa de adesão geral e a sustentação do programa no tempo. A relação entre o total de servidores acompanhados (22.200) e o contingente com plano de trabalho ativo na última competência (17.585) demonstra uma taxa de cobertura de 79,2% da força de trabalho elegível, mantendo o contingente de não designados (4.615) dentro de limites controlados de transição de ciclos, afastamentos legais e licenças.

![Visão Geral](../imagens/visao_geral_dashboard.png)

---

### Eixo 2: Distribuição por Modalidades de Trabalho

A distribuição dos atos de designação ativos em agosto de 2026 reflete a coexistência equilibrada entre a atuação física nas unidades e a execução descentralizada por teletrabalho:

| Modalidade | Designações no Mês | Proporção no Mês |
| :--- | :---: | :---: |
| **Presencial** | 8.286 | 47,1% |
| **Remoto** | 8.067 | 45,8% |
| **Semipresencial** | 1.245 | 7,1% |

![Modalidades de Trabalho](../imagens/modalidades_dashboard.png)

A modalidade presencial responde pela maior fatia individual (47,1%), assegurando o funcionamento ininterrupto da rede física de atendimento e suporte. Por outro lado, a soma do trabalho remoto puro (45,8%) com o semipresencial (7,1%) perfaz 52,9% dos atos, confirmando que a análise processual de benefícios e demandas administrativas permanece ancorada no trabalho a distância.

---

### Eixos 3 e 4: Desempenho e Temporalidade dos Programas de Gestão

A estratificação dos programas demonstra uma nítida separação entre programas estratégicos/controle e programas de produção operacional contínua. 

![Programas de Gestão](../imagens/programas_dashboard.png)

Quanto ao ciclo de permanência, programas de auditoria, governança e tecnologia operam com pactos de longo prazo, enquanto as frentes operacionais realizam renovações periódicas:

| Sigla do Programa | Duração Média (Dias) | Perfil de Gestão |
| :--- | :---: | :--- |
| **PG-ACS** | **1101 dias** | Governança / Controle / Estratégico |
| **PG-DTI** | **911 dias** | Governança / Controle / Estratégico |
| **CES1** | **887 dias** | Governança / Controle / Estratégico |
| **ATEND_ACGREVE** | **870 dias** | Governança / Controle / Estratégico |
| **DIR_CENTRAL1** | **729 dias** | Operacional / Ciclos Periódicos |
| **CEAB1** | **706 dias** | Operacional / Ciclos Periódicos |

Em volume de pessoal alocado, o foco do INSS recai expressivamente sobre a redução de estoques operacionais e atendimento direto ao cidadão:

| Programa | Volume |
| :--- | :---: |
| **PROGRAMA DA CEAB I** | 6.777 servidores |
| **PROGRAMA DAS SUPERINTENDÊNCIAS - PGD** | 4.573 servidores |
| **PROGRAMA DAS UNIDADES DE ATENDIMENTO - PT 1800** | 3.079 servidores |
| **PROG. PRESENCIAL 6H + PONTUAÇÃO** | 1.976 servidores |
| **PROGRAMA DAS ÁREAS DA DIREÇÃO CENTRAL** | 995 servidores |

O Programa da Central de Análise de Benefícios I (CEAB I) lidera com folga o efetivo (6.777 servidores), reafirmando que o núcleo da política de desempenho da autarquia visa à celeridade decisória nos requerimentos de direitos previdenciários.

---

### Eixo 5: Alocação Estrutural por Lotações

O mapeamento das unidades organizacionais demonstra concentração de pessoal em áreas dedicadas à análise finalística e gestão orçamentária/administrativa:

| Lotação | Volume |
| :--- | :---: |
| **SECAO DE ANALISE DE RECONHECIMENTO DE DIREITOS** | 789 servidores |
| **COORDENACAO DE GESTAO DE ORCAMENTO, FINANCAS E LOGISTICA** | 740 servidores |
| **COORDENACAO DE GESTAO DE PESSOAS** | 561 servidores |
| **SERVICO DE GERENCIAMENTO DE BENEFICIOS** | 556 servidores |
| **SECAO DE ATENDIMENTO DE DEMANDAS JUDICIAIS** | 548 servidores |

![Lotações](../imagens/lotacoes_dashboard.png)

A Seção de Análise de Reconhecimento de Direitos figura como a principal lotação (789 servidores), acompanhada de perto pelas estruturas de suporte à infraestrutura institucional (Orçamento/Logística com 740 e Pessoas com 561), denotando sustentação tanto na ponta quanto nas áreas meio.

---

### Eixo 6: Regionalização e Linhas de Trabalho

A análise das linhas de trabalho demonstra o peso das estruturas operacionais descentralizadas, com destaque primordial para a Superintendência Regional Nordeste (SRNE) e a Superintendência Regional Sudeste 1 (SRSE1):

| Linha de Trabalho | Volume |
| :--- | :---: |
| **Linha de Trabalho - Unidades de Atendimento SRNE** | 1.876 servidores |
| **Central de Análise de Benefícios de Reconhecimento de Direitos SRNE** | 1.778 servidores |
| **Superintendência Regional Nordeste** | 1.614 servidores |
| **Linha de Trabalho - Unidades de Atendimento SRSE1** | 1.463 servidores |
| **Central de Análise de Benefícios de Reconhecimento de Direitos SRSE1** | 1.214 servidores |

![Linhas de Trabalho](../imagens/linhas_trabalho_dashboard.png)

O Nordeste concentra mais de 5.200 postos de trabalho somando suas três linhas principais (Atendimento, Reconhecimento de Direitos e Superintendência), refletindo a priorização estratégica de capacidade instalada para suprir a demanda previdenciária daquela região.

---

## Auditoria de Vínculos & Conformidade LGPD

A governança do PGD requer monitoramento sistemático da conformidade dos atos para mitigar sobreposições indevidas de atribuições. Com a média geral de 2,06 vínculos por servidor ao longo da série, foram mapeados os casos de maior densidade histórica de designações.

![Auditoria LGPD](../imagens/lgpd_dashboard.png)

A relação abaixo apresenta os servidores com maior incidência de vínculos no histórico, com identificadores integralmente anonimizados:

| Servidor (Código LGPD) | Total Designações | Designações / Mês | Meses Observados |
| :---: | :---: | :---: | :---: |
| `USR-AAD51E3A` | **12** | 0,35 | 34 |
| `USR-FFB5C436` | **12** | 0,36 | 33 |
| `USR-79379680` | **10** | 0,29 | 35 |
| `USR-360E60E9` | **9** | 0,26 | 35 |
| `USR-DDAE3965` | **9** | 0,26 | 34 |
| `USR-A81A7AAA` | **9** | 0,28 | 32 |
| `USR-EE5D9946` | **9** | 0,28 | 32 |
| `USR-B8A5A365` | **8** | 0,23 | 35 |

Os dados revelam que o teto de 12 vínculos registrados no histórico está atrelado a servidores observados por quase a totalidade dos 35 meses da série (33 a 34 meses), apresentando uma cadência média regular de 0,35 a 0,36 designações por mês. Esse comportamento indica transições e renovações sucessivas de planos de trabalho, e não cumulatividade ilícita simultânea.

---

## Recomendações Executivas para o Próximo Ciclo

Com base nos dados consolidados e nos desvios padrão identificados, recomenda-se à Diretoria e aos Coordenadores-Gerais:

1. **Revisão e Padronização dos Ciclos de Vigência dos Planos:**  
   Programas estratégicos e de controle (como PG-ACS com 1.101 dias e PG-DTI com 911 dias) operam com horizontes temporais demasiadamente extensos se comparados à CEAB I (706 dias). Recomenda-se instituir marcos avaliativos intermediários (semestrais ou anuais) para programas com vigência superior a 730 dias, assegurando alinhamento dinâmico das metas individuais às prioridades da gestão.

2. **Monitoramento Automatizado dos Casos com Mais de 8 Vínculos:**  
   Embora os casos com teto de até 12 designações (ex: `USR-AAD51E3A` e `USR-FFB5C436`) reflitam transições ao longo de quase 3 anos, recomenda-se parametrizar alertas de controle interno no sistema de gestão. O objetivo é certificar a extinção formal do ato anterior antes do registro de nova pactuação, prevenindo duplicidade de carga horária ou cômputo concorrente de pontuação.

3. **Otimização da Alocação Regional e Escalonamento do Regime Semipresencial:**  
   A modalidade Semipresencial responde por apenas 7,1% das designações ativas (1.245 servidores), em contraposição à polarização entre Presencial (47,1%) e Remoto (45,8%). Diante da forte concentração de força de trabalho na SRNE e SRSE1, a Direção Central deve avaliar a ampliação do semipresencial nas unidades com gargalos de espaço físico ou déficit de atendimento local, balanceando presença física para atendimento com produtividade no teletrabalho.