"""
Registro de execuções para reprodutibilidade (critério C1).

Cada execução gera `outputs/runs/<RUN_ID>/` com:
    metadata.json   ← tudo estruturado
    summary.txt     ← versão legível

Uso:
    from src.utils.reproducibility import Run

    with Run(modelo="logistic", parametros={"C": 1.0}) as r:
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

from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

from src.utils import config as C


RUNS_DIR: Path = getattr(C, "RUNS_DIR", C.ROOT_DIR / "outputs" / "runs")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def gerar_run_id(
    modelo: str | None = None,
    base_dir: Path | None = None,
) -> str:
    """
    Gera um identificador unico para uma execucao.

    O uso de microssegundos reduz o risco de duas execucoes
    receberem o mesmo identificador.
    """
    agora = datetime.now().strftime(
        "%Y-%m-%d_%H%M%S_%f"
    )

    sufixo = (
        f"_{modelo}"
        if modelo
        else ""
    )

    candidato = (
        f"{agora}{sufixo}"
    )

    if base_dir is None:
        return candidato

    base = Path(base_dir)
    run_id = candidato
    contador = 1

    while (
        base / run_id
    ).exists():
        run_id = (
            f"{candidato}_{contador:02d}"
        )
        contador += 1

    return run_id


def _agora() -> dict[str, str]:
    utc = datetime.now(timezone.utc)
    return {
        "utc":   utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "local": utc.astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def _resumo(meta: dict[str, Any]) -> str:
    """summary.txt curto e legível."""
    linhas = [
        f"RUN_ID:   {meta['run_id']}",
        f"MODELO:   {meta['modelo']}",
        f"SEED:     {meta['seed']}",
    ]
    ds = meta.get("dataset") or {}
    for k in ("n_rows", "train_rows", "valid_rows", "test_rows"):
        if k in ds:
            linhas.append(f"{k.upper():9s} {ds[k]:,}")
    if meta.get("duracao_s") is not None:
        linhas.append(f"DURACAO:  {meta['duracao_s']:.1f}s")

    if meta.get("metricas"):
        linhas.append("")
        linhas.append("MÉTRICAS:")
        for k, v in meta["metricas"].items():
            linhas.append(f"  {k:20s} {v:.4f}" if isinstance(v, float)
                          else f"  {k:20s} {v}")

    if meta.get("parametros"):
        linhas.append("")
        linhas.append("PARÂMETROS:")
        for k, v in meta["parametros"].items():
            linhas.append(f"  {k:20s} {v}")

    if meta.get("notas"):
        linhas.append("")
        linhas.append(f"NOTAS: {meta['notas']}")

    linhas.append("")
    linhas.append(f"TIMESTAMP_UTC: {meta['timestamp']['utc']}")
    return "\n".join(linhas) + "\n"

def _versoes() -> dict[str, str | None]:
    """
    Retorna as versoes fundamentais da execucao.
    """
    pacotes = [
        "numpy",
        "pandas",
        "pyarrow",
        "scikit-learn",
        "scipy",
        "matplotlib",
        "seaborn",
    ]

    resultado = {
        "python": platform.python_version(),
    }

    for pacote in pacotes:
        try:
            resultado[pacote] = (
                metadata.version(pacote)
            )
        except metadata.PackageNotFoundError:
            resultado[pacote] = None

    return resultado


def _git_info() -> dict[str, str | bool | None]:
    """
    Retorna commit, branch e estado da arvore de trabalho.
    """

    def executar_git(
        argumentos: list[str],
    ) -> str | None:
        try:
            processo = subprocess.run(
                ["git"] + argumentos,
                cwd=C.ROOT_DIR,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except OSError:
            return None

        if processo.returncode != 0:
            return None

        return processo.stdout.strip()

    status = executar_git(
        ["status", "--porcelain"]
    )

    return {
        "commit": executar_git(
            ["rev-parse", "HEAD"]
        ),
        "branch": executar_git(
            ["branch", "--show-current"]
        ),
        "dirty": (
            bool(status)
            if status is not None
            else None
        ),
    }


def _env_info() -> dict[str, str | bool]:
    """
    Retorna informacoes nao sensiveis do ambiente.
    """
    return {
        "python_executable": sys.executable,
        "python_version": (
            platform.python_version()
        ),
        "platform": platform.platform(),
        "cwd": str(Path.cwd()),
        "ci": bool(
            os.getenv("CI")
            or os.getenv("GITHUB_ACTIONS")
        ),
    }

# ---------------------------------------------------------------------------
# Núcleo
# ---------------------------------------------------------------------------

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
) -> Path:
    """Grava metadata.json + summary.txt em outputs/runs/<RUN_ID>/."""
    base = Path(
    output_dir
    if output_dir is not None
    else RUNS_DIR
    )

    if run_id is None:
        run_id = gerar_run_id(
            modelo=modelo,
            base_dir=base,
        )

    pasta = base / run_id

    pasta.mkdir(
        parents=True,
        exist_ok=False,
    )

    meta: dict[str, Any] = {
        "run_id": pasta.name,
        "timestamp": _agora(),
        "modelo": modelo,
        "seed": (
            seed
            if seed is not None
            else C.SEED
        ),
        "duracao_s": duracao_s,
        "parametros": parametros or {},
        "dataset": dataset or {},
        "features": features or {},
        "metricas": metricas or {},
        "notas": notas,
        "versoes": _versoes(),
        "git": _git_info(),
        "env": _env_info(),
        "supervised_yaml_sha256": (
            C.supervised_yaml_sha256()
        ),
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
    Lista os metadados das execucoes registradas.

    Cada item retornado corresponde ao conteudo de um
    metadata.json e inclui tambem o caminho da pasta.
    """
    raiz = Path(
        output_dir
        if output_dir is not None
        else RUNS_DIR
    )

    if not raiz.exists():
        return []

    runs: list[dict[str, Any]] = []

    for pasta in raiz.iterdir():
        if not pasta.is_dir():
            continue

        metadata_path = (
            pasta / "metadata.json"
        )

        if not metadata_path.exists():
            continue

        try:
            meta = json.loads(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            json.JSONDecodeError,
            OSError,
        ):
            continue

        meta["pasta"] = str(pasta)

        runs.append(meta)

    return sorted(
        runs,
        key=lambda item: str(
            item.get("run_id", "")
        ),
        reverse=True,
    )


def carregar_run(
    run: str | Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Carrega o metadata.json de uma execucao.
    """
    caminho = Path(run)

    if not caminho.is_absolute():
        raiz = Path(
            output_dir or RUNS_DIR
        )

        caminho = (
            raiz / caminho
        )

    metadata_path = (
        caminho / "metadata.json"
    )

    if not metadata_path.exists():
        raise FileNotFoundError(
            "metadata.json nao encontrado em "
            f"{caminho}"
        )

    texto = metadata_path.read_text(
        encoding="utf-8"
    )

    return json.loads(texto)
# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

class Run:
    """with Run(modelo="logistic", parametros={"C": 1.0}) as r: ..."""

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
    ) -> None:
        self.modelo      = modelo
        self.seed        = seed
        self.parametros  = dict(parametros or {})
        self.dataset     = dict(dataset or {})
        self.features    = dict(features or {})
        self.notas       = notas
        self.output_dir  = output_dir
        self._metricas:  dict[str, Any] = {}
        self._inicio:    float | None = None
        self.pasta:      Path | None = None

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
        )
        return False  # não suprime exceção