"""
Regressão logística — modelo linear interpretável.
...
"""

from __future__ import annotations

from typing import Literal

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.models.pipeline import build_preprocessor, random_state

Penalty = Literal["l1", "l2", "elasticnet", None]
Solver = Literal[
    "lbfgs", "liblinear", "newton-cg", "newton-cholesky", "sag", "saga"
]

# Combinações penalty × solver suportadas pelo sklearn.
_PENALTY_SOLVERS: dict[str | None, set[str]] = {
    None:          {"lbfgs", "newton-cg", "newton-cholesky", "sag", "saga"},
    "l2":          {"lbfgs", "liblinear", "newton-cg", "newton-cholesky", "sag", "saga"},
    "l1":          {"liblinear", "saga"},
    "elasticnet":  {"saga"},
}


def build_logistic_pipeline(
    *,
    C: float = 1.0,
    penalty: Penalty = "l2",
    solver: Solver = "lbfgs",
    max_iter: int = 1000,
    class_weight: str | dict | None = "balanced",
    preprocessor=None,
) -> Pipeline:
    """..."""
    solvers_validos = _PENALTY_SOLVERS.get(penalty)
    if solvers_validos is None:
        raise ValueError(f"penalty inválido: {penalty!r}")
    if solver not in solvers_validos:
        raise ValueError(
            f"combinação inválida: penalty={penalty!r} com solver={solver!r}. "
            f"Use um destes: {sorted(solvers_validos)}."
        )

    if penalty == "elasticnet":
        raise NotImplementedError(
            "elasticnet exige `l1_ratio`; exponha esse parâmetro antes de usar."
        )

    pre = preprocessor if preprocessor is not None else build_preprocessor()

    return Pipeline([
        ("pre", pre),
        ("clf", LogisticRegression(
            C=C,
            penalty=penalty,
            solver=solver,
            max_iter=max_iter,
            class_weight=class_weight,
            random_state=random_state(),
        )),
    ])