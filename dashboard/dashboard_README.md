# 📊 Dashboard de Designações

**Explicação dos Componentes do Dashboard**

- **Evolução da Quantidade de Designações por Status e Competência (Out/2023 a Jan/2026):** Gráfico de linha que exibe a trajetória histórica integral dos status (Designado, Não Designado e Desligado). Evidencia a estabilidade dos servidores designados em 2024 (~13-14 mil), o salto estrutural para um novo patamar a partir de 2025 (~18-19 mil), o declínio sustentado dos não designados e o evento de corte/saneamento administrativo em **março de 2025** (~3.428 desligamentos em lote).
- **Cartões de Métrica (KPIs Centrais):**

  - **45,40 Mil Designações:** Volume total acumulado de registros de designação no histórico monitorado.
  - **22,13 Mil Matrículas Ativas:** Total da força de trabalho/servidores ativos mapeados no sistema.
  - **15,75 Mil Média Designações Mês:** Volume médio de designações mantidas ativas a cada mês na instituição.
  - **30 Contagem de Programas:** Número de programas/modalidades de gestão cadastrados no PGD.
- **Média de Tempo (Dia) de Designação por Programa:** Gráfico de barras horizontal ordenado por duração. Mostra a **retenção temporal (em dias)** das designações, com topo liderado por unidades de governança, auditoria e gabinetes (`PG-ACS`, `PG-CORREG`, `PGRP`, `CEAP`), cujas tarefas permanecem ativas por mais tempo no Sisref.
- **Média Histórica de Designações por Mês:** Gráfico de colunas que analisa a sazonalidade anual do volume de designações (de janeiro a dezembro), mostrando estabilidade com picos nos meses de **março e abril** (~16,7 mil a 17 mil).
- **Tabela de Detalhamento por Servidor/Vínculo:** Tabela centralizada que apresenta o ranking individual filtrado com pseudonimização/anonimização por código (`USR-xxxxx`), em estrita conformidade com a LGPD. Exibe o **Total de Designações**, a **Média de Designações/Mês** e a quantidade de **Meses Observados**, evidenciando a pulverização da carga de trabalho entre os servidores.
- **Designações por Programa:** Gráfico de barras horizontal que mede a **volumetria/quantidade acumulada de designações**. Liderado de forma isolada pela **CEAB1** (Central de Análise de Benefício 1), seguida por `SR_PGD`, `ATENDIMENTO` e `DIR_CENTRAL1`.

---

## 🖼️ Visualização do Dashboard

![Dashboard de Designações](imagens/dashboard.png)

O dashboard apresenta indicadores e visualizações relacionados às designações, matrículas, programas, status e evolução ao longo do período analisado.

---

## 📥 Download e Extração do Dataset

O dashboard utiliza um dataset disponibilizado no Kaggle.

### 1. Baixar o dataset

Acesse:

https://www.kaggle.com/datasets/4894808d3f21243e3185b33f3d31f0881fc39ac74124b015dd2c2f2d017bac80

Clique em **Download** para baixar o dataset.

### 2. Extrair o dataset

Após o download:

1. Localize o arquivo `.zip` baixado.
2. Clique com o botão direito sobre o arquivo.
3. Selecione **Extrair tudo...**.
4. Escolha a pasta **Downloads** como destino da extração.
5. Clique em **Extrair**.

Ao final, os arquivos do dataset estarão disponíveis dentro da pasta `Downloads`.

### 3. Estrutura esperada

O arquivo CSV utilizado pelo Power BI deverá estar dentro da pasta `Downloads`, por exemplo:

```text
C:\Users\SEU_USUARIO\Downloads\archive\dataset\processed
└── pgd_designacoes_inss_2023_2026.csv
```

---

## ▶️ Execução do Dashboard

Após realizar o download e a extração do dataset:

1. Abra o arquivo `.pbix` do dashboard no **Power BI Desktop**.
2. Verifique se o arquivo `pgd_designacoes_inss_2023_2026.csv` está disponível na pasta `Downloads`.
3. Caso o Power BI solicite a localização da fonte de dados, selecione o arquivo CSV dentro da pasta `Downloads`.
4. No Power BI, clique em **Atualizar** para carregar os dados.
5. Aguarde a conclusão da atualização das consultas e dos visuais.
6. Após a atualização, o dashboard estará pronto para ser explorado.

> **Importante:** mantenha o arquivo CSV na pasta `Downloads` e não altere seu nome. Caso o arquivo seja movido ou renomeado, será necessário atualizar o caminho da fonte de dados no Power BI.
