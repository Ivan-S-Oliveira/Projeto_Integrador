from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils import config as C

__all__ = [
    "COLUNAS_DERIVADAS",
    "idade_em_anos",
    "intervalo_sintomas_internacao",
    "sazonalidade",
    "faixa_etaria",
    "sexo_categoria",
    "ano_mes_internacao",
    "montar_features",
]

_INTERVALO_MAX_DIAS_PADRAO: float = 60.0
_SEMANAS_POR_ANO: float = 52.18

_FAIXAS_PADRAO: tuple[tuple[str, float, float | None], ...] = (
    ("<1",    0.0,   1.0),
    ("1-4",   1.0,   5.0),
    ("5-11",  5.0,  12.0),
    ("12-17", 12.0, 18.0),
    ("18-39", 18.0, 40.0),
    ("40-59", 40.0, 60.0),
    ("60-79", 60.0, 80.0),
    ("80+",   80.0, None),
)

COLUNAS_DERIVADAS: tuple[str, ...] = (
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sin_semana",
    "cos_semana",
    "ano_internacao",
    "mes_internacao",
    "flag_intervalo_invalido",
    "flag_internacao_antes_sintomas",
    "faixa_etaria",
    "sexo_categoria",
)


def _intervalo_max_dias() -> float:
    valor = C.cfg("features", "engenharia", "intervalo_max_dias")
    return _INTERVALO_MAX_DIAS_PADRAO if valor is None else float(valor)


def _intervalo_politica() -> str:
    valor = C.cfg("features", "engenharia", "intervalo_politica")
    if valor is None:
        return "sinalizar"

    politica = str(valor).strip().lower()
    if politica not in ("sinalizar", "descartar"):
        raise ValueError(
            f"features.engenharia.intervalo_politica inválida: {valor!r}. "
            "Use 'sinalizar' ou 'descartar'."
        )
    return politica


def _faixas_etarias() -> list[tuple[str, float, float | None]]:
    bruto = C.cfg("features", "engenharia", "faixas_etarias")
    if not bruto:
        return list(_FAIXAS_PADRAO)

    return [
        (
            str(item["nome"]),
            float(item["min"]),
            None if item.get("max") is None else float(item["max"]),
        )
        for item in bruto
    ]


def idade_em_anos(df: pd.DataFrame) -> pd.Series:
    """
    Converte nu_idade_n + tp_idade (SIVEP) em idade em anos.

    tp_idade: 1=dias, 2=meses, 3=anos. Retorna float64 com NaN quando
    a codificação é desconhecida, a idade é negativa ou excede 120.
    """
    idade = pd.to_numeric(df["nu_idade_n"], errors="coerce")
    tipo = pd.to_numeric(df["tp_idade"], errors="coerce")

    valor = pd.Series(np.nan, index=df.index, dtype="float64")

    mask_d = tipo == 1
    mask_m = tipo == 2
    mask_a = tipo == 3

    valor[mask_d] = (idade[mask_d] / 365.25).to_numpy()
    valor[mask_m] = (idade[mask_m] / 12.0).to_numpy()
    valor[mask_a] = idade[mask_a].to_numpy()

    invalido = idade.isna() | (idade < 0) | ~tipo.isin([1, 2, 3])
    valor = valor.where(~invalido, np.nan)
    valor = valor.where(valor <= 120.0, np.nan)

    return valor


