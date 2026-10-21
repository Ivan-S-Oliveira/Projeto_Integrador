from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from src.data.cohort_contract import (
    load_cohort_contract,
    parse_cohort_contract,
)


CONTRACT_PATH = Path("configs/final_cohort_v1.yaml")


@pytest.fixture
def valid_contract_raw() -> dict:
    with CONTRACT_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_contract_file_loads() -> None:
    contract = load_cohort_contract(CONTRACT_PATH)

    assert contract.contract_id == "final_cohort_v1"
    assert contract.version == 1
    assert contract.status == "candidate"


def test_contract_exposes_approved_exclusions() -> None:
    contract = load_cohort_contract(CONTRACT_PATH)

    assert contract.approved_exclusion_rule_ids == (
        "hospital_nao_confirmado",
        "dt_interna_invalida",
        "evolucao_fora_alvo_principal",
        "dt_interna_antes_periodo",
        "dt_interna_apos_periodo",
    )


def test_contract_keeps_temporal_anomalies_as_audit_only() -> None:
    contract = load_cohort_contract(CONTRACT_PATH)

    assert contract.audit_only_rule_ids == (
        "intervalo_sintomas_negativo",
        "intervalo_sintomas_maior_limite",
    )


def test_contract_uses_expected_target_mapping() -> None:
    contract = load_cohort_contract(CONTRACT_PATH)

    assert contract.target_mapping == {
        "1": 0,
        "2": 1,
    }
    assert contract.target_excluded_codes == ("3", "9")
    assert contract.target_exclude_missing is True


def test_contract_uses_canonical_source() -> None:
    contract = load_cohort_contract(CONTRACT_PATH)

    assert contract.source_path == Path(
        "data/processed/dados-v2/srag.parquet"
    )


def test_missing_contract_file_fails(tmp_path: Path) -> None:
    missing = tmp_path / "inexistente.yaml"

    with pytest.raises(
        FileNotFoundError,
        match="Contrato de coorte nao encontrado",
    ):
        load_cohort_contract(missing)


def test_invalid_rule_action_fails(
    valid_contract_raw: dict,
) -> None:
    raw = deepcopy(valid_contract_raw)
    raw["audit"]["rules"]["hospital_nao_confirmado"][
        "action"
    ] = "acao_inexistente"

    with pytest.raises(ValueError, match="Acao invalida"):
        parse_cohort_contract(raw)


def test_exclusion_requires_decision_id(
    valid_contract_raw: dict,
) -> None:
    raw = deepcopy(valid_contract_raw)
    raw["audit"]["rules"]["hospital_nao_confirmado"][
        "decision_id"
    ] = None

    with pytest.raises(ValueError, match="exige decision_id"):
        parse_cohort_contract(raw)


def test_rule_order_rejects_unknown_rule(
    valid_contract_raw: dict,
) -> None:
    raw = deepcopy(valid_contract_raw)
    raw["audit"]["rule_order"].append("regra_inexistente")

    with pytest.raises(
        ValueError,
        match="rule_order diverge",
    ):
        parse_cohort_contract(raw)


def test_required_columns_cannot_omit_target(
    valid_contract_raw: dict,
) -> None:
    raw = deepcopy(valid_contract_raw)
    raw["required_columns"].remove("evolucao")

    with pytest.raises(
        ValueError,
        match="required_columns nao inclui",
    ):
        parse_cohort_contract(raw)


def test_target_codes_cannot_be_mapped_and_excluded(
    valid_contract_raw: dict,
) -> None:
    raw = deepcopy(valid_contract_raw)
    raw["target"]["excluded_codes"].append("1")

    with pytest.raises(
        ValueError,
        match="simultaneamente",
    ):
        parse_cohort_contract(raw)


def test_inverted_period_fails(
    valid_contract_raw: dict,
) -> None:
    raw = deepcopy(valid_contract_raw)
    raw["period"]["start"] = "2026-12-31"
    raw["period"]["end"] = "2019-01-01"

    with pytest.raises(
        ValueError,
        match="period_start nao pode ser posterior",
    ):
        parse_cohort_contract(raw)