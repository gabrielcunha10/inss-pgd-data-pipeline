import hashlib
import re
import sys
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tratamento.gerar_insights import (
    calcular_metricas,
    formatar_tabelas_auxiliares,
    formatar_nome_modelo_ia,
    gerar_relatorio_condicional_local,
    gerar_historico_csv_powerbi,
    salvar_relatorio,
    gerar_relatorio_com_gemini,
    adicionar_cabecalho_automacao,
    carregar_dados,
    main as gerar_insights_main,
    extrair_ano_mes_relatorio,
    arquivar_relatorio_anterior,
    RELATORIOS_DIR,
    OUTPUT_CSV_POWERBI,
)
from unittest.mock import MagicMock, patch
from dashboard.capturar_prints import (
    PAGINAS,
    IMAGENS_DIR,
    garantir_pagina_inicial,
    navegar_para_pagina,
    avancar_proxima_pagina,
    capturar_todas_as_paginas,
    atualizar_timestamp_dashboard_readme,
)



def test_funcao_calculo_metricas_mom():
    datas_mes1 = pd.to_datetime(["2026-07-01"] * 4)
    datas_mes2 = pd.to_datetime(["2026-08-01"] * 5)

    df_metricas = pd.DataFrame({
        "competencia": list(datas_mes1) + list(datas_mes2),
        "id_usuario": [
            "USR-0001", "USR-0002", "USR-0003", "USR-0004",
            "USR-0001", "USR-0002", "USR-0003", "USR-0004", "USR-0005"
        ],
        "id_designacao": [1, 2, 3, 4, 1, 2, 3, 4, 5],
        "status": [
            "Designado", "Designado", "Não Designado", "Desligado",
            "Designado", "Designado", "Designado", "Não Designado", "Desligado"
        ],
        "modalidade": [
            "Remoto", "Presencial", None, None,
            "Remoto", "Semipresencial", "Presencial", None, None
        ],
        "flag_pgd": ["Sim"] * 9,
        "programa": ["PG-DIRBEN"] * 9,
        "sigla_programa": ["PG-DIRBEN"] * 9,
        "lotacao": ["GEX BRASILIA"] * 9,
        "linha_trabalho": ["LINHA 1"] * 9,
        "tipo_entrega": ["Meta e Produto"] * 9,
        "dt_inicio_designacao": pd.to_datetime(["2026-01-01"] * 9),
        "dt_fim_designacao": pd.to_datetime(["2026-12-31"] * 9),
    })

    m = calcular_metricas(df_metricas)

    assert m["serv_desig_ant"] == 2
    assert m["serv_desig_ult"] == 3
    assert m["var_serv_desig"] == 50.0

    assert m["teletrab_serv_ult"] == 2
    assert m["presenc_serv_ult"] == 1
    assert pytest.approx(m["pct_teletrab_serv"], 0.1) == 66.7
    assert pytest.approx(m["pct_presenc_serv"], 0.1) == 33.3


def test_funcao_formatar_tabelas_auxiliares():
    df_mini = pd.DataFrame({
        "competencia": pd.to_datetime(["2026-07-01", "2026-08-01", "2026-08-01"]),
        "id_usuario": ["USR-01", "USR-01", "USR-02"],
        "id_designacao": [1, 1, 2],
        "status": ["Designado", "Designado", "Designado"],
        "modalidade": ["Remoto", "Remoto", "Presencial"],
        "flag_pgd": ["Sim", "Sim", "Sim"],
        "programa": ["PG-DIRBEN", "PG-DIRBEN", "CEAB1"],
        "sigla_programa": ["DIRBEN", "DIRBEN", "CEAB1"],
        "lotacao": ["GEX BRASILIA", "GEX BRASILIA", "GEX SP"],
        "linha_trabalho": ["LINHA 1", "LINHA 1", "LINHA 2"],
        "tipo_entrega": ["Meta e Produto", "Meta e Produto", "Meta e Produto"],
        "dt_inicio_designacao": pd.to_datetime(["2026-01-01"] * 3),
        "dt_fim_designacao": pd.to_datetime(["2026-12-31"] * 3),
    })

    metricas = calcular_metricas(df_mini)
    tabelas = formatar_tabelas_auxiliares(metricas)

    chaves_esperadas = {
        "tabela_top_prog",
        "tabela_top_lot",
        "tabela_top_lin",
        "tabela_serv_vinc",
        "tabela_duracao",
        "tabela_mod",
    }
    assert chaves_esperadas.issubset(tabelas.keys()), f"Faltam tabelas auxiliares: {chaves_esperadas - set(tabelas.keys())}"

    for chave, conteudo in tabelas.items():
        assert isinstance(conteudo, str), f"A tabela '{chave}' deve ser uma string Markdown."
        assert "|" in conteudo, f"A tabela '{chave}' não possui delimitadores Markdown '|'."


