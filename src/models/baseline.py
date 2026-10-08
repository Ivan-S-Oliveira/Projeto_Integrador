"""
Baseline: `DummyClassifier` — referência mínima.

Serve para responder: "o modelo aprendeu algo além da classe majoritária?"

Se o AUC do baseline ≈ 0.5 e a acurácia ≈ frequência da classe majoritária,
qualquer modelo com desempenho acima disso está efetivamente aprendendo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score

from src.evaluation.metrics import metricas_completas, average_precision

from typing import Literal

from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline

from src.models.calibration import metricas_completas
from src.models.pipeline import build_preprocessor, random_state

# Estratégias aceitas pelo DummyClassifier do scikit-learn.
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
    """
    Retorna um `Pipeline` com `DummyClassifier`.

    Parâmetros
    ----------
    strategy : DummyStrategy
        Estratégia do DummyClassifier. Recomendadas:
            - "prior"        : prediz a frequência das classes (baseline AUC)
            - "most_frequent": prediz sempre a classe majoritária (baseline acc)
            - "stratified"   : prediz aleatoriamente respeitando o prior
    preprocessor : ColumnTransformer | None
        Se None, usa `build_preprocessor()`.
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
    """
    Treina um DummyClassifier em (X_train, y_train) e avalia em (X_eval, y_eval).

    Retorna dict com AUC, AP, Brier, F1, precision, recall, accuracy.
    Serve como piso: qualquer modelo real precisa superar isto.

    Nota
    ----
    - strategy="prior"        → probabilidade constante = prevalência do treino
                                (AUC ≈ 0.5 por construção, mas Brier informativo)
    - strategy="most_frequent"→ prevê sempre a classe majoritária
                                (F1/recall = 0 se a positiva for minoria)
    """
    pipe = build_baseline_pipeline(strategy=strategy)
    pipe.fit(X_train, y_train)

    y_prob = pipe.predict_proba(X_eval)[:, 1]
    y_pred = pipe.predict(X_eval)

    return {
        "strategy": strategy,
        **metricas_completas(y_eval, y_prob, limiar=0.5),
    }