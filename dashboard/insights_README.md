# Insights Executivos do Dashboard — Acompanhamento PGD / INSS

> **Relatório Analítico Gerado Automaticamente por Inteligência Artificial (Google Gemini — gemini-3.6-flash)**  
> **Última Atualização:** 01/11/2026 às 15:40  
> *Diagnóstico executivo sintetizado de forma autônoma a partir dos microdados oficiais tratados do PGD/INSS.*

---

> **Nota Metodológica & Governança:** Este relatório consolida as métricas e indicadores de desempenho do Programa de Gestão e Desempenho (PGD) do Instituto Nacional do Seguro Social (INSS), fundamentando-se em dados operacionais estruturados em formato Parquet referentes às competências de 10/2023 a 08/2026. Em estrita conformidade com a Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018 - LGPD), a identificação dos servidores foi anonimizada por meio de algoritmos de dispersão criptográfica (HMAC-SHA256), assegurando auditabilidade com total preservação da privacidade.

---

## Resumo Rápido da Série Histórica

O acompanhamento longitudinal do PGD abrange um horizonte temporal de **35 competências mensais** (outubro de 2023 a agosto de 2026), registrando o comportamento da força de trabalho pactuada na autarquia:

*   **Universo Acompanhado:** 22.200 servidores mapeados ao longo da série histórica.
*   **Volume Acumulado de Atos de Designação:** 652.788 atos homologados.
*   **Média Mensal de Designações:** 18.651 atos/mês.
*   **Programas de Gestão Ativos:** 26 programas em operação regular.
*   **Índice de Densidade de Vínculos:** Média de 2,06 vínculos por servidor (amplamente resguardada do teto regulatório de 12 vínculos simultâneos).

---

## Destaques da Última Competência (08/2026 vs. 07/2026)

A transição entre os meses de julho e agosto de 2026 demonstrou estabilidade operacional e consolidação das metas pactuadas, com variações residuais previsíveis:

*   **Servidores Designados (Plano Ativo):** Expansão de **+0,23%** (de 17.545 para **17.585** servidores).
*   **Servidores Não Designados:** Incremento marginal de **+0,50%** (de 4.592 para **4.615** servidores sem plano ativo no mês).
*   **Desligamentos no Mês:** Redução de **-100,00%** (passando de 42 desligamentos em 07/2026 para **0** desligamentos em 08/2026).
*   **Adesão ao Teletrabalho:** O contingente total em modalidade não presencial (Remoto + Semipresencial) atingiu **9.311 servidores**, o que representa **52,9%** do efetivo pactuado no mês, registrando uma variação MoM de **+0,62%**.
*   **Regime Presencial:** Concentra **8.274 servidores**, equivalendo a **47,1%** da força de trabalho pactuada.

---

## Análise Detalhada dos 6 Eixos do Painel

### Eixo 1: Visão Geral e Volume Ativo

![Visão Geral](imagens/visao_geral_dashboard.png)

A sustentabilidade do PGD no INSS reflete-se na previsibilidade do volume de designações ativas. O total de **17.585 servidores com planos ativos** em 08/2026 evidencia a maturidade institucional na pactuação continuada de metas. Do universo total histórico de 22.200 servidores monitorados, a manutenção contínua de mais de 79% do quadro ativo sob o PGD demonstra que o programa se consolidou como a principal ferramenta de gestão de desempenho do órgão.

---

### Eixo 2: Distribuição por Modalidades de Trabalho

![Modalidades de Trabalho](imagens/modalidades_dashboard.png)

A distribuição das vagas ativas reflete um equilíbrio estratégico entre o atendimento físico nas agências e o processamento descentralizado de análise de benefícios.

| Modalidade | Designações no Mês | Proporção no Mês |
| :--- | :---: | :---: |
| **Presencial** | 8.286 | 47,1% |
| **Remoto** | 8.067 | 45,8% |
| **Semipresencial** | 1.245 | 7,1% |

**Análise de Desempenho:** A soma das modalidades flexíveis (Remoto e Semipresencial) responde por 52,9% do total pactuado. A prevalência do trabalho remoto integral em 45,8% sustenta a produtividade nas Centrais de Análise de Benefícios, enquanto o regime presencial (47,1%) garante a capacidade operacional do atendimento direto ao cidadão nas Unidades de Atendimento.

---

### Eixos 3 e 4: Caracterização dos Programas de Gestão e Duração dos Pactos

![Programas de Gestão](imagens/programas_dashboard.png)

Os programas de gestão ativos apresentam perfis distintos de duração e adesão, correlacionados diretamente com a natureza das atribuições (governança vs. rotina operacional).

#### Duração Média por Programa e Perfil Executivo

| Sigla do Programa | Duração Média (Dias) | Perfil de Gestão |
| :--- | :---: | :--- |
| **PG-ACS** | **1101 dias** | Governança / Controle / Estratégico |
| **PG-DTI** | **911 dias** | Governança / Controle / Estratégico |
| **CES1** | **887 dias** | Governança / Controle / Estratégico |
| **ATEND_ACGREVE** | **870 dias** | Governança / Controle / Estratégico |
| **DIR_CENTRAL1** | **729 dias** | Operacional / Ciclos Periódicos |
| **CEAB1** | **706 dias** | Operacional / Ciclos Periódicos |

#### Concentração de Servidores por Programa

| Programa | Volume |
| :--- | :---: |
| **PROGRAMA DA CEAB I** | 6.777 servidores |
| **PROGRAMA DAS SUPERINTENDÊNCIAS - PGD** | 4.573 servidores |
| **PROGRAMA DAS UNIDADES DE ATENDIMENTO - PT 1800** | 3.079 servidores |
| **PROG. PRESENCIAL 6H + PONTUAÇÃO** | 1.976 servidores |
| **PROGRAMA DAS ÁREAS DA DIREÇÃO CENTRAL** | 995 servidores |

