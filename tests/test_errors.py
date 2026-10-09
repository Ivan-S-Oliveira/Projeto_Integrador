"""Testes de análise de erros em `src.evaluation.errors`."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.evaluation.errors import (
    extrair_falsos_negativos,
    extrair_falsos_positivos,
    matriz_confusao,
    metricas_por_grupo,
    top_erros,
)


@pytest.fixture
def dados():
    #         idx: 0  1  2  3  4  5  6  7
    y_true = np.array([0, 0, 1, 1, 0, 1, 0, 1])
    y_pred = np.array([0, 1, 1, 0, 0, 1, 1, 1])
    # fp: 1, 6  |  fn: 3
    return y_true, y_pred


# ---------------------------------------------------------------------------
# Matriz de confusão
# ---------------------------------------------------------------------------

def test_matriz_confusao_shape_e_valores(dados):
    y_true, y_pred = dados
    m = matriz_confusao(y_true, y_pred)
    assert {"pred_0", "pred_1"}.issubset(m.columns)
    assert {"real_0", "real_1"}.issubset(m.index)
    assert m.loc["real_0", "pred_1"] == 2  # FP
    assert m.loc["real_1", "pred_0"] == 1  # FN


def test_matriz_confusao_tem_totais(dados):
    y_true, y_pred = dados
    m = matriz_confusao(y_true, y_pred)
    assert "total" in m.columns
    assert "total" in m.index
    assert m.loc["total", "total"] == len(y_true)


# ---------------------------------------------------------------------------
# Extração de FP/FN
# ---------------------------------------------------------------------------

def test_extrair_fp(dados):
    y_true, y_pred = dados
    df = pd.DataFrame({"x": range(len(y_true))})
    fp = extrair_falsos_positivos(df, y_true, y_pred)
    assert len(fp) == 2
    assert set(fp["x"]) == {1, 6}


def test_extrair_fn(dados):
    y_true, y_pred = dados
    df = pd.DataFrame({"x": range(len(y_true))})
    fn = extrair_falsos_negativos(df, y_true, y_pred)
    assert len(fn) == 1
    assert fn["x"].iloc[0] == 3


# ---------------------------------------------------------------------------
# Métricas por grupo
# ---------------------------------------------------------------------------

def test_metricas_por_grupo_coluna_renomeada():
    """A coluna de prevalência chama-se `taxa_positivos` (não `positivos`)."""
    n = 300
    df = pd.DataFrame({"grupo": ["A"] * n + ["B"] * n})
    y = pd.Series(np.tile([0, 1], n))
    p = pd.Series(np.tile([0.1, 0.9], n))

    r = metricas_por_grupo(df, y, p, "grupo", min_n=10)
    assert "taxa_positivos" in r.columns
    assert "positivos" not in r.columns


def test_metricas_por_grupo_ignora_abaixo_de_min_n():
    df = pd.DataFrame({"grupo": ["A"] * 5 + ["B"] * 300})
    y = pd.Series([0, 1] * 150 + [0, 1] * 3 + [0, 0])
    p = pd.Series([0.1, 0.9] * 152 + [0.5])

    r = metricas_por_grupo(df, y, p, "grupo", min_n=30)
    assert "A" not in set(r["grupo"])
    assert "B" in set(r["grupo"])


def test_metricas_por_grupo_coluna_ausente():
    df = pd.DataFrame({"outra": [1, 2]})
    y = np.array([0, 1])
    p = np.array([0.1, 0.9])
    with pytest.raises(KeyError):
        metricas_por_grupo(df, y, p, "grupo")


def test_metricas_por_grupo_tamanho_incompativel():
    df = pd.DataFrame({"grupo": ["A"] * 5})
    y = np.array([0, 1, 0, 1, 0, 1])  # 6 ≠ 5
    p = np.array([0.1, 0.9, 0.2, 0.8, 0.3, 0.7])
    with pytest.raises(ValueError):
        metricas_por_grupo(df, y, p, "grupo")


# ---------------------------------------------------------------------------
# Top erros
# ---------------------------------------------------------------------------

def test_top_erros_erro_absoluto():
    df = pd.DataFrame({"x": range(6)})
    y_true = np.array([0, 0, 1, 1, 0, 1])
    y_prob = np.array([0.1, 0.9, 0.1, 0.9, 0.5, 0.5])

    t = top_erros(df, y_true, y_prob, n=3, criterio="erro_absoluto")
    assert len(t) == 3
    for c in ("y_true", "y_prob", "y_pred", "erro_abs"):
        assert c in t.columns


def test_top_erros_fp_ordena_por_prob_decrescente():
    df = pd.DataFrame({"x": range(5)})
    y_true = np.array([0, 0, 1, 1, 0])
    y_prob = np.array([0.1, 0.9, 0.1, 0.9, 0.6])

    t = top_erros(df, y_true, y_prob, n=5, criterio="fp")
    assert (t["y_true"] == 0).all()
    assert (t["y_pred"] == 1).all()
    assert t["y_prob"].is_monotonic_decreasing


def test_top_erros_fn_ordena_por_prob_crescente():
    df = pd.DataFrame({"x": range(5)})
    y_true = np.array([0, 0, 1, 1, 1])
    y_prob = np.array([0.1, 0.9, 0.1, 0.4, 0.9])

    t = top_erros(df, y_true, y_prob, n=5, criterio="fn")
    assert (t["y_true"] == 1).all()
    assert (t["y_pred"] == 0).all()
    assert t["y_prob"].is_monotonic_increasing


def test_top_erros_criterio_invalido():
    df = pd.DataFrame({"x": [1, 2]})
    y_true = np.array([0, 1])
    y_prob = np.array([0.1, 0.9])
    with pytest.raises(ValueError, match="criterio inválido"):
        top_erros(df, y_true, y_prob, criterio="xxx")  # type: ignore[arg-type]