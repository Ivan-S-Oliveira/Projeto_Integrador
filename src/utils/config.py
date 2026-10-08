"""
Configurações centralizadas do Projeto Integrador.
... (docstring igual) ...
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
ROOT_DIR: Path = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Reprodutibilidade
# ---------------------------------------------------------------------------
SEED = 42
RANDOM_STATE = SEED


# ---------------------------------------------------------------------------
# Diretórios do projeto (fonte única da verdade)
# ---------------------------------------------------------------------------
DATA_DIR       = ROOT_DIR / "data"
RAW_DIR        = DATA_DIR / "raw"
PROCESSED_DIR  = DATA_DIR / "processed"
ANALYTICAL_DIR = DATA_DIR / "analytical"        # ← NOVO
TREINO_DIR     = DATA_DIR / "treino"

CONFIGS_DIR   = ROOT_DIR / "configs"
MODELS_DIR    = ROOT_DIR / "models"
OUTPUTS_DIR   = ROOT_DIR / "outputs"
RUNS_DIR      = OUTPUTS_DIR / "runs"
LOGS_DIR      = ROOT_DIR / "logs"
REPORTS_DIR   = ROOT_DIR / "reports"
FIGURES_DIR   = REPORTS_DIR / "figures"

TABLES_DIR      = OUTPUTS_DIR / "tables"
PREDICTIONS_DIR = OUTPUTS_DIR / "predictions"


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
def github_token() -> str | None:
    return os.getenv("GITHUB_TOKEN")


def srag_parquet_url() -> str:
    return os.getenv(
        "SRAG_PARQUET_URL",
        "https://s3.sa-east-1.amazonaws.com/"
        "ckan.saude.gov.br/SRAG/2023/INFLUD23-16-10-2023.parquet",
    )


# ---------------------------------------------------------------------------
# Configuração supervisionada — LEITURA LAZY + CACHEADA
# ---------------------------------------------------------------------------
_ENV_PATTERN = re.compile(r"\$\{(\w+)\}")


def _interpolar_env(texto: str) -> str:
    return _ENV_PATTERN.sub(lambda m: os.getenv(m.group(1), ""), texto)


@lru_cache(maxsize=1)
def carregar_supervised() -> dict[str, Any]:
    if not SUPERVISED_YAML.exists():
        raise FileNotFoundError(
            f"Configuração não encontrada: {SUPERVISED_YAML}\n"
            f"Crie o arquivo em {CONFIGS_DIR}/supervised.yaml "
            f"ou ajuste CONFIGS_DIR / SUPERVISED_YAML em config.py."
        )

    try:
        import yaml
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
COLS         = None


# ---------------------------------------------------------------------------
# Conversão CSV → Parquet
# ---------------------------------------------------------------------------
PARQUET_COMPRESSION = "zstd"
CSV_CHUNKSIZE       = 500_000


# ---------------------------------------------------------------------------
# Compatibilidade retroativa
# ---------------------------------------------------------------------------
API_URL   = None
PAGE_SIZE = None
N_PAGINAS = None


# ---------------------------------------------------------------------------
# Acesso tipado ao YAML supervisionado
# ---------------------------------------------------------------------------
class GatePendenteError(RuntimeError):
    """Levantado quando se tenta usar um valor que depende de gate não aprovado."""


def cfg(*chaves: str, default: Any = None) -> Any:
    atual: Any = carregar_supervised()
    for k in chaves:
        if not isinstance(atual, dict) or k not in atual:
            return default
        atual = atual[k]
    return atual


def exigir_valor(valor: Any, *, caminho: str, gate: str) -> Any:
    if valor is None or valor == "TBD":
        raise GatePendenteError(
            f"Valor não definido em '{caminho}'. "
            f"Aprove o gate '{gate}' em configs/supervised.yaml antes de usar."
        )
    return valor


def gate_aprovado(nome_gate: str) -> bool:
    g = cfg("gates", nome_gate) or {}
    return g.get("status") == "aprovado"


def exigir_gate(nome_gate: str) -> None:
    if not gate_aprovado(nome_gate):
        raise GatePendenteError(
            f"Gate '{nome_gate}' está pendente. "
            f"Aprove-o em configs/supervised.yaml (status: aprovado) "
            f"antes de rodar esta etapa."
        )


def features_finais() -> list[str]:
    f = cfg("features") or {}
    final = f.get("final")
    if final:
        return list(final)
    return list(f.get("numericas", [])) + list(f.get("categoricas", []))


def limiar_ativo() -> float:
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
    yaml_ok = "ok" if SUPERVISED_YAML.exists() else "AUSENTE"
    return (
        f"ROOT_DIR          = {ROOT_DIR}\n"
        f"DATA_DIR          = {DATA_DIR}\n"
        f"RAW_DIR           = {RAW_DIR}\n"
        f"PROCESSED_DIR     = {PROCESSED_DIR}\n"
        f"ANALYTICAL_DIR    = {ANALYTICAL_DIR}\n"      # ← NOVO
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