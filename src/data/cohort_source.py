"""Resolve a coorte definitiva sem acoplar notebooks ao nome do arquivo.

O projeto usa uma única coorte: a definitiva (``coorte_final.parquet``).
A coorte provisória foi aposentada e não é mais aceita por este módulo.
A variável de ambiente ``SRAG_COHORT_KIND`` continua existindo por
compatibilidade com os notebooks e só aceita ``final``.

Contrato:
- ``kind=None`` consulta ``SRAG_COHORT_KIND`` (default ``final``).
- ``kind="provisional"`` e ``kind="auto"`` falham com erro explicativo.
- ``explicit_path`` exige o nome canônico ``coorte_final.parquet``.

Não transforma a coorte, não cria partições e não altera o alvo.
"""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, get_args

import pandas as pd

from src.utils.hashing import sha256_file

# ---------------------------------------------------------------------------
# Tipo e constantes
# ---------------------------------------------------------------------------
CohortKind = Literal["final"]

_ENV_VAR: str = "SRAG_COHORT_KIND"
_DEFAULT_KIND: str = "final"
_VALID_KINDS: frozenset[str] = frozenset(get_args(CohortKind))
# Tipos que existiram antes: geram erro explicativo em vez de "valor inválido".
_RETIRED_KINDS: frozenset[str] = frozenset({"provisional", "auto"})
_ANALYTICAL_DIR = Path("data") / "analytical"

# Nome canônico por tipo. Só este é aceito em ``explicit_path`` e na descoberta
# automática. Nomes ambíguos (ex.: "coorte.parquet") continuam rejeitados.
_FILENAMES_BY_KIND: dict[str, tuple[str, ...]] = {
    "final": ("coorte_final.parquet",),
}

# Índice reverso (nome em minúsculas -> tipo), preenchido uma única vez.
_KIND_BY_FILENAME: dict[str, str] = {
    name.lower(): kind
    for kind, names in _FILENAMES_BY_KIND.items()
    for name in names
}


# ---------------------------------------------------------------------------
# Modelo de metadados
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------
def cohort_candidates(root: Path) -> dict[str, tuple[Path, ...]]:
    """Candidatos de coorte por tipo, na ordem de preferência."""
    analytical = root / _ANALYTICAL_DIR
    return {
        kind: tuple(analytical / name for name in names)
        for kind, names in _FILENAMES_BY_KIND.items()
    }


def resolve_cohort_path(
    root: Path,
    *,
    kind: CohortKind | None = None,
    explicit_path: Path | None = None,
) -> tuple[str, Path]:
    """Resolve o caminho da coorte definitiva.

    Parâmetros
    ----------
    root:
        Raiz do projeto (contém ``data/analytical``).
    kind:
        ``final``. ``None`` consulta a variável de ambiente
        ``SRAG_COHORT_KIND``. ``provisional`` e ``auto`` falham.
    explicit_path:
        Caminho explícito para a coorte. O nome do arquivo precisa ser o
        canônico (``coorte_final.parquet``).
    """
    if explicit_path is not None:
        return _resolve_explicit_path(explicit_path, requested_kind=kind)

    selected = _resolve_kind(kind)
    candidates = cohort_candidates(root)
    preference = (selected,)

    for effective_kind in preference:
        for path in candidates[effective_kind]:
            if path.is_file():
                return effective_kind, path.resolve()

    raise FileNotFoundError(_not_found_message(selected, preference, candidates))


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
    frame = pd.read_parquet(path, columns=columns)
    for col in frame.select_dtypes(include=["object", "string"]).columns:
        if frame[col].nunique(dropna=True) <= 1000:
            frame[col] = frame[col].astype("category")
    source = CohortSource(
        kind=effective_kind,
        path=str(path),
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        rows=int(len(frame)),
        columns=int(frame.shape[1]),
    )
    return frame, source


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------
def _resolve_kind(kind: CohortKind | None) -> str:
    """Normaliza o tipo solicitado (parâmetro ou env var)."""
    selected = (kind or os.getenv(_ENV_VAR, _DEFAULT_KIND)).lower()
    if selected in _RETIRED_KINDS:
        raise ValueError(
            f"Tipo de coorte {selected!r} não é mais aceito: a coorte "
            "provisória foi aposentada e o projeto usa apenas a definitiva. "
            f"Use 'final' (parâmetro kind ou variável {_ENV_VAR})."
        )
    if selected not in _VALID_KINDS:
        raise ValueError(
            f"{_ENV_VAR} deve ser final. Recebido: {selected!r}."
        )
    return selected


def _kind_from_path(path: Path) -> str:
    """Classifica uma coorte pelo nome canônico. Nome desconhecido -> ``ValueError``."""
    kind = _KIND_BY_FILENAME.get(path.name.lower())
    if kind is not None:
        return kind
    raise ValueError(_unknown_filename_message(path))


def _resolve_explicit_path(
    explicit_path: Path,
    *,
    requested_kind: CohortKind | None,
) -> tuple[str, Path]:
    """Valida o tipo pedido, a existência e o nome canônico do arquivo."""
    if requested_kind is not None:
        _resolve_kind(requested_kind)

    path = Path(explicit_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Coorte explícita não encontrada: {path}")

    return _kind_from_path(path), path


def _unknown_filename_message(path: Path) -> str:
    known = ", ".join(
        f"{name} ({kind})"
        for kind, names in _FILENAMES_BY_KIND.items()
        for name in names
    )
    aposentada = ""
    if path.name.lower().startswith("coorte_provisoria"):
        aposentada = " A coorte provisória foi aposentada."
    return (
        f"Nome de coorte não reconhecido: {path.name!r}. "
        f"Esperado um de: {known}.{aposentada} "
        "Renomeie o arquivo para o nome canônico da coorte definitiva."
    )


def _not_found_message(
    selected: str,
    preference: tuple[str, ...],
    candidates: dict[str, tuple[Path, ...]],
) -> str:
    paths = "\n".join(
        f"- {path}" for kind in preference for path in candidates[kind]
    )
    return f"Nenhuma coorte do tipo {selected!r} encontrada. Candidatos:\n{paths}"
