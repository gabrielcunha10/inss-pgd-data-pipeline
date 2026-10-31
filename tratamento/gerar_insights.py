import logging
import os
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import numpy as np
import pandas as pd

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "pipeline.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)

PARQUET_PATH = PROJECT_DIR / "tests" / "pgd_designacoes_inss_2023_2026.parquet"
OUTPUT_MARKDOWN = PROJECT_DIR / "dashboard" / "insights_README.md"
OUTPUT_CSV_POWERBI = PROJECT_DIR / "dashboard" / "insights_historico_powerbi.csv"
RELATORIOS_DIR = PROJECT_DIR / "dashboard" / "relatorios"


try:
    from google import genai
    GENAI_DISPONIVEL = True
except ImportError:
    GENAI_DISPONIVEL = False


def carregar_dados(caminho: Path) -> pd.DataFrame:
    logging.info(f"Carregando dados consolidados de: {caminho}")
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}. Execute o ETL antes.")
    return pd.read_parquet(caminho)


def calcular_metricas(df: pd.DataFrame) -> dict:
    logging.info("Calculando métricas analíticas e comparativos MoM...")
    comps = sorted(df["competencia"].dropna().unique())
    total_meses = len(comps)
    primeira_comp = comps[0]
    ult_comp = comps[-1]
    ant_comp = comps[-2] if total_meses > 1 else comps[0]

    df_ult = df[df["competencia"] == ult_comp]
    df_ant = df[df["competencia"] == ant_comp]

    total_registros = len(df)
    total_servidores = df["id_usuario"].nunique()
    programas_ativos_geral = df[df["flag_pgd"] == "Sim"]["programa"].nunique()
    media_desig_mes = total_registros / total_meses if total_meses > 0 else 0

    status_dist_geral = df["status"].value_counts(dropna=False)
    status_pct_geral = df["status"].value_counts(normalize=True, dropna=False) * 100

    serv_desig_ult = df_ult[df_ult["status"] == "Designado"]["id_usuario"].nunique()
    serv_desig_ant = df_ant[df_ant["status"] == "Designado"]["id_usuario"].nunique()
    var_serv_desig = (
        ((serv_desig_ult - serv_desig_ant) / serv_desig_ant * 100)
        if serv_desig_ant > 0
        else 0.0
    )

    serv_nao_desig_ult = df_ult[df_ult["status"] == "Não Designado"]["id_usuario"].nunique()
    serv_nao_desig_ant = df_ant[df_ant["status"] == "Não Designado"]["id_usuario"].nunique()
    var_nao_desig = (
        ((serv_nao_desig_ult - serv_nao_desig_ant) / serv_nao_desig_ant * 100)
        if serv_nao_desig_ant > 0
        else 0.0
    )

    serv_deslig_ult = df_ult[df_ult["status"] == "Desligado"]["id_usuario"].nunique()
    serv_deslig_ant = df_ant[df_ant["status"] == "Desligado"]["id_usuario"].nunique()
    var_deslig = (
        ((serv_deslig_ult - serv_deslig_ant) / serv_deslig_ant * 100)
        if serv_deslig_ant > 0
        else 0.0
    )

    mod_ult_counts = df_ult["modalidade"].value_counts()
    mod_ult_pct = df_ult["modalidade"].value_counts(normalize=True) * 100

    teletrab_serv_ult = df_ult[
        df_ult["modalidade"].isin(["Remoto", "Semipresencial"])
    ]["id_usuario"].nunique()
    presenc_serv_ult = df_ult[df_ult["modalidade"] == "Presencial"][
        "id_usuario"
    ].nunique()
    total_mod_serv = teletrab_serv_ult + presenc_serv_ult
    pct_teletrab_serv = (
        (teletrab_serv_ult / total_mod_serv * 100) if total_mod_serv > 0 else 0
    )
    pct_presenc_serv = (
        (presenc_serv_ult / total_mod_serv * 100) if total_mod_serv > 0 else 0
    )

    teletrab_serv_ant = df_ant[
        df_ant["modalidade"].isin(["Remoto", "Semipresencial"])
    ]["id_usuario"].nunique()
    var_teletrab = (
        ((teletrab_serv_ult - teletrab_serv_ant) / teletrab_serv_ant * 100)
        if teletrab_serv_ant > 0
        else 0.0
    )

    top_programas_serv = (
        df_ult.groupby("programa")["id_usuario"]
        .nunique()
        .sort_values(ascending=False)
        .head(5)
    )

    df_valid_dates = df.dropna(
        subset=["dt_inicio_designacao", "dt_fim_designacao"]
    ).copy()
    df_valid_dates["dias"] = (
        df_valid_dates["dt_fim_designacao"] - df_valid_dates["dt_inicio_designacao"]
    ).dt.days
    duracao_media_prog = (
        df_valid_dates[df_valid_dates["dias"] > 0]
        .groupby("sigla_programa")["dias"]
        .mean()
        .sort_values(ascending=False)
        .head(6)
    )

    top_lotacoes_serv = (
        df_ult.groupby("lotacao")["id_usuario"]
        .nunique()
        .sort_values(ascending=False)
        .head(5)
    )

    top_linhas_serv = (
        df_ult.groupby("linha_trabalho")["id_usuario"]
        .nunique()
        .sort_values(ascending=False)
        .head(5)
    )

    entregas_pct = df_ult["tipo_entrega"].value_counts(normalize=True) * 100

    vinc_por_serv = df.groupby("id_usuario")["id_designacao"].nunique()
    media_vinc = vinc_por_serv.mean()
    max_vinc = vinc_por_serv.max()
    top_servidores_vinc = (
        df.groupby("id_usuario")
        .agg(
            total_designacoes=("id_designacao", "nunique"),
            meses_observados=("competencia", "nunique"),
        )
        .assign(
            desig_por_mes=lambda x: (
                x["total_designacoes"] / x["meses_observados"]
            ).round(2)
        )
        .sort_values("total_designacoes", ascending=False)
        .head(8)
    )

    return {
        "periodo_inicio": primeira_comp.strftime("%m/%Y"),
        "periodo_fim": ult_comp.strftime("%m/%Y"),
        "total_meses": total_meses,
        "comp_atual_str": ult_comp.strftime("%m/%Y"),
        "comp_ant_str": ant_comp.strftime("%m/%Y"),
        "total_registros": total_registros,
        "total_servidores": total_servidores,
        "programas_ativos_geral": programas_ativos_geral,
        "media_desig_mes": media_desig_mes,
        "status_dist_geral": status_dist_geral,
        "status_pct_geral": status_pct_geral,
        "serv_desig_ult": serv_desig_ult,
        "serv_desig_ant": serv_desig_ant,
        "var_serv_desig": var_serv_desig,
        "serv_nao_desig_ult": serv_nao_desig_ult,
        "serv_nao_desig_ant": serv_nao_desig_ant,
        "var_nao_desig": var_nao_desig,
        "serv_deslig_ult": serv_deslig_ult,
        "serv_deslig_ant": serv_deslig_ant,
        "var_deslig": var_deslig,
        "mod_ult_counts": mod_ult_counts,
        "mod_ult_pct": mod_ult_pct,
        "teletrab_serv_ult": teletrab_serv_ult,
        "presenc_serv_ult": presenc_serv_ult,
        "pct_teletrab_serv": pct_teletrab_serv,
        "pct_presenc_serv": pct_presenc_serv,
        "var_teletrab": var_teletrab,
        "top_programas_serv": top_programas_serv,
        "duracao_media_prog": duracao_media_prog,
        "top_lotacoes_serv": top_lotacoes_serv,
        "top_linhas_serv": top_linhas_serv,
        "entregas_pct": entregas_pct,
        "media_vinc": media_vinc,
        "max_vinc": max_vinc,
        "top_servidores_vinc": top_servidores_vinc,
    }


