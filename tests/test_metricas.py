"""Métricas e bootstrap."""

from __future__ import annotations

import numpy as np
import pytest
from src.avaliacao import accuracy, auc, brier, f1, ic_bootstrap, metricas_completas, metricas_por_limiar, precision, recall


@pytest.fixture
def y_true() -> np.ndarray:
    """10 rótulos binários — 6 positivos (1), 4 negativos (0)."""
    return np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])


@pytest.fixture
def y_prob() -> np.ndarray:
    """10 probabilidades em ``[0, 1]`` correlacionadas com ``y_true``."""
    return np.array([0.1, 0.2, 0.8, 0.9, 0.6, 0.3, 0.7, 0.4, 0.85, 0.75])


_CHAVES_METRICAS_COMPLETAS = (
    "auc", "ap", "brier", "f1", "precision", "recall",
    "accuracy", "limiar", "n",
)


def test_auc_perfeito() -> None:
    """Classificador com separação perfeita → AUC = 1.0."""
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    assert auc(y, p) == pytest.approx(1.0)


def test_brier_em_intervalo(y_true: np.ndarray, y_prob: np.ndarray) -> None:
    assert 0.0 <= brier(y_true, y_prob) <= 1.0


def test_zero_division_nao_quebra() -> None:
    """``y_true`` e ``y_pred`` sem positivos → métricas devolvem 0.0, não ``ZeroDivisionError``."""
    y_true = np.zeros(3, dtype=int)
    y_pred = np.zeros(3, dtype=int)
    assert f1(y_true, y_pred) == 0.0
    assert precision(y_true, y_pred) == 0.0
    assert recall(y_true, y_pred) == 0.0


def test_metricas_completas_chaves(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    d = metricas_completas(y_true, y_prob, limiar=0.5)
    for k in _CHAVES_METRICAS_COMPLETAS:
        assert k in d
    assert d["limiar"] == 0.5
    assert d["n"] == float(len(y_true))


def test_metricas_por_limiar(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    t = metricas_por_limiar(y_true, y_prob, n_limiares=11)
    assert {"limiar", "f1", "precision", "recall", "accuracy"}.issubset(t.columns)
    assert len(t) == 11
    assert (t["limiar"] > 0).all()
    assert (t["limiar"] < 1).all()


def test_ic_bootstrap_deterministico(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    """Mesma seed → mesmo resultado."""
    a = ic_bootstrap(y_true, y_prob, n_boot=50, seed=42)
    b = ic_bootstrap(y_true, y_prob, n_boot=50, seed=42)
    assert a == b


def test_bootstrap_grupo_igual_ao_sklearn_com_pesos_um():
    from sklearn.metrics import average_precision_score, roc_auc_score

    from src.avaliacao import _ap_ponderada, _auc_ponderada, _niveis

    rng = np.random.default_rng(0)
    p = np.round(rng.beta(1, 10, 20_000), 2)
    y = (rng.random(20_000) < np.clip(p * 1.2, 0, 1)).astype(float)
    cod, k = _niveis(p)
    um = np.ones(len(y))
    assert abs(_auc_ponderada(cod, k, y, um) - roc_auc_score(y, p)) < 1e-9
    assert abs(_ap_ponderada(cod, k, y, um) - average_precision_score(y, p)) < 1e-9
    pesos = rng.integers(0, 3, len(y)).astype(float)
    repetido = np.repeat(np.arange(len(y)), pesos.astype(int))
    assert abs(_auc_ponderada(cod, k, y, pesos) - roc_auc_score(y[repetido], p[repetido])) < 1e-9
    assert abs(_ap_ponderada(cod, k, y, pesos) - average_precision_score(y[repetido], p[repetido])) < 1e-9


def test_bootstrap_grupo_diferenca_nula_e_semente():
    from src.avaliacao import bootstrap_grupo

    rng = np.random.default_rng(1)
    p = rng.beta(1, 10, 4_000)
    y = (rng.random(4_000) < p).astype(int)
    grupos = np.arange(4_000)
    r = bootstrap_grupo(y, p, grupos, metrica="ap", prob_b=p, n=50, seed=7)
    assert r["estimativa_diferenca"] == 0 and r["ic_inferior"] <= 0 <= r["ic_superior"]
    r1 = bootstrap_grupo(y, p, grupos, metrica="auc", n=50, seed=7)
    r2 = bootstrap_grupo(y, p, grupos, metrica="auc", n=50, seed=7)
    assert r1 == r2 and r1["ic_inferior"] < r1["estimativa"] < r1["ic_superior"]
