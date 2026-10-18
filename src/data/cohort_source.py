"""Resolve a fonte de coorte sem acoplar notebooks ao nome do arquivo.

A troca entre coorte provisória e definitiva acontece por parâmetro ou
pela variável de ambiente ``SRAG_COHORT_KIND``.

Contrato:
- ``kind=None`` consulta ``SRAG_COHORT_KIND`` (default ``provisional``).
- ``auto`` prefere a definitiva quando existir.
- ``explicit_path`` exige nome canônico; se ``kind`` também for informado
  e divergir da classificação pelo nome, a chamada falha em vez de
  prosseguir com o tipo errado.

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

CohortKind = Literal["provisional", "final", "auto"]

_ENV_VAR: str = "SRAG_COHORT_KIND"
_DEFAULT_KIND: str = "provisional"
_VALID_KINDS: frozenset[str] = frozenset(get_args(CohortKind))

_ANALYTICAL_DIR = Path("data") / "analytical"

# Nomes canônicos por tipo. Só estes são aceitos em `explicit_path` e na
# descoberta automática. Nomes ambíguos (ex.: "coorte.parquet") foram
# deliberadamente removidos para impedir que uma coorte definitiva salva
# com nome errado seja carregada como provisória.
_FILENAMES_BY_KIND: dict[str, tuple[str, ...]] = {
    "final":       ("coorte_final.parquet",),
    "provisional": ("coorte_provisoria.parquet", "coorte_provisoria_b.parquet"),
}

# Índice reverso (nome em minúsculas → tipo), preenchido uma única vez.
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
    """Resolve a coorte sem alternar silenciosamente de provisória para final.

    Parâmetros
    ----------
    root:
        Raiz do projeto (contém ``data/analytical``).
    kind:
        ``provisional``, ``final`` ou ``auto``. ``None`` consulta a
        variável de ambiente ``SRAG_COHORT_KIND``.
    explicit_path:
        Caminho explícito para uma coorte. Quando informado, o nome do
        arquivo precisa estar na lista canônica do tipo; se ``kind`` for
        ``provisional`` ou ``final`` e divergir do nome, a chamada falha.
    """
    if explicit_path is not None:
        return _resolve_explicit_path(explicit_path, requested_kind=kind)

    selected = _resolve_kind(kind)
    candidates = cohort_candidates(root)
    preference = ("final", "provisional") if selected == "auto" else (selected,)

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
    if selected not in _VALID_KINDS:
        raise ValueError(
            f"{_ENV_VAR} deve ser provisional, final ou auto. "
            f"Recebido: {selected!r}."
        )
    return selected


def _kind_from_path(path: Path) -> str:
    """Classifica uma coorte pelo nome canônico. Nome desconhecido → ``ValueError``."""
    kind = _KIND_BY_FILENAME.get(path.name.lower())
    if kind is not None:
        return kind
    raise ValueError(_unknown_filename_message(path))


def _resolve_explicit_path(
    explicit_path: Path,
    *,
    requested_kind: CohortKind | None,
) -> tuple[str, Path]:
    """Valida existência, nome canônico e coerência com ``kind`` explícito."""
    path = Path(explicit_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Coorte explícita não encontrada: {path}")

    declared = _kind_from_path(path)

    if (
        requested_kind is not None
        and requested_kind != "auto"
        and declared != requested_kind
    ):
        raise ValueError(
            f"Coorte em {path.name!r} classificada como {declared!r} pelo "
            f"nome, mas kind={requested_kind!r} foi solicitado. "
            "Renomeie o arquivo para um nome canônico do tipo desejado "
            "ou remova `kind` para aceitar a classificação pelo nome."
        )

    return declared, path


def _unknown_filename_message(path: Path) -> str:
    known = ", ".join(
        f"{name} ({kind})"
        for kind, names in _FILENAMES_BY_KIND.items()
        for name in names
    )
    return (
        f"Nome de coorte não reconhecido: {path.name!r}. "
        f"Esperado um de: {known}. "
        "Renomeie o arquivo ou passe `kind` explicitamente."
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