"""Documenta a transição entre a coorte provisória e a candidata definitiva.

A comparação reconcilia população, alvo, distribuição anual e schema.
O módulo não publica arquivos, não cria partições e não altera os
Parquets recebidos.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


@dataclass(frozen=True)
class CohortTransitionResult:
    """Resultado consolidado da transição de coorte."""

    annual_comparison: pd.DataFrame
    summary: dict[str, Any]

    @property
    def transition_gate_passed(self) -> bool:
        """Indica se a transição foi integralmente reconciliada."""

        return bool(
            self.summary["transition_gate_passed"]
        )


def sha256_file(
    path: Path,
    chunk_size: int = 1024 * 1024,
) -> str:
    """Calcula SHA-256 sem carregar o arquivo inteiro em memória."""

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


def _read_identity_and_target(
    path: Path,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Lê, ordena e valida identificador e alvo de um Parquet."""

    table = pq.read_table(
        path,
        columns=[
            "id_registro",
            "alvo_obito_srag",
        ],
    )

    if table["id_registro"].null_count:
        raise ValueError(
            "O artefato contém id_registro ausente: "
            f"{path}"
        )

    if table["alvo_obito_srag"].null_count:
        raise ValueError(
            "O artefato contém alvo ausente: "
            f"{path}"
        )

    identifiers = table[
        "id_registro"
    ].to_numpy(
        zero_copy_only=False
    )

    target = table[
        "alvo_obito_srag"
    ].to_numpy(
        zero_copy_only=False
    )

    order = np.argsort(
        identifiers,
        kind="stable",
    )

    identifiers = identifiers[order]
    target = target[order]

    duplicate_count = int(
        np.count_nonzero(
            identifiers[1:]
            == identifiers[:-1]
        )
    )

    if duplicate_count:
        raise ValueError(
            "O artefato contém id_registro duplicado: "
            f"{path}"
        )

    target_values = set(
        np.unique(target).tolist()
    )

    if not target_values <= {0, 1}:
        raise ValueError(
            "O artefato contém alvo fora de 0 e 1: "
            f"{sorted(target_values)}"
        )

    return (
        identifiers,
        target,
        int(len(identifiers)),
    )


def compare_population_and_target(
    provisional_ids: np.ndarray,
    provisional_target: np.ndarray,
    candidate_ids: np.ndarray,
    candidate_target: np.ndarray,
) -> dict[str, int]:
    """Reconcilia população e alvo por identificadores únicos."""

    only_provisional = np.setdiff1d(
        provisional_ids,
        candidate_ids,
        assume_unique=True,
    )

    only_candidate = np.setdiff1d(
        candidate_ids,
        provisional_ids,
        assume_unique=True,
    )

    common = np.intersect1d(
        provisional_ids,
        candidate_ids,
        assume_unique=True,
    )

    provisional_positions = np.searchsorted(
        provisional_ids,
        common,
    )

    candidate_positions = np.searchsorted(
        candidate_ids,
        common,
    )

    target_mismatches = int(
        np.count_nonzero(
            provisional_target[
                provisional_positions
            ]
            != candidate_target[
                candidate_positions
            ]
        )
    )

    return {
        "only_provisional_rows": int(
            len(only_provisional)
        ),
        "only_candidate_rows": int(
            len(only_candidate)
        ),
        "common_rows": int(
            len(common)
        ),
        "target_mismatches": (
            target_mismatches
        ),
    }


