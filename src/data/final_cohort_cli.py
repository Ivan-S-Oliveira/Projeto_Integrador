"""Interface operacional para a construção da coorte definitiva SRAG.

O modo ``audit`` avalia as regras populacionais sobre a fonte real sem
remover registros, gerar uma candidata ou publicar artefatos canônicos.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

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
from src.data.final_cohort import (
    build_final_cohort_candidate,
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
            "candidate",
        ],
        required=True,
        help=(
            "Operação executada: audit avalia as regras e candidate "
            "materializa a candidata sem publicar a coorte."
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


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Calcula o SHA-256 sem carregar o arquivo inteiro em memória."""

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


def resolve_candidate_output_paths(
    contract: CohortContract,
) -> dict[str, Path]:
    """Resolve os arquivos produzidos pelo modo candidate."""

    candidate_path = resolve_project_path(
        contract.outputs["candidate_parquet"]
    )

    return {
        "candidate_parquet": candidate_path,
        "effective_waterfall": resolve_project_path(
            contract.outputs["effective_waterfall"]
        ),
        "manifest": resolve_project_path(
            contract.outputs["manifest"]
        ),
        "publication_validation": resolve_project_path(
            contract.outputs["publication_validation"]
        ),
        "temporary_candidate": candidate_path.with_suffix(
            candidate_path.suffix + ".tmp"
        ),
    }


def validate_candidate_preconditions(
    contract: CohortContract,
    output_paths: dict[str, Path],
    overwrite: bool,
) -> None:
    """Recusa decisões pendentes, saídas existentes e temporários abandonados."""

    if contract.audit_only_rule_ids:
        raise ValueError(
            "A candidata não pode ser gerada enquanto existirem "
            "regras audit_only: "
            f"{contract.audit_only_rule_ids}."
        )

    temporary_path = output_paths["temporary_candidate"]

    if temporary_path.exists():
        raise FileExistsError(
            "Existe um arquivo temporário de execução anterior: "
            f"{temporary_path}. Revise e remova o arquivo antes de continuar."
        )

    final_paths = [
        output_paths["candidate_parquet"],
        output_paths["effective_waterfall"],
        output_paths["manifest"],
        output_paths["publication_validation"],
    ]
    existing_paths = [path for path in final_paths if path.exists()]

    if existing_paths and not overwrite:
        formatted = "\n".join(f"- {path}" for path in existing_paths)
        raise FileExistsError(
            "Já existem artefatos da candidata:\n"
            f"{formatted}\n"
            "Use --overwrite somente após revisar a execução anterior."
        )


def build_global_effective_waterfall(
    rule_order: Sequence[str],
    excluded_by_rule: dict[str, int],
    total_source_rows: int,
) -> pd.DataFrame:
    """Consolida o waterfall efetivo acumulado entre os row groups."""

    remaining = total_source_rows
    rows: list[dict[str, object]] = []

    for order, rule_id in enumerate(rule_order, start=1):
        excluded = int(excluded_by_rule[rule_id])
        remaining -= excluded
        rows.append(
            {
                "ordem": order,
                "regra": rule_id,
                "excluidas_na_etapa": excluded,
                "restantes_apos_etapa": remaining,
            }
        )

    return pd.DataFrame(rows)


def validate_temporary_candidate(
    path: Path,
    contract: CohortContract,
    expected_rows: int,
    expected_columns: int,
) -> dict[str, object]:
    """Valida a candidata temporária antes da promoção do arquivo."""

    parquet_file = pq.ParquetFile(path)
    metadata = parquet_file.metadata

    if metadata.num_rows != expected_rows:
        raise ValueError(
            "A contagem física da candidata diverge da execução: "
            f"esperado={expected_rows}, observado={metadata.num_rows}."
        )

    if metadata.num_columns != expected_columns:
        raise ValueError(
            "A quantidade de colunas da candidata diverge do esperado: "
            f"esperado={expected_columns}, observado={metadata.num_columns}."
        )

    required_validation_columns = [
        "id_registro",
        "hospital",
        "dt_interna",
        "dt_sin_pri",
        "evolucao",
        contract.target_output_column,
    ]
    available_columns = set(parquet_file.schema_arrow.names)
    missing_columns = sorted(
        set(required_validation_columns) - available_columns
    )

    if missing_columns:
        raise ValueError(
            "A candidata não contém colunas obrigatórias para validação: "
            f"{missing_columns}."
        )

    table = pq.read_table(
        path,
        columns=required_validation_columns,
    )
    frame = table.to_pandas(types_mapper=pd.ArrowDtype)

    if frame["id_registro"].isna().any():
        raise ValueError("A candidata contém id_registro ausente.")

    distinct_ids = int(
        pc.count_distinct(table["id_registro"]).as_py()
    )

    if distinct_ids != expected_rows:
        raise ValueError(
            "A candidata contém id_registro duplicado: "
            f"linhas={expected_rows}, distintos={distinct_ids}."
        )

    evaluation = evaluate_audit_rules(
        frame=frame,
        parameters=contract.audit_parameters,
    )
    surviving_violations = {
        rule_id: int(evaluation.masks[rule_id].sum())
        for rule_id in contract.approved_exclusion_rule_ids
    }

    if any(surviving_violations.values()):
        raise ValueError(
            "A candidata temporária ainda contém violações aprovadas: "
            f"{surviving_violations}."
        )

    target = frame[contract.target_output_column]

    if target.isna().any():
        raise ValueError("O alvo da candidata contém valores ausentes.")

    observed_target = set(
        pd.to_numeric(target, errors="coerce")
        .dropna()
        .astype("int8")
        .unique()
        .tolist()
    )

    if not observed_target <= {0, 1}:
        raise ValueError(
            "O alvo da candidata contém valores fora de 0 e 1: "
            f"{sorted(observed_target)}."
        )

    return {
        "physical_rows": int(metadata.num_rows),
        "physical_columns": int(metadata.num_columns),
        "row_groups": int(parquet_file.num_row_groups),
        "id_registro_missing": 0,
        "id_registro_distinct": distinct_ids,
        "approved_rule_violations": surviving_violations,
        "target_missing": 0,
        "target_values": sorted(observed_target),
    }


