"""
Configurações centralizadas do Projeto Integrador.

Regras deste módulo:
- NÃO usar caminhos pessoais (C:/Users/... , /home/fulano/...).
- NÃO usar caminhos absolutos externos ao projeto.
- Todos os caminhos derivam de ROOT_DIR, calculado a partir deste arquivo.
- Segredos e URLs sensíveis são lidos LAZILY (função), nunca no import —
  porque o `.env` é carregado por `env.carregar_dotenv()` depois.
- O YAML de configuração (`configs/supervised.yaml`) também é lido LAZILY
  e cacheado, pelo mesmo motivo.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Raiz do projeto
# ---------------------------------------------------------------------------
# <ROOT>/src/utils/config.py → parents[2] = <ROOT>
# ---------------------------------------------------------------------------
ROOT_DIR: Path = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Reprodutibilidade
# ---------------------------------------------------------------------------
SEED = 42
RANDOM_STATE = SEED


# ---------------------------------------------------------------------------
# Diretórios do projeto (fonte única da verdade)
# ---------------------------------------------------------------------------
DATA_DIR      = ROOT_DIR / "data"
RAW_DIR       = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
TREINO_DIR    = DATA_DIR / "treino"

CONFIGS_DIR   = ROOT_DIR / "configs"
MODELS_DIR    = ROOT_DIR / "models"
OUTPUTS_DIR   = ROOT_DIR / "outputs"
RUNS_DIR      = OUTPUTS_DIR / "runs"
LOGS_DIR      = ROOT_DIR / "logs"
REPORTS_DIR   = ROOT_DIR / "reports"
FIGURES_DIR   = REPORTS_DIR / "figures"

TABLES_DIR        = OUTPUTS_DIR / "tables"
PREDICTIONS_DIR   = OUTPUTS_DIR / "predictions"


# ---------------------------------------------------------------------------
# Arquivos de configuração do projeto
# ---------------------------------------------------------------------------
SUPERVISED_YAML = CONFIGS_DIR / "supervised.yaml"


# ---------------------------------------------------------------------------
# Dataset processado (versão distribuída via GitHub Release)
# ---------------------------------------------------------------------------
GITHUB_REPO  = "Ivan-S-Oliveira/Projeto_Integrador"
DATA_VERSION = "dados-v1"
PARQUET_NAME = "srag.parquet"

GITHUB_RELEASE_URL = (
    f"https://github.com/{GITHUB_REPO}/releases/download/{DATA_VERSION}/"
)


# ---------------------------------------------------------------------------
# Segredos e URLs sensíveis — LEITURA LAZY
# ---------------------------------------------------------------------------
# Não use estas constantes em tempo de import. Chame as funções abaixo,
# sempre depois de `env.carregar_dotenv()`. Assim o `.env` funciona.
# ---------------------------------------------------------------------------

def github_token() -> str | None:
    """Token do GitHub — lido a cada chamada (permite .env tardio)."""
    return os.getenv("GITHUB_TOKEN")


def srag_parquet_url() -> str:
    """
    URL do Parquet do SRAG 2019–2026.

    Override via variável de ambiente `SRAG_PARQUET_URL`.
    O link do Parquet muda semanalmente — atualize em:
      https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026
    """
    return os.getenv(
        "SRAG_PARQUET_URL",
        "https://s3.sa-east-1.amazonaws.com/"
        "ckan.saude.gov.br/SRAG/2023/INFLUD23-16-10-2023.parquet",
    )


# ---------------------------------------------------------------------------
# Configuração supervisionada — LEITURA LAZY + CACHEADa
# ---------------------------------------------------------------------------
# Interpolação simples de ${VAR} com variáveis de ambiente. Útil quando o
# YAML quiser referenciar algo do .env (ex.: caminhos de artefato).
# ---------------------------------------------------------------------------
_ENV_PATTERN = re.compile(r"\$\{(\w+)\}")


def _interpolar_env(texto: str) -> str:
    """Substitui `${VAR}` pelo valor de os.environ (vazio se ausente)."""
    return _ENV_PATTERN.sub(lambda m: os.getenv(m.group(1), ""), texto)


@lru_cache(maxsize=1)
def carregar_supervised() -> dict[str, Any]:
    """
    Lê `configs/supervised.yaml` de forma lazy e cacheada.

    Regras:
    - Import de `yaml` é local (dependência opcional em tempo de import).
    - Se o arquivo não existir, levanta FileNotFoundError com instrução.
    - Suporta `${VAR}` interpolado a partir do ambiente.
    - O resultado é cacheado — para recarregar após editar o YAML, chame
      `carregar_supervised.cache_clear()`.
    """
    if not SUPERVISED_YAML.exists():
        raise FileNotFoundError(
            f"Configuração não encontrada: {SUPERVISED_YAML}\n"
            f"Crie o arquivo em {CONFIGS_DIR}/supervised.yaml "
            f"ou ajuste CONFIGS_DIR / SUPERVISED_YAML em config.py."
        )

    try:
        import yaml  # import local: não quebra quem não usa o YAML
    except ImportError as e:
        raise ImportError(
            "PyYAML não está instalado. Rode: pip install pyyaml"
        ) from e

    texto = _interpolar_env(SUPERVISED_YAML.read_text(encoding="utf-8"))
    dados = yaml.safe_load(texto) or {}

    if not isinstance(dados, dict):
        raise ValueError(
            f"{SUPERVISED_YAML} deve conter um mapeamento (dict) na raiz, "
            f"mas veio {type(dados).__name__}."
        )
    return dados


def supervised_yaml_sha256() -> str | None:
    """
    SHA-256 do YAML atual (ou None se não existir).
    Útil para gravar em `metadata.json` e garantir reprodutibilidade.
    """
    import hashlib
    if not SUPERVISED_YAML.exists():
        return None
    h = hashlib.sha256()
    with open(SUPERVISED_YAML, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
HTTP_TIMEOUT    = 180
HTTP_TENTATIVAS = 3
HTTP_BACKOFF    = 5


# ---------------------------------------------------------------------------
# Leitura de CSV
# ---------------------------------------------------------------------------
CSV_SEP      = ","
CSV_ENCODING = "utf-8-sig"
COLS         = None   # None = todas as colunas


# ---------------------------------------------------------------------------
# Conversão CSV → Parquet
# ---------------------------------------------------------------------------
PARQUET_COMPRESSION = "zstd"
CSV_CHUNKSIZE       = 500_000


# ---------------------------------------------------------------------------
# Compatibilidade retroativa
# ---------------------------------------------------------------------------
# O SRAG não possui API paginada — mantidos como None para deixar explícito.
API_URL   = None
PAGE_SIZE = None
N_PAGINAS = None

# ---------------------------------------------------------------------------
# Acesso tipado ao YAML supervisionado
# ---------------------------------------------------------------------------
class GatePendenteError(RuntimeError):
    """Levantado quando se tenta usar um valor que depende de gate não aprovado."""


def cfg(*chaves: str, default: Any = None) -> Any:
    """
    Acessa uma chave aninhada do supervised.yaml.

        cfg("target", "coluna")          -> "evolucao"
        cfg("models", "logistic", "C")   -> None (TBD)
    """
    atual: Any = carregar_supervised()
    for k in chaves:
        if not isinstance(atual, dict) or k not in atual:
            return default
        atual = atual[k]
    return atual


def exigir_valor(valor: Any, *, caminho: str, gate: str) -> Any:
    """
    Garante que `valor` não é None nem 'TBD'. Se for, levanta erro
    apontando o gate que precisa ser aprovado antes.
    """
    if valor is None or valor == "TBD":
        raise GatePendenteError(
            f"Valor não definido em '{caminho}'. "
            f"Aprove o gate '{gate}' em configs/supervised.yaml antes de usar."
        )
    return valor


def gate_aprovado(nome_gate: str) -> bool:
    """Retorna True se o gate existe e está com status 'aprovado'."""
    g = cfg("gates", nome_gate) or {}
    return g.get("status") == "aprovado"


def exigir_gate(nome_gate: str) -> None:
    """Levanta GatePendenteError se o gate ainda não foi aprovado."""
    if not gate_aprovado(nome_gate):
        raise GatePendenteError(
            f"Gate '{nome_gate}' está pendente. "
            f"Aprove-o em configs/supervised.yaml (status: aprovado) "
            f"antes de rodar esta etapa."
        )


def features_finais() -> list[str]:
    """
    Retorna a lista final de features.
    Se `features.final` for null, usa numericas + categoricas.
    """
    f = cfg("features") or {}
    final = f.get("final")
    if final:
        return list(final)
    return list(f.get("numericas", [])) + list(f.get("categoricas", []))


def limiar_ativo() -> float:
    """
    Retorna o limiar operacional.
    Só usa `otimo` se o gate G7 estiver aprovado; caso contrário, `default`.
    """
    lim = cfg("limiar") or {}
    if gate_aprovado("G7_limiar") and lim.get("otimo") is not None:
        return float(lim["otimo"])
    return float(lim.get("default", 0.5))


# ---------------------------------------------------------------------------
# Utilitário de diagnóstico
# ---------------------------------------------------------------------------
def _status(valor: object) -> str:
    return "definido" if valor else "vazio"


def resumo() -> str:
    """Retorna um resumo legível das configurações ativas."""
    yaml_ok = "ok" if SUPERVISED_YAML.exists() else "AUSENTE"
    return (
        f"ROOT_DIR          = {ROOT_DIR}\n"
        f"DATA_DIR          = {DATA_DIR}\n"
        f"RAW_DIR           = {RAW_DIR}\n"
        f"PROCESSED_DIR     = {PROCESSED_DIR}\n"
        f"TREINO_DIR        = {TREINO_DIR}\n"
        f"OUTPUTS_DIR       = {OUTPUTS_DIR}\n"
        f"RUNS_DIR          = {RUNS_DIR}\n"
        f"LOGS_DIR          = {LOGS_DIR}\n"
        f"CONFIGS_DIR       = {CONFIGS_DIR}\n"
        f"SUPERVISED_YAML   = {SUPERVISED_YAML} ({yaml_ok})\n"
        f"PARQUET_NAME      = {PARQUET_NAME}\n"
        f"DATA_VERSION      = {DATA_VERSION}\n"
        f"GITHUB_REPO       = {GITHUB_REPO}\n"
        f"HTTP_TIMEOUT      = {HTTP_TIMEOUT}\n"
        f"HTTP_TENTATIVAS   = {HTTP_TENTATIVAS}\n"
        f"SEED              = {SEED}\n"
        f"GITHUB_TOKEN?     = {bool(github_token())}\n"
        f"SRAG_PARQUET_URL  = {srag_parquet_url()}\n"
        f"SUPERVISED_SHA256 = {supervised_yaml_sha256()}\n"
    )


if __name__ == "__main__":
    print(resumo())