"""Verificação anti-vazamento de dados.

``check_leakage`` valida que nenhuma coluna proibida aparece em ``X``.
A lista efetiva é a união de:

- ``forbidden_columns`` (explícito) OU ``features.proibidas`` do YAML;
- ``DEFAULT_LEAKAGE_COLUMNS`` (desfecho, tratamentos, clusters);
- ``target_column`` (explícito) OU ``target.coluna`` do YAML.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from src.utils import config as C

__all__ = ["LeakageError", "check_leakage"]


class LeakageError(RuntimeError):
    """Erro lançado quando variáveis com vazamento são encontradas."""


DEFAULT_LEAKAGE_COLUMNS = frozenset({
    "evolucao", "dt_evoluca", "dt_encerra",
    "uti", "utilizouvni", "suport_ven",
    "antiviral", "antivirais",
    "classificacao_final",
    "cluster", "cluster_rotulo",
})


def _resolve_forbidden_columns(
    forbidden_columns: Iterable[str] | None,
    target_column: str | None,
) -> set[str]:
    """Conjunto efetivo de colunas proibidas.

    Prioridade: ``forbidden_columns`` explícito > ``features.proibidas``
    do YAML. Sempre soma ``DEFAULT_LEAKAGE_COLUMNS`` e o alvo.
    """
    base = (
        set(forbidden_columns)
        if forbidden_columns is not None
        else set(C.cfg("features", "proibidas") or [])
    )
    base |= DEFAULT_LEAKAGE_COLUMNS

    target = target_column if target_column is not None else C.cfg("target", "coluna")
    if target:
        base.add(target)
    return base


def check_leakage(
    X: pd.DataFrame,
    *,
    forbidden_columns: Iterable[str] | None = None,
    target_column: str | None = None,
) -> None:
    """Levanta ``LeakageError`` se ``X`` contiver colunas proibidas.

    ``forbidden_columns=None`` usa ``features.proibidas`` do YAML;
    ``target_column=None`` usa ``target.coluna`` do YAML.
    """
    forbidden = _resolve_forbidden_columns(forbidden_columns, target_column)
    if detected := sorted(set(X.columns) & forbidden):
        raise LeakageError(f"Variáveis de leakage detectadas: {', '.join(detected)}")