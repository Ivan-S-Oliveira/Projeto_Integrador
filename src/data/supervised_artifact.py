"""Persistencia e leitura do dataset supervisionado canonico.

O modulo separa notebooks da origem fisica da coorte. O Notebook 03 materializa
uma unica particao e os notebooks seguintes apenas a reutilizam.

O manifesto registra, alem do hash e das particoes:

- ``feature_columns`` — colunas efetivamente usadas como features;
- ``numeric_columns`` / ``categorical_columns`` — divisao das features por
  tipo, consumida por ``build_preprocessor`` (evita reclassificar manualmente
  em cada notebook);
- ``audit_columns`` — colunas presentes no parquet que NAO entram em X, mas
  devem ser preservadas para auditoria (ex.: ``sg_uf``, ``faixa_etaria``).
  Nao entram em ``feature_columns`` nem sao validadas como features.

Convencoes:

- As particoes canonicas sao ``treino``, ``validacao`` e ``teste``.
- ``split_partitions`` devolve ``(treino, validacao)`` — o par consumido
  durante a fase de selecao. O bloco ``teste`` NAO e exposto por essa
  funcao; use ``holdout_partition`` e respeite a disciplina do gate
  ``G9_holdout``.
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


def _resolver_grupos(
    feature_columns: Sequence[str],
    numeric_columns: Sequence[str] | None,
    categorical_columns: Sequence[str] | None,
) -> tuple[list[str] | None, list[str] | None]:
    """
    Resolve o par ``(numericas, categoricas)`` a partir das entradas.

    - Se ambas forem ``None``, devolve ``(None, None)`` — manifesto segue
      sem a divisao por tipo (compatibilidade com chamadas antigas).
    - Se apenas uma for passada, o complemento e inferido dentro de
      ``feature_columns``.
    - Se ambas forem passadas, valida que sao disjuntas e que a uniao
      cobre exatamente ``feature_columns``.
    """
    if numeric_columns is None and categorical_columns is None:
        return None, None

    feats = list(feature_columns)
    feats_set = set(feats)

    num: list[str] | None = list(numeric_columns) if numeric_columns is not None else None
    cat: list[str] | None = (
        list(categorical_columns) if categorical_columns is not None else None
    )

    if num is None:
        cat_set = set(cat or [])
        num = [c for c in feats if c not in cat_set]
    if cat is None:
        num_set = set(num)
        cat = [c for c in feats if c not in num_set]

    num_set, cat_set = set(num), set(cat)

    overlap = num_set & cat_set
    if overlap:
        raise ValueError(
            "Colunas presentes em numeric_columns E categorical_columns: "
            f"{sorted(overlap)}"
        )
    fora = (num_set | cat_set) - feats_set
    if fora:
        raise ValueError(
            "numeric_columns/categorical_columns contem colunas fora de "
            f"feature_columns: {sorted(fora)}"
        )
    faltando = feats_set - (num_set | cat_set)
    if faltando:
        raise ValueError(
            "Cada feature precisa estar em numeric_columns ou "
            f"categorical_columns. Faltando: {sorted(faltando)}"
        )
    return num, cat


def validate_supervised_frame(
    frame: pd.DataFrame,
    *,
    feature_columns: Sequence[str],
    target_column: str,
    partition_column: str,
    audit_columns: Sequence[str] | None = None,
) -> None:
    """Valida schema minimo, alvo e particoes do artefato supervisionado."""
    required = set(feature_columns) | {target_column, partition_column}
    if audit_columns:
        required |= set(audit_columns)
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
    numeric_columns: Sequence[str] | None = None,
    categorical_columns: Sequence[str] | None = None,
    audit_columns: Sequence[str] | None = None,
    overwrite: bool = False,
) -> tuple[Path, Path]:
    """
    Grava dataset e manifesto, preservando a particao criada no Notebook 03.

    Parametros
    ----------
    numeric_columns, categorical_columns : sequencia de str | None
        Divisao das ``feature_columns`` por tipo. Se ambas forem passadas,
        precisam particionar exatamente ``feature_columns``. Se apenas uma
        for passada, o complemento e inferido. Se ambas ``None``, o
        manifesto e gravado sem a divisao por tipo (compatibilidade).
    audit_columns : sequencia de str | None
        Colunas presentes no parquet que NAO entram em X, mas devem ser
        preservadas para auditoria (ex.: ``sg_uf``, ``faixa_etaria``).
        Validadas como presentes em ``frame``, mas nao confundidas com
        features.
    """
    num, cat = _resolver_grupos(feature_columns, numeric_columns, categorical_columns)

    validate_supervised_frame(
        frame,
        feature_columns=feature_columns,
        target_column=target_column,
        partition_column=partition_column,
        audit_columns=audit_columns,
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
        "schema_version": 2,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cohort_kind": str(cohort_kind),
        "source": dict(source),
        "dataset_path": str(dataset_path),
        "dataset_sha256": sha256_file(dataset_path),
        "rows": int(len(frame)),
        "columns": int(frame.shape[1]),
        "feature_columns": list(feature_columns),
        "numeric_columns": num,
        "categorical_columns": cat,
        "audit_columns": list(audit_columns) if audit_columns else [],
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
            audit_columns=manifest.get("audit_columns") or None,
        )
    manifest["dataset_path"] = str(dataset_path)
    return frame, manifest


def split_partitions(
    frame: pd.DataFrame,
    manifest: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Devolve ``(treino, validacao)`` a partir da coluna de particao canonica.

    Este e o par consumido durante a fase de selecao de modelo (C2..C6).
    O bloco ``teste`` NAO e exposto aqui de proposito — a avaliacao final
    exige o gate ``G9_holdout`` aprovado e passa por ``holdout_partition``.

    Levanta ``KeyError`` se a coluna de particao nao existir em ``frame`` e
    ``ValueError`` se qualquer um dos blocos estiver vazio.
    """
    col = manifest["partition_column"]
    if col not in frame.columns:
        raise KeyError(f"Coluna de particao ausente no DataFrame: {col!r}")

    rotulos = frame[col].astype(str)
    treino = frame.loc[rotulos == "treino"].reset_index(drop=True)
    validacao = frame.loc[rotulos == "validacao"].reset_index(drop=True)

    if treino.empty:
        raise ValueError("Particao 'treino' vazia no dataset supervisionado.")
    if validacao.empty:
        raise ValueError("Particao 'validacao' vazia no dataset supervisionado.")
    return treino, validacao


def holdout_partition(
    frame: pd.DataFrame,
    manifest: Mapping[str, Any],
) -> pd.DataFrame:
    """
    Devolve o bloco ``teste`` (holdout).

    Uso disciplinado: so deve ser chamada depois que o gate ``G9_holdout``
    estiver aprovado. A checagem do gate e responsabilidade do fluxo de
    modelagem (ver ``TemporalSplit.concluir_selecao``); esta funcao apenas
    isola o acesso fisico a particao.
    """
    col = manifest["partition_column"]
    if col not in frame.columns:
        raise KeyError(f"Coluna de particao ausente no DataFrame: {col!r}")

    teste = frame.loc[frame[col].astype(str) == "teste"].reset_index(drop=True)
    if teste.empty:
        raise ValueError("Particao 'teste' vazia no dataset supervisionado.")
    return teste