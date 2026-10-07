"""
Gradient boosting — `HistGradientBoostingClassifier` (nativo do sklearn).

Requisitos:
    - scikit-learn >= 1.4 para `class_weight` (incluindo "balanced").
    - scikit-learn >= 1.2 apenas para `class_weight` como dict.
"""
from __future__ import annotations

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline

from src.models.pipeline import build_preprocessor, random_state


def build_boosting_pipeline(
    *,
    learning_rate: float = 0.05,
    max_iter: int = 500,
    max_depth: int | None = None,
    max_leaf_nodes: int = 31,
    min_samples_leaf: int = 20,
    l2_regularization: float = 0.0,
    early_stopping: bool = True,
    validation_fraction: float = 0.1,
    n_iter_no_change: int = 20,
    class_weight: str | dict | None = "balanced",
    preprocessor=None,
) -> Pipeline:
    pre = preprocessor if preprocessor is not None else build_preprocessor()

    clf = HistGradientBoostingClassifier(
        learning_rate=learning_rate,
        max_iter=max_iter,
        max_depth=max_depth,
        max_leaf_nodes=max_leaf_nodes,
        min_samples_leaf=min_samples_leaf,
        l2_regularization=l2_regularization,
        early_stopping=early_stopping,
        validation_fraction=validation_fraction,
        n_iter_no_change=n_iter_no_change,
        class_weight=class_weight,
        random_state=random_state(),
    )

    return Pipeline([("pre", pre), ("clf", clf)])