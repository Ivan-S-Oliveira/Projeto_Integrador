"""Carregamento e validação do contrato populacional da coorte SRAG.

O módulo converte o YAML versionado em objetos imutáveis e falha antes do
processamento dos dados quando encontra decisões incompletas ou incoerentes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd
import yaml

from src.data.cohort_audit import (
    CohortAuditParameters,
    DEFAULT_RULE_ORDER,
)


VALID_CONTRACT_STATUSES: frozenset[str] = frozenset(
    {
        "candidate",
        "approved",
        "retired",
    }
)

VALID_RULE_ACTIONS: frozenset[str] = frozenset(
    {
        "audit_only",
        "approved_exclusion",
        "quarantine",
    }
)


@dataclass(frozen=True)
class CohortRuleContract:
    """Decisão declarada para uma regra de auditoria."""

    rule_id: str
    action: str
    rationale: str
    decision_id: str | None

    @property
    def removes_rows(self) -> bool:
        return self.action in {
            "approved_exclusion",
            "quarantine",
        }


@dataclass(frozen=True)
class CohortContract:
    """Contrato populacional validado da coorte."""

    contract_id: str
    version: int
    status: str
    description: str
    source_path: Path
    source_manifest_path: Path
    audit_parameters: CohortAuditParameters
    rule_order: tuple[str, ...]
    rules: Mapping[str, CohortRuleContract]
    required_columns: tuple[str, ...]
    target_source_column: str
    target_output_column: str
    target_mapping: Mapping[str, int]
    target_excluded_codes: tuple[str, ...]
    target_exclude_missing: bool
    outputs: Mapping[str, Path]

    @property
    def approved_exclusion_rule_ids(self) -> tuple[str, ...]:
        return tuple(
            rule_id
            for rule_id in self.rule_order
            if self.rules[rule_id].action == "approved_exclusion"
        )

    @property
    def quarantine_rule_ids(self) -> tuple[str, ...]:
        return tuple(
            rule_id
            for rule_id in self.rule_order
            if self.rules[rule_id].action == "quarantine"
        )

    @property
    def audit_only_rule_ids(self) -> tuple[str, ...]:
        return tuple(
            rule_id
            for rule_id in self.rule_order
            if self.rules[rule_id].action == "audit_only"
        )


def load_cohort_contract(path: Path) -> CohortContract:
    """Carrega e valida integralmente um contrato YAML."""

    contract_path = Path(path)

    if not contract_path.is_file():
        raise FileNotFoundError(
            f"Contrato de coorte nao encontrado: {contract_path}"
        )

    with contract_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if not isinstance(raw, dict):
        raise ValueError(
            "O contrato precisa ter um objeto YAML no nivel raiz."
        )

    return parse_cohort_contract(raw)


def parse_cohort_contract(raw: Mapping[str, Any]) -> CohortContract:
    """Valida um contrato já carregado e cria sua representação imutável."""

    contract_section = _require_mapping(raw, "contract")
    source_section = _require_mapping(raw, "source")
    period_section = _require_mapping(raw, "period")
    target_section = _require_mapping(raw, "target")
    audit_section = _require_mapping(raw, "audit")
    outputs_section = _require_mapping(raw, "outputs")

    contract_id = _require_nonempty_string(contract_section, "id")
    version = _require_positive_integer(contract_section, "version")
    status = _require_nonempty_string(contract_section, "status")
    description = _require_nonempty_string(
        contract_section,
        "description",
    )

    if status not in VALID_CONTRACT_STATUSES:
        raise ValueError(
            f"Status de contrato invalido: {status!r}. "
            f"Permitidos: {sorted(VALID_CONTRACT_STATUSES)}"
        )

    source_path = Path(
        _require_nonempty_string(source_section, "path")
    )
    source_manifest_path = Path(
        _require_nonempty_string(source_section, "manifest_path")
    )

    period_start = _parse_contract_date(
        period_section,
        "start",
    )
    period_end = _parse_contract_date(
        period_section,
        "end",
    )

    max_interval = _require_nonnegative_integer(
        audit_section,
        "max_symptom_to_admission_days",
    )

    audit_parameters = CohortAuditParameters(
        period_start=period_start,
        period_end=period_end,
        max_symptom_to_admission_days=max_interval,
    )

    rule_order = _require_unique_string_sequence(
        audit_section,
        "rule_order",
    )

    rules_raw = _require_mapping(audit_section, "rules")
    rules = _parse_rules(rules_raw)

    expected_rules = set(DEFAULT_RULE_ORDER)
    ordered_rules = set(rule_order)
    declared_rules = set(rules)

    if ordered_rules != expected_rules:
        missing = sorted(expected_rules - ordered_rules)
        extra = sorted(ordered_rules - expected_rules)
        raise ValueError(
            "rule_order diverge das regras implementadas. "
            f"Ausentes: {missing}. Extras: {extra}."
        )

    if declared_rules != ordered_rules:
        missing = sorted(ordered_rules - declared_rules)
        extra = sorted(declared_rules - ordered_rules)
        raise ValueError(
            "A secao audit.rules diverge de rule_order. "
            f"Ausentes: {missing}. Extras: {extra}."
        )

    required_columns = _require_unique_string_sequence(
        raw,
        "required_columns",
    )

    minimum_required_columns = {
        "hospital",
        "dt_interna",
        "dt_sin_pri",
        "evolucao",
    }
    missing_required = sorted(
        minimum_required_columns.difference(required_columns)
    )

    if missing_required:
        raise ValueError(
            "required_columns nao inclui as colunas minimas: "
            + ", ".join(missing_required)
        )

    target_source_column = _require_nonempty_string(
        target_section,
        "source_column",
    )
    target_output_column = _require_nonempty_string(
        target_section,
        "output_column",
    )

    target_mapping = _parse_target_mapping(
        _require_mapping(target_section, "mapping")
    )

    target_excluded_codes = _require_unique_string_sequence(
        target_section,
        "excluded_codes",
    )

    target_exclude_missing = target_section.get("exclude_missing")

    if not isinstance(target_exclude_missing, bool):
        raise ValueError(
            "target.exclude_missing precisa ser booleano."
        )

    if target_source_column not in required_columns:
        raise ValueError(
            "A coluna de origem do alvo precisa estar em required_columns."
        )

    if set(target_mapping).intersection(target_excluded_codes):
        raise ValueError(
            "Um codigo do alvo nao pode estar simultaneamente em mapping "
            "e excluded_codes."
        )

    outputs = _parse_outputs(outputs_section)

    return CohortContract(
        contract_id=contract_id,
        version=version,
        status=status,
        description=description,
        source_path=source_path,
        source_manifest_path=source_manifest_path,
        audit_parameters=audit_parameters,
        rule_order=rule_order,
        rules=rules,
        required_columns=required_columns,
        target_source_column=target_source_column,
        target_output_column=target_output_column,
        target_mapping=target_mapping,
        target_excluded_codes=target_excluded_codes,
        target_exclude_missing=target_exclude_missing,
        outputs=outputs,
    )


def _parse_rules(
    rules_raw: Mapping[str, Any],
) -> dict[str, CohortRuleContract]:
    rules: dict[str, CohortRuleContract] = {}

    for rule_id, value in rules_raw.items():
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise ValueError(
                "Todo identificador de regra precisa ser texto nao vazio."
            )

        if not isinstance(value, dict):
            raise ValueError(
                f"A regra {rule_id!r} precisa ser um objeto YAML."
            )

        action = _require_nonempty_string(value, "action")
        rationale = _require_nonempty_string(value, "rationale")
        decision_id_raw = value.get("decision_id")

        if action not in VALID_RULE_ACTIONS:
            raise ValueError(
                f"Acao invalida para {rule_id!r}: {action!r}. "
                f"Permitidas: {sorted(VALID_RULE_ACTIONS)}"
            )

        if decision_id_raw is not None:
            if (
                not isinstance(decision_id_raw, str)
                or not decision_id_raw.strip()
            ):
                raise ValueError(
                    f"decision_id invalido para {rule_id!r}."
                )
            decision_id = decision_id_raw.strip()
        else:
            decision_id = None

        if action in {"approved_exclusion", "quarantine"}:
            if decision_id is None:
                raise ValueError(
                    f"A regra {rule_id!r} remove registros e exige "
                    "decision_id."
                )

        rules[rule_id] = CohortRuleContract(
            rule_id=rule_id,
            action=action,
            rationale=rationale,
            decision_id=decision_id,
        )

    return rules


def _parse_target_mapping(
    mapping_raw: Mapping[str, Any],
) -> dict[str, int]:
    mapping: dict[str, int] = {}

    for source_code, target_value in mapping_raw.items():
        normalized_code = str(source_code).strip()

        if not normalized_code:
            raise ValueError(
                "O mapeamento do alvo contem codigo vazio."
            )

        if isinstance(target_value, bool) or target_value not in {0, 1}:
            raise ValueError(
                "Os valores produzidos pelo alvo precisam ser 0 ou 1."
            )

        mapping[normalized_code] = int(target_value)

    if set(mapping.values()) != {0, 1}:
        raise ValueError(
            "O mapeamento do alvo precisa produzir as classes 0 e 1."
        )

    return mapping


def _parse_outputs(
    outputs_raw: Mapping[str, Any],
) -> dict[str, Path]:
    required_output_keys = {
        "candidate_directory",
        "candidate_parquet",
        "audit_summary",
        "simulated_waterfall",
        "effective_waterfall",
        "manifest",
        "publication_validation",
        "published_parquet",
    }

    missing = sorted(required_output_keys.difference(outputs_raw))
    extra = sorted(set(outputs_raw).difference(required_output_keys))

    if missing or extra:
        raise ValueError(
            "A secao outputs possui chaves invalidas. "
            f"Ausentes: {missing}. Extras: {extra}."
        )

    return {
        key: Path(_require_nonempty_string(outputs_raw, key))
        for key in sorted(required_output_keys)
    }


def _require_mapping(
    mapping: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any]:
    value = mapping.get(key)

    if not isinstance(value, dict):
        raise ValueError(
            f"A chave {key!r} precisa conter um objeto YAML."
        )

    return value


def _require_nonempty_string(
    mapping: Mapping[str, Any],
    key: str,
) -> str:
    value = mapping.get(key)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"A chave {key!r} precisa ser texto nao vazio."
        )

    return value.strip()


def _require_positive_integer(
    mapping: Mapping[str, Any],
    key: str,
) -> int:
    value = mapping.get(key)

    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(
            f"A chave {key!r} precisa ser inteiro positivo."
        )

    return value


def _require_nonnegative_integer(
    mapping: Mapping[str, Any],
    key: str,
) -> int:
    value = mapping.get(key)

    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(
            f"A chave {key!r} precisa ser inteiro nao negativo."
        )

    return value


def _require_unique_string_sequence(
    mapping: Mapping[str, Any],
    key: str,
) -> tuple[str, ...]:
    value = mapping.get(key)

    if not isinstance(value, list) or not value:
        raise ValueError(
            f"A chave {key!r} precisa ser uma lista nao vazia."
        )

    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(
            f"A chave {key!r} aceita somente textos nao vazios."
        )

    normalized = tuple(item.strip() for item in value)

    if len(normalized) != len(set(normalized)):
        raise ValueError(
            f"A chave {key!r} nao pode conter duplicatas."
        )

    return normalized


def _parse_contract_date(
    mapping: Mapping[str, Any],
    key: str,
) -> pd.Timestamp:
    raw_value = _require_nonempty_string(mapping, key)
    parsed = pd.to_datetime(raw_value, errors="coerce")

    if pd.isna(parsed):
        raise ValueError(
            f"A chave {key!r} precisa conter uma data valida."
        )

    return pd.Timestamp(parsed)