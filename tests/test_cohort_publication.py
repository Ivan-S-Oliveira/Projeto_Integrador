from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pytest

from src.data.cohort_publication import (
    publish_final_cohort,
    sha256_file,
    validate_publication_gates,
)


def _write_candidate(
    tmp_path: Path,
) -> tuple[Path, str]:
    candidate_path = (
        tmp_path / "candidate.parquet"
    )

    frame = pd.DataFrame(
        {
            "id_registro": [1, 2],
            "alvo_obito_srag": pd.Series(
                [0, 1],
                dtype="int8",
            ),
        }
    )

    frame.to_parquet(
        candidate_path,
        index=False,
    )

    return (
        candidate_path,
        sha256_file(candidate_path),
    )


def _write_evidence(
    tmp_path: Path,
) -> dict[str, Path]:
    (
        candidate_path,
        candidate_hash,
    ) = _write_candidate(tmp_path)

    parquet_file = pq.ParquetFile(
        candidate_path
    )

    candidate_manifest_path = (
        tmp_path / "manifest.json"
    )

    validation_path = (
        tmp_path / "validation.json"
    )

    parity_path = (
        tmp_path / "parity.json"
    )

    transition_path = (
        tmp_path / "transition.json"
    )

    candidate_manifest_path.write_text(
        json.dumps(
            {
                "candidate": {
                    "sha256": (
                        candidate_hash
                    ),
                },
                "execution_guarantees": {
                    "test_consulted": False,
                    "partitions_created": False,
                },
            }
        ),
        encoding="utf-8",
    )

    validation_path.write_text(
        json.dumps(
            {
                "status": (
                    "approved_for_comparison"
                ),
                "candidate_sha256": (
                    candidate_hash
                ),
                "checks": {
                    "physical_rows": 2,
                    "physical_columns": 2,
                    "row_groups": (
                        parquet_file
                        .num_row_groups
                    ),
                    "id_registro_missing": 0,
                    "id_registro_distinct": 2,
                    "approved_rule_violations": {
                        "regra": 0,
                    },
                    "target_missing": 0,
                    "target_values": [0, 1],
                },
                "population_reconciliation": {
                    "closed": True,
                },
                "publication_performed": False,
                "legacy_parity_reviewed": False,
                "provisional_comparison_reviewed": False,
            }
        ),
        encoding="utf-8",
    )

    parity_path.write_text(
        json.dumps(
            {
                "candidate": {
                    "sha256": (
                        candidate_hash
                    ),
                },
                "population_parity_status": (
                    "explained"
                ),
                "target_parity_status": (
                    "passed"
                ),
                "publication_gate_passed": True,
                "totals": {
                    "only_legacy_unexplained": 0,
                    "only_candidate_unexplained": 0,
                    "target_mismatches": 0,
                },
                "execution_guarantees": {
                    "test_consulted": False,
                    "partitions_created": False,
                },
            }
        ),
        encoding="utf-8",
    )

    transition_path.write_text(
        json.dumps(
            {
                "candidate": {
                    "sha256": (
                        candidate_hash
                    ),
                },
                "transition_status": (
                    "explained"
                ),
                "transition_gate_passed": True,
                "population": {
                    "only_provisional_rows": 1,
                    "only_candidate_rows": 0,
                    "target_mismatches": 0,
                },
                "annual_removed_rows": 1,
                "execution_guarantees": {
                    "test_consulted": False,
                    "partitions_created": False,
                },
            }
        ),
        encoding="utf-8",
    )

    return {
        "candidate": candidate_path,
        "candidate_manifest": (
            candidate_manifest_path
        ),
        "validation": validation_path,
        "parity": parity_path,
        "transition": transition_path,
    }


def test_validate_publication_gates_accepts_valid_evidence(
    tmp_path: Path,
) -> None:
    paths = _write_evidence(
        tmp_path
    )

    result = validate_publication_gates(
        candidate_path=paths[
            "candidate"
        ],
        candidate_manifest_path=paths[
            "candidate_manifest"
        ],
        candidate_validation_path=paths[
            "validation"
        ],
        parity_manifest_path=paths[
            "parity"
        ],
        transition_manifest_path=paths[
            "transition"
        ],
    )

    assert result["rows"] == 2
    assert result["columns"] == 2


