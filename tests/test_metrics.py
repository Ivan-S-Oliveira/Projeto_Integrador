"""Testes das métricas em ``src.evaluation.metrics``."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.evaluation.metrics import (
    accuracy,
    auc,
    average_precision,
    brier,
    f1,
    ic_bootstrap,
    metricas_completas,
    metricas_por_limiar,
    precision,
    recall,
)


@pytest.fixture
def y_true() -> np.ndarray:
    """10 rótulos binários — 6 positivos (1), 4 negativos (0)."""
    return np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])


@pytest.fixture
def y_prob() -> np.ndarray:
    """10 probabilidades em ``[0, 1]`` correlacionadas com ``y_true``."""
    return np.array([0.1, 0.2, 0.8, 0.9, 0.6, 0.3, 0.7, 0.4, 0.85, 0.75])


# Chaves contratuais de ``metricas_completas`` — a lista serve como
# armadilha contra remoções silenciosas no módulo fonte.
_CHAVES_METRICAS_COMPLETAS = (
    "auc", "ap", "brier", "f1", "precision", "recall",
    "accuracy", "limiar", "n",
)


# ---------------------------------------------------------------------------
# AUC
# ---------------------------------------------------------------------------

def test_auc_perfeito() -> None:
    """Classificador com separação perfeita → AUC = 1.0."""
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    assert auc(y, p) == pytest.approx(1.0)


def test_auc_constante_e_meio() -> None:
    """Probabilidades constantes → AUC = 0.5 por construção."""
    y = np.array([0, 0, 1, 1])
    p = np.array([0.5, 0.5, 0.5, 0.5])
    assert auc(y, p) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Métricas de probabilidade (aceitam y_prob)
# ---------------------------------------------------------------------------

def test_metricas_individuais_retornam_float(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    for fn in (auc, average_precision, brier):
        assert isinstance(fn(y_true, y_prob), float)


def test_average_precision_em_intervalo(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    assert 0.0 <= average_precision(y_true, y_prob) <= 1.0


def test_brier_em_intervalo(y_true: np.ndarray, y_prob: np.ndarray) -> None:
    assert 0.0 <= brier(y_true, y_prob) <= 1.0


# ---------------------------------------------------------------------------
# Métricas de classificação (aceitam y_pred duro)
# ---------------------------------------------------------------------------

def test_f1_precision_recall(y_true: np.ndarray) -> None:
    y_pred = np.array([0, 0, 1, 1, 1, 0, 0, 0, 1, 1])
    for fn in (f1, precision, recall):
        v = fn(y_true, y_pred)
        assert isinstance(v, float)
        assert 0.0 <= v <= 1.0


def test_accuracy_perfeita() -> None:
    y = np.array([0, 1, 0, 1])
    assert accuracy(y, y) == pytest.approx(1.0)


def test_zero_division_nao_quebra() -> None:
    """``y_true`` e ``y_pred`` sem positivos → métricas devolvem 0.0, não ``ZeroDivisionError``."""
    y_true = np.zeros(3, dtype=int)
    y_pred = np.zeros(3, dtype=int)
    assert f1(y_true, y_pred) == 0.0
    assert precision(y_true, y_pred) == 0.0
    assert recall(y_true, y_pred) == 0.0


# ---------------------------------------------------------------------------
# metricas_completas
# ---------------------------------------------------------------------------

def test_metricas_completas_chaves(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    d = metricas_completas(y_true, y_prob, limiar=0.5)
    for k in _CHAVES_METRICAS_COMPLETAS:
        assert k in d
    assert d["limiar"] == 0.5
    assert d["n"] == float(len(y_true))


def test_metricas_completas_aceita_series(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    """``metricas_completas`` deve aceitar ``pd.Series`` como entrada."""
    d = metricas_completas(pd.Series(y_true), pd.Series(y_prob))
    assert "auc" in d


# ---------------------------------------------------------------------------
# metricas_por_limiar
# ---------------------------------------------------------------------------

def test_metricas_por_limiar(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    t = metricas_por_limiar(y_true, y_prob, n_limiares=11)
    assert {"limiar", "f1", "precision", "recall", "accuracy"}.issubset(t.columns)
    assert len(t) == 11
    assert (t["limiar"] > 0).all()
    assert (t["limiar"] < 1).all()


# ---------------------------------------------------------------------------
# ic_bootstrap
# ---------------------------------------------------------------------------

def test_ic_bootstrap_retorna_tres_floats(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    est, inf, sup = ic_bootstrap(y_true, y_prob, n_boot=50, seed=42)
    assert isinstance(est, float)
    assert isinstance(inf, float)
    assert isinstance(sup, float)
    assert inf <= sup


def test_ic_bootstrap_deterministico(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    """Mesma seed → mesmo resultado."""
    a = ic_bootstrap(y_true, y_prob, n_boot=50, seed=42)
    b = ic_bootstrap(y_true, y_prob, n_boot=50, seed=42)
    assert a == b


def test_ic_bootstrap_metrica_customizada(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    est, inf, sup = ic_bootstrap(
        y_true,
        y_prob,
        metrica=average_precision,
        n_boot=30,
        seed=1,
    )
    assert inf <= est <= sup