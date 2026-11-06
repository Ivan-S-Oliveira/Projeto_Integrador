"""Construção da coorte final."""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest
from src.dados import load_cohort_contract
from src.dados import build_final_cohort_candidate


CONTRACT_PATH = Path(__file__).resolve().parents[1] / "configs" / "final_cohort_v1.yaml"


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