def test_validate_publication_gates_rejects_hash_mismatch(
    tmp_path: Path,
) -> None:
    paths = _write_evidence(
        tmp_path
    )

    parity = json.loads(
        paths["parity"].read_text(
            encoding="utf-8"
        )
    )

    parity["candidate"]["sha256"] = (
        "invalido"
    )

    paths["parity"].write_text(
        json.dumps(parity),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="SHA-256",
    ):
        validate_publication_gates(
            candidate_path=paths[
                "candidate"
            ],
            candidate_manifest_path=paths[
                "candidate_manifest"
            ],
            candidate_validation_path=paths[
                "validation"
            ],
            parity_manifest_path=paths[
                "parity"
            ],
            transition_manifest_path=paths[
                "transition"
            ],
        )


def test_validate_publication_gates_rejects_failed_transition(
    tmp_path: Path,
) -> None:
    paths = _write_evidence(
        tmp_path
    )

    transition = json.loads(
        paths["transition"].read_text(
            encoding="utf-8"
        )
    )

    transition[
        "transition_gate_passed"
    ] = False

    paths["transition"].write_text(
        json.dumps(transition),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="transição",
    ):
        validate_publication_gates(
            candidate_path=paths[
                "candidate"
            ],
            candidate_manifest_path=paths[
                "candidate_manifest"
            ],
            candidate_validation_path=paths[
                "validation"
            ],
            parity_manifest_path=paths[
                "parity"
            ],
            transition_manifest_path=paths[
                "transition"
            ],
        )


def test_publish_final_cohort_preserves_candidate(
    tmp_path: Path,
) -> None:
    paths = _write_evidence(
        tmp_path
    )

    published_path = (
        tmp_path
        / "data"
        / "analytical"
        / "coorte_final.parquet"
    )

    publication_manifest_path = (
        published_path.with_suffix(
            ".manifest.json"
        )
    )

    candidate_hash = sha256_file(
        paths["candidate"]
    )

    result = publish_final_cohort(
        candidate_path=paths[
            "candidate"
        ],
        published_path=published_path,
        candidate_manifest_path=paths[
            "candidate_manifest"
        ],
        candidate_validation_path=paths[
            "validation"
        ],
        parity_manifest_path=paths[
            "parity"
        ],
        transition_manifest_path=paths[
            "transition"
        ],
        publication_manifest_path=(
            publication_manifest_path
        ),
    )

    assert paths[
        "candidate"
    ].is_file()

    assert published_path.is_file()

    assert (
        publication_manifest_path
        .is_file()
    )

    assert (
        result.candidate_sha256
        == candidate_hash
    )

    assert (
        result.published_sha256
        == candidate_hash
    )

    validation = json.loads(
        paths["validation"].read_text(
            encoding="utf-8"
        )
    )

    assert (
        validation["status"]
        == "published"
    )

    assert (
        validation[
            "publication_performed"
        ]
        is True
    )

    assert (
        validation[
            "legacy_parity_reviewed"
        ]
        is True
    )

    assert (
        validation[
            "provisional_comparison_reviewed"
        ]
        is True
    )


def test_publish_rejects_existing_destination(
    tmp_path: Path,
) -> None:
    paths = _write_evidence(
        tmp_path
    )

    published_path = (
        tmp_path / "coorte_final.parquet"
    )

    published_path.write_bytes(
        b"existente"
    )

    with pytest.raises(
        FileExistsError,
        match="Já existem",
    ):
        publish_final_cohort(
            candidate_path=paths[
                "candidate"
            ],
            published_path=published_path,
            candidate_manifest_path=paths[
                "candidate_manifest"
            ],
            candidate_validation_path=paths[
                "validation"
            ],
            parity_manifest_path=paths[
                "parity"
            ],
            transition_manifest_path=paths[
                "transition"
            ],
            publication_manifest_path=(
                tmp_path
                / "coorte_final.manifest.json"
            ),
        )


def test_publish_rejects_abandoned_temporary(
    tmp_path: Path,
) -> None:
    paths = _write_evidence(
        tmp_path
    )

    published_path = (
        tmp_path / "coorte_final.parquet"
    )

    temporary_path = (
        published_path.with_suffix(
            ".parquet.tmp"
        )
    )

    temporary_path.write_bytes(
        b"parcial"
    )

    with pytest.raises(
        FileExistsError,
        match="temporários",
    ):
        publish_final_cohort(
            candidate_path=paths[
                "candidate"
            ],
            published_path=published_path,
            candidate_manifest_path=paths[
                "candidate_manifest"
            ],
            candidate_validation_path=paths[
                "validation"
            ],
            parity_manifest_path=paths[
                "parity"
            ],
            transition_manifest_path=paths[
                "transition"
            ],
            publication_manifest_path=(
                tmp_path
                / "coorte_final.manifest.json"
            ),
        )