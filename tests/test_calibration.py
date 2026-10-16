"""Testes de calibração e escolha de limiar."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from src.models.calibration import calibrar, escolher_limiar


@pytest.fixture
def dados_limiar() -> tuple[np.ndarray, np.ndarray]:
    """10 amostras balanceadas — y_true binário, y_prob em [0, 1]."""
    y = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9, 0.6, 0.3, 0.7, 0.4, 0.85, 0.75])
    return y, p


@pytest.fixture
def modelo_ajustado() -> tuple[LogisticRegression, pd.DataFrame, pd.Series]:
    """``LogisticRegression`` ajustado em ``X`` 1D sintético com sinal.

    Fixture separada (não por teste) para que múltiplos testes de calibração
    reutilizem o mesmo modelo — o objecto é imutável após ``fit``.
    """
    pytest.importorskip("sklearn.frozen")
    rng = np.random.RandomState(0)
    X = pd.DataFrame({"a": rng.randn(200)})
    y = pd.Series((X["a"] + rng.randn(200) * 0.1 > 0).astype(int))
    return LogisticRegression().fit(X, y), X, y


# ---------------------------------------------------------------------------
# escolher_limiar
# ---------------------------------------------------------------------------

def test_escolher_limiar_retorna_dict(dados_limiar):
    y, p = dados_limiar
    r = escolher_limiar(y, p, metrica="f1")
    assert {"limiar", "valor", "metrica", "auc", "brier", "tabela"} <= set(r)
    assert r["metrica"] == "f1"
    assert 0 < r["limiar"] < 1


def test_escolher_limiar_metrica_invalida(dados_limiar):
    y, p = dados_limiar
    # Metrica não existe no Literal — passagem intencional de valor inválido.
    with pytest.raises(ValueError, match="metrica inválida"):
        escolher_limiar(y, p, metrica="nao_existe")  # type: ignore[arg-type]


def test_escolher_limiar_min_precision_respeitado():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    r = escolher_limiar(y, p, metrica="recall", min_precision=0.9)
    linha = r["tabela"][r["tabela"]["limiar"] == r["limiar"]]
    assert linha["precision"].iloc[0] >= 0.9


def test_escolher_limiar_min_precision_impossivel():
    y = np.array([1, 0, 0, 0])
    p = np.array([0.1, 0.9, 0.8, 0.85])
    with pytest.raises(ValueError, match="precision"):
        escolher_limiar(y, p, min_precision=0.5)


# ---------------------------------------------------------------------------
# calibrar
# ---------------------------------------------------------------------------

def test_calibrar_metodo_invalido(modelo_ajustado):
    modelo, X, y = modelo_ajustado
    with pytest.raises(ValueError, match="method inválido"):
        calibrar(modelo, X, y, method="nao_existe")  # type: ignore[arg-type]


def test_calibrar_sigmoid_preserva_shape(modelo_ajustado):
    modelo, X, y = modelo_ajustado
    cal = calibrar(modelo, X, y, method="sigmoid")
    proba = cal.predict_proba(X)
    assert proba.shape == (len(X), 2)
    assert np.allclose(proba.sum(axis=1), 1.0)
    assert np.all((proba >= 0) & (proba <= 1))


def test_calibrar_isotonic_preserva_shape():
    pytest.importorskip("sklearn.frozen")
    rng = np.random.RandomState(1)
    X = pd.DataFrame({"a": rng.randn(500)})
    y = pd.Series((X["a"] > 0).astype(int))
    modelo = LogisticRegression().fit(X, y)

    cal = calibrar(modelo, X, y, method="isotonic")
    assert cal.predict_proba(X).shape == (len(X), 2)