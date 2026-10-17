"""Testes do artefacto supervisionado (``src.data.supervised_artifact``).

Cobrem o contrato de persistência/leitura: preservação da partição,
validação do tipo de coorte e exigência das três partições.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.data.supervised_artifact import (
    load_supervised_artifact,
    persist_supervised_artifact,
)


def _frame() -> pd.DataFrame:
    """6 registos — 2 por partição, alvo alternado (0/1).

    Colunas mínimas para os testes: uma feature numérica, o alvo binário
    e a coluna de partição.
    """
    return pd.DataFrame({
        "idade_anos":      [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "alvo_obito_srag": [0, 1, 0, 1, 0, 1],
        "particao":        ["treino", "treino", "validacao", "validacao", "teste", "teste"],
    })


def _persistir(tmp_path: Path, frame: pd.DataFrame, **kwargs: Any) -> None:
    """Grava ``frame`` como artefacto supervisionado em ``tmp_path``.

    Preenche os kwargs obrigatórios com valores mínimos e deixa
    ``**kwargs`` sobrepor (ex.: ``source`` com conteúdo).
    """
    params: dict[str, Any] = {
        "source":           {},
        "feature_columns":  ["idade_anos"],
        "target_column":    "alvo_obito_srag",
        "partition_column": "particao",
        "cohort_kind":      "provisional",
        "seed":             42,
    }
    params.update(kwargs)
    persist_supervised_artifact(frame, root=tmp_path, **params)


# ---------------------------------------------------------------------------
# Contrato de round-trip
# ---------------------------------------------------------------------------

def test_roundtrip_preserva_particao(tmp_path: Path) -> None:
    """Gravar e ler preserva a partição, e o manifesto regista o estado inicial."""
    frame = _frame()
    _persistir(tmp_path, frame, source={"kind": "provisional", "sha256": "abc"})

    loaded, manifest = load_supervised_artifact(tmp_path, expected_kind="provisional")

    assert loaded["particao"].tolist() == frame["particao"].tolist()
    assert manifest["test_opened"] is False
    assert manifest["seed"] == 42


# ---------------------------------------------------------------------------
# Validações
# ---------------------------------------------------------------------------

def test_tipo_de_coorte_incorreto_falha(tmp_path: Path) -> None:
    """Ler com ``expected_kind`` diferente do gravado deve falhar."""
    _persistir(tmp_path, _frame())

    with pytest.raises(RuntimeError, match="SRAG_COHORT_KIND"):
        load_supervised_artifact(tmp_path, expected_kind="final")


def test_particoes_incompletas_falham(tmp_path: Path) -> None:
    """Dataset sem o bloco ``teste`` viola o contrato de partições."""
    frame = _frame().query("particao != 'teste'")

    with pytest.raises(ValueError, match="Particoes esperadas"):
        _persistir(tmp_path, frame)