def compare_schemas(
    provisional_path: Path,
    candidate_path: Path,
) -> dict[str, Any]:
    """Compara nomes e tipos físicos das colunas."""

    provisional_schema = pq.ParquetFile(
        provisional_path
    ).schema_arrow

    candidate_schema = pq.ParquetFile(
        candidate_path
    ).schema_arrow

    provisional_types = {
        field.name: str(field.type)
        for field in provisional_schema
    }

    candidate_types = {
        field.name: str(field.type)
        for field in candidate_schema
    }

    provisional_columns = set(
        provisional_types
    )

    candidate_columns = set(
        candidate_types
    )

    common_columns = sorted(
        provisional_columns
        & candidate_columns
    )

    type_differences = {
        column: {
            "provisional": (
                provisional_types[column]
            ),
            "candidate": (
                candidate_types[column]
            ),
        }
        for column in common_columns
        if provisional_types[column]
        != candidate_types[column]
    }

    return {
        "common_columns": (
            common_columns
        ),
        "only_provisional_columns": sorted(
            provisional_columns
            - candidate_columns
        ),
        "only_candidate_columns": sorted(
            candidate_columns
            - provisional_columns
        ),
        "common_column_count": len(
            common_columns
        ),
        "only_provisional_column_count": len(
            provisional_columns
            - candidate_columns
        ),
        "only_candidate_column_count": len(
            candidate_columns
            - provisional_columns
        ),
        "type_differences": (
            type_differences
        ),
    }


def build_annual_comparison(
    provisional_path: Path,
    candidate_path: Path,
) -> pd.DataFrame:
    """Compara volume, óbitos e prevalência por ano."""

    provisional = pd.read_parquet(
        provisional_path,
        columns=[
            "id_registro",
            "ano_internacao",
            "alvo_obito_srag",
        ],
    )

    candidate = pd.read_parquet(
        candidate_path,
        columns=[
            "id_registro",
            "dt_interna",
            "alvo_obito_srag",
        ],
    )

    candidate["ano_internacao"] = pd.to_datetime(
        candidate["dt_interna"]
        .astype("string")
        .str.strip(),
        format="%Y-%m-%d",
        errors="coerce",
    ).dt.year.astype("Int64")

    if candidate[
        "ano_internacao"
    ].isna().any():
        raise ValueError(
            "A candidata contém ano de "
            "internação inválido."
        )

    def summarize(
        frame: pd.DataFrame,
    ) -> pd.DataFrame:
        result = (
            frame.groupby(
                "ano_internacao",
                dropna=False,
            )
            .agg(
                registros=(
                    "id_registro",
                    "size",
                ),
                obitos=(
                    "alvo_obito_srag",
                    "sum",
                ),
            )
            .reset_index()
        )

        result["prevalencia_obito"] = (
            result["obitos"]
            / result["registros"]
        )

        return result

    comparison = summarize(
        provisional
    ).merge(
        summarize(candidate),
        on="ano_internacao",
        how="outer",
        suffixes=(
            "_provisoria",
            "_candidata",
        ),
    )

    comparison["diferenca_registros"] = (
        comparison["registros_candidata"]
        - comparison["registros_provisoria"]
    )

    comparison["diferenca_obitos"] = (
        comparison["obitos_candidata"]
        - comparison["obitos_provisoria"]
    )

    comparison[
        "diferenca_prevalencia"
    ] = (
        comparison[
            "prevalencia_obito_candidata"
        ]
        - comparison[
            "prevalencia_obito_provisoria"
        ]
    )

    return comparison.sort_values(
        "ano_internacao"
    ).reset_index(
        drop=True
    )


