# 📊 Dashboard de Designações — Acompanhamento PGD / INSS

Este documento descreve os componentes, indicadores de negócio e formas de acesso ao painel analítico do **Programa de Gestão e Desempenho (PGD)** do INSS.

---

## 📌 Explicação dos Componentes do Dashboard

- **Evolução da Quantidade de Designações por Status e Competência (Out/2023 a Jan/2026):** Gráfico de linha que exibe a trajetória histórica integral dos status (Designado, Não Designado e Desligado). Evidencia a estabilidade dos servidores designados em 2024 (~13-14 mil), o salto estrutural para um novo patamar a partir de 2025 (~18-19 mil), o declínio sustentado dos não designados e o evento de corte/saneamento administrativo em **março de 2025** (~3.433 desligamentos em lote).
- **Cartões de Métrica (KPIs Centrais):**
  - **45,40 Mil Designações:** Volume total acumulado de registros de designação no histórico monitorado.
  - **22,13 Mil Matrículas Ativas:** Total da força de trabalho e servidores ativos mapeados no sistema.
  - **15,75 Mil Média Designações Mês:** Volume médio de designações mantidas ativas a cada mês na instituição.
  - **30 Contagem de Programas:** Número de programas e modalidades de gestão cadastrados no PGD.
- **Média de Tempo (Dia) de Designação por Programa:** Gráfico de barras horizontal ordenado por duração. Mostra a **retenção temporal (em dias)** das designações, com topo liderado por unidades de governança, auditoria e gabinetes (`PG-ACS`, `PG-CORREG`, `PGRP`, `CEAP`), cujas tarefas permanecem ativas por mais tempo no Sisref.
- **Média Histórica de Designações por Mês:** Gráfico de colunas que analisa a sazonalidade anual do volume de designações (de janeiro a dezembro), mostrando estabilidade com picos nos meses de **março e abril** (~16,7 mil a 17 mil).
- **Tabela de Detalhamento por Servidor/Vínculo:** Tabela interativa com pseudonimização/anonimização por código numérico de servidor, em estrita conformidade com a LGPD. Permite duas análises cruciais de gestão: ordenação por **Total de Designações** (evidenciando a estabilidade a longo prazo, liderada pelo servidor `49732` com teto de 15 designações em 33 meses) e por **Designações/Mês** (evidenciando a frequência de curto prazo e o viés de janelas amostrais reduzidas, como o servidor `36060` com taxa 2,00 em apenas 1 mês).
- **Designações por Programa:** Gráfico de barras horizontal que mede a **volumetria/quantidade acumulada de designações**. Liderado de forma isolada pela **CEAB1** (Central de Análise de Benefício 1), seguida por `SR_PGD`, `ATENDIMENTO` e `DIR_CENTRAL1`.

---

## 🖼️ Visualização do Dashboard

![Dashboard de Designações](imagens/dashboard.png)

---

## 🌐 Publicação Web (Power BI Service) — Em Andamento

> [!NOTE]
> **Status da Publicação Online (Power BI Service / Web):**
> O objetivo é disponibilizar o dashboard para navegação pública e interativa diretamente pelo navegador via Power BI Service. Atualmente, a publicação web está temporariamente pausada devido a uma pendência de validação/provisionamento na conta estudantil da Microsoft, com **previsão de resolução e publicação do link online até 22/09/2026**.
> 
> Enquanto a publicação web é concluída, o acesso pode ser realizado diretamente pelo Power BI Desktop conforme as opções abaixo.

---

## 🚀 Como Acessar e Executar o Dashboard

Existem duas formas de abrir e utilizar o relatório no Power BI:

### 🟢 Opção 1: Acesso Direto via .PBIX (Principal e Recomendada)

Esta é a opção mais rápida e automatizada. O relatório já está configurado e integrado nativamente ao banco de dados relacional **PostgreSQL na nuvem (Neon Tech)**:

1. Baixe ou clone este repositório em sua máquina.
2. Abra o arquivo do relatório no **Power BI Desktop**:
   ```text
   dashboard/Dash_INSS_Acompanhamento_PGD.pbix
   ```
3. **Pronto!** O dashboard já abrirá com todos os visuais, medidas DAX, tabela anonimizada e dados carregados diretamente da nuvem.
4. Caso queira atualizar com novos dados inseridos pelo pipeline, basta clicar no botão **"Atualizar"** na barra superior do Power BI.

---

### 🟡 Opção 2: Carga Manual via CSV / Kaggle (100% Manual e Offline)

Caso prefira operar de forma estritamente offline ou queira recriar o processo a partir de arquivos planos sem conectar ao banco de dados em nuvem, você pode fazer todo o processo manualmente:

#### 1. Baixar o dataset no Kaggle
Acesse o conjunto de dados no Kaggle:
👉 [Dataset INSS - PGD Designações no Kaggle](https://www.kaggle.com/datasets/4894808d3f21243e3185b33f3d31f0881fc39ac74124b015dd2c2f2d017bac80)

Clique em **Download** para baixar o arquivo compactado (`archive.zip`).

#### 2. Extrair o arquivo CSV
1. Localize o arquivo `.zip` baixado na sua máquina.
2. Extraia o conteúdo (ex: na sua pasta `Downloads`).
3. Localize o CSV tratado dentro da pasta de destino:
   ```text
   Downloads/archive/dataset/processed/pgd_designacoes_inss_2023_2026.csv
   ```

#### 3. Vincular a fonte manual no Power BI
1. Abra o arquivo `Dash_INSS_Acompanhamento_PGD.pbix` no Power BI Desktop.
2. No menu superior, clique em **Transformar Dados** (Power Query).
3. Selecione a consulta principal e vá em **Configurações da Fonte de Dados**.
4. Altere a origem para o arquivo `pgd_designacoes_inss_2023_2026.csv` extraído na sua pasta local.
5. Clique em **Fechar e Aplicar** e aguarde o carregamento dos registros.

---

## 📄 Documentos Relacionados

- 💡 [Relatório de Insights e Análise Executiva](insights_README.md): Análise detalhada das tendências temporais, do pico de março/2025 e do comportamento das linhas de trabalho.
- 📘 [README Principal do Projeto](../README.md): Arquitetura completa da solução, scripts de ingestão/ETL e orquestração CI/CD.
