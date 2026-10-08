"""
Verifica que o ambiente e a configuracao estao integros.

Estes testes sao rapidos e nao fazem I/O pesado.
Devem rodar em toda validacao local e em CI.
"""

import ast

from pathlib import Path
import pytest

from src.utils import config as C
from src.utils import env


def test_root_dir_existe():
    assert C.ROOT_DIR.exists()
    assert C.ROOT_DIR.is_dir()


def test_root_dir_calculado_a_partir_do_arquivo():
    esperado = Path(C.__file__).resolve().parents[2]

    assert C.ROOT_DIR == esperado


@pytest.mark.parametrize(
    "chave",
    [
        "DATA_DIR",
        "RAW_DIR",
        "PROCESSED_DIR",
        "REPORTS_DIR",
        "MODELS_DIR",
    ],
)
def test_diretorios_derivam_da_raiz(chave):
    """
    Os diretorios do projeto devem derivar de ROOT_DIR.

    O caminho absoluto pode conter C:/Users ou OneDrive porque
    esse pode ser o local real do clone. O que nao pode existir
    e um caminho pessoal gravado diretamente em config.py.
    """
    valor = getattr(C, chave)

    assert isinstance(valor, Path)

    assert valor.is_absolute(), (
        f"{chave} deveria ser um caminho absoluto."
    )

    assert C.ROOT_DIR in valor.parents, (
        f"{chave}={valor} nao deriva de "
        f"ROOT_DIR={C.ROOT_DIR}"
    )


def test_config_nao_contem_caminho_pessoal_hardcoded():
    """
    Examina somente atribuicoes de constantes relacionadas
    a caminhos.

    Comentarios, docstrings e mensagens explicativas podem
    mencionar exemplos como C:/Users ou /home sem representar
    uma configuracao real do projeto.
    """
    caminho_config = Path(C.__file__)

    fonte = caminho_config.read_text(
        encoding="utf-8"
    )

    arvore = ast.parse(
        fonte,
        filename=str(caminho_config),
    )

    nomes_de_caminho = {
        "ROOT_DIR",
        "DATA_DIR",
        "RAW_DIR",
        "PROCESSED_DIR",
        "TREINO_DIR",
        "CONFIGS_DIR",
        "MODELS_DIR",
        "OUTPUTS_DIR",
        "RUNS_DIR",
        "LOGS_DIR",
        "REPORTS_DIR",
        "FIGURES_DIR",
        "TABLES_DIR",
        "PREDICTIONS_DIR",
        "SUPERVISED_YAML",
    }

    proibidos = [
        "c:/users/",
        "/home/",
        "/users/",
        "onedrive - pfizer",
    ]

    problemas = []

    for no in ast.walk(arvore):
        nome_alvo = None
        valor = None

        if isinstance(no, ast.Assign):
            if len(no.targets) != 1:
                continue

            alvo = no.targets[0]

            if isinstance(alvo, ast.Name):
                nome_alvo = alvo.id
                valor = no.value

        elif isinstance(no, ast.AnnAssign):
            alvo = no.target

            if isinstance(alvo, ast.Name):
                nome_alvo = alvo.id
                valor = no.value

        if nome_alvo not in nomes_de_caminho:
            continue

        if valor is None:
            continue

        valores_textuais = [
            item.value
            for item in ast.walk(valor)
            if isinstance(item, ast.Constant)
            and isinstance(item.value, str)
        ]

        for texto in valores_textuais:
            texto_normalizado = (
                texto
                .replace("\\", "/")
                .lower()
            )

            encontrados = [
                termo
                for termo in proibidos
                if termo in texto_normalizado
            ]

            if encontrados:
                problemas.append(
                    {
                        "constante": nome_alvo,
                        "valor": texto,
                        "termos": encontrados,
                    }
                )

    assert not problemas, (
        "Foram encontrados caminhos pessoais hard-coded "
        "em constantes de configuracao: "
        f"{problemas}"
    )


def test_seed_definido():
    assert isinstance(C.SEED, int)
    assert C.SEED == 42


def test_random_state_igual_ao_seed():
    assert C.RANDOM_STATE == C.SEED


def test_repo_e_data_version_definidos():
    assert C.GITHUB_REPO
    assert "/" in C.GITHUB_REPO
    assert C.DATA_VERSION
    assert C.PARQUET_NAME.endswith(".parquet")


def test_srag_parquet_url_nao_vazia():
    url = C.srag_parquet_url()

    assert isinstance(url, str)
    assert url.strip()
    assert url.startswith(("http://", "https://"))


def test_parametros_http_razoaveis():
    assert C.HTTP_TIMEOUT > 0
    assert C.HTTP_TENTATIVAS >= 1
    assert C.HTTP_BACKOFF >= 0


def test_env_aponta_para_mesma_raiz():
    assert env.ROOT == C.ROOT_DIR


def test_env_diretorios_padrao_existem():
    env.garantir_diretorios()

    caminhos = [
        env.RAW,
        env.PROCESSED,
        env.TREINO,
        env.FIGURES,
    ]

    for caminho in caminhos:
        assert caminho.exists(), (
            f"{caminho} nao foi criado por "
            "env.garantir_diretorios()"
        )

        assert caminho.is_dir(), (
            f"{caminho} existe, mas nao e um diretorio."
        )


def test_env_resumo_nao_quebra():
    texto = env.resumo()

    assert "ROOT_DIR" in texto
    assert "ENV" in texto


def test_get_secret_obrigatorio_levanta_erro(
    monkeypatch,
):
    nome = "VAR_QUE_NAO_EXISTE_XYZ"

    monkeypatch.delenv(
        nome,
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match=nome,
    ):
        env.get_secret(nome)


def test_get_secret_opcional_retorna_none(
    monkeypatch,
):
    nome = "VAR_OPCIONAL_XYZ"

    monkeypatch.delenv(
        nome,
        raising=False,
    )

    assert env.get_secret(
        nome,
        obrigatorio=False,
    ) is None