def test_funcao_gerar_relatorio_condicional_local():
    df_mini = pd.DataFrame({
        "competencia": pd.to_datetime(["2026-07-01", "2026-08-01"]),
        "id_usuario": ["USR-01", "USR-02"],
        "id_designacao": [1, 2],
        "status": ["Designado", "Designado"],
        "modalidade": ["Remoto", "Presencial"],
        "flag_pgd": ["Sim", "Sim"],
        "programa": ["PG-DIRBEN", "CEAB1"],
        "sigla_programa": ["DIRBEN", "CEAB1"],
        "lotacao": ["GEX BRASILIA", "GEX SP"],
        "linha_trabalho": ["LINHA 1", "LINHA 2"],
        "sigla_linha_trabalho": ["LINHA 1", "LINHA 2"],
        "tipo_entrega": ["Meta e Produto", "Meta e Produto"],
        "dt_inicio_designacao": pd.to_datetime(["2026-01-01"] * 2),
        "dt_fim_designacao": pd.to_datetime(["2026-12-31"] * 2),
    })

    metricas = calcular_metricas(df_mini)
    tabelas = formatar_tabelas_auxiliares(metricas)
    relatorio = gerar_relatorio_condicional_local(metricas, tabelas)

    assert "# Insights Executivos do Dashboard" in relatorio
    assert "Nota Metodológica & Governança" in relatorio
    assert "imagens/visao_geral_dashboard.png" in relatorio
    assert "imagens/modalidades_dashboard.png" in relatorio
    assert "imagens/programas_dashboard.png" in relatorio
    assert "imagens/lotacoes_dashboard.png" in relatorio
    assert "imagens/linhas_trabalho_dashboard.png" in relatorio
    assert "imagens/lgpd_dashboard.png" in relatorio
    assert "Recomendações Executivas para o Próximo Ciclo" in relatorio


def test_funcao_salvar_relatorio(tmp_path):
    caminho_teste = tmp_path / "subdiretorio" / "relatorio_teste.md"
    conteudo_teste = "# Relatório de Teste\nConteúdo executivo UTF-8 com acentuação: Atenção, Açúcar, Gestão."

    salvar_relatorio(conteudo_teste, caminho_teste)

    assert caminho_teste.exists(), "O arquivo de relatório não foi criado no destino informado."
    conteudo_lido = caminho_teste.read_text(encoding="utf-8")
    assert conteudo_lido == conteudo_teste, "Conteúdo gravado difere do original ou teve corrupção de encoding."


def test_configuracao_paginas_prints():
    assert len(PAGINAS) == 9, f"Esperava 9 páginas cadastradas no dashboard, mas foram encontradas {len(PAGINAS)}."
    ordens = [p["ordem"] for p in PAGINAS]
    assert ordens == list(range(1, 10)), f"A numeração de ordem das páginas deve ser estritamente de 1 a 9: {ordens}"

    arquivos = [p["arquivo"] for p in PAGINAS]
    assert len(arquivos) == len(set(arquivos)), "Existem nomes de arquivo duplicados no mapeamento de páginas."
    for arq in arquivos:
        assert arq.endswith(".png"), f"O arquivo '{arq}' deve ter extensão '.png'."


def test_existencia_e_integridade_prints_dashboard():
    cabecalho_png_magico = b"\x89PNG\r\n\x1a\n"

    for p in PAGINAS:
        caminho_img = IMAGENS_DIR / p["arquivo"]
        assert caminho_img.exists(), f"A captura da página '{p['nome']}' ({p['arquivo']}) não foi encontrada em '{IMAGENS_DIR}'."

        tamanho_bytes = caminho_img.stat().st_size
        assert tamanho_bytes > 10000, f"A imagem '{p['arquivo']}' tem apenas {tamanho_bytes} bytes e parece corrompida ou vazia."

        with open(caminho_img, "rb") as f:
            header = f.read(8)
            assert header == cabecalho_png_magico, f"O arquivo '{p['arquivo']}' não é um PNG binário válido (cabeçalho inválido)."


