from pathlib import Path

import pandas as pd
import pytest

from src.data.supervised_artifact import (
    load_supervised_artifact,
    persist_supervised_artifact,
)


def _frame():
    return pd.DataFrame(
        {
            "idade_anos": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
            "alvo_obito_srag": [0, 1, 0, 1, 0, 1],
            "particao": ["treino", "treino", "validacao", "validacao", "teste", "teste"],
        }
    )


def test_roundtrip_preserva_particao(tmp_path):
    persist_supervised_artifact(
        _frame(),
        root=tmp_path,
        source={"kind": "provisional", "sha256": "abc"},
        feature_columns=["idade_anos"],
        target_column="alvo_obito_srag",
        partition_column="particao",
        cohort_kind="provisional",
        seed=42,
    )
    loaded, manifest = load_supervised_artifact(tmp_path, expected_kind="provisional")
    assert loaded["particao"].tolist() == _frame()["particao"].tolist()
    assert manifest["test_opened"] is False
    assert manifest["seed"] == 42


def test_tipo_de_coorte_incorreto_falha(tmp_path):
    persist_supervised_artifact(
        _frame(), root=tmp_path, source={}, feature_columns=["idade_anos"],
        target_column="alvo_obito_srag", partition_column="particao",
        cohort_kind="provisional", seed=42,
    )
    with pytest.raises(RuntimeError, match="SRAG_COHORT_KIND"):
        load_supervised_artifact(tmp_path, expected_kind="final")


def test_particoes_incompletas_falham(tmp_path):
    frame = _frame().query("particao != 'teste'")
    with pytest.raises(ValueError, match="Particoes esperadas"):
        persist_supervised_artifact(
            frame, root=tmp_path, source={}, feature_columns=["idade_anos"],
            target_column="alvo_obito_srag", partition_column="particao",
            cohort_kind="provisional", seed=42,
        )
