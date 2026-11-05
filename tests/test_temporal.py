"""Split temporal, holdout e métricas por grupo."""

from __future__ import annotations

import pandas as pd
import pytest
from src.avaliacao import TemporalSplit, split_temporal_3way
from src import config as C
import numpy as np
from src.avaliacao import matriz_confusao, metricas_por_grupo


@pytest.fixture
def df_temporal() -> pd.DataFrame:
    """100 dias consecutivos a partir de 2020-01-01, coluna ``x`` = range(100)."""
    return pd.DataFrame({
        "data": pd.date_range("2020-01-01", periods=100, freq="D"),
        "x":    range(100),
    })


@pytest.fixture
def df_temporal_com_nat(df_temporal: pd.DataFrame) -> pd.DataFrame:
    """``df_temporal`` com ``NaT`` na linha 5 da coluna ``data``."""
    df = df_temporal.copy()
    df.loc[5, "data"] = pd.NaT
    return df


def test_split_temporal_ordem_correta(df_temporal: pd.DataFrame) -> None:
    """Sem sobreposição temporal entre blocos; proporções 70/15/15."""
    treino, validacao, holdout = split_temporal_3way(df_temporal, "data")

    assert treino["data"].max() <= validacao["data"].min()
    assert validacao["data"].max() <= holdout["data"].min()
    assert len(treino) == 70
    assert len(validacao) == 15
    assert len(holdout) == 15


def test_coluna_tempo_ausente(df_temporal: pd.DataFrame) -> None:
    with pytest.raises(KeyError):
        split_temporal_3way(df_temporal, "coluna_inexistente")


def test_on_nat_raise(df_temporal_com_nat: pd.DataFrame) -> None:
    with pytest.raises(ValueError):
        split_temporal_3way(df_temporal_com_nat, "data", on_nat="raise")


def test_holdout_bloqueado_por_padrao(df_temporal: pd.DataFrame) -> None:
    split = TemporalSplit(df_temporal, "data")
    assert not split.holdout_liberado
    with pytest.raises(RuntimeError):
        split.holdout()


def test_holdout_liberado_apos_gate(
    df_temporal: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Com ``G9_holdout`` aprovado, ``concluir_selecao()`` libera o holdout."""
    monkeypatch.setattr(C, "cfg", lambda *a, **kw: {"status": "aprovado"})

    split = TemporalSplit(df_temporal, "data")
    split.concluir_selecao()

    assert split.holdout_liberado
    assert len(split.holdout()) == 15


def test_treino_validacao_nao_expoe_holdout(df_temporal: pd.DataFrame) -> None:
    split = TemporalSplit(df_temporal, "data")
    treino, validacao = split.treino_validacao()

    assert treino is split.treino
    assert validacao is split.validacao


@pytest.fixture
def y_true_y_pred() -> tuple[np.ndarray, np.ndarray]:
    """8 amostras com falsos positivos e negativos plantados.

    Labels (não probabilidades) — para ``top_erros``, cada teste constrói
    os seus próprios dados.
    """
    y_true = np.array([0, 0, 1, 1, 0, 1, 0, 1])
    y_pred = np.array([0, 1, 1, 0, 0, 1, 1, 1])
    return y_true, y_pred


def test_matriz_confusao_shape_e_valores(y_true_y_pred) -> None:
    y_true, y_pred = y_true_y_pred
    m = matriz_confusao(y_true, y_pred)
    assert {"pred_0", "pred_1"}.issubset(m.columns)
    assert {"real_0", "real_1"}.issubset(m.index)
    assert m.loc["real_0", "pred_1"] == 2
    assert m.loc["real_1", "pred_0"] == 1


def test_metricas_por_grupo_suprime_abaixo_de_min_n() -> None:
    """Grupo com menos de ``min_n`` continua na tabela com ``suprimido=True``."""
    df = pd.DataFrame({"grupo": ["A"] * 5 + ["B"] * 300})
    y = pd.Series([0, 1] * 152 + [0])
    p = pd.Series([0.1, 0.9] * 152 + [0.5])

    r = metricas_por_grupo(df, y, p, "grupo", min_n=30).set_index("grupo")
    assert set(r.index) == {"A", "B"}
    assert bool(r.loc["A", "suprimido"]) is True
    assert pd.isna(r.loc["A", "pr_auc"])
    assert bool(r.loc["B", "suprimido"]) is False
    assert r.loc["B", "n"] == 300


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
