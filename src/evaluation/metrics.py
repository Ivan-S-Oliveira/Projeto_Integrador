"""
Métricas de classificação binária — todas retornam `float`.

Motivo: o scikit-learn retorna `Float | ndarray` para várias métricas,
o que faz o Pylance reclamar. Aqui a gente encapsula e garante `float`.

Também oferece:
    - `metricas_por_limiar` → tabela varrendo limiares
    - `ic_bootstrap`        → intervalo de confiança por bootstrap
"""

from __future__ import annotations

from typing import Callable, Union

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

__all__ = [
    "ArrayLike",
    "auc",
    "average_precision",
    "brier",
    "f1",
    "precision",
    "recall",
    "accuracy",
    "metricas_completas",
    "metricas_por_limiar",
    "ic_bootstrap",
]


# ---------------------------------------------------------------------------
# Tipos auxiliares
# ---------------------------------------------------------------------------

ArrayLike = Union[np.ndarray, pd.Series, list]


def _to_np(x: ArrayLike) -> np.ndarray:
    return np.asarray(x).ravel()


def _to_int_labels(y: ArrayLike) -> np.ndarray:
    return np.asarray(y).ravel().astype(int)


# ---------------------------------------------------------------------------
# Métricas individuais (retornam float)
# ---------------------------------------------------------------------------

def auc(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(roc_auc_score(_to_int_labels(y_true), _to_np(y_prob)))


def average_precision(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(average_precision_score(_to_int_labels(y_true), _to_np(y_prob)))


def brier(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(brier_score_loss(_to_int_labels(y_true), _to_np(y_prob)))


def f1(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(f1_score(_to_int_labels(y_true), _to_int_labels(y_pred), zero_division=0))


def precision(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(precision_score(_to_int_labels(y_true), _to_int_labels(y_pred), zero_division=0))


def recall(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(recall_score(_to_int_labels(y_true), _to_int_labels(y_pred), zero_division=0))


def accuracy(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(accuracy_score(_to_int_labels(y_true), _to_int_labels(y_pred)))


# ---------------------------------------------------------------------------
# Resumo completo
# ---------------------------------------------------------------------------

def metricas_completas(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    limiar: float = 0.5,
) -> dict[str, float]:
    """
    Retorna um dict com AUC, AP, Brier, F1, precision, recall e accuracy.
    Pronto para `Run.metrica(**d)`.
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)
    y_pred = (p >= limiar).astype(int)

    return {
        "auc":       auc(y, p),
        "ap":        average_precision(y, p),
        "brier":     brier(y, p),
        "f1":        f1(y, y_pred),
        "precision": precision(y, y_pred),
        "recall":    recall(y, y_pred),
        "accuracy":  accuracy(y, y_pred),
        "limiar":    float(limiar),
        "n":         float(len(y)),
    }


# ---------------------------------------------------------------------------
# Varredura de limiar
# ---------------------------------------------------------------------------

def metricas_por_limiar(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_limiares: int = 101,
) -> pd.DataFrame:
    """
    Tabela com métricas para cada limiar em [0.01, 0.99].

    Colunas: limiar, f1, precision, recall, accuracy.

    Usa as métricas deste próprio módulo (`f1`, `precision`, `recall`,
    `accuracy`) — não há tabela paralela de lambdas.
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)

    linhas: list[dict[str, float]] = []
    for th in np.linspace(0.01, 0.99, n_limiares):
        y_pred = (p >= float(th)).astype(int)
        linhas.append({
            "limiar":    float(th),
            "f1":        f1(y, y_pred),
            "precision": precision(y, y_pred),
            "recall":    recall(y, y_pred),
            "accuracy":  accuracy(y, y_pred),
        })

    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def ic_bootstrap(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    *,
    metrica: Callable[[ArrayLike, ArrayLike], float] = auc,
    n_boot: int = 200,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float, float]:
    """
    Intervalo de confiança via bootstrap percentil.

    Retorna (estimativa, limite_inferior, limite_superior).

    Parâmetros
    ----------
    metrica : callable(y_true, y_prob) -> float
        Função de métrica. Default: `auc`.
    n_boot : int
        Número de reamostragens.
    alpha : float
        Nível de significância (0.05 → IC 95%).
    seed : int
        Semente para reprodutibilidade.
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)

    rng = np.random.default_rng(seed)
    n = len(y)
    valores = np.empty(n_boot, dtype="float64")

    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        valores[i] = metrica(y[idx], p[idx])

    est = float(metrica(y, p))
    inf = float(np.quantile(valores, alpha / 2))
    sup = float(np.quantile(valores, 1 - alpha / 2))
    return est, inf, sup