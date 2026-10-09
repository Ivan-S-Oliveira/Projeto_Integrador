"""
Coleta do Parquet bruto de SRAG — fonte upstream (OpenDataSUS).

Diferente de `src.utils.storage`, que serve o Parquet **processado** a
partir de GitHub Release, este módulo baixa o arquivo **bruto** direto
do repositório do Ministério da Saúde e o coloca em `data/raw/`,
preservando o nome original (ex.: `INFLUD24-16-12-2024.parquet`).

O trabalho pesado de rede (retry, verificação de magic bytes, sidecar
`.sha256`) fica em `src.utils.storage.download_file` — fonte única para
download HTTP de Parquet no projeto.

Também expõe `csv_to_parquet`, para converter CSVs grandes em Parquet
em chunks (útil quando a fonte upstream publica CSV).
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.utils import config as C
from src.utils.storage import PARQUET_MAGIC, download_file, sha256_path


def baixar_srag_bruto(
    url: str | None = None,
    *,
    force: bool = False,
) -> Path:
    """
    Baixa o Parquet bruto de SRAG para `data/raw/` e devolve o caminho.

    Diferente de `src.utils.storage.get_parquet`, que serve o Parquet
    processado/versionado via GitHub Release, este download preserva o
    arquivo original do OpenDataSUS em `data/raw/<nome-original>`.

    Parâmetros
    ----------
    url : str | None
        URL do Parquet. Se None, usa `C.srag_parquet_url()` — default do
        OpenDataSUS, sobrescrevível pela variável de ambiente
        `SRAG_PARQUET_URL`.
    force : bool
        Se True, rebaixa mesmo que o arquivo exista localmente e
        descarta o sidecar `.sha256` antigo.

    Retorno
    -------
    Path
        Caminho do arquivo bruto baixado.

    Efeitos colaterais
    ------------------
    - Arquivo gravado em `data/raw/<nome-do-arquivo>`.
    - Sidecar `<arquivo>.sha256` com o hash do conteúdo.
    - SHA-256 e tamanho impressos no stdout.
    """
    url = url or C.srag_parquet_url()
    nome = url.split("/")[-1]

    C.RAW_DIR.mkdir(parents=True, exist_ok=True)
    destino = C.RAW_DIR / nome

    if destino.exists() and not force:
        digest_antigo = None
        sidecar = sha256_path(destino)
        if sidecar.exists():
            digest_antigo = sidecar.read_text(encoding="utf-8").split()[0]
        print(
            f"[baixar_srag_bruto] reutilizando {destino}"
            + (f"  sha256={digest_antigo}" if digest_antigo else "")
        )
        return destino

    if force and destino.exists():
        destino.unlink()
        sha256_path(destino).unlink(missing_ok=True)

    inicio = time.time()
    digest = download_file(
        url,
        destino,
        expected_magic=PARQUET_MAGIC,
    )
    duracao = time.time() - inicio

    print(
        f"[baixar_srag_bruto] {destino.name} "
        f"({destino.stat().st_size / 1e6:.1f} MB) em {duracao:.0f}s"
    )
    print(f"[baixar_srag_bruto] SHA-256: {digest}")
    return destino


def csv_to_parquet(
    csv_path: str | Path,
    out_path: str | Path,
    chunksize: int = 500_000,
) -> Path:
    """
    Converte um CSV grande em Parquet em chunks, com compressão zstd.

    Lê o CSV em pedaços de `chunksize` linhas, converte cada chunk para
    string e escreve incrementalmente com `pyarrow.parquet.ParquetWriter`
    — o arquivo inteiro nunca é carregado de uma vez.

    Parâmetros
    ----------
    csv_path : str | Path
        CSV de origem. Precisa existir.
    out_path : str | Path
        Parquet de destino. O diretório pai é criado se necessário.
    chunksize : int
        Linhas por chunk.

    Retorno
    -------
    Path
        Caminho do Parquet gerado.

    Levanta
    ------
    FileNotFoundError
        Se `csv_path` não existir.
    """
    csv_path = Path(csv_path)
    out_path = Path(out_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {csv_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    size = csv_path.stat().st_size
    writer: pq.ParquetWriter | None = None
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
                        compression=C.PARQUET_COMPRESSION,
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