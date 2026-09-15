import os
import re
import requests
from datetime import datetime

API_URL = "https://dadosabertos.inss.gov.br/api/3/action/package_show?id=sistema-de-gerenciamento-de-produtividade-sgp"

MESES = {
    "janeiro": "01", "fevereiro": "02", "marco": "03", "março": "03",
    "abril": "04", "maio": "05", "junho": "06", "julho": "07",
    "agosto": "08", "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"
}

def extrair_competencia(nome_recurso, url, data_criacao):
    texto_busca = f"{nome_recurso} {url}".lower()
    
    ano_match = re.search(r"202[3-6]", texto_busca)
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

    # Formato unificado AAAAMM (ex: pgd_inss_202310.csv)
    if ano and mes:
        return f"pgd_inss_{ano}{mes}.csv"
    
    nome_limpo = re.sub(r'[^a-zA-Z0-9_]', '_', nome_recurso).strip("_")
    return f"{nome_limpo}.csv"

def baixar_arquivos_padronizados():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    print("Consultando API publica do INSS (dadosabertos.inss.gov.br)...")
    try:
        response = requests.get(API_URL, headers=headers, timeout=30)
        response.raise_for_status()
        resources = response.json().get("result", {}).get("resources", [])
    except Exception as e:
        print(f"Erro na consulta a API: {e}")
        return

    novos_arquivos = 0

    for res in resources:
        url_download = res.get("url", "")
        format_file = res.get("format", "").upper()
        
        if format_file == "CSV" or url_download.lower().endswith(".csv"):
            nome_original = res.get("name", "")
            data_criacao = res.get("created", "") or res.get("last_modified", "")
            
            nome_padronizado = extrair_competencia(nome_original, url_download, data_criacao)
            caminho_local = os.path.join(data_dir, nome_padronizado)

            if not os.path.exists(caminho_local):
                print(f"Baixando e padronizando em 'data/': {nome_padronizado}...")
                try:
                    r = requests.get(url_download, headers=headers, stream=True, timeout=60)
                    r.raise_for_status()
                    
                    if r.encoding is None:
                        r.encoding = 'utf-8'

                    with open(caminho_local, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Salvo como: {nome_padronizado}")
                    novos_arquivos += 1
                except Exception as err:
                    print(f"Erro ao baixar {nome_padronizado}: {err}")

    print(f"\nIngestao concluida! {novos_arquivos} arquivo(s) novo(s) processado(s) em 'data/'.")

if __name__ == "__main__":
    baixar_arquivos_padronizados()