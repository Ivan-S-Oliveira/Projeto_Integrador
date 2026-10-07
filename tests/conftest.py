"""
Fixtures compartilhadas e marcação de testes.

Marcadores:
    slow  → testes que fazem I/O pesado (download/leitura do Parquet completo)
    net   → testes que exigem acesso à internet

Uso:
    pytest                       # só testes rápidos
    pytest -m slow               # só testes lentos
    pytest -m "not slow"         # idem ao primeiro
    pytest -m "slow and net"     # testes lentos que precisam de rede
"""

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils import env, config as C  # noqa: E402


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: teste lento (I/O pesado)")
    config.addinivalue_line("markers", "net:  teste que exige internet")


# ---------------------------------------------------------------------------
# Fixtures de caminhos
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def root_dir() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def processed_dir() -> Path:
    return env.PROCESSED


@pytest.fixture(scope="session")
def parquet_disponivel() -> Path | None:
    """
    Retorna o primeiro Parquet de SRAG encontrado, ou None.

    Ordem de preferência:
        1) data/processed/dados-v1/srag.parquet   (release oficial)
        2) data/processed/srag_amostra.parquet    (extração local)
        3) data/raw/*.parquet                     (baixado por extracao.py)
    """
    candidatos = [
        env.PROCESSED / C.DATA_VERSION / C.PARQUET_NAME,
        env.PROCESSED / "srag_amostra.parquet",
    ]
    candidatos += sorted((env.RAW).glob("*.parquet"))

    for p in candidatos:
        if p.exists():
            return p
    return None