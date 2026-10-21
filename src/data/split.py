"""Particionamento agrupado, estratificado e determinístico por hash."""

from __future__ import annotations

import hashlib
import warnings
from typing import Any, Literal, cast, get_args

import numpy as np
import pandas as pd

__all__ = [
    "DEFAULT_FRACOES_MASTER",
    "MASTER_BLOCKS",
    "PARTICOES_CANONICAS",
    "SplitWarning",
    "atribuir_blocos_por_hash",
    "atribuir_particao_estratificada_por_hash",
    "criar_particao_mestra",
    "criar_particoes_agrupadas",
]

PARTICOES_CANONICAS: tuple[str, ...] = ("treino", "validacao", "teste")

MASTER_BLOCKS: tuple[str, ...] = (
    "train_ref",
    "val_tune",
    "val_cal",
    "val_meas",
    "test_ref",
    "test_pandemic",
)

DEFAULT_FRACOES_MASTER: dict[str, float] = {
    "train_ref": 0.70,
    "val_tune": 0.05,
    "val_cal": 0.05,
    "val_meas": 0.05,
    "test_ref": 0.15,
}

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
        raise ValueError("DataFrame vazio.")
    if target_column not in df.columns:
        raise KeyError(f"Coluna de alvo ausente: {target_column!r}")
    if group_column not in df.columns:
        raise KeyError(f"Coluna de grupo ausente: {group_column!r}")
    if partition_column in df.columns:
        raise ValueError(
            f"DataFrame já contém {partition_column!r}; "
            "o split não sobrescreve partições."
        )

    if not 0.0 < frac_treino < 1.0:
        raise ValueError(f"frac_treino inválido: {frac_treino!r}.")
    if not 0.0 < frac_validacao < 1.0:
        raise ValueError(f"frac_validacao inválido: {frac_validacao!r}.")
    if frac_treino + frac_validacao >= 1.0:
        raise ValueError("frac_treino + frac_validacao deve ser < 1.")

    if min_grupos_por_estrato < len(PARTICOES_CANONICAS):
        raise ValueError(
            f"min_grupos_por_estrato deve ser >= {len(PARTICOES_CANONICAS)}; "
            f"recebido {min_grupos_por_estrato!r}."
        )
    if politica_estratos_pequenos not in _POLITICAS_ESTRATOS_PEQUENOS:
        raise ValueError(
            f"politica_estratos_pequenos inválida: {politica_estratos_pequenos!r}."
        )
    if on_grupo_alvo_heterogeneo not in _POLITICAS_GRUPO_HETEROGENEO:
        raise ValueError(
            f"on_grupo_alvo_heterogeneo inválido: {on_grupo_alvo_heterogeneo!r}."
        )


def _estrato_por_grupo(
    df: pd.DataFrame,
    *,
    target_column: str,
    group_column: str,
    on_grupo_alvo_heterogeneo: PoliticaGrupoHeterogeneo,
) -> pd.Series:
    """Estrato (moda do alvo) por grupo."""
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
                msg + ". Use on_grupo_alvo_heterogeneo='warn' para seguir."
            )
        warnings.warn(msg + ". Usando a moda.", SplitWarning, stacklevel=3)

    estrato = agrupado.agg(
        lambda s: s.dropna().mode().iloc[0] if s.notna().any() else None
    )

    if estrato.isna().any():
        n = int(estrato.isna().sum())
        warnings.warn(
            f"{n} grupo(s) sem alvo não nulo; serão descartados.",
            SplitWarning,
            stacklevel=3,
        )
        estrato = estrato.dropna()

    if estrato.empty:
        raise ValueError("Nenhum grupo com alvo não nulo.")

    return estrato


def _distribuir_tamanhos(
    n: int,
    frac_treino: float,
    frac_validacao: float,
) -> tuple[int, int, int]:
    """Distribui ``n >= 3`` grupos em (treino, validação, teste), ≥1 por partição."""
    if n < 3:
        raise ValueError(f"requer n >= 3; recebido {n}.")

    n_valid = max(1, int(n * frac_validacao))
    n_teste = max(1, n - max(1, int(n * frac_treino)) - n_valid)
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
        f"Estrato {estrato!r} tem {n} grupo(s) "
        f"(< {min_grupos_por_estrato}); política {politica!r}."
    )

    if politica == "raise":
        raise ValueError(msg)

    if politica == "drop":
        warnings.warn(f"{msg} Descartando.", SplitWarning, stacklevel=2)
        descartar.update(grupos)
        return

    destino = "teste" if politica == "warn_teste" else "treino"
    warnings.warn(f"{msg} Destinando ao {destino}.", SplitWarning, stacklevel=2)
    atribuicao.update({g: destino for g in grupos})


