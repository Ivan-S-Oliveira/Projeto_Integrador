"""Mover para tests/test_errors.py."""
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from src.protocolo.metricas_por_grupo import metricas_por_grupo


def _dados(n=400, seed=0):
    rng = np.random.default_rng(seed)
    p = rng.uniform(0.01, 0.9, n)
    y = (rng.random(n) < p).astype(int)
    return y, p


def test_valores_batem_com_sklearn():
    y, p = _dados()
    r = metricas_por_grupo(y, p, ["a"] * len(y)).iloc[0]
    assert r["n"] == len(y) and r["obitos"] == y.sum()
    assert r["pr_auc"] == pytest.approx(average_precision_score(y, p))
    assert r["roc_auc"] == pytest.approx(roc_auc_score(y, p))
    assert r["brier"] == pytest.approx(brier_score_loss(y, p))
    assert r["pr_auc_sobre_prev"] == pytest.approx(r["pr_auc"] / y.mean())
    assert r["o_e"] == pytest.approx(y.sum() / p.sum())
    assert not r["suprimido"]


def test_grupo_so_de_curas_devolve_vazio_sem_erro():
    y, p = _dados()
    g = np.array(["a"] * 200 + ["so_curas"] * 200)
    y = y.copy(); y[200:] = 0
    r = metricas_por_grupo(y, p, g).set_index("grupo")
    assert r.loc["so_curas", ["pr_auc", "roc_auc", "brier", "o_e"]].isna().all()
    assert r.loc["so_curas", "n"] == 200 and not r.loc["so_curas", "suprimido"]
    assert not np.isnan(r.loc["a", "pr_auc"])


def test_grupo_so_de_obitos_devolve_vazio_sem_erro():
    y, p = _dados()
    y = y.copy(); y[200:] = 1
    r = metricas_por_grupo(y, p, ["a"] * 200 + ["so_obitos"] * 200).set_index("grupo")
    assert r.loc["so_obitos", ["pr_auc", "roc_auc"]].isna().all()


def test_grupo_pequeno_e_suprimido():
    y, p = _dados()
    g = np.array(["grande"] * 350 + ["pequeno"] * 50)
    r = metricas_por_grupo(y, p, g, min_n=100).set_index("grupo")
    assert r.loc["pequeno", "suprimido"] and r.loc["pequeno", "n"] == 50
    assert r.loc["pequeno", ["pr_auc", "roc_auc", "brier", "o_e"]].isna().all()
    assert not r.loc["grande", "suprimido"]


def test_grupo_ausente_nao_some():
    y, p = _dados()
    g = pd.Series(["a"] * 300 + [None] * 100)
    r = metricas_por_grupo(y, p, g)
    assert "ausente" in set(r["grupo"]) and r["n"].sum() == len(y)


def test_tamanhos_diferentes_levantam_erro():
    with pytest.raises(ValueError):
        metricas_por_grupo([0, 1], [0.1], ["a", "a"])
