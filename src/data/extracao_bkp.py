
import time
from pathlib import Path

import pandas as pd
import requests

URL = (
    "https://apidadosabertos.saude.gov.br/"
    "vigilancia-e-meio-ambiente/srag-2019-2026"
)

TOTAL_APROX = 4_440_000
LIMIT = 1000
N_PAGINAS = 50

ROOT_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = ROOT_DIR / "data" / "raw"

RAW_DIR.mkdir(parents=True, exist_ok=True)

ARQUIVO_SAIDA = RAW_DIR / "srag_amostra.csv"

def baixar_pagina(
    offset: int,
    limit: int = LIMIT,
    tentativas: int = 3
) -> list[dict]:
    
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

def coletar_amostra(
    n_paginas: int = N_PAGINAS
) -> pd.DataFrame:

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


def limpeza_basica(
    df: pd.DataFrame
) -> pd.DataFrame:

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

    df = coletar_amostra()

    print(
        f"\nColeta finalizada: "
        f"{len(df):,} registros."
    )

    print("\nRealizando limpeza básica...")

    df = limpeza_basica(df)

    df.to_csv(
        ARQUIVO_SAIDA,
        index=False
    )

    print(
        f"\n{len(df):,} registros x "
        f"{df.shape[1]} colunas salvos em:"
    )

    print(ARQUIVO_SAIDA)

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


if __name__ == "__main__":
    main()
