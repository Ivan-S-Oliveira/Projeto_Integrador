"""
Baseline: `DummyClassifier` — referência mínima.

Serve para responder: "o modelo aprendeu algo além da classe majoritária?"

Se o AUC do baseline ≈ 0.5 e a acurácia ≈ frequência da classe majoritária,
qualquer modelo com desempenho acima disso está efetivamente aprendendo.
"""

from __future__ import annotations

from typing import Literal

from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline

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