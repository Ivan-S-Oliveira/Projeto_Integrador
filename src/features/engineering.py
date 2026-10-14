"""
Engenharia de atributos do pipeline supervisionado.

Funções puras que derivam colunas a partir do DataFrame analítico.
Nenhuma função muta a entrada — todas devolvem cópia ou Series novas.

Decisões configuráveis vêm de `configs/supervised.yaml`, bloco
`features.engenharia`.

Política de intervalos inválidos
--------------------------------
`decisoes.md` pede sinalizar, não corrigir em silêncio. O default é
manter `dias_sintomas_ate_internacao` bruto (NaN apenas quando alguma
data é `NaT`) e comunicar invalidade via flags explícitas:
`flag_intervalo_invalido` (umbrella) e `flag_internacao_antes_sintomas`.

`features.engenharia.intervalo_politica` aceita `"sinalizar"` (default)
ou `"descartar"` — este último substitui valores inválidos por `NaN`
mantendo as flags.

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


def _intervalo_max_dias() -> float:
    """Limite (dias) para o intervalo sintomas→internação."""
    valor = C.cfg("features", "engenharia", "intervalo_max_dias")
    return _INTERVALO_MAX_DIAS_PADRAO if valor is None else float(valor)


def _intervalo_politica() -> str:
    """
    Política para valores fora de `[0, intervalo_max_dias]`.

    `"sinalizar"` (default): mantém o valor bruto, apenas marca nas flags.
    `"descartar"`: substitui o valor por `NaN` quando inválido.
    """
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
    """Faixas etárias configuradas em `features.engenharia.faixas_etarias`."""
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
    Converte `nu_idade_n` + `tp_idade` (codificação SIVEP) em idade em anos.

    Codificação SIVEP: 1 → dias (÷ 365,25); 2 → meses (÷ 12); 3 → anos.

    Retorna `pd.Series` float64. Vira `NaN` quando `tp_idade` está fora
    de {1, 2, 3}, `nu_idade_n` é nulo/negativo, ou a idade ultrapassa
    120 anos. Não imputa e não muta a entrada.
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
    Intervalo em dias entre `dt_sin_pri` e `dt_interna`, com flags.

    Colunas geradas
    ---------------
    - `dias_sintomas_ate_internacao` (float64): `(dt_interna - dt_sin_pri).days`.
      `NaN` apenas quando alguma data é nula/não parseável. Negativos e
      valores acima do limite ficam visíveis; a invalidade é comunicada
      pelas flags. Comportamento controlado por
      `features.engenharia.intervalo_politica`: `"sinalizar"` (default)
      mantém o valor bruto; `"descartar"` substitui por `NaN`.
    - `flag_intervalo_invalido` (int8): 1 para data ausente, dias < 0,
      ou dias > `intervalo_max_dias`.
    - `flag_internacao_antes_sintomas` (int8): 1 quando dias < 0.

    `dt_interna` precisa ser reconhecida pelo gate G1 como disponível
    no momento da admissão; a decisão de incluir as colunas em
    `features.numericas` depende desse gate, não desta função.

    Não muta o DataFrame de entrada.
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
    Codifica a semana ISO do ano como par (seno, cosseno).

    A codificação é `2π × (semana − 1) / 52,18`, mantendo continuidade
    entre as semanas 52/53 e a semana 1 do ano seguinte.

    A coluna default é `dt_sin_pri` — reflete melhor a sazonalidade da
    circulação viral do que a data de notificação/internação, que
    depende de fatores administrativos. Pode ser sobrescrita por
    `features.engenharia.coluna_sazonalidade`.

    Retorna `pd.DataFrame` com `sin_semana` e `cos_semana` (float64).
    Datas nulas ou não parseáveis resultam em `NaN`.

    Não muta o DataFrame de entrada.
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
    Categoriza idade em anos em faixas configuradas no YAML.

    As faixas vêm de `features.engenharia.faixas_etarias`, cada uma no
    formato `{nome, min, max}`, interpretado como intervalo semiaberto
    `[min, max)`. `max: null` significa "sem limite superior".

    Idade nula vira a categoria explícita `"desconhecida"`.
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
    Normaliza `cs_sexo` (SIVEP) em uma categórica explícita.

    Mapeamento: `"M"` → `"masculino"`; `"F"` → `"feminino"`;
    `"I"` → `"ignorado"`; qualquer outro valor (ou nulo) → `"ausente"`.
    Nunca levanta erro por código desconhecido.
    """
    sexo = df["cs_sexo"].astype("string").str.strip().str.upper()

    out = pd.Series("ausente", index=df.index, dtype="object")
    out[sexo == "M"] = "masculino"
    out[sexo == "F"] = "feminino"
    out[sexo == "I"] = "ignorado"

    return out.astype("category")


def ano_mes_internacao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai `ano_internacao` e `mes_internacao` de `dt_interna`.

    Datas nulas resultam em `NaN` (float64), mantendo compatibilidade
    com `SimpleImputer` e `StandardScaler` sem conversões extras.
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
    Aplica todas as funções acima e devolve cópia de `df` com as
    colunas derivadas adicionadas. O DataFrame de entrada NÃO é
    modificado.

    Colunas adicionadas: `idade_anos`, `dias_sintomas_ate_internacao`,
    `flag_intervalo_invalido`, `flag_internacao_antes_sintomas`,
    `sin_semana`, `cos_semana`, `faixa_etaria`, `sexo_categoria`,
    `ano_internacao`, `mes_internacao`.
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