def run_cohort_transition(
    provisional_path: Path,
    candidate_path: Path,
    candidate_manifest_path: Path,
    parity_manifest_path: Path,
) -> CohortTransitionResult:
    """Executa a transição e valida sua linhagem."""

    for path in (
        provisional_path,
        candidate_path,
        candidate_manifest_path,
        parity_manifest_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {path}"
            )

    candidate_manifest = json.loads(
        candidate_manifest_path.read_text(
            encoding="utf-8"
        )
    )

    parity_manifest = json.loads(
        parity_manifest_path.read_text(
            encoding="utf-8"
        )
    )

    candidate_hash = sha256_file(
        candidate_path
    )

    if (
        candidate_manifest[
            "candidate"
        ]["sha256"]
        != candidate_hash
    ):
        raise ValueError(
            "O hash da candidata diverge "
            "do manifesto da coorte."
        )

    if (
        parity_manifest[
            "candidate"
        ]["sha256"]
        != candidate_hash
    ):
        raise ValueError(
            "O hash da candidata diverge "
            "do relatório de paridade."
        )

    if not parity_manifest.get(
        "publication_gate_passed",
        False,
    ):
        raise ValueError(
            "O gate de paridade legada "
            "não foi aprovado."
        )

    (
        provisional_ids,
        provisional_target,
        provisional_rows,
    ) = _read_identity_and_target(
        provisional_path
    )

    (
        candidate_ids,
        candidate_target,
        candidate_rows,
    ) = _read_identity_and_target(
        candidate_path
    )

    population = (
        compare_population_and_target(
            provisional_ids,
            provisional_target,
            candidate_ids,
            candidate_target,
        )
    )

    schema = compare_schemas(
        provisional_path,
        candidate_path,
    )

    annual = build_annual_comparison(
        provisional_path,
        candidate_path,
    )

    annual_removed_rows = int(
        -annual[
            "diferenca_registros"
        ].sum()
    )

    transition_gate_passed = bool(
        population[
            "only_candidate_rows"
        ] == 0
        and population[
            "target_mismatches"
        ] == 0
        and population[
            "only_provisional_rows"
        ]
        == provisional_rows
        - candidate_rows
        and population[
            "common_rows"
        ]
        == candidate_rows
        and annual_removed_rows
        == population[
            "only_provisional_rows"
        ]
    )

    provisional_file = pq.ParquetFile(
        provisional_path
    )

    candidate_file = pq.ParquetFile(
        candidate_path
    )

    summary: dict[str, Any] = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "provisional": {
            "path": str(
                provisional_path
            ),
            "sha256": sha256_file(
                provisional_path
            ),
            "rows": provisional_rows,
            "columns": (
                provisional_file
                .metadata
                .num_columns
            ),
            "row_groups": (
                provisional_file
                .num_row_groups
            ),
        },
        "candidate": {
            "path": str(
                candidate_path
            ),
            "sha256": candidate_hash,
            "rows": candidate_rows,
            "columns": (
                candidate_file
                .metadata
                .num_columns
            ),
            "row_groups": (
                candidate_file
                .num_row_groups
            ),
        },
        "population": population,
        "schema": schema,
        "annual_removed_rows": (
            annual_removed_rows
        ),
        "transition_status": (
            "explained"
            if transition_gate_passed
            else "unexplained"
        ),
        "transition_gate_passed": (
            transition_gate_passed
        ),
        "execution_guarantees": {
            "provisional_modified": False,
            "candidate_modified": False,
            "cohort_published": False,
            "partitions_created": False,
            "test_consulted": False,
        },
    }

    return CohortTransitionResult(
        annual_comparison=annual,
        summary=summary,
    )


def write_transition_outputs(
    result: CohortTransitionResult,
    annual_path: Path,
    manifest_path: Path,
    overwrite: bool = False,
) -> None:
    """Grava os artefatos com proteção contra sobrescrita."""

    existing = [
        path
        for path in (
            annual_path,
            manifest_path,
        )
        if path.exists()
    ]

    if existing and not overwrite:
        formatted = "\n".join(
            f"- {path}"
            for path in existing
        )

        raise FileExistsError(
            "Já existem artefatos de transição:\n"
            f"{formatted}\n"
            "Use overwrite somente após revisar "
            "a execução anterior."
        )

    annual_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    annual_temp = annual_path.with_suffix(
        annual_path.suffix + ".tmp"
    )

    manifest_temp = manifest_path.with_suffix(
        manifest_path.suffix + ".tmp"
    )

    try:
        result.annual_comparison.to_csv(
            annual_temp,
            index=False,
            encoding="utf-8-sig",
        )

        manifest_temp.write_text(
            json.dumps(
                result.summary,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        os.replace(
            annual_temp,
            annual_path,
        )

        os.replace(
            manifest_temp,
            manifest_path,
        )

    except Exception:
        for temporary in (
            annual_temp,
            manifest_temp,
        ):
            if temporary.exists():
                temporary.unlink()

        raise