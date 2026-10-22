from __future__ import annotations

import pandas as pd
import pytest

from src.data.cohort_audit import (
    CohortAuditParameters,
    build_approved_exclusion_mask,
    build_rule_overlap,
    build_simulated_waterfall,
    evaluate_audit_rules,
    normalize_srag_code,
    parse_srag_date,
    summarize_audit_rules,
    validate_audit_schema,
)


@pytest.fixture
def parameters() -> CohortAuditParameters:
    return CohortAuditParameters(
        period_start=pd.Timestamp("2019-01-01"),
        period_end=pd.Timestamp("2026-12-31"),
        max_symptom_to_admission_days=60,
    )


@pytest.fixture
def audit_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "hospital": [1, "1", 2, None, 1, 1, 1, 1],
            "dt_interna": [
                "2019-01-10",
                "2023-06-15",
                "2024-05-10",
                "2025-03-01",
                None,
                "2018-12-31",
                "2027-01-01",
                "2025-08-01",
            ],
            "dt_sin_pri": [
                "2019-01-05",
                "2023-06-20",
                "2024-02-01",
                "2025-02-25",
                "2025-01-01",
                "2018-12-20",
                "2026-12-20",
                "2025-07-20",
            ],
            "evolucao": [1, 2, 1, 2, 1, 1, 9, None],
        }
    )


def test_parameters_reject_inverted_period() -> None:
    with pytest.raises(
        ValueError,
        match="period_start nao pode ser posterior",
    ):
        CohortAuditParameters(
            period_start=pd.Timestamp("2026-12-31"),
            period_end=pd.Timestamp("2019-01-01"),
            max_symptom_to_admission_days=60,
        )


def test_parameters_reject_negative_interval_limit() -> None:
    with pytest.raises(
        ValueError,
        match="nao pode ser negativo",
    ):
        CohortAuditParameters(
            period_start=pd.Timestamp("2019-01-01"),
            period_end=pd.Timestamp("2026-12-31"),
            max_symptom_to_admission_days=-1,
        )


def test_schema_validation_rejects_missing_columns() -> None:
    frame = pd.DataFrame({"hospital": [1]})

    with pytest.raises(
        ValueError,
        match="Colunas obrigatorias ausentes",
    ):
        validate_audit_schema(frame)


def test_normalization_preserves_distinct_codes() -> None:
    series = pd.Series([1, 2, 9, None, "", " 1 ", "2.0"])

    result = normalize_srag_code(series)

    assert result.iloc[0] == "1"
    assert result.iloc[1] == "2"
    assert result.iloc[2] == "9"
    assert pd.isna(result.iloc[3])
    assert pd.isna(result.iloc[4])
    assert result.iloc[5] == "1"
    assert result.iloc[6] == "2"

def test_parse_srag_date_accepts_iso_dates() -> None:
    source = pd.Series(
        [
            "2019-01-01",
            "2026-12-31",
            " 2024-02-29 ",
        ],
        dtype="string",
    )

    result = parse_srag_date(source)

    expected = pd.Series(
        pd.to_datetime(
            [
                "2019-01-01",
                "2026-12-31",
                "2024-02-29",
            ]
        )
    )

    pd.testing.assert_series_equal(
        result.reset_index(drop=True),
        expected,
        check_names=False,
    )


def test_parse_srag_date_converts_missing_values_to_nat() -> None:
    source = pd.Series(
        [
            None,
            pd.NA,
            "",
            "   ",
            "nan",
            "NaN",
            "None",
            "<NA>",
        ],
        dtype="string",
    )

    result = parse_srag_date(source)

    assert result.isna().all()


def test_parse_srag_date_rejects_non_iso_values() -> None:
    source = pd.Series(
        [
            "31/12/2024",
            "2024/12/31",
            "2024-02-30",
            "texto",
            "05/03/2022 00:00",
        ],
        dtype="string",
    )

    result = parse_srag_date(source)

    assert result.isna().all()


