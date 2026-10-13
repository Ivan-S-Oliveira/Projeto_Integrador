"""
Testes rápidos dos construtores de pipeline de modelos supervisionados.

Cobrem:

- `src/models/baseline.py`  → `build_baseline_pipeline`
- `src/models/logistic.py`  → `build_logistic_pipeline`
- `src/models/boosting.py`  → `build_boosting_pipeline`

Não dependem do Parquet nem fazem I/O pesado — rodam em CI com
`pytest -q` sem `-m slow`.

Cada teste:

- constrói o pipeline a partir do construtor público;
- verifica que as etapas obrigatórias estão na ordem esperada;
- (quando aplicável) executa `fit`/`predict_proba` em dados sintéticos;
- confirma que nenhuma coluna proibida aparece no pré-processador.

A lista de features vem de `src.models.pipeline`, que por sua vez lê
`configs/supervised.yaml`. Isso mantém o teste sincronizado com o YAML
sem hard-code.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.models import pipeline as P
from src.models.baseline import build_baseline_pipeline
from src.models.boosting import build_boosting_pipeline
from src.models.logistic import build_logistic_pipeline
from src.utils import config as C


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _df_features(n: int = 200, seed: int = 42) -> tuple[pd.DataFrame, pd.Series]:
    """
    DataFrame sintético com exatamente as features exigidas pelo YAML.

    Numéricas recebem distribuição normal; categóricas recebem 3 níveis
    como strings. O alvo é balanceado 50/50 e depois embaralhado — isso
    garante as duas classes para `DummyClassifier(strategy="prior")` e
    para `LogisticRegression(class_weight="balanced")`.
    """
    rng = np.random.default_rng(seed)
    dados: dict[str, np.ndarray] = {}

    for coluna in P.FEATURES_NUMERICAS:
        dados[coluna] = rng.normal(loc=50.0, scale=15.0, size=n)

    for coluna in P.FEATURES_CATEGORICAS:
        dados[coluna] = rng.choice(["0", "1", "2"], size=n)

    X = pd.DataFrame(dados)

    y = pd.Series(
        np.concatenate(
            [
                np.zeros(n // 2, dtype=int),
                np.ones(n - n // 2, dtype=int),
            ]
        ),
        name="alvo",
    ).sample(frac=1, random_state=seed).reset_index(drop=True)

    return X, y


# Cada entrada é (nome_curto, construtor). Passamos `max_iter` menores
# para manter os testes rápidos — não é tuning, só smoke de fit.
_CONSTRUTORES: list[tuple[str, Callable[[], Pipeline]]] = [
    ("baseline", lambda: build_baseline_pipeline()),
    ("logistic", lambda: build_logistic_pipeline(max_iter=500)),
    ("boosting", lambda: build_boosting_pipeline(max_iter=30)),
]

_IDS = [nome for nome, _ in _CONSTRUTORES]


# ---------------------------------------------------------------------------
# Construtores — estrutura
# ---------------------------------------------------------------------------

def test_build_baseline_pipeline_retorna_pipeline() -> None:
    pipe = build_baseline_pipeline()
    assert isinstance(pipe, Pipeline)
    assert list(pipe.named_steps.keys()) == ["pre", "clf"]
    assert isinstance(pipe.named_steps["clf"], DummyClassifier)


def test_build_logistic_pipeline_retorna_pipeline() -> None:
    pipe = build_logistic_pipeline()
    assert isinstance(pipe, Pipeline)
    assert list(pipe.named_steps.keys()) == ["pre", "clf"]
    assert isinstance(pipe.named_steps["clf"], LogisticRegression)


def test_build_boosting_pipeline_retorna_pipeline() -> None:
    pipe = build_boosting_pipeline()
    assert isinstance(pipe, Pipeline)
    assert list(pipe.named_steps.keys()) == ["pre", "clf"]
    assert isinstance(
        pipe.named_steps["clf"], HistGradientBoostingClassifier
    )


# ---------------------------------------------------------------------------
# Fit / predict_proba em dados sintéticos
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("nome", "ctor"),
    _CONSTRUTORES,
    ids=_IDS,
)
def test_pipelines_fit_predict_proba(
    nome: str, ctor: Callable[[], Pipeline]
) -> None:
    X, y = _df_features(n=200)
    pipe = ctor()
    pipe.fit(X, y)

    proba = pipe.predict_proba(X)

    assert proba.shape == (len(X), 2), (
        f"{nome}: shape inesperado {proba.shape}"
    )
    assert np.isfinite(proba).all(), (
        f"{nome}: probabilidades contêm NaN/Inf"
    )
    assert ((proba >= 0) & (proba <= 1)).all(), (
        f"{nome}: probabilidades fora de [0, 1]"
    )
    assert np.allclose(proba.sum(axis=1), 1.0), (
        f"{nome}: linhas de probabilidade não somam 1"
    )


# ---------------------------------------------------------------------------
# Contrato anti-leakage no pré-processador
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("nome", "ctor"),
    _CONSTRUTORES,
    ids=_IDS,
)
def test_pipelines_nao_incluem_proibidas(
    nome: str, ctor: Callable[[], Pipeline]
) -> None:
    proibidas = set(C.cfg("features", "proibidas") or [])
    assert proibidas, (
        "`features.proibidas` está vazio no supervised.yaml — "
        "ao menos o alvo e as colunas posteriores ao desfecho precisam "
        "estar listadas."
    )

    pipe = ctor()
    pre = pipe.named_steps["pre"]

    # ColumnTransformer.transformers é uma lista de
    # (nome, transformer, colunas). Extraímos a terceira posição.
    colunas_no_pre: set[str] = set()
    for _, _, cols in pre.transformers:
        if isinstance(cols, list):
            colunas_no_pre.update(cols)

    colisoes = colunas_no_pre & proibidas
    assert not colisoes, (
        f"{nome}: colunas proibidas presentes no pré-processador: "
        f"{sorted(colisoes)}"
    )


# ---------------------------------------------------------------------------
# Cobertura adicional leve
# ---------------------------------------------------------------------------

def test_pipelines_usam_features_do_yaml() -> None:
    """
    O pré-processador de cada pipeline precisa expor exatamente o
    conjunto `FEATURES_NUMERICAS + FEATURES_CATEGORICAS` derivado do
    YAML. Serve como canário: se alguém adicionar uma feature fora do
    YAML ou filtrar silenciosamente, o teste acusa.
    """
    esperadas = set(P.FEATURES_NUMERICAS) | set(P.FEATURES_CATEGORICAS)
    assert esperadas, "Nenhuma feature declarada em supervised.yaml."

    for nome, ctor in _CONSTRUTORES:
        pipe = ctor()
        pre = pipe.named_steps["pre"]
        colunas: set[str] = set()
        for _, _, cols in pre.transformers:
            if isinstance(cols, list):
                colunas.update(cols)

        faltando = esperadas - colunas
        extras = colunas - esperadas
        assert colunas == esperadas, (
            f"{nome}: pré-processador divergente do YAML. "
            f"Faltando: {sorted(faltando)}; Extras: {sorted(extras)}"
        )


def test_logistic_pipeline_solver_invalido() -> None:
    """
    `l1_ratio=1.0` (L1 puro) exige `liblinear` ou `saga`. Com `lbfgs`,
    `build_logistic_pipeline` precisa levantar `ValueError` — a validação
    de compatibilidade é parte do contrato do módulo.
    """
    with pytest.raises(ValueError, match="combinação inválida"):
        build_logistic_pipeline(l1_ratio=1.0, solver="lbfgs")