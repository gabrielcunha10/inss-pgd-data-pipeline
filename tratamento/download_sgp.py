import os
import re
import requests
import io
import pandas as pd
import logging
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "pipeline.log"

# Configuração de logging unificado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)

API_URL = "https://dadosabertos.inss.gov.br/api/3/action/package_show?id=sistema-de-gerenciamento-de-produtividade-sgp"
PORTAL_HOME_URL = "https://dadosabertos.inss.gov.br/dataset/sistema-de-gerenciamento-de-produtividade-sgp"

S3_BASE_2023_2025 = (
    "https://armazenamento-dadosabertos.s3.sa-east-1.amazonaws.com/"
    "PDA_2023_2025/Grupos_de_dados/Sistema+de+Gerenciamento+de+Produtividade+%E2%80%93+SGP"
)
S3_BASE_SISREF_2025 = (
    "https://armazenamento-dadosabertos.s3.sa-east-1.amazonaws.com/"
    "PDA_2023_2025/Grupos_de_dados/Sistema+Eletr%C3%B4nico+de+Frequ%C3%AAncia+-+SISREF"
)
S3_BASE_2025_2027 = (
    "https://armazenamento-dadosabertos.s3.sa-east-1.amazonaws.com/"
    "PDA_2025_2027/Grupos_de_dados/Sistema+de+Gerenciamento+de+Produtividade+%E2%80%93+SGP"
)

