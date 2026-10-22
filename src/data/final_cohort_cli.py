"""Interface operacional para a construção da coorte definitiva SRAG.

O modo ``audit`` avalia as regras populacionais sobre a fonte real sem
remover registros, gerar uma candidata ou publicar artefatos canônicos.

Os modos de geração da candidata e publicação serão adicionados depois
da revisão dos resultados desta auditoria.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import pandas as pd

from src.data.cohort_audit import (
    CohortAuditEvaluation,
    build_rule_overlap,
    build_simulated_waterfall,
    evaluate_audit_rules,
    summarize_audit_rules,
)
from src.data.cohort_contract import (
    CohortContract,
    load_cohort_contract,
)


ROOT_DIR = Path(__file__).resolve().parents[2]

DEFAULT_CONTRACT_PATH = (
    ROOT_DIR
    / "configs"
    / "final_cohort_v1.yaml"
)


def parse_arguments(
    arguments: Sequence[str] | None = None,
) -> argparse.Namespace:
    """Interpreta os argumentos da interface operacional."""

    parser = argparse.ArgumentParser(
        description=(
            "Audita e constrói a coorte definitiva do projeto SRAG."
        )
    )

    parser.add_argument(
        "--mode",
        choices=[
            "audit",
        ],
        required=True,
        help=(
            "Operação executada. Neste incremento, somente audit "
            "está disponível."
        ),
    )

    parser.add_argument(
        "--contract",
        type=Path,
        default=DEFAULT_CONTRACT_PATH,
        help="Caminho do contrato YAML da coorte.",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Permite substituir os artefatos anteriores "
            "da auditoria."
        ),
    )

    return parser.parse_args(arguments)


def resolve_project_path(path: Path) -> Path:
    """Resolve caminhos relativos a partir da raiz do projeto."""

    normalized_path = Path(path)

    if normalized_path.is_absolute():
        return normalized_path

    return ROOT_DIR / normalized_path


def validate_audit_outputs(
    output_paths: Sequence[Path],
    overwrite: bool,
) -> None:
    """Impede a substituição acidental de auditorias anteriores."""

    existing_paths = [
        path
        for path in output_paths
        if path.exists()
    ]

    if existing_paths and not overwrite:
        formatted_paths = "\n".join(
            f"- {path}"
            for path in existing_paths
        )

        raise FileExistsError(
            "Já existem artefatos da auditoria:\n"
            f"{formatted_paths}\n"
            "Use --overwrite somente após revisar "
            "a execução anterior."
        )


def build_rules_by_year(
    evaluation: CohortAuditEvaluation,
) -> pd.DataFrame:
    """Resume cada regra pelo ano da internação."""

    years = (
        evaluation.normalized[
            "dt_interna_parseada"
        ]
        .dt.year
        .astype("Int64")
        .astype("string")
        .fillna("SEM_ANO_VALIDO")
    )

    rows: list[dict[str, object]] = []

    for rule_id, mask in evaluation.masks.items():
        counts = (
            years.loc[mask]
            .value_counts(dropna=False)
            .sort_index()
        )

        for year, count in counts.items():
            rows.append(
                {
                    "ano_internacao": str(year),
                    "regra": rule_id,
                    "linhas_sinalizadas": int(count),
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "ano_internacao",
            "regra",
            "linhas_sinalizadas",
        ],
    )


def build_rules_by_outcome(
    evaluation: CohortAuditEvaluation,
) -> pd.DataFrame:
    """Resume cada regra pelo código normalizado de evolução."""

    outcome = (
        evaluation.normalized[
            "evolucao_normalizada"
        ]
        .fillna("AUSENTE")
    )

    rows: list[dict[str, object]] = []

    for rule_id, mask in evaluation.masks.items():
        counts = (
            outcome.loc[mask]
            .value_counts(dropna=False)
            .sort_index()
        )

        for value, count in counts.items():
            rows.append(
                {
                    "evolucao_normalizada": str(value),
                    "regra": rule_id,
                    "linhas_sinalizadas": int(count),
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "evolucao_normalizada",
            "regra",
            "linhas_sinalizadas",
        ],
    )


def resolve_audit_output_paths(
    contract: CohortContract,
) -> dict[str, Path]:
    """Resolve todos os caminhos produzidos pelo modo de auditoria."""

    output_directory = resolve_project_path(
        contract.outputs[
            "candidate_directory"
        ]
    )

    return {
        "output_directory": output_directory,
        "audit_summary": resolve_project_path(
            contract.outputs[
                "audit_summary"
            ]
        ),
        "simulated_waterfall": resolve_project_path(
            contract.outputs[
                "simulated_waterfall"
            ]
        ),
        "rule_overlap": (
            output_directory
            / "sobreposicao_regras.csv"
        ),
        "rules_by_year": (
            output_directory
            / "regras_por_ano.csv"
        ),
        "rules_by_outcome": (
            output_directory
            / "regras_por_evolucao.csv"
        ),
        "audit_manifest": (
            output_directory
            / "manifesto_auditoria.json"
        ),
    }


def write_audit_outputs(
    audit_summary: pd.DataFrame,
    simulated_waterfall: pd.DataFrame,
    rule_overlap: pd.DataFrame,
    rules_by_year: pd.DataFrame,
    rules_by_outcome: pd.DataFrame,
    output_paths: dict[str, Path],
) -> None:
    """Grava os relatórios tabulares produzidos pela auditoria."""

    for key, path in output_paths.items():
        if key == "output_directory":
            continue

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    audit_summary.to_csv(
        output_paths["audit_summary"],
        index=False,
        encoding="utf-8-sig",
    )

    simulated_waterfall.to_csv(
        output_paths["simulated_waterfall"],
        index=False,
        encoding="utf-8-sig",
    )

    rule_overlap.to_csv(
        output_paths["rule_overlap"],
        encoding="utf-8-sig",
    )

    rules_by_year.to_csv(
        output_paths["rules_by_year"],
        index=False,
        encoding="utf-8-sig",
    )

    rules_by_outcome.to_csv(
        output_paths["rules_by_outcome"],
        index=False,
        encoding="utf-8-sig",
    )


def build_audit_manifest(
    contract: CohortContract,
    contract_path: Path,
    source_path: Path,
    source: pd.DataFrame,
    columns_read: list[str],
    evaluation: CohortAuditEvaluation,
    output_paths: dict[str, Path],
) -> dict[str, object]:
    """Monta o manifesto da auditoria sem alterar a fonte."""

    approved_exclusion_counts = {
        rule_id: int(
            evaluation.masks[
                rule_id
            ].sum()
        )
        for rule_id
        in contract.approved_exclusion_rule_ids
    }

    audit_only_counts = {
        rule_id: int(
            evaluation.masks[
                rule_id
            ].sum()
        )
        for rule_id
        in contract.audit_only_rule_ids
    }

    return {
        "schema_version": 1,
        "kind": "final_cohort_pre_exclusion_audit",
        "generated_at_utc": (
            datetime.now(timezone.utc).isoformat()
        ),
        "contract": {
            "id": contract.contract_id,
            "version": contract.version,
            "status": contract.status,
            "path": str(contract_path),
        },
        "source": {
            "path": str(source_path),
            "rows": int(len(source)),
            "columns_read": columns_read,
        },
        "execution_guarantees": {
            "source_modified": False,
            "candidate_generated": False,
            "cohort_published": False,
            "exclusions_applied": False,
            "partitions_created": False,
            "test_consulted": False,
        },
        "approved_exclusion_counts": (
            approved_exclusion_counts
        ),
        "audit_only_counts": (
            audit_only_counts
        ),
        "outputs": {
            key: str(path)
            for key, path in output_paths.items()
            if key != "output_directory"
        },
        "environment": {
            "python": sys.version,
            "pandas": pd.__version__,
        },
    }


def execute_audit(
    contract: CohortContract,
    contract_path: Path,
    overwrite: bool,
) -> None:
    """Executa a auditoria real sem aplicar exclusões."""

    source_path = resolve_project_path(
        contract.source_path
    )

    if not source_path.is_file():
        raise FileNotFoundError(
            "A fonte declarada no contrato não foi encontrada: "
            f"{source_path}"
        )

    output_paths = resolve_audit_output_paths(
        contract
    )

    output_paths["output_directory"].mkdir(
        parents=True,
        exist_ok=True,
    )

    paths_to_validate = [
        path
        for key, path in output_paths.items()
        if key != "output_directory"
    ]

    validate_audit_outputs(
        output_paths=paths_to_validate,
        overwrite=overwrite,
    )

    columns_to_read = list(
        dict.fromkeys(
            contract.required_columns
        )
    )

    print(
        "Fonte:",
        source_path,
    )

    print(
        "Contrato:",
        contract_path,
    )

    print(
        "Colunas da auditoria:",
        columns_to_read,
    )

    source = pd.read_parquet(
        source_path,
        columns=columns_to_read,
    )

    if source.empty:
        raise ValueError(
            "A fonte foi carregada, mas não contém registros."
        )

    print(
        "Linhas carregadas:",
        len(source),
    )

    evaluation = evaluate_audit_rules(
        frame=source,
        parameters=contract.audit_parameters,
    )

    audit_summary = summarize_audit_rules(
        evaluation
    )

    rule_overlap = build_rule_overlap(
        evaluation=evaluation,
        rule_order=contract.rule_order,
    )

    simulated_waterfall = build_simulated_waterfall(
        evaluation=evaluation,
        rule_order=contract.rule_order,
    )

    rules_by_year = build_rules_by_year(
        evaluation
    )

    rules_by_outcome = build_rules_by_outcome(
        evaluation
    )

    write_audit_outputs(
        audit_summary=audit_summary,
        simulated_waterfall=simulated_waterfall,
        rule_overlap=rule_overlap,
        rules_by_year=rules_by_year,
        rules_by_outcome=rules_by_outcome,
        output_paths=output_paths,
    )

    manifest = build_audit_manifest(
        contract=contract,
        contract_path=contract_path,
        source_path=source_path,
        source=source,
        columns_read=columns_to_read,
        evaluation=evaluation,
        output_paths=output_paths,
    )

    output_paths[
        "audit_manifest"
    ].write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("Auditoria concluída.")

    print(
        "Regras aprovadas para exclusão:",
        manifest[
            "approved_exclusion_counts"
        ],
    )

    print(
        "Regras pendentes de decisão:",
        manifest[
            "audit_only_counts"
        ],
    )

    print(
        "Diretório dos resultados:",
        output_paths[
            "output_directory"
        ],
    )

    print("Nenhuma exclusão foi aplicada.")
    print("Nenhuma candidata foi gerada.")
    print("Nenhuma coorte foi publicada.")


def main(
    arguments: Sequence[str] | None = None,
) -> int:
    """Executa a operação solicitada."""

    parsed_arguments = parse_arguments(
        arguments
    )

    contract_path = resolve_project_path(
        parsed_arguments.contract
    )

    contract = load_cohort_contract(
        contract_path
    )

    if parsed_arguments.mode == "audit":
        execute_audit(
            contract=contract,
            contract_path=contract_path,
            overwrite=parsed_arguments.overwrite,
        )

        return 0

    raise RuntimeError(
        "Modo não implementado: "
        f"{parsed_arguments.mode!r}"
    )


if __name__ == "__main__":
    raise SystemExit(main())