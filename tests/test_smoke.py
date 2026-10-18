"""
Smoke tests do Parquet de SRAG.

Verificam que o dataset existe, abre, tem o schema esperado e produz uma
saída mínima. Todos os testes são marcados ``slow`` via ``pytestmark``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pytest

from src.utils import storage


pytestmark = pytest.mark.slow


# Colunas mínimas esperadas no SRAG; ajustar conforme o dicionário de dados.
COLUNAS_ESPERADAS: frozenset[str] = frozenset({"sg_uf", "dt_notific"})


@pytest.fixture
def parquet(parquet_disponivel: Path | None) -> Path:
    """``parquet_disponivel`` obrigatório — faz skip se ausente."""
    if parquet_disponivel is None:
        pytest.skip(
            "Nenhum Parquet encontrado. Rode 00_acesso_dados_parquet.ipynb "
            "ou 01_extracao.ipynb primeiro."
        )
    return parquet_disponivel


@pytest.fixture
def schema_colunas(parquet: Path) -> set[str]:
    """Nome das colunas do Parquet para os testes de schema."""
    return set(pq.read_schema(parquet).names)



# ---------------------------------------------------------------------------
# Estrutura do arquivo
# ---------------------------------------------------------------------------

def test_parquet_existe_e_nao_vazio(parquet: Path) -> None:
    assert parquet.is_file()
    assert parquet.stat().st_size > 0


def test_parquet_tem_magic_bytes(parquet: Path) -> None:
    with open(parquet, "rb") as f:
        magic = f.read(4)
    assert magic == b"PAR1", f"Arquivo não é Parquet válido (magic={magic!r})"


def test_parquet_abre(schema_colunas: set[str]) -> None:
    assert schema_colunas


def test_parquet_tem_colunas_esperadas(schema_colunas: set[str]) -> None:
    faltando = COLUNAS_ESPERADAS - schema_colunas
    assert not faltando, f"Colunas ausentes: {sorted(faltando)}"


# ---------------------------------------------------------------------------
# Leitura via pandas
# ---------------------------------------------------------------------------

def test_parquet_tem_registros(parquet: Path) -> None:
    df = pd.read_parquet(parquet, columns=["sg_uf"])
    assert len(df) > 0


def test_produz_saida_pequena(parquet: Path) -> None:
    """O smoke final — produzir uma saída minúscula funciona ponta-a-ponta."""
    df = pd.read_parquet(parquet, columns=["sg_uf"]).head(10)
    assert len(df) == 10


# ---------------------------------------------------------------------------
# Leitura via storage.read_srag
# ---------------------------------------------------------------------------

def test_storage_read_srag(parquet: Path) -> None:
    """``storage.read_srag`` devolve DataFrame não vazio com as colunas pedidas."""
    df = storage.read_srag(columns=["sg_uf"])
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "sg_uf" in df.columns


def test_storage_read_srag_com_filtro(parquet: Path) -> None:
    """O filtro ``sg_uf == "SP"`` é aplicado no lado do Parquet."""
    df = storage.read_srag(
        columns=["sg_uf"],
        filters=[("sg_uf", "==", "SP")],
    )
    if df.empty:
        pytest.skip("Nenhum registro de SP no dataset.")
    assert (df["sg_uf"] == "SP").all()