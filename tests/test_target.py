"""Contrato do alvo binário: `evolucao` → {0, 1, NaN}."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.models.pipeline import criar_alvo_binario, filtrar_rotulos_validos


def _df(valores: list) -> pd.DataFrame:
    return pd.DataFrame({"evolucao": valores, "feat": range(len(valores))})


def test_positivo_e_um() -> None:
    y = criar_alvo_binario(_df([2.0, 2.0]))
    assert y.tolist() == [1.0, 1.0]


def test_negativo_e_zero() -> None:
    y = criar_alvo_binario(_df([1.0, 1.0]))
    assert y.tolist() == [0.0, 0.0]


def test_codigos_3_e_9_viram_nan() -> None:
    y = criar_alvo_binario(_df([3.0, 9.0]))
    assert y.isna().all()


def test_nan_de_entrada_permanece_nan() -> None:
    y = criar_alvo_binario(_df([np.nan, 1.0, 2.0]))
    assert pd.isna(y.iloc[0])
    assert y.iloc[1] == 0.0
    assert y.iloc[2] == 1.0


def test_mistura_completa() -> None:
    y = criar_alvo_binario(_df([1.0, 2.0, 3.0, 9.0, np.nan]))
    assert y.iloc[0] == 0.0
    assert y.iloc[1] == 1.0
    assert y.iloc[2:].isna().all()


def test_filtrar_remove_nan() -> None:
    df = _df([1.0, 2.0, 3.0, 9.0, np.nan])
    X = df[["feat"]]
    y = criar_alvo_binario(df)
    X_ok, y_ok = filtrar_rotulos_validos(X, y)

    assert len(y_ok) == 2
    assert y_ok.dtype == np.int8
    assert y_ok.tolist() == [0, 1]
    assert list(X_ok["feat"]) == [0, 1]


def test_filtrar_exige_indice_alinhado() -> None:
    X = pd.DataFrame({"feat": [1, 2]}, index=[0, 1])
    y = pd.Series([0, 1], index=[1, 2])
    with pytest.raises(ValueError, match="mesmo índice"):
        filtrar_rotulos_validos(X, y)


def test_positivos_e_negativos_nao_se_sobrepoem() -> None:
    with pytest.raises(ValueError, match="sobrepor"):
        criar_alvo_binario(_df([1.0, 2.0]), positivos=[1.0, 2.0], negativos=[1.0])


def test_positivos_vazio_levanta() -> None:
    with pytest.raises(ValueError, match="positivos"):
        criar_alvo_binario(_df([1.0, 2.0]), positivos=[], negativos=[1.0])


def test_negativos_vazio_levanta() -> None:
    with pytest.raises(ValueError, match="negativos"):
        criar_alvo_binario(_df([1.0, 2.0]), positivos=[2.0], negativos=[])


def test_default_vem_do_yaml() -> None:
    """Sem argumentos, usa `target.positivos` e `target.negativos` do YAML."""
    from src.utils import config as C

    pos = C.cfg("target", "positivos")
    neg = C.cfg("target", "negativos")
    assert pos, "target.positivos precisa estar definido no YAML"
    assert neg, "target.negativos precisa estar definido no YAML"

    df = _df([float(pos[0]), float(neg[0])])
    y = criar_alvo_binario(df)
    assert y.tolist() == [1.0, 0.0]