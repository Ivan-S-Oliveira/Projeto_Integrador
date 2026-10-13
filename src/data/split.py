"""
Criação de partições agrupadas e estratificadas (treino / validação / teste).

Este módulo concentra o split canônico do projeto, antes embutido no
Notebook 03. A função `criar_particoes_agrupadas` garante duas
propriedades simultâneas:

- **Estratificação**: cada partição preserva aproximadamente a proporção
  do alvo (0/1). Útil porque a prevalência de óbito é baixa e um split
  puramente aleatório poderia gerar partições com pouquíssimos positivos.

- **Agrupamento**: todas as linhas de um mesmo grupo (p.ex. mesmo
  paciente, identificado por `nu_notific` ou similar) caem em uma única
  partição. Isso evita vazamento entre treino e avaliação — o mesmo
  indivíduo nunca aparece em treino e teste.

Estratos pequenos
-----------------
Quando um estrato tem menos de `min_grupos_por_estrato` grupos, não há
como distribuir pelo menos um grupo por partição. O comportamento era
silencioso — os grupos iam para `teste` sem aviso. Agora é controlado
por `politica_estratos_pequenos`:

- ``"raise"``        → levanta `ValueError` (default; força decisão).
- ``"warn_teste"``   → warning + todos os grupos do estrato vão para
  `teste` (comportamento legado, agora ruidoso).
- ``"warn_treino"``  → warning + todos para `treino` (mais conservador
  quando o estrato é pequeno demais para ser avaliado).
- ``"drop"``         → warning + linhas do estrato são removidas do
  resultado.

O default é ``"raise"``: prefere quebrar ruidosamente a herdar em
silêncio um comportamento que enviesa o teste.

Uso típico
----------
    from src.data.split import criar_particoes_agrupadas

    df_part = criar_particoes_agrupadas(
        df,
        target_column="alvo",
        group_column="nu_notific",
        partition_column="particao",
    )
    # df_part tem coluna "particao" em {"treino","validacao","teste"}
"""

from __future__ import annotations

import warnings
from typing import Any, Literal

import numpy as np
import pandas as pd

__all__ = [
    "PARTICOES_CANONICAS",
    "SplitWarning",
    "criar_particoes_agrupadas",
]


PARTICOES_CANONICAS: tuple[str, ...] = ("treino", "validacao", "teste")

PoliticaEstratosPequenos = Literal[
    "raise", "warn_teste", "warn_treino", "drop"
]
PoliticaGrupoHeterogeneo = Literal["raise", "warn"]


class SplitWarning(UserWarning):
    """
    Emitido quando o split precisa tomar uma decisão não-trivial.

    Casos que disparam: estratos pequenos demais para as três partições
    e grupos com alvo heterogêneo. Filtre com
    ``warnings.filterwarnings("ignore", category=SplitWarning)`` se a
    decisão já foi tomada pelo grupo.
    """


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validar_parametros(
    df: pd.DataFrame,
    *,
    target_column: str,
    group_column: str,
    partition_column: str,
    frac_treino: float,
    frac_validacao: float,
    min_grupos_por_estrato: int,
    politica_estratos_pequenos: str,
    on_grupo_alvo_heterogeneo: str,
) -> None:
    if df.empty:
        raise ValueError("DataFrame vazio — não há como criar partições.")

    if target_column not in df.columns:
        raise KeyError(f"Coluna de alvo ausente: {target_column!r}")
    if group_column not in df.columns:
        raise KeyError(f"Coluna de grupo ausente: {group_column!r}")
    if partition_column in df.columns:
        raise ValueError(
            f"DataFrame já contém a coluna {partition_column!r}. "
            "Remova-a ou escolha outro nome para `partition_column` — "
            "o split não sobrescreve partições existentes."
        )

    if not (0.0 < frac_treino < 1.0):
        raise ValueError(f"frac_treino deve estar em (0, 1); recebido {frac_treino!r}.")
    if not (0.0 < frac_validacao < 1.0):
        raise ValueError(
            f"frac_validacao deve estar em (0, 1); recebido {frac_validacao!r}."
        )
    if frac_treino + frac_validacao >= 1.0:
        raise ValueError(
            "frac_treino + frac_validacao deve ser < 1 "
            "(o restante vira `teste`)."
        )

    if min_grupos_por_estrato < len(PARTICOES_CANONICAS):
        raise ValueError(
            f"min_grupos_por_estrato deve ser >= {len(PARTICOES_CANONICAS)}; "
            f"recebido {min_grupos_por_estrato!r}."
        )

    if politica_estratos_pequenos not in (
        "raise", "warn_teste", "warn_treino", "drop"
    ):
        raise ValueError(
            f"politica_estratos_pequenos inválida: {politica_estratos_pequenos!r}. "
            "Use 'raise', 'warn_teste', 'warn_treino' ou 'drop'."
        )

    if on_grupo_alvo_heterogeneo not in ("raise", "warn"):
        raise ValueError(
            f"on_grupo_alvo_heterogeneo inválido: "
            f"{on_grupo_alvo_heterogeneo!r}. Use 'raise' ou 'warn'."
        )