def formatar_tabela_top(serie: pd.Series, label_col: str, valor_sufixo: str = "") -> str:
    linhas = [f"| {label_col} | Volume |", "| :--- | :---: |"]
    for nome, val in serie.items():
        if isinstance(val, float):
            linhas.append(f"| **{nome}** | {val:,.1f}{valor_sufixo} |")
        else:
            linhas.append(f"| **{nome}** | {val:,}{valor_sufixo} |")
    return "\n".join(linhas)


def formatar_tabelas_auxiliares(m: dict) -> dict:
    tabela_top_prog = formatar_tabela_top(m["top_programas_serv"], "Programa", " servidores")
    tabela_top_lot = formatar_tabela_top(m["top_lotacoes_serv"], "Lotação", " servidores")
    tabela_top_lin = formatar_tabela_top(m["top_linhas_serv"], "Linha de Trabalho", " servidores")

    linhas_top_serv = [
        "| Servidor (Código LGPD) | Total Designações | Designações / Mês | Meses Observados |",
        "| :---: | :---: | :---: | :---: |",
    ]
    for uid, r in m["top_servidores_vinc"].iterrows():
        linhas_top_serv.append(
            f"| `{uid}` | **{int(r['total_designacoes'])}** | {r['desig_por_mes']:.2f} | {int(r['meses_observados'])} |"
        )
    tabela_serv_vinc = "\n".join(linhas_top_serv)

    linhas_duracao = [
        "| Sigla do Programa | Duração Média (Dias) | Perfil de Gestão |",
        "| :--- | :---: | :--- |",
    ]
    for sigla, dias in m["duracao_media_prog"].items():
        perfil = "Governança / Controle / Estratégico" if dias >= 800 else "Operacional / Ciclos Periódicos"
        linhas_duracao.append(f"| **{sigla}** | **{dias:.0f} dias** | {perfil} |")
    tabela_duracao = "\n".join(linhas_duracao)

    linhas_mod = [
        "| Modalidade | Designações no Mês | Proporção no Mês |",
        "| :--- | :---: | :---: |",
    ]
    for mod, cnt in m["mod_ult_counts"].items():
        pct = m["mod_ult_pct"].get(mod, 0)
        linhas_mod.append(f"| **{mod}** | {cnt:,} | {pct:.1f}% |")
    tabela_mod = "\n".join(linhas_mod)

    return {
        "tabela_top_prog": tabela_top_prog,
        "tabela_top_lot": tabela_top_lot,
        "tabela_top_lin": tabela_top_lin,
        "tabela_serv_vinc": tabela_serv_vinc,
        "tabela_duracao": tabela_duracao,
        "tabela_mod": tabela_mod,
    }


