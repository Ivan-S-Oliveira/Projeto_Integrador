"""
Calibração de probabilidades e escolha de limiar de decisão.

Este módulo concentra as operações que vivem na fronteira entre modelo e
decisão operacional:

- `calibrar`: envolve um `Pipeline` **já ajustado** em
  `CalibratedClassifierCV` (via `FrozenEstimator`), ajustando o calibrador
  em uma base separada (`X_cal`, `y_cal`) — nunca no mesmo conjunto usado
  para treinar o modelo base.

- `escolher_limiar`: varre uma grade de limiares, reporta a tabela completa
  de métricas (f1, precision, recall, accuracy) e devolve o limiar ótimo
  segundo a métrica escolhida, opcionalmente sujeito a uma precisão mínima.

Funções de diagnóstico e agregação de métricas vivem em `src.evaluation`
(fonte única). `curva_confiabilidade` e `metricas_completas` são
reexportadas aqui apenas por compatibilidade — não há implementação local.
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

# Reexportados de `src.evaluation` — não reimplementar aqui.
from src.evaluation.calibration import curva_confiabilidade
from src.evaluation.metrics import metricas_completas

__all__ = [
    "Metrica",
    "calibrar",
    "escolher_limiar",
    # reexports
    "curva_confiabilidade",
    "metricas_completas",
]


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
):
    """
    Envolve um `Pipeline` **já ajustado** em `CalibratedClassifierCV`.

    O pipeline base é congelado com `FrozenEstimator`, de modo que o
    calibrador aprende apenas o mapeamento probabilidade → probabilidade
    calibrada, sem re-treinar o estimador subjacente. Use uma base de
    calibração (`X_cal`, `y_cal`) distinta da base de treino do pipeline.

    Parâmetros
    ----------
    pipeline :
        Estimador já ajustado (p.ex. `Pipeline` de pré-processamento +
        classificador). Não é re-treinado.
    X_cal, y_cal :
        Base de calibração. Não deve ser o mesmo conjunto usado no fit do
        `pipeline`, sob pena de o calibrador herdar o overfit do modelo.
    method : {"isotonic", "sigmoid"}
        Método de calibração. `"isotonic"` é não-paramétrico e requer mais
        dados; `"sigmoid"` (Platt) é paramétrico e mais estável em amostras
        pequenas.

    Retorno
    -------
    `CalibratedClassifierCV` já ajustado, pronto para `predict_proba`.

    Requer scikit-learn >= 1.6 (`sklearn.frozen.FrozenEstimator`).
    """
    if method not in ("isotonic", "sigmoid"):
        raise ValueError(f"method inválido: {method!r}")

    from sklearn.frozen import FrozenEstimator  # sklearn >= 1.6

    modelo = CalibratedClassifierCV(
        estimator=FrozenEstimator(pipeline),
        method=method,
    )
    modelo.fit(X_cal, y_cal)
    return modelo


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
    """
    Varre uma grade de limiares e devolve o ótimo segundo `metrica`.

    Parâmetros
    ----------
    y_true, y_prob :
        Rótulos verdadeiros (0/1) e probabilidades preditas em [0, 1].
    metrica : {"f1", "precision", "recall", "accuracy"}
        Métrica maximizada na escolha do limiar.
    n_limiares : int
        Número de limiares avaliados, linearmente espaçados em (0.01, 0.99).
    min_precision : float | None
        Se informado, restringe os candidatos a limiares cuja precision
        seja ≥ `min_precision` antes de maximizar `metrica`. Se nenhum
        candidato satisfizer, levanta `ValueError`.

    Retorno
    -------
    dict com:
        - `limiar`  : float — limiar ótimo.
        - `valor`   : float — valor da métrica escolhida no ótimo.
        - `metrica` : str   — métrica usada.
        - `auc`     : float — ROC-AUC no conjunto avaliado.
        - `brier`   : float — Brier score no conjunto avaliado.
        - `tabela`  : `pd.DataFrame` — grade completa com todas as métricas.
    """
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