def _estrato_por_grupo(
    df: pd.DataFrame,
    *,
    target_column: str,
    group_column: str,
    on_grupo_alvo_heterogeneo: PoliticaGrupoHeterogeneo,
) -> pd.Series:
    """
    Devolve uma `Series` indexada por grupo com o estrato (valor do alvo).

    Grupos com mais de um valor distinto de alvo são tratados por
    `on_grupo_alvo_heterogeneo`:
        - ``"raise"`` (default): levanta `ValueError`.
        - ``"warn"``: emite `SplitWarning` e usa a moda por grupo.

    Grupos com alvo todo nulo são descartados com `SplitWarning` (não há
    estrato para atribuir).
    """
    nunique = (
        df.groupby(group_column, observed=True)[target_column]
          .nunique(dropna=True)
    )
    heterogeneos = nunique[nunique > 1]
    if len(heterogeneos) > 0:
        amostra = heterogeneos.index.tolist()[:5]
        msg = (
            f"{len(heterogeneos)} grupo(s) com mais de um valor distinto "
            f"de alvo em {target_column!r}. Exemplos: {amostra}"
        )
        if on_grupo_alvo_heterogeneo == "raise":
            raise ValueError(
                msg + ". Resolva as inconsistências ou use "
                "on_grupo_alvo_heterogeneo='warn'."
            )
        warnings.warn(
            msg + ". Usando a moda por grupo.",
            SplitWarning,
            stacklevel=3,
        )

    if len(heterogeneos) > 0:
        estrato = (
            df.groupby(group_column, observed=True)[target_column]
              .agg(lambda s: s.dropna().mode().iloc[0] if s.notna().any() else None)
        )
    else:
        estrato = (
            df.groupby(group_column, observed=True)[target_column]
              .agg(lambda s: s.dropna().iloc[0] if s.notna().any() else None)
        )

    sem_alvo = estrato[estrato.isna()]
    if len(sem_alvo) > 0:
        warnings.warn(
            f"{len(sem_alvo)} grupo(s) com alvo todo nulo em {target_column!r}. "
            "Serão descartados do split.",
            SplitWarning,
            stacklevel=3,
        )
        estrato = estrato.dropna()

    if estrato.empty:
        raise ValueError(
            "Nenhum grupo com alvo não nulo — impossível estratificar."
        )

    return estrato


def _distribuir_tamanhos(
    n: int,
    frac_treino: float,
    frac_validacao: float,
) -> tuple[int, int, int]:
    """
    Distribui `n` grupos em (treino, validacao, teste) respeitando as
    frações e garantindo ≥1 grupo por partição.

    Requer `n >= 3`.
    """
    if n < 3:
        raise ValueError(f"_distribuir_tamanhos requer n >= 3; recebido {n}.")

    n_treino = max(1, int(n * frac_treino))
    n_valid = max(1, int(n * frac_validacao))
    n_teste = n - n_treino - n_valid
    if n_teste < 1:
        n_treino = n - n_valid - 1
        n_teste = 1
    return n_treino, n_valid, n_teste


# ---------------------------------------------------------------------------
# Split agrupado + estratificado
# ---------------------------------------------------------------------------