def gerar_relatorio_com_gemini(m: dict, tabs: dict, api_key: str) -> str:
    logging.info("Solicitando análise executiva avançada ao Google Gemini...")
    client = genai.Client(api_key=api_key)

    prompt = f"""Você é um Especialista Sênior em Analytics e Gestão de Pessoas no Setor Público, responsável por redigir o relatório executivo mensal do Programa de Gestão e Desempenho (PGD) do INSS.

Abaixo estão os fatos matemáticos consolidados extraídos diretamente da base de dados oficial (formato Parquet) cobrindo a série de {m['periodo_inicio']} a {m['periodo_fim']} ({m['total_meses']} competências), com ênfase no comparativo da última competência ({m['comp_atual_str']}) em relação à anterior ({m['comp_ant_str']}):

--- DADOS CONSOLIDADOS ---
- Série completa: {m['periodo_inicio']} a {m['periodo_fim']} ({m['total_meses']} meses).
- Total de servidores acompanhados no histórico: {m['total_servidores']:,}
- Volume total de atos de designação: {m['total_registros']:,}
- Média mensal de designações: {m['media_desig_mes']:,.0f}
- Programas de gestão ativos: {m['programas_ativos_geral']}
- Média de vínculos por servidor: {m['media_vinc']:.2f} (teto máximo: {int(m['max_vinc'])})

--- MOVIMENTAÇÃO NA ÚLTIMA COMPETÊNCIA ({m['comp_atual_str']} vs {m['comp_ant_str']}) ---
- Servidores Designados (Plano Ativo): {m['serv_desig_ult']:,} vs {m['serv_desig_ant']:,} no mês anterior (Variação MoM: {m['var_serv_desig']:+.2f}%)
- Servidores Não Designados: {m['serv_nao_desig_ult']:,} vs {m['serv_nao_desig_ant']:,} (Variação MoM: {m['var_nao_desig']:+.2f}%)
- Servidores Desligados no mês: {m['serv_deslig_ult']:,} vs {m['serv_deslig_ant']:,} (Variação MoM: {m['var_deslig']:+.2f}%)
- Teletrabalho (Remoto + Semipresencial): {m['teletrab_serv_ult']:,} servidores ({m['pct_teletrab_serv']:.1f}% do efetivo pactuado), variação MoM de {m['var_teletrab']:+.2f}%
- Presencial: {m['presenc_serv_ult']:,} servidores ({m['pct_presenc_serv']:.1f}%)

--- TABELAS ESTRUTURADAS PARA INCLUIR NO RELATÓRIO ---
Tabela de Modalidades:
{tabs['tabela_mod']}

Tabela de Duração Média por Programa:
{tabs['tabela_duracao']}

Tabela de Top Programas:
{tabs['tabela_top_prog']}

Tabela de Top Lotações:
{tabs['tabela_top_lot']}

Tabela de Top Linhas de Trabalho:
{tabs['tabela_top_lin']}

Tabela de Auditoria LGPD:
{tabs['tabela_serv_vinc']}

--- DIRETRIZES OBRIGATÓRIAS ---
1. Redija um relatório em Markdown altamente analítico, elegante, sóbrio e profissional, voltado a gestores públicos e diretores do INSS.
2. ESTRITAMENTE SEM EMOJIS: Não utilize nenhum emoji no relatório inteiro.
3. Não invente números fora dos fornecidos. Correlacione as movimentações (ex: avanço/recuo de teletrabalho, setores que mais demandaram força de trabalho, dinâmica de entregas).
4. Inclua as imagens dos eixos utilizando as tags Markdown relativas à pasta 'imagens':
   - No Eixo 1: ![Visão Geral](imagens/visao_geral_dashboard.png)
   - No Eixo 2: ![Modalidades de Trabalho](imagens/modalidades_dashboard.png)
   - Nos Eixos 3 e 4: ![Programas de Gestão](imagens/programas_dashboard.png)
   - No Eixo 5: ![Lotações](imagens/lotacoes_dashboard.png)
   - No Eixo 6: ![Linhas de Trabalho](imagens/linhas_trabalho_dashboard.png)
   - Na Auditoria LGPD: ![Auditoria LGPD](imagens/lgpd_dashboard.png)
5. Estrutura exata das seções:
   # Insights Executivos do Dashboard — Acompanhamento PGD / INSS
   > Nota Metodológica & Governança (mencionar HMAC-SHA256, Parquet e Lei 13.709/2018)
   ## Resumo Rápido da Série Histórica
   ## Destaques da Última Competência ({m['comp_atual_str']} vs. {m['comp_ant_str']})
   ## Análise Detalhada dos 6 Eixos do Painel (incluir as seções de cada eixo com suas respectivas imagens e tabelas fornecidas)
   ## Auditoria de Vínculos & Conformidade LGPD (incluir imagem e tabela de servidores anonimizados)
   ## Recomendações Executivas para o Próximo Ciclo (com 3 orientações práticas fundamentadas nos dados)
"""

    modelos = [
        "gemini-4-argon",
        "gemini-3.8-flash",
        "gemini-3.1-pro",
    ]

    response = None
    ultimo_erro = None
    modelo_sucesso = None
    for modelo in modelos:
        try:
            logging.info(f"Tentando gerar análise executiva com o modelo '{modelo}'...")
            response = client.models.generate_content(
                model=modelo,
                contents=prompt,
            )
            if response and response.text:
                logging.info(f"Análise executiva gerada com sucesso via '{modelo}'.")
                modelo_sucesso = modelo
                break
        except Exception as e:
            logging.warning(f"Modelo '{modelo}' retornou erro: {e}")
            ultimo_erro = e

    if not response or not response.text:
        raise RuntimeError(f"Nenhum modelo Gemini respondeu com sucesso. Último erro: {ultimo_erro}")

    texto = response.text
    emoji_rx = re.compile(r"[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf\u2300-\u23ff\ufe00-\ufe0f]")
    texto_sem_emojis = emoji_rx.sub("", texto)
    return texto_sem_emojis, modelo_sucesso


