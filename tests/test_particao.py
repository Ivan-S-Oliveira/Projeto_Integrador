"""Grupo e partição-mestre."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.dados import PARTICOES_CANONICAS, criar_group_id, criar_particao_mestra


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


def test_criar_group_id_exige_nu_notific() -> None:
    with pytest.raises(KeyError, match="nu_notific"):
        criar_group_id(pd.DataFrame({"id_registro": [1]}))


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
        "val_ref":      {"anos": [2019, 2023, 2024, 2025], "fracao": 0.15},
        "test_ref":      {"anos": [2019, 2023, 2024, 2025], "fracao": 0.15},
        "test_pandemic": {"anos": [2020, 2021, 2022]},
    },
}


def test_particao_mestra_pandemia_isolada():
    out, m = criar_particao_mestra(_df_master(), temporal_cfg=TEMPORAL_CFG)
    assert set(out.loc[out.ano_internacao.isin([2020, 2021, 2022]), "particao"]) == {"test_pandemic"}
    assert set(out.loc[out.ano_internacao.isin([2019, 2023, 2024, 2025]), "particao"]) <= {
        "train_ref", "val_ref", "test_ref",
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
    for nome in ("train_ref", "val_ref", "test_ref", "test_pandemic"):
        assert m["blocos"][nome]["n_linhas"] > 0
        assert m["blocos"][nome]["hash_bloco"]


def test_particao_mestra_aceita_regiao_categorica():
    """regiao_residencia chega categórica de montar_features."""
    df = _df_master()
    df["regiao_residencia"] = df["regiao_residencia"].astype("category")
    out, m = criar_particao_mestra(df, temporal_cfg=TEMPORAL_CFG)
    referencia, m_ref = criar_particao_mestra(_df_master(), temporal_cfg=TEMPORAL_CFG)
    assert m["estratificacao"] == m_ref["estratificacao"]
    assert out["particao"].tolist() == referencia["particao"].tolist()
