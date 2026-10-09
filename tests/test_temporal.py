"""Testes do split temporal e da trava do holdout (gate G7)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.evaluation.temporal import TemporalSplit, split_temporal_3way


def _df(n: int = 100) -> pd.DataFrame:
    return pd.DataFrame({
        "dt_notific": pd.date_range("2020-01-01", periods=n, freq="D"),
        "valor": range(n),
    })


# ---------------------------------------------------------------------------
# split_temporal_3way
# ---------------------------------------------------------------------------

def test_split_3way_ordem():
    tr, va, ho = split_temporal_3way(_df(), coluna_tempo="dt_notific")
    assert tr["dt_notific"].max() <= va["dt_notific"].min()
    assert va["dt_notific"].max() <= ho["dt_notific"].min()


def test_split_3way_coluna_ausente():
    with pytest.raises(KeyError):
        split_temporal_3way(pd.DataFrame({"x": [1]}), coluna_tempo="dt_notific")


def test_split_3way_coluna_nao_datetime():
    df = pd.DataFrame({"dt_notific": ["2020-01-01", "2020-01-02", "2020-01-03"]})
    with pytest.raises(TypeError):
        split_temporal_3way(df, coluna_tempo="dt_notific")


def test_split_3way_nat_default_levanta():
    df = _df(10)
    df.loc[3, "dt_notific"] = pd.NaT
    with pytest.raises(ValueError, match="data inválida"):
        split_temporal_3way(df, coluna_tempo="dt_notific")


def test_split_3way_nat_drop():
    df = _df(10)
    df.loc[3, "dt_notific"] = pd.NaT
    tr, va, ho = split_temporal_3way(df, coluna_tempo="dt_notific", on_nat="drop")
    assert len(tr) + len(va) + len(ho) == 9


def test_split_3way_on_nat_invalido():
    with pytest.raises(ValueError, match="on_nat"):
        split_temporal_3way(_df(), coluna_tempo="dt_notific", on_nat="xxx") # type: ignore[arg-type]


def test_split_3way_fracoes_invalidas():
    with pytest.raises(ValueError):
        split_temporal_3way(
            _df(), coluna_tempo="dt_notific",
            frac_treino=0.9, frac_validacao=0.2,
        )


def test_split_3way_dataset_minusculo():
    with pytest.raises(ValueError, match="pequeno demais"):
        split_temporal_3way(
            pd.DataFrame({"dt_notific": [pd.Timestamp("2020-01-01")]}),
            coluna_tempo="dt_notific",
        )


# ---------------------------------------------------------------------------
# TemporalSplit
# ---------------------------------------------------------------------------

def test_temporal_split_propriedades():
    split = TemporalSplit(df=_df(), coluna_tempo="dt_notific")
    assert split.n_treino + split.n_validacao + split.n_holdout == 100


def test_holdout_bloqueado_inicialmente():
    split = TemporalSplit(df=_df(), coluna_tempo="dt_notific")
    assert not split.holdout_liberado
    with pytest.raises(RuntimeError, match="Holdout bloqueado"):
        split.holdout()


# ---------------------------------------------------------------------------
# Gate G7
# ---------------------------------------------------------------------------

def test_concluir_selecao_exige_gate_g7(monkeypatch):
    """Com `G7_limiar` pendente, `concluir_selecao()` levanta RuntimeError."""
    from src.utils import config as C

    monkeypatch.setattr(
        C, "cfg",
        lambda *k, default=None: (
            {"status": "pendente"} if k == ("gates", "G7_limiar") else default
        ),
    )

    split = TemporalSplit(df=_df(), coluna_tempo="dt_notific")
    with pytest.raises(RuntimeError, match="G7_limiar"):
        split.concluir_selecao()
    assert not split.holdout_liberado


def test_concluir_selecao_libera_quando_gate_aprovado(monkeypatch):
    """Com `G7_limiar` aprovado, `concluir_selecao()` libera o holdout."""
    from src.utils import config as C

    monkeypatch.setattr(
        C, "cfg",
        lambda *k, default=None: (
            {"status": "aprovado"} if k == ("gates", "G7_limiar") else default
        ),
    )

    split = TemporalSplit(df=_df(), coluna_tempo="dt_notific")
    split.concluir_selecao()
    assert split.holdout_liberado
    assert not split.holdout().empty


def test_resumo_nao_quebra():
    split = TemporalSplit(df=_df(), coluna_tempo="dt_notific")
    txt = split.resumo()
    assert "TemporalSplit" in txt
    assert "treino" in txt
    assert "holdout" in txt