def test_consistencia_imagens_referenciadas_nos_readmes():
    readmes = [
        PROJECT_ROOT / "dashboard" / "insights_README.md",
        PROJECT_ROOT / "dashboard" / "dashboard_README.md",
    ]
    if RELATORIOS_DIR.exists():
        readmes.extend(list(RELATORIOS_DIR.glob("insights_*.md")))

    for caminho_readme in readmes:
        assert caminho_readme.exists(), f"Arquivo de documentação não encontrado: {caminho_readme}"
        texto = caminho_readme.read_text(encoding="utf-8")

        referencias = re.findall(r"(?:(?:\.\./)?imagens/)([a-zA-Z0-9_\-]+\.(?:png|svg))", texto)
        assert len(referencias) > 0, f"Nenhuma imagem encontrada em {caminho_readme.name}"

        for ref in referencias:
            alvo = IMAGENS_DIR / ref
            assert alvo.exists(), (
                f"Link quebrado detectado em '{caminho_readme.name}': a imagem '{ref}' "
                f"não existe em '{IMAGENS_DIR}'."
            )


def test_extracao_ano_mes_relatorio():
    conteudo_teste_comp = "## Destaques da Última Competência (08/2026 vs. 07/2026)"
    assert extrair_ano_mes_relatorio(conteudo_teste_comp) == "2026_08"

    conteudo_teste_data = "> **Última Atualização:** 14/10/2026 às 22:42"
    assert extrair_ano_mes_relatorio(conteudo_teste_data) == "2026_10"


def test_arquivamento_relatorio_anterior(tmp_path):
    origem = tmp_path / "insights_README.md"
    origem.write_text(
        "# Relatorio\n## Destaques da Última Competência (05/2025 vs. 04/2025)\n![Grafico](imagens/visao_geral.png)",
        encoding="utf-8",
    )
    pasta_relatorios = tmp_path / "relatorios"

    caminho_gerado = arquivar_relatorio_anterior(origem, pasta_relatorios)
    assert caminho_gerado is not None
    assert caminho_gerado.exists()
    assert caminho_gerado.name == "insights_2025_05.md"

    conteudo_arquivado = caminho_gerado.read_text(encoding="utf-8")
    assert "(../imagens/visao_geral.png)" in conteudo_arquivado


def test_existencia_relatorios_historicos():
    assert RELATORIOS_DIR.exists(), f"Pasta de relatórios históricos '{RELATORIOS_DIR}' não existe."
    arquivos_relatorios = list(RELATORIOS_DIR.glob("insights_*.md"))
    assert len(arquivos_relatorios) > 0, "Nenhum relatório histórico encontrado em dashboard/relatorios/."


def test_unicidade_prints_dashboard():
    hashes_vistos = {}
    for p in PAGINAS:
        caminho_img = IMAGENS_DIR / p["arquivo"]
        assert caminho_img.exists(), f"A imagem '{p['arquivo']}' não foi encontrada."

        digest = hashlib.sha256(caminho_img.read_bytes()).hexdigest()
        assert digest not in hashes_vistos.values(), (
            f"Falha de navegação detectada: a imagem '{p['arquivo']}' é idêntica a "
            f"'{[k for k, v in hashes_vistos.items() if v == digest][0]}' (print duplicado)."
        )
        hashes_vistos[p["arquivo"]] = digest


