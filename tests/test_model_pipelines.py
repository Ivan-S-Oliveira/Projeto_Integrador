"""
Testes rápidos dos construtores de pipeline de modelos supervisionados.

Cobrem baseline, logística e boosting. Não dependem do Parquet nem fazem
I/O pesado. As features vêm de ``src.models.pipeline`` (que lê o
``supervised.yaml``) — sem hard-code.
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


def _df_features(
    n: int = 200,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.Series]:
    """DataFrame sintético com exactamente as features exigidas pelo YAML.

    Numéricas com distribuição normal; categóricas com 3 níveis como
    strings. O alvo é balanceado 50/50 e depois embaralhado — garante as
    duas classes para ``DummyClassifier(strategy="prior")`` e para
    ``LogisticRegression(class_weight="balanced")``.
    """
    rng = np.random.default_rng(seed)
    dados: dict[str, np.ndarray] = {}

    for coluna in P.FEATURES_NUMERICAS:
        dados[coluna] = rng.normal(loc=50.0, scale=15.0, size=n)
    for coluna in P.FEATURES_CATEGORICAS:
        dados[coluna] = rng.choice(["0", "1", "2"], size=n)

    X = pd.DataFrame(dados)
    y = pd.Series(
        np.concatenate([np.zeros(n // 2, dtype=int), np.ones(n - n // 2, dtype=int)]),
        name="alvo",
    ).sample(frac=1, random_state=seed).reset_index(drop=True)

    return X, y


def _colunas_do_pre(pipe: Pipeline) -> set[str]:
    """Colunas declaradas no ``ColumnTransformer`` do pipeline.

    ``ColumnTransformer.transformers`` é uma lista de
    ``(nome, transformer, colunas)`` — extraímos a terceira posição.
    """
    colunas: set[str] = set()
    for _, _, cols in pipe.named_steps["pre"].transformers:
        if isinstance(cols, list):
            colunas.update(cols)
    return colunas


# `max_iter` reduzido para manter os testes rápidos — smoke de fit, não tuning.
_CONSTRUTORES: list[tuple[str, Callable[[], Pipeline], type]] = [
    ("baseline", lambda: build_baseline_pipeline(), DummyClassifier),
    ("logistic", lambda: build_logistic_pipeline(max_iter=500), LogisticRegression),
    ("boosting", lambda: build_boosting_pipeline(max_iter=30), HistGradientBoostingClassifier),
]

_IDS = [nome for nome, _, _ in _CONSTRUTORES]


# ---------------------------------------------------------------------------
# Contrato do pipeline (estrutura)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("nome", "ctor", "clf_esperado"), _CONSTRUTORES, ids=_IDS)
def test_pipeline_retorna_pipeline(
    nome: str,
    ctor: Callable[[], Pipeline],
    clf_esperado: type,
) -> None:
    """Cada construtor devolve ``Pipeline(pre, clf)`` com o classificador correto."""
    pipe = ctor()
    assert isinstance(pipe, Pipeline), nome
    assert list(pipe.named_steps.keys()) == ["pre", "clf"], nome
    assert isinstance(pipe.named_steps["clf"], clf_esperado), nome


@pytest.mark.parametrize(("nome", "ctor", "clf_esperado"), _CONSTRUTORES, ids=_IDS)
def test_pipeline_nao_inclui_proibidas(
    nome: str,
    ctor: Callable[[], Pipeline],
    clf_esperado: type,
) -> None:
    proibidas = set(C.cfg("features", "proibidas") or [])
    assert proibidas, (
        "`features.proibidas` está vazio no supervised.yaml — "
        "ao menos o alvo e as colunas posteriores ao desfecho precisam "
        "estar listadas."
    )

    colisoes = _colunas_do_pre(ctor()) & proibidas
    assert not colisoes, (
        f"{nome}: colunas proibidas no pré-processador: {sorted(colisoes)}"
    )


# ---------------------------------------------------------------------------
# Comportamento (fit + predict_proba)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("nome", "ctor", "clf_esperado"), _CONSTRUTORES, ids=_IDS)
def test_pipeline_fit_predict_proba(
    nome: str,
    ctor: Callable[[], Pipeline],
    clf_esperado: type,
) -> None:
    X, y = _df_features(n=200)
    pipe = ctor().fit(X, y)
    proba = pipe.predict_proba(X)

    assert proba.shape == (len(X), 2), f"{nome}: shape {proba.shape}"
    assert np.isfinite(proba).all(), f"{nome}: probabilidades com NaN/Inf"
    assert ((proba >= 0) & (proba <= 1)).all(), f"{nome}: fora de [0, 1]"
    assert np.allclose(proba.sum(axis=1), 1.0), f"{nome}: linhas não somam 1"


# ---------------------------------------------------------------------------
# Contrato de features
# ---------------------------------------------------------------------------

def test_pipelines_usam_features_do_yaml() -> None:
    """Pré-processador expõe ``FEATURES_NUMERICAS + FEATURES_CATEGORICAS`` do YAML.

    Canário contra features fora do YAML ou filtros silenciosos.
    """
    esperadas = set(P.FEATURES_NUMERICAS) | set(P.FEATURES_CATEGORICAS)
    assert esperadas, "Nenhuma feature declarada em supervised.yaml."

    for nome, ctor, _ in _CONSTRUTORES:
        colunas = _colunas_do_pre(ctor())
        faltando = esperadas - colunas
        extras = colunas - esperadas
        assert colunas == esperadas, (
            f"{nome}: pré-processador divergente do YAML. "
            f"Faltando: {sorted(faltando)}; Extras: {sorted(extras)}"
        )


# ---------------------------------------------------------------------------
# Validação de parâmetros
# ---------------------------------------------------------------------------

def test_logistic_pipeline_solver_invalido() -> None:
    """``l1_ratio=1.0`` (L1 puro) exige ``liblinear`` ou ``saga``.

    Com ``lbfgs`` o construtor deve levantar ``ValueError``.
    """
    with pytest.raises(ValueError, match="combinação inválida"):
        build_logistic_pipeline(l1_ratio=1.0, solver="lbfgs")