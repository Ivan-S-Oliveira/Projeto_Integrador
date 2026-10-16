"""
Configurações centralizadas do Projeto Integrador.

Fonte única da verdade para diretórios, identificação da versão dos dados,
seed de reprodutibilidade e acesso tipado ao ``configs/supervised.yaml``.

Segredos e URLs sensíveis (``GITHUB_TOKEN``, ``SRAG_PARQUET_URL``) são lidos
em tempo de execução via ``os.getenv``, nunca no import. O YAML aceita
interpolação ``${VAR}``, resolvida no momento da leitura.

Uso típico::

    from src.utils import config as C

    C.SEED
    C.OUTPUTS_DIR
    C.cfg("target", "coluna")
    C.exigir_gate("G7_calibracao")
"""

from __future__ import annotations

import hashlib
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


ROOT_DIR: Path = Path(__file__).resolve().parents[2]

SEED         = 42
RANDOM_STATE = SEED

DATA_DIR       = ROOT_DIR / "data"
RAW_DIR        = DATA_DIR / "raw"
PROCESSED_DIR  = DATA_DIR / "processed"
ANALYTICAL_DIR = DATA_DIR / "analytical"
TREINO_DIR     = DATA_DIR / "treino"

CONFIGS_DIR  = ROOT_DIR / "configs"
MODELS_DIR   = ROOT_DIR / "models"
OUTPUTS_DIR  = ROOT_DIR / "outputs"
RUNS_DIR     = OUTPUTS_DIR / "runs"
LOGS_DIR     = ROOT_DIR / "logs"
REPORTS_DIR  = ROOT_DIR / "reports"
FIGURES_DIR  = REPORTS_DIR / "figures"

TABLES_DIR      = OUTPUTS_DIR / "tables"
PREDICTIONS_DIR = OUTPUTS_DIR / "predictions"

SUPERVISED_YAML = CONFIGS_DIR / "supervised.yaml"

GITHUB_REPO  = "Ivan-S-Oliveira/Projeto_Integrador"
DATA_VERSION = "dados-v2"
PARQUET_NAME = "srag.parquet"

GITHUB_RELEASE_URL = (
    f"https://github.com/{GITHUB_REPO}/releases/download/{DATA_VERSION}/"
)

HTTP_TIMEOUT    = 180
HTTP_TENTATIVAS = 3
HTTP_BACKOFF    = 5

CSV_SEP      = ","
CSV_ENCODING = "utf-8-sig"
COLS         = None

PARQUET_COMPRESSION = "zstd"
CSV_CHUNKSIZE       = 500_000


class GatePendenteError(RuntimeError):
    """Levantado quando se tenta usar um valor que depende de gate não aprovado."""


def github_token() -> str | None:
    """Token do GitHub (opcional) para releases/downloads autenticados."""
    return os.getenv("GITHUB_TOKEN")


def srag_parquet_url() -> str:
    """URL do Parquet oficial processado.

    Construída a partir de ``GITHUB_REPO`` / ``DATA_VERSION`` /
    ``PARQUET_NAME``. Pode ser sobrescrita via ``SRAG_PARQUET_URL``.
    """
    url_padrao = (
        f"https://github.com/{GITHUB_REPO}/releases/download/"
        f"{DATA_VERSION}/{PARQUET_NAME}"
    )
    return os.getenv("SRAG_PARQUET_URL", url_padrao).strip() or url_padrao


_ENV_PATTERN = re.compile(r"\$\{(\w+)\}")


def _interpolar_env(texto: str) -> str:
    """Substitui ``${VAR}`` pelo valor de ``os.getenv``; ausente vira ``""``."""
    return _ENV_PATTERN.sub(lambda m: os.getenv(m.group(1), ""), texto)


def _get_nested(mapping: Any, *chaves: str, default: Any = None) -> Any:
    """Acesso a caminho de chaves num dict; devolve ``default`` se faltar."""
    atual = mapping
    for k in chaves:
        if not isinstance(atual, dict) or k not in atual:
            return default
        atual = atual[k]
    return atual


@lru_cache(maxsize=1)
def carregar_supervised() -> dict[str, Any]:
    """Lê ``configs/supervised.yaml`` e devolve o dict parseado (cacheado).

    Resolve ``${VAR}`` antes do parse. Levanta ``FileNotFoundError`` se o
    YAML não existir e ``ValueError`` se a raiz não for mapping.
    """
    if not SUPERVISED_YAML.exists():
        raise FileNotFoundError(
            f"Configuração não encontrada: {SUPERVISED_YAML}\n"
            f"Crie o arquivo em {CONFIGS_DIR}/supervised.yaml "
            f"ou ajuste CONFIGS_DIR / SUPERVISED_YAML em config.py."
        )

    texto = _interpolar_env(SUPERVISED_YAML.read_text(encoding="utf-8"))
    dados = yaml.safe_load(texto) or {}

    if not isinstance(dados, dict):
        raise ValueError(
            f"{SUPERVISED_YAML} deve conter um mapeamento (dict) na raiz, "
            f"mas veio {type(dados).__name__}."
        )
    return dados


