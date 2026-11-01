"""Particionamento agrupado, estratificado e determinístico por hash."""

from __future__ import annotations

import hashlib
from typing import Any, cast

import numpy as np
import pandas as pd

__all__ = [
    "DEFAULT_FRACOES_MASTER",
    "MASTER_BLOCKS",
    "PARTICOES_CANONICAS",
    "atribuir_blocos_por_hash",
    "atribuir_particao_estratificada_por_hash",
    "criar_group_id",
    "criar_particao_mestra",
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

_VALORES_TEXTUAIS_AUSENTES = frozenset({"", "nan", "none", "null", "<na>"})


def criar_group_id(df: pd.DataFrame) -> pd.Series:
    """Cria o identificador estável usado no particionamento agrupado.

    Usa ``nu_notific`` sem espaços quando o valor é válido. Apenas nas linhas
    sem notificação válida exige ``id_registro`` e usa o prefixo
    ``sem_notific:``. O resultado independe da ordem e do índice das linhas.
    """
    if "nu_notific" not in df.columns:
        raise KeyError("Coluna necessária para criar group_id ausente: 'nu_notific'")

    nu_notific = (
        df["nu_notific"]
        .astype("string")
        .str.replace(r"\s+", "", regex=True)
    )
    notific_normalizada = nu_notific.str.lower()
    notific_valida = (
        nu_notific.notna()
        & ~notific_normalizada.isin(_VALORES_TEXTUAIS_AUSENTES)
    )

    if notific_valida.all():
        return nu_notific.rename("group_id")

    if "id_registro" not in df.columns:
        raise KeyError(
            "Coluna necessária para fallback de group_id ausente: 'id_registro'"
        )

    id_registro = df["id_registro"].astype("string").str.strip()
    id_normalizado = id_registro.str.lower()
    id_invalido = (
        id_registro.isna()
        | id_normalizado.isin(_VALORES_TEXTUAIS_AUSENTES)
    )
    fallback_necessario = ~notific_valida
    fallback_invalido = fallback_necessario & id_invalido

    if fallback_invalido.any():
        quantidade = int(fallback_invalido.sum())
        raise ValueError(
            "id_registro ausente ou inválido em "
            f"{quantidade} registro(s) que exigem fallback de group_id."
        )

    fallback = "sem_notific:" + id_registro
    group_id = nu_notific.where(notific_valida, fallback)
    return group_id.astype("string").rename("group_id")


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
    A entrada não é alterada; as colunas originais são compartilhadas
    com ``df`` (cópia rasa), sem duplicar a memória do DataFrame.
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
    usar_regiao = bool(region_column and region_column in df.columns)
    colunas_estrato = [group_column, year_column, target_column]
    if usar_regiao:
        colunas_estrato.append(region_column)
    out = df.copy(deep=False)
    out[partition_column] = pd.NA
    mascara_pandemia = out[year_column].isin(anos_pandemia)
    out.loc[mascara_pandemia, partition_column] = "test_pandemic"
    mascara_compartilhada = out[year_column].isin(anos_compartilhados)
    usado_fallback = False
    if mascara_compartilhada.any():
        # Só as colunas necessárias ao sorteio são copiadas.
        sub = df.loc[mascara_compartilhada, colunas_estrato]
        estrato = sub[year_column].astype(str) + "|" + sub[target_column].astype(str)
        if usar_regiao:
            # astype("string") antes do fillna: regiao_residencia chega
            # categórica e fillna com categoria nova levanta TypeError.
            estrato = estrato + "|" + sub[region_column].astype("string").fillna("__NA__")
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
        del sub, estrato
        out.loc[mascara_compartilhada, partition_column] = blocos
    mascara_fora = ~(mascara_pandemia | mascara_compartilhada)
    out.loc[mascara_fora, partition_column] = "exploracao"
    if out[partition_column].isna().any():
        raise RuntimeError("Há linhas sem bloco atribuído.")
    blocos_por_grupo = (
        out[[group_column, partition_column]]
        .groupby(group_column)[partition_column]
        .nunique()
    )
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
    resumo = out[[group_column, year_column, target_column, partition_column]]
    for nome in (*MASTER_BLOCKS, "exploracao"):
        sub = resumo.loc[resumo[partition_column] == nome]
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