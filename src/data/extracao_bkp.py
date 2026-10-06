import time

import pandas as pd
import requests


URL = (
    "https://apidadosabertos.saude.gov.br/"
    "vigilancia-e-meio-ambiente/srag-2019-2026"
)

TOTAL_APROX = 4_440_000
LIMIT = 1000
N_PAGINAS = 50


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

            return dados.get(
                "srag_2019_2026",
                []
            )

        except (requests.RequestException, ValueError) as erro:

            print(
                f"offset={offset}: "
                f"erro na tentativa {tentativa}: {erro}"
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
            f"offset={offset:,} "
            f"→ {len(bloco)} registros"
        )

        time.sleep(0.5)

    return pd.DataFrame(registros)