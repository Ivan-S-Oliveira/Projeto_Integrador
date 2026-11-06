"""Engenharia de variáveis."""

from __future__ import annotations

import pandas as pd
import pytest
from src.features import faixa_etaria, idade_em_anos, intervalo_sintomas_internacao, montar_features, regiao_residencia, sexo_categoria


def test_regiao_residencia_trata_ausentes_e_invalidos() -> None:
    entrada = pd.Series(
        [None, pd.NA, "", "  ", "XX", "nan"],
        index=[10, 20, 30, 40, 50, 60],
    )
    resultado = regiao_residencia(entrada)
    assert resultado.index.equals(entrada.index)
    assert resultado.astype("string").tolist() == ["AUSENTE"] * 6


def test_regiao_residencia_cobre_as_27_ufs() -> None:
    ufs = pd.Series([
        "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
        "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
        "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
    ])
    resultado = regiao_residencia(ufs).astype("string")
    assert not resultado.eq("AUSENTE").any()
    assert set(resultado) == {
        "NORTE", "NORDESTE", "CENTRO-OESTE", "SUDESTE", "SUL",
    }


ENTRADAS_OBRIGATORIAS: tuple[str, ...] = (
    "nu_idade_n",
    "tp_idade",
    "cs_sexo",
    "dt_sin_pri",
    "dt_interna",
)


COLUNAS_DERIVADAS_ESPERADAS: frozenset[str] = frozenset({
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "flag_intervalo_invalido",
    "flag_internacao_antes_sintomas",
    "sin_semana",
    "cos_semana",
    "faixa_etaria",
    "sexo_categoria",
    "ano_internacao",
    "mes_internacao",
})


@pytest.fixture
def df_base() -> pd.DataFrame:
    """DataFrame mínimo com as colunas exigidas por ``montar_features``."""
    return pd.DataFrame({
        "nu_idade_n": [30, 6, 40, 1],
        "tp_idade":   [3, 2, 3, 1],
        "cs_sexo":    ["M", "F", "I", "M"],
        "dt_sin_pri": ["2024-01-01", "2024-03-15", "2024-06-20", "2024-09-05"],
        "dt_interna": ["2024-01-05", "2024-03-20", "2024-06-25", "2024-09-10"],
    })


class TestIdadeEmAnos:
    def test_anos_direto(self, df_base: pd.DataFrame) -> None:
        assert idade_em_anos(df_base).iloc[0] == pytest.approx(30.0)

    def test_meses_convertidos(self, df_base: pd.DataFrame) -> None:
        assert idade_em_anos(df_base).iloc[1] == pytest.approx(0.5)


    def test_idade_acima_de_120_vira_nan(self) -> None:
        df = pd.DataFrame({"nu_idade_n": [200], "tp_idade": [3]})
        assert pd.isna(idade_em_anos(df)).all()


class TestIntervaloSintomasInternacao:


    def test_negativo_seta_ambas_flags(self) -> None:
        df = pd.DataFrame({"dt_sin_pri": ["2024-01-10"], "dt_interna": ["2024-01-05"]})
        out = intervalo_sintomas_internacao(df)
        assert out["flag_internacao_antes_sintomas"].iloc[0] == 1
        assert out["flag_intervalo_invalido"].iloc[0] == 1


    def test_politica_descartar_substitui_por_nan(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        df = pd.DataFrame({"dt_sin_pri": ["2024-01-10"], "dt_interna": ["2024-01-05"]})
        monkeypatch.setattr(
            "src.features._intervalo_politica",
            lambda: "descartar",
        )
        out = intervalo_sintomas_internacao(df)
        assert pd.isna(out["dias_sintomas_ate_internacao"].iloc[0])
        assert out["flag_intervalo_invalido"].iloc[0] == 1


class TestFaixaEtaria:
    def test_fronteiras_semiabertas(self) -> None:
        out = faixa_etaria(pd.Series([0.0, 0.99, 1.0, 4.99, 5.0, 80.0, 120.0]))
        assert list(out) == ["<1", "<1", "1-4", "1-4", "5-11", "80+", "80+"]


class TestMontarFeatures:
    def test_gera_todas_as_derivadas_do_yaml(self, df_base: pd.DataFrame) -> None:
        """Trava o contrato entre ``features.engenharia.derivadas`` e a função."""
        faltando = COLUNAS_DERIVADAS_ESPERADAS - set(montar_features(df_base).columns)
        assert not faltando, f"Derivadas ausentes: {sorted(faltando)}"

    def test_nao_muta_entrada(self, df_base: pd.DataFrame) -> None:
        antes = df_base.copy(deep=True)
        montar_features(df_base)
        pd.testing.assert_frame_equal(df_base, antes)

    def test_preserva_colunas_originais(self, df_base: pd.DataFrame) -> None:
        out = montar_features(df_base)
        assert set(df_base.columns).issubset(out.columns)

    def test_nao_gera_colunas_proibidas(self, df_base: pd.DataFrame) -> None:
        proibidas = {"evolucao", "alvo_obito_srag", "dt_evoluca", "uti", "cluster"}
        assert proibidas.isdisjoint(montar_features(df_base).columns)


class TestPontoNoTempo:
    """Invariantes contra vazamento temporal — o ponto de previsão é a admissão."""


    def test_colunas_pos_admissao_nao_influenciam(self, df_base: pd.DataFrame) -> None:
        """Injetar colunas pós-alta não pode alterar a saída."""
        baseline = montar_features(df_base)

        df_contaminado = df_base.copy()
        df_contaminado["evolucao"]  = [1.0, 2.0, 1.0, 2.0]
        df_contaminado["dt_evoluca"] = pd.to_datetime(
            ["2024-02-01", "2024-04-01", "2024-07-01", "2024-10-01"]
        )
        df_contaminado["uti"]        = [0, 1, 0, 1]
        df_contaminado["suport_ven"] = [0, 1, 0, 0]

        contaminado = montar_features(df_contaminado)

        pd.testing.assert_frame_equal(
            baseline[list(COLUNAS_DERIVADAS_ESPERADAS)].reset_index(drop=True),
            contaminado[list(COLUNAS_DERIVADAS_ESPERADAS)].reset_index(drop=True),
        )
