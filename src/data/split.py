"""Particionamento agrupado, estratificado e determinístico por hash."""

from __future__ import annotations

import warnings
from typing import Any, Literal, cast, get_args

import numpy as np
import pandas as pd

__all__ = [
    "PARTICOES_CANONICAS",
    "SplitWarning",
    "atribuir_particao_estratificada_por_hash",
    "criar_particoes_agrupadas",
]

PARTICOES_CANONICAS: tuple[str, ...] = ("treino", "validacao", "teste")

PoliticaEstratosPequenos = Literal["raise", "warn_teste", "warn_treino", "drop"]
PoliticaGrupoHeterogeneo = Literal["raise", "warn"]

_POLITICAS_ESTRATOS_PEQUENOS = frozenset(get_args(PoliticaEstratosPequenos))
_POLITICAS_GRUPO_HETEROGENEO = frozenset(get_args(PoliticaGrupoHeterogeneo))


class SplitWarning(UserWarning):
    """Decisão não-trivial do split (estrato pequeno, grupo com alvo misto).

    Filtre com ``warnings.filterwarnings("ignore", category=SplitWarning)``
    se a decisão já foi tomada pelo grupo.
    """


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
            "Remova-a ou escolha outro nome — o split não sobrescreve partições."
        )

    if not 0.0 < frac_treino < 1.0:
        raise ValueError(f"frac_treino deve estar em (0, 1); recebido {frac_treino!r}.")
    if not 0.0 < frac_validacao < 1.0:
        raise ValueError(f"frac_validacao deve estar em (0, 1); recebido {frac_validacao!r}.")
    if frac_treino + frac_validacao >= 1.0:
        raise ValueError("frac_treino + frac_validacao deve ser < 1 (resto vira `teste`).")

    if min_grupos_por_estrato < len(PARTICOES_CANONICAS):
        raise ValueError(
            f"min_grupos_por_estrato deve ser >= {len(PARTICOES_CANONICAS)}; "
            f"recebido {min_grupos_por_estrato!r}."
        )
    if politica_estratos_pequenos not in _POLITICAS_ESTRATOS_PEQUENOS:
        raise ValueError(
            f"politica_estratos_pequenos inválida: {politica_estratos_pequenos!r}. "
            f"Use uma de {sorted(_POLITICAS_ESTRATOS_PEQUENOS)}."
        )
    if on_grupo_alvo_heterogeneo not in _POLITICAS_GRUPO_HETEROGENEO:
        raise ValueError(
            f"on_grupo_alvo_heterogeneo inválido: {on_grupo_alvo_heterogeneo!r}. "
            f"Use uma de {sorted(_POLITICAS_GRUPO_HETEROGENEO)}."
        )


def _estrato_por_grupo(
    df: pd.DataFrame,
    *,
    target_column: str,
    group_column: str,
    on_grupo_alvo_heterogeneo: PoliticaGrupoHeterogeneo,
) -> pd.Series:
    """Estrato (valor do alvo) por grupo."""
    agrupado = df.groupby(group_column, observed=True)[target_column]

    heterogeneos = agrupado.nunique(dropna=True)
    heterogeneos = heterogeneos[heterogeneos > 1]
    if not heterogeneos.empty:
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
        warnings.warn(msg + ". Usando a moda por grupo.", SplitWarning, stacklevel=3)

    estrato = agrupado.agg(
        lambda s: s.dropna().mode().iloc[0] if s.notna().any() else None
    )

    if estrato.isna().any():
        n = int(estrato.isna().sum())
        warnings.warn(
            f"{n} grupo(s) com alvo todo nulo em {target_column!r}. "
            "Serão descartados do split.",
            SplitWarning,
            stacklevel=3,
        )
        estrato = estrato.dropna()

    if estrato.empty:
        raise ValueError("Nenhum grupo com alvo não nulo — impossível estratificar.")

    return estrato


def _distribuir_tamanhos(
    n: int,
    frac_treino: float,
    frac_validacao: float,
) -> tuple[int, int, int]:
    """Distribui ``n >= 3`` grupos em (treino, validação, teste), ≥1 por partição."""
    if n < 3:
        raise ValueError(f"_distribuir_tamanhos requer n >= 3; recebido {n}.")

    n_valid  = max(1, int(n * frac_validacao))
    n_teste  = max(1, n - max(1, int(n * frac_treino)) - n_valid)
    n_treino = n - n_valid - n_teste
    return n_treino, n_valid, n_teste


def _aplicar_politica_estrato_pequeno(
    grupos: list[Any],
    *,
    estrato: Any,
    min_grupos_por_estrato: int,
    politica: PoliticaEstratosPequenos,
    atribuicao: dict[Any, str],
    descartar: set[Any],
) -> None:
    n = len(grupos)
    msg = (
        f"Estrato {estrato!r} tem apenas {n} grupo(s) "
        f"(< min_grupos_por_estrato={min_grupos_por_estrato}). "
        f"Política: {politica!r}."
    )

    if politica == "raise":
        raise ValueError(
            msg + " Ajuste min_grupos_por_estrato ou use "
            "politica_estratos_pequenos='warn_teste'|'warn_treino'|'drop'."
        )

    if politica == "drop":
        warnings.warn(f"{msg} Descartando do resultado.", SplitWarning, stacklevel=2)
        descartar.update(grupos)
        return

    destino = "teste" if politica == "warn_teste" else "treino"
    warnings.warn(f"{msg} Destinando ao {destino}.", SplitWarning, stacklevel=2)
    atribuicao.update({g: destino for g in grupos})


