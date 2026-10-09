"""Engenharia de atributos do pipeline supervisionado.

Funções puras que derivam colunas a partir do DataFrame analítico.
Nenhuma função muta a entrada — todas devolvem cópia ou Series novas.

Decisões configuráveis (limite de intervalo, faixas etárias, inventário
das colunas derivadas) vêm de `configs/supervised.yaml`, bloco
`features.engenharia`.

Uso típico:
    from src.features import montar_features

    df_feat = montar_features(df)
    X = df_feat[FEATURES]
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils import config as C

__all__ = [
    "idade_em_anos",
    "intervalo_sintomas_internacao",
    "sazonalidade",
    "faixa_etaria",
    "montar_features",
]


# ---------------------------------------------------------------------------
# Constantes de fallback (espelho do que o YAML sugere)
# ---------------------------------------------------------------------------

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


def _intervalo_max_dias() -> float:
    """Limite (dias) para o intervalo sintomas→internação."""
    valor = C.cfg("features", "engenharia", "intervalo_max_dias")
    return _INTERVALO_MAX_DIAS_PADRAO if valor is None else float(valor)


def _faixas_etarias() -> list[tuple[str, float, float | None]]:
    """Faixas etárias configuradas em `features.engenharia.faixas_etarias`."""
    bruto = C.cfg("features", "engenharia", "faixas_etarias")
    if not bruto:
        return list(_FAIXAS_PADRAO)

    faixas: list[tuple[str, float, float | None]] = []
    for item in bruto:
        nome = str(item["nome"])
        lo = float(item["min"])
        hi_raw = item.get("max")
        hi = None if hi_raw is None else float(hi_raw)
        faixas.append((nome, lo, hi))
    return faixas


# ---------------------------------------------------------------------------
# 1) idade_em_anos
# ---------------------------------------------------------------------------

def idade_em_anos(df: pd.DataFrame) -> pd.Series:
    """
    Converte `nu_idade_n` + `tp_idade` (codificação SIVEP) em idade em anos.

    Codificação SIVEP:
        1 → dias    (dividido por 365,25)
        2 → meses   (dividido por 12)
        3 → anos    (inalterado)

    Retorna `pd.Series` float64. Vira `NaN` quando:
      - `tp_idade` está fora de {1, 2, 3};
      - `nu_idade_n` é nulo ou negativo;
      - a idade convertida ultrapassa 120 anos.

    Não imputa e não muta o DataFrame de entrada.

    Parâmetros
    ----------
    df : pd.DataFrame
        Precisa conter as colunas `nu_idade_n` e `tp_idade`. Valores
        textuais são aceitos (conversão via `pd.to_numeric`).

    Retorno
    -------
    pd.Series dtype float64, indexado como `df`.
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

    invalido = (
        idade.isna()
        | (idade < 0)
        | ~tipo.isin([1, 2, 3])
    )
    valor = valor.where(~invalido, np.nan)
    valor = valor.where(valor <= 120.0, np.nan)

    return valor


# ---------------------------------------------------------------------------
# 2) intervalo_sintomas_internacao
# ---------------------------------------------------------------------------

