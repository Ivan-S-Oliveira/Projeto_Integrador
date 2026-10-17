"""
Variáveis de ambiente e segredos do projeto.

Fluxo: ``.env`` → ``os.environ`` → ``config.py`` → restante do projeto.

O arquivo ``.env`` nunca é versionado (ver ``.gitignore``); use
``.env.example`` como template. Diretórios são aliases de
``src.utils.config``, fonte única da verdade.
"""

from __future__ import annotations

import os
from pathlib import Path

from src.utils import config as C


# Aliases públicos — conveniência para notebooks e testes.
ROOT      = C.ROOT_DIR
DATA      = C.DATA_DIR
RAW       = C.RAW_DIR
PROCESSED = C.PROCESSED_DIR
TREINO    = C.TREINO_DIR
FIGURES   = C.FIGURES_DIR

# Diretórios criados por ``garantir_diretorios``. A ordem não importa —
# ``mkdir(parents=True)`` cria a árvore conforme necessário.
_DIRS_PADRAO = (
    C.DATA_DIR, C.RAW_DIR, C.PROCESSED_DIR, C.ANALYTICAL_DIR,
    C.TREINO_DIR, C.CONFIGS_DIR, C.MODELS_DIR, C.OUTPUTS_DIR,
    C.RUNS_DIR, C.LOGS_DIR, C.REPORTS_DIR, C.FIGURES_DIR,
    C.TABLES_DIR, C.PREDICTIONS_DIR,
)


def garantir_diretorios() -> None:
    """Cria todos os diretórios padrão do projeto, se ainda não existirem.

    Percorre as constantes de ``config.py`` — nenhum caminho é redefinido aqui.
    """
    for p in _DIRS_PADRAO:
        p.mkdir(parents=True, exist_ok=True)


def carregar_dotenv(caminho: Path | None = None) -> bool:
    """Carrega ``.env`` da raiz do projeto (ou de ``caminho``).

    Retorna ``True`` se o arquivo foi encontrado e carregado, ``False`` caso
    contrário (arquivo ausente ou ``python-dotenv`` indisponível). Não
    sobrescreve variáveis já definidas no ambiente.
    """
    # Lazy: python-dotenv não é dependência obrigatória — permite importar
    # este módulo em ambientes que não o têm instalado.
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False

    caminho = Path(caminho) if caminho else ROOT / ".env"
    if not caminho.exists():
        return False

    load_dotenv(dotenv_path=caminho, override=False)
    return True


def detectar_ambiente() -> str:
    """``"ci"`` se estiver em pipeline, senão ``"local"``."""
    return "ci" if os.getenv("CI") or os.getenv("GITHUB_ACTIONS") else "local"


ENV = detectar_ambiente()


def get_env(nome: str, default: str | None = None) -> str | None:
    """Lê uma variável de ambiente, com default opcional."""
    return os.getenv(nome, default)


def get_secret(nome: str, obrigatorio: bool = True) -> str | None:
    """Lê um segredo/variável sensível do ambiente.

    Se ``obrigatorio=True`` (default) e a variável não existir, levanta
    ``RuntimeError`` com instruções de configuração. Se ``False``, devolve
    ``None``.
    """
    valor = os.getenv(nome)
    if valor:
        return valor
    if not obrigatorio:
        return None

    raise RuntimeError(
        f"Variável de ambiente '{nome}' não definida.\n"
        f"Defina-a de uma destas formas:\n"
        f"  1) Crie/edite o arquivo {ROOT / '.env'} (não versionado):\n"
        f"         {nome}=seu_valor_aqui\n"
        f"  2) Exporte no shell antes de rodar o projeto:\n"
        f"         Linux/macOS:  export {nome}=seu_valor_aqui\n"
        f"         PowerShell:   $env:{nome} = \"seu_valor_aqui\"\n"
    )


def resumo() -> str:
    """Resumo legível do estado do ambiente."""
    linhas = [
        ("ROOT_DIR",         ROOT),
        ("ENV",              ENV),
        (".env encontrado?", (ROOT / ".env").exists()),
        ("GITHUB_TOKEN?",    bool(os.getenv("GITHUB_TOKEN"))),
    ]
    return "\n".join(f"{nome:18s}= {valor}" for nome, valor in linhas)


if __name__ == "__main__":
    carregar_dotenv()
    garantir_diretorios()
    print(resumo())