def test_gerar_historico_csv_powerbi(tmp_path):
    df_mini = pd.DataFrame({
        "competencia": pd.to_datetime(["2026-07-01", "2026-07-01", "2026-08-01", "2026-08-01"]),
        "id_usuario": ["USR-01", "USR-02", "USR-01", "USR-03"],
        "id_designacao": [1, 2, 1, 3],
        "status": ["Designado", "Não Designado", "Designado", "Designado"],
        "modalidade": ["Remoto", None, "Remoto", "Presencial"],
        "flag_pgd": ["Sim", None, "Sim", "Sim"],
        "programa": ["CEAB1", None, "CEAB1", "SR_PGD"],
        "sigla_programa": ["CEAB1", None, "CEAB1", "SR_PGD"],
        "lotacao": ["GEX SP", "GEX SP", "GEX SP", "GEX RJ"],
        "linha_trabalho": ["APS_SRNE", "APS_SRNE", "APS_SRNE", "APS_SRSE"],
        "sigla_linha_trabalho": ["APS_SRNE", "APS_SRNE", "APS_SRNE", "APS_SRSE"],
        "tipo_entrega": ["Meta e Produto", None, "Meta e Produto", "Meta e Produto"],
        "dt_inicio_designacao": pd.to_datetime(["2026-01-01"] * 4),
        "dt_fim_designacao": pd.to_datetime(["2026-12-31"] * 4),
    })

    csv_temp = tmp_path / "insights_historico_powerbi.csv"
    # 1a execucao: apenas competencia 07/2026 com Flash (2.5)
    df_jul = df_mini[df_mini["competencia"] == pd.Timestamp("2026-07-01")]
    df_hist_1 = gerar_historico_csv_powerbi(df_jul, motor_ia="gemini-2.5-flash", caminho_csv=csv_temp)
    assert len(df_hist_1) == 1
    assert df_hist_1["motor_analise_ia"].iloc[0] == "Google Gemini Flash (2.5)"

    # 2a execucao: base com 07/2026 e 08/2026 usando Argon (4) -> deve preservar 07/2026 intacta e criar so 08/2026
    df_hist = gerar_historico_csv_powerbi(df_mini, motor_ia="gemini-4-argon", caminho_csv=csv_temp)

    assert formatar_nome_modelo_ia("gemini-4-argon") == "Google Gemini Argon (4)"
    assert formatar_nome_modelo_ia("gemini-2.5-flash") == "Google Gemini Flash (2.5)"
    assert formatar_nome_modelo_ia("gemini-2.5-pro") == "Google Gemini Pro (2.5)"
    assert formatar_nome_modelo_ia("Motor Analítico Local (Python)") == "Motor Analítico (Python)"

    assert csv_temp.exists()
    assert len(df_hist) == 2
    mapa_motores = df_hist.set_index("competencia")["motor_analise_ia"].to_dict()
    assert mapa_motores["2026-07-01"] == "Google Gemini Flash (2.5)", "Competencia antiga deve ser preservada."
    assert mapa_motores["2026-08-01"] == "Google Gemini Argon (4)", "Apenas a nova competencia recebe o novo modelo."

    # 3a execucao repetida: idempotencia total (nenhuma linha duplicada)
    df_hist_rep = gerar_historico_csv_powerbi(df_mini, motor_ia="gemini-2.5-pro", caminho_csv=csv_temp)
    assert len(df_hist_rep) == 2
    assert df_hist_rep.set_index("competencia")["motor_analise_ia"].to_dict() == mapa_motores
    colunas_esperadas = {
        "competencia",
        "competencia_mes_ano",
        "servidores_plano_ativo",
        "servidores_plano_ativo_fmt",
        "variacao_mensal_mom",
        "variacao_mensal_mom_fmt",
        "adesao_teletrabalho_pct",
        "adesao_teletrabalho_fmt",
        "motor_analise_ia",
        "diagnostico_executivo",
        "principais_movimentacoes_mom",
        "matriz_alertas_recomendacoes",
    }
    assert colunas_esperadas.issubset(set(df_hist.columns))
    assert OUTPUT_CSV_POWERBI.exists(), "O arquivo oficial dashboard/insights_historico_powerbi.csv deve existir."


def test_garantir_pagina_inicial():
    page = MagicMock()
    indicador = MagicMock()
    indicador.is_visible.return_value = True
    indicador.inner_text.return_value = "3 de 9"
    page.locator.side_effect = lambda sel, **kwargs: indicador if "middleText" in sel else MagicMock()
    garantir_pagina_inicial(page)
    assert indicador.click.called

    indicador.reset_mock()
    indicador.inner_text.return_value = "1 de 9"
    garantir_pagina_inicial(page)
    assert not indicador.click.called

    page.locator.side_effect = Exception("erro locator")
    garantir_pagina_inicial(page)


