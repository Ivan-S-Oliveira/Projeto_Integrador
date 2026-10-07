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

def test_coletar_amostra_retorna_dataframe(parquet_disponivel):
    """Se já há Parquet em data/raw, deve reutilizar; caso contrário, tenta baixar."""
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível e download não testado em CI.")

    from src.data.extracao import coletar_amostra

    df = coletar_amostra()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert df.shape[1] > 0


def test_coletar_amostra_reaproveita_arquivo(parquet_disponivel):
    """Chamar duas vezes não deve re-baixar."""
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    from src.data.extracao import coletar_amostra

    df1 = coletar_amostra()
    df2 = coletar_amostra()
    assert len(df1) == len(df2)
    assert list(df1.columns) == list(df2.columns)


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
    assert env.RAW.exists()


def test_processed_dir_foi_criado():
    assert env.PROCESSED.exists()