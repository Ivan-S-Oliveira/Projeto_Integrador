"""
Avaliação de calibração de probabilidades.

Complementa ``src/models/calibration.py``:

    src/models/calibration.py      → AJUSTA a calibração
    src/evaluation/calibration.py  → MEDE a qualidade da calibração

Métricas implementadas
----------------------
- Curva de confiabilidade (reliability diagram)
- ECE  (Expected Calibration Error)
- MCE  (Maximum Calibration Error)
- Decomposição de Brier em Reliability + Resolution − Uncertainty
  (Murphy, 1973)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.evaluation.metrics import _to_int_labels, _to_np

ArrayLike = np.ndarray | pd.Series | list


def _bins_digitize(p: np.ndarray, n_bins: int) -> np.ndarray:
    """Índice do bin (0..n_bins-1) de cada probabilidade em ``[0, 1]``."""
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    return np.clip(np.digitize(p, edges[1:-1], right=True), 0, n_bins - 1)


def _linha_vazia(b: int, edges: np.ndarray) -> dict[str, float]:
    return {
        "bin_centro":    float((edges[b] + edges[b + 1]) / 2),
        "freq_positiva": float("nan"),
        "n":             0.0,
        "gap":           float("nan"),
    }


def curva_confiabilidade(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> pd.DataFrame:
    """
    Dados para o reliability diagram.

    Colunas:
        bin_centro    — probabilidade média prevista no bin
        freq_positiva — fração real de positivos no bin
        n             — número de amostras no bin
        gap           — |freq_positiva - bin_centro|
    """
    y      = _to_int_labels(y_true)
    p      = _to_np(y_prob)
    edges  = np.linspace(0.0, 1.0, n_bins + 1)
    idx    = _bins_digitize(p, n_bins)

    linhas: list[dict[str, float]] = []
    for b in range(n_bins):
        m = idx == b
        n = int(m.sum())

        if n == 0:
            linhas.append(_linha_vazia(b, edges))
            continue

        centro = float(p[m].mean())
        freq   = float(y[m].mean())
        linhas.append({
            "bin_centro":    centro,
            "freq_positiva": freq,
            "n":             float(n),
            "gap":           abs(freq - centro),
        })

    return pd.DataFrame(linhas)


def ece(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> float:
    """Expected Calibration Error — média ponderada dos gaps por bin."""
    tabela = curva_confiabilidade(y_true, y_prob, n_bins=n_bins)
    total  = float(tabela["n"].sum())

    if total == 0:
        return float("nan")

    pesos = tabela["n"] / total
    gaps  = tabela["gap"].fillna(0.0)
    return float((pesos * gaps).sum())


def mce(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> float:
    """Maximum Calibration Error — o pior gap entre os bins."""
    tabela = curva_confiabilidade(y_true, y_prob, n_bins=n_bins)
    gaps   = tabela["gap"].dropna()

    if gaps.empty:
        return float("nan")

    return float(gaps.max())


def brier_decomposicao(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> dict[str, float]:
    """
    Decompõe o Brier score (Murphy, 1973):

        Brier = Reliability − Resolution + Uncertainty

    Retorna
    -------
    dict com:
        brier         — Brier score observado
        reliability   — quanto menor, melhor (penaliza desvios locais)
        resolution    — quanto maior, melhor (capacidade de separar)
        uncertainty   — entropia binária da base (fixa para o dataset)
        n             — número de amostras
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)
    n = len(y)

    if n == 0:
        raise ValueError("y_true vazio — não há como decompor o Brier.")

    base_rate   = float(y.mean())
    uncertainty = base_rate * (1.0 - base_rate)
    brier_obs   = float(np.mean((p - y) ** 2))
    idx         = _bins_digitize(p, n_bins)

    reliability = 0.0
    resolution  = 0.0

    for b in range(n_bins):
        m   = idx == b
        n_b = int(m.sum())

        if n_b == 0:
            continue

        freq_obs  = float(y[m].mean())
        freq_pred = float(p[m].mean())
        peso      = n_b / n

        reliability += peso * (freq_obs - freq_pred) ** 2
        resolution  += peso * (freq_obs - base_rate) ** 2

    return {
        "brier":       brier_obs,
        "reliability": float(reliability),
        "resolution":  float(resolution),
        "uncertainty": float(uncertainty),
        "n":           float(n),
    }


def calibracao_intercepto_inclinacao(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    eps: float = 1e-6,
) -> tuple[float, float]:
    """Regressão logística de y em logit(p): intercepto ideal 0 e inclinação ideal 1."""
    from sklearn.linear_model import LogisticRegression

    p = np.clip(_to_np(y_prob), eps, 1 - eps)
    z = np.log(p / (1 - p)).reshape(-1, 1)
    modelo = LogisticRegression(C=1e6, solver="lbfgs", max_iter=200).fit(z, _to_int_labels(y_true))
    return float(modelo.intercept_[0]), float(modelo.coef_[0, 0])


def ece_quantis(y_true: ArrayLike, y_prob: ArrayLike, n_bins: int = 10) -> float:
    """ECE com faixas de tamanho igual (quantis da probabilidade prevista)."""
    y, p = _to_int_labels(y_true), _to_np(y_prob)
    partes = np.array_split(np.argsort(p, kind="stable"), n_bins)
    return float(sum(len(i) * abs(y[i].mean() - p[i].mean()) for i in partes if len(i)) / len(y))


def test_calibracao_intercepto_inclinacao_e_ece_quantis():
    from src.evaluation.calibration import calibracao_intercepto_inclinacao, ece_quantis

    rng = np.random.default_rng(0)
    p = rng.beta(1, 10, 100_000)
    y = (rng.random(100_000) < p).astype(int)

    intercepto, inclinacao = calibracao_intercepto_inclinacao(y, p)
    assert abs(intercepto) < 0.1 and 0.9 < inclinacao < 1.1
    assert ece_quantis(y, p) < 0.01

    inflada = np.clip(p * 2.5, 0, 1)
    assert calibracao_intercepto_inclinacao(y, inflada)[1] < 0.5
    assert ece_quantis(y, inflada) > 0.05