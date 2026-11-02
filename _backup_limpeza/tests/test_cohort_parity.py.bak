from __future__ import annotations

import copy
from pathlib import Path

import pandas as pd
import pytest

from src.data.cohort_contract import load_cohort_contract
from src.data.cohort_parity import (
    CohortParityResult,
    _summarize,
    build_period_aligned_legacy_config,
    compare_parity_frames,
    write_parity_outputs,
)
from src.protocolo import verificacoes as legacy


CONTRACT_PATH = Path("configs/final_cohort_v1.yaml")


@pytest.fixture
def contract():
    return load_cohort_contract(CONTRACT_PATH)


@pytest.fixture
def historical_config() -> dict:
    config = legacy.load_config("configs/decisoes.yaml")
    config["min_date"] = "2019-01-01"
    config["dev_years"] = list(range(2019, 2027))
    config["holdout_years"] = []
    return config


def make_source() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id_registro": ["ok", "negativo", "longo"],
            "hospital": [1, 1, 1],
            "dt_interna": ["2024-01-10", "2024-01-10", "2024-04-01"],
            "dt_sin_pri": ["2024-01-05", "2024-01-11", "2024-01-01"],
            "evolucao": [1, 2, 2],
        }
    )


def make_candidate() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id_registro": ["ok"],
            "alvo_obito_srag": pd.Series([0], dtype="int8"),
        }
    )


def test_build_period_aligned_legacy_config(contract) -> None:
    historical = {"min_date": "2009-01-01", "dev_years": [2024], "holdout_years": [2025]}
    aligned = build_period_aligned_legacy_config(historical, contract)

    assert aligned["min_date"] == "2019-01-01"
    assert aligned["dev_years"] == list(range(2019, 2027))
    assert aligned["holdout_years"] == []
    assert historical["min_date"] == "2009-01-01"


def test_compare_explains_temporal_differences(
    contract,
    historical_config,
) -> None:
    source = make_source()
    candidate = make_candidate()
    source_before = source.copy(deep=True)
    candidate_before = candidate.copy(deep=True)

    row = compare_parity_frames(
        source_frame=source,
        candidate_frame=candidate,
        contract=contract,
        historical_config=historical_config,
        period_aligned_config=copy.deepcopy(historical_config),
        row_group=1,
    )

    assert row["only_legacy_rows"] == 2
    assert row["only_legacy_negative_interval"] == 1
    assert row["only_legacy_above_limit"] == 1
    assert row["only_legacy_unexplained"] == 0
    assert row["only_candidate_rows"] == 0
    assert row["target_mismatches"] == 0
    pd.testing.assert_frame_equal(source, source_before)
    pd.testing.assert_frame_equal(candidate, candidate_before)


def test_compare_detects_target_mismatch(
    contract,
    historical_config,
) -> None:
    source = make_source().iloc[[0]].copy()
    candidate = pd.DataFrame(
        {
            "id_registro": ["ok"],
            "alvo_obito_srag": pd.Series([1], dtype="int8"),
        }
    )

    row = compare_parity_frames(
        source_frame=source,
        candidate_frame=candidate,
        contract=contract,
        historical_config=historical_config,
        period_aligned_config=copy.deepcopy(historical_config),
        row_group=1,
    )

    assert row["target_mismatches"] == 1


def test_compare_detects_unexplained_candidate_record(
    contract,
    historical_config,
) -> None:
    source = make_source().iloc[[0]].copy()
    candidate = pd.DataFrame(
        {
            "id_registro": ["ok", "inexistente"],
            "alvo_obito_srag": pd.Series([0, 0], dtype="int8"),
        }
    )

    row = compare_parity_frames(
        source_frame=source,
        candidate_frame=candidate,
        contract=contract,
        historical_config=historical_config,
        period_aligned_config=copy.deepcopy(historical_config),
        row_group=1,
    )

    assert row["only_candidate_rows"] == 1
    assert row["only_candidate_unexplained"] == 1


def test_compare_rejects_duplicate_id(
    contract,
    historical_config,
) -> None:
    source = make_source()
    source.loc[1, "id_registro"] = "ok"

    with pytest.raises(ValueError, match="duplicado"):
        compare_parity_frames(
            source_frame=source,
            candidate_frame=make_candidate(),
            contract=contract,
            historical_config=historical_config,
            period_aligned_config=copy.deepcopy(historical_config),
            row_group=1,
        )


def test_summarize_closes_counts() -> None:
    details = pd.DataFrame(
        [
            {
                "row_group": 1,
                "source_rows": 3,
                "legacy_historical_rows": 3,
                "legacy_aligned_rows": 3,
                "candidate_rows": 1,
                "common_rows": 1,
                "only_legacy_rows": 2,
                "only_candidate_rows": 0,
                "only_legacy_negative_interval": 1,
                "only_legacy_above_limit": 1,
                "only_legacy_unexplained": 0,
                "only_candidate_unexplained": 0,
                "target_mismatches": 0,
            }
        ]
    )

    totals = _summarize(details)

    assert totals["legacy_aligned_rows"] == 3
    assert totals["candidate_rows"] == 1
    assert totals["only_legacy_rows"] == 2


def test_write_parity_outputs_protects_overwrite(tmp_path: Path) -> None:
    result = CohortParityResult(
        details=pd.DataFrame([{"row_group": 1}]),
        summary={"publication_gate_passed": True},
    )
    csv_path = tmp_path / "comparacao.csv"
    json_path = tmp_path / "paridade.json"

    write_parity_outputs(result, csv_path, json_path)

    assert csv_path.is_file()
    assert json_path.is_file()

    with pytest.raises(FileExistsError, match="Já existem"):
        write_parity_outputs(result, csv_path, json_path)
