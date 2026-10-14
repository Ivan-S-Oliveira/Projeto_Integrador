"""
Métricas de classificação binária — todas retornam `float`.

Motivo: o scikit-learn retorna `Float | ndarray` para várias métricas,
o que faz o Pylance reclamar. Aqui a gente encapsula e garante `float`.

Também oferece:
    - `metricas_por_limiar` → tabela varrendo limiares
    - `ic_bootstrap`        → intervalo de confiança por bootstrap

Convenção de nomes de chaves em `metricas_completas`
----------------------------------------------------
`ap` (average precision) e `pr_auc` (área sob a curva precision-recall)
são a **mesma métrica** — a chave `pr_auc` é um alias mantido para
compatibilidade com consumidores que usam essa nomenclatura (ex.: C4).
Ambas apontam para o mesmo valor; não divergem.
"""

from __future__ import annotations

from typing import Callable, Union

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    log_loss as sk_log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

__all__ = [
    "ArrayLike",
    "auc",
    "average_precision",
    "brier",
    "log_loss",
    "f1",
    "precision",
    "recall",
    "accuracy",
    "especificidade",
    "sensibilidade",
    "metricas_completas",
    "metricas_por_limiar",
    "ic_bootstrap",
]

ArrayLike = Union[np.ndarray, pd.Series, list]


def _to_np(x: ArrayLike) -> np.ndarray:
    return np.asarray(x).ravel()


def _to_int_labels(y: ArrayLike) -> np.ndarray:
    return np.asarray(y).ravel().astype(int)


def _contagens_confusao(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> tuple[int, int, int, int]:
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    return tp, fp, tn, fn


def auc(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(roc_auc_score(_to_int_labels(y_true), _to_np(y_prob)))


def average_precision(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(average_precision_score(_to_int_labels(y_true), _to_np(y_prob)))


def brier(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(brier_score_loss(_to_int_labels(y_true), _to_np(y_prob)))


def log_loss(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    """
    Log loss (entropia cruzada binária).

    Recebe probabilidades (não rótulos duros) e devolve `float`.
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)
    return float(sk_log_loss(y, p, labels=[0, 1]))


def f1(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(
        f1_score(
            _to_int_labels(y_true),
            _to_int_labels(y_pred),
            zero_division=0,
        )
    )


def precision(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(
        precision_score(
            _to_int_labels(y_true),
            _to_int_labels(y_pred),
            zero_division=0,
        )
    )


def recall(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(
        recall_score(
            _to_int_labels(y_true),
            _to_int_labels(y_pred),
            zero_division=0,
        )
    )


def accuracy(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(
        accuracy_score(_to_int_labels(y_true), _to_int_labels(y_pred))
    )


def especificidade(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """
    Especificidade = TN / (TN + FP).

    Ou seja, `recall` da classe negativa. Retorna 0.0 quando não há
    nenhum negativo real (evita divisão por zero).
    """
    y = _to_int_labels(y_true)
    p = _to_int_labels(y_pred)

    _, fp, tn, _ = _contagens_confusao(y, p)
    denom = tn + fp
    return float(tn / denom) if denom > 0 else 0.0


def sensibilidade(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """
    Sensibilidade = recall da classe positiva.

    Alias semântico de `recall` — mantido para alinhar com o YAML,
    que pede explicitamente "sensibilidade".
    """
    return recall(y_true, y_pred)


def metricas_completas(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    limiar: float = 0.5,
) -> dict[str, float]:
    """
    Retorna um dict com AUC, AP, pr_auc, Brier, log_loss, F1, precision,
    recall, sensibilidade, especificidade e accuracy.

    Pronto para `Run.metrica(**d)`.

    Notas
    -----
    - `pr_auc` é **alias** de `ap` (ambos = `average_precision_score`),
      mantido para compatibilidade com consumidores que usam esse nome
      (ex.: C4). Os dois valores são idênticos.
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)
    y_pred = (p >= limiar).astype(int)

    ap = average_precision(y, p)

    return {
        "auc":            auc(y, p),
        "ap":             ap,
        "pr_auc":         ap,
        "brier":          brier(y, p),
        "log_loss":       log_loss(y, p),
        "f1":             f1(y, y_pred),
        "precision":      precision(y, y_pred),
        "recall":         recall(y, y_pred),
        "sensibilidade":  sensibilidade(y, y_pred),
        "especificidade": especificidade(y, y_pred),
        "accuracy":       accuracy(y, y_pred),
        "limiar":         float(limiar),
        "n":              float(len(y)),
    }


def metricas_por_limiar(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_limiares: int = 101,
) -> pd.DataFrame:
    """
    Tabela com métricas para cada limiar em [0.01, 0.99].

    Colunas: limiar, tp, fp, tn, fn, f1, precision, recall,
    sensibilidade, especificidade, accuracy, youden_j.

    Usa as métricas deste próprio módulo — não há tabela paralela de lambdas.

    Notas
    -----
    - `youden_j` = sensibilidade + especificidade − 1 = recall +
      especificidade − 1. Índice de Youden, útil para escolher o limiar
      que maximiza a separação entre as classes.
    - `tp`, `fp`, `tn`, `fn` vêm da matriz de confusão no limiar corrente
      e permitem derivar qualquer outra métrica a posteriori.
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)

    linhas: list[dict[str, float]] = []

    for th in np.linspace(0.01, 0.99, n_limiares):
        lim = float(th)
        y_pred = (p >= lim).astype(int)

        tp, fp, tn, fn = _contagens_confusao(y, y_pred)

        rec = recall(y, y_pred)
        esp = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
        youden_j = rec + esp - 1.0

        linhas.append({
            "limiar":         lim,
            "tp":             tp,
            "fp":             fp,
            "tn":             tn,
            "fn":             fn,
            "f1":             f1(y, y_pred),
            "precision":      precision(y, y_pred),
            "recall":         rec,
            "sensibilidade":  rec,
            "especificidade": esp,
            "accuracy":       accuracy(y, y_pred),
            "youden_j":       youden_j,
        })

    return pd.DataFrame(linhas)


def ic_bootstrap(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    *,
    metrica: Callable[[ArrayLike, ArrayLike], float] = auc,
    n_boot: int = 200,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float, float]:
    """
    Intervalo de confiança via bootstrap percentil.

    Retorna (estimativa, limite_inferior, limite_superior).

    Parâmetros
    ----------
    metrica : callable(y_true, y_prob) -> float
        Função de métrica. Default: `auc`.
    n_boot : int
        Número de reamostragens.
    alpha : float
        Nível de significância (0.05 → IC 95%).
    seed : int
        Semente para reprodutibilidade.
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)

    rng = np.random.default_rng(seed)
    n = len(y)
    valores = np.empty(n_boot, dtype="float64")

    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)

        if len(np.unique(y[idx])) < 2:
            valores[i] = np.nan
            continue

        valores[i] = metrica(y[idx], p[idx])

    est = float(metrica(y, p))
    validos = valores[~np.isnan(valores)]

    if validos.size == 0:
        return est, float("nan"), float("nan")

    inf = float(np.quantile(validos, alpha / 2))
    sup = float(np.quantile(validos, 1 - alpha / 2))
    return est, inf, sup