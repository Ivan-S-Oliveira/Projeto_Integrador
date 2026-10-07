"""
Avaliação de calibração de probabilidades.

Complementa `src/models/calibration.py`:

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

from typing import Union

import numpy as np
import pandas as pd

from src.evaluation.metrics import _to_int_labels, _to_np

ArrayLike = Union[np.ndarray, pd.Series, list]


# ---------------------------------------------------------------------------
# Reliability diagram
# ---------------------------------------------------------------------------

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
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(p, bins[1:-1], right=True), 0, n_bins - 1)

    linhas: list[dict[str, float]] = []
    for b in range(n_bins):
        m = idx == b
        n = int(m.sum())
        if n == 0:
            linhas.append({
                "bin_centro":    float((bins[b] + bins[b + 1]) / 2),
                "freq_positiva": float("nan"),
                "n":             0.0,
                "gap":           float("nan"),
            })
        else:
            centro = float(p[m].mean())
            freq = float(y[m].mean())
            linhas.append({
                "bin_centro":    centro,
                "freq_positiva": freq,
                "n":             float(n),
                "gap":           float(abs(freq - centro)),
            })

    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# ECE / MCE
# ---------------------------------------------------------------------------

def ece(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> float:
    """Expected Calibration Error — média ponderada dos gaps por bin."""
    tabela = curva_confiabilidade(y_true, y_prob, n_bins=n_bins)
    total = float(tabela["n"].sum())
    if total == 0:
        return float("nan")
    pesos = tabela["n"] / total
    gaps = tabela["gap"].fillna(0.0)
    return float((pesos * gaps).sum())


def mce(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> float:
    """Maximum Calibration Error — o pior gap entre os bins."""
    tabela = curva_confiabilidade(y_true, y_prob, n_bins=n_bins)
    gaps = tabela["gap"].dropna()
    if gaps.empty:
        return float("nan")
    return float(gaps.max())


# ---------------------------------------------------------------------------
# Decomposição de Brier (Murphy)
# ---------------------------------------------------------------------------

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
        raise ValueError("y_true vazio.")

    base_rate = float(y.mean())
    uncertainty = base_rate * (1.0 - base_rate)
    brier_obs = float(np.mean((p - y) ** 2))

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(p, bins[1:-1], right=True), 0, n_bins - 1)

    reliability = 0.0
    resolution = 0.0
    for b in range(n_bins):
        m = idx == b
        n_b = int(m.sum())
        if n_b == 0:
            continue
        freq_obs = float(y[m].mean())
        freq_pred = float(p[m].mean())
        peso = n_b / n
        reliability += peso * (freq_obs - freq_pred) ** 2
        resolution += peso * (freq_obs - base_rate) ** 2

    return {
        "brier":       brier_obs,
        "reliability": float(reliability),
        "resolution":  float(resolution),
        "uncertainty": float(uncertainty),
        "n":           float(n),
    }