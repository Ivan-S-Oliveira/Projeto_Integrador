"""
Testes de engenharia de atributos — src/features/engineering.py.

Cobre as funções puras e o orquestrador `montar_features`. Foco em:
- contrato de cada coluna derivada (nome, tipo, semântica);
- casos inválidos e ausentes;
- não-mutação da entrada;
- invariante de ponto-no-tempo: nada posterior à admissão entra em X;
- ponto único de verdade: `montar_features` é a única porta de saída.

Não testa parsing do YAML — isso é responsabilidade de src/utils/config.py.
Assumimos que C.cfg lê a configuração ativa corretamente.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.features.engineering import (
    ano_mes_internacao,
    faixa_etaria,
    idade_em_anos,
    intervalo_sintomas_internacao,
    montar_features,
    sazonalidade,
    sexo_categoria,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ENTRADAS_OBRIGATORIAS = [
    "nu_idade_n",
    "tp_idade",
    "cs_sexo",
    "dt_sin_pri",
    "dt_interna",
]


@pytest.fixture
def df_base() -> pd.DataFrame:
    """
    DataFrame mínimo com as colunas de entrada exigidas por `montar_features`.

    Linhas:
    - 0: adulto (30a), 4 dias até internação, M
    - 1: bebê (6 meses), 5 dias, F
    - 2: adulto (40a), 5 dias, sexo ignorado
    - 3: recém-nascido (1 dia), 5 dias, M
    """
    return pd.DataFrame(
        {
            "nu_idade_n": [30, 6, 40, 1],
            "tp_idade":   [3, 2, 3, 1],
            "cs_sexo":    ["M", "F", "I", "M"],
            "dt_sin_pri": ["2024-01-01", "2024-03-15", "2024-06-20", "2024-09-05"],
            "dt_interna": ["2024-01-05", "2024-03-20", "2024-06-25", "2024-09-10"],
        }
    )


# ---------------------------------------------------------------------------
# idade_em_anos
# ---------------------------------------------------------------------------

class TestIdadeEmAnos:
    def test_anos_direto(self, df_base):
        assert idade_em_anos(df_base).iloc[0] == pytest.approx(30.0)

    def test_meses_convertidos(self, df_base):
        assert idade_em_anos(df_base).iloc[1] == pytest.approx(0.5)

    def test_dias_convertidos(self, df_base):
        assert idade_em_anos(df_base).iloc[3] == pytest.approx(1 / 365.25)

    def test_retorna_float64(self, df_base):
        assert idade_em_anos(df_base).dtype == np.float64

    def test_tipo_invalido_vira_nan(self):
        df = pd.DataFrame({"nu_idade_n": [10], "tp_idade": [9]})
        assert pd.isna(idade_em_anos(df)).all()

    def test_idade_negativa_vira_nan(self):
        df = pd.DataFrame({"nu_idade_n": [-1], "tp_idade": [3]})
        assert pd.isna(idade_em_anos(df)).all()

    def test_idade_acima_de_120_vira_nan(self):
        df = pd.DataFrame({"nu_idade_n": [200], "tp_idade": [3]})
        assert pd.isna(idade_em_anos(df)).all()

    def test_nao_muta_entrada(self, df_base):
        antes = df_base.copy(deep=True)
        idade_em_anos(df_base)
        pd.testing.assert_frame_equal(df_base, antes)


# ---------------------------------------------------------------------------
# intervalo_sintomas_internacao
# ---------------------------------------------------------------------------

class TestIntervaloSintomasInternacao:
    def test_intervalo_positivo(self, df_base):
        out = intervalo_sintomas_internacao(df_base)
        assert out["dias_sintomas_ate_internacao"].iloc[0] == pytest.approx(4.0)

    def test_tipos_das_colunas(self, df_base):
        out = intervalo_sintomas_internacao(df_base)
        assert out["dias_sintomas_ate_internacao"].dtype == np.float64
        assert out["flag_intervalo_invalido"].dtype == np.int8
        assert out["flag_internacao_antes_sintomas"].dtype == np.int8

    def test_negativo_seta_ambas_flags(self):
        df = pd.DataFrame(
            {"dt_sin_pri": ["2024-01-10"], "dt_interna": ["2024-01-05"]}
        )
        out = intervalo_sintomas_internacao(df)
        assert out["flag_internacao_antes_sintomas"].iloc[0] == 1
        assert out["flag_intervalo_invalido"].iloc[0] == 1

    def test_acima_do_limite_seta_flag_umbrella_sem_marcar_sinal(self):
        df = pd.DataFrame(
            {"dt_sin_pri": ["2024-01-01"], "dt_interna": ["2024-06-01"]}
        )
        out = intervalo_sintomas_internacao(df)
        assert out["flag_intervalo_invalido"].iloc[0] == 1
        assert out["flag_internacao_antes_sintomas"].iloc[0] == 0

    def test_data_ausente_seta_flag_umbrella(self):
        df = pd.DataFrame(
            {"dt_sin_pri": [None], "dt_interna": ["2024-01-05"]}
        )
        out = intervalo_sintomas_internacao(df)
        assert pd.isna(out["dias_sintomas_ate_internacao"].iloc[0])
        assert out["flag_intervalo_invalido"].iloc[0] == 1

    def test_politica_sinalizar_mantem_valor_bruto(self, monkeypatch):
        """Default: valor inválido fica visível, comunicado por flags."""
        df = pd.DataFrame(
            {"dt_sin_pri": ["2024-01-10"], "dt_interna": ["2024-01-05"]}
        )
        monkeypatch.setattr(
            "src.features.engineering._intervalo_politica",
            lambda: "sinalizar",
        )
        out = intervalo_sintomas_internacao(df)
        assert out["dias_sintomas_ate_internacao"].iloc[0] == pytest.approx(-5.0)

    def test_politica_descartar_substitui_por_nan(self, monkeypatch):
        df = pd.DataFrame(
            {"dt_sin_pri": ["2024-01-10"], "dt_interna": ["2024-01-05"]}
        )
        monkeypatch.setattr(
            "src.features.engineering._intervalo_politica",
            lambda: "descartar",
        )
        out = intervalo_sintomas_internacao(df)
        assert pd.isna(out["dias_sintomas_ate_internacao"].iloc[0])
        assert out["flag_intervalo_invalido"].iloc[0] == 1


# ---------------------------------------------------------------------------
# sazonalidade
# ---------------------------------------------------------------------------

class TestSazonalidade:
    def test_gera_sin_e_cos_no_intervalo(self, df_base):
        out = sazonalidade(df_base)
        assert set(out.columns) == {"sin_semana", "cos_semana"}
        for col in out.columns:
            assert out[col].between(-1.0, 1.0, inclusive="both").all()

    def test_mesma_semana_em_anos_diferentes_proxima(self):
        df = pd.DataFrame(
            {"dt_sin_pri": ["2023-03-15", "2024-03-13"]}  # ~mesma semana ISO
        )
        out = sazonalidade(df)
        assert abs(out["sin_semana"].iloc[0] - out["sin_semana"].iloc[1]) < 0.1
        assert abs(out["cos_semana"].iloc[0] - out["cos_semana"].iloc[1]) < 0.1

    def test_data_nula_vira_nan(self):
        df = pd.DataFrame({"dt_sin_pri": [None]})
        out = sazonalidade(df)
        assert pd.isna(out["sin_semana"].iloc[0])
        assert pd.isna(out["cos_semana"].iloc[0])

    def test_coluna_ausente_levanta_keyerror(self):
        df = pd.DataFrame({"outra_data": ["2024-01-01"]})
        with pytest.raises(KeyError, match="Coluna temporal ausente"):
            sazonalidade(df, coluna_data="dt_sin_pri")


# ---------------------------------------------------------------------------
# faixa_etaria
# ---------------------------------------------------------------------------

class TestFaixaEtaria:
    def test_fronteiras_semiabertas(self):
        idades = pd.Series([0.0, 0.99, 1.0, 4.99, 5.0, 80.0, 120.0])
        out = faixa_etaria(idades)
        assert list(out) == ["<1", "<1", "1-4", "1-4", "5-11", "80+", "80+"]

    def test_idade_nula_vira_desconhecida(self):
        out = faixa_etaria(pd.Series([np.nan, 30.0]))
        assert out.iloc[0] == "desconhecida"
        assert out.iloc[1] == "18-39"

    def test_retorna_categoria(self):
        out = faixa_etaria(pd.Series([30.0]))
        assert isinstance(out.dtype, pd.CategoricalDtype)


# ---------------------------------------------------------------------------
# sexo_categoria
# ---------------------------------------------------------------------------

class TestSexoCategoria:
    @pytest.mark.parametrize(
        "entrada, esperado",
        [
            ("M", "masculino"),
            ("f", "feminino"),
            (" I ", "ignorado"),
            ("X", "ausente"),
            (None, "ausente"),
        ],
    )
    def test_mapeamento(self, entrada, esperado):
        df = pd.DataFrame({"cs_sexo": [entrada]})
        assert sexo_categoria(df).iloc[0] == esperado

    def test_retorna_categoria(self):
        df = pd.DataFrame({"cs_sexo": ["M"]})
        assert isinstance(sexo_categoria(df).dtype, pd.CategoricalDtype)


# ---------------------------------------------------------------------------
# ano_mes_internacao
# ---------------------------------------------------------------------------

class TestAnoMesInternacao:
    def test_extrai_ano_e_mes(self, df_base):
        out = ano_mes_internacao(df_base)
        assert out["ano_internacao"].tolist() == [2024.0] * 4
        assert out["mes_internacao"].tolist() == [1.0, 3.0, 6.0, 9.0]

    def test_data_nula_vira_nan(self):
        df = pd.DataFrame({"dt_interna": [None]})
        out = ano_mes_internacao(df)
        assert pd.isna(out["ano_internacao"].iloc[0])
        assert pd.isna(out["mes_internacao"].iloc[0])


# ---------------------------------------------------------------------------
# montar_features — orquestrador
# ---------------------------------------------------------------------------

COLUNAS_DERIVADAS_ESPERADAS = {
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
}


class TestMontarFeatures:
    def test_gera_todas_as_derivadas_do_yaml(self, df_base):
        """
        Este é o teste que o relatório estático não fez.
        Trava o contrato entre features.engenharia.derivadas e a função.
        """
        out = montar_features(df_base)
        faltando = COLUNAS_DERIVADAS_ESPERADAS - set(out.columns)
        assert not faltando, f"Derivadas ausentes: {sorted(faltando)}"

    def test_nao_muta_entrada(self, df_base):
        antes = df_base.copy(deep=True)
        montar_features(df_base)
        pd.testing.assert_frame_equal(df_base, antes)

    def test_preserva_colunas_originais(self, df_base):
        out = montar_features(df_base)
        for col in df_base.columns:
            assert col in out.columns

    def test_nao_gera_colunas_proibidas(self, df_base):
        proibidas = {"evolucao", "alvo_obito_srag", "dt_evoluca", "uti", "cluster"}
        out = montar_features(df_base)
        assert proibidas.isdisjoint(out.columns)


# ---------------------------------------------------------------------------
# Ponto-no-tempo
# ---------------------------------------------------------------------------

class TestPontoNoTempo:
    """
    Invariantes que protegem contra vazamento temporal.
    O ponto de previsão é a admissão hospitalar.
    """

    def test_so_precisa_das_entradas_declaradas(self, df_base):
        """
        Se `montar_features` só depende de features.engenharia.entradas,
        um df com exatamente essas colunas deve ser suficiente.
        Qualquer dependência extra quebra este teste.
        """
        df = df_base[ENTRADAS_OBRIGATORIAS].copy()
        out = montar_features(df)
        assert out is not None
        assert COLUNAS_DERIVADAS_ESPERADAS.issubset(out.columns)

    def test_colunas_pos_admissao_nao_influenciam(self, df_base):
        """
        Injetar colunas conhecidas só após a alta não pode alterar a saída.
        Se alterar, há vazamento temporal.
        """
        baseline = montar_features(df_base)

        df_contaminado = df_base.copy()
        df_contaminado["evolucao"] = [1.0, 2.0, 1.0, 2.0]
        df_contaminado["dt_evoluca"] = pd.to_datetime(
            ["2024-02-01", "2024-04-01", "2024-07-01", "2024-10-01"]
        )
        df_contaminado["uti"] = [0, 1, 0, 1]
        df_contaminado["suport_ven"] = [0, 1, 0, 0]

        contaminado = montar_features(df_contaminado)

        # Comparar apenas as derivadas — o contaminado tem colunas extras.
        pd.testing.assert_frame_equal(
            baseline[list(COLUNAS_DERIVADAS_ESPERADAS)].reset_index(drop=True),
            contaminado[list(COLUNAS_DERIVADAS_ESPERADAS)].reset_index(drop=True),
        )

    def test_ordem_das_linhas_nao_altera_derivadas(self, df_base):
        """Derivadas devem ser pointwise — sem dependência de ordem/agregação."""
        normal = montar_features(df_base)
        invertido = montar_features(df_base.iloc[::-1].reset_index(drop=True))

        pd.testing.assert_frame_equal(
            normal[list(COLUNAS_DERIVADAS_ESPERADAS)].reset_index(drop=True),
            invertido[list(COLUNAS_DERIVADAS_ESPERADAS)]
            .iloc[::-1]
            .reset_index(drop=True),
        )