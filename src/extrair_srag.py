"""
Extração de amostra do SRAG 2019-2026
=====================================

Coleta uma amostra da base SRAG 2019-2026
via API de Dados Abertos do Ministério da Saúde.

Endpoint:
https://apidadosabertos.saude.gov.br/vigilancia-e-meio-ambiente/srag-2019-2026

Comportamento observado da API (testado em 19/09/2026):

- limit: máximo de 1000 registros por chamada.
- offset: funciona como deslocamento em linhas.
  Exemplo: offset=1 pula 1 registro.
- Filtros dt_notific / anomes_notific retornaram vazio nos testes.
- dt_notific NÃO representa a data real da notificação.
- Para análise temporal, utilizar dt_sin_pri (início dos sintomas)
  ou dt_interna.
- A base possui aproximadamente 4,44 milhões de linhas.
- Os registros são aproximadamente ordenados por data.
- Por isso, são coletados blocos distribuídos ao longo da base.
"""

import time
from pathlib import Path

import pandas as pd
import requests


# ============================================================
# CONFIGURAÇÕES
# ============================================================

URL = (
    "https://apidadosabertos.saude.gov.br/"
    "vigilancia-e-meio-ambiente/srag-2019-2026"
)

TOTAL_APROX = 4_440_000
LIMIT = 1000
N_PAGINAS = 50

# Localização do projeto
# Este arquivo está em: projeto/src/extrair_srag.py
# Então parents[1] representa a raiz do projeto.
ROOT_DIR = Path(__file__).resolve().parents[1]

# Pasta onde o CSV será salvo
RAW_DIR = ROOT_DIR / "data" / "raw"

# Cria a pasta caso ela ainda não exista
RAW_DIR.mkdir(parents=True, exist_ok=True)

ARQUIVO_SAIDA = RAW_DIR / "srag_amostra.csv"


# ============================================================
# FUNÇÃO: BAIXAR UMA PÁGINA
# ============================================================

def baixar_pagina(
    offset: int,
    limit: int = LIMIT,
    tentativas: int = 3
) -> list[dict]:
    """
    Baixa um bloco de registros da API a partir de um offset.

    Parameters
    ----------
    offset : int
        Posição inicial dos registros.

    limit : int
        Quantidade máxima de registros solicitados.

    tentativas : int
        Número máximo de tentativas em caso de erro.

    Returns
    -------
    list[dict]
        Lista de registros retornados pela API.
    """

    for tentativa in range(1, tentativas + 1):

        try:
            resposta = requests.get(
                URL,
                params={
                    "limit": limit,
                    "offset": offset
                },
                timeout=180
            )

            resposta.raise_for_status()

            dados = resposta.json()

            return dados.get("srag_2019_2026", [])

        except (requests.RequestException, ValueError) as erro:

            print(
                f"offset={offset}: "
                f"erro na tentativa {tentativa} "
                f"({erro})"
            )

            time.sleep(5 * tentativa)

    return []


# ============================================================
# FUNÇÃO: COLETAR AMOSTRA
# ============================================================

def coletar_amostra(
    n_paginas: int = N_PAGINAS
) -> pd.DataFrame:
    """
    Coleta blocos distribuídos uniformemente ao longo da base.

    A base possui aproximadamente 4,44 milhões de registros.
    Em vez de pegar apenas os primeiros 50.000 registros,
    os offsets são distribuídos ao longo de toda a base.

    Returns
    -------
    pandas.DataFrame
        DataFrame contendo a amostra coletada.
    """

    passo = TOTAL_APROX // n_paginas

    registros = []

    for i in range(n_paginas):

        offset = i * passo

        bloco = baixar_pagina(offset)

        registros.extend(bloco)

        print(
            f"[{i + 1}/{n_paginas}] "
            f"offset={offset:>9,} "
            f"-> {len(bloco)} registros"
        )

        # Pequena pausa para evitar muitas requisições consecutivas
        time.sleep(0.5)

    return pd.DataFrame(registros)


# ============================================================
# FUNÇÃO: LIMPEZA BÁSICA
# ============================================================

def limpeza_basica(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Realiza uma limpeza inicial dos dados.

    Operações:
    - Substitui strings "nan" e vazias por valores nulos.
    - Remove registros duplicados pelo número da notificação.
    - Corrige códigos numéricos como "1.0" para "1".
    - Converte colunas de data para datetime.
    """

    # Substituição de valores vazios/nulos
    df = df.replace(
        {
            "nan": pd.NA,
            "": pd.NA
        }
    )

    # Remove duplicidades
    if "nu_notific" in df.columns:
        df = df.drop_duplicates(
            subset="nu_notific"
        )

    # Alguns anos podem apresentar códigos
    # como "1.0" em vez de "1".
    df = df.replace(
        r"^(\d+)\.0+$",
        r"\1",
        regex=True
    )

    # Conversão das colunas de data
    colunas_data = [
        coluna
        for coluna in df.columns
        if coluna.startswith("dt_")
    ]

    for coluna in colunas_data:
        df[coluna] = pd.to_datetime(
            df[coluna],
            errors="coerce"
        )

    return df


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def main() -> None:
    """
    Executa todo o processo de extração, limpeza
    e salvamento da amostra.
    """

    print("=" * 60)
    print("EXTRAÇÃO DE AMOSTRA DO SRAG 2019-2026")
    print("=" * 60)

    print("\nIniciando coleta do SRAG...")
    print(f"Arquivo de saída: {ARQUIVO_SAIDA}\n")

    # --------------------------------------------------------
    # 1. Coleta
    # --------------------------------------------------------

    df = coletar_amostra()

    print(
        f"\nColeta finalizada: "
        f"{len(df):,} registros."
    )

    # --------------------------------------------------------
    # 2. Limpeza
    # --------------------------------------------------------

    print("\nRealizando limpeza básica...")

    df = limpeza_basica(df)

    # --------------------------------------------------------
    # 3. Salvar CSV
    # --------------------------------------------------------

    df.to_csv(
        ARQUIVO_SAIDA,
        index=False
    )

    print(
        f"\n{len(df):,} registros x "
        f"{df.shape[1]} colunas salvos em:"
    )

    print(ARQUIVO_SAIDA)

    # --------------------------------------------------------
    # 4. Distribuição por ano
    # --------------------------------------------------------

    if "dt_sin_pri" in df.columns:

        print(
            "\nCasos por ano "
            "(data de início dos sintomas):"
        )

        casos_por_ano = (
            df["dt_sin_pri"]
            .dt.year
            .value_counts()
            .sort_index()
        )

        print(casos_por_ano)

    # --------------------------------------------------------
    # 5. Distribuição do desfecho
    # --------------------------------------------------------

    if "evolucao" in df.columns:

        print(
            "\nDistribuição do desfecho "
            "(evolucao):"
        )

        distribuicao = (
            df["evolucao"]
            .value_counts(
                dropna=False,
                normalize=True
            )
            .round(3)
        )

        print(distribuicao)

    print("\nProcesso concluído.")


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()