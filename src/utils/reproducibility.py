"""
Registro de execuções para reprodutibilidade (critério C1).

Cada execução grava em ``outputs/runs/<RUN_ID>/``:

- ``metadata.json`` — tudo estruturado
- ``summary.txt``   — versão legível

Uso::

    from src.utils.reproducibility import Run

    with Run(modelo="logistic", parametros={"C": 1.0}) as r:
        ... treino ...
        r.metrica(auc=0.82, accuracy=0.78)
        r.anotar("split aleatorio estratificado")
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any, Literal

from src.utils import config as C
from src.utils.storage import read_sha256

RUNS_DIR: Path = C.RUNS_DIR

Status = Literal["success", "error"]
_VERSOES_PACOTES = ("numpy", "pandas", "pyarrow", "scikit-learn", "scipy", "matplotlib", "seaborn")
_DATASET_TAMANHOS = ("n_rows", "train_rows", "valid_rows", "test_rows")


# ---------------------------------------------------------------------------
# Helpers de metadados
# ---------------------------------------------------------------------------

def _agora() -> dict[str, str]:
    utc = datetime.now(timezone.utc)
    return {
        "utc":   utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "local": utc.astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def _coletar_gates() -> dict[str, str]:
    """Estado atual de cada gate em ``supervised.yaml`` como ``{nome: status}``."""
    gates = C.cfg("gates") or {}
    return {nome: (info or {}).get("status", "desconhecido") for nome, info in gates.items()}


def _versoes() -> dict[str, str | None]:
    """Versões das bibliotecas fundamentais e do Python."""
    resultado: dict[str, str | None] = {"python": platform.python_version()}
    for pacote in _VERSOES_PACOTES:
        try:
            resultado[pacote] = metadata.version(pacote)
        except metadata.PackageNotFoundError:
            resultado[pacote] = None
    return resultado


def _run_git(args: list[str]) -> str | None:
    """Corre ``git args`` em ``C.ROOT_DIR``; devolve stdout ou ``None``."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=C.ROOT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def _git_info() -> dict[str, str | bool | None]:
    """Commit, branch e estado da árvore de trabalho."""
    status = _run_git(["status", "--porcelain"])
    return {
        "commit": _run_git(["rev-parse", "HEAD"]),
        "branch": _run_git(["branch", "--show-current"]),
        "dirty":  bool(status) if status is not None else None,
    }


def _env_info() -> dict[str, str | bool]:
    """Informações não sensíveis do ambiente."""
    return {
        "python_executable": sys.executable,
        "python_version":    platform.python_version(),
        "platform":          platform.platform(),
        "cwd":               str(Path.cwd()),
        "ci":                bool(os.getenv("CI") or os.getenv("GITHUB_ACTIONS")),
    }


def _resolver_dataset_sha256(
    dataset_sha256: str | None,
    dataset_path: Path | None,
) -> str | None:
    """SHA-256 do dataset por prioridade: explícito > sidecar > ``None``.

    O sidecar é ``<dataset_path>.sha256`` (ver ``src.utils.storage``).
    """
    if dataset_sha256:
        return dataset_sha256
    if dataset_path is None:
        return None
    try:
        return read_sha256(Path(dataset_path))
    except OSError:
        return None


# ---------------------------------------------------------------------------
# summary.txt
# ---------------------------------------------------------------------------

def _bloco(titulo: str, itens: dict[str, Any], largura: int = 20) -> list[str]:
    """``titulo`` seguido de ``k: v`` alinhados — devolve linhas já vazias acima."""
    linhas = ["", f"{titulo}:"]
    for k, v in itens.items():
        if isinstance(v, float):
            linhas.append(f"  {k:{largura}s} {v:.4f}")
        else:
            linhas.append(f"  {k:{largura}s} {v}")
    return linhas


def _resumo(meta: dict[str, Any]) -> str:
    """``summary.txt`` curto e legível a partir do metadata."""
    linhas = [
        f"RUN_ID:   {meta['run_id']}",
        f"MODELO:   {meta['modelo']}",
        f"SEED:     {meta['seed']}",
        f"STATUS:   {meta.get('status', 'desconhecido')}",
    ]

    if meta.get("data_version"):
        linhas.append(f"DADOS:    {meta['data_version']}")
    if meta.get("dataset_sha256"):
        linhas.append(f"SHA-256:  {meta['dataset_sha256']}")

    ds = meta.get("dataset") or {}
    for k in _DATASET_TAMANHOS:
        if k in ds:
            linhas.append(f"{k.upper():10s} {ds[k]:,}")

    if meta.get("duracao_s") is not None:
        linhas.append(f"DURACAO:  {meta['duracao_s']:.1f}s")

    if meta.get("erro"):
        err = meta["erro"]
        linhas += ["", "ERRO:",
                   f"  tipo:     {err.get('tipo')}",
                   f"  mensagem: {err.get('mensagem')}"]

    if meta.get("metricas"):
        linhas += _bloco("MÉTRICAS", meta["metricas"])

    if meta.get("parametros"):
        linhas += _bloco("PARÂMETROS", meta["parametros"])

    if meta.get("gates"):
        linhas += _bloco("GATES", meta["gates"], largura=34)

    if meta.get("notas"):
        linhas += ["", f"NOTAS: {meta['notas']}"]

    linhas += ["", f"TIMESTAMP_UTC: {meta['timestamp']['utc']}"]
    return "\n".join(linhas) + "\n"


