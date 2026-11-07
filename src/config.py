"""Configuração, caminhos, ambiente e hash de arquivos."""

from __future__ import annotations

import sys
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml
C = sys.modules[__name__]


ROOT_DIR: Path = Path(__file__).resolve().parents[1]

SEED         = 42

DATA_DIR       = ROOT_DIR / "data"
PROCESSED_DIR  = DATA_DIR / "processed"
ANALYTICAL_DIR = DATA_DIR / "analytical"

CONFIGS_DIR  = ROOT_DIR / "configs"
OUTPUTS_DIR  = ROOT_DIR / "outputs"
RUNS_DIR     = OUTPUTS_DIR / "runs"
REPORTS_DIR  = ROOT_DIR / "reports"
FIGURES_DIR  = REPORTS_DIR / "figures"

TABLES_DIR      = OUTPUTS_DIR / "tables"
PREDICTIONS_DIR = OUTPUTS_DIR / "predictions"

SUPERVISED_YAML = CONFIGS_DIR / "supervised.yaml"

GITHUB_REPO  = "Ivan-S-Oliveira/Projeto_Integrador"
DATA_VERSION = "dados-v2"
PARQUET_NAME = "srag.parquet"

HTTP_TIMEOUT    = 180
HTTP_TENTATIVAS = 3
HTTP_BACKOFF    = 5

class GatePendenteError(RuntimeError):
    """Levantado quando se tenta usar um valor que depende de gate não aprovado."""


def github_token() -> str | None:
    """Token do GitHub (opcional) para releases/downloads autenticados."""
    return os.getenv("GITHUB_TOKEN")


def srag_parquet_url() -> str:
    """URL do Parquet oficial processado."""
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