def _hash_codes(
    grupos_unicos: pd.Index,
    estrato_grupo: np.ndarray,
    sal: str,
) -> np.ndarray:
    """Ordem estável dos grupos por hash dentro de cada estrato."""
    chaves = sal + "|" + pd.Series(grupos_unicos.astype(str), dtype=object)
    hashes = pd.util.hash_pandas_object(chaves, index=False).to_numpy(dtype=np.uint64)
    # lexsort usa a última chave como primária: (hash, estrato)
    return np.lexsort((hashes, estrato_grupo))


def _validar_estratos(
    grupos: pd.Series,
    estratos: pd.Series,
    min_grupos_por_estrato: int,
    n_blocos: int,
) -> tuple[np.ndarray, pd.Index, np.ndarray]:
    """Fatoriza grupos/estratos e devolve (codigo_grupo, grupos_unicos, estrato_grupo)."""
    if grupos.isna().any():
        raise ValueError(f"'{grupos.name}' contém valores ausentes.")
    if estratos.isna().any():
        raise ValueError(f"'{estratos.name}' contém valores ausentes.")
    if min_grupos_por_estrato < n_blocos:
        raise ValueError(
            f"min_grupos_por_estrato deve ser >= {n_blocos}; "
            f"recebido {min_grupos_por_estrato!r}."
        )

    codigo_grupo, grupos_unicos = pd.factorize(grupos, sort=False)
    codigo_estrato_linha, estratos_unicos = pd.factorize(estratos, sort=True)
    n_grupos = len(grupos_unicos)

    estrato_min = np.full(n_grupos, np.iinfo(np.int64).max, dtype=np.int64)
    estrato_max = np.full(n_grupos, -1, dtype=np.int64)
    np.minimum.at(estrato_min, codigo_grupo, codigo_estrato_linha)
    np.maximum.at(estrato_max, codigo_grupo, codigo_estrato_linha)
    if int((estrato_min != estrato_max).sum()):
        raise ValueError("Há grupos com mais de um estrato.")
    estrato_grupo = estrato_min

    grupos_por_estrato = np.bincount(estrato_grupo, minlength=len(estratos_unicos))
    pequenos = [
        (str(estratos_unicos[i]), int(q))
        for i, q in enumerate(grupos_por_estrato)
        if q < min_grupos_por_estrato
    ]
    if pequenos:
        raise ValueError(
            f"Estratos abaixo de {min_grupos_por_estrato} grupos: {pequenos}"
        )
    return codigo_grupo, grupos_unicos, estrato_grupo


