"""
Smoke tests: o dataset existe, abre, tem colunas e registros?

Todos os testes de I/O estão marcados como `slow`.
Rode com:  pytest -m slow
"""

import pandas as pd
import pytest

from src.utils import config as C


pytestmark = pytest.mark.slow


# ---------------------------------------------------------------------------
# Existência e integridade do arquivo
# ---------------------------------------------------------------------------

def test_parquet_existe(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip(
            "Nenhum Parquet encontrado. Rode 00_acesso_dados_parquet.ipynb "
            "ou 01_extracao.ipynb primeiro."
        )
    assert parquet_disponivel.exists()
    assert parquet_disponivel.stat().st_size > 0


def test_parquet_tem_magic_bytes(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    with open(parquet_disponivel, "rb") as f:
        magic = f.read(4)
    assert magic == b"PAR1", f"Arquivo não é Parquet válido (magic={magic!r})"


# ---------------------------------------------------------------------------
# Abertura e esquema
# ---------------------------------------------------------------------------

def test_parquet_abre(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    import pyarrow.parquet as pq

    schema = pq.read_schema(parquet_disponivel)
    assert len(schema.names) > 0


def test_parquet_tem_colunas_esperadas(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    import pyarrow.parquet as pq

    schema = pq.read_schema(parquet_disponivel)
    colunas = set(schema.names)

    # Colunas mínimas que o projeto espera encontrar no SRAG.
    # Ajuste aqui conforme o dicionário de dados for consolidado.
    esperadas = {"sg_uf", "dt_notific"}
    faltando = esperadas - colunas

    assert not faltando, f"Colunas ausentes: {faltando}"


# ---------------------------------------------------------------------------
# Leitura e registros
# ---------------------------------------------------------------------------

def test_parquet_tem_registros(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    df = pd.read_parquet(parquet_disponivel, columns=["sg_uf"])
    assert len(df) > 0


def test_leitura_de_uma_coluna(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    df = pd.read_parquet(parquet_disponivel, columns=["sg_uf"])
    assert df.shape[1] == 1
    assert "sg_uf" in df.columns


def test_produz_saida_pequena(parquet_disponivel):
    """Confirma que conseguimos produzir uma saída minúscula — o 'smoke' final."""
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    df = pd.read_parquet(parquet_disponivel, columns=["sg_uf"]).head(10)
    assert len(df) == 10
    # Uma contagem simples, só pra exercitar o DataFrame
    contagem = df["sg_uf"].value_counts()
    assert contagem.sum() == 10


# ---------------------------------------------------------------------------
# storage.py
# ---------------------------------------------------------------------------

def test_storage_read_srag(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    from src.utils import storage

    df = storage.read_srag(columns=["sg_uf"])
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "sg_uf" in df.columns


def test_storage_read_srag_com_filtro(parquet_disponivel):
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")
    from src.utils import storage

    df = storage.read_srag(
        columns=["sg_uf"],
        filters=[("sg_uf", "==", "SP")],
    )
    if len(df) == 0:
        pytest.skip("Nenhum registro de SP no dataset.")
    assert (df["sg_uf"] == "SP").all()