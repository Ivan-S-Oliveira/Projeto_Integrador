"""
Extração de amostra do SRAG 2019-2026 via API de Dados Abertos do Ministério da Saúde.
Endpoint: https://apidadosabertos.saude.gov.br/vigilancia-e-meio-ambiente/srag-2019-2026

Comportamento observado da API (testado em 19/09/2026):
- limit: máx. 1000 registros por chamada.
- offset: apesar de a documentação dizer "número da página", funciona como
  deslocamento em LINHAS (offset=1 pula 1 registro, não 1 página).
- Filtros dt_notific / anomes_notific retornaram vazio nos testes -> não usamos.
- A base tem ~4,44 milhões de linhas, ordenadas aproximadamente por data.
  Por isso pegamos páginas espalhadas ao longo de toda a base, e não só as primeiras
  (senão a amostra seria toda de dez/2018-2019).

Uso:  pip install requests pandas
      python extrair_srag.py
"""

import time
import requests
import pandas as pd

URL = "https://apidadosabertos.saude.gov.br/vigilancia-e-meio-ambiente/srag-2019-2026"
TOTAL_APROX = 4_440_000   # tamanho aproximado da base
LIMIT = 1000              # máximo permitido pela API
N_PAGINAS = 50            # 50 páginas x 1000 = ~50 mil registros (ajuste à vontade)


def baixar_pagina(offset: int, limit: int = LIMIT, tentativas: int = 3) -> list[dict]:
    """Baixa um bloco de registros a partir de `offset`, com novas tentativas em caso de erro."""
    for t in range(1, tentativas + 1):
        try:
            r = requests.get(URL, params={"limit": limit, "offset": offset}, timeout=180)
            r.raise_for_status()
            return r.json().get("srag_2019_2026", [])
        except (requests.RequestException, ValueError) as e:
            print(f"  offset={offset}: erro na tentativa {t} ({e})")
            time.sleep(5 * t)
    return []


def coletar_amostra(n_paginas: int = N_PAGINAS) -> pd.DataFrame:
    """Coleta n_paginas blocos distribuídos uniformemente ao longo da base."""
    passo = TOTAL_APROX // n_paginas
    registros = []
    for i in range(n_paginas):
        offset = i * passo
        bloco = baixar_pagina(offset)
        registros.extend(bloco)
        print(f"[{i + 1}/{n_paginas}] offset={offset:>9,} -> {len(bloco)} registros")
        time.sleep(0.5)  # gentileza com o servidor público
    return pd.DataFrame(registros)


def limpeza_basica(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza nulos e converte datas. A decodificação das categorias fica para o EDA."""
    df = df.replace({"nan": pd.NA, "": pd.NA}).drop_duplicates(subset="nu_notific")
    # alguns anos vêm com códigos "1.0" em vez de "1" -> unifica
    df = df.replace(r"^(\d+)\.0+$", r"\1", regex=True)
    for col in [c for c in df.columns if c.startswith("dt_")]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


if __name__ == "__main__":
    df = limpeza_basica(coletar_amostra())
    df.to_csv("srag_amostra.csv", index=False)

    print(f"\n{len(df):,} registros x {df.shape[1]} colunas salvos em srag_amostra.csv")
    print("\nNotificações por ano:")
    print(df["dt_notific"].dt.year.value_counts().sort_index())
    # evolucao: 1 = cura, 2 = óbito, 3 = óbito por outras causas, 9 = ignorado
    print("\nDistribuição do desfecho (evolucao):")
    print(df["evolucao"].value_counts(dropna=False, normalize=True).round(3))
