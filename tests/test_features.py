"""Testes de engenharia de atributos (src/features/engineering.py)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.features.engineering import (
    faixa_etaria,
    idade_em_anos,
    intervalo_sintomas_internacao,
    montar_features,
    sazonalidade,
)
from src.utils import config as C


# ---------------------------------------------------------------------------
# idade_em_anos
# ---------------------------------------------------------------------------

def test_idade_dias():
    df = pd.DataFrame({"nu_idade_n": [365.25, 730.5], "tp_idade": [1, 1]})
    y = idade_em_anos(df)
    assert y.tolist() == pytest.approx([1.0, 2.0])


def test_idade_meses():
    df = pd.DataFrame({"nu_idade_n": [12, 24], "tp_idade": [2, 2]})
    y = idade_em_anos(df)
    assert y.tolist() == pytest.approx([1.0, 2.0])


def test_idade_anos():
    df = pd.DataFrame({"nu_idade_n": [45, 80], "tp_idade": [3, 3]})
    y = idade_em_anos(df)
    assert y.tolist() == [45.0, 80.0]


def test_tipo_invalido_vira_nan():
    df = pd.DataFrame({"nu_idade_n": [10, 10, 10], "tp_idade": [0, 9, 99]})
    y = idade_em_anos(df)
    assert y.isna().all()


def test_idade_negativa_vira_nan():
    df = pd.DataFrame({"nu_idade_n": [-1, 10], "tp_idade": [3, 3]})
    y = idade_em_anos(df)
    assert pd.isna(y.iloc[0])
    assert y.iloc[1] == 10.0


def test_idade_absurda_vira_nan():
    df = pd.DataFrame({"nu_idade_n": [200, 500], "tp_idade": [3, 3]})
    y = idade_em_anos(df)
    assert y.isna().all()


def test_idade_nula_vira_nan():
    df = pd.DataFrame({"nu_idade_n": [np.nan, 10], "tp_idade": [3, 3]})
    y = idade_em_anos(df)
    assert pd.isna(y.iloc[0])
    assert y.iloc[1] == 10.0


def test_idade_string_numerica():
    df = pd.DataFrame({"nu_idade_n": ["45", "abc"], "tp_idade": ["3", "3"]})
    y = idade_em_anos(df)
    assert y.iloc[0] == 45.0
    assert pd.isna(y.iloc[1])


# ---------------------------------------------------------------------------
# intervalo_sintomas_internacao
# ---------------------------------------------------------------------------

def test_intervalo_normal():
    df = pd.DataFrame({
        "dt_sin_pri": ["2024-01-01", "2024-02-01"],
        "dt_interna": ["2024-01-06", "2024-02-11"],
    })
    r = intervalo_sintomas_internacao(df)
    assert r["intervalo_sint_interna_dias"].tolist() == [5.0, 10.0]
    assert (r["flag_intervalo_invalido"] == 0).all()


def test_intervalo_negativo():
    df = pd.DataFrame({
        "dt_sin_pri": ["2024-01-10"],
        "dt_interna": ["2024-01-01"],
    })
    r = intervalo_sintomas_internacao(df)
    assert pd.isna(r["intervalo_sint_interna_dias"].iloc[0])
    assert r["flag_intervalo_invalido"].iloc[0] == 1


def test_intervalo_nulo():
    df = pd.DataFrame({
        "dt_sin_pri": [pd.NaT],
        "dt_interna": ["2024-01-01"],
    })
    r = intervalo_sintomas_internacao(df)
    assert pd.isna(r["intervalo_sint_interna_dias"].iloc[0])
    assert r["flag_intervalo_invalido"].iloc[0] == 1


def test_intervalo_acima_do_limite():
    max_dias = int(C.cfg("features", "engenharia", "intervalo_max_dias") or 60)
    dt_int = pd.Timestamp("2024-01-01") + pd.Timedelta(days=max_dias + 1)
    df = pd.DataFrame({
        "dt_sin_pri": [pd.Timestamp("2024-01-01")],
        "dt_interna": [dt_int],
    })
    r = intervalo_sintomas_internacao(df)
    assert pd.isna(r["intervalo_sint_interna_dias"].iloc[0])
    assert r["flag_intervalo_invalido"].iloc[0] == 1


def test_intervalo_limite_exato_valido():
    max_dias = int(C.cfg("features", "engenharia", "intervalo_max_dias") or 60)
    dt_int = pd.Timestamp("2024-01-01") + pd.Timedelta(days=max_dias)
    df = pd.DataFrame({
        "dt_sin_pri": [pd.Timestamp("2024-01-01")],
        "dt_interna": [dt_int],
    })
    r = intervalo_sintomas_internacao(df)
    assert r["intervalo_sint_interna_dias"].iloc[0] == float(max_dias)
    assert r["flag_intervalo_invalido"].iloc[0] == 0


# ---------------------------------------------------------------------------
# sazonalidade
# ---------------------------------------------------------------------------

def test_sazonalidade_range():
    df = pd.DataFrame({
        "dt_notific": pd.date_range("2024-01-01", periods=52, freq="7D"),
    })
    r = sazonalidade(df, coluna_data="dt_notific")
    assert r["sin_semana"].between(-1, 1).all()
    assert r["cos_semana"].between(-1, 1).all()


def test_sazonalidade_semana_1_e_53_proximas():
    # 2024-01-01 → ISO W01/2024; 2024-12-29 → ISO W52/2024.
    # Ambos caem no início do ciclo anual, devem estar próximos no círculo.
    df = pd.DataFrame({"dt_notific": ["2024-01-01", "2024-12-29"]})
    r = sazonalidade(df, coluna_data="dt_notific")
    d = float(np.hypot(
        r["sin_semana"].iloc[0] - r["sin_semana"].iloc[1],
        r["cos_semana"].iloc[0] - r["cos_semana"].iloc[1],
    ))
    assert d < 0.5


def test_sazonalidade_nulo():
    df = pd.DataFrame({"dt_notific": [pd.NaT, "2024-06-15"]})
    r = sazonalidade(df, coluna_data="dt_notific")
    assert pd.isna(r["sin_semana"].iloc[0])
    assert pd.isna(r["cos_semana"].iloc[0])


# ---------------------------------------------------------------------------
# faixa_etaria
# ---------------------------------------------------------------------------

def test_faixa_etaria_limites():
    s = pd.Series([
        0.0, 0.99, 1.0, 4.99, 5.0, 11.99,
        12.0, 17.99, 18.0, 39.99,
        40.0, 59.99, 60.0, 79.99,
        80.0, 120.0,
    ])
    r = faixa_etaria(s).astype(str).tolist()
    esperado = [
        "<1", "<1", "1-4", "1-4", "5-11", "5-11",
        "12-17", "12-17", "18-39", "18-39",
        "40-59", "40-59", "60-79", "60-79",
        "80+", "80+",
    ]
    assert r == esperado


def test_faixa_etaria_nulo():
    s = pd.Series([np.nan, 10.0])
    r = faixa_etaria(s)
    assert str(r.iloc[0]) == "desconhecida"
    assert str(r.iloc[1]) == "5-11"


# ---------------------------------------------------------------------------
# montar_features — pureza e integração com build_pipeline
# ---------------------------------------------------------------------------

def _df_base() -> pd.DataFrame:
    return pd.DataFrame({
        "nu_idade_n": [30.0, 60.0, 400.0],
        "tp_idade":   [3.0, 3.0, 1.0],
        "dt_sin_pri": ["2024-01-01", "2024-02-01", pd.NaT],
        "dt_interna": ["2024-01-05", "2024-02-11", "2024-03-01"],
        "dt_notific": ["2024-01-02", "2024-02-02", "2024-03-02"],
        "sg_uf":      ["SP", "RJ", "MG"],
        "cs_sexo":    ["M", "F", "M"],
        "cs_gestant": [pd.NA, "1", pd.NA],
        "febre":      ["1", "1", "0"],
        "tosse":      ["1", "0", "1"],
        "dispneia":   ["1", "1", "0"],
        "saturacao":  ["1", "0", "1"],
        "vacina_cov": ["1", "0", "1"],
    })


def test_montar_features_colunas():
    df = _df_base()
    out = montar_features(df)
    for c in (
        "idade_anos",
        "intervalo_sint_interna_dias",
        "flag_intervalo_invalido",
        "sin_semana",
        "cos_semana",
        "faixa_etaria",
    ):
        assert c in out.columns


def test_montar_features_nao_altera_original():
    df = _df_base()
    original = df.copy(deep=True)
    _ = montar_features(df)
    pd.testing.assert_frame_equal(df, original)


def test_montar_features_alimenta_build_pipeline():
    from src.models.pipeline import FEATURES, build_pipeline

    df = _df_base()
    out = montar_features(df)
    pipe = build_pipeline(X=out[FEATURES], strict=True)
    assert pipe is not None


# ---------------------------------------------------------------------------
# Sem colisão com features.proibidas
# ---------------------------------------------------------------------------

def test_derivadas_sem_colisao_com_proibidas():
    proibidas = set(C.cfg("features", "proibidas") or [])
    derivadas = {
        "idade_anos",
        "intervalo_sint_interna_dias",
        "flag_intervalo_invalido",
        "sin_semana",
        "cos_semana",
        "faixa_etaria",
    }
    assert not (derivadas & proibidas)