"""
Testes do pipeline de ingestão: extracao.py, read_srag, csv_to_parquet.

Testes que tocam arquivos grandes são marcados com `@pytest.mark.slow`.
Os testes de diretório são rápidos e não recebem esse marcador.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.utils import env


# ---------------------------------------------------------------------------
# Leitura do Parquet local
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_read_srag_retorna_dataframe(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    from src.utils.storage import read_srag

    df = read_srag(columns=["sg_uf", "dt_notific"])

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert {"sg_uf", "dt_notific"}.issubset(set(df.columns))


@pytest.mark.slow
def test_get_parquet_reaproveita_arquivo(parquet_disponivel):
    """`force=False` reutiliza o arquivo existente (mesmo mtime e tamanho)."""
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    from src.utils.storage import get_parquet

    caminho_1 = get_parquet(force=False)
    estado_1 = caminho_1.stat()

    caminho_2 = get_parquet(force=False)
    estado_2 = caminho_2.stat()

    assert caminho_1.resolve() == caminho_2.resolve()
    assert estado_1.st_mtime_ns == estado_2.st_mtime_ns
    assert estado_1.st_size == estado_2.st_size


# ---------------------------------------------------------------------------
# csv_to_parquet
# ---------------------------------------------------------------------------

def test_csv_to_parquet_round_trip(tmp_path):
    """CSV pequeno → Parquet → lê de volta e confere."""
    from src.data.extracao import csv_to_parquet

    csv_path = tmp_path / "amostra.csv"
    parquet_path = tmp_path / "amostra.parquet"

    df_orig = pd.DataFrame({
        "sg_uf": ["SP", "RJ", "MG"],
        "dt_notific": ["2024-01-01", "2024-01-02", "2024-01-03"],
    })
    df_orig.to_csv(csv_path, index=False, encoding="utf-8-sig")

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
# Pipeline supervisionado: feature ausente
# ---------------------------------------------------------------------------

def test_build_pipeline_falha_feature_ausente():
    """`build_pipeline(strict=True)` levanta KeyError quando falta feature."""
    from src.models.pipeline import build_pipeline

    # Falta propositalmente o conjunto de categóricas declarado no YAML.
    X = pd.DataFrame({"nu_idade_n": [30.0, 40.0, 50.0]})

    with pytest.raises(KeyError, match="ausentes"):
        build_pipeline(X=X)


def test_build_pipeline_strict_false_avisa_mas_continua(caplog):
    """`strict=False` emite warning e segue com as features presentes."""
    from src.models.pipeline import build_pipeline

    X = pd.DataFrame({"nu_idade_n": [30.0, 40.0, 50.0]})

    with caplog.at_level("WARNING"):
        pipe = build_pipeline(X=X, strict=False)

    assert pipe is not None
    assert "ausentes" in caplog.text.lower()


# ---------------------------------------------------------------------------
# Diretórios (rápidos)
# ---------------------------------------------------------------------------

def test_raw_dir_foi_criado():
    env.garantir_diretorios()
    assert env.RAW.exists()
    assert env.RAW.is_dir()


def test_processed_dir_foi_criado():
    env.garantir_diretorios()
    assert env.PROCESSED.exists()
    assert env.PROCESSED.is_dir()