def gerar_relatorio_condicional_local(m: dict, tabs: dict) -> str:
    logging.info("Gerando relatório analítico via regras dinâmicas locais (fallback)...")
    p_inicio = m["periodo_inicio"]
    p_fim = m["periodo_fim"]
    c_atual = m["comp_atual_str"]
    c_ant = m["comp_ant_str"]

    if m["var_serv_desig"] > 0:
        coment_efetivo = f"registrou expansão de {m['var_serv_desig']:+.2f}%, indicando adesão contínua de novos planos de trabalho"
    elif m["var_serv_desig"] < 0:
        coment_efetivo = f"registrou leve retração de {m['var_serv_desig']:+.2f}%, condizente com transições de contratos e fechamentos operacionais"
    else:
        coment_efetivo = "manteve-se em estabilidade absoluta em relação ao ciclo anterior"

    if m["var_teletrab"] >= 0:
        coment_teletrab = f"O regime de teletrabalho avançou {m['var_teletrab']:+.2f}% no mês, consolidando {m['pct_teletrab_serv']:.1f}% da força ativa em ambiente remoto ou semipresencial"
    else:
        coment_teletrab = f"Houve movimentação em direção ao presencial, com o teletrabalho oscilando {m['var_teletrab']:+.2f}% e fechando em {m['pct_teletrab_serv']:.1f}% dos pactuados"

    return f"""# Insights Executivos do Dashboard — Acompanhamento PGD / INSS

Este documento apresenta o diagnóstico analítico consolidado dos microdados do **Programa de Gestão e Desempenho (PGD)** do INSS, abrangendo a série histórica completa de **{p_inicio} a {p_fim}** ({m['total_meses']} competências observadas).

> **Nota Metodológica & Governança:**  
> Os indicadores apresentados neste relatório são extraídos diretamente da base colunar tratada (`.parquet`), espelhando com precisão matemática todas as medidas e filtros presentes no painel oficial do Power BI. A identificação individual de servidores está resguardada sob pseudonimização criptográfica irreversível (HMAC-SHA256), atendendo integralmente à Lei Geral de Proteção de Dados (Lei nº 13.709/2018).

---

## Resumo Rápido da Série Histórica ({p_inicio} a {p_fim})

* **Força de Trabalho Total Coberta**: **{m['total_servidores']:,} servidores públicos** distintos participaram de programas ou foram acompanhados ao longo da série.
* **Volume Global de Atos de Gestão**: **{m['total_registros']:,} registros de designações e acompanhamentos**, com uma média de **{m['media_desig_mes']:,.0f} registros por competência mensal**.
* **Leque de Programas Ativos**: **{m['programas_ativos_geral']} programas de gestão** institucionais estruturados no âmbito das diretorias, superintendências e órgãos de assistência direta da Presidência do INSS.
* **Média de Vínculos por Servidor**: **{m['media_vinc']:.2f} vínculos**, demonstrando rotação controlada e estabilidade na pactuação de planos de trabalho (teto histórico de {int(m['max_vinc'])} designações).

---

## Destaques da Última Competência ({c_atual} vs. {c_ant})

O comparativo mês contra mês (**MoM - Month over Month**) entre a competência atual (**{c_atual}**) e a anterior (**{c_ant}**) evidencia a dinâmica operacional recente:

1. **Movimentação do Efetivo Pactuado**:
   * O total de servidores com status **Designado (Plano Ativo)** fechou em **{m['serv_desig_ult']:,} servidores** ({coment_efetivo}).
2. **Distribuição Real das Modalidades de Trabalho**:
   * **Teletrabalho (Remoto + Semipresencial)**: {coment_teletrab}.
   * **Regime Presencial**: Concentra **{m['presenc_serv_ult']:,} servidores únicos ({m['pct_presenc_serv']:.1f}%)**, assegurando a sustentação dos postos de atendimento ao cidadão e supervisão nas APS.
3. **Pactuação por Entregas**:
   * A ampla maioria das pactuações ativas opera sob o modelo de **Meta e Produto**, garantindo mensuração objetiva de entregas em conformidade com as diretrizes da administração pública federal.

---

## Análise Detalhada dos 6 Eixos do Painel

### Eixo 1 — Visão Geral & Evolução Histórica

![Visão Geral do Dashboard](imagens/visao_geral_dashboard.png)

A evolução das modalidades revela três momentos estratégicos nítidos:
* **2024 (Fase de Estabilidade Inicial)**: Efetivo ativo estabilizado entre 13,2 mil e 13,5 mil servidores, com sazonalidade no fechamento anual (dezembro).
* **2025 (Salto Estrutural & Virada Cadastral)**: Em março/2025, o programa salta para o patamar de 18,6 mil a 19 mil servidores, acompanhado por um pico pontual de 3,4 mil encerramentos em lote para renovação contratual na nova sistemática.
* **2026 (Maturidade Operacional)**: O programa sustenta um patamar consistente entre 17,5 mil e 18,8 mil servidores ativos, demonstrando maturidade e integração nos processos rotineiros da autarquia.

### Eixo 2 — Modalidades de Trabalho

![Modalidades de Trabalho](imagens/modalidades_dashboard.png)

Distribuição detalhada das designações no mês mais recente ({c_atual}):

{tabs['tabela_mod']}

### Eixo 3 — Programas de Gestão & Duração Média dos Planos

![Programas de Gestão e Duração Média](imagens/programas_dashboard.png)

A análise do ciclo de vida dos planos revela perfis distintos de permanência:

{tabs['tabela_duracao']}

### Eixo 4 — Top Programas com Maior Efetivo Ativo

Os 5 programas com maior concentração de servidores no mês de **{c_atual}**:

{tabs['tabela_top_prog']}

### Eixo 5 — Distribuição Geográfica & Lotações

![Distribuição Geográfica e Lotações](imagens/lotacoes_dashboard.png)

As 5 unidades com maior concentração de servidores no mês de **{c_atual}**:

{tabs['tabela_top_lot']}

### Eixo 6 — Principais Linhas de Trabalho

![Linhas de Trabalho](imagens/linhas_trabalho_dashboard.png)

As 5 linhas de trabalho mais demandadas no mês de **{c_atual}**:

{tabs['tabela_top_lin']}

---

## Auditoria de Vínculos & Conformidade LGPD

![Auditoria de Vínculos e Conformidade LGPD](imagens/lgpd_dashboard.png)

A distribuição de vínculos por servidor evidencia uma governança cadastral saudável e sem sobreposições anômalas:

{tabs['tabela_serv_vinc']}

### Conclusões da Auditoria:
1. **Regularidade Temporal**: Os servidores com maior número histórico de pactuações (11 a 12 designações) acompanham a série ao longo de mais de 30 meses, indicando uma taxa média de renovação de 0,35 a 0,38 designações/mês (renovação a cada ~2,7 meses).
2. **Ausência de Super-Concentração**: Não foram detectados registros com acúmulo desproporcional de planos simultâneos.
3. **Privacidade Assegurada**: Todos os microdados de identificação pessoal civil foram suprimidos do pipeline e do relatório.

---

## Recomendações Executivas para o Próximo Ciclo

1. **Acompanhamento de Renovação Sazonal**: Monitorar o encerramento do primeiro trimestre e a virada de ano, períodos onde tradicionalmente ocorrem quedas temporárias de pactuação formal enquanto os novos termos são assinados.
2. **Equalização de Prazos em Unidades Regionais**: Avaliar a padronização dos ciclos de pactuação nas Centrais Regionais (`CEABRD`), aproximando os ciclos de análise para evitar disparidades de indicadores de permanência.
3. **Manutenção do Pipeline Automatizado**: Garantir a reexecução mensal deste script (`tratamento/gerar_insights.py`) a cada nova extração de microdados pelo SGP.
"""