def intervalo_sintomas_internacao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Intervalo em dias entre início dos sintomas (`dt_sin_pri`) e
    internação (`dt_interna`), mais uma flag de invalidade.

    Regras
    ------
    - `intervalo_sint_interna_dias` = `(dt_interna - dt_sin_pri).days`.
    - `flag_intervalo_invalido` (int8) = 1 quando:
        * qualquer das datas é nula/não parseável, ou
        * o intervalo é negativo, ou
        * o intervalo ultrapassa
          `features.engenharia.intervalo_max_dias`.
      Caso contrário, 0.
    - Quando inválido, o intervalo vira `NaN`.

    ATENÇÃO metodológica
    --------------------
    `dt_interna` precisa ser reconhecida pelo gate G1 como disponível
    no momento da admissão. A função existe independentemente dessa
    decisão; o que depende de G1 é a inclusão das colunas derivadas em
    `features.numericas`.

    Não muta o DataFrame de entrada.

    Parâmetros
    ----------
    df : pd.DataFrame
        Precisa conter `dt_sin_pri` e `dt_interna`.

    Retorno
    -------
    pd.DataFrame com colunas:
        - `intervalo_sint_interna_dias` (float64)
        - `flag_intervalo_invalido` (int8)
    """
    max_dias = _intervalo_max_dias()

    dt_sin = pd.to_datetime(df["dt_sin_pri"], errors="coerce")
    dt_int = pd.to_datetime(df["dt_interna"], errors="coerce")

    delta = pd.to_numeric((dt_int - dt_sin).dt.days, errors="coerce").astype("float64")
    delta_arr = delta.to_numpy(dtype="float64", na_value=np.nan)

    invalido = (
        pd.isna(delta_arr)
        | (delta_arr < 0)
        | (delta_arr > float(max_dias))
    )
    invalido = pd.Series(invalido, index=df.index, dtype="bool")
    delta_limpo = delta.where(~invalido, np.nan).astype("float64")

    return pd.DataFrame(
        {
            "intervalo_sint_interna_dias": delta_limpo,
            "flag_intervalo_invalido": invalido.astype("int8"),
        }
    )


# ---------------------------------------------------------------------------
# 3) sazonalidade
# ---------------------------------------------------------------------------

def sazonalidade(
    df: pd.DataFrame,
    coluna_data: str | None = None,
) -> pd.DataFrame:
    """
    Codifica a semana ISO do ano como par (seno, cosseno).

    A codificação é `2π × (semana − 1) / 52,18`, o que mantém a
    continuidade entre as semanas 52/53 e a semana 1 do ano seguinte.

    Parâmetros
    ----------
    df : pd.DataFrame
    coluna_data : str | None
        Coluna de data a usar. Se None, usa `coluna_tempo` do
        `supervised.yaml`.

    Retorno
    -------
    pd.DataFrame com colunas `sin_semana` e `cos_semana` (float64).
    Datas nulas ou não parseáveis resultam em `NaN`.

    Não muta o DataFrame de entrada.
    """
    if coluna_data is None:
        coluna_data = C.cfg("coluna_tempo")
    if not coluna_data:
        raise ValueError(
            "`coluna_data` não informado e `coluna_tempo` ausente no "
            "supervised.yaml."
        )
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


# ---------------------------------------------------------------------------
# 4) faixa_etaria
# ---------------------------------------------------------------------------

def faixa_etaria(idade_anos: pd.Series) -> pd.Series:
    """
    Categoriza idade em anos em faixas configuradas no YAML.

    As faixas vêm de `features.engenharia.faixas_etarias`, cada uma no
    formato `{nome, min, max}`, interpretado como intervalo semiaberto
    `[min, max)`. `max: null` significa "sem limite superior".

    Idade nula vira a categoria explícita `"desconhecida"`.

    Parâmetros
    ----------
    idade_anos : pd.Series
        Idade em anos. Aceita qualquer tipo numérico ou numérico em
        string (conversão via `pd.to_numeric(errors="coerce")`).

    Retorno
    -------
    pd.Series dtype `category` com nomes das faixas ou `"desconhecida"`.
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


# ---------------------------------------------------------------------------
# 5) montar_features
# ---------------------------------------------------------------------------

def montar_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica todas as funções acima e devolve uma cópia de `df` com as
    colunas derivadas adicionadas.

    Colunas adicionadas:
        - idade_anos
        - intervalo_sint_interna_dias
        - flag_intervalo_invalido
        - sin_semana
        - cos_semana
        - faixa_etaria

    O DataFrame de entrada NÃO é modificado.

    Parâmetros
    ----------
    df : pd.DataFrame
        Precisa conter `nu_idade_n`, `tp_idade`, `dt_sin_pri`,
        `dt_interna` e a coluna de tempo configurada (`coluna_tempo`).

    Retorno
    -------
    pd.DataFrame
        Cópia de `df` com as colunas derivadas.
    """
    out = df.copy()

    out["idade_anos"] = idade_em_anos(df)

    intervalo = intervalo_sintomas_internacao(df)
    out["intervalo_sint_interna_dias"] = intervalo["intervalo_sint_interna_dias"]
    out["flag_intervalo_invalido"] = intervalo["flag_intervalo_invalido"]

    saz = sazonalidade(df)
    out["sin_semana"] = saz["sin_semana"]
    out["cos_semana"] = saz["cos_semana"]

    out["faixa_etaria"] = faixa_etaria(out["idade_anos"])

    return out