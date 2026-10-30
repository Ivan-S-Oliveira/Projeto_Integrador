"""
Testes para ``src.data.split.criar_particoes_agrupadas``.

Invariantes:

1. nenhum grupo em mais de uma partição;
2. proporções de linhas próximas de 70/15/15 (com tolerância);
3. mesma seed → mesma partição.

Cobrem também políticas de estratos pequenos, grupos com alvo
heterogéneo (raise/warn) e validações de parâmetros/colunas.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pytest

from src.data.split import (
    PARTICOES_CANONICAS,
    SplitWarning,
    atribuir_particao_estratificada_por_hash,
    criar_group_id,
    criar_particao_mestra,
    criar_particoes_agrupadas,
)


def test_criar_group_id_usa_notificacao_valida_e_fallback() -> None:
    df = pd.DataFrame(
        {
            "nu_notific": [" 123 456 ", None, "", pd.NA, "nan"],
            "id_registro": [10, 11, 12, 13, 14],
        },
        index=[50, 40, 30, 20, 10],
    )
    esperado = pd.Series(
        [
            "123456",
            "sem_notific:11",
            "sem_notific:12",
            "sem_notific:13",
            "sem_notific:14",
        ],
        index=df.index,
        dtype="string",
        name="group_id",
    )
    pd.testing.assert_series_equal(criar_group_id(df), esperado)


def test_criar_group_id_mesma_notificacao_mesmo_grupo() -> None:
    df = pd.DataFrame(
        {"nu_notific": ["123", " 123 ", "456"], "id_registro": [1, 2, 3]}
    )
    resultado = criar_group_id(df)
    assert resultado.iloc[0] == resultado.iloc[1]
    assert resultado.iloc[0] != resultado.iloc[2]


def test_criar_group_id_independe_do_indice_e_da_ordem() -> None:
    df = pd.DataFrame(
        {
            "id_registro": [101, 102, 103, 104],
            "nu_notific": ["900", None, "901", ""],
        },
        index=[7, 7, 99, -4],
    )
    original = dict(zip(df["id_registro"], criar_group_id(df), strict=True))
    reordenado = df.iloc[[3, 1, 0, 2]].copy()
    reordenado.index = [1000, 2000, 3000, 4000]
    novo = dict(
        zip(reordenado["id_registro"], criar_group_id(reordenado), strict=True)
    )
    assert original == novo


def test_criar_group_id_exige_id_registro_apenas_no_fallback() -> None:
    resultado = criar_group_id(pd.DataFrame({"nu_notific": ["123", "456"]}))
    assert resultado.tolist() == ["123", "456"]

    with pytest.raises(KeyError, match="id_registro"):
        criar_group_id(pd.DataFrame({"nu_notific": [None, "123"]}))


def test_criar_group_id_rejeita_id_invalido_no_fallback() -> None:
    df = pd.DataFrame({"nu_notific": [None, "123"], "id_registro": [pd.NA, 2]})
    with pytest.raises(ValueError, match="exigem fallback"):
        criar_group_id(df)


def test_criar_group_id_exige_nu_notific() -> None:
    with pytest.raises(KeyError, match="nu_notific"):
        criar_group_id(pd.DataFrame({"id_registro": [1]}))


# ---------------------------------------------------------------------------
# Fixtures sintéticas
# ---------------------------------------------------------------------------

def _df_estratificado(
    n_grupos_classe0: int = 30,
    n_grupos_classe1: int = 20,
    linhas_por_grupo: int = 3,
    seed: int = 0,
) -> pd.DataFrame:
    """DataFrame com grupos homogéneos (alvo constante por grupo)."""
    rng = np.random.default_rng(seed)
    linhas = []
    gid = 0
    for classe, n_grupos in [(0, n_grupos_classe0), (1, n_grupos_classe1)]:
        for _ in range(n_grupos):
            grupo = f"g{gid:04d}"
            gid += 1
            n = int(rng.integers(1, linhas_por_grupo + 1))
            for i in range(n):
                linhas.append({
                    "nu_notific": grupo,
                    "alvo": classe,
                    "valor": float(rng.normal()),
                    "idx_linha": i,
                })
    return pd.DataFrame(linhas)


def _df_grande(
    n_grupos_classe0: int = 700,
    n_grupos_classe1: int = 300,
) -> pd.DataFrame:
    """Base grande o suficiente para checar proporções com folga."""
    return _df_estratificado(
        n_grupos_classe0=n_grupos_classe0,
        n_grupos_classe1=n_grupos_classe1,
        linhas_por_grupo=2,
        seed=1,
    )


def _df_com_estrato_pequeno() -> pd.DataFrame:
    """1 grupo na classe 1 (estrato pequeno) + 20 grupos na classe 0."""
    return _df_estratificado(n_grupos_classe0=20, n_grupos_classe1=1)


def _df_com_grupo_heterogeneo() -> pd.DataFrame:
    """``g0000`` (classe 0) recebe uma linha com alvo=1."""
    df = _df_estratificado(n_grupos_classe0=20, n_grupos_classe1=10)
    idx = df.index[df["nu_notific"] == "g0000"][0]
    df.loc[idx, "alvo"] = 1
    return df


def _split(df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
    """``criar_particoes_agrupadas`` com os defaults dos testes."""
    params: dict[str, Any] = {
        "target_column": "alvo",
        "group_column": "nu_notific",
        "partition_column": "particao",
    }
    params.update(kwargs)
    return criar_particoes_agrupadas(df, **params)


def _assert_proporcoes(contagem: pd.Series, tol: float = 0.05) -> None:
    """Asserts de 70/15/15 sobre ``value_counts(normalize=True)``."""
    assert abs(contagem["treino"] - 0.70) < tol, contagem
    assert abs(contagem["validacao"] - 0.15) < tol, contagem
    assert abs(contagem["teste"] - 0.15) < tol, contagem


# ---------------------------------------------------------------------------
# Invariantes de partição
# ---------------------------------------------------------------------------

def test_grupos_nao_cruzam_particoes() -> None:
    """Nenhum ``nu_notific`` aparece em mais de uma partição."""
    out = _split(_df_estratificado(), seed=42)
    grupos_por_particao = out.groupby("nu_notific", observed=True)["particao"].nunique()
    assert (grupos_por_particao == 1).all(), (
        f"Grupos em mais de uma partição:\n{grupos_por_particao[grupos_por_particao > 1]}"
    )


def test_nenhuma_linha_perdida() -> None:
    df = _df_estratificado()
    out = _split(df, seed=42)
    assert len(out) == len(df)
    assert set(out["particao"].unique()) == set(PARTICOES_CANONICAS)


# ---------------------------------------------------------------------------
# Proporções 70/15/15
# ---------------------------------------------------------------------------

def test_proporcoes_linhas_proximas_de_70_15_15() -> None:
    """Grupos são atómicos; a proporção real de linhas oscila em torno do alvo."""
    out = _split(_df_grande(), seed=42)
    _assert_proporcoes(out["particao"].value_counts(normalize=True))


def test_proporcoes_grupos_proximas_de_70_15_15() -> None:
    out = _split(_df_grande(), seed=42)
    por_grupo = out.groupby("nu_notific", observed=True)["particao"].first()
    _assert_proporcoes(por_grupo.value_counts(normalize=True))


def test_estratificacao_preserva_proporcao_aproximada() -> None:
    df = _df_estratificado(n_grupos_classe0=70, n_grupos_classe1=30)
    out = _split(df, seed=42)

    prevalencia_global = df["alvo"].mean()
    for particao in PARTICOES_CANONICAS:
        sub = out[out["particao"] == particao]
        assert abs(sub["alvo"].mean() - prevalencia_global) < 0.10


# ---------------------------------------------------------------------------
# Reprodutibilidade por seed
# ---------------------------------------------------------------------------

def test_reprodutibilidade_mesma_seed() -> None:
    """Mesma seed → mesmas partições."""
    df = _df_estratificado()
    a = _split(df, seed=7)
    b = _split(df, seed=7)
    pd.testing.assert_series_equal(a["particao"], b["particao"])


def test_seeds_diferentes_produzem_splits_diferentes() -> None:
    df = _df_estratificado()
    a = _split(df, seed=1)
    b = _split(df, seed=2)
    assert not a["particao"].equals(b["particao"])


# ---------------------------------------------------------------------------
# Estratos pequenos — 4 políticas
# ---------------------------------------------------------------------------

def test_estrato_pequeno_raise_e_default() -> None:
    with pytest.raises(ValueError, match="Estrato"):
        _split(_df_com_estrato_pequeno())


def test_estrato_pequeno_warn_teste_manda_para_teste() -> None:
    df = _df_com_estrato_pequeno()
    with pytest.warns(SplitWarning, match="Destinando ao teste"):
        out = _split(df, politica_estratos_pequenos="warn_teste")

    linhas_classe1 = out[out["alvo"] == 1]
    assert (linhas_classe1["particao"] == "teste").all()
    assert len(out) == len(df)


def test_estrato_pequeno_warn_treino_manda_para_treino() -> None:
    with pytest.warns(SplitWarning, match="Destinando ao treino"):
        out = _split(_df_com_estrato_pequeno(), politica_estratos_pequenos="warn_treino")

    linhas_classe1 = out[out["alvo"] == 1]
    assert (linhas_classe1["particao"] == "treino").all()


def test_estrato_pequeno_drop_remove_linhas() -> None:
    df = _df_com_estrato_pequeno()
    with pytest.warns(SplitWarning, match="Descartando"):
        out = _split(df, politica_estratos_pequenos="drop")

    assert (out["alvo"] == 1).sum() == 0
    assert len(out) < len(df)
    assert set(out["particao"].unique()).issubset(set(PARTICOES_CANONICAS))


# ---------------------------------------------------------------------------
# Grupos com alvo heterogéneo
# ---------------------------------------------------------------------------

def test_grupo_heterogeneo_raise() -> None:
    with pytest.raises(ValueError, match="mais de um valor distinto"):
        _split(_df_com_grupo_heterogeneo())


def test_grupo_heterogeneo_warn() -> None:
    with pytest.warns(SplitWarning, match="mais de um valor distinto"):
        _split(_df_com_grupo_heterogeneo(), on_grupo_alvo_heterogeneo="warn")


# ---------------------------------------------------------------------------
# Validação de parâmetros e colunas
# ---------------------------------------------------------------------------

def test_coluna_alvo_ausente() -> None:
    with pytest.raises(KeyError, match="alvo"):
        criar_particoes_agrupadas(
            _df_estratificado(),
            target_column="nao_existe",
            group_column="nu_notific",
        )


def test_coluna_grupo_ausente() -> None:
    with pytest.raises(KeyError, match="grupo"):
        criar_particoes_agrupadas(
            _df_estratificado(),
            target_column="alvo",
            group_column="nao_existe",
        )


def test_partition_column_ja_existente() -> None:
    df = _df_estratificado()
    df["particao"] = "treino"
    with pytest.raises(ValueError, match="já contém"):
        _split(df)


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"frac_treino": 0.0}, "frac_treino"),
        ({"frac_validacao": 1.5}, "frac_validacao"),
        ({"frac_treino": 0.7, "frac_validacao": 0.4}, "< 1"),
    ],
    ids=["frac_treino_zero", "frac_validacao_acima", "soma_maior_que_1"],
)
def test_frac_invalida(kwargs: dict, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        _split(_df_estratificado(), **kwargs)


def test_min_grupos_abaixo_de_3() -> None:
    with pytest.raises(ValueError, match="min_grupos_por_estrato"):
        _split(_df_estratificado(), min_grupos_por_estrato=2)


def test_politica_invalida() -> None:
    # Valor viola intencionalmente o Literal PoliticaEstratosPequenos.
    with pytest.raises(ValueError, match="politica_estratos_pequenos"):
        _split(_df_estratificado(), politica_estratos_pequenos="qualquer_coisa")  # type: ignore[arg-type]


def test_df_vazio() -> None:
    with pytest.raises(ValueError, match="vazio"):
        _split(pd.DataFrame({"alvo": [], "nu_notific": []}))

# ---------------------------------------------------------------------------
# Partição por hash (método oficial) — #86
# ---------------------------------------------------------------------------

def _df_hash(
    estratos: dict[str, int] | None = None,
    *,
    linhas_por_grupo: int = 3,
    seed: int = 0,
) -> pd.DataFrame:
    """DataFrame com um estrato por grupo, várias linhas por grupo."""
    estratos = estratos or {"A": 30, "B": 20}
    rng = np.random.default_rng(seed)
    linhas = []
    gid = 0
    for estrato, n_grupos in estratos.items():
        for _ in range(n_grupos):
            grupo = f"g{gid:04d}"
            gid += 1
            n = int(rng.integers(1, linhas_por_grupo + 1))
            for _ in range(n):
                linhas.append({"grupo": grupo, "estrato": estrato, "valor": float(rng.normal())})
    return pd.DataFrame(linhas)


def _hash_particao(df: pd.DataFrame, *, sal: str = "s", ft: float = 0.70, fv: float = 0.15):
    return atribuir_particao_estratificada_por_hash(
        df["grupo"], df["estrato"], sal=sal, frac_treino=ft, frac_validacao=fv,
    )


def test_hash_deterministica_com_linhas_embaralhadas() -> None:
    """Mesma coorte, linhas em ordem diferente → mesma partição por grupo."""
    df = _df_hash()
    a = _hash_particao(df)
    df_shuffled = df.sample(frac=1, random_state=1).reset_index(drop=True)
    b = _hash_particao(df_shuffled)
    part_a = df.assign(p=a).groupby("grupo")["p"].first()
    part_b = df_shuffled.assign(p=b).groupby("grupo")["p"].first()
    pd.testing.assert_series_equal(part_a.sort_index(), part_b.sort_index())


def test_hash_grupos_nao_cruzam_particoes() -> None:
    df = _df_hash()
    df = df.assign(particao=_hash_particao(df))
    assert (df.groupby("grupo")["particao"].nunique() == 1).all()


def test_hash_remover_um_estrato_nao_afeta_o_outro() -> None:
    """Remover todos os grupos de um estrato não muda a partição do outro."""
    df = _df_hash({"A": 100, "B": 100}, linhas_por_grupo=1)
    part_full = df.assign(p=_hash_particao(df)).set_index("grupo")["p"]
    df_a = df[df["estrato"] == "A"].reset_index(drop=True)
    part_a = df_a.assign(p=_hash_particao(df_a)).set_index("grupo")["p"]
    for grupo in part_a.index:
        assert part_a[grupo] == part_full[grupo], grupo


def test_hash_desvio_por_estrato_pequeno() -> None:
    df = _df_hash({"A": 100, "B": 100}, linhas_por_grupo=1)
    df = df.assign(particao=_hash_particao(df))
    for estrato in ("A", "B"):
        props = df.loc[df["estrato"] == estrato, "particao"].value_counts(normalize=True)
        assert abs(props["treino"] - 0.70) < 0.03
        assert abs(props["validacao"] - 0.15) < 0.03
        assert abs(props["teste"] - 0.15) < 0.03


def test_hash_estrato_abaixo_do_minimo_levanta_erro() -> None:
    df = _df_hash({"A": 30, "B": 2})  # B tem 2 < 3
    with pytest.raises(ValueError, match="Estratos abaixo"):
        _hash_particao(df)


def test_hash_grupo_em_dois_estratos_levanta_erro() -> None:
    df = _df_hash({"A": 30, "B": 20})
    # Corrompe: põe a primeira linha de g0000 no estrato B
    idx = df.index[df["grupo"] == "g0000"][0]
    df.loc[idx, "estrato"] = "B"
    with pytest.raises(ValueError, match="mais de um estrato"):
        _hash_particao(df)


def test_hash_sal_diferente_muda_particao() -> None:
    df = _df_hash({"A": 100}, linhas_por_grupo=1)
    a = _hash_particao(df, sal="s1")
    b = _hash_particao(df, sal="s2")
    assert not (a == b).all()


def test_hash_sem_grupo_nulo_ou_estrato_nulo() -> None:
    df = _df_hash({"A": 30})
    df_bad = df.copy()
    df_bad.loc[df_bad.index[0], "grupo"] = None
    with pytest.raises(ValueError, match="valores ausentes"):
        _hash_particao(df_bad)

def _df_master(seed=0, anos=None):
    rng = np.random.default_rng(seed)
    anos = anos or [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
    linhas = []
    gid = 0
    for ano in anos:
        for _ in range(100):  # 100 grupos por ano
            g = f"g{gid:04d}"; gid += 1
            alvo = int(rng.integers(0, 2))
            regiao = rng.choice(["N", "SE", "S"])
            for _ in range(int(rng.integers(1, 4))):
                linhas.append({
                    "group_id": g, "ano_internacao": ano,
                    "alvo_obito_srag": alvo, "regiao_residencia": regiao,
                })
    return pd.DataFrame(linhas)


TEMPORAL_CFG = {
    "seed": 42,
    "min_grupos_por_estrato": 5,
    "coluna_particao": "particao",
    "blocos": {
        "train_ref":     {"anos": [2019, 2023, 2024, 2025], "fracao": 0.70},
        "val_tune":      {"anos": [2019, 2023, 2024, 2025], "fracao": 0.05},
        "val_cal":       {"anos": [2019, 2023, 2024, 2025], "fracao": 0.05},
        "val_meas":      {"anos": [2019, 2023, 2024, 2025], "fracao": 0.05},
        "test_ref":      {"anos": [2019, 2023, 2024, 2025], "fracao": 0.15},
        "test_pandemic": {"anos": [2020, 2021, 2022]},
    },
}


def test_particao_mestra_pandemia_isolada():
    out, m = criar_particao_mestra(_df_master(), temporal_cfg=TEMPORAL_CFG)
    assert set(out.loc[out.ano_internacao.isin([2020, 2021, 2022]), "particao"]) == {"test_pandemic"}
    assert set(out.loc[out.ano_internacao.isin([2019, 2023, 2024, 2025]), "particao"]) <= {
        "train_ref", "val_tune", "val_cal", "val_meas", "test_ref",
    }


def test_particao_mestra_disjuncao_por_grupo():
    out, _ = criar_particao_mestra(_df_master(), temporal_cfg=TEMPORAL_CFG)
    assert (out.groupby("group_id")["particao"].nunique() == 1).all()


def test_particao_mestra_2026_marcado_exploracao():
    out, m = criar_particao_mestra(_df_master(), temporal_cfg=TEMPORAL_CFG)
    assert set(out.loc[out.ano_internacao == 2026, "particao"]) == {"exploracao"}
    assert m["blocos"]["exploracao"]["n_linhas"] > 0


def test_particao_mestra_manifesto_tem_hash_por_bloco():
    _, m = criar_particao_mestra(_df_master(), temporal_cfg=TEMPORAL_CFG)
    for nome in ("train_ref", "val_tune", "val_cal", "val_meas", "test_ref", "test_pandemic"):
        assert m["blocos"][nome]["n_linhas"] > 0
        assert m["blocos"][nome]["hash_bloco"]


def test_particao_mestra_aceita_regiao_categorica():
    """regiao_residencia chega categórica de montar_features (#142)."""
    df = _df_master()
    df["regiao_residencia"] = df["regiao_residencia"].astype("category")
    out, m = criar_particao_mestra(df, temporal_cfg=TEMPORAL_CFG)
    referencia, m_ref = criar_particao_mestra(_df_master(), temporal_cfg=TEMPORAL_CFG)
    assert m["estratificacao"] == m_ref["estratificacao"]
    assert out["particao"].tolist() == referencia["particao"].tolist()
