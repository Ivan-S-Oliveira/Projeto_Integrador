"""
Testes do pipeline de ingestão: extracao.py, read_srag, csv_to_parquet.

Marcados como `slow` porque tocam arquivos grandes.
"""

from pathlib import Path

import pandas as pd
import pytest

from src.utils import config as C, env


pytestmark = pytest.mark.slow


# ---------------------------------------------------------------------------
# coletar_amostra — download do Parquet
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Leitura do Parquet local
# ---------------------------------------------------------------------------

def test_read_srag_retorna_dataframe(
    parquet_disponivel,
):
    """
    Valida o caminho oficial de leitura local do projeto.
    """
    if parquet_disponivel is None:
        pytest.skip(
            "Parquet nao disponivel."
        )

    from src.utils.storage import read_srag

    df = read_srag(
        columns=[
            "sg_uf",
            "dt_notific",
        ]
    )

    assert isinstance(
        df,
        pd.DataFrame,
    )

    assert not df.empty

    assert {
        "sg_uf",
        "dt_notific",
    }.issubset(
        set(df.columns)
    )


def test_get_parquet_reaproveita_arquivo(
    parquet_disponivel,
):
    """
    get_parquet com force igual a False deve reutilizar
    o arquivo existente.
    """
    if parquet_disponivel is None:
        pytest.skip(
            "Parquet nao disponivel."
        )

    from src.utils.storage import get_parquet

    caminho_1 = Path(
        get_parquet(force=False)
    )

    estado_1 = caminho_1.stat()

    caminho_2 = Path(
        get_parquet(force=False)
    )

    estado_2 = caminho_2.stat()

    assert (
        caminho_1.resolve()
        == caminho_2.resolve()
    )

    assert (
        estado_1.st_mtime_ns
        == estado_2.st_mtime_ns
    )

    assert (
        estado_1.st_size
        == estado_2.st_size
    )


# ---------------------------------------------------------------------------
# csv_to_parquet
# ---------------------------------------------------------------------------

def test_csv_to_parquet_round_trip(tmp_path):
    """CSV pequeno → Parquet → lê de volta e confere."""
    from src.data.extracao import csv_to_parquet

    csv_path = tmp_path / "amostra.csv"
    parquet_path = tmp_path / "amostra.parquet"

    df_orig = pd.DataFrame(
        {
            "sg_uf": ["SP", "RJ", "MG"],
            "dt_notific": ["2024-01-01", "2024-01-02", "2024-01-03"],
        }
    )
    df_orig.to_csv(csv_path, index=False, encoding="utf-8-sig")

    # csv_to_parquet usa C.COLS e C.CSV_SEP; como C.COLS = None, lê tudo
    csv_to_parquet(csv_path=csv_path, out_path=parquet_path)

    assert parquet_path.exists()
    df_lido = pd.read_parquet(parquet_path)
    assert len(df_lido) == len(df_orig)
    assert set(df_lido.columns) >= set(df_orig.columns)


def test_csv_to_parquet_erro_quando_csv_inexistente(tmp_path):
    from src.data.extracao import csv_to_parquet

    with pytest.raises(FileNotFoundError):
        csv_to_parquet(
            csv_path=tmp_path / "nao_existe.csv",
            out_path=tmp_path / "saida.parquet",
        )


# ---------------------------------------------------------------------------
# Diretórios
# ---------------------------------------------------------------------------

def test_raw_dir_foi_criado():
    env.garantir_diretorios()

    assert env.RAW.exists()
    assert env.RAW.is_dir()


def test_processed_dir_foi_criado():
    env.garantir_diretorios()

    assert env.PROCESSED.exists()
    assert env.PROCESSED.is_dir()