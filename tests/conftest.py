"""
Fixtures e configuração de testes.

- `parquet_disponivel`: caminho do Parquet **oficial** (processado/versionado
  em `data/processed/<DATA_VERSION>/srag.parquet`), ou `None` se ainda não
  foi gerado. Não há fallback para arquivos brutos nem para amostras locais —
  quem depende dele deve tratar o `None` com `pytest.skip`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.utils import config as C


def pytest_configure(config: pytest.Config) -> None:
    """Registra os marcadores customizados do projeto (uma única vez)."""
    config.addinivalue_line(
        "markers",
        "slow: testes que tocam arquivos grandes (Parquet de SRAG).",
    )


@pytest.fixture(scope="session")
def parquet_disponivel() -> Path | None:
    """
    Parquet processado/versionado, se existir.

    Retorna `None` quando o arquivo ainda não foi gerado — os testes que
    dependem dele devem chamar `pytest.skip`.
    """
    caminho = C.PROCESSED_DIR / C.DATA_VERSION / C.PARQUET_NAME
    return caminho if caminho.exists() else None