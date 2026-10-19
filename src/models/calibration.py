"""
Calibração de probabilidades e escolha de limiar de decisão.

``calibrar`` envolve um ``Pipeline`` já ajustado em
``CalibratedClassifierCV`` com ``FrozenEstimator`` — o pipeline base
não é re-treinado. ``escolher_limiar`` varre uma grade de limiares e
devolve o ótimo segundo uma métrica, com restrições opcionais de
precision/recall.

Requer scikit-learn>=1.6 (``FrozenEstimator``); o projeto fixa >=1.8
por causa da API de ``l1_ratio`` em ``src/models/logistic.py``.

A agregação de métricas vive em ``src.evaluation.metrics``.
"""

from __future__ import annotations

from importlib import metadata
from typing import Any, Literal, get_args

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, roc_auc_score

from src.evaluation.metrics import metricas_por_limiar

__all__ = [
    "MetodoCalibracao",
    "Metrica",
    "calibrar",
    "escolher_limiar",
]

Metrica          = Literal["f1", "precision", "recall", "accuracy", "youden_j"]
MetodoCalibracao = Literal["isotonic", "sigmoid"]

_METRICAS_VALIDAS = frozenset(get_args(Metrica))
_METODOS_VALIDOS  = frozenset(get_args(MetodoCalibracao))


def calibrar(
    pipeline,
    X_cal: pd.DataFrame,
    y_cal: pd.Series,
    *,
    method: MetodoCalibracao = "isotonic",
):
    """Ajusta um ``CalibratedClassifierCV`` sobre um pipeline congelado.

    Use uma base de calibração distinta do treino do ``pipeline``. O
    pipeline não é re-treinado — o calibrador aprende só o mapeamento
    probabilidade → probabilidade.

    ``"isotonic"`` é não-paramétrico (requer mais dados); ``"sigmoid"``
    (Platt) é paramétrico e mais estável em amostras pequenas.

    Levanta ``RuntimeError`` se ``sklearn.frozen`` não estiver disponível
    (scikit-learn anterior a 1.6).
    """
    if method not in _METODOS_VALIDOS:
        raise ValueError(
            f"method inválido: {method!r}. Use {sorted(_METODOS_VALIDOS)}."
        )

    try:
        from sklearn.frozen import FrozenEstimator
    except ImportError as exc:
        try:
            instalada = metadata.version("scikit-learn")
        except metadata.PackageNotFoundError:
            instalada = "não instalado"

        raise RuntimeError(
            "calibrar() requer scikit-learn>=1.6 (FrozenEstimator); "
            f"o projeto exige >=1.8. Versão instalada: {instalada}. "
            "Atualize: pip install \"scikit-learn>=1.8\""
        ) from exc

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
    """Devolve o limiar ótimo segundo ``metrica`` e um resumo associado.

    Restrições opcionais de ``min_precision`` / ``min_recall`` filtram
    candidatos antes de maximizar ``metrica``; se nada sobrar, levanta
    ``ValueError``.

    Retorna dict com ``limiar``, ``valor`` (da métrica escolhida),
    ``metrica``, ``auc``, ``brier`` e ``tabela`` (grade completa de
    ``metricas_por_limiar``).
    """
    if metrica not in _METRICAS_VALIDAS:
        raise ValueError(
            f"metrica inválida: {metrica!r}. Use {sorted(_METRICAS_VALIDAS)}."
        )

    y_true_arr = np.asarray(y_true).ravel().astype(int)
    y_prob_arr = np.asarray(y_prob).ravel()

    tabela = metricas_por_limiar(y_true_arr, y_prob_arr, n_limiares=n_limiares)

    candidatos = tabela
    filtros: list[str] = []
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
            f"A métrica {metrica!r} não foi produzida por metricas_por_limiar. "
            f"Colunas disponíveis: {sorted(candidatos.columns)}"
        )

    idx_melhor   = candidatos[metrica].idxmax()
    linha_melhor = tabela.loc[[idx_melhor]].iloc[0]

    return {
        "limiar":  float(linha_melhor["limiar"]),
        "valor":   float(linha_melhor[metrica]),
        "metrica": metrica,
        "auc":     float(roc_auc_score(y_true_arr, y_prob_arr)),
        "brier":   float(brier_score_loss(y_true_arr, y_prob_arr)),
        "tabela":  tabela,
    }