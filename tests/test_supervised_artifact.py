"""Testes do artefato supervisionado (``src.data.supervised_artifact``).

Cobrem persistência, leitura, validação do tipo de coorte, exigência das
três partições na gravação e a trava do gate ``G9_holdout`` sobre a
partição de teste na leitura (#16).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.data.supervised_artifact import (
    GatePendenteError,
    holdout_partition,
    load_supervised_artifact,
    persist_supervised_artifact,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _frame() -> pd.DataFrame:
    """6 registos — 2 por partição, alvo alternado (0/1)."""
    return pd.DataFrame({
        "idade_anos":      [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "alvo_obito_srag": [0, 1, 0, 1, 0, 1],
        "particao":        ["treino", "treino", "validacao", "validacao", "teste", "teste"],
    })


def _persistir(tmp_path: Path, frame: pd.DataFrame, **kwargs: Any) -> None:
    """Grava ``frame`` com kwargs obrigatórios mínimos; ``**kwargs`` sobrepõe."""
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


@pytest.fixture
def g9_aprovado(monkeypatch: pytest.MonkeyPatch) -> None:
    """``exigir_gate`` aceita qualquer gate (G9 aprovado)."""
    monkeypatch.setattr("src.utils.config.gate_aprovado", lambda _nome: True)


@pytest.fixture
def g9_pendente(monkeypatch: pytest.MonkeyPatch) -> None:
    """``exigir_gate`` rejeita qualquer gate (G9 pendente)."""
    monkeypatch.setattr("src.utils.config.gate_aprovado", lambda _nome: False)


# ---------------------------------------------------------------------------
# Persistência
# ---------------------------------------------------------------------------

def test_persistencia_exige_tres_particoes(tmp_path: Path) -> None:
    """Gravar sem ``teste`` viola o contrato de partições."""
    with pytest.raises(ValueError, match="Particoes esperadas"):
        _persistir(tmp_path, _frame().query("particao != 'teste'"))


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

def test_default_nao_carrega_teste(tmp_path: Path) -> None:
    """Por omissão, o loader devolve apenas treino+validação."""
    _persistir(tmp_path, _frame(), source={"kind": "provisional", "sha256": "abc"})

    loaded, manifest = load_supervised_artifact(tmp_path, expected_kind="provisional")

    assert set(loaded["particao"]) == {"treino", "validacao"}
    assert manifest["test_opened"] is False
    assert manifest["seed"] == 42


def test_roundtrip_completo_apos_g9(tmp_path: Path, g9_aprovado: None) -> None:
    """Com G9 aprovado e ``partitions`` explícito, o teste entra no round-trip."""
    frame = _frame()
    _persistir(tmp_path, frame)

    loaded, _ = load_supervised_artifact(
        tmp_path, partitions=("treino", "validacao", "teste"),
    )

    assert loaded["particao"].tolist() == frame["particao"].tolist()


# ---------------------------------------------------------------------------
# Tipo de coorte
# ---------------------------------------------------------------------------

def test_tipo_de_coorte_incorreto_falha(tmp_path: Path) -> None:
    """``expected_kind`` divergente falha antes de tocar nos dados."""
    _persistir(tmp_path, _frame())

    with pytest.raises(RuntimeError, match="SRAG_COHORT_KIND"):
        load_supervised_artifact(tmp_path, expected_kind="final")


# ---------------------------------------------------------------------------
# Trava do gate G9 (#16)
# ---------------------------------------------------------------------------

def test_default_funciona_com_g9_pendente(tmp_path: Path, g9_pendente: None) -> None:
    """Sem ``teste`` na seleção, o loader não consulta o gate."""
    _persistir(tmp_path, _frame())

    loaded, _ = load_supervised_artifact(tmp_path)

    assert set(loaded["particao"]) == {"treino", "validacao"}


def test_load_com_teste_sem_g9_falha(tmp_path: Path, g9_pendente: None) -> None:
    """Pedir ``teste`` sem G9 aprovado levanta antes de materializar o bloco."""
    _persistir(tmp_path, _frame())

    with pytest.raises(GatePendenteError, match="G9_holdout"):
        load_supervised_artifact(
            tmp_path, partitions=("treino", "validacao", "teste"),
        )


def test_holdout_partition_sem_g9_falha(tmp_path: Path, g9_pendente: None) -> None:
    """``holdout_partition`` revalida o gate (defesa em profundidade)."""
    _persistir(tmp_path, _frame())
    loaded, manifest = load_supervised_artifact(tmp_path)

    with pytest.raises(GatePendenteError, match="G9_holdout"):
        holdout_partition(loaded, manifest)


def test_holdout_partition_apos_g9(tmp_path: Path, g9_aprovado: None) -> None:
    """Com G9 aprovado, ``holdout_partition`` devolve o bloco de teste."""
    _persistir(tmp_path, _frame())
    loaded, manifest = load_supervised_artifact(
        tmp_path, partitions=("treino", "validacao", "teste"),
    )

    teste = holdout_partition(loaded, manifest)

    assert set(teste["particao"]) == {"teste"}
    assert len(teste) == 2


# ---------------------------------------------------------------------------
# Validação de ``partitions``
# ---------------------------------------------------------------------------

def test_partitions_vazias_falham(tmp_path: Path) -> None:
    _persistir(tmp_path, _frame())

    with pytest.raises(ValueError, match="partitions.*vazio"):
        load_supervised_artifact(tmp_path, partitions=())


def test_partitions_desconhecidas_falham(tmp_path: Path) -> None:
    _persistir(tmp_path, _frame())

    with pytest.raises(ValueError, match="Particoes desconhecidas"):
        load_supervised_artifact(tmp_path, partitions=("treino", "foo"))

# ---------------------------------------------------------------------------
# ``columns=`` não pula a validação (#18)
# ---------------------------------------------------------------------------

def test_load_com_columns_devolve_apenas_o_pedido(tmp_path: Path) -> None:
    """``columns=["idade_anos"]`` devolve só essa coluna; alvo/partição saem."""
    _persistir(tmp_path, _frame())
    loaded, _ = load_supervised_artifact(tmp_path, columns=["idade_anos"])
    assert list(loaded.columns) == ["idade_anos"]
    assert not loaded.empty


def test_load_com_columns_preserva_colunas_pedidas(tmp_path: Path) -> None:
    """Se o chamador pedir alvo/partição, elas continuam no retorno."""
    _persistir(tmp_path, _frame())
    loaded, _ = load_supervised_artifact(
        tmp_path, columns=["idade_anos", "alvo_obito_srag", "particao"],
    )
    assert {"idade_anos", "alvo_obito_srag", "particao"} <= set(loaded.columns)


def test_load_com_columns_valida_alvo_binario(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Artefato com alvo inválido falha mesmo com ``columns=`` (que exclui o alvo)."""
    _persistir(tmp_path, _frame())

    dataset_path = tmp_path / "data" / "analytical" / "dataset_supervisionado.parquet"
    frame = pd.read_parquet(dataset_path)
    frame.loc[frame.index[0], "alvo_obito_srag"] = 5
    frame.to_parquet(dataset_path, index=False)

    manifest_hash = json.loads(
        (dataset_path.parent / "manifesto_supervisionado.json").read_text(encoding="utf-8")
    )["dataset_sha256"]
    monkeypatch.setattr(
        "src.data.supervised_artifact.sha256_file", lambda _p: manifest_hash,
    )

    with pytest.raises(ValueError, match="binario"):
        load_supervised_artifact(tmp_path, columns=["idade_anos"])


def test_load_com_columns_valida_particoes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Partição desaparecida do parquet é detectada mesmo com ``columns=``."""
    _persistir(tmp_path, _frame())

    dataset_path = tmp_path / "data" / "analytical" / "dataset_supervisionado.parquet"
    frame = pd.read_parquet(dataset_path)
    frame.loc[frame["particao"] == "validacao", "particao"] = "treino"
    frame.to_parquet(dataset_path, index=False)

    manifest_hash = json.loads(
        (dataset_path.parent / "manifesto_supervisionado.json").read_text(encoding="utf-8")
    )["dataset_sha256"]
    monkeypatch.setattr(
        "src.data.supervised_artifact.sha256_file", lambda _p: manifest_hash,
    )

    with pytest.raises(ValueError, match="Particoes esperadas"):
        load_supervised_artifact(tmp_path, columns=["idade_anos"])