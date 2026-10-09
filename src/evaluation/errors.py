"""
Análise de erros: quem o modelo erra, por quanto, e em quais grupos.

Ferramentas
-----------
- `matriz_confusao`           → TP/FP/FN/TN em DataFrame
- `extrair_falsos_positivos`  → subconjunto do df com FP
- `extrair_falsos_negativos`  → subconjunto do df com FN
- `metricas_por_grupo`        → métricas por categoria de uma coluna
- `top_erros`                 → os N piores erros por confiança

A checagem de leakage vive em `src.evaluation.leakage` — importe de lá:

    from src.evaluation.leakage import LeakageError, check_leakage
"""

from __future__ import annotations

from typing import Literal, Union

import numpy as np
import pandas as pd

from src.evaluation.metrics import (
    _to_int_labels,
    _to_np,
    auc,
    f1,
    precision,
    recall,
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

ArrayLike = Union[np.ndarray, pd.Series, list]

CriterioTop = Literal["fp", "fn", "erro_absoluto"]


# ---------------------------------------------------------------------------
# Matriz de confusão
# ---------------------------------------------------------------------------

def matriz_confusao(
    y_true: ArrayLike,
    y_pred: ArrayLike,
) -> pd.DataFrame:
    """
    Matriz de confusão 2×2 como DataFrame.

    Colunas: ["pred_0", "pred_1"], índice: ["real_0", "real_1"].
    Adiciona linha/coluna "total" para conveniência.
    """
    y = _to_int_labels(y_true)
    p = _to_int_labels(y_pred)

    tn = int(((y == 0) & (p == 0)).sum())
    fp = int(((y == 0) & (p == 1)).sum())
    fn = int(((y == 1) & (p == 0)).sum())
    tp = int(((y == 1) & (p == 1)).sum())

    df = pd.DataFrame(
        [[tn, fp], [fn, tp]],
        index=["real_0", "real_1"],
        columns=["pred_0", "pred_1"],
    )
    df["total"] = df.sum(axis=1)
    df.loc["total"] = df.sum(axis=0)
    return df


# ---------------------------------------------------------------------------
# Falsos positivos / negativos
# ---------------------------------------------------------------------------

def extrair_falsos_positivos(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_pred: ArrayLike,
) -> pd.DataFrame:
    """Retorna as linhas de `df` onde o modelo previu 1 mas o real é 0."""
    y = _to_int_labels(y_true)
    p = _to_int_labels(y_pred)
    mascara = (y == 0) & (p == 1)
    return df.loc[mascara].reset_index(drop=True)


def extrair_falsos_negativos(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_pred: ArrayLike,
) -> pd.DataFrame:
    """Retorna as linhas de `df` onde o modelo previu 0 mas o real é 1."""
    y = _to_int_labels(y_true)
    p = _to_int_labels(y_pred)
    mascara = (y == 1) & (p == 0)
    return df.loc[mascara].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Métricas por grupo
# ---------------------------------------------------------------------------

def metricas_por_grupo(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_prob: ArrayLike,
    coluna_grupo: str,
    *,
    limiar: float = 0.5,
    min_n: int = 30,
) -> pd.DataFrame:
    """
    Métricas por categoria de `coluna_grupo` (ex.: "sg_uf", "cs_sexo").

    Ignora grupos com menos de `min_n` amostras (evita métricas instáveis).

    Colunas: grupo, n, taxa_positivos, auc, f1, precision, recall.
    """
    if coluna_grupo not in df.columns:
        raise KeyError(f"Coluna de grupo ausente: {coluna_grupo!r}")

    y = _to_int_labels(y_true)
    p = _to_np(y_prob)

    if len(df) != len(y):
        raise ValueError(
            f"df tem {len(df)} linhas e y_true tem {len(y)}."
        )

    # zera o índice para casar com arrays
    base = df.reset_index(drop=True)
    grupos = base[coluna_grupo].astype("string")

    linhas: list[dict[str, float | str]] = []
    for g in grupos.dropna().unique():
        m = (grupos == g).to_numpy()
        n = int(m.sum())
        if n < min_n:
            continue

        y_g = y[m]
        p_g = p[m]
        y_pred = (p_g >= limiar).astype(int)

        # AUC só faz sentido se houver as duas classes
        if len(np.unique(y_g)) < 2:
            auc_g = float("nan")
        else:
            auc_g = auc(y_g, p_g)

        linhas.append({
            "grupo":          str(g),
            "n":              float(n),
            "taxa_positivos": float(y_g.mean()),
            "auc":            auc_g,
            "f1":             f1(y_g, y_pred),
            "precision":      precision(y_g, y_pred),
            "recall":         recall(y_g, y_pred),
        })

    return pd.DataFrame(linhas).sort_values("n", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Top-N piores erros
# ---------------------------------------------------------------------------

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
    Retorna as N linhas de `df` com os piores erros.

    Parâmetros
    ----------
    criterio : {"fp", "fn", "erro_absoluto"}
        - "fp"            → ordena por prob decrescente entre FP
        - "fn"            → ordena por prob crescente entre FN
        - "erro_absoluto" → ordena por |prob − y| decrescente (todos os erros)

    Adiciona colunas: `y_true`, `y_prob`, `y_pred`, `erro_abs`.
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)
    y_pred = (p >= limiar).astype(int)

    if len(df) != len(y):
        raise ValueError(
            f"df tem {len(df)} linhas e y_true tem {len(y)}."
        )

    out = df.reset_index(drop=True).copy()
    out["y_true"] = y
    out["y_prob"] = p
    out["y_pred"] = y_pred
    out["erro_abs"] = np.abs(p - y)

    if criterio == "fp":
        sel = out[(out["y_true"] == 0) & (out["y_pred"] == 1)]
        sel = sel.sort_values("y_prob", ascending=False)
    elif criterio == "fn":
        sel = out[(out["y_true"] == 1) & (out["y_pred"] == 0)]
        sel = sel.sort_values("y_prob", ascending=True)
    elif criterio == "erro_absoluto":
        sel = out[out["y_true"] != out["y_pred"]]
        sel = sel.sort_values("erro_abs", ascending=False)
    else:
        raise ValueError(
            f"criterio inválido: {criterio!r}. "
            f"Use 'fp', 'fn' ou 'erro_absoluto'."
        )

    return sel.head(n).reset_index(drop=True)