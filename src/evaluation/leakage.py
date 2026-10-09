"""
Verificação de vazamento de alvo (leakage).

Uma coluna proibida em `X` invalida qualquer avaliação posterior: o
modelo aprende o alvo por um atalho e as métricas de validação/holdout
viram ficção. Este módulo concentra a checagem em um único ponto.

Uso típico
----------
    from src.evaluation.leakage import check_leakage

    check_leakage(X_train)   # lê `features.proibidas` do supervised.yaml
    check_leakage(X_val)

Para inspeção manual (sem config), passe a lista explicitamente:

    check_leakage(X, forbidden_columns=["evolucao", "dt_evoluca"])
"""

from __future__ import annotations

import pandas as pd


class LeakageError(RuntimeError):
    """Levantado quando uma coluna proibida aparece em X."""


def check_leakage(
    X: pd.DataFrame,
    *,
    forbidden_columns: list[str] | None = None,
    target_column: str | None = None,
) -> None:
    """
    Garante que X não contém colunas que vazam o alvo.

    Parâmetros
    ----------
    X : pd.DataFrame
        Matriz de features a ser verificada.
    forbidden_columns : list[str] | None
        Colunas proibidas. Se None, lê `features.proibidas` do
        `configs/supervised.yaml`. Lista vazia desliga a checagem de
        proibidas (apenas o alvo é verificado).
    target_column : str | None
        Nome da coluna alvo. Se None, lê `target.coluna`. Sempre
        adicionado ao conjunto de proibidas, se não vazio.

    Levanta
    ------
    LeakageError
        Se qualquer coluna proibida estiver presente em `X`.
    """
    from src.utils import config as C

    if forbidden_columns is None:
        forbidden_columns = list(C.cfg("features", "proibidas") or [])
    if target_column is None:
        target_column = C.cfg("target", "coluna")

    proibidas = set(forbidden_columns)
    if target_column:
        proibidas.add(target_column)

    encontradas = sorted(set(X.columns) & proibidas)
    if encontradas:
        raise LeakageError(
            f"Leakage detectado: colunas proibidas em X → {encontradas}.\n"
            f"Revise `features.proibidas` em supervised.yaml "
            f"ou remova essas colunas antes de prosseguir."
        )

    print(
        f"[check_leakage] OK — {X.shape[1]} colunas, "
        f"nenhuma proibida presente."
    )