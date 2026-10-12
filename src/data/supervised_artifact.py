"""Persistencia e leitura do dataset supervisionado canonico.

O modulo separa notebooks da origem fisica da coorte. O Notebook 03 materializa
uma unica particao e os notebooks seguintes apenas a reutilizam.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

DATASET_NAME = "dataset_supervisionado.parquet"
MANIFEST_NAME = "manifesto_supervisionado.json"
ALLOWED_PARTITIONS = {"treino", "validacao", "teste"}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _analytical_dir(root: Path) -> Path:
    return Path(root).resolve() / "data" / "analytical"


def validate_supervised_frame(
    frame: pd.DataFrame,
    *,
    feature_columns: Sequence[str],
    target_column: str,
    partition_column: str,
) -> None:
    """Valida schema minimo, alvo e particoes do artefato supervisionado."""
    required = set(feature_columns) | {target_column, partition_column}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise KeyError(f"Colunas ausentes no dataset supervisionado: {missing}")
    if frame.empty:
        raise ValueError("O dataset supervisionado nao pode ser vazio.")
    target_values = set(
        pd.to_numeric(frame[target_column], errors="coerce")
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )
    if not target_values or not target_values.issubset({0, 1}):
        raise ValueError(f"Alvo deve ser binario 0/1. Observado: {sorted(target_values)}")
    observed = set(frame[partition_column].dropna().astype(str).unique().tolist())
    if observed != ALLOWED_PARTITIONS:
        raise ValueError(
            "Particoes esperadas treino, validacao e teste. "
            f"Observado: {sorted(observed)}"
        )


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
    overwrite: bool = False,
) -> tuple[Path, Path]:
    """Grava dataset e manifesto, preservando a particao criada no Notebook 03."""
    validate_supervised_frame(
        frame,
        feature_columns=feature_columns,
        target_column=target_column,
        partition_column=partition_column,
    )
    output_dir = _analytical_dir(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = output_dir / DATASET_NAME
    manifest_path = output_dir / MANIFEST_NAME
    if not overwrite and (dataset_path.exists() or manifest_path.exists()):
        raise FileExistsError(
            "Artefato supervisionado ja existe. Use overwrite=True somente em uma "
            "reconstrucao deliberada da mesma etapa."
        )
    frame.to_parquet(dataset_path, index=False)
    partition_counts = {
        str(key): int(value)
        for key, value in frame[partition_column].value_counts(dropna=False).items()
    }
    manifest = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cohort_kind": str(cohort_kind),
        "source": dict(source),
        "dataset_path": str(dataset_path),
        "dataset_sha256": sha256_file(dataset_path),
        "rows": int(len(frame)),
        "columns": int(frame.shape[1]),
        "feature_columns": list(feature_columns),
        "target_column": target_column,
        "partition_column": partition_column,
        "partition_counts": partition_counts,
        "seed": int(seed),
        "test_opened": False,
    }
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
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Carrega o artefato canonico e valida hash, tipo de coorte e schema."""
    output_dir = _analytical_dir(root)
    dataset_path = output_dir / DATASET_NAME
    manifest_path = output_dir / MANIFEST_NAME
    if not dataset_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError(
            "Execute o Notebook 03 adaptado para gerar dataset_supervisionado.parquet "
            "e manifesto_supervisionado.json."
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if expected_kind and manifest.get("cohort_kind") != expected_kind:
        raise RuntimeError(
            f"Artefato de coorte {manifest.get('cohort_kind')!r}, mas "
            f"SRAG_COHORT_KIND={expected_kind!r}. Reconstrua no Notebook 03."
        )
    actual_hash = sha256_file(dataset_path)
    if actual_hash != manifest.get("dataset_sha256"):
        raise RuntimeError("Hash do dataset supervisionado difere do manifesto.")
    frame = pd.read_parquet(dataset_path, columns=list(columns) if columns else None)
    if columns is None:
        validate_supervised_frame(
            frame,
            feature_columns=manifest["feature_columns"],
            target_column=manifest["target_column"],
            partition_column=manifest["partition_column"],
        )
    manifest["dataset_path"] = str(dataset_path)
    return frame, manifest