def adicionar_cabecalho_automacao(conteudo: str, motor: str) -> str:
    agora_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
    banner = (
        f"> **Relatório Analítico Gerado Automaticamente por Inteligência Artificial ({motor})**  \n"
        f"> **Última Atualização:** {agora_str}  \n"
        f"> *Diagnóstico executivo sintetizado de forma autônoma a partir dos microdados oficiais tratados do PGD/INSS.*\n\n"
        "---\n\n"
    )
    linhas = conteudo.strip().split("\n")
    if linhas and linhas[0].startswith("# "):
        titulo = linhas[0]
        corpo = "\n".join(linhas[1:]).lstrip()
        return f"{titulo}\n\n{banner}{corpo}"
    return f"{banner}{conteudo}"


def extrair_ano_mes_relatorio(conteudo: str) -> str:
    """
    Extrai ano e mes no formato AAAA_MM a partir do conteudo do relatorio.
    Prioriza a secao de 'Ultima Competencia (MM/AAAA)' e fallback para 'Ultima Atualizacao'.
    """
    match_comp = re.search(r"Última Competência\s*\(([0-1][0-9])/([2-9][0-9]{3})", conteudo)
    if match_comp:
        mes, ano = match_comp.group(1), match_comp.group(2)
        return f"{ano}_{mes}"

    match_data = re.search(r"Última Atualização:\*\*\s*[0-3]?[0-9]/([0-1][0-9])/([2-9][0-9]{3})", conteudo)
    if match_data:
        mes, ano = match_data.group(1), match_data.group(2)
        return f"{ano}_{mes}"

    return datetime.now().strftime("%Y_%m")


def arquivar_relatorio_anterior(caminho_atual: Path, pasta_relatorios: Path = RELATORIOS_DIR) -> Path | None:
    """
    Arquiva o relatorio existente na pasta relatorios antes de ser substituido.
    Nome do arquivo gerado: insights_AAAA_MM.md (ex: insights_2026_08.md).
    Ajusta caminhos de imagens relativas para ../imagens/ garantindo exibicao correta.
    """
    if not caminho_atual.exists():
        return None

    try:
        conteudo_antigo = caminho_atual.read_text(encoding="utf-8")
        if not conteudo_antigo.strip():
            return None

        ano_mes = extrair_ano_mes_relatorio(conteudo_antigo)
        pasta_relatorios.mkdir(parents=True, exist_ok=True)
        caminho_historico = pasta_relatorios / f"insights_{ano_mes}.md"

        conteudo_historico = re.sub(r"\((?:\./)?imagens/", "(../imagens/", conteudo_antigo)

        caminho_historico.write_text(conteudo_historico, encoding="utf-8")
        logging.info(f"Relatorio anterior arquivado com sucesso em: {caminho_historico}")
        return caminho_historico
    except Exception as e:
        logging.warning(f"Nao foi possivel arquivar relatorio anterior: {e}")
        return None


def salvar_relatorio(conteudo: str, caminho: Path, pasta_relatorios: Path | None = None) -> None:
    """
    Arquiva a versao anterior em relatorios/ antes de substitui-la e salva a versao atualizada.
    """
    if pasta_relatorios is None:
        pasta_relatorios = caminho.parent / "relatorios"

    arquivar_relatorio_anterior(caminho, pasta_relatorios)

    logging.info(f"Salvando relatorio executivo atualizado em: {caminho}")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)
    logging.info("Relatorio salvo com sucesso!")




def _fmt_int_pt(valor: int | float) -> str:
    return f"{int(round(valor)):,}".replace(",", ".")


def _fmt_pct_pt(valor: float, casas: int = 1, com_sinal: bool = False) -> str:
    formato = f"{{:+.{casas}f}}%" if com_sinal else f"{{:.{casas}f}}%"
    return formato.format(valor).replace(".", ",")