def intervalo_sintomas_internacao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deriva dias entre dt_sin_pri e dt_interna, com flags de invalidade.

    Colunas: dias_sintomas_ate_internacao (float64), flag_intervalo_invalido
    (int8), flag_internacao_antes_sintomas (int8). A política de valores
    fora de [0, intervalo_max_dias] vem de features.engenharia.intervalo_politica.
    """
    max_dias = _intervalo_max_dias()
    politica = _intervalo_politica()

    dt_sin = pd.to_datetime(df["dt_sin_pri"], errors="coerce")
    dt_int = pd.to_datetime(df["dt_interna"], errors="coerce")

    delta = pd.to_numeric(
        (dt_int - dt_sin).dt.days, errors="coerce"
    ).astype("float64")

    delta_arr = delta.to_numpy(dtype="float64", na_value=np.nan)
    data_ausente = pd.isna(delta_arr)
    negativo = (~data_ausente) & (delta_arr < 0)
    acima_limite = (~data_ausente) & (delta_arr > float(max_dias))

    invalido = data_ausente | negativo | acima_limite

    if politica == "descartar":
        delta_final = delta.where(~invalido, np.nan).astype("float64")
    else:
        delta_final = delta

    return pd.DataFrame(
        {
            "dias_sintomas_ate_internacao":   delta_final,
            "flag_intervalo_invalido":        invalido.astype("int8"),
            "flag_internacao_antes_sintomas": negativo.astype("int8"),
        }
    )


def sazonalidade(
    df: pd.DataFrame,
    coluna_data: str | None = None,
) -> pd.DataFrame:
    """
    Codifica a semana ISO como par (seno, cosseno) em 2π × (semana − 1)/52,18.

    Coluna default: dt_sin_pri (ou features.engenharia.coluna_sazonalidade).
    Datas nulas resultam em NaN.
    """
    if coluna_data is None:
        coluna_data = C.cfg("features", "engenharia", "coluna_sazonalidade")
    if coluna_data is None:
        coluna_data = "dt_sin_pri"
    if coluna_data not in df.columns:
        raise KeyError(f"Coluna temporal ausente: {coluna_data!r}")

    datas = pd.to_datetime(df[coluna_data], errors="coerce")

    semana = pd.Series(np.nan, index=df.index, dtype="float64")
    mask = datas.notna()
    if mask.any():
        iso = datas[mask].dt.isocalendar()
        semana.loc[mask] = iso["week"].astype("float64").to_numpy()

    angulo = 2.0 * np.pi * (semana - 1.0) / _SEMANAS_POR_ANO

    return pd.DataFrame(
        {
            "sin_semana": np.sin(angulo),
            "cos_semana": np.cos(angulo),
        }
    )


def faixa_etaria(idade_anos: pd.Series) -> pd.Series:
    """
    Categoriza idade em faixas semiabertas [min, max) do YAML.

    Idade nula vira a categoria explícita "desconhecida".
    """
    faixas = _faixas_etarias()
    idade = pd.to_numeric(idade_anos, errors="coerce")

    out = pd.Series("desconhecida", index=idade.index, dtype="object")

    for nome, lo, hi in faixas:
        if hi is None:
            mask = idade.notna() & (idade >= lo)
        else:
            mask = idade.notna() & (idade >= lo) & (idade < hi)
        out[mask] = nome

    return out.astype("category")


def sexo_categoria(df: pd.DataFrame) -> pd.Series:
    """
    Normaliza cs_sexo em categórica explícita.

    M → masculino; F → feminino; I → ignorado; demais/nulo → ausente.
    """
    sexo = df["cs_sexo"].astype("string").str.strip().str.upper()

    out = pd.Series("ausente", index=df.index, dtype="object")
    out[sexo == "M"] = "masculino"
    out[sexo == "F"] = "feminino"
    out[sexo == "I"] = "ignorado"

    return out.astype("category")


def ano_mes_internacao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai ano_internacao e mes_internacao de dt_interna como float64.

    Datas nulas resultam em NaN, mantendo compatibilidade com
    SimpleImputer e StandardScaler.
    """
    dt = pd.to_datetime(df["dt_interna"], errors="coerce")

    return pd.DataFrame(
        {
            "ano_internacao": dt.dt.year.astype("float64"),
            "mes_internacao": dt.dt.month.astype("float64"),
        }
    )


def montar_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica todas as derivações e devolve cópia de df com as colunas de
    COLUNAS_DERIVADAS adicionadas. Não muta a entrada.
    """
    out = df.copy()

    out["idade_anos"] = idade_em_anos(df)

    intervalo = intervalo_sintomas_internacao(df)
    out["dias_sintomas_ate_internacao"]   = intervalo["dias_sintomas_ate_internacao"]
    out["flag_intervalo_invalido"]        = intervalo["flag_intervalo_invalido"]
    out["flag_internacao_antes_sintomas"] = intervalo["flag_internacao_antes_sintomas"]

    saz = sazonalidade(df)
    out["sin_semana"] = saz["sin_semana"]
    out["cos_semana"] = saz["cos_semana"]

    out["faixa_etaria"]   = faixa_etaria(out["idade_anos"])
    out["sexo_categoria"] = sexo_categoria(df)

    ano_mes = ano_mes_internacao(df)
    out["ano_internacao"] = ano_mes["ano_internacao"]
    out["mes_internacao"] = ano_mes["mes_internacao"]

    return out