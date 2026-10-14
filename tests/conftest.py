"""Fixtures e configuração de testes."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.utils import config as C


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "slow: testes que tocam arquivos grandes (Parquet de SRAG).",
    )


@pytest.fixture(scope="session")
def parquet_disponivel() -> Path | None:
    """Retorna o Parquet processado, ou None se ainda não foi gerado."""
    caminho = C.PROCESSED_DIR / C.DATA_VERSION / C.PARQUET_NAME
    return caminho if caminho.is_file() else None