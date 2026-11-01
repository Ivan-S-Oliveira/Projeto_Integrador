"""
Métricas de classificação binária — todas retornam ``float``.

Encapsula o scikit-learn para garantir ``float``: em várias funções ele
retorna ``Float | ndarray``, o que polui o type-checker.

Oferece ainda:
    - ``metricas_por_limiar`` → tabela varrendo limiares
    - ``ic_bootstrap``        → intervalo de confiança por bootstrap

``ap`` (average precision) e ``pr_auc`` são a **mesma métrica** — a
chave ``pr_auc`` é um alias mantido para compatibilidade com consumidores
que usam essa nomenclatura (ex.: C4). Ambas apontam para o mesmo valor.
"""

from __future__ import annotations

from typing import Callable

from numpy.typing import ArrayLike

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
    "bootstrap_grupo",
]

ArrayLike = np.ndarray | pd.Series | list


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


def _especificidade_de_contagens(tn: int, fp: int) -> float:
    """``TN / (TN + FP)``; 0.0 quando não há negativo real."""
    denom = tn + fp
    return tn / denom if denom > 0 else 0.0


def auc(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(roc_auc_score(_to_int_labels(y_true), _to_np(y_prob)))


def average_precision(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(average_precision_score(_to_int_labels(y_true), _to_np(y_prob)))


def brier(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(brier_score_loss(_to_int_labels(y_true), _to_np(y_prob)))


def log_loss(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    """Log loss (entropia cruzada binária) sobre probabilidades."""
    return float(sk_log_loss(_to_int_labels(y_true), _to_np(y_prob), labels=[0, 1]))


def f1(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(f1_score(
        _to_int_labels(y_true), _to_int_labels(y_pred), zero_division=0,
    ))


def precision(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(precision_score(
        _to_int_labels(y_true), _to_int_labels(y_pred), zero_division=0,
    ))


def recall(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(recall_score(
        _to_int_labels(y_true), _to_int_labels(y_pred), zero_division=0,
    ))


def accuracy(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return float(accuracy_score(
        _to_int_labels(y_true), _to_int_labels(y_pred),
    ))


def especificidade(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Especificidade = ``TN / (TN + FP)`` — recall da classe negativa."""
    _, fp, tn, _ = _contagens_confusao(
        _to_int_labels(y_true), _to_int_labels(y_pred),
    )
    return _especificidade_de_contagens(tn, fp)


def sensibilidade(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Alias semântico de ``recall`` — alinha com a chave do YAML."""
    return recall(y_true, y_pred)


def metricas_completas(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    limiar: float = 0.5,
) -> dict[str, float]:
    """
    Dict com todas as métricas agregadas — pronto para ``Run.metrica(**d)``.

    ``pr_auc`` é **alias** de ``ap`` (ambos = ``average_precision_score``),
    mantido por compatibilidade com consumidores que usam esse nome (ex.: C4).
    """
    y      = _to_int_labels(y_true)
    p      = _to_np(y_prob)
    y_pred = (p >= limiar).astype(int)
    ap     = average_precision(y, p)

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
    Tabela com métricas para cada limiar em ``[0.01, 0.99]``.

    Colunas: ``limiar, tp, fp, tn, fn, f1, precision, recall,
    sensibilidade, especificidade, accuracy, youden_j``.

    ``youden_j`` = sensibilidade + especificidade − 1, útil para escolher
    o limiar que maximiza a separação entre as classes. As contagens de
    confusão ficam expostas para permitir derivar qualquer outra métrica
    a posteriori — não há tabela paralela de lambdas.
    """
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)

    linhas: list[dict[str, float]] = []

    for th in np.linspace(0.01, 0.99, n_limiares):
        lim    = float(th)
        y_pred = (p >= lim).astype(int)

        tp, fp, tn, fn = _contagens_confusao(y, y_pred)
        rec = recall(y, y_pred)
        esp = _especificidade_de_contagens(tn, fp)

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
            "youden_j":       rec + esp - 1.0,
        })

    return pd.DataFrame(linhas)


def ic_bootstrap(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    *,
    metrica: Callable[[ArrayLike, ArrayLike], float] = auc,
    n_boot: int | None = None,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float, float]:
    """
    Intervalo de confiança via bootstrap percentil.

    Retorna ``(estimativa, limite_inferior, limite_superior)``. Amostras
    degeneradas (uma única classe) são descartadas internamente. Métrica
    default é ``auc``; ``alpha=0.05`` corresponde a IC 95%.
    """
    y = _to_int_labels(y_true)
    if n_boot is None:
        from src.utils import config as C  # noqa: N812

        n_boot = int(C.cfg("avaliacao", "bootstrap", "repeticoes") or 200)
    p = _to_np(y_prob)
    n = len(y)

    rng     = np.random.default_rng(seed)
    valores = np.empty(n_boot, dtype="float64")

    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        valores[i] = (
            metrica(y[idx], p[idx]) if len(np.unique(y[idx])) >= 2 else np.nan
        )

    est     = float(metrica(y, p))
    validos = valores[~np.isnan(valores)]

    if validos.size == 0:
        return est, float("nan"), float("nan")

    return (
        est,
        float(np.quantile(validos, alpha / 2)),
        float(np.quantile(validos, 1 - alpha / 2)),
    )
def _niveis(prob: np.ndarray) -> tuple[np.ndarray, int]:
    """Códigos inteiros dos valores distintos de ``prob`` (ordem crescente)."""
    niveis, codigos = np.unique(prob, return_inverse=True)
    return codigos.astype(np.int64), int(niveis.size)


def _auc_ponderada(cod: np.ndarray, k: int, y: np.ndarray, w: np.ndarray) -> float:
    """AUC com pesos, tratando empates como metade (igual ao ``roc_auc_score``)."""
    pos = np.bincount(cod, weights=w * y, minlength=k)
    neg = np.bincount(cod, weights=w * (1.0 - y), minlength=k)
    total_pos, total_neg = pos.sum(), neg.sum()
    if total_pos <= 0 or total_neg <= 0:
        return float("nan")
    neg_abaixo = np.cumsum(neg) - neg
    return float((pos * (neg_abaixo + 0.5 * neg)).sum() / (total_pos * total_neg))


def _ap_ponderada(cod: np.ndarray, k: int, y: np.ndarray, w: np.ndarray) -> float:
    """Average precision com pesos (igual ao ``average_precision_score``)."""
    pos = np.bincount(cod, weights=w * y, minlength=k)[::-1]
    neg = np.bincount(cod, weights=w * (1.0 - y), minlength=k)[::-1]
    tp, fp = np.cumsum(pos), np.cumsum(neg)
    if tp[-1] <= 0:
        return float("nan")
    precisao = np.divide(tp, tp + fp, out=np.zeros_like(tp), where=(tp + fp) > 0)
    return float((pos / tp[-1] * precisao).sum())


def _brier_ponderado(y: np.ndarray, p: np.ndarray, w: np.ndarray) -> float:
    return float((w * (y - p) ** 2).sum() / w.sum())


def bootstrap_grupo(
    y_true: ArrayLike,
    prob_a: ArrayLike,
    grupos: ArrayLike,
    *,
    metrica: str = "auc",
    prob_b: ArrayLike | None = None,
    n: int | None = None,
    alpha: float = 0.05,
    seed: int | None = None,
) -> dict[str, float]:
    """Bootstrap por grupo (``group_id``) de AUC, AP ou Brier.

    Cada réplica sorteia grupos com reposição; todas as linhas do grupo entram juntas,
    com peso igual ao número de vezes sorteado. As probabilidades são ordenadas uma vez.
    Com ``prob_b``, o sorteio é o mesmo para os dois modelos e o resultado é a
    diferença A − B (IC percentil e p bilateral).
    """
    from src.utils import config as C  # noqa: N812

    if metrica not in {"auc", "ap", "brier"}:
        raise ValueError(f"metrica inválida: {metrica!r}. Use 'auc', 'ap' ou 'brier'.")
    n = int(n if n is not None else (C.cfg("avaliacao", "bootstrap", "repeticoes") or 1000))
    seed = int(seed if seed is not None else (C.cfg("avaliacao", "bootstrap", "seed") or 42))

    y = _to_int_labels(y_true).astype(np.float64)
    pa = _to_np(prob_a).astype(np.float64)
    pb = None if prob_b is None else _to_np(prob_b).astype(np.float64)
    cod_grupo = pd.factorize(np.asarray(grupos))[0]
    if (cod_grupo < 0).any():
        raise ValueError("grupos não pode ter valores ausentes.")
    n_grupos = int(cod_grupo.max()) + 1

    def calcular(p: np.ndarray, pre, w: np.ndarray) -> float:
        if metrica == "brier":
            return _brier_ponderado(y, p, w)
        cod, k = pre
        return (_auc_ponderada if metrica == "auc" else _ap_ponderada)(cod, k, y, w)

    pre_a = _niveis(pa) if metrica != "brier" else None
    pre_b = _niveis(pb) if (pb is not None and metrica != "brier") else None
    um = np.ones(len(y))

    est_a = calcular(pa, pre_a, um)
    est_b = calcular(pb, pre_b, um) if pb is not None else None

    rng = np.random.default_rng(seed)
    valores = np.full(n, np.nan)
    for i in range(n):
        sorteio = np.bincount(rng.integers(0, n_grupos, n_grupos), minlength=n_grupos)
        w = sorteio[cod_grupo].astype(np.float64)
        va = calcular(pa, pre_a, w)
        valores[i] = va if pb is None else va - calcular(pb, pre_b, w)

    validos = valores[~np.isnan(valores)]
    if validos.size == 0:
        raise ValueError("Nenhuma réplica com as duas classes: confira y_true e grupos.")
    inferior, superior = np.quantile(validos, [alpha / 2, 1 - alpha / 2])
    if pb is None:
        return {"estimativa": est_a, "ic_inferior": float(inferior), "ic_superior": float(superior),
                "n_validas": int(validos.size)}
    p_bilateral = min(1.0, 2 * min(float((validos <= 0).mean()), float((validos >= 0).mean())))
    return {"estimativa_diferenca": est_a - est_b, "ic_inferior": float(inferior),
            "ic_superior": float(superior), "p_bilateral": p_bilateral, "n_validas": int(validos.size)}