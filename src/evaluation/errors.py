"""
Análise de erros: quem o modelo erra, por quanto, e em quais grupos.

A checagem de leakage vive em ``src/evaluation/leakage`` — importe de lá::

    from src.evaluation.leakage import LeakageError, check_leakage
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from src.evaluation.metrics import (
    _to_int_labels,
    _to_np,
    auc,
    f1,
    precision,
    recall,
    average_precision_score,
    brier_score_loss,
)

__all__ = [
    "ArrayLike",
    "CriterioTop",
    "matriz_confusao",
    "extrair_falsos_positivos",
    "extrair_falsos_negativos",
    "metricas_por_grupo",
    "top_erros",
]

ArrayLike   = np.ndarray | pd.Series | list
CriterioTop = Literal["fp", "fn", "erro_absoluto"]


def _validar_tamanhos(df: pd.DataFrame, y: np.ndarray) -> None:
    """Garante que ``df`` e os rótulos têm o mesmo número de linhas."""
    if len(df) != len(y):
        raise ValueError(f"df tem {len(df)} linhas e y_true tem {len(y)}.")


def matriz_confusao(
    y_true: ArrayLike,
    y_pred: ArrayLike,
) -> pd.DataFrame:
    """
    Matriz de confusão 2×2 como DataFrame.

    Colunas: ``["pred_0", "pred_1"]``, índice: ``["real_0", "real_1"]``.
    Adiciona linha/coluna ``"total"``.
    """
    y = _to_int_labels(y_true)
    p = _to_int_labels(y_pred)

    contagens = {
        (yv, pv): int(((y == yv) & (p == pv)).sum())
        for yv in (0, 1)
        for pv in (0, 1)
    }

    df = pd.DataFrame(
        [[contagens[(0, 0)], contagens[(0, 1)]],
         [contagens[(1, 0)], contagens[(1, 1)]]],
        index=["real_0", "real_1"],
        columns=["pred_0", "pred_1"],
    )
    df["total"] = df.sum(axis=1)
    df.loc["total"] = df.sum(axis=0)
    return df


def _extrair_por_mascara(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_pred: ArrayLike,
    *,
    yv: int,
    pv: int,
) -> pd.DataFrame:
    """Linhas de ``df`` onde ``y_true == yv`` e ``y_pred == pv``."""
    y = _to_int_labels(y_true)
    p = _to_int_labels(y_pred)
    return df.loc[(y == yv) & (p == pv)].reset_index(drop=True)


def extrair_falsos_positivos(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_pred: ArrayLike,
) -> pd.DataFrame:
    """Linhas de ``df`` onde o modelo previu 1 mas o real é 0."""
    return _extrair_por_mascara(df, y_true, y_pred, yv=0, pv=1)


def extrair_falsos_negativos(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_pred: ArrayLike,
) -> pd.DataFrame:
    """Linhas de ``df`` onde o modelo previu 0 mas o real é 1."""
    return _extrair_por_mascara(df, y_true, y_pred, yv=1, pv=0)


def metricas_por_grupo(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_prob: ArrayLike,
    coluna_grupo: str,
    *,
    limiar: float = 0.5,
    min_n: int = 100,
) -> pd.DataFrame:
       """
    Métricas por categoria de ``coluna_grupo`` (ex.: ``"sg_uf"``).

    Grupos com menos de ``min_n`` amostras são mantidos na tabela com
    ``suprimido=True`` e métricas probabilísticas vazias (``n`` e
    ``prevalencia`` continuam preenchidos).

    Grupos com uma classe só (só curas ou só óbitos) devolvem ``pr_auc``,
    ``roc_auc`` e ``brier`` vazios, sem erro.

    Colunas: ``grupo, n, prevalencia, taxa_positivos, pr_auc,
    pr_auc_sobre_prev, auc, roc_auc, brier, o_e, f1, precision, recall,
    suprimido``.
    """
    if coluna_grupo not in df.columns:
        raise KeyError(f"Coluna de grupo ausente: {coluna_grupo!r}")

    y = _to_int_labels(y_true)
    p = _to_np(y_prob)
    _validar_tamanhos(df, y)

    base   = df.reset_index(drop=True)
    grupos = base[coluna_grupo].astype("string")

    linhas: list[dict[str, float | str]] = []

     for g in grupos.dropna().unique():
        m = (grupos == g).to_numpy()
        n = int(m.sum())

        y_g    = y[m]
        p_g    = p[m]

        duas_classes = len(np.unique(y_g)) >= 2

        if n < min_n:
            linhas.append({
                "grupo":            str(g),
                "n":                float(n),
                "prevalencia":      float(y_g.mean()) if n > 0 else np.nan,
                "taxa_positivos":   float(y_g.mean()) if n > 0 else np.nan,
                "pr_auc":           np.nan,
                "pr_auc_sobre_prev":np.nan,
                "auc":              np.nan,
                "roc_auc":          np.nan,
                "brier":            np.nan,
                "o_e":              np.nan,
                "f1":               np.nan,
                "precision":        np.nan,
                "recall":           np.nan,
                "suprimido":        True,
            })
            continue

        y_pred = (p_g >= limiar).astype(int)

        pr_auc = (
            float(average_precision_score(y_g, p_g))
            if duas_classes else np.nan
        )
        prevalencia = float(y_g.mean()) if n > 0 else np.nan
        pr_auc_sobre_prev = (
            pr_auc / prevalencia
            if not np.isnan(pr_auc) and prevalencia > 0
            else np.nan
        )
        roc_auc = auc(y_g, p_g) if duas_classes else np.nan
        brier   = (
            float(brier_score_loss(y_g, p_g))
            if duas_classes else np.nan
        )
        soma_p  = float(p_g.sum())
        o_e     = (
            float(y_g.sum()) / soma_p
            if soma_p > 0 else np.nan
        )

        linhas.append({
            "grupo":            str(g),
            "n":                float(n),
            "prevalencia":      prevalencia,
            "taxa_positivos":   prevalencia,   # alias de compatibilidade
            "pr_auc":           pr_auc,
            "pr_auc_sobre_prev":pr_auc_sobre_prev,
            "auc":              roc_auc,       # alias de compatibilidade
            "roc_auc":          roc_auc,
            "brier":            brier,
            "o_e":              o_e,
            "f1":               f1(y_g, y_pred),
            "precision":        precision(y_g, y_pred),
            "recall":           recall(y_g, y_pred),
            "suprimido":        False,
        })

    return (
        pd.DataFrame(linhas)
        .sort_values(["suprimido", "n"], ascending=[True, False])
        .reset_index(drop=True)
    )


def top_erros(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_prob: ArrayLike,
    *,
    n: int = 20,
    criterio: CriterioTop = "erro_absoluto",
    limiar: float = 0.5,
) -> pd.DataFrame:
    """
    Retorna as ``n`` linhas de ``df`` com os piores erros.

    ``criterio``:
        - ``"fp"``            → prob decrescente entre FP
        - ``"fn"``            → prob crescente entre FN
        - ``"erro_absoluto"`` → ``|prob − y|`` decrescente (todos os erros)

    Adiciona colunas ``y_true``, ``y_prob``, ``y_pred``, ``erro_abs``.
    """
    y      = _to_int_labels(y_true)
    p      = _to_np(y_prob)
    y_pred = (p >= limiar).astype(int)
    _validar_tamanhos(df, y)

    out = df.reset_index(drop=True).copy()
    out["y_true"]   = y
    out["y_prob"]   = p
    out["y_pred"]   = y_pred
    out["erro_abs"] = np.abs(p - y)

    if criterio == "fp":
        sel = out[(out.y_true == 0) & (out.y_pred == 1)].sort_values("y_prob", ascending=False)
    elif criterio == "fn":
        sel = out[(out.y_true == 1) & (out.y_pred == 0)].sort_values("y_prob", ascending=True)
    elif criterio == "erro_absoluto":
        sel = out[out.y_true != out.y_pred].sort_values("erro_abs", ascending=False)
    else:
        raise ValueError(f"criterio inválido: {criterio!r}. Use 'fp', 'fn' ou 'erro_absoluto'.")

    return sel.head(n).reset_index(drop=True)