"""Regras puras de auditoria populacional da coorte SRAG.

Este módulo avalia condições de elegibilidade e qualidade sem decidir quais
regras removem registros. A promoção de uma regra para exclusão pertence ao
contrato versionado da coorte.

As funções deste módulo:

- não leem arquivos;
- não gravam arquivos;
- não alteram o DataFrame recebido;
- não consultam partições de treino, validação ou teste;
- não aplicam exclusões silenciosas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import pandas as pd


DEFAULT_RULE_ORDER: tuple[str, ...] = (
    "hospital_nao_confirmado",
    "dt_interna_invalida",
    "evolucao_fora_alvo_principal",
    "dt_interna_antes_periodo",
    "dt_interna_apos_periodo",
    "intervalo_sintomas_negativo",
    "intervalo_sintomas_maior_limite",
)

REQUIRED_COLUMNS: frozenset[str] = frozenset(
    {
        "hospital",
        "dt_interna",
        "dt_sin_pri",
        "evolucao",
    }
)


@dataclass(frozen=True)
class CohortAuditParameters:
    """Parâmetros necessários para avaliar as regras populacionais."""

    period_start: pd.Timestamp
    period_end: pd.Timestamp
    max_symptom_to_admission_days: int

    def __post_init__(self) -> None:
        period_start = pd.Timestamp(self.period_start)
        period_end = pd.Timestamp(self.period_end)

        if pd.isna(period_start):
            raise ValueError("period_start precisa ser uma data valida.")

        if pd.isna(period_end):
            raise ValueError("period_end precisa ser uma data valida.")

        if period_start > period_end:
            raise ValueError(
                "period_start nao pode ser posterior a period_end."
            )

        if self.max_symptom_to_admission_days < 0:
            raise ValueError(
                "max_symptom_to_admission_days nao pode ser negativo."
            )

        object.__setattr__(self, "period_start", period_start)
        object.__setattr__(self, "period_end", period_end)


@dataclass(frozen=True)
class CohortAuditEvaluation:
    """Resultado imutavel da avaliacao das regras."""

    masks: Mapping[str, pd.Series]
    normalized: pd.DataFrame

    @property
    def row_count(self) -> int:
        return int(len(self.normalized))

    @property
    def rule_ids(self) -> tuple[str, ...]:
        return tuple(self.masks.keys())


def validate_audit_schema(frame: pd.DataFrame) -> None:
    """Valida se as colunas mínimas para auditoria estão disponíveis."""

    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame precisa ser um pandas.DataFrame.")

    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))

    if missing:
        raise ValueError(
            "Colunas obrigatorias ausentes para auditoria: "
            + ", ".join(missing)
        )


def normalize_srag_code(series: pd.Series) -> pd.Series:
    """Normaliza códigos sem fundir ausente, não, ignorado ou não se aplica."""

    normalized = series.astype("string").str.strip()
    normalized = normalized.str.replace(r"\.0$", "", regex=True)

    lowered = normalized.str.lower()
    null_like = lowered.isin(
        {
            "",
            "nan",
            "none",
            "null",
            "<na>",
            "nat",
        }
    )

    return normalized.mask(null_like, pd.NA)


def parse_srag_date(series: pd.Series) -> pd.Series:
    """Converte datas inválidas em NaT sem corrigir valores silenciosamente."""

    return pd.to_datetime(series, errors="coerce")


def evaluate_audit_rules(
    frame: pd.DataFrame,
    parameters: CohortAuditParameters,
) -> CohortAuditEvaluation:
    """Avalia todas as regras sem remover registros.

    A função cria representações normalizadas somente para auditoria. O
    DataFrame recebido não é modificado.
    """

    validate_audit_schema(frame)

    hospital = normalize_srag_code(frame["hospital"])
    evolucao = normalize_srag_code(frame["evolucao"])
    dt_interna = parse_srag_date(frame["dt_interna"])
    dt_sin_pri = parse_srag_date(frame["dt_sin_pri"])

    intervalo_dias = (dt_interna - dt_sin_pri).dt.total_seconds() / 86_400.0

    masks: dict[str, pd.Series] = {
        "hospital_nao_confirmado": hospital.isna() | hospital.ne("1"),
        "dt_interna_invalida": dt_interna.isna(),
        "evolucao_fora_alvo_principal": ~evolucao.isin(["1", "2"]),
        "dt_interna_antes_periodo": (
            dt_interna.notna()
            & dt_interna.lt(parameters.period_start)
        ),
        "dt_interna_apos_periodo": (
            dt_interna.notna()
            & dt_interna.gt(parameters.period_end)
        ),
        "intervalo_sintomas_negativo": (
            dt_interna.notna()
            & dt_sin_pri.notna()
            & intervalo_dias.lt(0)
        ),
        "intervalo_sintomas_maior_limite": (
            dt_interna.notna()
            & dt_sin_pri.notna()
            & intervalo_dias.gt(
                parameters.max_symptom_to_admission_days
            )
        ),
    }

    normalized = pd.DataFrame(
        {
            "hospital_normalizado": hospital,
            "evolucao_normalizada": evolucao,
            "dt_interna_parseada": dt_interna,
            "dt_sin_pri_parseada": dt_sin_pri,
            "intervalo_sintomas_internacao_dias": intervalo_dias,
        },
        index=frame.index,
    )

    return CohortAuditEvaluation(
        masks=masks,
        normalized=normalized,
    )


def summarize_audit_rules(
    evaluation: CohortAuditEvaluation,
) -> pd.DataFrame:
    """Resume cada regra sem assumir que os conjuntos são disjuntos."""

    rows: list[dict[str, object]] = []

    for rule_id, mask in evaluation.masks.items():
        flagged = int(mask.sum())

        rows.append(
            {
                "regra": rule_id,
                "linhas_sinalizadas": flagged,
                "total_linhas": evaluation.row_count,
                "proporcao_fonte": (
                    flagged / evaluation.row_count
                    if evaluation.row_count > 0
                    else 0.0
                ),
            }
        )

    return pd.DataFrame(rows)


def build_rule_overlap(
    evaluation: CohortAuditEvaluation,
    rule_order: Sequence[str] = DEFAULT_RULE_ORDER,
) -> pd.DataFrame:
    """Cria uma matriz simétrica de sobreposição entre regras."""

    validated_order = _validate_rule_order(
        evaluation=evaluation,
        rule_order=rule_order,
    )

    overlap = pd.DataFrame(
        0,
        index=validated_order,
        columns=validated_order,
        dtype="int64",
    )
    overlap.index.name = "regra"

    for left_rule in validated_order:
        for right_rule in validated_order:
            overlap.loc[left_rule, right_rule] = int(
                (
                    evaluation.masks[left_rule]
                    & evaluation.masks[right_rule]
                ).sum()
            )

    return overlap


def build_simulated_waterfall(
    evaluation: CohortAuditEvaluation,
    rule_order: Sequence[str] = DEFAULT_RULE_ORDER,
) -> pd.DataFrame:
    """Simula exclusões sequenciais sem modificar ou devolver uma coorte."""

    validated_order = _validate_rule_order(
        evaluation=evaluation,
        rule_order=rule_order,
    )

    active = pd.Series(
        True,
        index=evaluation.normalized.index,
        dtype=bool,
    )
    rows: list[dict[str, object]] = []

    for order, rule_id in enumerate(validated_order, start=1):
        mask = evaluation.masks[rule_id]
        excluded_now = active & mask
        excluded_count = int(excluded_now.sum())

        active = active & ~mask
        remaining_count = int(active.sum())

        rows.append(
            {
                "ordem": order,
                "regra": rule_id,
                "excluidas_na_etapa": excluded_count,
                "restantes_apos_etapa": remaining_count,
            }
        )

    return pd.DataFrame(rows)


def build_approved_exclusion_mask(
    evaluation: CohortAuditEvaluation,
    approved_rule_ids: Sequence[str],
) -> pd.Series:
    """Combina somente regras explicitamente aprovadas.

    A função devolve a máscara que futuramente poderá ser utilizada pelo
    construtor da candidata. Ela não aplica a máscara ao DataFrame.
    """

    approved = tuple(approved_rule_ids)

    unknown = sorted(set(approved).difference(evaluation.masks))

    if unknown:
        raise ValueError(
            "Regras aprovadas desconhecidas: " + ", ".join(unknown)
        )

    if len(approved) != len(set(approved)):
        raise ValueError(
            "approved_rule_ids nao pode conter regras duplicadas."
        )

    combined = pd.Series(
        False,
        index=evaluation.normalized.index,
        dtype=bool,
    )

    for rule_id in approved:
        combined = combined | evaluation.masks[rule_id]

    return combined


def _validate_rule_order(
    evaluation: CohortAuditEvaluation,
    rule_order: Sequence[str],
) -> tuple[str, ...]:
    """Valida uma ordem de regras antes de produzir relatórios."""

    normalized_order = tuple(rule_order)

    if not normalized_order:
        raise ValueError("rule_order nao pode ser vazio.")

    if len(normalized_order) != len(set(normalized_order)):
        raise ValueError("rule_order nao pode conter regras duplicadas.")

    unknown = sorted(set(normalized_order).difference(evaluation.masks))

    if unknown:
        raise ValueError(
            "rule_order contem regras desconhecidas: "
            + ", ".join(unknown)
        )

    return normalized_order