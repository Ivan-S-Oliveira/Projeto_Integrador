from pathlib import Path
import time

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests

from src.utils import config as C


# ---------------------------------------------------------------------------
# URL do arquivo Parquet do SRAG 2019–2026 (banco vivo)
# ---------------------------------------------------------------------------
# O link exato muda periodicamente (novas atualizações semanais).
# Consulte a página do conjunto de dados para obter a URL atualizada:
#   https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026
#
# Padrão observado:
#   https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG/2023/INFLUD23-16-10-2023.parquet
# ---------------------------------------------------------------------------
SRAG_PARQUET_URL = getattr(
    C,
    "SRAG_PARQUET_URL",
    "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG/2023/INFLUD23-16-10-2023.parquet"
)

HTTP_TIMEOUT = getattr(C, "HTTP_TIMEOUT", 180)
HTTP_TENTATIVAS = getattr(C, "HTTP_TENTATIVAS", 3)


def baixar_arquivo(
    url: str,
    destino: str | Path,
    timeout: int = HTTP_TIMEOUT,
    tentativas: int = HTTP_TENTATIVAS,
) -> Path:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    ultimo_erro: Exception | None = None

    for tentativa in range(1, tentativas + 1):
        try:
            print(f"[baixar_arquivo] tentativa {tentativa}/{tentativas} → {url}")

            with requests.get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()

                total = int(r.headers.get("content-length", 0))
                baixado = 0
                inicio = time.time()

                with open(destino, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1 MB
                        if chunk:
                            f.write(chunk)
                            baixado += len(chunk)

                            if total > 0:
                                percentual = baixado / total * 100
                                tempo = time.time() - inicio
                                print(
                                    f"\r{percentual:5.1f}% | "
                                    f"{baixado / 1024**2:,.1f} MB | "
                                    f"{tempo:.0f}s",
                                    end="",
                                    flush=True,
                                )

            print()  # nova linha após a barra de progresso
            return destino

        except requests.RequestException as e:
            ultimo_erro = e
            print(f"[baixar_arquivo] tentativa {tentativa}/{tentativas} falhou: {e}")
            time.sleep(2 * tentativa)

    raise RuntimeError(
        f"Falha ao baixar {url} após {tentativas} tentativas"
    ) from ultimo_erro


def coletar_amostra(
    n_paginas: int | None = None,   # mantido por compatibilidade, não é mais usado
    url: str = SRAG_PARQUET_URL,
    page_size: int | None = None,   # mantido por compatibilidade, não é mais usado
) -> pd.DataFrame:
    inicio = time.time()

    # ------------------------------------------------------------------
    # 1) Define diretório de destino
    # ------------------------------------------------------------------
    raw_dir = (
        Path.cwd().parent / "data" / "raw"
        if Path.cwd().name == "notebooks"
        else Path.cwd() / "data" / "raw"
    )
    raw_dir.mkdir(parents=True, exist_ok=True)

    nome_arquivo = url.split("/")[-1]  # ex: INFLUD23-16-10-2023.parquet
    destino = raw_dir / nome_arquivo

    # ------------------------------------------------------------------
    # 2) Baixa o arquivo (se ainda não existir)
    # ------------------------------------------------------------------
    if destino.exists():
        print(f"[coletar_amostra] arquivo já existe em {destino}, reutilizando.")
    else:
        baixar_arquivo(url, destino)

    # ------------------------------------------------------------------
    # 3) Lê o Parquet e retorna DataFrame
    # ------------------------------------------------------------------
    print(f"[coletar_amostra] lendo {destino} …")
    df = pd.read_parquet(destino)

    tempo = time.time() - inicio
    print(
        f"[coletar_amostra] {len(df):,} linhas em {tempo:.1f}s "
        f"({df.shape[1]} colunas)"
    )
    return df


# ---------------------------------------------------------------------------
# csv_to_parquet permanece inalterado (útil para outros fluxos)
# ---------------------------------------------------------------------------
def csv_to_parquet(
    csv_path: str | Path,
    out_path: str | Path,
    chunksize: int = 500_000,
) -> Path:
    csv_path = Path(csv_path)
    out_path = Path(out_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {csv_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

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

                percentual = min(arquivo.tell() / size * 100, 100)
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