S3_RECURSOS_CONHECIDOS = [
    {"name": "SGP - outubro 2023", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.ACSINSS.PGD.202310.csv"},
    {"name": "SGP - novembro 2023", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.ACSINSS.PGD.202311.csv"},
    {"name": "SGP - dezembro 2023", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.ACSINSS.PGD.202312.csv"},
    {"name": "SGP - janeiro 2024", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.202401.csv"},
    {"name": "SGP - fevereiro 2024", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.202402.csv"},
    {"name": "SGP - marco 2024", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.202403.csv"},
    {"name": "SGP - abril 2024", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.202404.csv"},
    {"name": "SGP - maio 2024", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.202405.csv"},
    {"name": "SGP - junho 2024", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.202406.csv"},
    {"name": "SGP - julho 2024", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.202407.csv"},
    {"name": "SGP - agosto 2024", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.202408.csv"},
    {"name": "SGP - setembro 2024", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.202409.csv"},
    {"name": "SGP - outubro 2024", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.202410.csv"},
    {"name": "SGP - novembro 2024", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.202411.csv"},
    {"name": "SGP - dezembro 2024", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.202412.csv"},
    {"name": "SGP - janeiro 2025", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS202501.csv"},
    {"name": "SGP - fevereiro 2025", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.202502.csv"},
    {"name": "SGP - marco 2025", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.csv"},
    {"name": "SGP - abril 2025", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.202504.csv"},
    {"name": "SGP - maio 2025", "format": "CSV", "url": f"{S3_BASE_SISREF_2025}/D.SRF.FQS.005.PGD.ACSINSS.202505.csv"},
    {"name": "SGP - junho 2025", "format": "CSV", "url": f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS202506.csv"},
    {"name": "SGP - julho 2025", "format": "CSV", "url": f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.202507.csv"},
    {"name": "SGP - agosto 2025", "format": "CSV", "url": f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.202508.csv"},
    {"name": "SGP - setembro 2025", "format": "CSV", "url": f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.202509.csv"},
    {"name": "SGP - outubro 2025", "format": "CSV", "url": f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.202510.csv"},
    {"name": "SGP - novembro 2025", "format": "CSV", "url": f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.202511.csv"},
    {"name": "SGP - dezembro 2025", "format": "CSV", "url": f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.202512.csv"},
    {"name": "SGP - janeiro 2026", "format": "CSV", "url": f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.202601.csv"},
    {"name": "SGP - fevereiro 2026", "format": "CSV", "url": f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.202602.csv"},
    {"name": "SGP - marco 2026", "format": "CSV", "url": f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.202603.csv"},
    {"name": "SGP - abril 2026", "format": "CSV", "url": f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.202604.csv"},
    {"name": "SGP - maio 2026", "format": "CSV", "url": f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.202605.csv"},
    {"name": "SGP - junho 2026", "format": "CSV", "url": f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.202606.csv"},
    {"name": "SGP - julho 2026", "format": "CSV", "url": f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.202607.csv"},
    {"name": "SGP - agosto 2026", "format": "XLSX", "url": f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.202608.xlsx"},
]

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": PORTAL_HOME_URL,
    "Origin": "https://dadosabertos.inss.gov.br",
    "Connection": "keep-alive",
}

MESES = {
    "janeiro": "01", "fevereiro": "02", "marco": "03", "março": "03",
    "abril": "04", "maio": "05", "junho": "06", "julho": "07",
    "agosto": "08", "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"
}

def extrair_competencia(nome_recurso, url, data_criacao):
    texto_busca = f"{nome_recurso} {url}".lower()
    
    ano_match = re.search(r"20\d{2}", texto_busca)
    ano = ano_match.group(0) if ano_match else None
    
    mes = None
    for nome_mes, num_mes in MESES.items():
        if nome_mes in texto_busca:
            mes = num_mes
            break
            
    if not (ano and mes) and data_criacao:
        try:
            dt = datetime.strptime(data_criacao.split("T")[0], "%Y-%m-%d")
            ano = str(dt.year)
            mes = f"{dt.month:02d}"
        except Exception:
            pass

    if ano and mes:
        return f"pgd_inss_{ano}{mes}.csv"
    
    nome_limpo = re.sub(r'[^a-zA-Z0-9_]', '_', nome_recurso).strip("_")
    return f"{nome_limpo}.csv"

def descobrir_recursos_s3_direto(headers=None):
    """Descobre recursos diretamente no bucket Amazon S3 oficial do INSS (sa-east-1).

    Utilizado automaticamente quando o catalogo CKAN (.gov.br) bloqueia IPs de
    datacenters internacionais (ex: GitHub Actions nos EUA) com HTTP 403.
    Verifica tambem novas competencias publicadas no S3 a partir de 202609 via HEAD.
    """
    recursos = [dict(r) for r in S3_RECURSOS_CONHECIDOS]
    nomes_mes = [
        "janeiro", "fevereiro", "marco", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]
    hoje = datetime.now()
    ano_atual, mes_atual = hoje.year, hoje.month

    ano, mes = 2026, 9
    while (ano < ano_atual) or (ano == ano_atual and mes <= mes_atual):
        ym = f"{ano}{mes:02d}"
        nome_mes = nomes_mes[mes - 1]
        candidatos = [
            ("CSV", f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.{ym}.csv"),
            ("XLSX", f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.{ym}.xlsx"),
            ("CSV", f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS{ym}.csv"),
            ("XLSX", f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS{ym}.xlsx"),
        ]
        for fmt, url_cand in candidatos:
            try:
                r_head = requests.head(url_cand, headers=headers, timeout=10)
                if r_head.status_code == 200:
                    logging.info(f"Nova competencia descoberta diretamente no S3 do INSS: {ym} ({fmt})")
                    recursos.append({
                        "name": f"SGP - {nome_mes} {ano}",
                        "format": fmt,
                        "url": url_cand,
                    })
                    break
            except Exception:
                continue

        if mes == 12:
            ano += 1
            mes = 1
        else:
            mes += 1

    return recursos


def baixar_arquivos_padronizados():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    headers = DEFAULT_HEADERS.copy()

    logging.info("Consultando API publica do INSS (dadosabertos.inss.gov.br)...")
    try:
        response = requests.get(API_URL, headers=headers, timeout=30)
        if getattr(response, "status_code", 200) == 403:
            logging.warning(
                "HTTP 403 no catalogo CKAN (.gov.br). Tentando sessao com cookies do portal (cookie-prodi)..."
            )
            session = requests.Session()
            session.headers.update(headers)
            session.get(PORTAL_HOME_URL, timeout=20)
            response = session.get(API_URL, timeout=30)
        response.raise_for_status()
        resources = response.json().get("result", {}).get("resources", [])
    except requests.exceptions.HTTPError as e:
        status_code = getattr(e.response, "status_code", None)
        if status_code == 403:
            logging.warning(
                "Catalogo CKAN (.gov.br) bloqueou o IP de origem (HTTP 403 Geo-IP). "
                "Acionando descoberta e download direto no bucket Amazon S3 do INSS (sa-east-1)..."
            )
            resources = descobrir_recursos_s3_direto(headers=headers)
        else:
            logging.error(f"Erro fatal na consulta a API do INSS: {e}")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Erro fatal na consulta a API do INSS: {e}")
        sys.exit(1)

    novos_arquivos = 0

    for res in resources:
        url_download = res.get("url", "")
        format_file = res.get("format", "").upper()
        
        is_csv = format_file == "CSV" or url_download.lower().endswith(".csv")
        is_excel = format_file in ("XLSX", "XLS") or url_download.lower().endswith((".xlsx", ".xls"))
        
        if is_csv or is_excel:
            nome_original = res.get("name", "")
            data_criacao = res.get("created", "") or res.get("last_modified", "")
            
            nome_padronizado = extrair_competencia(nome_original, url_download, data_criacao)
            caminho_local = os.path.join(data_dir, nome_padronizado)

            if not os.path.exists(caminho_local):
                logging.info(f"Baixando e padronizando em 'data/': {nome_padronizado}...")
                try:
                    if is_csv:
                        r = requests.get(url_download, headers=headers, stream=True, timeout=60)
                        r.raise_for_status()
                        
                        if r.encoding is None:
                            r.encoding = 'utf-8'

                        with open(caminho_local, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                    elif is_excel:
                        r = requests.get(url_download, headers=headers, timeout=60)
                        r.raise_for_status()
                        
                        df = pd.read_excel(io.BytesIO(r.content), dtype=str)
                        df.to_csv(caminho_local, index=False, encoding='utf-8')
                        
                    logging.info(f"Salvo como: {nome_padronizado}")
                    novos_arquivos += 1
                except Exception as err:
                    logging.error(f"Erro critico ao baixar {nome_padronizado}: {err}")
                    sys.exit(1)

    logging.info(f"Ingestao concluida! {novos_arquivos} arquivo(s) novo(s) processado(s) em 'data/'.")

def main():
    baixar_arquivos_padronizados()

if __name__ == "__main__":
    main()