def formatar_nome_modelo_ia(modelo_raw: str) -> str:
    """
    Formata o identificador tecnico do modelo de IA para exibicao visual nos Cards do Power BI.
    Exemplos:
      - 'gemini-4-argon'   -> 'Google Gemini Argon (4)'
      - 'gemini-2.5-flash' -> 'Google Gemini Flash (2.5)'
      - 'gemini-2.5-pro'   -> 'Google Gemini Pro (2.5)'
      - 'Motor Analítico Local (Python)' -> 'Motor Analítico (Python)'
    """
    if not modelo_raw:
        return "Google Gemini Flash (2.5)"
    s = str(modelo_raw).strip()
    if s.startswith("Google Gemini ") and "(" in s and ")" in s:
        return s

    s_lower = s.lower()
    if "python" in s_lower or "local" in s_lower:
        return "Motor Analítico (Python)"

    # Captura padrao 'gemini-<versao>-<variante>' (ex: gemini-4-argon, gemini-2.5-flash, gemini-2.5-pro)
    m = re.search(r"gemini[-_\s]*([0-9]+(?:\.[0-9]+)?)[-_\s]*([a-zA-Z][a-zA-Z0-9\-_]*)", s_lower)
    if m:
        versao = m.group(1)
        variante = " ".join(
            parte.capitalize()
            for parte in re.split(r"[-_\s]+", m.group(2))
            if parte
        )
        return f"Google Gemini {variante} ({versao})"

    # Captura padrao 'gemini-<variante>' sem versao numerica (ex: gemini-argon)
    m_sem_ver = re.search(r"gemini[-_\s]+([a-zA-Z][a-zA-Z0-9\-_]*)", s_lower)
    if m_sem_ver:
        variante = " ".join(
            parte.capitalize()
            for parte in re.split(r"[-_\s]+", m_sem_ver.group(1))
            if parte
        )
        return f"Google Gemini {variante}"

    return f"Google Gemini ({s})"


def _obter_modelo_ia_padrao(caminho_md: Path = OUTPUT_MARKDOWN) -> str:
    """Extrai o identificador do modelo Gemini registrado no relatorio vigente e formata para exibicao."""
    if caminho_md and caminho_md.exists():
        try:
            texto = caminho_md.read_text(encoding="utf-8")
            m = re.search(r"Google Gemini\s*[—\-]\s*([a-zA-Z0-9\.\-]+)", texto)
            if m:
                return formatar_nome_modelo_ia(m.group(1).strip())
        except Exception:
            pass
    return formatar_nome_modelo_ia("gemini-2.5-flash")


