"""
Configurações centralizadas do Projeto Integrador.

Fonte única da verdade para:

    - diretórios do projeto (data, outputs, logs, configs);
    - identificação da versão dos dados distribuídos (GITHUB_REPO, DATA_VERSION);
    - seed de reprodutibilidade;
    - leitura lazy e cacheada de `configs/supervised.yaml`;
    - acesso tipado a valores do YAML (`cfg`) com trava de gates
      (`gate_aprovado`, `exigir_gate`, `exigir_valor`).

Segredos e URLs sensíveis (`GITHUB_TOKEN`, `SRAG_PARQUET_URL`) são lidos em
tempo de execução via `os.getenv`, nunca no import. O YAML aceita
interpolação `${VAR}` — resolvida no momento da leitura.

Uso típico:
    from src.utils import config as C

    C.SEED
    C.OUTPUTS_DIR
    C.cfg("target", "coluna")
    C.exigir_gate("G7_limiar")
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
ANALYTICAL_DIR = DATA_DIR / "analytical"
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
DATA_VERSION = "dados-v2"
PARQUET_NAME = "srag.parquet"

GITHUB_RELEASE_URL = (
    f"https://github.com/{GITHUB_REPO}/releases/download/{DATA_VERSION}/"
)


# ---------------------------------------------------------------------------
# Segredos e URLs sensíveis — LEITURA LAZY
# ---------------------------------------------------------------------------
def github_token() -> str | None:
    """Token do GitHub (opcional) para releases/downloads autenticados."""
    return os.getenv("GITHUB_TOKEN")


def srag_parquet_url() -> str:
    """
    URL do Parquet de SRAG usado como fonte bruta.

    O default aponta para o arquivo mais recente publicado no OpenDataSUS
    (``INFLUD24``). Como esse arquivo é atualizado periodicamente pelo
    Ministério da Saúde, o valor pode ser sobrescrito pela variável de
    ambiente ``SRAG_PARQUET_URL``.
    """
    return os.getenv(
        "SRAG_PARQUET_URL",
        "https://s3.sa-east-1.amazonaws.com/"
        "ckan.saude.gov.br/SRAG/2024/INFLUD24-16-12-2024.parquet",
    )


# ---------------------------------------------------------------------------
# Configuração supervisionada — LEITURA LAZY + CACHEADA
# ---------------------------------------------------------------------------
_ENV_PATTERN = re.compile(r"\$\{(\w+)\}")


def _interpolar_env(texto: str) -> str:
    return _ENV_PATTERN.sub(lambda m: os.getenv(m.group(1), ""), texto)


@lru_cache(maxsize=1)
def carregar_supervised() -> dict[str, Any]:
    """
    Lê `configs/supervised.yaml` e devolve o dict parseado.

    - Resolve `${VAR}` a partir do ambiente antes de fazer o parse.
    - Resultado é cacheado (`lru_cache(maxsize=1)`) — o arquivo é lido
      uma única vez por processo.
    - Levanta `FileNotFoundError` se o YAML não existir e
      `ImportError` se `PyYAML` não estiver instalado.
    """
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
    """SHA-256 do `supervised.yaml`, ou `None` se o arquivo não existir."""
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
# Acesso tipado ao YAML supervisionado
# ---------------------------------------------------------------------------
class GatePendenteError(RuntimeError):
    """Levantado quando se tenta usar um valor que depende de gate não aprovado."""


def cfg(*chaves: str, default: Any = None) -> Any:
    """
    Acessa `configs/supervised.yaml` por caminho de chaves.

    Exemplo
    -------
        cfg("target", "coluna")        # → "evolucao"
        cfg("temporal", "fracao")      # → {"treino": 0.7, "validacao": 0.15}

    Retorna `default` se qualquer chave do caminho não existir.
    """
    atual: Any = carregar_supervised()
    for k in chaves:
        if not isinstance(atual, dict) or k not in atual:
            return default
        atual = atual[k]
    return atual


def exigir_valor(valor: Any, *, caminho: str, gate: str) -> Any:
    """
    Devolve `valor` se preenchido; levanta `GatePendenteError` caso
    contrário (`None` ou `"TBD"`).

    Usado para valores do YAML que só podem ser preenchidos após um gate
    ser aprovado (p.ex. `models.logistic.C`).
    """
    if valor is None or valor == "TBD":
        raise GatePendenteError(
            f"Valor não definido em '{caminho}'. "
            f"Aprove o gate '{gate}' em configs/supervised.yaml antes de usar."
        )
    return valor


def gate_aprovado(nome_gate: str) -> bool:
    """True se `gates.<nome_gate>.status == 'aprovado'`."""
    g = cfg("gates", nome_gate) or {}
    return g.get("status") == "aprovado"


def exigir_gate(nome_gate: str) -> None:
    """
    Levanta `GatePendenteError` se o gate ainda não estiver aprovado.

    Use no início de qualquer etapa que dependa de decisão metodológica
    congelada (p.ex. split temporal antes de G2, holdout antes de G7).
    """
    if not gate_aprovado(nome_gate):
        raise GatePendenteError(
            f"Gate '{nome_gate}' está pendente. "
            f"Aprove-o em configs/supervised.yaml (status: aprovado) "
            f"antes de rodar esta etapa."
        )


def features_finais() -> list[str]:
    """
    Lista final de features.

    Se `features.final` estiver preenchida no YAML, usa-a. Caso contrário,
    concatena `features.numericas` + `features.categoricas`.
    """
    f = cfg("features") or {}
    final = f.get("final")
    if final:
        return list(final)
    return list(f.get("numericas", [])) + list(f.get("categoricas", []))


def limiar_ativo() -> float:
    """
    Limiar de decisão vigente.

    Usa `limiar.otimo` se o gate `G7_limiar` estiver aprovado e o valor
    estiver preenchido; caso contrário, cai em `limiar.default` (0.5).
    """
    lim = cfg("limiar") or {}
    if gate_aprovado("G7_limiar") and lim.get("otimo") is not None:
        return float(lim["otimo"])
    return float(lim.get("default", 0.5))


# ---------------------------------------------------------------------------
# Utilitário de diagnóstico
# ---------------------------------------------------------------------------
def resumo() -> str:
    """Resumo legível das configurações ativas — usado em bootstrap de notebooks."""
    yaml_ok = "ok" if SUPERVISED_YAML.exists() else "AUSENTE"
    return (
        f"ROOT_DIR          = {ROOT_DIR}\n"
        f"DATA_DIR          = {DATA_DIR}\n"
        f"RAW_DIR           = {RAW_DIR}\n"
        f"PROCESSED_DIR     = {PROCESSED_DIR}\n"
        f"ANALYTICAL_DIR    = {ANALYTICAL_DIR}\n"
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