**Análise de Desempenho:** Observa-se que programas estratégicos como **PG-ACS** (1.101 dias) e **PG-DTI** (911 dias) operam sob vigências estendidas para garantir a continuidade de projetos de longo prazo em infraestrutura e governança. Por outro lado, o **PROGRAMA DA CEAB I** sobressai-se como o maior indutor de força de trabalho, alocando 6.777 servidores em entregas operacionais focadas no reconhecimento do direito dos segurados.

---

### Eixo 5: Mapeamento de Lotações Estratégicas e Operacionais

![Lotações](imagens/lotacoes_dashboard.png)

A distribuição do contingente alocado no PGD revela as unidades administrativas e operacionais prioritárias na execução dos processos do INSS:

| Lotação | Volume |
| :--- | :---: |
| **COORDENACAO DE GESTAO DE ORCAMENTO, FINANCAS E LOGISTICA** | 749 servidores |
| **COORDENACAO DE GESTAO DE PESSOAS** | 747 servidores |
| **SECAO DE ANALISE DE RECONHECIMENTO DE DIREITOS** | 656 servidores |
| **SECAO DE ATENDIMENTO DE DEMANDAS JUDICIAIS** | 607 servidores |
| **SERVICO DE GERENCIAMENTO DE BENEFICIOS** | 552 servidores |

**Análise de Desempenho:** Há uma expressiva concentração de servidores pactuados em coordenações centrais de suporte (Gestão de Pessoas e Orçamento/Finanças/Logística, totalizando 1.496 servidores), combinada à priorização de unidades finalísticas de alta demanda, como Reconhecimento de Direitos e Atendimento de Demandas Judiciais.

---

### Eixo 6: Desempenho por Linhas de Trabalho

![Linhas de Trabalho](imagens/linhas_trabalho_dashboard.png)

O volume por linha de trabalho explicita a descentralização geográfica do fluxo produtivo, com destaque para a Região Nordeste e a Região Sudeste I:

| Linha de Trabalho | Volume |
| :--- | :---: |
| **Linha de Trabalho - Unidades de Atendimento SRNE** | 1.873 servidores |
| **Central de Análise de Benefícios de Reconhecimento de Direitos SRNE** | 1.695 servidores |
| **Superintendência Regional Nordeste** | 1.640 servidores |
| **Linha de Trabalho - Unidades de Atendimento SRSE1** | 1.390 servidores |
| **Central de Análise de Benefícios de Reconhecimento de Direitos SRSE1** | 1.173 servidores |

**Análise de Desempenho:** A Superintendência Regional Nordeste (SRNE) absorve a maior fatia das pactuações operacionais, somando 5.208 servidores distribuídos entre atendimento, análise de benefícios e governança regional, refletindo a elevada demanda de processamento de requisitos de proteção social nessa jurisdição.

---

## Auditoria de Vínculos & Conformidade LGPD

![Auditoria LGPD](imagens/lgpd_dashboard.png)

Em compliance com as normas de governança corporativa e integridade da informação, o monitoramento preventivo auditou a ocorrência de múltiplos vínculos de pactuação por servidor.

| Servidor (Código LGPD) | Total Designações | Designações / Mês | Meses Observados |
| :---: | :---: | :---: | :---: |
| `USR-AAD51E3A` | **12** | 0,35 | 34 |
| `USR-FFB5C436` | **12** | 0,36 | 33 |
| `USR-79379680` | **10** | 0,29 | 35 |
| `USR-DDAE3965` | **9** | 0,26 | 34 |
| `USR-360E60E9` | **9** | 0,26 | 35 |
| `USR-EE5D9946` | **9** | 0,28 | 32 |
| `USR-A81A7AAA` | **9** | 0,28 | 32 |
| `USR-27D83F6D` | **8** | 0,23 | 35 |

**Avaliação de Conformidade:** 
1. **Conformidade Normativa:** A média institucional mantida é de **2,06 vínculos por servidor**, com o teto máximo de acúmulo individual fixado em **12 designações** ao longo de toda a série de 35 meses.
2. **Frequência de Repactuação:** O servidor com maior histórico acumulado (`USR-AAD51E3A`) registrou 12 designações ao longo de 34 meses observados, resultando em uma taxa de 0,35 designações/mês. Isso evidencia regularidade no ciclo de renovação dos planos de trabalho, sem sobreposição indevida de jornadas ou violação aos normativos do PGD.

---

## Recomendações Executivas para o Próximo Ciclo

1. **Plano de Ação para a Força Não Designada (4.615 servidores):**
   Desenvolver diagnóstico focalizado junto às Unidades Rurais e Centrais de Atendimento para mapear e regularizar a situação dos 4.615 servidores que constam sem plano ativo em 08/2026 (+0,50% MoM), reengajando-os nos programas de gestão vigentes ou justificando exceções regulamentares.

2. **Revisão e Padronização dos Ciclos de Repactuação Longos:**
   Estabelecer marcos intermediários formais de avaliação de metas para programas com ciclo médio superior a 800 dias (como **PG-ACS** com 1.101 dias e **PG-DTI** com 911 dias), prevenindo a desatualização de entregas perante as metas institucionais do INSS.

3. **Reequilíbrio e Suporte Logístico Operacional na SRNE e SRSE1:**
   Direcionar reforço em ferramentas tecnológicas e automação para as Centrais de Análise de Benefícios da SRNE (1.695 servidores) e SRSE1 (1.173 servidores), visto que concentram o maior volume de força de trabalho em teletrabalho, garantindo o atingimento do plano de redução da fila nacional de requerimentos.