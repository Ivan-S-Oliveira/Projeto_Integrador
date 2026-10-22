"""Construção em memória da candidata à coorte definitiva SRAG.

Este módulo conecta o contrato declarativo às regras de auditoria já
implementadas. Ele não lê nem grava arquivos e não cria partições de
desenvolvimento ou teste.

A persistência e a publicação da coorte serão tratadas em incrementos
posteriores.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.data.cohort_audit import (
    CohortAuditEvaluation,
    build_approved_exclusion_mask,
    build_rule_overlap,
    build_simulated_waterfall,
    evaluate_audit_rules,
    normalize_srag_code,
    summarize_audit_rules,
)
from src.data.cohort_contract import CohortContract


@dataclass(frozen=True)
class FinalCohortCandidate:
    """Resultado da construção em memória da candidata."""

    frame: pd.DataFrame
    audit_evaluation: CohortAuditEvaluation
    audit_summary: pd.DataFrame
    rule_overlap: pd.DataFrame
    simulated_waterfall: pd.DataFrame
    effective_waterfall: pd.DataFrame
    excluded_mask: pd.Series
    total_source_rows: int
    total_excluded_rows: int
    total_candidate_rows: int

    @property
    def exclusion_rate(self) -> float:
        """Retorna a proporção excluída em relação à fonte."""

        if self.total_source_rows == 0:
            return 0.0

        return (
            self.total_excluded_rows
            / self.total_source_rows
        )


def build_final_cohort_candidate(
    frame: pd.DataFrame,
    contract: CohortContract,
) -> FinalCohortCandidate:
    """Constrói uma candidata sem modificar o DataFrame recebido.

    Somente regras declaradas como ``approved_exclusion`` removem linhas.
    Regras ``audit_only`` continuam medidas e documentadas, mas não
    participam da máscara efetiva de exclusão.
    """

    _validate_candidate_input(
        frame=frame,
        contract=contract,
    )

    source = frame.copy(deep=True)

    audit_evaluation = evaluate_audit_rules(
        frame=source,
        parameters=contract.audit_parameters,
    )

    audit_summary = summarize_audit_rules(
        audit_evaluation
    )

    rule_overlap = build_rule_overlap(
        evaluation=audit_evaluation,
        rule_order=contract.rule_order,
    )

    simulated_waterfall = build_simulated_waterfall(
        evaluation=audit_evaluation,
        rule_order=contract.rule_order,
    )

    approved_rule_ids = (
        contract.approved_exclusion_rule_ids
    )

    excluded_mask = build_approved_exclusion_mask(
        evaluation=audit_evaluation,
        approved_rule_ids=approved_rule_ids,
    )

    effective_waterfall = build_simulated_waterfall(
        evaluation=audit_evaluation,
        rule_order=approved_rule_ids,
    )

    candidate = (
        source.loc[~excluded_mask]
        .copy()
    )

    normalized_target = normalize_srag_code(
        candidate[contract.target_source_column]
    )

    candidate[contract.target_output_column] = (
        normalized_target.map(
            contract.target_mapping
        )
    )

    _validate_candidate_output(
        source=source,
        candidate=candidate,
        contract=contract,
        excluded_mask=excluded_mask,
    )

    candidate[contract.target_output_column] = (
        candidate[contract.target_output_column]
        .astype("int8")
    )

    total_source_rows = int(len(source))
    total_excluded_rows = int(excluded_mask.sum())
    total_candidate_rows = int(len(candidate))

    if (
        total_source_rows
        != total_excluded_rows + total_candidate_rows
    ):
        raise RuntimeError(
            "A contagem da candidata não fecha com a fonte "
            "e a máscara de exclusão."
        )

    return FinalCohortCandidate(
        frame=candidate,
        audit_evaluation=audit_evaluation,
        audit_summary=audit_summary,
        rule_overlap=rule_overlap,
        simulated_waterfall=simulated_waterfall,
        effective_waterfall=effective_waterfall,
        excluded_mask=excluded_mask.copy(),
        total_source_rows=total_source_rows,
        total_excluded_rows=total_excluded_rows,
        total_candidate_rows=total_candidate_rows,
    )


def _validate_candidate_input(
    frame: pd.DataFrame,
    contract: CohortContract,
) -> None:
    """Valida o contrato mínimo antes de avaliar qualquer regra."""

    if not isinstance(frame, pd.DataFrame):
        raise TypeError(
            "frame precisa ser um pandas.DataFrame."
        )

    if frame.empty:
        raise ValueError(
            "A fonte da candidata não pode estar vazia."
        )

    missing_columns = sorted(
        set(contract.required_columns)
        - set(frame.columns)
    )

    if missing_columns:
        raise ValueError(
            "A fonte não contém todas as colunas exigidas "
            "pelo contrato: "
            + ", ".join(missing_columns)
        )

    if (
        contract.target_source_column
        not in frame.columns
    ):
        raise ValueError(
            "A coluna de origem do alvo não existe "
            "na fonte."
        )

    if (
        contract.target_output_column
        in frame.columns
    ):
        raise ValueError(
            "A coluna de saída do alvo já existe na fonte: "
            f"{contract.target_output_column!r}."
        )

    duplicated_columns = (
        frame.columns[
            frame.columns.duplicated()
        ]
        .tolist()
    )

    if duplicated_columns:
        raise ValueError(
            "A fonte contém colunas duplicadas: "
            f"{duplicated_columns}"
        )

    if not frame.index.is_unique:
        raise ValueError(
            "O índice da fonte precisa ser único antes "
            "da construção da candidata."
        )


def _validate_candidate_output(
    source: pd.DataFrame,
    candidate: pd.DataFrame,
    contract: CohortContract,
    excluded_mask: pd.Series,
) -> None:
    """Valida invariantes populacionais após as exclusões."""

    if len(excluded_mask) != len(source):
        raise RuntimeError(
            "A máscara de exclusão não possui o mesmo "
            "tamanho da fonte."
        )

    if not excluded_mask.index.equals(source.index):
        raise RuntimeError(
            "A máscara de exclusão não está alinhada "
            "ao índice da fonte."
        )

    if candidate.empty:
        raise ValueError(
            "As regras aprovadas removeram todos os registros."
        )

    if not candidate.index.is_unique:
        raise RuntimeError(
            "A candidata possui índice duplicado."
        )

    if not candidate.index.isin(source.index).all():
        raise RuntimeError(
            "A candidata contém índices inexistentes na fonte."
        )

    target = candidate[
        contract.target_output_column
    ]

    if target.isna().any():
        unexpected_codes = sorted(
            normalize_srag_code(
                candidate[
                    contract.target_source_column
                ]
            )
            .loc[target.isna()]
            .dropna()
            .unique()
            .tolist()
        )

        raise RuntimeError(
            "A candidata contém valores sem mapeamento "
            "no alvo principal. "
            f"Códigos observados: {unexpected_codes}"
        )

    observed_target_values = set(
        pd.to_numeric(
            target,
            errors="coerce",
        )
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    if not observed_target_values.issubset(
        {0, 1}
    ):
        raise RuntimeError(
            "O alvo produzido contém valores fora de 0 e 1: "
            f"{sorted(observed_target_values)}"
        )

    if contract.target_exclude_missing:
        normalized_source_target = normalize_srag_code(
            candidate[
                contract.target_source_column
            ]
        )

        if normalized_source_target.isna().any():
            raise RuntimeError(
                "A candidata preservou valores ausentes "
                "na coluna de origem do alvo."
            )

    excluded_codes_present = sorted(
        set(
            normalize_srag_code(
                candidate[
                    contract.target_source_column
                ]
            )
            .dropna()
            .unique()
            .tolist()
        )
        .intersection(
            contract.target_excluded_codes
        )
    )

    if excluded_codes_present:
        raise RuntimeError(
            "A candidata preservou códigos explicitamente "
            "excluídos do alvo: "
            f"{excluded_codes_present}"
        )