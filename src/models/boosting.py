"""
Gradient boosting — `HistGradientBoostingClassifier` (nativo do sklearn).

Requisitos de versão do scikit-learn:
    - `class_weight` (incluindo "balanced") foi adicionado na versão 1.2.
    - `class_weight` como dict também foi adicionado na versão 1.2.

Nota: o default de `early_stopping` neste módulo é `False` (e não o
default `'auto'` do sklearn) para alinhar com a decisão metodológica do
projeto: sem early stopping interno, o número de iterações é escolhido na
validação temporal (gate G5).
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
    early_stopping: bool = False,
    validation_fraction: float = 0.1,
    n_iter_no_change: int = 20,
    class_weight: str | dict | None = "balanced",
    preprocessor=None,
) -> Pipeline:
    """
    Constrói um `Pipeline` com pré-processamento +
    `HistGradientBoostingClassifier`.

    Parâmetros
    ----------
    learning_rate : float
        Fator multiplicativo aplicado às folhas (shrinkage).
    max_iter : int
        Número máximo de iterações (árvores) do boosting.
    max_depth : int | None
        Profundidade máxima das árvores. None = sem limite explícito.
    max_leaf_nodes : int
        Número máximo de folhas por árvore.
    min_samples_leaf : int
        Mínimo de amostras por folha.
    l2_regularization : float
        Força da regularização L2.
    early_stopping : bool
        Se True, usa early stopping interno com `validation_fraction` do
        treino. Default `False` neste projeto: a escolha de `max_iter` é
        feita na validação temporal (gate G5), não internamente.
    validation_fraction : float
        Fração do treino reservada para early stopping (ignorada se
        `early_stopping=False`).
    n_iter_no_change : int
        Paciência do early stopping (ignorada se `early_stopping=False`).
    class_weight : str | dict | None
        Pesos das classes. `"balanced"` ajusta automaticamente.
    preprocessor : ColumnTransformer | None
        Se None, usa `build_preprocessor()`.
    """
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