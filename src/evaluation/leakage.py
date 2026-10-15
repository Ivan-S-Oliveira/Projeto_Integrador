from __future__ import annotations

from typing import Iterable

import pandas as pd


class LeakageError(RuntimeError):
    """Erro lançado quando variáveis com vazamento são encontradas."""


DEFAULT_LEAKAGE_COLUMNS = {
    "evolucao",
    "dt_evoluca",
    "dt_encerra",
    "uti",
    "utilizouvni",
    "suport_ven",
    "antiviral",
    "antivirais",
    "classificacao_final",
    "cluster",
    "cluster_rotulo",
}


def _resolve_forbidden_columns(
    forbidden_columns: Iterable[str] | None,
    target_column: str | None,
) -> set[str]:
    from src.utils import config as C

    yaml_columns = set(C.cfg("features", "proibidas") or [])

    forbidden = (
        set(forbidden_columns)
        if forbidden_columns is not None
        else yaml_columns
    )

    forbidden.update(DEFAULT_LEAKAGE_COLUMNS)

    if target_column is None:
        target_column = C.cfg("target", "coluna")

    if target_column:
        forbidden.add(target_column)

    return forbidden


def check_leakage(
    X: pd.DataFrame,
    *,
    forbidden_columns: Iterable[str] | None = None,
    target_column: str | None = None,
) -> None:
    """
    Valida que nenhuma variável de vazamento está presente na matriz X.

    Parameters
    ----------
    X : pd.DataFrame
        Conjunto de features.
    forbidden_columns : Iterable[str] | None
        Lista customizada de colunas proibidas.
    target_column : str | None
        Nome da variável alvo.
    """
    forbidden = _resolve_forbidden_columns(
        forbidden_columns=forbidden_columns,
        target_column=target_column,
    )

    detected = sorted(set(X.columns) & forbidden)

    if detected:
        raise LeakageError(
            "Variáveis de leakage detectadas: "
            f"{', '.join(detected)}"
        )