def criar_particoes_agrupadas(
    df: pd.DataFrame,
    *,
    target_column: str,
    group_column: str,
    partition_column: str = "particao",
    frac_treino: float = 0.7,
    frac_validacao: float = 0.15,
    seed: int = 42,
    min_grupos_por_estrato: int = 3,
    politica_estratos_pequenos: PoliticaEstratosPequenos = "raise",
    on_grupo_alvo_heterogeneo: PoliticaGrupoHeterogeneo = "raise",
) -> pd.DataFrame:
    """
    Cria partições treino/validação/teste agrupadas por `group_column`
    e estratificadas por `target_column`.

    A função **não muta** `df`: devolve uma cópia com a coluna
    `partition_column` adicionada, contendo os rótulos
    `"treino"`, `"validacao"` ou `"teste"`.

    Parâmetros
    ----------
    df : pd.DataFrame
        Base de entrada. Precisa conter `target_column` e `group_column`.
    target_column : str
        Coluna binária (0/1) usada como estrato.
    group_column : str
        Coluna de agrupamento (p.ex. `nu_notific`). Todas as linhas de um
        mesmo grupo caem na mesma partição.
    partition_column : str
        Nome da coluna de saída. Não pode já existir em `df`.
    frac_treino, frac_validacao : float
        Frações alvo. `frac_teste = 1 - frac_treino - frac_validacao`.
    seed : int
        Semente do gerador. Mesmo `seed` + mesmo `df` → mesmo resultado.
    min_grupos_por_estrato : int
        Mínimo de grupos por estrato para permitir split em três
        partições. Precisa ser ≥ 3. Estratos abaixo desse mínimo são
        tratados por `politica_estratos_pequenos`.
    politica_estratos_pequenos : {"raise", "warn_teste", "warn_treino", "drop"}
        O que fazer com estratos pequenos:
          - ``"raise"`` (default): falha explícita.
          - ``"warn_teste"``: warning + estrato inteiro vai para `teste`.
          - ``"warn_treino"``: warning + estrato inteiro vai para `treino`.
          - ``"drop"``: warning + linhas do estrato removidas.
    on_grupo_alvo_heterogeneo : {"raise", "warn"}
        Como tratar grupos com mais de um valor de alvo. ``"raise"``
        (default) falha; ``"warn"`` usa a moda por grupo.

    Retorno
    -------
    pd.DataFrame
        Cópia de `df` com a coluna `partition_column` (dtype `object`)
        contendo `"treino"`, `"validacao"` ou `"teste"`. Grupos com alvo
        nulo e estratos descartados por `politica_estratos_pequenos="drop"`
        não aparecem no resultado.

    Levanta
    ------
    KeyError
        Se `target_column` ou `group_column` não existirem em `df`.
    ValueError
        Parâmetros inválidos, DataFrame vazio, coluna de partição já
        presente, ou estrato pequeno com política ``"raise"``.
    """
    _validar_parametros(
        df,
        target_column=target_column,
        group_column=group_column,
        partition_column=partition_column,
        frac_treino=frac_treino,
        frac_validacao=frac_validacao,
        min_grupos_por_estrato=min_grupos_por_estrato,
        politica_estratos_pequenos=politica_estratos_pequenos,
        on_grupo_alvo_heterogeneo=on_grupo_alvo_heterogeneo,
    )

    estrato_por_grupo = _estrato_por_grupo(
        df,
        target_column=target_column,
        group_column=group_column,
        on_grupo_alvo_heterogeneo=on_grupo_alvo_heterogeneo,
    )

    rng = np.random.default_rng(seed)
    atribuicao: dict[Any, str] = {}
    descartar: set[Any] = set()

    for estrato, sub in estrato_por_grupo.groupby(estrato_por_grupo):
        grupos = sub.index.tolist()
        rng.shuffle(grupos)
        n = len(grupos)

        if n < min_grupos_por_estrato:
            msg = (
                f"Estrato {estrato!r} tem apenas {n} grupo(s) "
                f"(< min_grupos_por_estrato={min_grupos_por_estrato}). "
                f"Política: {politica_estratos_pequenos!r}."
            )
            if politica_estratos_pequenos == "raise":
                raise ValueError(
                    msg + " Ajuste min_grupos_por_estrato ou use "
                    "politica_estratos_pequenos='warn_teste'|'warn_treino'|'drop'."
                )
            if politica_estratos_pequenos == "warn_teste":
                warnings.warn(
                    msg + " Destinando ao teste.", SplitWarning, stacklevel=2
                )
                for g in grupos:
                    atribuicao[g] = "teste"
            elif politica_estratos_pequenos == "warn_treino":
                warnings.warn(
                    msg + " Destinando ao treino.", SplitWarning, stacklevel=2
                )
                for g in grupos:
                    atribuicao[g] = "treino"
            elif politica_estratos_pequenos == "drop":
                warnings.warn(
                    msg + " Descartando do resultado.", SplitWarning, stacklevel=2
                )
                descartar.update(grupos)
            continue

        n_treino, n_valid, _n_teste = _distribuir_tamanhos(
            n, frac_treino, frac_validacao
        )
        for g in grupos[:n_treino]:
            atribuicao[g] = "treino"
        for g in grupos[n_treino:n_treino + n_valid]:
            atribuicao[g] = "validacao"
        for g in grupos[n_treino + n_valid:]:
            atribuicao[g] = "teste"

    out = df.copy()
    out[partition_column] = out[group_column].map(atribuicao)

    # Grupos com alvo todo nulo (não atribuídos) e estratos descartados
    # saem do resultado final.
    invalidos = out[partition_column].isna() | out[group_column].isin(descartar)
    if invalidos.any():
        out = out.loc[~invalidos].reset_index(drop=True)

    out[partition_column] = out[partition_column].astype("object")

    faltando = set(PARTICOES_CANONICAS) - set(out[partition_column].unique())
    if faltando:
        warnings.warn(
            f"Partição(ões) sem nenhuma linha após o split: {sorted(faltando)}. "
            "Verifique a distribuição dos estratos antes de prosseguir.",
            SplitWarning,
            stacklevel=2,
        )

    return out