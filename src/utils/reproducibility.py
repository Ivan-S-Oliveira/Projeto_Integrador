"""
Registro de execuções para reprodutibilidade (critério C1).

Cada execução gera `outputs/runs/<RUN_ID>/` com:
    metadata.json   ← tudo estruturado
    summary.txt     ← versão legível

O metadata captura identificação (run_id, modelo, seed, timestamps),
status (`success` | `error`), erro estruturado quando houver exceção,
versão e SHA-256 do Parquet, estado dos gates, versões de bibliotecas,
commit/branch e ambiente.

Uso:
    from src.utils.reproducibility import Run

    with Run(
        modelo="logistic",
        parametros={"C": 1.0},
        dataset_path=C.ANALYTICAL_DIR / "dataset_supervisionado.parquet",
    ) as r:
        ... treino ...
        r.metrica(auc=0.82, accuracy=0.78)
        r.anotar("split temporal por dt_notific")
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
from typing import Any

from src.utils import config as C


RUNS_DIR: Path = C.RUNS_DIR


def gerar_run_id(
    modelo: str | None = None,
    base_dir: Path | None = None,
) -> str:
    """
    Gera um identificador único no formato
    `YYYY-MM-DD_HHMMSS_micros[_modelo]`.

    Se `base_dir` for informado, garante unicidade contra o sistema de
    arquivos adicionando sufixo `_NN` em caso de colisão.
    """
    agora = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")
    candidato = f"{agora}_{modelo}" if modelo else agora

    if base_dir is None:
        return candidato

    base = Path(base_dir)
    run_id = candidato
    contador = 1
    while (base / run_id).exists():
        run_id = f"{candidato}_{contador:02d}"
        contador += 1

    return run_id


def _agora() -> dict[str, str]:
    utc = datetime.now(timezone.utc)
    return {
        "utc":   utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "local": utc.astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def _coletar_gates() -> dict[str, str]:
    """Estado atual de cada gate em `supervised.yaml` como `{nome: status}`."""
    gates = C.cfg("gates") or {}
    return {
        nome: (info or {}).get("status", "desconhecido")
        for nome, info in gates.items()
    }


def _resolver_dataset_sha256(
    dataset_sha256: str | None,
    dataset_path: Path | None,
) -> str | None:
    """
    Resolve o SHA-256 do dataset por prioridade: valor explícito, sidecar
    `<dataset_path>.sha256`, ou `None`.
    """
    if dataset_sha256:
        return dataset_sha256
    if dataset_path is None:
        return None
    try:
        from src.utils.storage import read_sha256
        return read_sha256(Path(dataset_path))
    except Exception:
        return None


def _resumo(meta: dict[str, Any]) -> str:
    """`summary.txt` curto e legível a partir do metadata."""
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
    for k in ("n_rows", "train_rows", "valid_rows", "test_rows"):
        if k in ds:
            linhas.append(f"{k.upper():9s} {ds[k]:,}")

    if meta.get("duracao_s") is not None:
        linhas.append(f"DURACAO:  {meta['duracao_s']:.1f}s")

    if meta.get("erro"):
        err = meta["erro"]
        linhas.append("")
        linhas.append("ERRO:")
        linhas.append(f"  tipo:     {err.get('tipo')}")
        linhas.append(f"  mensagem: {err.get('mensagem')}")

    if meta.get("metricas"):
        linhas.append("")
        linhas.append("MÉTRICAS:")
        for k, v in meta["metricas"].items():
            if isinstance(v, float):
                linhas.append(f"  {k:20s} {v:.4f}")
            else:
                linhas.append(f"  {k:20s} {v}")

    if meta.get("parametros"):
        linhas.append("")
        linhas.append("PARÂMETROS:")
        for k, v in meta["parametros"].items():
            linhas.append(f"  {k:20s} {v}")

    if meta.get("gates"):
        linhas.append("")
        linhas.append("GATES:")
        for nome, st in meta["gates"].items():
            linhas.append(f"  {nome:34s} {st}")

    if meta.get("notas"):
        linhas.append("")
        linhas.append(f"NOTAS: {meta['notas']}")

    linhas.append("")
    linhas.append(f"TIMESTAMP_UTC: {meta['timestamp']['utc']}")
    return "\n".join(linhas) + "\n"


def _versoes() -> dict[str, str | None]:
    """Versões das bibliotecas fundamentais da execução."""
    pacotes = [
        "numpy",
        "pandas",
        "pyarrow",
        "scikit-learn",
        "scipy",
        "matplotlib",
        "seaborn",
    ]
    resultado: dict[str, str | None] = {
        "python": platform.python_version(),
    }
    for pacote in pacotes:
        try:
            resultado[pacote] = metadata.version(pacote)
        except metadata.PackageNotFoundError:
            resultado[pacote] = None
    return resultado


def _git_info() -> dict[str, str | bool | None]:
    """Commit, branch e estado da árvore de trabalho."""

    def executar_git(args: list[str]) -> str | None:
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

    status = executar_git(["status", "--porcelain"])
    return {
        "commit": executar_git(["rev-parse", "HEAD"]),
        "branch": executar_git(["branch", "--show-current"]),
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
    status: str = "success",
    erro: dict[str, Any] | None = None,
    dataset_sha256: str | None = None,
) -> Path:
    """
    Grava `metadata.json` + `summary.txt` em `outputs/runs/<RUN_ID>/`.

    `status` deve ser `"success"` ou `"error"`; este último deve vir
    acompanhado de `erro` (dict com `tipo`, `mensagem` e opcionalmente
    `traceback`). Se `dataset_sha256` for None, fica ausente do metadata.
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


def listar_runs(
    output_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Lista os metadados das execuções registradas, ordenados por `run_id`
    decrescente. Cada item inclui o caminho da pasta em `"pasta"`.
    """
    raiz = Path(output_dir) if output_dir is not None else RUNS_DIR
    if not raiz.exists():
        return []

    runs: list[dict[str, Any]] = []
    for pasta in raiz.iterdir():
        if not pasta.is_dir():
            continue
        metadata_path = pasta / "metadata.json"
        if not metadata_path.exists():
            continue
        try:
            meta = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        meta["pasta"] = str(pasta)
        runs.append(meta)

    return sorted(
        runs,
        key=lambda item: str(item.get("run_id", "")),
        reverse=True,
    )


def carregar_run(
    run: str | Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Carrega o `metadata.json` de uma execução."""
    caminho = Path(run)
    if not caminho.is_absolute():
        caminho = (Path(output_dir) if output_dir else RUNS_DIR) / caminho

    metadata_path = caminho / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata.json não encontrado em {caminho}")

    return json.loads(metadata_path.read_text(encoding="utf-8"))


class Run:
    """
    Context manager de registro de execução.

    Uso::

        with Run(modelo="logistic", parametros={"C": 1.0}) as r:
            ...
            r.metrica(auc=0.82)

    O metadata é gravado sempre ao sair do bloco, inclusive em caso de
    exceção — com `status="error"` e `erro` estruturado. A exceção não
    é suprimida.
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

        status = "success"
        erro: dict[str, Any] | None = None
        if exc_type is not None:
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

        sha = _resolver_dataset_sha256(
            self.dataset_sha256,
            self.dataset_path,
        )

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
            dataset_sha256=sha,
        )
        return False