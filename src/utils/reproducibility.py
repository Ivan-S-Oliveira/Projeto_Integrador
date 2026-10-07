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
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.utils import config as C


RUNS_DIR: Path = getattr(C, "RUNS_DIR", C.ROOT_DIR / "outputs" / "runs")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def gerar_run_id(modelo: str | None = None) -> str:
    """YYYY-MM-DD_HHMMSS[_modelo] — segundos evitam colisão."""
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return f"{ts}_{modelo}" if modelo else ts


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
    base = Path(output_dir) if output_dir else RUNS_DIR
    pasta = base / (run_id or gerar_run_id(modelo))
    pasta.mkdir(parents=True, exist_ok=True)

    meta: dict[str, Any] = {
        "run_id":                pasta.name,
        "timestamp":             _agora(),
        "modelo":                modelo,
        "seed":                  seed if seed is not None else C.SEED,
        "duracao_s":             duracao_s,
        "parametros":            parametros or {},
        "dataset":               dataset or {},
        "features":              features or {},
        "metricas":              metricas or {},
        "notas":                 notas,
        "supervised_yaml_sha256": C.supervised_yaml_sha256(),
    }

    (pasta / "metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    (pasta / "summary.txt").write_text(_resumo(meta), encoding="utf-8")

    print(f"[reproducibility] run registrado em: {pasta}")
    return pasta


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