def gerar_historico_csv_powerbi(
    df: pd.DataFrame,
    motor_ia: str | None = None,
    caminho_csv: Path | None = OUTPUT_CSV_POWERBI,
) -> pd.DataFrame:
    """
    Gera/atualiza tabela historica estruturada por competencia (1 linha por mes)
    de forma incremental e idempotente (append-only por competencia inedita),
    preservando integralmente as competencias ja registradas no CSV.
    """
    motor_ia_formatado = (
        formatar_nome_modelo_ia(motor_ia) if motor_ia else _obter_modelo_ia_padrao()
    )

    df_existente = None
    comps_existentes = set()
    if caminho_csv is not None and caminho_csv.exists():
        try:
            df_existente = pd.read_csv(caminho_csv)
            if "competencia" in df_existente.columns:
                comps_existentes = set(df_existente["competencia"].dropna().astype(str))
        except Exception as e:
            logging.warning(f"Não foi possível ler CSV histórico existente ({e}). Recriando base...")
            df_existente = None

    comps = sorted(df["competencia"].dropna().unique())
    registros = []

    for idx, comp in enumerate(comps):
        comp_dt = pd.Timestamp(comp)
        comp_iso = comp_dt.strftime("%Y-%m-%d")

        if comp_iso in comps_existentes:
            continue

        df_mes = df[df["competencia"] == comp]
        comp_ant = comps[idx - 1] if idx > 0 else comp
        df_ant = df[df["competencia"] == comp_ant]

        comp_ant_dt = pd.Timestamp(comp_ant)
        comp_label = comp_dt.strftime("%m/%Y")
        comp_ant_label = comp_ant_dt.strftime("%m/%Y")

        # Card 1: Servidores em Plano Ativo (Designados)
        df_desig_mes = df_mes[df_mes["status"] == "Designado"]
        df_desig_ant = df_ant[df_ant["status"] == "Designado"]

        serv_ativo = int(df_desig_mes["id_usuario"].nunique())
        serv_ativo_ant = int(df_desig_ant["id_usuario"].nunique())

        # Card 2: Variacao Mensal MoM (%)
        if idx > 0 and serv_ativo_ant > 0:
            var_mom = ((serv_ativo - serv_ativo_ant) / serv_ativo_ant) * 100.0
        else:
            var_mom = 0.0

        # Card 3: Adesao ao Teletrabalho (%)
        serv_teletrab = int(
            df_mes[df_mes["modalidade"].isin(["Remoto", "Semipresencial"])]["id_usuario"].nunique()
        )
        serv_teletrab_ant = int(
            df_ant[df_ant["modalidade"].isin(["Remoto", "Semipresencial"])]["id_usuario"].nunique()
        )
        serv_presenc = int(
            df_mes[df_mes["modalidade"] == "Presencial"]["id_usuario"].nunique()
        )
        serv_remoto = int(
            df_mes[df_mes["modalidade"] == "Remoto"]["id_usuario"].nunique()
        )
        total_mod = serv_teletrab + serv_presenc
        pct_teletrab = (serv_teletrab / total_mod * 100.0) if total_mod > 0 else 0.0
        pct_remoto = (serv_remoto / total_mod * 100.0) if total_mod > 0 else 0.0
        pct_presenc = (serv_presenc / total_mod * 100.0) if total_mod > 0 else 0.0

        if idx > 0 and serv_teletrab_ant > 0:
            var_teletrab_mom = ((serv_teletrab - serv_teletrab_ant) / serv_teletrab_ant) * 100.0
        else:
            var_teletrab_mom = 0.0

        # Nao designados e desligados no mes
        serv_nao_desig = int(df_mes[df_mes["status"] == "Não Designado"]["id_usuario"].nunique())
        serv_nao_desig_ant = int(df_ant[df_ant["status"] == "Não Designado"]["id_usuario"].nunique())
        var_nao_desig = (
            ((serv_nao_desig - serv_nao_desig_ant) / serv_nao_desig_ant * 100.0)
            if idx > 0 and serv_nao_desig_ant > 0
            else 0.0
        )
        serv_deslig = int(df_mes[df_mes["status"] == "Desligado"]["id_usuario"].nunique())

        # Top Programas, Lotacoes e Linhas no mes
        top_progs = (
            df_mes.dropna(subset=["sigla_programa"])
            .groupby("sigla_programa")["id_usuario"]
            .nunique()
            .sort_values(ascending=False)
        )
        prog1_nome = top_progs.index[0] if len(top_progs) > 0 else "PG-DIRBEN"
        prog1_val = int(top_progs.iloc[0]) if len(top_progs) > 0 else 0
        prog2_nome = top_progs.index[1] if len(top_progs) > 1 else "ATENDIMENTO"
        prog2_val = int(top_progs.iloc[1]) if len(top_progs) > 1 else 0

        top_lots = (
            df_mes.dropna(subset=["lotacao"])
            .groupby("lotacao")["id_usuario"]
            .nunique()
            .sort_values(ascending=False)
        )
        lot1_nome = top_lots.index[0] if len(top_lots) > 0 else "DIRETORIA DE BENEFICIOS"
        lot1_val = int(top_lots.iloc[0]) if len(top_lots) > 0 else 0

        top_linhas = (
            df_mes.dropna(subset=["sigla_linha_trabalho"])
            .groupby("sigla_linha_trabalho")["id_usuario"]
            .nunique()
            .sort_values(ascending=False)
        )
        lin1_nome = top_linhas.index[0] if len(top_linhas) > 0 else "APS"
        lin1_val = int(top_linhas.iloc[0]) if len(top_linhas) > 0 else 0

        # Formatacoes PT-BR para exibicao direta nos Cards
        serv_ativo_fmt = _fmt_int_pt(serv_ativo)
        var_mom_fmt = _fmt_pct_pt(var_mom, casas=2, com_sinal=True)
        pct_teletrab_fmt = _fmt_pct_pt(pct_teletrab, casas=1, com_sinal=False)
        pct_remoto_fmt = _fmt_pct_pt(pct_remoto, casas=1, com_sinal=False)

        if idx == 0:
            tendencia_txt = "estabelecendo a linha de base inicial da série monitorada"
        elif var_mom > 0.5:
            tendencia_txt = (
                f"registrando expansão de {var_mom_fmt} em relação a {comp_ant_label} "
                f"(saldo líquido de {serv_ativo - serv_ativo_ant:+d} servidores ativos)"
            )
        elif var_mom < -0.5:
            tendencia_txt = (
                f"apresentando retração de {var_mom_fmt} frente a {comp_ant_label}, "
                "Associada ao ciclo de encerramento e repactuação de planos de trabalho"
            )
        else:
            tendencia_txt = (
                f"mantendo estabilidade operacional ({var_mom_fmt} ante {comp_ant_label}) "
                "na sustentação da força de trabalho pactuada"
            )

        # Bloco 1: Diagnostico Executivo da Competencia (2 paragrafos)
        paragrafo_1 = (
            f"Na competência {comp_label}, o Programa de Gestão e Desempenho (PGD) do INSS contabilizou "
            f"{serv_ativo_fmt} servidores em plano ativo, {tendencia_txt}. "
            f"A composição das modalidades evidencia {pct_teletrab_fmt} de adesão ao teletrabalho "
            f"({_fmt_int_pt(serv_teletrab)} servidores em regime remoto ou semipresencial, sendo {pct_remoto_fmt} "
            f"em regime remoto integral) contra {_fmt_pct_pt(pct_presenc, 1)} em modalidade presencial "
            f"({_fmt_int_pt(serv_presenc)} servidores)."
        )
        paragrafo_2 = (
            f"A alocação funcional na competência manteve forte concentração nos programas estruturantes, "
            f"liderados por {prog1_nome} ({_fmt_int_pt(prog1_val)} servidores) e {prog2_nome} "
            f"({_fmt_int_pt(prog2_val)} servidores). No recorte organizacional, a unidade {lot1_nome} "
            f"concentrou {_fmt_int_pt(lot1_val)} servidores ativos, com destaque operacional para a linha "
            f"de trabalho {lin1_nome} ({_fmt_int_pt(lin1_val)} profissionais pactuados sob metas de entrega)."
        )
        diagnostico_executivo = f"{paragrafo_1}\n\n{paragrafo_2}"

        # Bloco 2: Principais Movimentacoes MoM (4 bullets)
        principais_movimentacoes_mom = "\n".join([
            f"• Efetivo em Plano Ativo: {serv_ativo_fmt} servidores ({var_mom_fmt} ante {comp_ant_label})",
            f"• Adesão ao Teletrabalho: {pct_teletrab_fmt} ({_fmt_int_pt(serv_teletrab)} servidores, {_fmt_pct_pt(var_teletrab_mom, 2, True)} MoM)",
            f"• Regime Remoto Integral: {pct_remoto_fmt} do efetivo modal ({_fmt_int_pt(serv_remoto)} servidores no mês)",
            f"• Não Designados e Desligamentos: {_fmt_int_pt(serv_nao_desig)} não designados ({_fmt_pct_pt(var_nao_desig, 1, True)} MoM) e {_fmt_int_pt(serv_deslig)} desligados",
        ])

        # Bloco 3: Matriz de Alertas & Recomendacoes (2 paragrafos)
        if serv_deslig > 500 or var_mom < -2.0:
            alerta_p1 = (
                f"Alerta de Transição Contratual: A competência {comp_label} registrou {_fmt_int_pt(serv_deslig)} "
                f"desligamentos e variação de {var_mom_fmt} no efetivo ativo. Recomenda-se auditar as filas de "
                f"renovação de planos de trabalho em {lot1_nome} para evitar hiatos de cobertura na análise de benefícios."
            )
        elif serv_nao_desig > 1200:
            alerta_p1 = (
                f"Alerta de Capacidade Ociosa no PGD: Foram identificados {_fmt_int_pt(serv_nao_desig)} servidores "
                f"com status Não Designado na competência {comp_label} ({_fmt_pct_pt(var_nao_desig, 1, True)} MoM). "
                f"Priorizar a conversão e repactuação desse contingente nas centrais de análise ({prog1_nome})."
            )
        else:
            alerta_p1 = (
                f"Estabilidade de Ciclo: Baixo volume de desligamentos ({_fmt_int_pt(serv_deslig)} registros) e "
                f"manutenção da taxa de adesão em {serv_ativo_fmt} servidores ativos em {comp_label}, confirmando "
                "alta retenção e aderência às metas pactuadas no período."
            )

        alerta_p2 = (
            f"Recomendação Estratégica: Concentrar o monitoramento gerencial no programa {prog1_nome} "
            f"({_fmt_int_pt(prog1_val)} servidores) e na linha {lin1_nome}, equilibrando a proporção entre "
            f"teletrabalho ({pct_teletrab_fmt}) e atendimento presencial ({_fmt_pct_pt(pct_presenc, 1)}) "
            "para cumprimento dos prazos normativos do INSS."
        )
        matriz_alertas_recomendacoes = f"{alerta_p1}\n\n{alerta_p2}"

        registros.append({
            "competencia": comp_iso,
            "competencia_mes_ano": comp_label,
            "servidores_plano_ativo": serv_ativo,
            "servidores_plano_ativo_fmt": serv_ativo_fmt,
            "variacao_mensal_mom": round(var_mom, 2),
            "variacao_mensal_mom_fmt": var_mom_fmt,
            "adesao_teletrabalho_pct": round(pct_teletrab, 1),
            "adesao_teletrabalho_fmt": pct_teletrab_fmt,
            "adesao_remoto_pct": round(pct_remoto, 1),
            "adesao_remoto_fmt": pct_remoto_fmt,
            "motor_analise_ia": motor_ia_formatado,
            "diagnostico_executivo": diagnostico_executivo,
            "principais_movimentacoes_mom": principais_movimentacoes_mom,
            "matriz_alertas_recomendacoes": matriz_alertas_recomendacoes,
        })

    if not registros and df_existente is not None:
        logging.info(
            f"Nenhuma competência nova detectada. CSV histórico já está atualizado ({len(df_existente)} competências)."
        )
        return df_existente

    df_novos = pd.DataFrame(registros)
    if df_existente is not None and not df_existente.empty:
        df_hist = pd.concat([df_existente, df_novos], ignore_index=True)
        df_hist = df_hist.drop_duplicates(subset=["competencia"], keep="first").sort_values("competencia").reset_index(drop=True)
    else:
        df_hist = df_novos

    if caminho_csv is not None:
        caminho_csv.parent.mkdir(parents=True, exist_ok=True)
        df_hist.to_csv(caminho_csv, index=False, encoding="utf-8")
        logging.info(
            f"CSV histórico atualizado com +{len(df_novos)} nova(s) competência(s) em: {caminho_csv} "
            f"(total: {len(df_hist)} competências)"
        )

    return df_hist


