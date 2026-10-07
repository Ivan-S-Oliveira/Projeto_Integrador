"""
Verifica que o ambiente e a configuração estão íntegros.

Estes testes são rápidos e não fazem I/O pesado — devem rodar sempre.
"""

from pathlib import Path

import pytest

from src.utils import config as C
from src.utils import env


# ---------------------------------------------------------------------------
# ROOT_DIR e ausência de caminhos pessoais
# ---------------------------------------------------------------------------

def test_root_dir_existe():
    assert C.ROOT_DIR.exists()
    assert C.ROOT_DIR.is_dir()


def test_root_dir_calculado_a_partir_do_arquivo():
    # <ROOT>/src/utils/config.py → parents[2] == <ROOT>
    esperado = Path(C.__file__).resolve().parents[2]
    assert C.ROOT_DIR == esperado


@pytest.mark.parametrize(
    "chave",
    ["ROOT_DIR", "DATA_DIR", "RAW_DIR", "PROCESSED_DIR", "REPORTS_DIR", "MODELS_DIR"],
)
def test_diretorios_derivam_da_raiz(chave):
    """Nenhum caminho deve conter C:/Users, OneDrive, /home/<algo>, etc."""
    valor: Path = getattr(C, chave)
    s = str(valor).replace("\\", "/").lower()

    proibidos = ["c:/users", "onedrive", "/home/", "/users/"]
    for termo in proibidos:
        assert termo not in s, f"{chave}={valor} contém caminho pessoal ({termo!r})"


# ---------------------------------------------------------------------------
# Reprodutibilidade
# ---------------------------------------------------------------------------

def test_seed_definido():
    assert isinstance(C.SEED, int)
    assert C.SEED == 42


def test_random_state_igual_ao_seed():
    assert C.RANDOM_STATE == C.SEED


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

def test_repo_e_data_version_definidos():
    assert C.GITHUB_REPO
    assert "/" in C.GITHUB_REPO  # formato owner/repo
    assert C.DATA_VERSION
    assert C.PARQUET_NAME.endswith(".parquet")


def test_srag_parquet_url_nao_vazia():
    assert C.SRAG_PARQUET_URL
    assert C.SRAG_PARQUET_URL.startswith("http")


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def test_parametros_http_razoaveis():
    assert C.HTTP_TIMEOUT > 0
    assert C.HTTP_TENTATIVAS >= 1
    assert C.HTTP_BACKOFF >= 0


# ---------------------------------------------------------------------------
# env.py
# ---------------------------------------------------------------------------

def test_env_aponta_para_mesma_raiz():
    assert env.ROOT == C.ROOT_DIR


def test_env_diretorios_padrao_existem():
    for p in (env.RAW, env.PROCESSED, env.TREINO, env.FIGURES):
        assert p.exists(), f"{p} não foi criado por env.garantir_diretorios()"


def test_env_resumo_nao_quebra():
    txt = env.resumo()
    assert "ROOT_DIR" in txt
    assert "ENV" in txt


def test_get_secret_obrigatorio_levanta_erro(monkeypatch):
    monkeypatch.delenv("VAR_QUE_NAO_EXISTE_XYZ", raising=False)
    with pytest.raises(RuntimeError, match="VAR_QUE_NAO_EXISTE_XYZ"):
        env.get_secret("VAR_QUE_NAO_EXISTE_XYZ")


def test_get_secret_opcional_retorna_none(monkeypatch):
    monkeypatch.delenv("VAR_OPCIONAL_XYZ", raising=False)
    assert env.get_secret("VAR_OPCIONAL_XYZ", obrigatorio=False) is None