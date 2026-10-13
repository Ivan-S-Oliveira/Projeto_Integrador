"""
Testes para `src.data.split.criar_particoes_agrupadas`.

Invariantes centrais:
    1. nenhum grupo aparece em mais de uma partição (group integrity);
    2. proporções de linhas próximas de 70/15/15 (com tolerância);
    3. mesma seed → mesma partição (reprodutibilidade).

Cobrem ainda:
    - partição completa e bem-distribuída;
    - as quatro políticas de estratos pequenos;
    - grupo com alvo heterogêneo (raise e warn);
    - validações de parâmetros e colunas.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data.split import (
    PARTICOES_CANONICAS,
    SplitWarning,
    criar_particoes_agrupadas,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _df_estratificado(
    n_grupos_classe0: int = 30,
    n_grupos_classe1: int = 20,
    linhas_por_grupo: int = 3,
    seed: int = 0,
) -> pd.DataFrame:
    """
    Cria um DataFrame com grupos homogêneos (alvo constante por grupo)
    e duas classes bem representadas.
    """
    rng = np.random.default_rng(seed)
    linhas = []
    gid = 0
    for classe, n_grupos in [(0, n_grupos_classe0), (1, n_grupos_classe1)]:
        for _ in range(n_grupos):
            grupo = f"g{gid:04d}"
            gid += 1
            n = int(rng.integers(1, linhas_por_grupo + 1))
            for i in range(n):
                linhas.append(
                    {
                        "nu_notific": grupo,
                        "alvo": classe,
                        "valor": float(rng.normal()),
                        "idx_linha": i,
                    }
                )
    return pd.DataFrame(linhas)


def _df_grande(n_grupos_classe0: int = 700, n_grupos_classe1: int = 300) -> pd.DataFrame:
    """Base grande o bastante para checar proporções com folga."""
    return _df_estratificado(
        n_grupos_classe0=n_grupos_classe0,
        n_grupos_classe1=n_grupos_classe1,
        linhas_por_grupo=2,
        seed=1,
    )


# ---------------------------------------------------------------------------
# Invariante 1 — nenhum grupo em duas partições
# ---------------------------------------------------------------------------

def test_grupos_nao_cruzam_particoes():
    df = _df_estratificado()
    out = criar_particoes_agrupadas(
        df,
        target_column="alvo",
        group_column="nu_notific",
        partition_column="particao",
        seed=42,
    )

    grupos_por_particao = (
        out.groupby("nu_notific", observed=True)["particao"].nunique()
    )
    assert (grupos_por_particao == 1).all(), (
        "Algum grupo aparece em mais de uma partição:\n"
        f"{grupos_por_particao[grupos_por_particao > 1]}"
    )


def test_nenhuma_linha_perdida():
    df = _df_estratificado()
    out = criar_particoes_agrupadas(
        df,
        target_column="alvo",
        group_column="nu_notific",
        partition_column="particao",
        seed=42,
    )
    assert len(out) == len(df)
    assert set(out["particao"].unique()) == set(PARTICOES_CANONICAS)


# ---------------------------------------------------------------------------
# Invariante 2 — proporções 70/15/15
# ---------------------------------------------------------------------------

def test_proporcoes_linhas_proximas_de_70_15_15():
    df = _df_grande()
    out = criar_particoes_agrupadas(
        df,
        target_column="alvo",
        group_column="nu_notific",
        partition_column="particao",
        seed=42,
    )

    contagem = out["particao"].value_counts(normalize=True)
    # Tolerância generosa: grupos são atômicos, então a proporção real
    # de linhas oscila em torno do alvo.
    tol = 0.05

    assert abs(contagem["treino"] - 0.70) < tol, contagem
    assert abs(contagem["validacao"] - 0.15) < tol, contagem
    assert abs(contagem["teste"] - 0.15) < tol, contagem


def test_proporcoes_grupos_proximas_de_70_15_15():
    df = _df_grande()
    out = criar_particoes_agrupadas(
        df,
        target_column="alvo",
        group_column="nu_notific",
        partition_column="particao",
        seed=42,
    )

    por_grupo = (
        out.groupby("nu_notific", observed=True)["particao"].first()
    )
    contagem = por_grupo.value_counts(normalize=True)
    tol = 0.05

    assert abs(contagem["treino"] - 0.70) < tol, contagem
    assert abs(contagem["validacao"] - 0.15) < tol, contagem
    assert abs(contagem["teste"] - 0.15) < tol, contagem


def test_estratificacao_preserva_proporcao_aproximada():
    df = _df_estratificado(n_grupos_classe0=70, n_grupos_classe1=30)
    out = criar_particoes_agrupadas(
        df, target_column="alvo", group_column="nu_notific",
        partition_column="particao", seed=42,
    )
    prevalencia_global = df["alvo"].mean()
    for particao in PARTICOES_CANONICAS:
        sub = out[out["particao"] == particao]
        # tolerância generosa: 10 pontos percentuais
        assert abs(sub["alvo"].mean() - prevalencia_global) < 0.10


# ---------------------------------------------------------------------------
# Invariante 3 — reprodutibilidade por seed
# ---------------------------------------------------------------------------

def test_reprodutibilidade_mesma_seed():
    df = _df_estratificado()
    a = criar_particoes_agrupadas(
        df, target_column="alvo", group_column="nu_notific",
        partition_column="particao", seed=7,
    )
    b = criar_particoes_agrupadas(
        df, target_column="alvo", group_column="nu_notific",
        partition_column="particao", seed=7,
    )
    pd.testing.assert_series_equal(a["particao"], b["particao"])


def test_seeds_diferentes_produzem_splits_diferentes():
    df = _df_estratificado()
    a = criar_particoes_agrupadas(
        df, target_column="alvo", group_column="nu_notific",
        partition_column="particao", seed=1,
    )
    b = criar_particoes_agrupadas(
        df, target_column="alvo", group_column="nu_notific",
        partition_column="particao", seed=2,
    )
    assert not a["particao"].equals(b["particao"])


# ---------------------------------------------------------------------------
# Estratos pequenos
# ---------------------------------------------------------------------------

def _df_com_estrato_pequeno() -> pd.DataFrame:
    """1 grupo na classe 1 (estrato pequeno) + 20 grupos na classe 0."""
    return _df_estratificado(n_grupos_classe0=20, n_grupos_classe1=1)


def test_estrato_pequeno_raise_e_default():
    df = _df_com_estrato_pequeno()
    with pytest.raises(ValueError, match="Estrato"):
        criar_particoes_agrupadas(
            df, target_column="alvo", group_column="nu_notific",
            partition_column="particao",
        )


def test_estrato_pequeno_warn_teste_manda_para_teste():
    df = _df_com_estrato_pequeno()
    with pytest.warns(SplitWarning, match="Destinando ao teste"):
        out = criar_particoes_agrupadas(
            df, target_column="alvo", group_column="nu_notific",
            partition_column="particao",
            politica_estratos_pequenos="warn_teste",
        )
    linhas_classe1 = out[out["alvo"] == 1]
    assert (linhas_classe1["particao"] == "teste").all()
    assert len(out) == len(df)


def test_estrato_pequeno_warn_treino_manda_para_treino():
    df = _df_com_estrato_pequeno()
    with pytest.warns(SplitWarning, match="Destinando ao treino"):
        out = criar_particoes_agrupadas(
            df, target_column="alvo", group_column="nu_notific",
            partition_column="particao",
            politica_estratos_pequenos="warn_treino",
        )
    linhas_classe1 = out[out["alvo"] == 1]
    assert (linhas_classe1["particao"] == "treino").all()


def test_estrato_pequeno_drop_remove_linhas():
    df = _df_com_estrato_pequeno()
    with pytest.warns(SplitWarning, match="Descartando"):
        out = criar_particoes_agrupadas(
            df, target_column="alvo", group_column="nu_notific",
            partition_column="particao",
            politica_estratos_pequenos="drop",
        )
    assert (out["alvo"] == 1).sum() == 0
    assert len(out) < len(df)
    assert set(out["particao"].unique()).issubset(set(PARTICOES_CANONICAS))


# ---------------------------------------------------------------------------
# Grupo com alvo heterogêneo
# ---------------------------------------------------------------------------

def _df_com_grupo_heterogeneo() -> pd.DataFrame:
    df = _df_estratificado(n_grupos_classe0=20, n_grupos_classe1=10)
    idx = df.index[df["nu_notific"] == "g0000"][0]
    df.loc[idx, "alvo"] = 1
    return df


def test_grupo_heterogeneo_raise():
    df = _df_com_grupo_heterogeneo()
    with pytest.raises(ValueError, match="mais de um valor distinto"):
        criar_particoes_agrupadas(
            df, target_column="alvo", group_column="nu_notific",
            partition_column="particao",
        )


def test_grupo_heterogeneo_warn():
    df = _df_com_grupo_heterogeneo()
    with pytest.warns(SplitWarning, match="mais de um valor distinto"):
        criar_particoes_agrupadas(
            df, target_column="alvo", group_column="nu_notific",
            partition_column="particao",
            on_grupo_alvo_heterogeneo="warn",
        )


# ---------------------------------------------------------------------------
# Validações de parâmetros
# ---------------------------------------------------------------------------

def test_coluna_alvo_ausente():
    df = _df_estratificado()
    with pytest.raises(KeyError, match="alvo"):
        criar_particoes_agrupadas(
            df, target_column="nao_existe", group_column="nu_notific",
        )


def test_coluna_grupo_ausente():
    df = _df_estratificado()
    with pytest.raises(KeyError, match="grupo"):
        criar_particoes_agrupadas(
            df, target_column="alvo", group_column="nao_existe",
        )


def test_partition_column_ja_existente():
    df = _df_estratificado()
    df["particao"] = "treino"
    with pytest.raises(ValueError, match="já contém"):
        criar_particoes_agrupadas(
            df, target_column="alvo", group_column="nu_notific",
            partition_column="particao",
        )


def test_frac_invalida():
    df = _df_estratificado()
    with pytest.raises(ValueError, match="frac_treino"):
        criar_particoes_agrupadas(
            df, target_column="alvo", group_column="nu_notific",
            frac_treino=0.0,
        )
    with pytest.raises(ValueError, match="frac_validacao"):
        criar_particoes_agrupadas(
            df, target_column="alvo", group_column="nu_notific",
            frac_validacao=1.5,
        )
    with pytest.raises(ValueError, match="< 1"):
        criar_particoes_agrupadas(
            df, target_column="alvo", group_column="nu_notific",
            frac_treino=0.7, frac_validacao=0.4,
        )


def test_min_grupos_abaixo_de_3():
    df = _df_estratificado()
    with pytest.raises(ValueError, match="min_grupos_por_estrato"):
        criar_particoes_agrupadas(
            df, target_column="alvo", group_column="nu_notific",
            min_grupos_por_estrato=2,
        )


def test_politica_invalida():
    df = _df_estratificado()
    with pytest.raises(ValueError, match="politica_estratos_pequenos"):
        criar_particoes_agrupadas(
            df, target_column="alvo", group_column="nu_notific",
            politica_estratos_pequenos="qualquer_coisa",  # type: ignore[arg-type]
        )


def test_df_vazio():
    df = pd.DataFrame({"alvo": [], "nu_notific": []})
    with pytest.raises(ValueError, match="vazio"):
        criar_particoes_agrupadas(
            df, target_column="alvo", group_column="nu_notific",
        )