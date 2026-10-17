"""
Testes do split temporal em três blocos e da trava do holdout.

Cobrem garantia de não sobreposição temporal, validação de frações e
coluna temporal, tratamento de ``NaT`` e liberação do holdout apenas com
``G9_holdout`` aprovado.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.evaluation.temporal import TemporalSplit, split_temporal_3way
from src.utils import config as C


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


# ---------------------------------------------------------------------------
# split_temporal_3way — ordem e proporções
# ---------------------------------------------------------------------------

def test_split_temporal_ordem_correta(df_temporal: pd.DataFrame) -> None:
    """Sem sobreposição temporal entre blocos; proporções 70/15/15."""
    treino, validacao, holdout = split_temporal_3way(df_temporal, "data")

    assert treino["data"].max() <= validacao["data"].min()
    assert validacao["data"].max() <= holdout["data"].min()
    assert len(treino) == 70
    assert len(validacao) == 15
    assert len(holdout) == 15


def test_split_temporal_preserva_ordem(df_temporal: pd.DataFrame) -> None:
    treino, validacao, holdout = split_temporal_3way(df_temporal, "data")

    assert treino["data"].is_monotonic_increasing
    assert validacao["data"].is_monotonic_increasing
    assert holdout["data"].is_monotonic_increasing


# ---------------------------------------------------------------------------
# split_temporal_3way — validações de parâmetros
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "kwargs",
    [
        {"frac_treino": 0},
        {"frac_treino": 1},
        {"frac_validacao": 0},
        {"frac_validacao": 1},
        {"frac_treino": 0.8, "frac_validacao": 0.3},
    ],
    ids=[
        "frac_treino_zero",
        "frac_treino_um",
        "frac_validacao_zero",
        "frac_validacao_um",
        "soma_maior_que_1",
    ],
)
def test_fracoes_invalidas(df_temporal: pd.DataFrame, kwargs: dict) -> None:
    with pytest.raises(ValueError):
        split_temporal_3way(df_temporal, "data", **kwargs)


def test_coluna_tempo_ausente(df_temporal: pd.DataFrame) -> None:
    with pytest.raises(KeyError):
        split_temporal_3way(df_temporal, "coluna_inexistente")


def test_coluna_tempo_nao_datetime(df_temporal: pd.DataFrame) -> None:
    df = df_temporal.copy()
    df["data"] = df["data"].astype(str)
    with pytest.raises(TypeError):
        split_temporal_3way(df, "data")


# ---------------------------------------------------------------------------
# split_temporal_3way — tratamento de NaT
# ---------------------------------------------------------------------------

def test_on_nat_raise(df_temporal_com_nat: pd.DataFrame) -> None:
    with pytest.raises(ValueError):
        split_temporal_3way(df_temporal_com_nat, "data", on_nat="raise")


def test_on_nat_drop(df_temporal_com_nat: pd.DataFrame) -> None:
    treino, validacao, holdout = split_temporal_3way(
        df_temporal_com_nat, "data", on_nat="drop",
    )
    assert len(treino) + len(validacao) + len(holdout) == 99


def test_on_nat_invalido(df_temporal: pd.DataFrame) -> None:
    # Valor viola intencionalmente o Literal OnNat.
    with pytest.raises(ValueError):
        split_temporal_3way(df_temporal, "data", on_nat="ignorar")  # type: ignore[arg-type]


def test_dataset_pequeno() -> None:
    df = pd.DataFrame({"data": pd.date_range("2020-01-01", periods=2)})
    with pytest.raises(ValueError):
        split_temporal_3way(df, "data")


# ---------------------------------------------------------------------------
# TemporalSplit — trava do holdout
# ---------------------------------------------------------------------------

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


def test_holdout_bloqueado_sem_gate(
    df_temporal: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Com ``G9_holdout`` pendente, ``concluir_selecao()`` levanta ``RuntimeError``."""
    monkeypatch.setattr(C, "cfg", lambda *a, **kw: {"status": "pendente"})

    split = TemporalSplit(df_temporal, "data")
    with pytest.raises(RuntimeError):
        split.concluir_selecao()


def test_treino_validacao_nao_expoe_holdout(df_temporal: pd.DataFrame) -> None:
    split = TemporalSplit(df_temporal, "data")
    treino, validacao = split.treino_validacao()

    assert treino is split.treino
    assert validacao is split.validacao


def test_resumo_marca_holdout_bloqueado(df_temporal: pd.DataFrame) -> None:
    resumo = TemporalSplit(df_temporal, "data").resumo()

    assert "treino" in resumo
    assert "validacao" in resumo
    assert "holdout" in resumo
    assert "bloqueado" in resumo