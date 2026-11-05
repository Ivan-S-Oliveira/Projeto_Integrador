"""Auditoria, contrato e fonte da coorte."""

from __future__ import annotations

import pandas as pd
import pytest
from src.dados import CohortAuditParameters, build_approved_exclusion_mask, build_rule_overlap, build_simulated_waterfall, evaluate_audit_rules, normalize_srag_code, parse_srag_date, summarize_audit_rules, validate_audit_schema
from copy import deepcopy
from pathlib import Path
import yaml
from src.dados import load_cohort_contract, parse_cohort_contract
from src.dados import CohortSource, cohort_candidates, load_cohort, resolve_cohort_path


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


def test_evaluation_does_not_modify_source(
    audit_frame: pd.DataFrame,
    parameters: CohortAuditParameters,
) -> None:
    original = audit_frame.copy(deep=True)

    evaluate_audit_rules(audit_frame, parameters)

    pd.testing.assert_frame_equal(audit_frame, original)


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


CONTRACT_PATH = Path("configs/final_cohort_v1.yaml")


@pytest.fixture
def valid_contract_raw() -> dict:
    with CONTRACT_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_contract_file_loads() -> None:
    contract = load_cohort_contract(CONTRACT_PATH)

    assert contract.contract_id == "final_cohort_v1"
    assert contract.version == 1
    assert contract.status == "approved"


def test_contract_uses_expected_target_mapping() -> None:
    contract = load_cohort_contract(CONTRACT_PATH)

    assert contract.target_mapping == {
        "1": 0,
        "2": 1,
    }
    assert contract.target_excluded_codes == ("3", "9")
    assert contract.target_exclude_missing is True


def test_exclusion_requires_decision_id(
    valid_contract_raw: dict,
) -> None:
    raw = deepcopy(valid_contract_raw)
    raw["audit"]["rules"]["hospital_nao_confirmado"][
        "decision_id"
    ] = None

    with pytest.raises(ValueError, match="exige decision_id"):
        parse_cohort_contract(raw)


_FINAL = "coorte_final.parquet"


@pytest.fixture(autouse=True)
def _limpar_variavel_de_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove ``SRAG_COHORT_KIND`` antes de cada teste.

    Sem isto, uma variável definida no shell do runner mudaria o default
    ``final`` e tornaria os testes dependentes do ambiente.
    """
    monkeypatch.delenv("SRAG_COHORT_KIND", raising=False)


def _criar(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"conteudo")
    return path


def _coorte_final(root: Path) -> Path:
    return _criar(root / "data" / "analytical" / _FINAL)


def test_default_resolve_a_coorte_final(tmp_path: Path) -> None:
    esperado = _coorte_final(tmp_path)

    kind, path = resolve_cohort_path(tmp_path)

    assert kind == "final"
    assert path == esperado.resolve()


def test_kind_provisional_e_rejeitado(tmp_path: Path) -> None:
    _coorte_final(tmp_path)

    with pytest.raises(ValueError, match="não é mais aceito"):
        resolve_cohort_path(tmp_path, kind="provisional")  # type: ignore[arg-type]


def test_explicit_path_com_nome_ambiguo_e_rejeitado(tmp_path: Path) -> None:
    caminho = _criar(tmp_path / "coorte.parquet")

    with pytest.raises(ValueError, match="não reconhecido"):
        resolve_cohort_path(tmp_path, explicit_path=caminho)


def test_load_cohort_devolve_dados_e_metadados(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    caminho = _coorte_final(tmp_path)
    quadro = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    chamadas: dict[str, object] = {}

    def _ler(path: object, columns: list[str] | None = None) -> pd.DataFrame:
        chamadas["path"] = Path(str(path))
        chamadas["columns"] = columns
        return quadro if columns is None else quadro[columns]

    monkeypatch.setattr(pd, "read_parquet", _ler)

    frame, fonte = load_cohort(tmp_path)

    assert isinstance(fonte, CohortSource)
    assert chamadas["path"] == caminho.resolve()
    assert chamadas["columns"] is None
    assert fonte.kind == "final"
    assert fonte.path == str(caminho.resolve())
    assert fonte.rows == 3
    assert fonte.columns == 2
    assert fonte.size_bytes == len(b"conteudo")
    assert len(fonte.sha256) == 64
    assert fonte.to_dict()["kind"] == "final"
    assert list(frame.columns) == ["a", "b"]
