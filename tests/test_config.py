"""Integridade do ambiente e da configuração do projeto."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.utils import config as C
from src.utils import env


def _url_parquet_esperada() -> str:
    """URL canônica do Parquet na release pública."""
    return (
        f"https://github.com/{C.GITHUB_REPO}/releases/download/"
        f"{C.DATA_VERSION}/{C.PARQUET_NAME}"
    )


# ---------------------------------------------------------------------------
# Raiz e diretórios
# ---------------------------------------------------------------------------

def test_root_dir_existe() -> None:
    assert C.ROOT_DIR.exists()
    assert C.ROOT_DIR.is_dir()


def test_root_dir_calculado_a_partir_do_arquivo() -> None:
    """``ROOT_DIR`` deriva de ``config.py`` (dois níveis acima: ``src/utils/``)."""
    assert C.ROOT_DIR == Path(C.__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "chave",
    ["DATA_DIR", "RAW_DIR", "PROCESSED_DIR", "REPORTS_DIR", "MODELS_DIR"],
)
def test_diretorios_derivam_da_raiz(chave: str) -> None:
    """Diretórios públicos derivam de ``ROOT_DIR``.

    O clone pode estar em ``C:/Users`` ou ``OneDrive`` — o que não pode
    é o caminho estar literalmente gravado em ``config.py``.
    """
    valor = getattr(C, chave)
    assert isinstance(valor, Path)
    assert valor.is_absolute()
    assert C.ROOT_DIR in valor.parents, f"{chave}={valor} não deriva de {C.ROOT_DIR}"


# ---------------------------------------------------------------------------
# Sem caminhos pessoais hardcoded
# ---------------------------------------------------------------------------

def _encontrar_caminhos_hardcoded(fonte: str, nomes_de_caminho: set[str]) -> list[dict]:
    """Inspeciona atribuições de ``nomes_de_caminho`` à procura de caminhos pessoais.

    Só atribuições são olhadas — comentários, docstrings e mensagens podem
    mencionar ``C:/Users`` ou ``/home`` sem serem configuração real.
    """
    proibidos = ("c:/users/", "/home/", "/users/")
    problemas: list[dict] = []

    for no in ast.walk(ast.parse(fonte)):
        if isinstance(no, ast.Assign) and len(no.targets) == 1:
            alvo, valor = no.targets[0], no.value
        elif isinstance(no, ast.AnnAssign):
            alvo, valor = no.target, no.value
        else:
            continue

        if valor is None or not isinstance(alvo, ast.Name) or alvo.id not in nomes_de_caminho:
            continue

        for item in ast.walk(valor):
            if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                continue
            texto = item.value.replace("\\", "/").lower()
            if termos := [t for t in proibidos if t in texto]:
                problemas.append({"constante": alvo.id, "valor": item.value, "termos": termos})

    return problemas


def test_config_nao_contem_caminho_pessoal_hardcoded() -> None:
    """Nenhuma constante de caminho em ``config.py`` tem caminho pessoal literal."""
    nomes_de_caminho = {
        "ROOT_DIR", "DATA_DIR", "RAW_DIR", "PROCESSED_DIR",
        "TREINO_DIR", "CONFIGS_DIR", "MODELS_DIR", "OUTPUTS_DIR",
        "RUNS_DIR", "LOGS_DIR", "REPORTS_DIR", "FIGURES_DIR",
        "TABLES_DIR", "PREDICTIONS_DIR", "SUPERVISED_YAML",
    }
    fonte = Path(C.__file__).read_text(encoding="utf-8")

    problemas = _encontrar_caminhos_hardcoded(fonte, nomes_de_caminho)
    assert not problemas, f"Caminhos pessoais hardcoded em constantes: {problemas}"


# ---------------------------------------------------------------------------
# Seed, versão e HTTP
# ---------------------------------------------------------------------------

def test_seed_definido() -> None:
    assert isinstance(C.SEED, int)
    assert C.SEED == 42


def test_random_state_igual_ao_seed() -> None:
    assert C.RANDOM_STATE == C.SEED


def test_repo_definido() -> None:
    assert C.GITHUB_REPO and "/" in C.GITHUB_REPO


def test_data_version_e_parquet_definidos() -> None:
    assert C.DATA_VERSION
    assert C.PARQUET_NAME.endswith(".parquet")


def test_parametros_http_razoaveis() -> None:
    assert C.HTTP_TIMEOUT > 0
    assert C.HTTP_TENTATIVAS >= 1
    assert C.HTTP_BACKOFF >= 0


# ---------------------------------------------------------------------------
# URL do Parquet — prioridade da variável de ambiente
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "valor_env, esperado_override",
    [
        (None, False),
        ("https://example.org/dados/srag_teste.parquet", True),
        ("   ", False),
    ],
    ids=["sem_env", "env_customizada", "env_vazia"],
)
def test_srag_parquet_url(valor_env, esperado_override, monkeypatch: pytest.MonkeyPatch) -> None:
    """``SRAG_PARQUET_URL`` sobrepõe a URL padrão; vazia cai no padrão."""
    if valor_env is None:
        monkeypatch.delenv("SRAG_PARQUET_URL", raising=False)
    else:
        monkeypatch.setenv("SRAG_PARQUET_URL", valor_env)

    url = C.srag_parquet_url()
    if esperado_override:
        assert valor_env is not None
        assert url == valor_env.strip()
    else:
        assert url == _url_parquet_esperada()


# ---------------------------------------------------------------------------
# env.py
# ---------------------------------------------------------------------------

def test_env_aponta_para_mesma_raiz() -> None:
    assert env.ROOT == C.ROOT_DIR


def test_env_diretorios_padrao_existem() -> None:
    env.garantir_diretorios()
    for caminho in (env.RAW, env.PROCESSED, env.TREINO, env.FIGURES):
        assert caminho.is_dir(), f"{caminho} não é diretório após garantir_diretorios()"


def test_env_resumo_nao_quebra() -> None:
    texto = env.resumo()
    assert "ROOT_DIR" in texto
    assert "ENV" in texto


def test_get_secret_obrigatorio_levanta_erro(monkeypatch: pytest.MonkeyPatch) -> None:
    nome = "VAR_QUE_NAO_EXISTE_XYZ"
    monkeypatch.delenv(nome, raising=False)
    with pytest.raises(RuntimeError, match=nome):
        env.get_secret(nome)


def test_get_secret_opcional_retorna_none(monkeypatch: pytest.MonkeyPatch) -> None:
    nome = "VAR_OPCIONAL_XYZ"
    monkeypatch.delenv(nome, raising=False)
    assert env.get_secret(nome, obrigatorio=False) is None


# ---------------------------------------------------------------------------
# Schema do Parquet (slow)
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_features_finais_existem_no_schema(parquet_disponivel) -> None:
    """Colunas do ``supervised.yaml`` existem no Parquet (ou são derivadas).

    Features derivadas (produzidas por ``montar_features``) não existem no
    Parquet bruto — excluídas da checagem. As colunas de entrada exigidas
    pela derivação são verificadas explicitamente.
    """
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    import pyarrow.parquet as pq
    from src.models import pipeline

    colunas = set(pq.read_schema(parquet_disponivel).names)
    derivadas = set(C.cfg("features", "engenharia", "derivadas") or [])
    entradas = set(C.cfg("features", "engenharia", "entradas") or [])
    base = set(pipeline.FEATURES) - derivadas

    faltando = (base | entradas) - colunas
    assert not faltando, f"Colunas ausentes no Parquet: {sorted(faltando)}"

# ---------------------------------------------------------------------------
# Consistência entre pyproject.toml e requirements.txt (#63)
# ---------------------------------------------------------------------------

def _nomes_diretos(specs: list[str]) -> set[str]:
    from packaging.requirements import Requirement

    return {Requirement(s).name.lower().replace("_", "-") for s in specs}


def test_requirements_cobre_dependencias_de_runtime_do_pyproject() -> None:
    """Toda dependência de runtime do pyproject está no requirements.txt.

    Se este teste falhar, alguém adicionou uma dependência nova em
    ``pyproject.toml`` (ou removeu do ``requirements.txt``) e os dois
    arquivos divergiram — exatamente o cenário do card #63.
    """
    import tomllib

    root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    declaradas = _nomes_diretos(pyproject["project"]["dependencies"])

    listadas: set[str] = set()
    for linha in (root / "requirements.txt").read_text(encoding="utf-8").splitlines():
        limpa = linha.split("#", 1)[0].strip()
        if not limpa or limpa.startswith("-"):
            continue
        listadas |= _nomes_diretos([limpa])

    faltando = sorted(declaradas - listadas)
    assert not faltando, (
        f"requirements.txt não inclui dependências de runtime: {faltando}. "
        "Atualize-o junto com pyproject.toml."
    )


def test_requirements_tem_versao_fixada() -> None:
    """Nenhum pacote no requirements.txt pode ficar sem versão.

    Um pacote sem ``==`` ou ``>=`` faz duas máquinas receberem versões
    diferentes com o mesmo repositório — o cenário do card #63.
    """
    root = Path(__file__).resolve().parents[1]
    sem_versao: list[str] = []
    for linha in (root / "requirements.txt").read_text(encoding="utf-8").splitlines():
        limpa = linha.split("#", 1)[0].strip()
        if not limpa or limpa.startswith("-"):
            continue
        if "==" not in limpa and ">=" not in limpa and "~=" not in limpa:
            sem_versao.append(limpa)

    assert not sem_versao, f"requirements.txt tem pacotes sem versão: {sem_versao}"