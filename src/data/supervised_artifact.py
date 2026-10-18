"""Persistencia e leitura do dataset supervisionado canonico.

O manifesto registra features, divisao por tipo, colunas de auditoria e
particoes. As particoes canonicas sao ``treino``, ``validacao`` e ``teste``.

O bloco ``teste`` exige o gate ``G9_holdout`` aprovado: tanto
``load_supervised_artifact(partitions=(..., "teste"))`` quanto
``holdout_partition`` levantam ``GatePendenteError`` caso contrario.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from src.utils.config import GatePendenteError, exigir_gate
from src.utils.hashing import sha256_file

__all__ = [
    "ALLOWED_PARTITIONS",
    "DATASET_NAME",
    "MANIFEST_NAME",
    "SCHEMA_VERSION",
    "GatePendenteError",
    "holdout_partition",
    "load_supervised_artifact",
    "persist_supervised_artifact",
    "split_partitions",
    "validate_supervised_frame",
]

DATASET_NAME = "dataset_supervisionado.parquet"
MANIFEST_NAME = "manifesto_supervisionado.json"
SCHEMA_VERSION = 2

_PARTITION_TREINO = "treino"
_PARTITION_VALIDACAO = "validacao"
_PARTITION_TESTE = "teste"

ALLOWED_PARTITIONS = frozenset({_PARTITION_TREINO, _PARTITION_VALIDACAO, _PARTITION_TESTE})


def _paths(root: Path) -> tuple[Path, Path]:
    output_dir = Path(root).resolve() / "data" / "analytical"
    return output_dir / DATASET_NAME, output_dir / MANIFEST_NAME


def _validar_grupos(num_set: set[str], cat_set: set[str], feats_set: set[str]) -> None:
    if overlap := num_set & cat_set:
        raise ValueError(
            f"Colunas presentes em numeric_columns E categorical_columns: {sorted(overlap)}"
        )
    if fora := (num_set | cat_set) - feats_set:
        raise ValueError(
            f"numeric_columns/categorical_columns contem colunas fora de "
            f"feature_columns: {sorted(fora)}"
        )
    if faltando := feats_set - (num_set | cat_set):
        raise ValueError(
            f"Cada feature precisa estar em numeric_columns ou categorical_columns. "
            f"Faltando: {sorted(faltando)}"
        )


def _resolver_grupos(
    feature_columns: Sequence[str],
    numeric_columns: Sequence[str] | None,
    categorical_columns: Sequence[str] | None,
) -> tuple[list[str] | None, list[str] | None]:
    """Resolve o par (numericas, categoricas).

    - ambas None → (None, None)
    - apenas uma → o complemento é inferido dentro de feature_columns
    - ambas → valida disjunção e cobertura exata
    """
    if numeric_columns is None and categorical_columns is None:
        return None, None

    num = list(numeric_columns) if numeric_columns is not None else None
    cat = list(categorical_columns) if categorical_columns is not None else None

    if num is None:
        assert cat is not None
        cat_set = set(cat)
        num = [c for c in feature_columns if c not in cat_set]
    if cat is None:
        num_set = set(num)
        cat = [c for c in feature_columns if c not in num_set]

    _validar_grupos(set(num), set(cat), set(feature_columns))
    return num, cat


def validate_supervised_frame(
    frame: pd.DataFrame,
    *,
    feature_columns: Sequence[str],
    target_column: str,
    partition_column: str,
    audit_columns: Sequence[str] | None = None,
    required_partitions: Sequence[str] | None = None,
) -> None:
    """Valida schema minimo, alvo binario e particoes do dataset.

    ``required_partitions=None`` exige as tres particoes canonicas; um
    subconjunto permite validar leituras parciais (ex.: treino+validacao).
    """
    required = set(feature_columns) | {target_column, partition_column}
    if audit_columns:
        required |= set(audit_columns)

    if missing := sorted(required - set(frame.columns)):
        raise KeyError(f"Colunas ausentes no dataset supervisionado: {missing}")

    if frame.empty:
        raise ValueError("O dataset supervisionado nao pode ser vazio.")

    target_values = set(
        pd.to_numeric(frame[target_column], errors="coerce")
        .dropna().astype(int).unique()
    )
    if not target_values or not target_values.issubset({0, 1}):
        raise ValueError(f"Alvo deve ser binario 0/1. Observado: {sorted(target_values)}")

    expected = (
        frozenset(required_partitions) if required_partitions is not None
        else ALLOWED_PARTITIONS
    )
    if unknown := expected - ALLOWED_PARTITIONS:
        raise ValueError(f"Particoes desconhecidas: {sorted(unknown)}")

    observed = set(frame[partition_column].dropna().astype(str).unique())
    if observed != expected:
        raise ValueError(
            f"Particoes esperadas {sorted(expected)}. Observado: {sorted(observed)}"
        )


def _build_manifest(
    *,
    frame: pd.DataFrame,
    dataset_path: Path,
    source: Mapping[str, Any],
    feature_columns: Sequence[str],
    numeric_columns: list[str] | None,
    categorical_columns: list[str] | None,
    audit_columns: Sequence[str] | None,
    target_column: str,
    partition_column: str,
    cohort_kind: str,
    seed: int,
) -> dict[str, Any]:
    partition_counts = {
        str(key): int(value)
        for key, value in frame[partition_column].value_counts(dropna=False).items()
    }
    return {
        "schema_version":      SCHEMA_VERSION,
        "generated_utc":       datetime.now(timezone.utc).isoformat(),
        "cohort_kind":         str(cohort_kind),
        "source":              dict(source),
        "dataset_path":        str(dataset_path),
        "dataset_sha256":      sha256_file(dataset_path),
        "rows":                int(len(frame)),
        "columns":             int(frame.shape[1]),
        "feature_columns":     list(feature_columns),
        "numeric_columns":     numeric_columns,
        "categorical_columns": categorical_columns,
        "audit_columns":       list(audit_columns) if audit_columns else [],
        "target_column":       target_column,
        "partition_column":    partition_column,
        "partition_counts":    partition_counts,
        "seed":                int(seed),
        "test_opened":         False,
    }


def persist_supervised_artifact(
    frame: pd.DataFrame,
    *,
    root: Path,
    source: Mapping[str, Any],
    feature_columns: Sequence[str],
    target_column: str,
    partition_column: str,
    cohort_kind: str,
    seed: int,
    numeric_columns: Sequence[str] | None = None,
    categorical_columns: Sequence[str] | None = None,
    audit_columns: Sequence[str] | None = None,
    overwrite: bool = False,
) -> tuple[Path, Path]:
    """Grava dataset e manifesto, exigindo as tres particoes canonicas."""
    num, cat = _resolver_grupos(feature_columns, numeric_columns, categorical_columns)

    validate_supervised_frame(
        frame,
        feature_columns=feature_columns,
        target_column=target_column,
        partition_column=partition_column,
        audit_columns=audit_columns,
    )

    dataset_path, manifest_path = _paths(root)
    dataset_path.parent.mkdir(parents=True, exist_ok=True)

    if not overwrite and (dataset_path.exists() or manifest_path.exists()):
        raise FileExistsError(
            "Artefato supervisionado ja existe. Use overwrite=True somente em uma "
            "reconstrucao deliberada da mesma etapa."
        )

    frame.to_parquet(dataset_path, index=False)

    manifest = _build_manifest(
        frame=frame,
        dataset_path=dataset_path,
        source=source,
        feature_columns=feature_columns,
        numeric_columns=num,
        categorical_columns=cat,
        audit_columns=audit_columns,
        target_column=target_column,
        partition_column=partition_column,
        cohort_kind=cohort_kind,
        seed=seed,
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return dataset_path, manifest_path


def load_supervised_artifact(
    root: Path,
    *,
    expected_kind: str | None = None,
    columns: Sequence[str] | None = None,
    partitions: Sequence[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Carrega o artefato canonico e valida hash, tipo de coorte e schema.

    ``partitions`` restringe o subconjunto carregado (pushdown no Parquet);
    o default e ``("treino", "validacao")``. Incluir ``"teste"`` exige o
    gate ``G9_holdout`` aprovado — caso contrario levanta
    ``GatePendenteError`` antes de tocar no arquivo.
    """
    dataset_path, manifest_path = _paths(root)

    if not dataset_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError(
            f"Execute o Notebook 03 adaptado para gerar {DATASET_NAME} e {MANIFEST_NAME}."
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if expected_kind and manifest.get("cohort_kind") != expected_kind:
        raise RuntimeError(
            f"Artefato de coorte {manifest.get('cohort_kind')!r}, mas "
            f"SRAG_COHORT_KIND={expected_kind!r}. Reconstrua no Notebook 03."
        )

    if sha256_file(dataset_path) != manifest.get("dataset_sha256"):
        raise RuntimeError("Hash do dataset supervisionado difere do manifesto.")

    selected = (
        tuple(partitions) if partitions is not None
        else (_PARTITION_TREINO, _PARTITION_VALIDACAO)
    )
    if not selected:
        raise ValueError("``partitions`` nao pode ser vazio.")

    if unknown := set(selected) - ALLOWED_PARTITIONS:
        raise ValueError(
            f"Particoes desconhecidas: {sorted(unknown)}. "
            f"Use subconjunto de {sorted(ALLOWED_PARTITIONS)}."
        )

    if _PARTITION_TESTE in selected:
        exigir_gate("G9_holdout")

    frame = pd.read_parquet(
        dataset_path,
        columns=list(columns) if columns else None,
        filters=[(manifest["partition_column"], "in", list(selected))],
    )

    if columns is None:
        validate_supervised_frame(
            frame,
            feature_columns=manifest["feature_columns"],
            target_column=manifest["target_column"],
            partition_column=manifest["partition_column"],
            audit_columns=manifest.get("audit_columns") or None,
            required_partitions=selected,
        )

    manifest["dataset_path"] = str(dataset_path)
    return frame, manifest


def _select_partition(
    frame: pd.DataFrame,
    manifest: Mapping[str, Any],
    partition: str,
) -> pd.DataFrame:
    col = manifest["partition_column"]
    if col not in frame.columns:
        raise KeyError(f"Coluna de particao ausente no DataFrame: {col!r}")
    return frame.loc[frame[col].astype(str) == partition].reset_index(drop=True)


def split_partitions(
    frame: pd.DataFrame,
    manifest: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devolve ``(treino, validacao)`` para a fase de selecao (C2..C6).

    O bloco ``teste`` nao e exposto — use ``holdout_partition`` apos
    aprovar ``G9_holdout``.
    """
    treino = _select_partition(frame, manifest, _PARTITION_TREINO)
    validacao = _select_partition(frame, manifest, _PARTITION_VALIDACAO)

    if treino.empty:
        raise ValueError("Particao 'treino' vazia no dataset supervisionado.")
    if validacao.empty:
        raise ValueError("Particao 'validacao' vazia no dataset supervisionado.")

    return treino, validacao


def holdout_partition(
    frame: pd.DataFrame,
    manifest: Mapping[str, Any],
) -> pd.DataFrame:
    """Devolve o bloco ``teste``. Exige ``G9_holdout`` aprovado."""
    exigir_gate("G9_holdout")
    teste = _select_partition(frame, manifest, _PARTITION_TESTE)
    if teste.empty:
        raise ValueError("Particao 'teste' vazia no dataset supervisionado.")
    return teste