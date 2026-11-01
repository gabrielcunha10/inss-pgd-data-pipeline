import io
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd
import requests

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

S3_BUCKET_ROOT = "https://armazenamento-dadosabertos.s3.sa-east-1.amazonaws.com"
S3_BASE_2023_2025 = (
    f"{S3_BUCKET_ROOT}/PDA_2023_2025/Grupos_de_dados/Sistema+de+Gerenciamento+de+Produtividade+%E2%80%93+SGP"
)
S3_BASE_SISREF_2025 = (
    f"{S3_BUCKET_ROOT}/PDA_2023_2025/Grupos_de_dados/Sistema+Eletr%C3%B4nico+de+Frequ%C3%AAncia+-+SISREF"
)
S3_BASE_2025_2027 = (
    f"{S3_BUCKET_ROOT}/PDA_2025_2027/Grupos_de_dados/Sistema+de+Gerenciamento+de+Produtividade+%E2%80%93+SGP"
)

NOMES_MESES_ORDEM = [
    "janeiro", "fevereiro", "marco", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]

# Apenas as 5 competências históricas em que o INSS publicou com grafia fora do padrão no bucket S3
EXCECOES_S3_HISTORICAS = {
    "202501": ("CSV", f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS202501.csv"),
    "202503": ("CSV", f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.csv"),
    "202505": ("CSV", f"{S3_BASE_SISREF_2025}/D.SRF.FQS.005.PGD.ACSINSS.202505.csv"),
    "202506": ("CSV", f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS202506.csv"),
    "202608": ("XLSX", f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.202608.xlsx"),
}


def construir_catalogo_s3_historico(ate_ano: int = 2026, ate_mes: int = 8) -> list[dict]:
    """Gera programaticamente os recursos históricos do S3 a partir das regras de ciclo PDA do INSS."""
    catalogo = []
    ano, mes = 2023, 10
    while (ano < ate_ano) or (ano == ate_ano and mes <= ate_mes):
        ym = f"{ano}{mes:02d}"
        nome_mes = NOMES_MESES_ORDEM[mes - 1]
        if ym in EXCECOES_S3_HISTORICAS:
            fmt, url = EXCECOES_S3_HISTORICAS[ym]
        elif ano == 2023:
            fmt, url = "CSV", f"{S3_BASE_2023_2025}/D.SRF.FQS.005.ACSINSS.PGD.{ym}.csv"
        elif (ano, mes) <= (2025, 6):
            fmt, url = "CSV", f"{S3_BASE_2023_2025}/D.SRF.FQS.005.PGD.ACSINSS.{ym}.csv"
        else:
            fmt, url = "CSV", f"{S3_BASE_2025_2027}/D.SRF.FQS.005.PGD.ACSINSS.{ym}.csv"

        catalogo.append({"name": f"SGP - {nome_mes} {ano}", "format": fmt, "url": url})
        if mes == 12:
            ano += 1
            mes = 1
        else:
            mes += 1
    return catalogo


S3_RECURSOS_CONHECIDOS = construir_catalogo_s3_historico()

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

def gerar_candidatos_s3(ano: int, mes: int) -> list[tuple[str, str]]:
    """Gera todas as variações plausíveis de URL no S3 para uma competência (ano, mês)."""
    ym = f"{ano}{mes:02d}"
    bases = [S3_BASE_2025_2027]
    if ano >= 2027:
        ciclo_ini = ano if ano % 2 == 1 else ano - 1
        bases.insert(
            0,
            f"{S3_BUCKET_ROOT}/PDA_{ciclo_ini}_{ciclo_ini + 2}/Grupos_de_dados/"
            "Sistema+de+Gerenciamento+de+Produtividade+%E2%80%93+SGP",
        )
    bases.append(
        f"{S3_BUCKET_ROOT}/PDA_2025_2027/Grupos_de_dados/"
        "Sistema+Eletr%C3%B4nico+de+Frequ%C3%AAncia+-+SISREF"
    )

    prefixos_arq = [
        "D.SRF.FQS.005.PGD.ACSINSS",
        "D.SRF.FQS.005.ACSINSS.PGD",
    ]
    separadores = [".", "", "_", "-"]
    formatos = [("CSV", "csv"), ("XLSX", "xlsx"), ("XLS", "xls")]

    candidatos = []
    for base in bases:
        for pref in prefixos_arq:
            for sep in separadores:
                for fmt, ext in formatos:
                    candidatos.append((fmt, f"{base}/{pref}{sep}{ym}.{ext}"))
    return candidatos


def descobrir_recursos_s3_direto(headers=None):
    """Descobre recursos diretamente no bucket Amazon S3 oficial do INSS (sa-east-1).

    Utilizado automaticamente quando o catalogo CKAN (.gov.br) bloqueia IPs de
    datacenters internacionais (ex: GitHub Actions nos EUA) com HTTP 403.
    Verifica tambem novas competencias publicadas no S3 a partir de 202609 via HEAD.
    """
    recursos = [dict(r) for r in S3_RECURSOS_CONHECIDOS]
    hoje = datetime.now()
    ano_atual, mes_atual = hoje.year, hoje.month

    ano, mes = 2026, 9
    while (ano < ano_atual) or (ano == ano_atual and mes <= mes_atual):
        ym = f"{ano}{mes:02d}"
        nome_mes = NOMES_MESES_ORDEM[mes - 1]
        candidatos = gerar_candidatos_s3(ano, mes)
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


def precisa_baixar_recurso(
    caminho_local: str,
    nome_padronizado: str,
    res: dict,
    manifest: dict,
    headers: dict = None,
    verificar_head_remoto: bool = False,
) -> bool:
    """Verifica se um arquivo precisa ser baixado (inexistente ou republicado/atualizado pelo INSS)."""
    if not os.path.exists(caminho_local):
        return True

    meta_anterior = manifest.get(nome_padronizado)
    last_mod_atual = str(res.get("last_modified") or res.get("revision_id") or "")
    etag_atual = str(res.get("etag") or res.get("hash") or "")
    size_atual = res.get("size")

    if meta_anterior:
        if last_mod_atual and meta_anterior.get("last_modified") and last_mod_atual != meta_anterior.get("last_modified"):
            logging.info(f"Detectada republicacao no CKAN (last_modified alterado) para {nome_padronizado}.")
            return True
        if etag_atual and meta_anterior.get("etag") and etag_atual != meta_anterior.get("etag"):
            logging.info(f"Detectada republicacao (ETag alterado) para {nome_padronizado}.")
            return True
        if size_atual and meta_anterior.get("size") and int(size_atual) != int(meta_anterior.get("size")):
            logging.info(f"Detectada alteracao de tamanho para {nome_padronizado}.")
            return True

    if verificar_head_remoto and res.get("url"):
        try:
            r_head = requests.head(res["url"], headers=headers, timeout=10)
            if r_head.status_code == 200:
                remote_etag = r_head.headers.get("ETag", "").strip('"')
                remote_len = r_head.headers.get("Content-Length")
                if meta_anterior and remote_etag and meta_anterior.get("etag") and remote_etag != meta_anterior.get("etag"):
                    logging.info(f"ETag S3 alterado para {nome_padronizado}. Rebaixando versao corrigida...")
                    return True
                if (
                    remote_len
                    and res.get("url", "").lower().endswith(".csv")
                    and int(remote_len) != os.path.getsize(caminho_local)
                ):
                    logging.info(f"Content-Length S3 diferente do arquivo local em {nome_padronizado}. Rebaixando...")
                    return True
        except Exception:
            pass

    return False


def verificar_atualizacao_dados(data_dir: str, max_meses_defasagem: int = 3, data_ref: datetime = None) -> dict:
    """Verifica a atualidade da competencia mais recente disponivel em data/ e emite alerta se defasada."""
    ref = data_ref or datetime.now()
    padrao = re.compile(r"pgd_inss_(\d{4})(\d{2})\.csv$")
    competencias = []
    if os.path.exists(data_dir):
        for nome in os.listdir(data_dir):
            m = padrao.match(nome)
            if m:
                competencias.append((int(m.group(1)), int(m.group(2))))

    if not competencias:
        msg = "[ALERTA DE DADOS] Nenhum arquivo de competencia PGD encontrado em 'data/'."
        logging.warning(msg)
        return {"ok": False, "ultima_competencia": None, "meses_defasagem": None, "mensagem": msg}

    ult_ano, ult_mes = max(competencias)
    meses_defasagem = (ref.year - ult_ano) * 12 + (ref.month - ult_mes)
    ultima_str = f"{ult_ano}-{ult_mes:02d}"

    if meses_defasagem > max_meses_defasagem:
        msg = (
            f"[ALERTA DE DEFASAGEM] A competencia mais recente ({ultima_str}) esta defasada em "
            f"{meses_defasagem} meses em relacao a data atual ({ref.strftime('%Y-%m')}). "
            "Verifique se o Portal de Dados Abertos do INSS atrasou a publicacao."
        )
        logging.warning(msg)
        return {"ok": False, "ultima_competencia": ultima_str, "meses_defasagem": meses_defasagem, "mensagem": msg}

    msg = f"Verificacao de atualidade OK: competencia mais recente {ultima_str} (defasagem: {meses_defasagem} mes(es))."
    logging.info(msg)
    return {"ok": True, "ultima_competencia": ultima_str, "meses_defasagem": meses_defasagem, "mensagem": msg}


def baixar_arquivos_padronizados(verificar_remoto: bool = False):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    manifest_path = os.path.join(data_dir, ".download_manifest.json")

    manifest = {}
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as mf:
                manifest = json.load(mf)
        except Exception:
            manifest = {}

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
            msg = f"Erro fatal na consulta a API do INSS: {e}"
            logging.error(msg)
            raise RuntimeError(msg) from e
    except Exception as e:
        msg = f"Erro fatal na consulta a API do INSS: {e}"
        logging.error(msg)
        raise RuntimeError(msg) from e

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

            if precisa_baixar_recurso(
                caminho_local=caminho_local,
                nome_padronizado=nome_padronizado,
                res=res,
                manifest=manifest,
                headers=headers,
                verificar_head_remoto=verificar_remoto,
            ):
                logging.info(f"Baixando e padronizando em 'data/': {nome_padronizado}...")
                try:
                    etag_resp = ""
                    if is_csv:
                        r = requests.get(url_download, headers=headers, stream=True, timeout=60)
                        r.raise_for_status()
                        etag_resp = getattr(r, "headers", {}).get("ETag", "").strip('"') if hasattr(r, "headers") else ""
                        
                        if r.encoding is None:
                            r.encoding = 'utf-8'

                        with open(caminho_local, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                    elif is_excel:
                        r = requests.get(url_download, headers=headers, timeout=60)
                        r.raise_for_status()
                        etag_resp = getattr(r, "headers", {}).get("ETag", "").strip('"') if hasattr(r, "headers") else ""
                        
                        df = pd.read_excel(io.BytesIO(r.content), dtype=str)
                        df.to_csv(caminho_local, index=False, encoding='utf-8')
                        
                    manifest[nome_padronizado] = {
                        "url": url_download,
                        "last_modified": str(res.get("last_modified") or res.get("revision_id") or ""),
                        "etag": etag_resp or str(res.get("etag") or res.get("hash") or ""),
                        "size": res.get("size") or os.path.getsize(caminho_local),
                        "updated_at": datetime.now().isoformat(),
                    }
                    logging.info(f"Salvo como: {nome_padronizado}")
                    novos_arquivos += 1
                except Exception as err:
                    msg = f"Erro critico ao baixar {nome_padronizado}: {err}"
                    logging.error(msg)
                    raise RuntimeError(msg) from err

    try:
        with open(manifest_path, "w", encoding="utf-8") as mf:
            json.dump(manifest, mf, indent=2, ensure_ascii=False)
    except Exception:
        pass

    logging.info(f"Ingestao concluida! {novos_arquivos} arquivo(s) novo(s) ou atualizado(s) processado(s) em 'data/'.")
    verificar_atualizacao_dados(data_dir)


def main():
    baixar_arquivos_padronizados()


if __name__ == "__main__":
    main()