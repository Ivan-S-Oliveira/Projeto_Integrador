"""Fixtures partilhadas entre testes."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.utils import config as C


@pytest.fixture(scope="session")
def parquet_disponivel() -> Path | None:
    """Parquet processado, ou ``None`` se ainda não foi gerado.

    Fixture de sessão — o path é calculado uma vez por execução. Testes
    que dependem dela devem fazer ``pytest.skip()`` quando o retorno é
    ``None`` (o Parquet não vem versionado no Git).
    """
    caminho = C.PROCESSED_DIR / C.DATA_VERSION / C.PARQUET_NAME
    return caminho if caminho.is_file() else None