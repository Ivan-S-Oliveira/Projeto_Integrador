"""Compara a coorte candidata com a implementação populacional legada."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import pandas as pd
import pyarrow.parquet as pq

from src.data.cohort_audit import evaluate_audit_rules
from src.data.cohort_contract import CohortContract, load_cohort_contract
from src.protocolo import verificacoes as legacy


@dataclass(frozen=True)
class CohortParityResult:
    """Resultado consolidado da comparação com a implementação legada."""

    details: pd.DataFrame
    summary: dict[str, Any]

    @property
    def publication_gate_passed(self) -> bool:
        """Indica se não restaram diferenças populacionais ou de alvo sem explicação."""

        return bool(self.summary["publication_gate_passed"])


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Calcula o SHA-256 sem carregar o arquivo inteiro em memória."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def build_period_aligned_legacy_config(
    historical_config: Mapping[str, Any],
    contract: CohortContract,
) -> dict[str, Any]:
    """Alinha apenas o domínio temporal do legado ao contrato populacional."""

    aligned = copy.deepcopy(dict(historical_config))
    start_year = int(contract.audit_parameters.period_start.year)
    end_year = int(contract.audit_parameters.period_end.year)
    aligned["min_date"] = contract.audit_parameters.period_start.date().isoformat()
    aligned["dev_years"] = list(range(start_year, end_year + 1))
    aligned["holdout_years"] = []
    return aligned


def _normalized_id(series: pd.Series) -> pd.Series:
    """Normaliza o identificador técnico para comparação determinística."""

    normalized = series.astype("string").str.strip()
    if normalized.isna().any() or normalized.eq("").any():
        raise ValueError("A comparação encontrou id_registro ausente ou vazio.")
    if normalized.duplicated().any():
        raise ValueError("A comparação encontrou id_registro duplicado no lote.")
    return normalized


def compare_parity_frames(
    source_frame: pd.DataFrame,
    candidate_frame: pd.DataFrame,
    contract: CohortContract,
    historical_config: Mapping[str, Any],
    period_aligned_config: Mapping[str, Any],
    row_group: int,
) -> dict[str, int | str]:
    """Compara um lote da fonte com o lote correspondente da candidata."""

    source_original = source_frame.copy(deep=True)
    candidate_original = candidate_frame.copy(deep=True)

    required_source = {
        "id_registro",
        "hospital",
        "dt_interna",
        "dt_sin_pri",
        "evolucao",
    }
    missing_source = sorted(required_source - set(source_frame.columns))
    if missing_source:
        raise ValueError(f"A fonte não contém colunas exigidas: {missing_source}.")

    required_candidate = {"id_registro", contract.target_output_column}
    missing_candidate = sorted(required_candidate - set(candidate_frame.columns))
    if missing_candidate:
        raise ValueError(
            f"A candidata não contém colunas exigidas: {missing_candidate}."
        )

    source_ids = _normalized_id(source_frame["id_registro"])
    candidate_ids = _normalized_id(candidate_frame["id_registro"])

    historical_input = legacy.prepare(source_frame.copy(deep=True))
    aligned_input = legacy.prepare(source_frame.copy(deep=True))
    historical_cohort = legacy.a1_cohort(
        historical_input,
        dict(historical_config),
    )
    aligned_cohort = legacy.a1_cohort(
        aligned_input,
        dict(period_aligned_config),
    )

    legacy_id_column = "ID_REGISTRO"
    if legacy_id_column not in aligned_cohort.columns:
        raise ValueError(
            "A implementação legada não preservou a coluna ID_REGISTRO."
        )

    historical_ids = _normalized_id(historical_cohort[legacy_id_column])
    aligned_ids = _normalized_id(aligned_cohort[legacy_id_column])

    historical_set = set(historical_ids.tolist())
    aligned_set = set(aligned_ids.tolist())
    candidate_set = set(candidate_ids.tolist())

    only_legacy = aligned_set - candidate_set
    only_candidate = candidate_set - aligned_set
    common = aligned_set & candidate_set

    evaluation = evaluate_audit_rules(
        frame=source_frame,
        parameters=contract.audit_parameters,
    )
    only_legacy_mask = source_ids.isin(only_legacy)
    negative_mask = evaluation.masks["intervalo_sintomas_negativo"]
    above_limit_mask = evaluation.masks["intervalo_sintomas_maior_limite"]

    only_legacy_negative = int((only_legacy_mask & negative_mask).sum())
    only_legacy_above_limit = int((only_legacy_mask & above_limit_mask).sum())
    only_legacy_explained = int(
        (only_legacy_mask & (negative_mask | above_limit_mask)).sum()
    )
    only_legacy_other = int(only_legacy_mask.sum() - only_legacy_explained)

    only_candidate_other = int(len(only_candidate))

    legacy_target = (
        aligned_cohort.loc[
            _normalized_id(aligned_cohort[legacy_id_column]).isin(common),
            [legacy_id_column, "_alvo"],
        ]
        .assign(**{legacy_id_column: lambda frame: _normalized_id(frame[legacy_id_column])})
        .set_index(legacy_id_column)["_alvo"]
        .astype("int8")
        .sort_index()
    )
    candidate_target = (
        candidate_frame.loc[
            candidate_ids.isin(common),
            ["id_registro", contract.target_output_column],
        ]
        .assign(id_registro=lambda frame: _normalized_id(frame["id_registro"]))
        .set_index("id_registro")[contract.target_output_column]
        .astype("int8")
        .sort_index()
    )

    if not legacy_target.index.equals(candidate_target.index):
        raise ValueError(
            f"Os identificadores comuns não ficaram alinhados no lote {row_group}."
        )

    target_mismatches = int(
        (legacy_target.to_numpy() != candidate_target.to_numpy()).sum()
    )

    pd.testing.assert_frame_equal(source_frame, source_original)
    pd.testing.assert_frame_equal(candidate_frame, candidate_original)

    return {
        "row_group": row_group,
        "source_rows": int(len(source_frame)),
        "legacy_historical_rows": int(len(historical_set)),
        "legacy_aligned_rows": int(len(aligned_set)),
        "candidate_rows": int(len(candidate_set)),
        "common_rows": int(len(common)),
        "only_legacy_rows": int(len(only_legacy)),
        "only_candidate_rows": int(len(only_candidate)),
        "only_legacy_negative_interval": only_legacy_negative,
        "only_legacy_above_limit": only_legacy_above_limit,
        "only_legacy_unexplained": only_legacy_other,
        "only_candidate_unexplained": only_candidate_other,
        "target_mismatches": target_mismatches,
    }


def _summarize(details: pd.DataFrame) -> dict[str, int]:
    """Soma as métricas dos lotes e valida o fechamento global."""

    numeric_columns = [column for column in details.columns if column != "row_group"]
    totals = {column: int(details[column].sum()) for column in numeric_columns}

    if totals["legacy_aligned_rows"] != (
        totals["common_rows"] + totals["only_legacy_rows"]
    ):
        raise ValueError("As contagens do legado alinhado não fecham.")

    if totals["candidate_rows"] != (
        totals["common_rows"] + totals["only_candidate_rows"]
    ):
        raise ValueError("As contagens da candidata não fecham.")

    if totals["only_legacy_rows"] != (
        totals["only_legacy_negative_interval"]
        + totals["only_legacy_above_limit"]
        + totals["only_legacy_unexplained"]
    ):
        raise ValueError("A classificação das diferenças do legado não fecha.")

    return totals


def run_legacy_parity(
    source_path: Path,
    candidate_path: Path,
    contract_path: Path,
    historical_config_path: Path,
    legacy_module_path: Path,
) -> CohortParityResult:
    """Executa a paridade por row group sem modificar os artefatos de entrada."""

    for path in (
        source_path,
        candidate_path,
        contract_path,
        historical_config_path,
        legacy_module_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    contract = load_cohort_contract(contract_path)
    historical_config = legacy.load_config(str(historical_config_path))
    aligned_config = build_period_aligned_legacy_config(
        historical_config,
        contract,
    )

    source_file = pq.ParquetFile(source_path)
    candidate_file = pq.ParquetFile(candidate_path)

    if source_file.num_row_groups != candidate_file.num_row_groups:
        raise ValueError(
            "A fonte e a candidata possuem quantidades diferentes de row groups."
        )

    rows: list[dict[str, int | str]] = []
    for index in range(source_file.num_row_groups):
        source_frame = source_file.read_row_group(
            index,
            columns=[
                "id_registro",
                "hospital",
                "dt_interna",
                "dt_sin_pri",
                "evolucao",
            ],
        ).to_pandas()
        candidate_frame = candidate_file.read_row_group(
            index,
            columns=["id_registro", contract.target_output_column],
        ).to_pandas()
        rows.append(
            compare_parity_frames(
                source_frame=source_frame,
                candidate_frame=candidate_frame,
                contract=contract,
                historical_config=historical_config,
                period_aligned_config=aligned_config,
                row_group=index + 1,
            )
        )

    details = pd.DataFrame(rows)
    totals = _summarize(details)
    population_status = (
        "explained"
        if totals["only_legacy_unexplained"] == 0
        and totals["only_candidate_unexplained"] == 0
        else "unexplained"
    )
    target_status = "passed" if totals["target_mismatches"] == 0 else "failed"
    gate_passed = population_status == "explained" and target_status == "passed"

    summary: dict[str, Any] = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "path": str(source_path),
            "sha256": sha256_file(source_path),
        },
        "candidate": {
            "path": str(candidate_path),
            "sha256": sha256_file(candidate_path),
        },
        "contract": {
            "path": str(contract_path),
            "sha256": sha256_file(contract_path),
            "id": contract.contract_id,
            "version": contract.version,
        },
        "legacy": {
            "config_path": str(historical_config_path),
            "config_sha256": sha256_file(historical_config_path),
            "module_path": str(legacy_module_path),
            "module_sha256": sha256_file(legacy_module_path),
            "historical_config": {
                "min_date": historical_config["min_date"],
                "dev_years": historical_config["dev_years"],
                "holdout_years": historical_config["holdout_years"],
                "drop_date_inconsistencies": historical_config[
                    "drop_date_inconsistencies"
                ],
            },
            "period_aligned_config": {
                "min_date": aligned_config["min_date"],
                "dev_years": aligned_config["dev_years"],
                "holdout_years": aligned_config["holdout_years"],
                "drop_date_inconsistencies": aligned_config[
                    "drop_date_inconsistencies"
                ],
            },
        },
        "totals": totals,
        "population_parity_status": population_status,
        "target_parity_status": target_status,
        "publication_gate_passed": gate_passed,
        "execution_guarantees": {
            "source_modified": False,
            "candidate_modified": False,
            "cohort_published": False,
            "partitions_created": False,
            "test_consulted": False,
        },
    }
    return CohortParityResult(details=details, summary=summary)


def write_parity_outputs(
    result: CohortParityResult,
    comparison_path: Path,
    manifest_path: Path,
    overwrite: bool = False,
) -> None:
    """Grava os artefatos de paridade após todas as validações."""

    existing = [path for path in (comparison_path, manifest_path) if path.exists()]
    if existing and not overwrite:
        formatted = "\n".join(f"- {path}" for path in existing)
        raise FileExistsError(
            "Já existem artefatos de paridade:\n"
            f"{formatted}\n"
            "Use overwrite somente após revisar a execução anterior."
        )

    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    comparison_temp = comparison_path.with_suffix(comparison_path.suffix + ".tmp")
    manifest_temp = manifest_path.with_suffix(manifest_path.suffix + ".tmp")

    result.details.to_csv(comparison_temp, index=False, encoding="utf-8-sig")
    manifest_temp.write_text(
        json.dumps(result.summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    comparison_temp.replace(comparison_path)
    manifest_temp.replace(manifest_path)
