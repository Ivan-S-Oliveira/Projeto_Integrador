from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from src.data.cohort_contract import (
    load_cohort_contract,
)
from src.data.final_cohort_cli import (
    build_audit_manifest,
    build_rules_by_outcome,
    build_rules_by_year,
    resolve_project_path,
    validate_audit_outputs,
)
from src.data.cohort_audit import (
    evaluate_audit_rules,
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
def audit_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "hospital": [
                1,
                1,
                2,
                1,
            ],
            "dt_interna": [
                "2019-01-10",
                "2023-06-15",
                "2024-05-10",
                None,
            ],
            "dt_sin_pri": [
                "2019-01-05",
                "2023-06-20",
                "2024-02-01",
                "2025-01-01",
            ],
            "evolucao": [
                1,
                2,
                9,
                None,
            ],
        },
        index=[
            100,
            101,
            102,
            103,
        ],
    )


def test_cli_exposes_audit_mode() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.data.final_cohort_cli",
            "--help",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--mode" in result.stdout
    assert "audit" in result.stdout


def test_resolve_project_path_preserves_absolute_path(
    tmp_path: Path,
) -> None:
    absolute_path = (
        tmp_path
        / "arquivo.parquet"
    )

    result = resolve_project_path(
        absolute_path
    )

    assert result == absolute_path


def test_resolve_project_path_resolves_relative_path() -> None:
    result = resolve_project_path(
        Path("configs/final_cohort_v1.yaml")
    )

    assert result.is_absolute()
    assert result.name == "final_cohort_v1.yaml"
    assert result.parent.name == "configs"


def test_existing_outputs_require_overwrite(
    tmp_path: Path,
) -> None:
    existing_path = (
        tmp_path
        / "resumo.csv"
    )

    existing_path.write_text(
        "conteudo",
        encoding="utf-8",
    )

    with pytest.raises(
        FileExistsError,
        match="Já existem artefatos",
    ):
        validate_audit_outputs(
            output_paths=[
                existing_path,
            ],
            overwrite=False,
        )


def test_existing_outputs_allow_explicit_overwrite(
    tmp_path: Path,
) -> None:
    existing_path = (
        tmp_path
        / "resumo.csv"
    )

    existing_path.write_text(
        "conteudo",
        encoding="utf-8",
    )

    validate_audit_outputs(
        output_paths=[
            existing_path,
        ],
        overwrite=True,
    )


def test_rules_by_year_preserves_invalid_date_group(
    audit_frame: pd.DataFrame,
    contract,
) -> None:
    evaluation = evaluate_audit_rules(
        frame=audit_frame,
        parameters=contract.audit_parameters,
    )

    result = build_rules_by_year(
        evaluation
    )

    invalid_date_rows = result.loc[
        result["ano_internacao"].eq(
            "SEM_ANO_VALIDO"
        )
    ]

    assert not invalid_date_rows.empty

    assert (
        "dt_interna_invalida"
        in set(
            invalid_date_rows[
                "regra"
            ]
        )
    )


def test_rules_by_outcome_preserves_missing_group(
    audit_frame: pd.DataFrame,
    contract,
) -> None:
    evaluation = evaluate_audit_rules(
        frame=audit_frame,
        parameters=contract.audit_parameters,
    )

    result = build_rules_by_outcome(
        evaluation
    )

    missing_rows = result.loc[
        result[
            "evolucao_normalizada"
        ].eq("AUSENTE")
    ]

    assert not missing_rows.empty

    assert (
        "evolucao_fora_alvo_principal"
        in set(
            missing_rows[
                "regra"
            ]
        )
    )


def test_manifest_declares_no_exclusion_or_publication(
    audit_frame: pd.DataFrame,
    contract,
    tmp_path: Path,
) -> None:
    evaluation = evaluate_audit_rules(
        frame=audit_frame,
        parameters=contract.audit_parameters,
    )

    output_paths = {
        "output_directory": tmp_path,
        "audit_summary": (
            tmp_path
            / "resumo_regras.csv"
        ),
        "simulated_waterfall": (
            tmp_path
            / "waterfall_simulado.csv"
        ),
        "rule_overlap": (
            tmp_path
            / "sobreposicao_regras.csv"
        ),
        "rules_by_year": (
            tmp_path
            / "regras_por_ano.csv"
        ),
        "rules_by_outcome": (
            tmp_path
            / "regras_por_evolucao.csv"
        ),
        "audit_manifest": (
            tmp_path
            / "manifesto_auditoria.json"
        ),
    }

    manifest = build_audit_manifest(
        contract=contract,
        contract_path=CONTRACT_PATH,
        source_path=(
            tmp_path
            / "fonte.parquet"
        ),
        source=audit_frame,
        columns_read=list(
            contract.required_columns
        ),
        evaluation=evaluation,
        output_paths=output_paths,
    )

    guarantees = manifest[
        "execution_guarantees"
    ]

    assert guarantees[
        "source_modified"
    ] is False

    assert guarantees[
        "candidate_generated"
    ] is False

    assert guarantees[
        "cohort_published"
    ] is False

    assert guarantees[
        "exclusions_applied"
    ] is False

    assert guarantees[
        "partitions_created"
    ] is False

    assert guarantees[
        "test_consulted"
    ] is False


def test_manifest_is_json_serializable(
    audit_frame: pd.DataFrame,
    contract,
    tmp_path: Path,
) -> None:
    evaluation = evaluate_audit_rules(
        frame=audit_frame,
        parameters=contract.audit_parameters,
    )

    output_paths = {
        "output_directory": tmp_path,
        "audit_summary": (
            tmp_path
            / "resumo_regras.csv"
        ),
        "simulated_waterfall": (
            tmp_path
            / "waterfall_simulado.csv"
        ),
        "rule_overlap": (
            tmp_path
            / "sobreposicao_regras.csv"
        ),
        "rules_by_year": (
            tmp_path
            / "regras_por_ano.csv"
        ),
        "rules_by_outcome": (
            tmp_path
            / "regras_por_evolucao.csv"
        ),
        "audit_manifest": (
            tmp_path
            / "manifesto_auditoria.json"
        ),
    }

    manifest = build_audit_manifest(
        contract=contract,
        contract_path=CONTRACT_PATH,
        source_path=(
            tmp_path
            / "fonte.parquet"
        ),
        source=audit_frame,
        columns_read=list(
            contract.required_columns
        ),
        evaluation=evaluation,
        output_paths=output_paths,
    )

    serialized = json.dumps(
        manifest,
        ensure_ascii=False,
    )

    assert (
        "final_cohort_pre_exclusion_audit"
        in serialized
    )