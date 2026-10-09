"""Testes de calibração e escolha de limiar."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.models.calibration import calibrar, escolher_limiar


# ---------------------------------------------------------------------------
# escolher_limiar
# ---------------------------------------------------------------------------

@pytest.fixture
def dados():
    y = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9, 0.6, 0.3, 0.7, 0.4, 0.85, 0.75])
    return y, p


def test_escolher_limiar_retorna_dict(dados):
    y, p = dados
    r = escolher_limiar(y, p, metrica="f1")
    assert {"limiar", "valor", "metrica", "auc", "brier", "tabela"} <= set(r)
    assert r["metrica"] == "f1"
    assert 0 < r["limiar"] < 1


def test_escolher_limiar_metrica_invalida(dados):
    y, p = dados
    with pytest.raises(ValueError, match="metrica inválida"):
        escolher_limiar(y, p, metrica="nao_existe")  # type: ignore[arg-type]


def test_escolher_limiar_min_precision_respeitado():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    r = escolher_limiar(y, p, metrica="recall", min_precision=0.9)
    linha = r["tabela"][r["tabela"]["limiar"] == r["limiar"]]
    assert linha["precision"].iloc[0] >= 0.9


def test_escolher_limiar_min_precision_impossivel():
    # Em nenhum limiar a precisão passa de 0.25.
    y = np.array([1, 0, 0, 0])
    p = np.array([0.1, 0.9, 0.8, 0.85])
    with pytest.raises(ValueError, match="precision"):
        escolher_limiar(y, p, min_precision=0.5)


# ---------------------------------------------------------------------------
# calibrar
# ---------------------------------------------------------------------------

def test_calibrar_requer_sklearn_16():
    pytest.importorskip("sklearn.frozen")


def test_calibrar_metodo_invalido():
    pytest.importorskip("sklearn.frozen")
    from sklearn.linear_model import LogisticRegression

    X = pd.DataFrame({"a": [0.0, 1.0, 2.0, 3.0]})
    y = pd.Series([0, 0, 1, 1])
    modelo = LogisticRegression().fit(X, y)

    with pytest.raises(ValueError, match="method inválido"):
        calibrar(modelo, X, y, method="nao_existe")


def test_calibrar_sigmoid_preserva_shape():
    pytest.importorskip("sklearn.frozen")
    from sklearn.linear_model import LogisticRegression

    rng = np.random.RandomState(0)
    X = pd.DataFrame({"a": rng.randn(200)})
    y = pd.Series((X["a"] + rng.randn(200) * 0.1 > 0).astype(int))

    modelo = LogisticRegression().fit(X, y)
    cal = calibrar(modelo, X, y, method="sigmoid")

    proba = cal.predict_proba(X)
    assert proba.shape == (len(X), 2)
    assert np.allclose(proba.sum(axis=1), 1.0)
    assert ((proba >= 0) & (proba <= 1)).all()


def test_calibrar_isotonic_preserva_shape():
    pytest.importorskip("sklearn.frozen")
    from sklearn.linear_model import LogisticRegression

    rng = np.random.RandomState(1)
    X = pd.DataFrame({"a": rng.randn(500)})
    y = pd.Series((X["a"] > 0).astype(int))

    modelo = LogisticRegression().fit(X, y)
    cal = calibrar(modelo, X, y, method="isotonic")
    assert cal.predict_proba(X).shape == (len(X), 2)