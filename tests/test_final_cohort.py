from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.data.cohort_contract import (
    load_cohort_contract,
)
from src.data.final_cohort import (
    build_final_cohort_candidate,
)


CONTRACT_PATH = Path(
    "configs/final_cohort_v1.yaml"
)


@pytest.fixture
def contract():
    return load_cohort_contract(
        CONTRACT_PATH
    )


@pytest.fixture
def source_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "hospital": [
                1,
                1,
                2,
                1,
                1,
                1,
                1,
                1,
                1,
            ],
            "dt_interna": [
                "2019-01-10",
                "2023-06-15",
                "2024-05-10",
                None,
                "2018-12-31",
                "2027-01-01",
                "2025-08-01",
                "2025-09-01",
                "2025-10-01",
            ],
            "dt_sin_pri": [
                "2019-01-05",
                "2023-06-20",
                "2024-05-01",
                "2025-01-01",
                "2018-12-20",
                "2026-12-20",
                "2025-05-01",
                "2025-08-20",
                "2025-09-20",
            ],
            "evolucao": [
                1,
                2,
                1,
                1,
                1,
                1,
                2,
                9,
                None,
            ],
            "coluna_auxiliar": [
                "a",
                "b",
                "c",
                "d",
                "e",
                "f",
                "g",
                "h",
                "i",
            ],
        },
        index=[
            100,
            101,
            102,
            103,
            104,
            105,
            106,
            107,
            108,
        ],
    )


def test_candidate_does_not_modify_source(
    source_frame: pd.DataFrame,
    contract,
) -> None:
    original = source_frame.copy(deep=True)

    build_final_cohort_candidate(
        frame=source_frame,
        contract=contract,
    )

    pd.testing.assert_frame_equal(
        source_frame,
        original,
    )

def test_candidate_applies_all_approved_exclusions(
    source_frame: pd.DataFrame,
    contract,
) -> None:
    result = build_final_cohort_candidate(
        frame=source_frame,
        contract=contract,
    )

    assert result.frame.index.tolist() == [
        100,
    ]


def test_negative_interval_is_excluded(
    source_frame: pd.DataFrame,
    contract,
) -> None:
    result = build_final_cohort_candidate(
        frame=source_frame,
        contract=contract,
    )

    assert bool(
        result.audit_evaluation.masks[
            "intervalo_sintomas_negativo"
        ].loc[101]
    )

    assert 101 not in result.frame.index
    assert bool(result.excluded_mask.loc[101])


def test_long_interval_is_excluded(
    source_frame: pd.DataFrame,
    contract,
) -> None:
    result = build_final_cohort_candidate(
        frame=source_frame,
        contract=contract,
    )

    assert bool(
        result.audit_evaluation.masks[
            "intervalo_sintomas_maior_limite"
        ].loc[106]
    )

    assert 106 not in result.frame.index
    assert bool(result.excluded_mask.loc[106])


def test_candidate_creates_binary_target(
    source_frame: pd.DataFrame,
    contract,
) -> None:
    result = build_final_cohort_candidate(
        frame=source_frame,
        contract=contract,
    )

    target = result.frame[
        contract.target_output_column
    ]

    assert target.to_dict() == {
        100: 0,
    }

    assert str(target.dtype) == "int8"
    assert target.isna().sum() == 0
    assert set(target.unique()) <= {0, 1}


def test_candidate_preserves_auxiliary_columns(
    source_frame: pd.DataFrame,
    contract,
) -> None:
    result = build_final_cohort_candidate(
        frame=source_frame,
        contract=contract,
    )

    assert "coluna_auxiliar" in result.frame.columns

    assert result.frame[
        "coluna_auxiliar"
    ].tolist() == [
        "a",
    ]


def test_candidate_counts_close(
    source_frame: pd.DataFrame,
    contract,
) -> None:
    result = build_final_cohort_candidate(
        frame=source_frame,
        contract=contract,
    )

    assert result.total_source_rows == 9
    assert result.total_excluded_rows == 8
    assert result.total_candidate_rows == 1

    assert (
        result.total_source_rows
        == result.total_excluded_rows
        + result.total_candidate_rows
    )

    assert int(result.excluded_mask.sum()) == 8


def test_effective_waterfall_uses_all_approved_rules(
    source_frame: pd.DataFrame,
    contract,
) -> None:
    result = build_final_cohort_candidate(
        frame=source_frame,
        contract=contract,
    )

    observed_rules = tuple(
        result.effective_waterfall[
            "regra"
        ].tolist()
    )

    assert observed_rules == (
        contract.approved_exclusion_rule_ids
    )

    assert observed_rules == contract.rule_order

    assert (
        "intervalo_sintomas_negativo"
        in observed_rules
    )

    assert (
        "intervalo_sintomas_maior_limite"
        in observed_rules
    )


def test_effective_and_simulated_waterfalls_match(
    source_frame: pd.DataFrame,
    contract,
) -> None:
    result = build_final_cohort_candidate(
        frame=source_frame,
        contract=contract,
    )

    assert tuple(
        result.simulated_waterfall[
            "regra"
        ].tolist()
    ) == contract.rule_order

    assert tuple(
        result.effective_waterfall[
            "regra"
        ].tolist()
    ) == contract.rule_order

    pd.testing.assert_frame_equal(
        result.effective_waterfall.reset_index(drop=True),
        result.simulated_waterfall.reset_index(drop=True),
    )


def test_candidate_rejects_missing_required_column(
    source_frame: pd.DataFrame,
    contract,
) -> None:
    invalid = source_frame.drop(
        columns=["hospital"]
    )

    with pytest.raises(
        ValueError,
        match="colunas exigidas",
    ):
        build_final_cohort_candidate(
            frame=invalid,
            contract=contract,
        )


def test_candidate_rejects_existing_target_column(
    source_frame: pd.DataFrame,
    contract,
) -> None:
    invalid = source_frame.copy()
    invalid[
        contract.target_output_column
    ] = 0

    with pytest.raises(
        ValueError,
        match="já existe na fonte",
    ):
        build_final_cohort_candidate(
            frame=invalid,
            contract=contract,
        )


def test_candidate_rejects_empty_source(
    contract,
) -> None:
    empty = pd.DataFrame(
        columns=[
            "hospital",
            "dt_interna",
            "dt_sin_pri",
            "evolucao",
        ]
    )

    with pytest.raises(
        ValueError,
        match="não pode estar vazia",
    ):
        build_final_cohort_candidate(
            frame=empty,
            contract=contract,
        )


def test_candidate_rejects_duplicate_index(
    source_frame: pd.DataFrame,
    contract,
) -> None:
    invalid = source_frame.copy()
    invalid.index = [
        100,
        100,
        102,
        103,
        104,
        105,
        106,
        107,
        108,
    ]

    with pytest.raises(
        ValueError,
        match="índice da fonte precisa ser único",
    ):
        build_final_cohort_candidate(
            frame=invalid,
            contract=contract,
        )