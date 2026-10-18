"""
Regressão logística — modelo linear interpretável.

A partir do scikit-learn 1.8, ``penalty`` foi depreciado (remoção prevista
para 1.10) em favor de ``l1_ratio``. A chave ``models.logistic.penalty``
do ``supervised.yaml`` (``"l1"``, ``"l2"`` ou ``"elasticnet"``) é
traduzida para o ``l1_ratio`` equivalente, mantendo a config como fonte
única da verdade sem depender da API depreciada.
"""

from __future__ import annotations

from typing import Literal, cast

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.models.pipeline import build_preprocessor, random_state
from src.utils import config as C

__all__ = ["Penalty", "Solver", "build_logistic_pipeline"]

Solver  = Literal["lbfgs", "liblinear", "newton-cg", "newton-cholesky", "sag", "saga"]
Penalty = Literal["l1", "l2", "elasticnet"]

# Solver × tipo de penalidade efetivo (derivado do l1_ratio final).
_L1_RATIO_SOLVERS: dict[str, frozenset[str]] = {
    "l2":         frozenset({"lbfgs", "liblinear", "newton-cg", "newton-cholesky", "sag", "saga"}),
    "l1":         frozenset({"liblinear", "saga"}),
    "elasticnet": frozenset({"saga"}),
}

_PENALTIES_VALIDAS = ("l1", "l2", "elasticnet")


def _penalty_do_yaml() -> Penalty | None:
    """Lê ``models.logistic.penalty`` do YAML.

    Devolve ``None`` quando a chave está ausente, vazia ou nula — o
    ``l1_ratio`` passado explicitamente é usado sem alteração. Levanta
    ``ValueError`` se a chave existir mas tiver valor desconhecido.
    """
    valor = C.cfg("models", "logistic", "penalty")
    if not valor:
        return None
    if valor not in _PENALTIES_VALIDAS:
        raise ValueError(
            f"models.logistic.penalty inválido: {valor!r}. "
            f"Use uma de {_PENALTIES_VALIDAS}."
        )
    return cast(Penalty, valor)


def _tipo_penalidade(l1_ratio: float) -> str:
    """Classifica o ``l1_ratio`` em ``"l2"``, ``"l1"`` ou ``"elasticnet"``."""
    if l1_ratio == 0.0:
        return "l2"
    if l1_ratio == 1.0:
        return "l1"
    return "elasticnet"


def build_logistic_pipeline(
    *,
    C: float = 1.0,
    l1_ratio: float = 0.0,
    penalty: Penalty | None = None,
    solver: Solver = "lbfgs",
    max_iter: int = 1000,
    class_weight: str | dict | None = "balanced",
    preprocessor=None,
) -> Pipeline:
    """``Pipeline`` de pré-processamento + ``LogisticRegression``.

    ``penalty=None`` (default) lê ``models.logistic.penalty`` do YAML.
    Quando definido, sobrepõe ``l1_ratio``:

    - ``"l2"``          → força ``l1_ratio=0.0``;
    - ``"l1"``          → força ``l1_ratio=1.0``;
    - ``"elasticnet"``  → exige ``0 < l1_ratio < 1``.

    ``l1_ratio`` (0..1) só tem efeito quando ``penalty`` é ``None`` ou
    ``"elasticnet"``. O ``solver`` precisa ser compatível com o tipo
    resultante (ver ``_L1_RATIO_SOLVERS``).

    Levanta ``ValueError`` para ``l1_ratio`` fora de ``[0, 1]``,
    combinação ``solver`` × tipo inválida, ou ``penalty="elasticnet"``
    com ``l1_ratio`` nos extremos.
    """
    if not 0.0 <= l1_ratio <= 1.0:
        raise ValueError(
            f"l1_ratio deve estar em [0, 1]; "
            f"recebido {l1_ratio!r}."
        )

    penalty_configurada = penalty

    if penalty_configurada is None and l1_ratio == 0.0:
        penalty_configurada = _penalty_do_yaml()

    if penalty_configurada == "l2":
        l1_ratio = 0.0

    elif penalty_configurada == "l1":
        l1_ratio = 1.0

    elif penalty_configurada == "elasticnet":
        if not 0.0 < l1_ratio < 1.0:
            raise ValueError(
                "penalty='elasticnet' requer "
                "0 < l1_ratio < 1; "
                f"recebido l1_ratio={l1_ratio!r}."
            )

    tipo             = _tipo_penalidade(l1_ratio)
    solvers_validos  = _L1_RATIO_SOLVERS[tipo]
    if solver not in solvers_validos:
        raise ValueError(
            f"combinação inválida: l1_ratio={l1_ratio!r} ({tipo}) "
            f"com solver={solver!r}. Use um destes: {sorted(solvers_validos)}."
        )

    pre = preprocessor if preprocessor is not None else build_preprocessor()

    return Pipeline([
        ("pre", pre),
        ("clf", LogisticRegression(
            C=C,
            l1_ratio=l1_ratio,
            solver=solver,
            max_iter=max_iter,
            class_weight=class_weight,
            random_state=random_state(),
        )),
    ])