# ---------------------------------------------------------------------------
# API pública: gerar, registar, listar, carregar
# ---------------------------------------------------------------------------

def gerar_run_id(
    modelo: str | None = None,
    base_dir: Path | None = None,
) -> str:
    """Identificador único ``YYYY-MM-DD_HHMMSS_micros[_modelo]``.

    Com ``base_dir``, acrescenta sufixo ``_NN`` em caso de colisão no
    sistema de arquivos.
    """
    candidato = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")
    if modelo:
        candidato = f"{candidato}_{modelo}"
    if base_dir is None:
        return candidato

    base = Path(base_dir)
    run_id, contador = candidato, 1
    while (base / run_id).exists():
        run_id = f"{candidato}_{contador:02d}"
        contador += 1
    return run_id


def registrar_execucao(
    modelo: str,
    *,
    seed: int | None = None,
    parametros: dict[str, Any] | None = None,
    dataset: dict[str, Any] | None = None,
    features: dict[str, Any] | None = None,
    metricas: dict[str, Any] | None = None,
    duracao_s: float | None = None,
    notas: str | None = None,
    run_id: str | None = None,
    output_dir: Path | None = None,
    status: Status = "success",
    erro: dict[str, Any] | None = None,
    dataset_sha256: str | None = None,
) -> Path:
    """Grava ``metadata.json`` + ``summary.txt`` em ``outputs/runs/<RUN_ID>/``.

    ``status='error'`` deve vir acompanhado de ``erro`` (dict com ``tipo``,
    ``mensagem`` e opcionalmente ``traceback``). ``dataset_sha256=None``
    deixa a chave ausente do metadata.
    """
    base = Path(output_dir) if output_dir is not None else RUNS_DIR
    if run_id is None:
        run_id = gerar_run_id(modelo=modelo, base_dir=base)

    pasta = base / run_id
    pasta.mkdir(parents=True, exist_ok=False)

    meta: dict[str, Any] = {
        "run_id":         pasta.name,
        "timestamp":      _agora(),
        "modelo":         modelo,
        "seed":           seed if seed is not None else C.SEED,
        "status":         status,
        "erro":           erro,
        "duracao_s":      duracao_s,
        "parametros":     parametros or {},
        "dataset":        dataset or {},
        "dataset_sha256": dataset_sha256,
        "data_version":   C.DATA_VERSION,
        "features":       features or {},
        "metricas":       metricas or {},
        "gates":          _coletar_gates(),
        "notas":          notas,
        "versoes":        _versoes(),
        "git":            _git_info(),
        "env":            _env_info(),
        "supervised_yaml_sha256": C.supervised_yaml_sha256(),
    }

    (pasta / "metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    (pasta / "summary.txt").write_text(_resumo(meta), encoding="utf-8")

    print(f"[reproducibility] run registrado em: {pasta}")
    return pasta


def listar_runs(output_dir: Path | None = None) -> list[dict[str, Any]]:
    """Metadados das execuções registadas, ordenados por ``run_id`` decrescente.

    Cada item inclui ``"pasta"`` com o caminho absoluto.
    """
    raiz = Path(output_dir) if output_dir is not None else RUNS_DIR
    if not raiz.exists():
        return []

    runs: list[dict[str, Any]] = []
    for pasta in raiz.iterdir():
        if not pasta.is_dir():
            continue
        meta_path = pasta / "metadata.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        meta["pasta"] = str(pasta)
        runs.append(meta)

    return sorted(runs, key=lambda m: str(m.get("run_id", "")), reverse=True)


def carregar_run(
    run: str | Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Carrega o ``metadata.json`` de uma execução."""
    caminho = Path(run)
    if not caminho.is_absolute():
        caminho = (Path(output_dir) if output_dir else RUNS_DIR) / caminho

    meta_path = caminho / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"metadata.json não encontrado em {caminho}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

class Run:
    """Context manager de registo de execução.

    O metadata é gravado sempre ao sair do bloco, inclusive em caso de
    excepção (com ``status="error"`` e ``erro`` estruturado). A excepção
    não é suprimida — ``__exit__`` devolve ``False``.
    """

    def __init__(
        self,
        modelo: str,
        *,
        seed: int | None = None,
        parametros: dict[str, Any] | None = None,
        dataset: dict[str, Any] | None = None,
        features: dict[str, Any] | None = None,
        notas: str | None = None,
        output_dir: Path | None = None,
        dataset_path: Path | None = None,
        dataset_sha256: str | None = None,
    ) -> None:
        self.modelo         = modelo
        self.seed           = seed
        self.parametros     = dict(parametros or {})
        self.dataset        = dict(dataset or {})
        self.features       = dict(features or {})
        self.notas          = notas
        self.output_dir     = output_dir
        self.dataset_path   = dataset_path
        self.dataset_sha256 = dataset_sha256
        self._metricas: dict[str, Any] = {}
        self._inicio: float | None = None
        self.pasta: Path | None = None

    def metrica(self, **kwargs: Any) -> "Run":
        self._metricas.update(kwargs)
        return self

    def anotar(self, texto: str) -> "Run":
        self.notas = f"{self.notas}\n{texto}" if self.notas else texto
        return self

    def add_dataset(self, **kwargs: Any) -> "Run":
        self.dataset.update(kwargs)
        return self

    def __enter__(self) -> "Run":
        self._inicio = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        duracao = time.perf_counter() - self._inicio if self._inicio else None

        if exc_type is None:
            status: Status = "success"
            erro: dict[str, Any] | None = None
        else:
            status = "error"
            erro = {
                "tipo":      exc_type.__name__,
                "modulo":    getattr(exc_type, "__module__", None),
                "mensagem":  str(exc) if exc is not None else None,
                "traceback": (
                    "".join(traceback.format_exception(exc_type, exc, tb))
                    if tb is not None else None
                ),
            }

        self.pasta = registrar_execucao(
            modelo=self.modelo,
            seed=self.seed,
            parametros=self.parametros,
            dataset=self.dataset,
            features=self.features,
            metricas=self._metricas,
            duracao_s=duracao,
            notas=self.notas,
            output_dir=self.output_dir,
            status=status,
            erro=erro,
            dataset_sha256=_resolver_dataset_sha256(self.dataset_sha256, self.dataset_path),
        )
        return False
    
    def buscar_runs(
    *,
    modelo: str | None = None,
    dataset_sha256: str | None = None,
    status: Status | None = None,
    output_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Filtra execuções por critérios, ordenadas por run_id decrescente.

    Parâmetros
    ----------
    modelo:
        Nome do modelo (match exato, case-insensitive).
    dataset_sha256:
        SHA-256 do dataset de entrada.
    status:
        ``"success"`` ou ``"error"``.
    output_dir:
        Diretório raiz das execuções (default: ``RUNS_DIR``).

    Retorna
    -------
    Lista de metadados (dicts) das execuções que casam com os filtros.
    """
    runs = listar_runs(output_dir=output_dir)

    if modelo is not None:
        modelo_lower = modelo.lower()
        runs = [r for r in runs if str(r.get("modelo", "")).lower() == modelo_lower]

    if dataset_sha256 is not None:
        runs = [r for r in runs if r.get("dataset_sha256") == dataset_sha256]

    if status is not None:
        runs = [r for r in runs if r.get("status") == status]

    return runs


def localizar_artefato(
    run_id: str,
    nome_artefato: str,
    *,
    output_dir: Path | None = None,
) -> Path | None:
    """Busca um arquivo pelo nome em uma execução específica.

    Varre o diretório da execução e subdiretórios, procurando o arquivo
    pelo sufixo. Retorna ``None`` se não encontrar.
    """
    base = Path(output_dir) if output_dir else RUNS_DIR
    pasta_run = base / run_id

    if not pasta_run.is_dir():
        return None

    alvo = Path(nome_artefato).name
    for caminho in pasta_run.rglob(alvo):
        if caminho.is_file():
            return caminho
    return None


def ultimo_run_com_artefato(
    nome_artefato: str,
    *,
    modelo: str | None = None,
    dataset_sha256: str | None = None,
    output_dir: Path | None = None,
) -> tuple[dict[str, Any], Path] | None:
    """Localiza a execução mais recente que possui o artefato e o caminho dele.

    Retorna ``(metadata, caminho_artefato)`` ou ``None``.
    """
    runs = buscar_runs(
        modelo=modelo,
        dataset_sha256=dataset_sha256,
        status="success",
        output_dir=output_dir,
    )

    for meta in runs:
        run_id = str(meta.get("run_id"))
        caminho = localizar_artefato(run_id, nome_artefato, output_dir=output_dir)
        if caminho is not None:
            return meta, caminho
    return None