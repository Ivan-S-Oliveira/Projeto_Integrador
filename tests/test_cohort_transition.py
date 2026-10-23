from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.data.cohort_transition import (
    CohortTransitionResult,
    compare_population_and_target,
    write_transition_outputs,
)


def test_population_transition_is_exact_subset() -> None:
    result = compare_population_and_target(
        provisional_ids=np.array(
            [1, 2, 3],
            dtype="int64",
        ),
        provisional_target=np.array(
            [0, 1, 1],
            dtype="int8",
        ),
        candidate_ids=np.array(
            [1, 3],
            dtype="int64",
        ),
        candidate_target=np.array(
            [0, 1],
            dtype="int8",
        ),
    )

    assert result == {
        "only_provisional_rows": 1,
        "only_candidate_rows": 0,
        "common_rows": 2,
        "target_mismatches": 0,
    }


def test_population_transition_detects_new_record() -> None:
    result = compare_population_and_target(
        provisional_ids=np.array(
            [1],
            dtype="int64",
        ),
        provisional_target=np.array(
            [0],
            dtype="int8",
        ),
        candidate_ids=np.array(
            [1, 2],
            dtype="int64",
        ),
        candidate_target=np.array(
            [0, 1],
            dtype="int8",
        ),
    )

    assert (
        result["only_candidate_rows"]
        == 1
    )


def test_population_transition_detects_target_mismatch() -> None:
    result = compare_population_and_target(
        provisional_ids=np.array(
            [1],
            dtype="int64",
        ),
        provisional_target=np.array(
            [0],
            dtype="int8",
        ),
        candidate_ids=np.array(
            [1],
            dtype="int64",
        ),
        candidate_target=np.array(
            [1],
            dtype="int8",
        ),
    )

    assert (
        result["target_mismatches"]
        == 1
    )


def test_write_transition_outputs_protects_overwrite(
    tmp_path: Path,
) -> None:
    result = CohortTransitionResult(
        annual_comparison=pd.DataFrame(
            [
                {
                    "ano_internacao": 2024,
                    "diferenca_registros": -1,
                }
            ]
        ),
        summary={
            "transition_gate_passed": True,
        },
    )

    annual_path = (
        tmp_path / "comparacao.csv"
    )

    manifest_path = (
        tmp_path / "transicao.json"
    )

    write_transition_outputs(
        result,
        annual_path,
        manifest_path,
    )

    assert annual_path.is_file()
    assert manifest_path.is_file()

    with pytest.raises(
        FileExistsError,
        match="Já existem",
    ):
        write_transition_outputs(
            result,
            annual_path,
            manifest_path,
        )