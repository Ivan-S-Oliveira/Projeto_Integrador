"""Testes de análise de erros em ``src.evaluation.errors``."""

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
def y_true_y_pred() -> tuple[np.ndarray, np.ndarray]:
    """8 amostras com falsos positivos e negativos plantados.

    Labels (não probabilidades) — para ``top_erros``, cada teste constrói
    os seus próprios dados.
    """
    y_true = np.array([0, 0, 1, 1, 0, 1, 0, 1])
    y_pred = np.array([0, 1, 1, 0, 0, 1, 1, 1])
    return y_true, y_pred


def _df_com_indice(n: int) -> pd.DataFrame:
    """DataFrame ``{"x": range(n)}`` — índice rastreável nos testes de extração."""
    return pd.DataFrame({"x": range(n)})


# ---------------------------------------------------------------------------
# matriz_confusao
# ---------------------------------------------------------------------------

def test_matriz_confusao_shape_e_valores(y_true_y_pred) -> None:
    y_true, y_pred = y_true_y_pred
    m = matriz_confusao(y_true, y_pred)
    assert {"pred_0", "pred_1"}.issubset(m.columns)
    assert {"real_0", "real_1"}.issubset(m.index)
    assert m.loc["real_0", "pred_1"] == 2
    assert m.loc["real_1", "pred_0"] == 1


def test_matriz_confusao_tem_totais(y_true_y_pred) -> None:
    y_true, y_pred = y_true_y_pred
    m = matriz_confusao(y_true, y_pred)
    assert "total" in m.columns
    assert "total" in m.index
    assert m.loc["total", "total"] == len(y_true)


# ---------------------------------------------------------------------------
# extrair_falsos_*
# ---------------------------------------------------------------------------

def test_extrair_fp(y_true_y_pred) -> None:
    y_true, y_pred = y_true_y_pred
    fp = extrair_falsos_positivos(_df_com_indice(len(y_true)), y_true, y_pred)
    assert len(fp) == 2
    assert set(fp["x"]) == {1, 6}


def test_extrair_fn(y_true_y_pred) -> None:
    y_true, y_pred = y_true_y_pred
    fn = extrair_falsos_negativos(_df_com_indice(len(y_true)), y_true, y_pred)
    assert len(fn) == 1
    assert fn["x"].iloc[0] == 3


# ---------------------------------------------------------------------------
# metricas_por_grupo
# ---------------------------------------------------------------------------

def test_metricas_por_grupo_coluna_renomeada() -> None:
    """A coluna de prevalência chama-se ``taxa_positivos``, não ``positivos``."""
    n = 300
    df = pd.DataFrame({"grupo": ["A"] * n + ["B"] * n})
    y = pd.Series(np.tile([0, 1], n))
    p = pd.Series(np.tile([0.1, 0.9], n))

    r = metricas_por_grupo(df, y, p, "grupo", min_n=10)
    assert "taxa_positivos" in r.columns
    assert "positivos" not in r.columns


def test_metricas_por_grupo_ignora_abaixo_de_min_n() -> None:
    """Grupo com menos de ``min_n`` é excluído do resultado."""
    df = pd.DataFrame({"grupo": ["A"] * 5 + ["B"] * 300})
    y = pd.Series([0, 1] * 152 + [0])
    p = pd.Series([0.1, 0.9] * 152 + [0.5])

    r = metricas_por_grupo(df, y, p, "grupo", min_n=30)
    assert set(r["grupo"]) == {"B"}
    assert r.loc[r["grupo"] == "B", "n"].iloc[0] == 300


def test_metricas_por_grupo_coluna_ausente() -> None:
    df = pd.DataFrame({"outra": [1, 2]})
    with pytest.raises(KeyError):
        metricas_por_grupo(df, np.array([0, 1]), np.array([0.1, 0.9]), "grupo")


def test_metricas_por_grupo_tamanho_incompativel() -> None:
    """``df`` (5 linhas) com ``y`` (6 linhas) deve falhar antes de agregar."""
    df = pd.DataFrame({"grupo": ["A"] * 5})
    y = np.array([0, 1, 0, 1, 0, 1])
    p = np.array([0.1, 0.9, 0.2, 0.8, 0.3, 0.7])
    with pytest.raises(ValueError):
        metricas_por_grupo(df, y, p, "grupo")


# ---------------------------------------------------------------------------
# top_erros
# ---------------------------------------------------------------------------