def test_parse_srag_date_preserves_datetime_series() -> None:
    source = pd.Series(
        pd.to_datetime(
            [
                "2019-01-01",
                "2026-12-31",
                None,
            ]
        )
    )

    result = parse_srag_date(source)

    expected = pd.to_datetime(source, errors="coerce")

    pd.testing.assert_series_equal(
        result,
        expected,
    )

def test_evaluation_does_not_modify_source(
    audit_frame: pd.DataFrame,
    parameters: CohortAuditParameters,
) -> None:
    original = audit_frame.copy(deep=True)

    evaluate_audit_rules(audit_frame, parameters)

    pd.testing.assert_frame_equal(audit_frame, original)


def test_evaluation_flags_expected_rules(
    audit_frame: pd.DataFrame,
    parameters: CohortAuditParameters,
) -> None:
    result = evaluate_audit_rules(audit_frame, parameters)

    assert int(result.masks["hospital_nao_confirmado"].sum()) == 2
    assert int(result.masks["dt_interna_invalida"].sum()) == 1
    assert int(result.masks["evolucao_fora_alvo_principal"].sum()) == 2
    assert int(result.masks["dt_interna_antes_periodo"].sum()) == 1
    assert int(result.masks["dt_interna_apos_periodo"].sum()) == 1
    assert int(result.masks["intervalo_sintomas_negativo"].sum()) == 1
    assert int(result.masks["intervalo_sintomas_maior_limite"].sum()) == 1


def test_rule_summary_reports_source_denominator(
    audit_frame: pd.DataFrame,
    parameters: CohortAuditParameters,
) -> None:
    evaluation = evaluate_audit_rules(audit_frame, parameters)
    summary = summarize_audit_rules(evaluation)

    assert set(summary["total_linhas"]) == {8}
    assert len(summary) == 7


def test_overlap_matrix_is_symmetric(
    audit_frame: pd.DataFrame,
    parameters: CohortAuditParameters,
) -> None:
    evaluation = evaluate_audit_rules(audit_frame, parameters)
    overlap = build_rule_overlap(evaluation)

    transposed = overlap.T.rename_axis(
        index=overlap.index.name,
        columns=overlap.columns.name,
    )

    pd.testing.assert_frame_equal(overlap, transposed)


def test_waterfall_never_increases_remaining_rows(
    audit_frame: pd.DataFrame,
    parameters: CohortAuditParameters,
) -> None:
    evaluation = evaluate_audit_rules(audit_frame, parameters)
    waterfall = build_simulated_waterfall(evaluation)

    remaining = waterfall["restantes_apos_etapa"]

    assert remaining.is_monotonic_decreasing
    assert int(remaining.iloc[0]) <= len(audit_frame)
    assert int(remaining.iloc[-1]) >= 0


def test_approved_mask_uses_only_requested_rules(
    audit_frame: pd.DataFrame,
    parameters: CohortAuditParameters,
) -> None:
    evaluation = evaluate_audit_rules(audit_frame, parameters)

    mask = build_approved_exclusion_mask(
        evaluation,
        approved_rule_ids=[
            "hospital_nao_confirmado",
            "dt_interna_invalida",
        ],
    )

    expected = (
        evaluation.masks["hospital_nao_confirmado"]
        | evaluation.masks["dt_interna_invalida"]
    )

    pd.testing.assert_series_equal(mask, expected)


def test_approved_mask_rejects_unknown_rule(
    audit_frame: pd.DataFrame,
    parameters: CohortAuditParameters,
) -> None:
    evaluation = evaluate_audit_rules(audit_frame, parameters)

    with pytest.raises(
        ValueError,
        match="Regras aprovadas desconhecidas",
    ):
        build_approved_exclusion_mask(
            evaluation,
            approved_rule_ids=["regra_inexistente"],
        )


def test_approved_mask_rejects_duplicate_rule(
    audit_frame: pd.DataFrame,
    parameters: CohortAuditParameters,
) -> None:
    evaluation = evaluate_audit_rules(audit_frame, parameters)

    with pytest.raises(
        ValueError,
        match="nao pode conter regras duplicadas",
    ):
        build_approved_exclusion_mask(
            evaluation,
            approved_rule_ids=[
                "hospital_nao_confirmado",
                "hospital_nao_confirmado",
            ],
        )