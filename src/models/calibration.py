"""
Calibração de probabilidades e escolha de limiar.
...
"""

from __future__ import annotations

from typing import Any, Callable, Literal

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


# Conjunto fechado de métricas suportadas em `escolher_limiar`.
Metrica = Literal["f1", "precision", "recall", "accuracy"]


# ---------------------------------------------------------------------------
# Calibração
# ---------------------------------------------------------------------------

def calibrar(
    pipeline,
    X_cal: pd.DataFrame,
    y_cal: pd.Series,
    *,
    method: str = "isotonic",
    cv: int | str | None = None,
):
    """
    Envolve um `Pipeline` JÁ AJUSTADO em `CalibratedClassifierCV`.

    Compatível com scikit-learn < 1.6 (usa `cv="prefit"`) e >= 1.6
    (usa `FrozenEstimator`).
    """
    if method not in ("isotonic", "sigmoid"):
        raise ValueError(f"method inválido: {method!r}")

    if cv is None or cv == "prefit":
        try:
            # scikit-learn >= 1.6
            from sklearn.frozen import FrozenEstimator  # type: ignore

            modelo = CalibratedClassifierCV(
                estimator=FrozenEstimator(pipeline),
                method=method,
            )
        except ImportError:
            # scikit-learn < 1.6
            modelo = CalibratedClassifierCV(
                estimator=pipeline,
                method=method,
                cv="prefit",
            )
    else:
        modelo = CalibratedClassifierCV(
            estimator=pipeline,
            method=method,
            cv=cv,
        )

    modelo.fit(X_cal, y_cal)
    return modelo


# ---------------------------------------------------------------------------
# Curva de confiabilidade
# ---------------------------------------------------------------------------

def curva_confiabilidade(
    y_true: pd.Series | np.ndarray,
    y_prob: pd.Series | np.ndarray,
    n_bins: int = 10,
) -> pd.DataFrame:
    """
    Dados para o reliability diagram.

    Bins meio-abertos à esquerda: `[0, 1/n], [1/n, 2/n), ..., [(n-1)/n, 1]`.
    """
    y_true = np.asarray(y_true).ravel()
    y_prob = np.asarray(y_prob).ravel()

    if not np.all((y_prob >= 0) & (y_prob <= 1)):
        raise ValueError("y_prob deve estar em [0, 1].")

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    # right=False → bins são [bins[i], bins[i+1]) — último recebe o 1.0 via clip.
    idx = np.clip(np.digitize(y_prob, bins[1:-1], right=False), 0, n_bins - 1)

    linhas = []
    for b in range(n_bins):
        mascara = idx == b
        n = int(mascara.sum())
        if n == 0:
            linhas.append({
                "bin_centro":    (bins[b] + bins[b + 1]) / 2,
                "freq_positiva": np.nan,
                "n":             0,
            })
        else:
            linhas.append({
                "bin_centro":    float(y_prob[mascara].mean()),
                "freq_positiva": float(y_true[mascara].mean()),
                "n":             n,
            })

    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# Escolha de limiar
# ---------------------------------------------------------------------------

# `float(...)` explícito dentro das lambdas resolve o typing do sklearn:
# os stubs declaram retorno como `Float | ndarray`, não `float`.
_METRICAS: dict[Metrica, Callable[[np.ndarray, np.ndarray], float]] = {
    "f1":        lambda y, p: float(f1_score(y, p, zero_division=0)),
    "precision": lambda y, p: float(precision_score(y, p, zero_division=0)),
    "recall":    lambda y, p: float(recall_score(y, p, zero_division=0)),
    "accuracy":  lambda y, p: float(accuracy_score(y, p)),
}


def escolher_limiar(
    y_true: pd.Series | np.ndarray,
    y_prob: pd.Series | np.ndarray,
    *,
    metrica: Metrica = "f1",
    n_limiares: int = 101,
    min_precision: float | None = None,
) -> dict[str, Any]:
    if metrica not in _METRICAS:
        raise ValueError(f"metrica inválida: {metrica!r}. Use {list(_METRICAS)}.")

    y_true_arr = np.asarray(y_true).ravel().astype(int)
    y_prob_arr = np.asarray(y_prob).ravel()

    linhas = []
    for th in np.linspace(0.01, 0.99, n_limiares):
        pred = (y_prob_arr >= th).astype(int)
        linhas.append({
            "limiar":    float(th),
            "f1":        _METRICAS["f1"](y_true_arr, pred),
            "precision": _METRICAS["precision"](y_true_arr, pred),
            "recall":    _METRICAS["recall"](y_true_arr, pred),
            "accuracy":  _METRICAS["accuracy"](y_true_arr, pred),
        })

    tabela = pd.DataFrame(linhas)

    candidatos = tabela
    if min_precision is not None:
        candidatos = candidatos[candidatos["precision"] >= min_precision]
        if candidatos.empty:
            raise ValueError(f"Nenhum limiar atinge precision ≥ {min_precision}.")

    # pandas-stubs ainda não resolvem `df[str]` como coluna única de forma
    # limpa. Montamos explicitamente o mapping de séries — cada chave é
    # vista pelo type checker e o `Literal` de `metrica` fecha o cerco.
    series: dict[Metrica, pd.Series] = {
        "f1":        candidatos["f1"],
        "precision": candidatos["precision"],
        "recall":    candidatos["recall"],
        "accuracy":  candidatos["accuracy"],
    }
    serie_metrica = series[metrica]
    melhor_idx = serie_metrica.idxmax()

    return {
        "limiar":  float(tabela.loc[melhor_idx, "limiar"]),
        "valor":   float(serie_metrica.loc[melhor_idx]),
        "metrica": metrica,
        "auc":     float(roc_auc_score(y_true_arr, y_prob_arr)),
        "brier":   float(brier_score_loss(y_true_arr, y_prob_arr)),
        "tabela":  tabela,
    }


# ---------------------------------------------------------------------------
# Conveniência
# ---------------------------------------------------------------------------

def metricas_completas(
    y_true: pd.Series | np.ndarray,
    y_prob: pd.Series | np.ndarray,
    limiar: float = 0.5,
) -> dict[str, float]:
    y_true_arr = np.asarray(y_true).ravel().astype(int)
    y_prob_arr = np.asarray(y_prob).ravel()
    pred = (y_prob_arr >= limiar).astype(int)

    return {
        "auc":       float(roc_auc_score(y_true_arr, y_prob_arr)),
        "brier":     float(brier_score_loss(y_true_arr, y_prob_arr)),
        "f1":        float(f1_score(y_true_arr, pred, zero_division=0)),
        "precision": float(precision_score(y_true_arr, pred, zero_division=0)),
        "recall":    float(recall_score(y_true_arr, pred, zero_division=0)),
        "accuracy":  float(accuracy_score(y_true_arr, pred)),
        "limiar":    float(limiar),
        "n":         int(len(y_true_arr)),
    }