"""
Regressão logística — modelo linear interpretável.

A partir do scikit-learn 1.8, o parâmetro `penalty` foi depreciado e será
removido na versão 1.10. O controle de regularização passou a ser feito via
`l1_ratio`:

    - `l1_ratio=0.0` → penalidade L2 (default histórico)
    - `l1_ratio=1.0` → penalidade L1
    - `0 < l1_ratio < 1` → elastic-net (requer solver `saga`)

Este módulo usa `l1_ratio` diretamente e valida a compatibilidade com o
`solver` escolhido.

A chave `logistic.penalty` do `supervised.yaml` (`"l1"`, `"l2"` ou
`"elasticnet"`) é traduzida para o `l1_ratio` equivalente, de modo que a
config continue sendo a fonte única da verdade sem depender da API
depreciada.
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

# Solvers compatíveis com cada faixa de l1_ratio.
#   l1_ratio == 0.0  → L2 puro (todos os solvers)
#   l1_ratio == 1.0  → L1 puro (liblinear, saga)
#   0 < l1_ratio < 1 → elastic-net (saga apenas)
_L1_RATIO_SOLVERS: dict[str, set[str]] = {
    "l2":          {"lbfgs", "liblinear", "newton-cg", "newton-cholesky", "sag", "saga"},
    "l1":          {"liblinear", "saga"},
    "elasticnet":  {"saga"},
}


def _penalty_do_yaml() -> Penalty | None:
    """
    Lê `logistic.penalty` do `supervised.yaml`.

    Retorna None quando a chave estiver ausente, vazia ou nula — nesse
    caso o `l1_ratio` passado explicitamente é usado sem alteração.
    """
    try:
        valor = C.cfg("logistic", "penalty")
    except (KeyError, TypeError):
        return None
    if not valor:
        return None
    if valor not in ("l1", "l2", "elasticnet"):
        raise ValueError(
            f"logistic.penalty inválido: {valor!r}. "
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

    # Traduz `penalty` (config) → `l1_ratio` (API nova do sklearn).
    if penalty == "l2":
        l1_ratio = 0.0
    elif penalty == "l1":
        l1_ratio = 1.0
    elif penalty == "elasticnet":
        if l1_ratio <= 0.0 or l1_ratio >= 1.0:
            raise ValueError(
                f"penalty='elasticnet' requer 0 < l1_ratio < 1; "
                f"recebido l1_ratio={l1_ratio!r}."
            )

    if not (0.0 <= l1_ratio <= 1.0):
        raise ValueError(f"l1_ratio deve estar em [0, 1]; recebido {l1_ratio!r}.")

    # Classifica o tipo de penalidade para validar solver.
    if l1_ratio == 0.0:
        tipo = "l2"
    elif l1_ratio == 1.0:
        tipo = "l1"
    else:
        tipo = "elasticnet"

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