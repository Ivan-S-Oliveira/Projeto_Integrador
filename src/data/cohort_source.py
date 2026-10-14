"""Resolve e descreve a fonte de coorte sem acoplar notebooks ao nome do arquivo.

A troca entre coorte provisoria e definitiva deve acontecer por parametro ou pela
variavel de ambiente ``SRAG_COHORT_KIND``. O modulo nao transforma a coorte, nao
cria particoes e nao altera o alvo.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import pandas as pd

from src.utils.hashing import sha256_file

CohortKind = Literal["provisional", "final", "auto"]

_ENV_VAR = "SRAG_COHORT_KIND"
_DEFAULT_KIND: CohortKind = "provisional"
_VALID_KINDS: frozenset[str] = frozenset({"provisional", "final", "auto"})
_ANALYTICAL_DIR = Path("data") / "analytical"

_FINAL_FILENAMES = ("coorte_final.parquet",)
_PROVISIONAL_FILENAMES = (
    "coorte_provisoria.parquet",
    "coorte_provisoria_b.parquet",
    "coorte.parquet",
)


@dataclass(frozen=True)
class CohortSource:
    """Metadados imutaveis da coorte selecionada."""

    kind: str
    path: str
    sha256: str
    size_bytes: int
    rows: int
    columns: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def cohort_candidates(root: Path) -> dict[str, tuple[Path, ...]]:
    """Retorna candidatos ordenados por tipo de coorte."""
    analytical = root / _ANALYTICAL_DIR
    return {
        "final": tuple(analytical / name for name in _FINAL_FILENAMES),
        "provisional": tuple(analytical / name for name in _PROVISIONAL_FILENAMES),
    }


def _resolve_kind(kind: CohortKind | None) -> str:
    selected = (kind or os.getenv(_ENV_VAR, _DEFAULT_KIND)).lower()
    if selected not in _VALID_KINDS:
        raise ValueError(
            f"{_ENV_VAR} deve ser provisional, final ou auto. Recebido: {selected!r}."
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
    """Resolve a coorte sem alternar silenciosamente de provisoria para final.

    ``kind=None`` consulta ``SRAG_COHORT_KIND`` e usa ``provisional`` como padrao.
    ``auto`` prefere a definitiva quando ela existir. Para reproducibilidade,
    execucoes oficiais devem usar ``provisional`` ou ``final`` explicitamente.
    """
    if explicit_path is not None:
        path = Path(explicit_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Coorte explicita nao encontrada: {path}")
        return _kind_from_path(path), path

    selected_kind = _resolve_kind(kind)
    candidates = cohort_candidates(root)
    order = ("final", "provisional") if selected_kind == "auto" else (selected_kind,)

    checked: list[Path] = []
    for effective_kind in order:
        for path in candidates[effective_kind]:
            checked.append(path)
            if path.is_file():
                return effective_kind, path.resolve()

    formatted = "\n".join(f"- {path}" for path in checked)
    raise FileNotFoundError(
        f"Nenhuma coorte do tipo {selected_kind!r} foi encontrada. "
        f"Candidatos:\n{formatted}"
    )


def load_cohort(
    root: Path,
    *,
    kind: CohortKind | None = None,
    explicit_path: Path | None = None,
    columns: list[str] | None = None,
) -> tuple[pd.DataFrame, CohortSource]:
    """Carrega a coorte selecionada e devolve dados mais metadados da fonte."""
    effective_kind, path = resolve_cohort_path(
        root,
        kind=kind,
        explicit_path=explicit_path,
    )
    frame = pd.read_parquet(path, columns=columns)
    source = CohortSource(
        kind=effective_kind,
        path=str(path),
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        rows=int(len(frame)),
        columns=int(frame.shape[1]),
    )
    return frame, source