def test_top_erros_erro_absoluto() -> None:
    """Adiciona ``y_true``, ``y_prob``, ``y_pred``, ``erro_abs`` ao DataFrame."""
    df = pd.DataFrame({"x": range(6)})
    y_true = np.array([0, 0, 1, 1, 0, 1])
    y_prob = np.array([0.1, 0.9, 0.1, 0.9, 0.5, 0.5])

    t = top_erros(df, y_true, y_prob, n=3, criterio="erro_absoluto")
    assert len(t) == 3
    for c in ("y_true", "y_prob", "y_pred", "erro_abs"):
        assert c in t.columns


def test_top_erros_fp_ordena_por_prob_decrescente() -> None:
    df = pd.DataFrame({"x": range(5)})
    y_true = np.array([0, 0, 1, 1, 0])
    y_prob = np.array([0.1, 0.9, 0.1, 0.9, 0.6])

    t = top_erros(df, y_true, y_prob, n=5, criterio="fp")
    assert (t["y_true"] == 0).all()
    assert (t["y_pred"] == 1).all()
    assert t["y_prob"].is_monotonic_decreasing


def test_top_erros_fn_ordena_por_prob_crescente() -> None:
    df = pd.DataFrame({"x": range(5)})
    y_true = np.array([0, 0, 1, 1, 1])
    y_prob = np.array([0.1, 0.9, 0.1, 0.4, 0.9])

    t = top_erros(df, y_true, y_prob, n=5, criterio="fn")
    assert (t["y_true"] == 1).all()
    assert (t["y_pred"] == 0).all()
    assert t["y_prob"].is_monotonic_increasing


def test_top_erros_criterio_invalido() -> None:
    df = pd.DataFrame({"x": [1, 2]})
    # Valor viola intencionalmente o Literal CriterioTop.
    with pytest.raises(ValueError, match="criterio inválido"):
        top_erros(df, np.array([0, 1]), np.array([0.1, 0.9]), criterio="xxx")  # type: ignore[arg-type]
        import numpy as np
import pandas as pd

from src.evaluation.errors import metricas_por_grupo


def test_grupo_so_de_curas_devolve_pr_auc_vazia():
    """Card #? — grupo com uma classe só devolve PR-AUC/Brier vazios, sem erro."""
    df = pd.DataFrame({"uf": ["SP"] * 200})
    y_true = np.zeros(200, dtype=np.int8)
    y_prob = np.full(200, 0.1, dtype=np.float64)

    out = metricas_por_grupo(
        df, y_true, y_prob, "uf", limiar=0.5, min_n=100,
    )

    assert len(out) == 1
    linha = out.iloc[0]
    assert linha["n"] == 200
    assert linha["prevalencia"] == 0.0
    assert pd.isna(linha["pr_auc"])
    assert pd.isna(linha["pr_auc_sobre_prev"])
    assert pd.isna(linha["roc_auc"])
    assert pd.isna(linha["brier"])
    assert pd.isna(linha["o_e"])
    assert linha["suprimido"] == False  # noqa: E712


def test_grupo_pequeno_e_suprimido_sem_desaparecer():
    """Card #? — grupo com n < min_n aparece com suprimido=True."""
    df = pd.DataFrame({"uf": ["SP"] * 50 + ["RJ"] * 200})
    y_true = np.array([0] * 50 + [0, 1] * 100, dtype=np.int8)
    y_prob = np.random.default_rng(42).random(250)

    out = metricas_por_grupo(
        df, y_true, y_prob, "uf", limiar=0.5, min_n=100,
    )

    assert set(out["grupo"]) == {"SP", "RJ"}
    sp = out.set_index("grupo").loc["SP"]
    rj = out.set_index("grupo").loc["RJ"]
    assert sp["suprimido"] == True  # noqa: E712
    assert pd.isna(sp["pr_auc"])
    assert rj["suprimido"] == False  # noqa: E712
    assert not pd.isna(rj["pr_auc"])
    assert not pd.isna(rj["brier"])
    assert not pd.isna(rj["o_e"])


def test_duas_classes_calcula_tudo():
    """Sanidade — grupo com duas classes preenche todas as métricas."""
    df = pd.DataFrame({"uf": ["SP"] * 200})
    rng = np.random.default_rng(42)
    y_true = rng.integers(0, 2, size=200, dtype=np.int8)
    y_prob = rng.random(200)

    out = metricas_por_grupo(
        df, y_true, y_prob, "uf", limiar=0.5, min_n=100,
    )

    linha = out.iloc[0]
    assert not pd.isna(linha["pr_auc"])
    assert not pd.isna(linha["pr_auc_sobre_prev"])
    assert not pd.isna(linha["roc_auc"])
    assert not pd.isna(linha["brier"])
    assert not pd.isna(linha["o_e"])
    assert linha["suprimido"] == False  # noqa: E712