def supervised_yaml_sha256() -> str | None:
    """SHA-256 do ``supervised.yaml``, ou ``None`` se o arquivo não existir."""
    if not SUPERVISED_YAML.exists():
        return None
    h = hashlib.sha256()
    with open(SUPERVISED_YAML, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def cfg(*chaves: str, default: Any = None) -> Any:
    """Acessa ``configs/supervised.yaml`` por caminho de chaves.

    Exemplo::

        cfg("target", "coluna")       # → "evolucao"
        cfg("temporal", "fracao")     # → {"treino": 0.7, "validacao": 0.15}

    Devolve ``default`` se qualquer chave do caminho não existir.
    """
    return _get_nested(carregar_supervised(), *chaves, default=default)


def exigir_valor(valor: Any, *, caminho: str, gate: str) -> Any:
    """Devolve ``valor`` se preenchido; levanta ``GatePendenteError`` se ``None`` ou ``"TBD"``.

    Usado para valores do YAML que só podem ser preenchidos após gate aprovado.
    """
    if valor is None or valor == "TBD":
        raise GatePendenteError(
            f"Valor não definido em '{caminho}'. "
            f"Aprove o gate '{gate}' em configs/supervised.yaml antes de usar."
        )
    return valor


def gate_aprovado(nome_gate: str) -> bool:
    """True se ``gates.<nome_gate>.status == 'aprovado'``."""
    return _get_nested(carregar_supervised(), "gates", nome_gate, default={}).get("status") == "aprovado"


def exigir_gate(nome_gate: str) -> None:
    """Levanta ``GatePendenteError`` se o gate ainda não estiver aprovado.

    Use no início de etapas que dependem de decisão metodológica congelada
    (ex.: holdout antes de G9).
    """
    if not gate_aprovado(nome_gate):
        raise GatePendenteError(
            f"Gate '{nome_gate}' está pendente. "
            f"Aprove-o em configs/supervised.yaml (status: aprovado) "
            f"antes de rodar esta etapa."
        )


def features_finais() -> list[str]:
    """Lista final de features.

    Usa ``features.final`` se preenchida; caso contrário, concatena
    ``features.numericas`` + ``features.categoricas``.
    """
    f = cfg("features") or {}
    return list(f["final"]) if f.get("final") else (
        list(f.get("numericas", [])) + list(f.get("categoricas", []))
    )


def limiar_ativo() -> float:
    """Limiar de decisão vigente.

    Usa ``limiar.otimo`` se o gate ``G8_limiar`` estiver aprovado e o valor
    preenchido; caso contrário, cai em ``limiar.default`` (0.5).
    """
    lim = cfg("limiar") or {}
    if gate_aprovado("G8_limiar") and lim.get("otimo") is not None:
        return float(lim["otimo"])
    return float(lim.get("default", 0.5))


def resumo() -> str:
    """Resumo legível das configurações ativas — usado em bootstrap de notebooks."""
    yaml_ok = "ok" if SUPERVISED_YAML.exists() else "AUSENTE"
    linhas = [
        ("ROOT_DIR",          ROOT_DIR),
        ("DATA_DIR",          DATA_DIR),
        ("RAW_DIR",           RAW_DIR),
        ("PROCESSED_DIR",     PROCESSED_DIR),
        ("ANALYTICAL_DIR",    ANALYTICAL_DIR),
        ("TREINO_DIR",        TREINO_DIR),
        ("OUTPUTS_DIR",       OUTPUTS_DIR),
        ("RUNS_DIR",          RUNS_DIR),
        ("LOGS_DIR",          LOGS_DIR),
        ("CONFIGS_DIR",       CONFIGS_DIR),
        ("SUPERVISED_YAML",   f"{SUPERVISED_YAML} ({yaml_ok})"),
        ("PARQUET_NAME",      PARQUET_NAME),
        ("DATA_VERSION",      DATA_VERSION),
        ("GITHUB_REPO",       GITHUB_REPO),
        ("HTTP_TIMEOUT",      HTTP_TIMEOUT),
        ("HTTP_TENTATIVAS",   HTTP_TENTATIVAS),
        ("SEED",              SEED),
        ("GITHUB_TOKEN?",     bool(github_token())),
        ("SRAG_PARQUET_URL",  srag_parquet_url()),
        ("SUPERVISED_SHA256", supervised_yaml_sha256()),
    ]
    return "\n".join(f"{nome:18s}= {valor}" for nome, valor in linhas)


if __name__ == "__main__":
    print(resumo())