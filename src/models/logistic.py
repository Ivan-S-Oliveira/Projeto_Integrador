"""
Regressão logística — modelo linear interpretável.

A partir do scikit-learn 1.8, `penalty` foi depreciado (remoção prevista
para 1.10) em favor de `l1_ratio`:

    - `l1_ratio=0.0`     → L2 (default histórico)
    - `l1_ratio=1.0`     → L1
    - `0 < l1_ratio < 1` → elastic-net (requer solver `saga`)

A chave `models.logistic.penalty` do `supervised.yaml` (`"l1"`, `"l2"` ou
`"elasticnet"`) é traduzida para o `l1_ratio` equivalente, mantendo a
config como fonte única da verdade sem depender da API depreciada.
"""

from __future__ import annotations

from typing import Literal

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.models.pipeline import build_preprocessor, random_state
from src.utils import config as C

Solver = Literal[
    "lbfgs", "liblinear", "newton-cg", "newton-cholesky", "sag", "saga"
]
Penalty = Literal["l1", "l2", "elasticnet"]

_L1_RATIO_SOLVERS: dict[str, set[str]] = {
    "l2":         {"lbfgs", "liblinear", "newton-cg", "newton-cholesky", "sag", "saga"},
    "l1":         {"liblinear", "saga"},
    "elasticnet": {"saga"},
}


def _penalty_do_yaml() -> Penalty | None:
    """
    Lê `models.logistic.penalty` do `supervised.yaml`.

    Retorna None quando a chave estiver ausente, vazia ou nula — nesse
    caso o `l1_ratio` passado explicitamente é usado sem alteração.
    """
    try:
        valor = C.cfg("models", "logistic", "penalty")
    except (KeyError, TypeError):
        return None
    if not valor:
        return None
    if valor not in ("l1", "l2", "elasticnet"):
        raise ValueError(
            f"models.logistic.penalty inválido: {valor!r}. "
            "Use 'l1', 'l2' ou 'elasticnet'."
        )
    return valor  # type: ignore[return-value]


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
    """
    Constrói um `Pipeline` com pré-processamento + `LogisticRegression`.

    Parâmetros
    ----------
    C : float
        Inverso da força de regularização. Valores menores → regularização
        mais forte.
    l1_ratio : float
        Controle da mistura L1/L2 (0 ≤ l1_ratio ≤ 1):
            - 0.0 → L2 puro (default)
            - 1.0 → L1 puro
            - 0 < l1_ratio < 1 → elastic-net
        Só tem efeito quando `penalty` (explícito ou do YAML) é None ou
        `"elasticnet"`.
    penalty : {"l1", "l2", "elasticnet"} | None
        Penalidade declarada na config. Quando None, lê
        `logistic.penalty` do `supervised.yaml`. Se definida, sobrepõe
        `l1_ratio`:
            - `"l2"` → força `l1_ratio=0.0`
            - `"l1"` → força `l1_ratio=1.0`
            - `"elasticnet"` → exige `0 < l1_ratio < 1` (o valor do YAML
              permanece)
    solver : Solver
        Algoritmo de otimização. Precisa ser compatível com `l1_ratio`.
    max_iter : int
        Número máximo de iterações do solver.
    class_weight : str | dict | None
        Pesos das classes. `"balanced"` ajusta automaticamente pelo
        inverso da frequência.
    preprocessor : ColumnTransformer | None
        Se None, usa `build_preprocessor()`.

    Levanta
    ------
    ValueError
        Se `l1_ratio` estiver fora de [0, 1], se a combinação
        `l1_ratio` × `solver` for inválida, ou se `penalty="elasticnet"`
        vier acompanhado de `l1_ratio` nos extremos (0 ou 1).
    """
    if penalty is None:
        penalty = _penalty_do_yaml()

    if penalty == "l2":
        l1_ratio = 0.0
    elif penalty == "l1":
        l1_ratio = 1.0
    elif penalty == "elasticnet" and not (0.0 < l1_ratio < 1.0):
        raise ValueError(
            f"penalty='elasticnet' requer 0 < l1_ratio < 1; "
            f"recebido l1_ratio={l1_ratio!r}."
        )

    if not (0.0 <= l1_ratio <= 1.0):
        raise ValueError(f"l1_ratio deve estar em [0, 1]; recebido {l1_ratio!r}.")

    tipo = "l2" if l1_ratio == 0.0 else "l1" if l1_ratio == 1.0 else "elasticnet"

    solvers_validos = _L1_RATIO_SOLVERS[tipo]
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