"""
Calibração de probabilidades e escolha de limiar de decisão.

Concentra as operações na fronteira entre modelo e decisão operacional:
envolver um `Pipeline` já ajustado em `CalibratedClassifierCV` com uma base
de calibração dedicada, e escolher o limiar de decisão ótimo segundo uma
métrica (opcionalmente sujeito a precisão/recall mínimos).

Toda a agregação de métricas vive em `src.evaluation`.
"""

from __future__ import annotations

from typing import Any, Literal, get_args

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, roc_auc_score

from src.evaluation.metrics import metricas_por_limiar

__all__ = [
    "Metrica",
    "calibrar",
    "escolher_limiar",
]

Metrica = Literal["f1", "precision", "recall", "accuracy", "youden_j"]
_METRICAS_VALIDAS: tuple[str, ...] = get_args(Metrica)


def calibrar(
    pipeline,
    X_cal: pd.DataFrame,
    y_cal: pd.Series,
    *,
    method: str = "isotonic",
):
    """
    Envolve um `Pipeline` já ajustado em `CalibratedClassifierCV`.

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


def escolher_limiar(
    y_true: pd.Series | np.ndarray,
    y_prob: pd.Series | np.ndarray,
    *,
    metrica: Metrica = "f1",
    n_limiares: int = 101,
    min_precision: float | None = None,
    min_recall: float | None = None,
) -> dict[str, Any]:
    """
    Varre uma grade de limiares e devolve o ótimo segundo `metrica`.

    A tabela completa de métricas por limiar vem de
    `src.evaluation.metrics.metricas_por_limiar`; este módulo apenas
    filtra, ranqueia e devolve o resumo.

    Parâmetros
    ----------
    y_true, y_prob :
        Rótulos verdadeiros (0/1) e probabilidades preditas em [0, 1].
    metrica : {"f1", "precision", "recall", "accuracy", "youden_j"}
        Métrica maximizada na escolha do limiar. `"youden_j"` corresponde a
        `recall + especificidade − 1`, critério citado em `decisoes.md`.
    n_limiares : int
        Número de limiares avaliados, linearmente espaçados em (0.01, 0.99).
    min_precision : float | None
        Se informado, restringe os candidatos a limiares cuja precision
        seja ≥ `min_precision` antes de maximizar `metrica`.
    min_recall : float | None
        Se informado, restringe os candidatos a limiares cujo recall seja
        ≥ `min_recall` antes de maximizar `metrica`. Pode ser combinado com
        `min_precision`; se nenhum candidato satisfizer o conjunto de
        restrições, levanta `ValueError`.

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
    if metrica not in _METRICAS_VALIDAS:
        raise ValueError(
            f"metrica inválida: {metrica!r}. Use {list(_METRICAS_VALIDAS)}."
        )

    y_true_arr = np.asarray(y_true).ravel().astype(int)
    y_prob_arr = np.asarray(y_prob).ravel()

    tabela = metricas_por_limiar(y_true_arr, y_prob_arr, n_limiares=n_limiares)

    filtros: list[str] = []
    candidatos = tabela
    if min_precision is not None:
        filtros.append(f"precision ≥ {min_precision}")
        candidatos = candidatos[candidatos["precision"] >= min_precision]
    if min_recall is not None:
        filtros.append(f"recall ≥ {min_recall}")
        candidatos = candidatos[candidatos["recall"] >= min_recall]
    if candidatos.empty:
        restricao = " e ".join(filtros) if filtros else "sem restrição"
        raise ValueError(f"Nenhum limiar atende à(s) restrição(ões): {restricao}.")

    if metrica not in candidatos.columns:
        raise ValueError(
            f"A métrica {metrica!r} não foi produzida por "
            f"metricas_por_limiar. Colunas disponíveis: "
            f"{sorted(candidatos.columns)}"
        )

    idx_melhor = candidatos[metrica].idxmax()
    linha_melhor = tabela.loc[[idx_melhor]].iloc[0]

    return {
        "limiar":  float(linha_melhor["limiar"]),
        "valor":   float(linha_melhor[metrica]),
        "metrica": metrica,
        "auc":     float(roc_auc_score(y_true_arr, y_prob_arr)),
        "brier":   float(brier_score_loss(y_true_arr, y_prob_arr)),
        "tabela":  tabela,
    }