def execute_candidate(
    contract: CohortContract,
    contract_path: Path,
    overwrite: bool,
) -> None:
    """Materializa a candidata por row group sem criar partições ou publicar."""

    source_path = resolve_project_path(contract.source_path)

    if not source_path.is_file():
        raise FileNotFoundError(
            "A fonte declarada no contrato não foi encontrada: "
            f"{source_path}"
        )

    output_paths = resolve_candidate_output_paths(contract)
    validate_candidate_preconditions(
        contract=contract,
        output_paths=output_paths,
        overwrite=overwrite,
    )

    for path in output_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = output_paths["temporary_candidate"]
    parquet_file = pq.ParquetFile(source_path)
    source_columns = parquet_file.schema_arrow.names

    if contract.target_output_column in source_columns:
        raise ValueError(
            "A coluna de alvo já existe na fonte: "
            f"{contract.target_output_column}."
        )

    if "id_registro" not in source_columns:
        raise ValueError(
            "A fonte não contém o identificador técnico id_registro."
        )

    source_rows = int(parquet_file.metadata.num_rows)
    excluded_by_rule = {
        rule_id: 0
        for rule_id in contract.approved_exclusion_rule_ids
    }
    raw_rule_counts = {
        rule_id: 0
        for rule_id in contract.rule_order
    }
    candidate_rows = 0
    writer: pq.ParquetWriter | None = None
    candidate_schema: pa.Schema | None = None

    print("Fonte:", source_path)
    print("Contrato:", contract_path)
    print("Row groups:", parquet_file.num_row_groups)
    print("Linhas da fonte:", source_rows)

    try:
        for row_group_index in range(parquet_file.num_row_groups):
            table = parquet_file.read_row_group(row_group_index)
            frame = table.to_pandas(types_mapper=pd.ArrowDtype)
            result = build_final_cohort_candidate(
                frame=frame,
                contract=contract,
            )

            for rule_id in contract.rule_order:
                raw_rule_counts[rule_id] += int(
                    result.audit_evaluation.masks[rule_id].sum()
                )

            for row in result.effective_waterfall.itertuples(index=False):
                excluded_by_rule[str(row.regra)] += int(
                    row.excluidas_na_etapa
                )

            candidate_table = pa.Table.from_pandas(
                result.frame,
                preserve_index=False,
            )

            if writer is None:
                candidate_schema = candidate_table.schema
                writer = pq.ParquetWriter(
                    temporary_path,
                    candidate_schema,
                    compression="zstd",
                    version="2.6",
                )
            elif candidate_table.schema != candidate_schema:
                candidate_table = candidate_table.cast(candidate_schema)

            writer.write_table(candidate_table)
            candidate_rows += int(candidate_table.num_rows)

            print(
                f"Row group {row_group_index + 1}/{parquet_file.num_row_groups}: "
                f"fonte={len(frame)}, candidata={candidate_table.num_rows}"
            )

        if writer is None:
            raise ValueError("Nenhum row group foi gravado na candidata.")

        writer.close()
        writer = None

        total_excluded_rows = int(sum(excluded_by_rule.values()))

        if source_rows != total_excluded_rows + candidate_rows:
            raise ValueError(
                "As contagens globais não fecham: "
                f"fonte={source_rows}, excluídas={total_excluded_rows}, "
                f"candidata={candidate_rows}."
            )

        effective_waterfall = build_global_effective_waterfall(
            rule_order=contract.approved_exclusion_rule_ids,
            excluded_by_rule=excluded_by_rule,
            total_source_rows=source_rows,
        )
        expected_columns = len(source_columns) + 1
        validation = validate_temporary_candidate(
            path=temporary_path,
            contract=contract,
            expected_rows=candidate_rows,
            expected_columns=expected_columns,
        )
        source_hash = sha256_file(source_path)
        candidate_hash = sha256_file(temporary_path)
        temporary_parquet = pq.ParquetFile(temporary_path)
        schema = temporary_parquet.schema_arrow
        temporary_row_groups = temporary_parquet.num_row_groups
        temporary_parquet.close()
        generated_at = datetime.now(timezone.utc).isoformat()

        manifest = {
            "schema_version": 1,
            "kind": "final_cohort_candidate",
            "generated_at_utc": generated_at,
            "contract": {
                "id": contract.contract_id,
                "version": contract.version,
                "status": contract.status,
                "path": str(contract_path),
                "sha256": sha256_file(contract_path),
            },
            "source": {
                "path": str(source_path),
                "sha256": source_hash,
                "rows": source_rows,
                "columns": len(source_columns),
                "row_groups": parquet_file.num_row_groups,
            },
            "rules": [
                {
                    "rule_id": rule_id,
                    "action": contract.rules[rule_id].action,
                    "decision_id": contract.rules[rule_id].decision_id,
                    "raw_count": raw_rule_counts[rule_id],
                    "incremental_count": excluded_by_rule.get(rule_id, 0),
                }
                for rule_id in contract.rule_order
            ],
            "candidate": {
                "path": str(output_paths["candidate_parquet"]),
                "sha256": candidate_hash,
                "rows": candidate_rows,
                "columns": len(schema),
                "row_groups": temporary_row_groups,
                "column_names": schema.names,
                "dtypes": {
                    field.name: str(field.type)
                    for field in schema
                },
            },
            "population": {
                "source_rows": source_rows,
                "excluded_rows": total_excluded_rows,
                "candidate_rows": candidate_rows,
                "exclusion_rate": total_excluded_rows / source_rows,
            },
            "target": {
                "source_column": contract.target_source_column,
                "output_column": contract.target_output_column,
                "mapping": contract.target_mapping,
                "excluded_codes": list(contract.target_excluded_codes),
                "exclude_missing": contract.target_exclude_missing,
            },
            "period": {
                "start": contract.audit_parameters.period_start.isoformat(),
                "end": contract.audit_parameters.period_end.isoformat(),
            },
            "environment": {
                "python": platform.python_version(),
                "pandas": pd.__version__,
                "pyarrow": pa.__version__,
            },
            "execution_guarantees": {
                "source_modified": False,
                "candidate_generated": True,
                "cohort_published": False,
                "exclusions_applied": True,
                "partitions_created": False,
                "test_consulted": False,
            },
        }
        validation_document = {
            "schema_version": 1,
            "generated_at_utc": generated_at,
            "status": "approved_for_comparison",
            "candidate_sha256": candidate_hash,
            "checks": validation,
            "population_reconciliation": {
                "source_rows": source_rows,
                "excluded_rows": total_excluded_rows,
                "candidate_rows": candidate_rows,
                "closed": source_rows == total_excluded_rows + candidate_rows,
            },
            "publication_performed": False,
            "legacy_parity_reviewed": False,
            "provisional_comparison_reviewed": False,
        }

        waterfall_temporary = output_paths["effective_waterfall"].with_suffix(
            ".csv.tmp"
        )
        manifest_temporary = output_paths["manifest"].with_suffix(
            ".json.tmp"
        )
        validation_temporary = output_paths[
            "publication_validation"
        ].with_suffix(".json.tmp")

        effective_waterfall.to_csv(
            waterfall_temporary,
            index=False,
            encoding="utf-8-sig",
        )
        manifest_temporary.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        validation_temporary.write_text(
            json.dumps(
                validation_document,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        os.replace(temporary_path, output_paths["candidate_parquet"])
        os.replace(
            waterfall_temporary,
            output_paths["effective_waterfall"],
        )
        os.replace(manifest_temporary, output_paths["manifest"])
        os.replace(
            validation_temporary,
            output_paths["publication_validation"],
        )

        print()
        print("Candidata gerada e validada.")
        print("Linhas da fonte:", source_rows)
        print("Linhas excluídas:", total_excluded_rows)
        print("Linhas da candidata:", candidate_rows)
        print("Arquivo:", output_paths["candidate_parquet"])
        print("Nenhuma partição foi criada.")
        print("Nenhum conjunto de teste foi consultado.")
        print("A coorte ainda não foi publicada.")
    except Exception:
        if writer is not None:
            writer.close()

        if temporary_path.exists():
            try:
                temporary_path.unlink()
            except PermissionError:
                pass

        raise


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

    if parsed_arguments.mode == "candidate":
        execute_candidate(
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