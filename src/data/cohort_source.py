"""Resolve a fonte de coorte sem acoplar notebooks ao nome do arquivo.

A troca entre coorte provisória e definitiva acontece por parâmetro ou
pela variável de ambiente ``SRAG_COHORT_KIND``. Não transforma a coorte,
não cria partições e não altera o alvo.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, get_args

import pandas as pd

from src.utils.hashing import sha256_file

CohortKind = Literal["provisional", "final", "auto"]

_ENV_VAR        = "SRAG_COHORT_KIND"
_DEFAULT_KIND   = "provisional"
_VALID_KINDS    = frozenset(get_args(CohortKind))
_ANALYTICAL_DIR = Path("data") / "analytical"

_FINAL_FILENAMES = ("coorte_final.parquet",)
_PROVISIONAL_FILENAMES = (
    "coorte_provisoria.parquet",
    "coorte_provisoria_b.parquet",
    "coorte.parquet",
)


@dataclass(frozen=True)
class CohortSource:
    """Metadados imutáveis da coorte selecionada."""

    kind: str
    path: str
    sha256: str
    size_bytes: int
    rows: int
    columns: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def cohort_candidates(root: Path) -> dict[str, tuple[Path, ...]]:
    """Candidatos de coorte por tipo, na ordem de preferência."""
    analytical = root / _ANALYTICAL_DIR
    return {
        "final":       tuple(analytical / n for n in _FINAL_FILENAMES),
        "provisional": tuple(analytical / n for n in _PROVISIONAL_FILENAMES),
    }


def _resolve_kind(kind: CohortKind | None) -> str:
    selected = (kind or os.getenv(_ENV_VAR, _DEFAULT_KIND)).lower()
    if selected not in _VALID_KINDS:
        raise ValueError(
            f"{_ENV_VAR} deve ser {sorted(_VALID_KINDS)}. Recebido: {selected!r}."
        )
    return selected


def _kind_from_path(path: Path) -> str:
    return "final" if "final" in path.name.lower() else "provisional"


def resolve_cohort_path(
    root: Path,
    *,
    kind: CohortKind | None = None,
    explicit_path: Path | None = None,
) -> tuple[str, Path]:
    """Resolve a coorte sem alternar silenciosamente de provisória para final.

    ``kind=None`` consulta ``SRAG_COHORT_KIND`` (default ``provisional``).
    ``auto`` prefere a definitiva quando existir. Execuções oficiais devem
    usar ``provisional`` ou ``final`` explícitos.
    """
    if explicit_path is not None:
        path = Path(explicit_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Coorte explícita não encontrada: {path}")
        return _kind_from_path(path), path

    selected   = _resolve_kind(kind)
    candidates = cohort_candidates(root)
    order      = ("final", "provisional") if selected == "auto" else (selected,)

    for effective_kind in order:
        for path in candidates[effective_kind]:
            if path.is_file():
                return effective_kind, path.resolve()

    candidatos = "\n".join(
        f"- {p}" for k in order for p in candidates[k]
    )
    raise FileNotFoundError(
        f"Nenhuma coorte do tipo {selected!r} encontrada. Candidatos:\n{candidatos}"
    )


def load_cohort(
    root: Path,
    *,
    kind: CohortKind | None = None,
    explicit_path: Path | None = None,
    columns: list[str] | None = None,
) -> tuple[pd.DataFrame, CohortSource]:
    """Carrega a coorte selecionada e devolve dados + metadados da fonte."""
    effective_kind, path = resolve_cohort_path(
        root, kind=kind, explicit_path=explicit_path,
    )
    frame  = pd.read_parquet(path, columns=columns)
    source = CohortSource(
        kind=effective_kind,
        path=str(path),
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        rows=int(len(frame)),
        columns=int(frame.shape[1]),
    )
    return frame, source