"""Fixtures partilhadas entre testes."""

from __future__ import annotations

from pathlib import Path

import pytest

from src import config as C


@pytest.fixture(scope="session")
def parquet_disponivel() -> Path | None:
    """Parquet processado, ou ``None`` se ainda não foi gerado."""
    caminho = C.PROCESSED_DIR / C.DATA_VERSION / C.PARQUET_NAME
    return caminho if caminho.is_file() else None