class _UniqueKeyLoader(yaml.SafeLoader):
    """Carregador YAML que rejeita chaves duplicadas."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    """Constrói um mapeamento YAML e falha em chave duplicada."""
    vistos: set[Any] = set()

    for key_node, _value_node in node.value:
        chave = loader.construct_object(key_node, deep=False)
        try:
            ja_existe = chave in vistos
        except TypeError:
            continue

        if ja_existe:
            linha = key_node.start_mark.line + 1
            raise ValueError(
                f"Chave duplicada em {SUPERVISED_YAML}: "
                f"{chave!r} (linha {linha})."
            )
        vistos.add(chave)

    return loader.construct_mapping(node, deep=deep)


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@dataclass
class _SupervisedCache:
    """Estado do cache do ``supervised.yaml``."""

    file_hash: str | None = None
    data: dict[str, Any] | None = None

    def invalidate(self) -> None:
        self.file_hash = None
        self.data = None

    def is_valid_for(self, file_hash: str) -> bool:
        return self.file_hash == file_hash and self.data is not None


_supervised_cache = _SupervisedCache()


def _ler_yaml_supervisionado(raw: bytes) -> dict[str, Any]:
    """Decodifica, interpola ``${VAR}`` e faz o parse do YAML."""
    try:
        texto = _interpolar_env(raw.decode("utf-8-sig"))
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"{SUPERVISED_YAML} não está em UTF-8 válido: {exc}"
        ) from exc

    try:
        dados = yaml.load(texto, Loader=_UniqueKeyLoader) or {}
    except yaml.YAMLError as exc:
        raise ValueError(
            f"{SUPERVISED_YAML} não pôde ser interpretado: {exc}"
        ) from exc

    if not isinstance(dados, dict):
        raise ValueError(
            f"{SUPERVISED_YAML} deve conter um mapeamento (dict) na raiz, "
            f"mas veio {type(dados).__name__}."
        )
    return dados


def carregar_supervised() -> dict[str, Any]:
    """Lê ``configs/supervised.yaml`` e devolve o dict parseado."""
    if not SUPERVISED_YAML.exists():
        raise FileNotFoundError(
            f"Configuração não encontrada: {SUPERVISED_YAML}\n"
            f"Crie o arquivo em {CONFIGS_DIR}/supervised.yaml "
            f"ou ajuste CONFIGS_DIR / SUPERVISED_YAML em config.py."
        )

    try:
        raw = SUPERVISED_YAML.read_bytes()
    except OSError as exc:
        raise OSError(
            f"Falha ao ler {SUPERVISED_YAML}: {exc}"
        ) from exc

    file_hash = hashlib.sha256(raw).hexdigest()

    if _supervised_cache.is_valid_for(file_hash):
        return _supervised_cache.data  # type: ignore[return-value]

    dados = _ler_yaml_supervisionado(raw)
    _supervised_cache.file_hash = file_hash
    _supervised_cache.data = dados
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
    """Acessa ``configs/supervised.yaml`` por caminho de chaves."""
    return _get_nested(carregar_supervised(), *chaves, default=default)


def gate_aprovado(nome_gate: str) -> bool:
    """True se ``gates.<nome_gate>.status == 'aprovado'``."""
    return _get_nested(carregar_supervised(), "gates", nome_gate, default={}).get("status") == "aprovado"


def exigir_gate(nome_gate: str) -> None:
    """Levanta ``GatePendenteError`` se o gate ainda não estiver aprovado."""
    if gate_aprovado(nome_gate):
        return
    status_atual = _get_nested(carregar_supervised(), "gates", nome_gate, default={}).get("status")
    if status_atual == "executado":
        raise GatePendenteError(
            f"Gate '{nome_gate}' já foi executado (não é mais 'aprovado'). "
            f"Reabrir exige uma decisão registrada em docs/decisoes.md."
        )
    raise GatePendenteError(
        f"Gate '{nome_gate}' está pendente. "
        f"Aprove-o em configs/supervised.yaml (status: aprovado) "
        f"antes de rodar esta etapa."
    )


def features_finais() -> list[str]:
    """Lista final de features."""
    f = cfg("features") or {}
    return list(f["final"]) if f.get("final") else (
        list(f.get("numericas", [])) + list(f.get("categoricas", []))
    )


def resumo() -> str:
    """Resumo legível das configurações ativas — usado em bootstrap de notebooks."""
    yaml_ok = "ok" if SUPERVISED_YAML.exists() else "AUSENTE"
    linhas = [
        ("ROOT_DIR",          ROOT_DIR),
        ("DATA_DIR",          DATA_DIR),
        ("PROCESSED_DIR",     PROCESSED_DIR),
        ("ANALYTICAL_DIR",    ANALYTICAL_DIR),
        ("OUTPUTS_DIR",       OUTPUTS_DIR),
        ("RUNS_DIR",          RUNS_DIR),
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


ROOT      = C.ROOT_DIR
DATA      = C.DATA_DIR
PROCESSED = C.PROCESSED_DIR
FIGURES   = C.FIGURES_DIR

_DIRS_PADRAO = (
    C.DATA_DIR, C.PROCESSED_DIR, C.ANALYTICAL_DIR,
    C.CONFIGS_DIR, C.OUTPUTS_DIR,
    C.RUNS_DIR, C.REPORTS_DIR, C.FIGURES_DIR,
    C.TABLES_DIR, C.PREDICTIONS_DIR,
)


def garantir_diretorios() -> None:
    """Cria todos os diretórios padrão do projeto, se ainda não existirem."""
    for p in _DIRS_PADRAO:
        p.mkdir(parents=True, exist_ok=True)


def carregar_dotenv(caminho: Path | None = None) -> bool:
    """Carrega ``.env`` da raiz do projeto (ou de ``caminho``)."""
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


def get_secret(nome: str, obrigatorio: bool = True) -> str | None:
    """Lê um segredo/variável sensível do ambiente."""
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


def resumo_ambiente() -> str:
    """Resumo legível do estado do ambiente."""
    linhas = [
        ("ROOT_DIR",         ROOT),
        ("ENV",              ENV),
        (".env encontrado?", (ROOT / ".env").exists()),
        ("GITHUB_TOKEN?",    bool(os.getenv("GITHUB_TOKEN"))),
    ]
    return "\n".join(f"{nome:18s}= {valor}" for nome, valor in linhas)


_DEFAULT_CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path, chunk_size: int = _DEFAULT_CHUNK_SIZE) -> str:
    """Calcula SHA-256 de um arquivo sem carregá-lo integralmente em memória."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
