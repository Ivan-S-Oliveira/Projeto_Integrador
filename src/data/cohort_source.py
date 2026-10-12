"""Resolve e descreve a fonte de coorte sem acoplar notebooks ao nome do arquivo.

A troca entre coorte provisoria e definitiva deve acontecer por parametro ou pela
variavel de ambiente ``SRAG_COHORT_KIND``. O modulo nao transforma a coorte, nao
cria particoes e nao altera o alvo.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import pandas as pd

CohortKind = Literal["provisional", "final", "auto"]


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
        """Retorna representacao serializavel da fonte."""
        return asdict(self)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Calcula SHA-256 de um arquivo sem carrega-lo integralmente em memoria."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def cohort_candidates(root: Path) -> dict[str, tuple[Path, ...]]:
    """Retorna candidatos ordenados por tipo de coorte."""
    analytical = root / "data" / "analytical"
    return {
        "final": (
            analytical / "coorte_final.parquet",
        ),
        "provisional": (
            analytical / "coorte_provisoria.parquet",
            analytical / "coorte_provisoria_b.parquet",
            analytical / "coorte.parquet",
        ),
    }


def resolve_cohort_path(
    root: Path,
    *,
    kind: CohortKind | None = None,
    explicit_path: Path | None = None,
) -> tuple[str, Path]:
    """Resolve a coorte sem alternar silenciosamente de provisoria para final.

    ``kind=None`` consulta ``SRAG_COHORT_KIND`` e usa ``provisional`` como padrao.
    ``auto`` prefere a definitiva quando ela existir, mas imprime esse fato no
    notebook consumidor. Para reproducibilidade, execucoes oficiais devem usar
    ``provisional`` ou ``final`` explicitamente.
    """
    selected_kind = (kind or os.getenv("SRAG_COHORT_KIND", "provisional")).lower()
    if selected_kind not in {"provisional", "final", "auto"}:
        raise ValueError(
            "SRAG_COHORT_KIND deve ser provisional, final ou auto. "
            f"Recebido: {selected_kind!r}."
        )

    if explicit_path is not None:
        path = Path(explicit_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Coorte explicita nao encontrada: {path}")
        effective_kind = "final" if "final" in path.name.lower() else "provisional"
        return effective_kind, path

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
        f"Nenhuma coorte do tipo {selected_kind!r} foi encontrada. Candidatos:\n{formatted}"
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