def test_navegar_para_pagina():
    page = MagicMock()
    indicador = MagicMock()
    indicador.is_visible.return_value = True
    item = MagicMock()
    item.is_visible.return_value = True

    def mock_locator(sel, **kwargs):
        if "middleText" in sel:
            return indicador
        return MagicMock(first=item)

    page.locator = mock_locator
    for nome in [
        "Insights & Diagnóstico IA",
        "Lotações",
        "Modalidades",
        "Linhas de Trabalho",
        "Programas",
        "Visão Geral",
        "Menu",
        "Transparência & LGPD",
        "Informações do Projeto",
    ]:
        res = navegar_para_pagina(page, nome)
        assert res is True

    indicador.is_visible.return_value = False
    assert navegar_para_pagina(page, "Menu") is False

    page.locator = MagicMock(side_effect=Exception("erro"))
    assert navegar_para_pagina(page, "Menu") is False


def test_avancar_proxima_pagina():
    page = MagicMock()
    with patch("dashboard.capturar_prints.navegar_para_pagina", return_value=True):
        assert avancar_proxima_pagina(page, 1) is True
        assert avancar_proxima_pagina(page, len(PAGINAS) + 1) is False


def test_atualizar_timestamp_dashboard_readme(tmp_path, monkeypatch):
    dash_dir = tmp_path / "dashboard"
    dash_dir.mkdir(parents=True, exist_ok=True)
    readme_real = dash_dir / "dashboard_README.md"
    readme_real.write_text("> **Última Atualização:** 01/01/2026 às 12:00  \nTexto", encoding="utf-8")
    monkeypatch.setattr("dashboard.capturar_prints.PROJECT_DIR", tmp_path)
    atualizar_timestamp_dashboard_readme()
    conteudo = readme_real.read_text(encoding="utf-8")
    assert "01/01/2026" not in conteudo


def test_capturar_todas_as_paginas_sem_playwright(monkeypatch):
    monkeypatch.setattr("dashboard.capturar_prints.sync_playwright", None)
    with pytest.raises(ImportError, match="Playwright não está instalado"):
        capturar_todas_as_paginas()


def test_capturar_todas_as_paginas_mock(tmp_path, monkeypatch):
    mock_p = MagicMock()
    mock_browser = MagicMock()
    mock_ctx = MagicMock()
    mock_page = MagicMock()

    mock_p.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_ctx
    mock_ctx.new_page.return_value = mock_page

    mock_host = MagicMock()
    mock_host.is_visible.return_value = True
    mock_host.screenshot.side_effect = [f"img_page_{i}".encode("utf-8") for i in range(50)]
    mock_page.locator.return_value = MagicMock(first=mock_host, is_visible=MagicMock(return_value=True))

    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_p
    mock_cm.__exit__.return_value = None

    monkeypatch.setattr("dashboard.capturar_prints.sync_playwright", lambda: mock_cm)
    monkeypatch.setattr("dashboard.capturar_prints.IMAGENS_DIR", tmp_path / "imagens")
    monkeypatch.setattr("dashboard.capturar_prints.atualizar_timestamp_dashboard_readme", MagicMock())

    capturar_todas_as_paginas()

    imagens_salvas = list((tmp_path / "imagens").glob("*.png"))
    assert len(imagens_salvas) == len(PAGINAS)


def test_gerar_relatorio_com_gemini_mock():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "# Relatório Executivo Gemini\nAnálise técnica completa sem emojis."
    mock_client.models.generate_content.return_value = mock_resp

    with patch("tratamento.gerar_insights.genai.Client", return_value=mock_client):
        metricas_teste = {
            "periodo_inicio": "10/2023",
            "periodo_fim": "08/2026",
            "total_meses": 35,
            "total_servidores": 1000,
            "total_registros": 5000,
            "media_desig_mes": 150,
            "programas_ativos_geral": 10,
            "media_vinc": 1.2,
            "max_vinc": 5,
            "comp_atual_str": "08/2026",
            "comp_ant_str": "07/2026",
            "serv_desig_ult": 800,
            "serv_desig_ant": 750,
            "var_serv_desig": 6.67,
            "serv_nao_desig_ult": 150,
            "serv_nao_desig_ant": 160,
            "var_nao_desig": -6.25,
            "serv_deslig_ult": 50,
            "serv_deslig_ant": 40,
            "var_deslig": 25.0,
            "teletrab_serv_ult": 600,
            "pct_teletrab_serv": 75.0,
            "var_teletrab": 5.0,
            "presenc_serv_ult": 200,
            "pct_presenc_serv": 25.0,
        }
        tabs_teste = {
            "tabela_mod": "| Mod |",
            "tabela_duracao": "| Dur |",
            "tabela_top_prog": "| Prog |",
            "tabela_top_lot": "| Lot |",
            "tabela_top_lin": "| Lin |",
            "tabela_serv_vinc": "| Vinc |",
        }
        texto, modelo = gerar_relatorio_com_gemini(metricas_teste, tabs_teste, "fake_key")
        assert "Relatório Executivo Gemini" in texto
        assert modelo == "gemini-4-argon"


