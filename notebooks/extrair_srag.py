"""
Extração de amostra do SRAG 2019-2026 via API de Dados Abertos do Ministério da Saúde.
Endpoint: https://apidadosabertos.saude.gov.br/vigilancia-e-meio-ambiente/srag-2019-2026

Comportamento observado da API (testado em 19/09/2026):
- limit: máx. 1000 registros por chamada.
- offset: apesar da documentação dizer "número da página", funciona como
  deslocamento em LINHAS (offset=1 pula 1 registro, não 1 página).
- Filtros dt_notific / anomes_notific retornaram vazio nos testes -> não usamos.
- ATENÇÃO: na API, dt_notific NÃO é a data real da notificação -- vem preenchida com
  o 1º dia do ano epidemiológico.
- Para datar os casos, use dt_sin_pri (início dos sintomas) ou dt_interna.
- A base tem ~4,44 milhões de linhas, ordenadas aproximadamente por data.
  Por isso pegamos páginas espalhadas ao longo de toda a base.

"""

import time
from pathlib import Path
import requests
import pandas as pd

URL = "https://apidadosabertos.saude.gov.br/vigilancia-e-meio-ambiente/srag-2019-2026"
TOTAL_APROX = 4_440_000
LIMIT = 1000
N_PAGINAS = 50
ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
ARQUIVO_SAIDA = RAW_DIR / "srag_amostra.csv"

def baixar_pagina(offset: int,limit: int = LIMIT,tentativas: int = 3) -> list[dict]:
    """Baixa um bloco de registros a partir de offset."""
    for t in range(1, tentativas + 1):
        try:
            r = requests.get(URL,params={"limit": limit,"offset": offset},timeout=180)
            r.raise_for_status()
            return r.json().get("srag_2019_2026", [])
        except (requests.RequestException, ValueError) as e:
            print(f"offset={offset}: "f"erro na tentativa {t} ({e})")
            time.sleep(5 * t)

    return []


def coletar_amostra(n_paginas: int = N_PAGINAS) -> pd.DataFrame:
    """Coleta blocos distribuídos uniformemente ao longo da base."""
    passo = TOTAL_APROX // n_paginas
    registros = []
    for i in range(n_paginas):
        offset = i * passo
        bloco = baixar_pagina(offset)
        registros.extend(bloco)
        print(f"[{i + 1}/{n_paginas}] "f"offset={offset:>9,} -> "f"{len(bloco)} registros")
        time.sleep(0.5)

    return pd.DataFrame(registros)


def limpeza_basica(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza nulos e converte datas.
    A decodificação das categorias fica para o EDA.
    """
    df = (df.replace({"nan": pd.NA,"": pd.NA}).drop_duplicates(subset="nu_notific"))
    # Alguns anos vêm com códigos "1.0" em vez de "1"
    df = df.replace(r"^(\d+)\.0+$",r"\1",regex=True)
    # Converte colunas de data
    for col in [c for c in df.columns if c.startswith("dt_")]:
        df[col] = pd.to_datetime(df[col],errors="coerce")
    return df

if __name__ == "__main__":
    print("Iniciando coleta do SRAG...")
    print(f"Arquivo de saída: {ARQUIVO_SAIDA}")
    print()
    df = limpeza_basica(coletar_amostra())
    df.to_csv(ARQUIVO_SAIDA,index=False)
    print()
    print(f"{len(df):,} registros x "f"{df.shape[1]} colunas "f"salvos em:")
    print(ARQUIVO_SAIDA)
    print("\nCasos por ano ""(data de início dos sintomas):")
    print(df["dt_sin_pri"].dt.year.value_counts().sort_index())
    # evolucao: 1 = cura 2 = óbito 3 = óbito por outras causas 9 = ignorado
    print("\nDistribuição do desfecho (evolucao):")
    print(df["evolucao"].value_counts(dropna=False,normalize=True).round(3))