def _posicao_no_estrato(
    grupos_unicos: pd.Index,
    estrato_grupo: np.ndarray,
    sal: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Devolve (posicao_dentro_do_estrato, tamanho_do_estrato) por grupo único."""
    ordem = _hash_codes(grupos_unicos, estrato_grupo, sal)
    n_grupos = len(grupos_unicos)
    tamanho_por_estrato = np.bincount(
        estrato_grupo, minlength=estrato_grupo.max() + 1 if n_grupos else 1
    )
    inicio = np.concatenate(([0], np.cumsum(tamanho_por_estrato)[:-1]))
    posicao = np.empty(n_grupos, dtype=np.int64)
    posicao[ordem] = np.arange(n_grupos) - inicio[estrato_grupo[ordem]]
    return posicao, tamanho_por_estrato[estrato_grupo]


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

    Todas as linhas de um grupo vão para a mesma partição. Dentro de cada
    estrato, os grupos são ordenados pelo hash do ID e cortados nas
    frações dadas. Não usa gerador aleatório — depende só do ID, do
    estrato, do ``sal`` e das frações.

    Método oficial do projeto (``hash_grupo_estratificado_v1``).
    """
    if not 0.0 < frac_treino < 1.0:
        raise ValueError(f"frac_treino inválido: {frac_treino!r}.")
    if not 0.0 < frac_validacao < 1.0:
        raise ValueError(f"frac_validacao inválido: {frac_validacao!r}.")
    if frac_treino + frac_validacao >= 1.0:
        raise ValueError("frac_treino + frac_validacao deve ser < 1.")

    codigo_grupo, grupos_unicos, estrato_grupo = _validar_estratos(
        grupos, estratos, min_grupos_por_estrato, len(PARTICOES_CANONICAS)
    )
    posicao, tamanho = _posicao_no_estrato(grupos_unicos, estrato_grupo, sal)

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


def atribuir_blocos_por_hash(
    grupos: pd.Series,
    estratos: pd.Series,
    *,
    sal: str,
    fracoes: dict[str, float],
    min_grupos_por_estrato: int = 5,
) -> pd.Categorical:
    """Atribui cada grupo a um dos blocos definidos em ``fracoes``.

    Mesma mecânica de ``atribuir_particao_estratificada_por_hash``, mas
    aceita N blocos com frações explícitas (devem somar 1). Cada estrato
    recebe ao menos um grupo por bloco.
    """
    nomes = list(fracoes)
    valores = list(fracoes.values())
    if abs(sum(valores) - 1.0) > 1e-6:
        raise ValueError(f"Frações devem somar 1; soma={sum(valores):.6f}.")

    codigo_grupo, grupos_unicos, estrato_grupo = _validar_estratos(
        grupos, estratos, min_grupos_por_estrato, len(nomes)
    )
    posicao, tamanho = _posicao_no_estrato(grupos_unicos, estrato_grupo, sal)

    restante = len(nomes) - 1
    acumulado = 0.0
    codigo_bloco = np.zeros(len(grupos_unicos), dtype=np.int8)
    for fracao in valores[:-1]:
        acumulado += fracao
        corte = np.minimum(
            np.floor(tamanho * acumulado).astype(np.int64),
            tamanho - restante,
        )
        codigo_bloco = np.where(posicao >= corte, codigo_bloco + 1, codigo_bloco)
        restante -= 1

    return pd.Categorical.from_codes(
        codigo_bloco[codigo_grupo].astype(np.int64),
        categories=cast(Any, nomes),
    )


def _resolver_fracoes_master(
    blocos_cfg: dict[str, Any],
    blocos_compartilhados: list[str],
) -> dict[str, float]:
    fracoes = {
        nome: float((blocos_cfg.get(nome) or {}).get("fracao", DEFAULT_FRACOES_MASTER[nome]))
        for nome in blocos_compartilhados
    }
    if abs(sum(fracoes.values()) - 1.0) > 1e-6:
        raise ValueError(
            f"Frações dos blocos compartilhados devem somar 1; recebido {fracoes}."
        )
    return fracoes

def _hash_bloco(grupos: pd.Series) -> str | None:
    if grupos.empty:
        return None
    chaves = sorted(grupos.astype(str).unique().tolist())
    return hashlib.sha256("|".join(chaves).encode()).hexdigest()


def criar_particao_mestra(
    df: pd.DataFrame,
    *,
    temporal_cfg: dict[str, Any],
    group_column: str = "group_id",
    year_column: str = "ano_internacao",
    target_column: str = "alvo_obito_srag",
    region_column: str | None = "regiao_residencia",
    partition_column: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Materializa os seis blocos de ``temporal.blocos`` no DataFrame.

    - 2019/2023/2024/2025 → hash por (ano × alvo × região) entre os cinco
      blocos compartilhados (fallback para ano × alvo se algum estrato
      ficar abaixo do mínimo).
    - 2020/2021/2022 → 100% em ``test_pandemic``.
    - Demais anos (2026) → ``"exploracao"``.

    Levanta ``RuntimeError`` se um ``group_id`` aparecer em mais de um
    bloco — normalmente indica linhas de um mesmo grupo em anos pandêmicos
    e não pandêmicos.

    Retorna ``(df_com_particao, manifesto)``. O manifesto registra, por
    bloco, contagem, nº de grupos, anos, prevalência do alvo e hash.
    """
    partition_column = str(
        partition_column or temporal_cfg.get("coluna_particao") or "particao"
    )
    seed = int(temporal_cfg.get("seed", 42))
    sal = f"srag_particao_mestra_v1_seed{seed}"

    blocos_cfg = temporal_cfg.get("blocos") or {}
    if not blocos_cfg:
        raise ValueError("temporal.blocos vazio no supervised.yaml.")

    anos_por_bloco = {
        nome: {int(a) for a in cfg.get("anos", [])}
        for nome, cfg in blocos_cfg.items()
    }
    if set(anos_por_bloco) != set(MASTER_BLOCKS):
        raise ValueError(
            f"Blocos do YAML {sorted(anos_por_bloco)} "
            f"não conferem com MASTER_BLOCKS {sorted(MASTER_BLOCKS)}."
        )

    anos_pandemia = anos_por_bloco["test_pandemic"]
    blocos_compartilhados = [n for n in MASTER_BLOCKS if n != "test_pandemic"]
    anos_compartilhados = set().union(
        *(anos_por_bloco[n] for n in blocos_compartilhados)
    )
    fracoes = _resolver_fracoes_master(blocos_cfg, blocos_compartilhados)

    min_grupos = int(temporal_cfg.get("min_grupos_por_estrato", 5))
    if min_grupos < len(blocos_compartilhados):
        raise ValueError(
            f"temporal.min_grupos_por_estrato={min_grupos} insuficiente "
            f"para {len(blocos_compartilhados)} blocos compartilhados; "
            f"use >= {len(blocos_compartilhados)}."
        )

    out = df.copy()
    out[partition_column] = pd.NA

    mascara_pandemia = out[year_column].isin(anos_pandemia)
    out.loc[mascara_pandemia, partition_column] = "test_pandemic"

    mascara_compartilhada = out[year_column].isin(anos_compartilhados)
    usado_fallback = False
    if mascara_compartilhada.any():
        sub = out.loc[mascara_compartilhada]
        estrato = sub[year_column].astype(str) + "|" + sub[target_column].astype(str)
        if region_column and region_column in sub.columns:
            estrato = estrato + "|" + sub[region_column].fillna("__NA__").astype(str)

        try:
            blocos = atribuir_blocos_por_hash(
                sub[group_column], estrato,
                sal=sal, fracoes=fracoes, min_grupos_por_estrato=min_grupos,
            )
        except ValueError:
            estrato = sub[year_column].astype(str) + "|" + sub[target_column].astype(str)
            blocos = atribuir_blocos_por_hash(
                sub[group_column], estrato,
                sal=sal, fracoes=fracoes, min_grupos_por_estrato=min_grupos,
            )
            usado_fallback = True

        out.loc[mascara_compartilhada, partition_column] = blocos

    mascara_fora = ~(mascara_pandemia | mascara_compartilhada)
    out.loc[mascara_fora, partition_column] = "exploracao"

    if out[partition_column].isna().any():
        raise RuntimeError("Há linhas sem bloco atribuído.")

    blocos_por_grupo = out.groupby(group_column)[partition_column].nunique()
    cruzados = blocos_por_grupo[blocos_por_grupo > 1]
    if not cruzados.empty:
        raise RuntimeError(
            f"{len(cruzados)} grupos em mais de um bloco; exemplos: "
            f"{cruzados.index.tolist()[:5]}. Verifique se algum group_id "
            "tem linhas em anos pandêmicos e não pandêmicos."
        )

    manifesto: dict[str, Any] = {
        "metodo": "hash_grupo_estratificado_mestre_v1",
        "salt": sal,
        "seed": seed,
        "min_grupos_por_estrato": min_grupos,
        "group_column": group_column,
        "year_column": year_column,
        "target_column": target_column,
        "region_column": region_column,
        "partition_column": partition_column,
        "fracoes": fracoes,
        "estratificacao": (
            "ano × alvo (fallback)" if usado_fallback else "ano × alvo × região"
        ),
        "blocos": {},
    }
    for nome in (*MASTER_BLOCKS, "exploracao"):
        sub = out.loc[out[partition_column] == nome]
        manifesto["blocos"][nome] = {
            "n_linhas": int(len(sub)),
            "n_grupos": int(sub[group_column].nunique()) if len(sub) else 0,
            "anos": sorted(int(a) for a in sub[year_column].dropna().unique()),
            "prevalencia_alvo": (
                float(pd.to_numeric(sub[target_column], errors="coerce").mean())
                if len(sub) else None
            ),
            "hash_bloco": _hash_bloco(sub[group_column]),
        }
    return out, manifesto


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
        não escala para a coorte real.
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
            "treino": grupos[:n_treino],
            "validacao": grupos[n_treino:n_treino + n_valid],
            "teste": grupos[n_treino + n_valid:],
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
            f"Partição(ões) sem linhas após o split: {sorted(faltando)}.",
            SplitWarning,
            stacklevel=2,
        )

    return out