def atribuir_particao_estratificada_por_hash(
    grupos: pd.Series,
    estratos: pd.Series,
    *,
    sal: str,
    frac_treino: float,
    frac_validacao: float,
    min_grupos_por_estrato: int = 3,
) -> pd.Categorical:
    """Partição agrupada, estratificada e determinística por hash.

    - Agrupada: todas as linhas de um grupo vão para a mesma partição.
    - Estratificada: dentro de cada estrato (ex.: ano x alvo), os grupos
      são ordenados pelo hash do ID e cortados nas frações dadas.
    - Determinística: não usa gerador aleatório. O resultado depende só
      do ID do grupo, do estrato, do ``sal`` e das frações, não da ordem
      das linhas.

    É o método oficial do projeto (``hash_grupo_estratificado_v1``).
    """
    if grupos.isna().any():
        raise ValueError(f"'{grupos.name}' contém valores ausentes.")
    if estratos.isna().any():
        raise ValueError(f"'{estratos.name}' contém valores ausentes.")

    if not 0.0 < frac_treino < 1.0:
        raise ValueError(f"frac_treino deve estar em (0, 1); recebido {frac_treino!r}.")
    if not 0.0 < frac_validacao < 1.0:
        raise ValueError(f"frac_validacao deve estar em (0, 1); recebido {frac_validacao!r}.")
    if frac_treino + frac_validacao >= 1.0:
        raise ValueError("frac_treino + frac_validacao deve ser < 1 (resto vira teste).")
    if min_grupos_por_estrato < len(PARTICOES_CANONICAS):
        raise ValueError(
            f"min_grupos_por_estrato deve ser >= {len(PARTICOES_CANONICAS)}; "
            f"recebido {min_grupos_por_estrato!r}."
        )

    codigo_grupo, grupos_unicos = pd.factorize(grupos, sort=False)
    codigo_estrato_linha, estratos_unicos = pd.factorize(estratos, sort=True)
    n_grupos = len(grupos_unicos)

    estrato_min = np.full(n_grupos, np.iinfo(np.int64).max, dtype=np.int64)
    estrato_max = np.full(n_grupos, -1, dtype=np.int64)
    np.minimum.at(estrato_min, codigo_grupo, codigo_estrato_linha)
    np.maximum.at(estrato_max, codigo_grupo, codigo_estrato_linha)
    multiestrato = int((estrato_min != estrato_max).sum())
    if multiestrato:
        raise ValueError(f"{multiestrato} grupos possuem mais de um estrato.")
    estrato_grupo = estrato_min

    grupos_por_estrato = np.bincount(estrato_grupo, minlength=len(estratos_unicos))
    pequenos = [
        (str(estratos_unicos[i]), int(qtd))
        for i, qtd in enumerate(grupos_por_estrato)
        if qtd < min_grupos_por_estrato
    ]
    if pequenos:
        raise ValueError(
            f"Estratos abaixo de min_grupos_por_estrato={min_grupos_por_estrato}: {pequenos}"
        )

    chaves = sal + "|" + pd.Series(grupos_unicos.astype(str), dtype=object)
    hashes = pd.util.hash_pandas_object(chaves, index=False).to_numpy(dtype=np.uint64)

    # lexsort usa a última chave como primária; por isso a ordem é (hash, estrato).
    ordem = np.lexsort((hashes, estrato_grupo))
    inicio_estrato = np.concatenate(([0], np.cumsum(grupos_por_estrato)[:-1]))
    posicao = np.empty(n_grupos, dtype=np.int64)
    posicao[ordem] = np.arange(n_grupos) - inicio_estrato[estrato_grupo[ordem]]

    tamanho = grupos_por_estrato[estrato_grupo]
    corte_valid = np.minimum(
        np.floor(tamanho * (frac_treino + frac_validacao)).astype(np.int64),
        tamanho - 1,
    )
    corte_treino = np.minimum(
        np.floor(tamanho * frac_treino).astype(np.int64),
        corte_valid - 1,
    )

    codigo_particao_grupo = np.where(
        posicao < corte_treino, 0, np.where(posicao < corte_valid, 1, 2)
    ).astype(np.int8)

    return pd.Categorical.from_codes(
        codigo_particao_grupo[codigo_grupo].astype(np.int64),
        categories=cast(Any, list(PARTICOES_CANONICAS)),
    )


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
    """Partições treino/validação/teste agrupadas e estratificadas.

    .. deprecated::
        Use ``atribuir_particao_estratificada_por_hash``. Esta função não
        produz a partição oficial do projeto — mantém-se apenas por
        compatibilidade com testes históricos e usa um laço em Python que
        não escala para a coorte real (> 10 min vs ~9 s).
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

    rng       = np.random.default_rng(seed)
    atribuicao: dict[Any, str] = {}
    descartar: set[Any] = set()

    for estrato, sub in estrato_por_grupo.groupby(estrato_por_grupo):
        grupos = sub.index.tolist()
        rng.shuffle(grupos)

        if len(grupos) < min_grupos_por_estrato:
            _aplicar_politica_estrato_pequeno(
                grupos,
                estrato=estrato,
                min_grupos_por_estrato=min_grupos_por_estrato,
                politica=politica_estratos_pequenos,
                atribuicao=atribuicao,
                descartar=descartar,
            )
            continue

        n_treino, n_valid, n_teste = _distribuir_tamanhos(
            len(grupos), frac_treino, frac_validacao,
        )
        fatias = {
            "treino":    grupos[:n_treino],
            "validacao": grupos[n_treino:n_treino + n_valid],
            "teste":     grupos[n_treino + n_valid:],
        }
        for particao, membros in fatias.items():
            atribuicao.update({g: particao for g in membros})

    out = df.copy()
    out[partition_column] = out[group_column].map(atribuicao)

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