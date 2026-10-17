"""
Baseline: ``DummyClassifier`` — piso mínimo de desempenho.

Serve para responder: "o modelo aprendeu algo além da classe majoritária?"
O piso efetivo depende de ``strategy`` — ver ``build_baseline_pipeline``.
"""
from __future__ import annotations

from typing import Literal

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline

from src.evaluation.metrics import metricas_completas
from src.models.pipeline import build_preprocessor, random_state

DummyStrategy = Literal[
    "most_frequent",
    "prior",
    "stratified",
    "uniform",
    "constant",
]


def build_baseline_pipeline(
    *,
    strategy: DummyStrategy = "prior",
    preprocessor=None,
) -> Pipeline:
    """``Pipeline`` com pré-processamento + ``DummyClassifier``.

    Estratégias mais úteis como piso:

    - ``"prior"``         → probabilidade constante = prevalência do treino
      (AUC ≈ 0.5 por construção; Brier ainda informativo);
    - ``"most_frequent"`` → sempre a classe majoritária
      (F1/recall = 0 se a positiva for minoria);
    - ``"stratified"``    → amostra respeitando o prior.

    ``preprocessor=None`` usa ``build_preprocessor()``.
    """
    pre = preprocessor if preprocessor is not None else build_preprocessor()

    return Pipeline([
        ("pre", pre),
        ("clf", DummyClassifier(
            strategy=strategy,
            random_state=random_state(),
        )),
    ])


def evaluate_baseline(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_eval: pd.DataFrame,
    y_eval: pd.Series,
    *,
    strategy: DummyStrategy = "prior",
) -> dict[str, str | float]:
    """Treina e avalia um ``DummyClassifier`` — devolve o dict de métricas.

    O dict inclui ``strategy`` (a escolhida) mais todas as chaves de
    ``metricas_completas`` — ver esse módulo para a lista completa.
    """
    pipe = build_baseline_pipeline(strategy=strategy)
    pipe.fit(X_train, y_train)
    y_prob = pipe.predict_proba(X_eval)[:, 1]

    return {
        "strategy": strategy,
        **metricas_completas(y_eval, y_prob, limiar=0.5),
    }