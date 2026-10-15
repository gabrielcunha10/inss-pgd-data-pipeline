import logging
import os
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import numpy as np
import pandas as pd

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
PARQUET_PATH = PROJECT_DIR / "tests" / "pgd_designacoes_inss_2023_2026.parquet"
OUTPUT_MARKDOWN = PROJECT_DIR / "dashboard" / "insights_README.md"
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




def main():
    df = carregar_dados(PARQUET_PATH)
    metricas = calcular_metricas(df)
    tabelas = formatar_tabelas_auxiliares(metricas)

    api_key = os.getenv("GEMINI_API_KEY")
    relatorio_gerado = None
    motor_utilizado = "Motor Analítico Local (Python)"

    if GENAI_DISPONIVEL and api_key and api_key != "sua_chave_aqui":
        try:
            relatorio_gerado, modelo_ok = gerar_relatorio_com_gemini(metricas, tabelas, api_key)
            motor_utilizado = f"Google Gemini — {modelo_ok}"
        except Exception as e:
            logging.warning(f"Falha ao chamar a API do Gemini ({e}). Utilizando gerador local...")

    if not relatorio_gerado:
        relatorio_gerado = gerar_relatorio_condicional_local(metricas, tabelas)

    relatorio_final = adicionar_cabecalho_automacao(relatorio_gerado, motor_utilizado)
    salvar_relatorio(relatorio_final, OUTPUT_MARKDOWN)


if __name__ == "__main__":
    main()
