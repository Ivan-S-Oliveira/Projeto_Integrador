"""
Smoke tests: o dataset existe, abre, tem colunas e registros?

Todos os testes são marcados como `slow` via `pytestmark`.
Rode com: pytest -m slow
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.utils import config as C


pytestmark = pytest.mark.slow


@pytest.fixture
def parquet(parquet_disponivel: Path | None) -> Path:
    """Versão obrigatória de `parquet_disponivel`, com skip se ausente."""
    if parquet_disponivel is None:
        pytest.skip(
            "Nenhum Parquet encontrado. Rode 00_acesso_dados_parquet.ipynb "
            "ou 01_extracao.ipynb primeiro."
        )
    return parquet_disponivel


def test_parquet_existe(parquet: Path) -> None:
    assert parquet.exists()
    assert parquet.stat().st_size > 0


def test_parquet_tem_magic_bytes(parquet: Path) -> None:
    with open(parquet, "rb") as f:
        magic = f.read(4)
    assert magic == b"PAR1", f"Arquivo não é Parquet válido (magic={magic!r})"


def test_parquet_abre(parquet: Path) -> None:
    import pyarrow.parquet as pq

    schema = pq.read_schema(parquet)
    assert len(schema.names) > 0


def test_parquet_tem_colunas_esperadas(parquet: Path) -> None:
    import pyarrow.parquet as pq

    colunas = set(pq.read_schema(parquet).names)

    # Colunas mínimas esperadas no SRAG; ajustar conforme o dicionário de dados.
    esperadas = {"sg_uf", "dt_notific"}
    faltando = esperadas - colunas

    assert not faltando, f"Colunas ausentes: {faltando}"


def test_parquet_tem_registros(parquet: Path) -> None:
    df = pd.read_parquet(parquet, columns=["sg_uf"])
    assert len(df) > 0


def test_leitura_de_uma_coluna(parquet: Path) -> None:
    df = pd.read_parquet(parquet, columns=["sg_uf"])
    assert df.shape[1] == 1
    assert "sg_uf" in df.columns


def test_produz_saida_pequena(parquet: Path) -> None:
    """Confirma que conseguimos produzir uma saída minúscula — o smoke final."""
    df = pd.read_parquet(parquet, columns=["sg_uf"]).head(10)
    assert len(df) == 10
    assert df["sg_uf"].value_counts().sum() == 10


def test_storage_read_srag(parquet: Path) -> None:
    from src.utils import storage

    df = storage.read_srag(columns=["sg_uf"])
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "sg_uf" in df.columns


def test_storage_read_srag_com_filtro(parquet: Path) -> None:
    from src.utils import storage

    df = storage.read_srag(
        columns=["sg_uf"],
        filters=[("sg_uf", "==", "SP")],
    )
    if len(df) == 0:
        pytest.skip("Nenhum registro de SP no dataset.")
    assert (df["sg_uf"] == "SP").all()