# ETL — Programa de Gestão de Desempenho (PGD) INSS

Pipeline de ETL em Python/pandas que consolida **28 arquivos CSV mensais** de dados abertos do governo federal, referentes ao Programa de Gestão de Desempenho (PGD) aplicado ao quadro de atendimento do INSS (ACSINSS), cobrindo o período de **outubro/2023 a janeiro/2026**.

Projeto desenvolvido como peça de portfólio, com foco em demonstrar habilidades de tratamento de dados reais e imperfeitos — o tipo de desafio recorrente em dados públicos governamentais brasileiros.

## Contexto

Projeto desenvolvido como parte de portfólio de análise de dados, com tema alinhado à área de atuação da Dataprev (processamento de dados de proteção social).

## Contexto

Este projeto foi desenvolvido como parte do meu portfólio de análise de dados, inspirado pelo processo seletivo de estágio atualmente promovido pela Dataprev. Durante minha preparação para a seleção, passei a pesquisar mais profundamente sobre a empresa, sua atuação estratégica no processamento e na gestão de dados relacionados à proteção social, previdência, benefícios e políticas públicas.

O contato com esse contexto despertou meu interesse pela Dataprev e pela aplicação da análise de dados em problemas de grande impacto social. A partir disso, decidi desenvolver um projeto tematicamente alinhado às atividades da empresa, utilizando técnicas de tratamento, exploração e visualização de dados para simular um cenário compatível com o tipo de informação que organizações públicas e de tecnologia para o setor governamental lidam diariamente.

Além de fortalecer meu aprendizado em Python, Pandas e análise exploratória de dados, este projeto representa uma demonstração prática do meu interesse em atuar na área de dados e, especialmente, em oportunidades como o programa de estágio da Dataprev.

## Resultado

O dataset final, já limpo e consolidado, está disponível diretamente neste repositório:

📄 **[`pgd_designacoes_inss_2023_2026.csv`](./pgd_designacoes_inss_2023_2026.csv)** — 503.972 linhas, 19 colunas padronizadas, pronto para uso (Excel, Power BI, Python, etc.), sem necessidade de rodar nenhum código.

## Sobre os dados

Os arquivos de origem não seguem um schema único: ao longo dos 28 meses, o sistema exportador passou por pelo menos três formatos diferentes, com nomes de coluna inconsistentes (`Matricula` / `Matrícula` / `siape2`), colunas que aparecem e desaparecem entre meses, formatos de data distintos e um arquivo (out/2023) com estrutura completamente diferente dos demais.

Mais detalhes sobre o dataset bruto estão descritos em [`descricao_dataset_kaggle.md`](./descricao_dataset_kaggle.md).

## O que o pipeline faz

1. **Leitura padronizada** dos 28 arquivos (`dtype=str` em toda a leitura, evitando ambiguidade de tipo entre arquivos)
2. **Harmonização de colunas** via dicionário de renomeação, unificando ~30 variações de nome em ~19 colunas finais
3. **Derivação de competência** a partir do nome do arquivo (mais confiável que a coluna de conteúdo, que nem sempre existe)
4. **Inferência de valores ausentes** com validação empírica de confiança antes de qualquer preenchimento — nenhuma tradução foi aplicada sem antes medir a taxa de acerto contra dados reais
5. **Exclusão de colunas redundantes ou constantes**, identificadas por investigação de conteúdo, não só pelo nome
6. **Consolidação final** em uma única tabela (`pgd_designacoes_inss_2023_2026.csv`)

## Decisões de tratamento de dados

Cada coluna com valores ausentes foi investigada individualmente antes de qualquer decisão. Resumo das principais:

| Situação encontrada                                                                                                               | Decisão                                                                                                                                                                                                               | Confiança                                                                             |
| ----------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `regime` (2023) e `Modalidade` (demais anos) são o mesmo campo renomeado                                                       | Unificados, com tradução de valores (`Integral`→`Remoto`, `Parcial`→`Semipresencial`)                                                                                                                      | 97,9% (validado cruzando meses)                                                        |
| `sigla_programa` e `programa` têm relação bijetiva quando ambos presentes                                                    | Preenchimento cruzado (`fillna` bidirecional)                                                                                                                                                                        | 100% (determinístico)                                                                 |
| `id_designacao` ausente em 2 meses específicos por falha estrutural do arquivo                                                   | Reconstruído via "ponte" entre meses vizinhos, só quando os dois lados concordam                                                                                                                                     | ~95-97%, com limitação residual documentada (~0,3%)                                  |
| `flag_pgd` correlaciona com `programa`, mas só para 13 dos 29 programas identificados                                          | Preenchido **apenas** para os 13 programas com correlação comprovada nos dados; os 16 restantes (confirmados por fonte externa apenas quanto ao nome, não quanto ao enquadramento no PGD) permanecem `NaN` | Decisão conservadora — sem extrapolação não verificável                          |
| `Tipo de Entrega` não tem correlação forte o bastante com nenhuma combinação de colunas disponível para os registros vazios | Não preenchido                                                                                                                                                                                                        | Testado (~90% em geral, mas 0% de cobertura aplicável aos registros realmente vazios) |
| `dt_alteracao_designacao`, `motivo_desligamento`, `id_lotacao`                                                                | Mantidos com`NaN` — ausência estrutural genuína, sem fonte alternativa segura                                                                                                                                     | —                                                                                     |

A lógica geral seguida em todo o pipeline: **nenhum valor foi inferido sem antes ser testado contra uma amostra real de dados**, e nenhuma inferência foi aplicada quando a confiança medida ficou abaixo de um limiar considerado seguro (~90-95%, variando por criticidade do campo).

## Estrutura do repositório

```
.
├── pgd_designacoes_inss_2023_2026.csv   # resultado final (pronto para uso)
├── etl_sgp_inss_2023_2026.py             # script de ETL completo
├── descricao_dataset_kaggle.md            # descrição do dataset bruto (28 CSVs)
├── README.md
└── data/                                   # não versionado — só necessário para reproduzir o ETL
    └── *.csv
```


## Como reproduzir o pipeline (opcional)

O CSV final já está disponível no repositório. Os passos abaixo só são necessários caso você queira rodar o processo de tratamento do zero, a partir dos dados brutos.

1. Baixe o dataset com os 28 arquivos CSV originais no [Kaggle](https://kaggle.com/datasets/4894808d3f21243e3185b33f3d31f0881fc39ac74124b015dd2c2f2d017bac80).
2. Após baixar o dataset, **extraia o arquivo ZIP em um local de sua preferência**. Em seguida, **arraste ou copie os 28 arquivos `.csv` extraídos para dentro da pasta `data/` do projeto**.

   **Não coloque o arquivo `.zip` dentro da pasta `data/` e não é necessário extrair o ZIP diretamente dentro dela.** O script espera encontrar os arquivos CSV diretamente nesse diretório.

   A estrutura do projeto deve ficar assim:

   ```text
   projeto/
   ├── etl_sgp_inss_2023_2026.py
   └── data/
       ├── D_SRF_FQS_005_ACSINSS_PGD_202310.csv
       ├── D_SRF_FQS_005_PGD_ACSINSS_202311.csv
       ├── ...
       └── (demais arquivos CSV)
   ```
3. As dependências (`pandas`, `numpy`) já vêm incluídas na instalação padrão do [Anaconda](https://www.anaconda.com/download). Caso esteja usando outro ambiente Python, instale com:

   ```bash
   pip install pandas numpy
   ```
4. Execute o script. Há duas formas possíveis:

   * **Diretamente pelo terminal:**

     ```bash
     python etl_sgp_inss_2023_2026.py
     ```
   * **Célula por célula (recomendado):** o script foi desenvolvido com marcações de célula (`#%%`), compatíveis com o Spyder (incluído no Anaconda) e com a extensão Python do VS Code. Abra o arquivo em uma dessas ferramentas e execute as células individualmente para acompanhar cada etapa do tratamento.
5. Ao final da execução, o arquivo tratado será gerado como:

   ```text
   pgd_designacoes_inss_2023_2026.csv
   ```

O arquivo completo tratado está disponível na pasta `processed/`do dataset no Kaggle. No GitHub, é disponibilizada apenas uma  **amostra (** `sample` **) do arquivo final** , evitando o versionamento de um arquivo grande no repositório.

## Tecnologias

- Python 3
- pandas
- numpy

## Próximos passos

- Análise de série temporal de modalidade de trabalho ao longo dos 28 meses
- Análise de rotatividade (turnover) a partir de datas de início/fim de designação
- Distribuição regional e por linha de trabalho