def test_gerar_relatorio_com_gemini_falha_todos_modelos():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("Erro de cota na API")

    with patch("tratamento.gerar_insights.genai.Client", return_value=mock_client):
        metricas_teste = {
            "periodo_inicio": "10/2023",
            "periodo_fim": "08/2026",
            "total_meses": 35,
            "total_servidores": 1000,
            "total_registros": 5000,
            "media_desig_mes": 150,
            "programas_ativos_geral": 10,
            "media_vinc": 1.2,
            "max_vinc": 5,
            "comp_atual_str": "08/2026",
            "comp_ant_str": "07/2026",
            "serv_desig_ult": 800,
            "serv_desig_ant": 750,
            "var_serv_desig": 6.67,
            "serv_nao_desig_ult": 150,
            "serv_nao_desig_ant": 160,
            "var_nao_desig": -6.25,
            "serv_deslig_ult": 50,
            "serv_deslig_ant": 40,
            "var_deslig": 25.0,
            "teletrab_serv_ult": 600,
            "pct_teletrab_serv": 75.0,
            "var_teletrab": 5.0,
            "presenc_serv_ult": 200,
            "pct_presenc_serv": 25.0,
        }
        tabs_teste = {
            "tabela_mod": "| Mod |",
            "tabela_duracao": "| Dur |",
            "tabela_top_prog": "| Prog |",
            "tabela_top_lot": "| Lot |",
            "tabela_top_lin": "| Lin |",
            "tabela_serv_vinc": "| Vinc |",
        }
        with pytest.raises(RuntimeError, match="Nenhum modelo Gemini respondeu com sucesso"):
            gerar_relatorio_com_gemini(metricas_teste, tabs_teste, "fake_key")


def test_insights_main_execucao_mock(tmp_path, monkeypatch):
    df_fake = pd.DataFrame({
        "competencia": pd.to_datetime(["2026-07-01", "2026-08-01"]),
        "id_usuario": ["USR-01", "USR-02"],
        "id_designacao": [1, 2],
        "status": ["Designado", "Designado"],
        "modalidade": ["Remoto", "Presencial"],
        "flag_pgd": ["Sim", "Sim"],
        "programa": ["PG-DIRBEN", "CEAB1"],
        "sigla_programa": ["DIRBEN", "CEAB1"],
        "lotacao": ["GEX BRASILIA", "GEX SP"],
        "linha_trabalho": ["LINHA 1", "LINHA 2"],
        "sigla_linha_trabalho": ["LINHA 1", "LINHA 2"],
        "tipo_entrega": ["Meta e Produto", "Meta e Produto"],
        "dt_inicio_designacao": pd.to_datetime(["2026-01-01"] * 2),
        "dt_fim_designacao": pd.to_datetime(["2026-12-31"] * 2),
    })
    monkeypatch.setattr("tratamento.gerar_insights.carregar_dados", lambda path: df_fake)
    monkeypatch.setattr("tratamento.gerar_insights.OUTPUT_MARKDOWN", tmp_path / "insights_README.md")
    monkeypatch.setattr("tratamento.gerar_insights.OUTPUT_CSV_POWERBI", tmp_path / "insights_hist.csv")
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key_para_teste")

    with patch("tratamento.gerar_insights.gerar_relatorio_com_gemini") as mock_gem:
        mock_gem.return_value = ("# Relatório Gemini Mock", "gemini-3.8-flash")
        gerar_insights_main()
        assert (tmp_path / "insights_README.md").exists()
        assert (tmp_path / "insights_hist.csv").exists()


