from __future__ import annotations

from typing import Callable, Literal, Iterable, TypeAlias, get_args
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
from dataclasses import dataclass, field

from src import config as C


ArrayLike: TypeAlias = np.ndarray | pd.Series | list


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
    denom = tn + fp
    return tn / denom if denom > 0 else 0.0


def auc(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(roc_auc_score(_to_int_labels(y_true), _to_np(y_prob)))


def average_precision(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(average_precision_score(_to_int_labels(y_true), _to_np(y_prob)))


def brier(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    return float(brier_score_loss(_to_int_labels(y_true), _to_np(y_prob)))


def log_loss(y_true: ArrayLike, y_prob: ArrayLike) -> float:
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
    _, fp, tn, _ = _contagens_confusao(
        _to_int_labels(y_true), _to_int_labels(y_pred),
    )
    return _especificidade_de_contagens(tn, fp)


def sensibilidade(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    return recall(y_true, y_pred)


def metricas_completas(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    limiar: float = 0.5,
) -> dict[str, float]:
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
    y = _to_int_labels(y_true)
    if n_boot is None:
        from src import config as C

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
    niveis, codigos = np.unique(prob, return_inverse=True)
    return codigos.astype(np.int64), int(niveis.size)


def _auc_ponderada(cod: np.ndarray, k: int, y: np.ndarray, w: np.ndarray) -> float:
    pos = np.bincount(cod, weights=w * y, minlength=k)
    neg = np.bincount(cod, weights=w * (1.0 - y), minlength=k)
    total_pos, total_neg = pos.sum(), neg.sum()
    if total_pos <= 0 or total_neg <= 0:
        return float("nan")
    neg_abaixo = np.cumsum(neg) - neg
    return float((pos * (neg_abaixo + 0.5 * neg)).sum() / (total_pos * total_neg))


def _ap_ponderada(cod: np.ndarray, k: int, y: np.ndarray, w: np.ndarray) -> float:
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
    from src import config as C

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
    assert est_b is not None
    p_bilateral = min(1.0, 2 * min(float((validos <= 0).mean()), float((validos >= 0).mean())))
    return {"estimativa_diferenca": est_a - est_b, "ic_inferior": float(inferior),
            "ic_superior": float(superior), "p_bilateral": p_bilateral, "n_validas": int(validos.size)}



def _bins_digitize(p: np.ndarray, n_bins: int) -> np.ndarray:
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
    tabela = curva_confiabilidade(y_true, y_prob, n_bins=n_bins)
    gaps   = tabela["gap"].dropna()

    if gaps.empty:
        return float("nan")

    return float(gaps.max())


def _bins_quantis(p: np.ndarray, n_bins: int) -> np.ndarray:
    quantis = np.linspace(0.0, 1.0, n_bins + 1)
    edges = np.unique(np.quantile(p, quantis))
    if edges.size < 2:
        edges = np.array([0.0, 1.0])
    return edges


def curva_confiabilidade_quantis(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> pd.DataFrame:
    y = _to_int_labels(y_true)
    p = _to_np(y_prob)
    edges = _bins_quantis(p, n_bins)
    idx = np.clip(np.digitize(p, edges[1:-1], right=True), 0, edges.size - 2)

    linhas: list[dict[str, float]] = []
    for b in range(edges.size - 1):
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


def ece_quantis(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> float:
    tabela = curva_confiabilidade_quantis(y_true, y_prob, n_bins=n_bins)
    total  = float(tabela["n"].sum())

    if total == 0:
        return float("nan")

    pesos = tabela["n"] / total
    gaps  = tabela["gap"].fillna(0.0)
    return float((pesos * gaps).sum())


def mce_quantis(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> float:
    tabela = curva_confiabilidade_quantis(y_true, y_prob, n_bins=n_bins)
    gaps   = tabela["gap"].dropna()

    if gaps.empty:
        return float("nan")

    return float(gaps.max())


def brier_decomposicao(
    y_true: ArrayLike,
    y_prob: ArrayLike,
    n_bins: int = 10,
) -> dict[str, float]:
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

CriterioTop = Literal["fp", "fn", "erro_absoluto"]


def _validar_tamanhos(df: pd.DataFrame, y: np.ndarray) -> None:
    if len(df) != len(y):
        raise ValueError(f"df tem {len(df)} linhas e y_true tem {len(y)}.")


def matriz_confusao(
    y_true: ArrayLike,
    y_pred: ArrayLike,
) -> pd.DataFrame:
    y = _to_int_labels(y_true)
    p = _to_int_labels(y_pred)

    contagens = {
        (yv, pv): int(((y == yv) & (p == pv)).sum())
        for yv in (0, 1)
        for pv in (0, 1)
    }

    df = pd.DataFrame(
        [[contagens[(0, 0)], contagens[(0, 1)]],
         [contagens[(1, 0)], contagens[(1, 1)]]],
        index=["real_0", "real_1"],
        columns=["pred_0", "pred_1"],
    )
    df["total"] = df.sum(axis=1)
    df.loc["total"] = df.sum(axis=0)
    return df


def metricas_por_grupo(
    df: pd.DataFrame,
    y_true: ArrayLike,
    y_prob: ArrayLike,
    coluna_grupo: str,
    *,
    limiar: float = 0.5,
    min_n: int = 100,
) -> pd.DataFrame:
    if coluna_grupo not in df.columns:
        raise KeyError(f"Coluna de grupo ausente: {coluna_grupo!r}")

    y = _to_int_labels(y_true)
    p = _to_np(y_prob)
    _validar_tamanhos(df, y)

    base   = df.reset_index(drop=True)
    grupos = base[coluna_grupo].astype("string")

    linhas: list[dict[str, float | str]] = []

    for g in grupos.dropna().unique():
        m = (grupos == g).to_numpy()
        n = int(m.sum())

        y_g    = y[m]
        p_g    = p[m]

        duas_classes = len(np.unique(y_g)) >= 2

        if n < min_n:
            linhas.append({
                "grupo":            str(g),
                "n":                float(n),
                "prevalencia":      float(y_g.mean()) if n > 0 else np.nan,
                "taxa_positivos":   float(y_g.mean()) if n > 0 else np.nan,
                "pr_auc":           np.nan,
                "pr_auc_sobre_prev":np.nan,
                "auc":              np.nan,
                "roc_auc":          np.nan,
                "brier":            np.nan,
                "o_e":              np.nan,
                "f1":               np.nan,
                "precision":        np.nan,
                "recall":           np.nan,
                "suprimido":        True,
            })
            continue

        y_pred = (p_g >= limiar).astype(int)

        pr_auc = (
            float(average_precision_score(y_g, p_g))
            if duas_classes else np.nan
        )
        prevalencia = float(y_g.mean()) if n > 0 else np.nan
        pr_auc_sobre_prev = (
            pr_auc / prevalencia
            if not np.isnan(pr_auc) and prevalencia > 0
            else np.nan
        )
        roc_auc = auc(y_g, p_g) if duas_classes else np.nan
        brier   = (
            float(brier_score_loss(y_g, p_g))
            if duas_classes else np.nan
        )
        soma_p  = float(p_g.sum())
        o_e     = (
            float(y_g.sum()) / soma_p
            if duas_classes and soma_p > 0 else np.nan
        )

        linhas.append({
            "grupo":            str(g),
            "n":                float(n),
            "prevalencia":      prevalencia,
            "taxa_positivos":   prevalencia,
            "pr_auc":           pr_auc,
            "pr_auc_sobre_prev":pr_auc_sobre_prev,
            "auc":              roc_auc,
            "roc_auc":          roc_auc,
            "brier":            brier,
            "o_e":              o_e,
            "f1":               f1(y_g, y_pred),
            "precision":        precision(y_g, y_pred),
            "recall":           recall(y_g, y_pred),
            "suprimido":        False,
        })

    return (
        pd.DataFrame(linhas)
        .sort_values(["suprimido", "n"], ascending=[True, False])
        .reset_index(drop=True)
    )


class LeakageError(RuntimeError):
    pass


DEFAULT_LEAKAGE_COLUMNS = frozenset({
    "evolucao", "dt_evoluca", "dt_encerra",
    "uti", "utilizouvni", "suport_ven",
    "antiviral", "antivirais",
    "classificacao_final",
    "cluster", "cluster_rotulo",
})


def _resolve_forbidden_columns(
    forbidden_columns: Iterable[str] | None,
    target_column: str | None,
) -> set[str]:
    base = (
        set(forbidden_columns)
        if forbidden_columns is not None
        else set(C.cfg("features", "proibidas") or [])
    )
    base |= DEFAULT_LEAKAGE_COLUMNS

    target = target_column if target_column is not None else C.cfg("target", "coluna")
    if target:
        base.add(target)
    return base


def check_leakage(
    X: pd.DataFrame,
    *,
    forbidden_columns: Iterable[str] | None = None,
    target_column: str | None = None,
) -> None:
    forbidden = _resolve_forbidden_columns(forbidden_columns, target_column)
    if detected := sorted(set(X.columns) & forbidden):
        raise LeakageError(f"Variáveis de leakage detectadas: {', '.join(detected)}")
