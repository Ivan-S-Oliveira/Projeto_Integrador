from pathlib import Path
import time

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests

from src.utils import config as C


# ---------------------------------------------------------------------------
# Configuração da API SRAG 2019–2026
# ---------------------------------------------------------------------------

API_URL = getattr(
    C,
    "API_URL",
    "https://apidadosabertos.saude.gov.br/"
    "vigilancia-e-meio-ambiente/srag-2019-2026",
)

PAGE_SIZE = getattr(C, "PAGE_SIZE", 1000)
N_PAGINAS = getattr(C, "N_PAGINAS", 50)
HTTP_TIMEOUT = getattr(C, "HTTP_TIMEOUT", 180)
HTTP_TENTATIVAS = getattr(C, "HTTP_TENTATIVAS", 3)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def baixar_pagina(
    offset: int,
    limit: int = PAGE_SIZE,
    tentativas: int = HTTP_TENTATIVAS,
) -> list[dict]:
    """
    Baixa uma página da API SRAG 2019–2026.

    Retorna uma lista de registros.
    """

    for tentativa in range(1, tentativas + 1):
        try:
            resposta = requests.get(
                API_URL,
                params={
                    "limit": limit,
                    "offset": offset,
                },
                timeout=HTTP_TIMEOUT,
            )

            resposta.raise_for_status()

            dados = resposta.json()

            registros = dados.get(
                "srag_2019_2026",
                [],
            )

            if not isinstance(registros, list):
                raise ValueError(
                    "A chave 'srag_2019_2026' não retornou uma lista."
                )

            return registros

        except (requests.RequestException, ValueError) as erro:
            print(
                f"[baixar_pagina] offset={offset:,} | "
                f"tentativa {tentativa}/{tentativas} | "
                f"erro: {erro}"
            )

            if tentativa < tentativas:
                time.sleep(5 * tentativa)

    return []


# ---------------------------------------------------------------------------
# Extração da amostra
# ---------------------------------------------------------------------------

def coletar_amostra(
    n_paginas: int = N_PAGINAS,
    page_size: int = PAGE_SIZE,
) -> pd.DataFrame:
    """
    Coleta uma amostra paginada da API SRAG 2019–2026.

    Por padrão:
        50 páginas × 1.000 registros = até 50.000 registros.
    """

    if n_paginas < 1:
        raise ValueError("n_paginas deve ser >= 1")

    if page_size < 1:
        raise ValueError("page_size deve ser >= 1")

    registros = []

    inicio = time.time()

    for i in range(n_paginas):

        offset = i * page_size

        bloco = baixar_pagina(
            offset=offset,
            limit=page_size,
        )

        registros.extend(bloco)

        print(
            f"[{i + 1}/{n_paginas}] "
            f"offset={offset:,} "
            f"→ {len(bloco):,} registros "
            f"| acumulado: {len(registros):,}"
        )

        # Evita fazer requisições muito rapidamente.
        time.sleep(0.5)

        # Se a API não retornar registros, não há motivo
        # para continuar avançando.
        if not bloco:
            print(
                "[coletar_amostra] API não retornou registros. "
                "Encerrando a coleta."
            )
            break

    tempo = time.time() - inicio

    df = pd.DataFrame(registros)

    print(
        f"\n[coletar_amostra] "
        f"{len(df):,} linhas coletadas em {tempo:.1f}s"
    )

    if not df.empty:
        print(
            f"[coletar_amostra] "
            f"{df.shape[1]} colunas"
        )

    return df


# ---------------------------------------------------------------------------
# Conversão CSV → Parquet
# ---------------------------------------------------------------------------

def csv_to_parquet(
    csv_path: str | Path,
    out_path: str | Path,
    chunksize: int = 500_000,
) -> Path:
    """
    Converte um CSV para Parquet em blocos,
    evitando carregar todo o arquivo na memória.
    """

    csv_path = Path(csv_path)
    out_path = Path(out_path)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Arquivo CSV não encontrado: {csv_path}"
        )

    out_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    size = csv_path.stat().st_size

    writer = None
    total = 0
    inicio = time.time()

    try:
        with open(csv_path, "rb") as arquivo:

            for chunk in pd.read_csv(
                arquivo,
                sep=C.CSV_SEP,
                usecols=C.COLS,
                chunksize=chunksize,
                encoding=C.CSV_ENCODING,
                low_memory=False,
            ):

                tabela = pa.Table.from_pandas(
                    chunk.astype("string"),
                    preserve_index=False,
                )

                if writer is None:
                    writer = pq.ParquetWriter(
                        out_path,
                        tabela.schema,
                        compression="zstd",
                    )

                writer.write_table(tabela)

                total += len(chunk)

                percentual = min(
                    arquivo.tell() / size * 100,
                    100,
                )

                tempo = time.time() - inicio

                print(
                    f"\r{percentual:5.1f}% | "
                    f"{total:,} linhas | "
                    f"{tempo:.0f}s",
                    end="",
                    flush=True,
                )

    finally:
        if writer is not None:
            writer.close()

    tempo_total = (time.time() - inicio) / 60

    print(
        f"\r100.0% | "
        f"{total:,} linhas | "
        f"{tempo_total:.1f} min - concluído"
    )

    return out_path