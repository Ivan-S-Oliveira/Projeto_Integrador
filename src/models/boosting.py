"""Gradient boosting supervisionado do Projeto SRAG."""

from __future__ import annotations

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline

from src.models.pipeline import (
    FEATURES_CATEGORICAS,
    FEATURES_NUMERICAS,
    build_preprocessor,
    random_state,
)

__all__ = ["build_boosting_pipeline"]


def build_boosting_pipeline(
    learning_rate: float = 0.08,
    max_iter: int = 150,
    max_depth: int | None = None,
    max_leaf_nodes: int = 31,
    min_samples_leaf: int = 100,
    l2_regularization: float = 0.10,
    early_stopping: bool = True,
    validation_fraction: float = 0.1,
    n_iter_no_change: int = 20,
    class_weight: str | dict | None = "balanced",
    preprocessor=None,
) -> Pipeline:
    """Constrói o pipeline ordinal do HistGradientBoostingClassifier."""

    categorical_features = None

    if preprocessor is None:
        preprocessor = build_preprocessor(
            numericas=FEATURES_NUMERICAS,
            categoricas=FEATURES_CATEGORICAS,
            saida="ordinal",
        )

        categorical_features = [
            False
            for _ in FEATURES_NUMERICAS
        ]

        categorical_features.extend(
            True
            for _ in FEATURES_CATEGORICAS
        )

    if categorical_features is not None:
        quantidade_features_esperada = sum(
            (
                len(FEATURES_NUMERICAS),
                len(FEATURES_CATEGORICAS),
            )
        )

        if len(categorical_features) != quantidade_features_esperada:
            raise RuntimeError(
                "A máscara categórica não possui o mesmo tamanho "
                "do contrato de features."
            )

    classificador = HistGradientBoostingClassifier(
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
        categorical_features=categorical_features,
        random_state=random_state(),
    )

    return Pipeline(
        steps=[
            ("pre", preprocessor),
            ("clf", classificador),
        ]
    )