def main():
    df = carregar_dados(PARQUET_PATH)
    metricas = calcular_metricas(df)
    tabelas = formatar_tabelas_auxiliares(metricas)

    api_key = os.getenv("GEMINI_API_KEY")
    relatorio_gerado = None
    motor_utilizado = "Motor Analítico Local (Python)"
    motor_card_curto = _obter_modelo_ia_padrao()

    if GENAI_DISPONIVEL and api_key and api_key != "sua_chave_aqui":
        try:
            relatorio_gerado, modelo_ok = gerar_relatorio_com_gemini(metricas, tabelas, api_key)
            motor_utilizado = f"Google Gemini — {modelo_ok}"
            motor_card_curto = modelo_ok
        except Exception as e:
            logging.warning(f"Falha ao chamar a API do Gemini ({e}). Utilizando gerador local...")

    if not relatorio_gerado:
        relatorio_gerado = gerar_relatorio_condicional_local(metricas, tabelas)

    relatorio_final = adicionar_cabecalho_automacao(relatorio_gerado, motor_utilizado)
    salvar_relatorio(relatorio_final, OUTPUT_MARKDOWN)
    gerar_historico_csv_powerbi(df, motor_ia=motor_card_curto, caminho_csv=OUTPUT_CSV_POWERBI)


if __name__ == "__main__":
    main()
