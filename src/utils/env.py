"""
Carregamento de variáveis de ambiente e segredos do projeto.

Fluxo:
    .env  →  os.environ  →  config.py  →  restante do projeto

Regras:
- O arquivo .env NUNCA vai para o Git (ver .gitignore).
- Use .env.example como template versionado.
- Não há dependência de Colab, Kaggle ou qualquer ambiente específico.
- Em CI/CD ou produção, defina as variáveis diretamente no ambiente;
  o .env é opcional e serve apenas para desenvolvimento local.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Raiz do projeto: <ROOT>/src/utils/env.py → parents[2] = <ROOT>
# ---------------------------------------------------------------------------
ROOT: Path = Path(__file__).resolve().parents[2]

# Diretórios padrão do projeto
DATA      = ROOT / "data"
RAW       = DATA / "raw"
PROCESSED = DATA / "processed"
TREINO    = DATA / "treino"
FIGURES   = ROOT / "reports" / "figures"


def garantir_diretorios() -> None:
    """Cria os diretórios padrão do projeto, se ainda não existirem."""
    for p in (RAW, PROCESSED, TREINO, FIGURES):
        p.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Carregamento do .env (opcional)
# ---------------------------------------------------------------------------
# python-dotenv é opcional: se não estiver instalado, seguimos apenas com
# variáveis de ambiente já definidas no sistema.
# ---------------------------------------------------------------------------
def carregar_dotenv(caminho: Path | None = None) -> bool:
    """
    Carrega o arquivo .env da raiz do projeto (ou o caminho informado).

    Retorna True se o arquivo foi encontrado e carregado, False caso contrário.
    Não sobrescreve variáveis já definidas no ambiente (override=False).
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False

    caminho = Path(caminho) if caminho else ROOT / ".env"

    if not caminho.exists():
        return False

    load_dotenv(dotenv_path=caminho, override=False)
    return True


# ---------------------------------------------------------------------------
# Detecção do ambiente (apenas informativa)
# ---------------------------------------------------------------------------
def detectar_ambiente() -> str:
    """
    Retorna 'ci' se estiver em pipeline, senão 'local'.

    Não é mais usado para escolher fonte de segredos — apenas para logs.
    """
    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
        return "ci"
    return "local"


ENV = detectar_ambiente()


# ---------------------------------------------------------------------------
# Acesso a variáveis e segredos
# ---------------------------------------------------------------------------
def get_env(nome: str, default: str | None = None) -> str | None:
    """Lê uma variável de ambiente, com default opcional."""
    return os.getenv(nome, default)


def get_secret(nome: str, obrigatorio: bool = True) -> str | None:
    """
    Lê um segredo/variável sensível do ambiente.

    Parâmetros
    ----------
    nome : str
        Nome da variável (ex.: 'GITHUB_TOKEN').
    obrigatorio : bool
        Se True (padrão) e a variável não existir, levanta RuntimeError
        com mensagem explicativa. Se False, retorna None.

    Uso
    ---
    >>> token = get_secret("GITHUB_TOKEN", obrigatorio=False)
    >>> if token: ...
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


# ---------------------------------------------------------------------------
# Diagnóstico
# ---------------------------------------------------------------------------
def resumo() -> str:
    """Resumo legível do estado do ambiente."""
    tem_env_file = (ROOT / ".env").exists()
    return (
        f"ROOT_DIR         = {ROOT}\n"
        f"ENV              = {ENV}\n"
        f".env encontrado? = {tem_env_file}\n"
        f"GITHUB_TOKEN?    = {bool(os.getenv('GITHUB_TOKEN'))}\n"
    )


# ---------------------------------------------------------------------------
# Execução direta: prepara diretórios e mostra o resumo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    carregar_dotenv()
    garantir_diretorios()
    print(resumo())