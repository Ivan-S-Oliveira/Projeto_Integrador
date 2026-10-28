"""Testes do artefato supervisionado (``src.data.supervised_artifact``).

Cobrem os dois esquemas suportados:

- **legado**: ``treino``, ``validacao``, ``teste`` (artefato provisório);
- **blocos**: ``train_ref``, ``val_tune``, ``val_cal``, ``val_meas``,
  ``test_ref``, ``test_pandemic`` (+ ``exploracao`` opcional).

Além do gate ``G9_holdout`` sobre **qualquer** partição de teste,
verificam a validação da leitura parcial (``columns=``) e a agregação
feita por ``split_partitions`` / ``holdout_partition``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.data.supervised_artifact import (
    BLOCKS_PADRAO_LEITURA,
    DATASET_NAME,
    MANIFEST_NAME,
    GatePendenteError,
    holdout_partition,
    load_supervised_artifact,
    persist_supervised_artifact,
    split_partitions,
)


# ---------------------------------------------------------------------------
# Caminhos canônicos (usados em vários testes)
# ---------------------------------------------------------------------------

_DATASET_REL = Path("data") / "analytical" / DATASET_NAME
_MANIFEST_REL = Path("data") / "analytical" / MANIFEST_NAME


# ---------------------------------------------------------------------------
# Frames de exemplo
# ---------------------------------------------------------------------------

def _frame_legado() -> pd.DataFrame:
    """6 registos: 2 por partição do esquema legado, alvo alternado."""
    return pd.DataFrame({
        "idade_anos":      [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "alvo_obito_srag": [0, 1, 0, 1, 0, 1],
        "particao": [
            "treino", "treino",
            "validacao", "validacao",
            "teste", "teste",
        ],
    })


def _frame_blocos() -> pd.DataFrame:
    """8 registos: 2 em train_ref, 1 em cada val_*, 1 em test_ref, 2 em test_pandemic."""
    return pd.DataFrame({
        "idade_anos":      [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0],
        "alvo_obito_srag": [0, 1, 0, 1, 0, 1, 0, 1],
        "bloco_mestre": [
            "train_ref", "train_ref",
            "val_tune", "val_cal", "val_meas",
            "test_ref",
            "test_pandemic", "test_pandemic",
        ],
    })


def _frame_blocos_com_exploracao() -> pd.DataFrame:
    """``_frame_blocos`` + 1 linha em ``exploracao`` (2026)."""
    base = _frame_blocos()
    extra = pd.DataFrame({
        "idade_anos":      [90.0],
        "alvo_obito_srag": [0],
        "bloco_mestre":    ["exploracao"],
    })
    return pd.concat([base, extra], ignore_index=True)


# ---------------------------------------------------------------------------
# Helpers de persistência
# ---------------------------------------------------------------------------

def _params_persistencia(**overrides: Any) -> dict[str, Any]:
    """Kwargs base de ``persist_supervised_artifact``; ``overrides`` sobrepõe."""
    base: dict[str, Any] = {
        "source":           {},
        "feature_columns":  ["idade_anos"],
        "target_column":    "alvo_obito_srag",
        "partition_column": "particao",
        "cohort_kind":      "provisional",
        "seed":             42,
    }
    base.update(overrides)
    return base


def _persistir(tmp_path: Path, frame: pd.DataFrame, **overrides: Any) -> None:
    persist_supervised_artifact(
        frame,
        root=tmp_path,
        **_params_persistencia(**overrides),
    )


def _persistir_blocos(
    tmp_path: Path,
    frame: pd.DataFrame,
    **overrides: Any,
) -> None:
    """Atalho: grava com ``partition_column="bloco_mestre"`` e ``cohort_kind="final"``."""
    overrides.setdefault("partition_column", "bloco_mestre")
    overrides.setdefault("cohort_kind", "final")
    _persistir(tmp_path, frame, **overrides)


# ---------------------------------------------------------------------------
# Helpers de inspeção e adulteração controlada
# ---------------------------------------------------------------------------

def _caminho_dataset(tmp_path: Path) -> Path:
    return tmp_path / _DATASET_REL


def _caminho_manifesto(tmp_path: Path) -> Path:
    return tmp_path / _MANIFEST_REL


def _rehash_manifesto(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mantém o hash do manifesto válido depois de adulterar o parquet.

    Útil para testar a validação da leitura parcial, que não deve ser
    mascarada pela checagem de SHA-256.
    """
    manifest_hash = json.loads(
        _caminho_manifesto(tmp_path).read_text(encoding="utf-8")
    )["dataset_sha256"]
    monkeypatch.setattr(
        "src.data.supervised_artifact.sha256_file",
        lambda _path: manifest_hash,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def g9_aprovado(monkeypatch: pytest.MonkeyPatch) -> None:
    """``exigir_gate`` aceita qualquer gate."""
    monkeypatch.setattr("src.utils.config.gate_aprovado", lambda _nome: True)


@pytest.fixture
def g9_pendente(monkeypatch: pytest.MonkeyPatch) -> None:
    """``exigir_gate`` rejeita qualquer gate."""
    monkeypatch.setattr("src.utils.config.gate_aprovado", lambda _nome: False)


@pytest.fixture
def exploracao_ativa(monkeypatch: pytest.MonkeyPatch) -> None:
    """``temporal.exploracao_2026.ativa`` responde ``True``."""
    original = __import__("src.utils.config", fromlist=["cfg"]).cfg

    def _cfg(*args: Any, **kwargs: Any) -> Any:
        if args[:3] == ("temporal", "exploracao_2026", "ativa"):
            return True
        return original(*args, **kwargs)

    monkeypatch.setattr("src.utils.config.cfg", _cfg)


@pytest.fixture
def exploracao_inativa(monkeypatch: pytest.MonkeyPatch) -> None:
    """``temporal.exploracao_2026.ativa`` responde ``False``."""
    original = __import__("src.utils.config", fromlist=["cfg"]).cfg

    def _cfg(*args: Any, **kwargs: Any) -> Any:
        if args[:3] == ("temporal", "exploracao_2026", "ativa"):
            return False
        return original(*args, **kwargs)

    monkeypatch.setattr("src.utils.config.cfg", _cfg)


# ===========================================================================
# Persistência — contrato de partições
# ===========================================================================

def test_persistencia_legado_exige_tres_particoes(tmp_path: Path) -> None:
    """Sem ``teste``, o esquema legado é incompleto."""
    with pytest.raises(ValueError, match="Partições incompletas"):
        _persistir(tmp_path, _frame_legado().query("particao != 'teste'"))


def test_persistencia_blocos_exige_seis_blocos(tmp_path: Path) -> None:
    """Sem ``test_pandemic``, o esquema de blocos é incompleto."""
    frame = _frame_blocos().query("bloco_mestre != 'test_pandemic'")
    with pytest.raises(ValueError, match="Partições incompletas"):
        _persistir_blocos(tmp_path, frame)


def test_persistencia_mistura_de_esquemas_falha(tmp_path: Path) -> None:
    """Um frame com ``treino`` e ``train_ref`` é rejeitado explicitamente."""
    frame = _frame_legado().rename(columns={"particao": "bloco_mestre"}).copy()
    frame.loc[0, "bloco_mestre"] = "train_ref"
    with pytest.raises(ValueError, match="misturou esquemas"):
        _persistir_blocos(tmp_path, frame)


# ===========================================================================
# Round-trip — esquema legado
# ===========================================================================

def test_default_legado_nao_carrega_teste(tmp_path: Path) -> None:
    """Sem ``partitions``, o loader devolve só treino+validação."""
    _persistir(tmp_path, _frame_legado(), source={"kind": "provisional", "sha256": "abc"})

    loaded, manifest = load_supervised_artifact(tmp_path, expected_kind="provisional")

    assert set(loaded["particao"]) == {"treino", "validacao"}
    assert manifest["test_opened"] is False
    assert manifest["seed"] == 42


def test_roundtrip_legado_completo_apos_g9(
    tmp_path: Path,
    g9_aprovado: None,
) -> None:
    """Com G9 aprovado e ``partitions`` explícito, o teste entra no round-trip."""
    frame = _frame_legado()
    _persistir(tmp_path, frame)

    loaded, _ = load_supervised_artifact(
        tmp_path, partitions=("treino", "validacao", "teste"),
    )

    assert set(loaded["particao"]) == {"treino", "validacao", "teste"}
    assert len(loaded) == len(frame)


# ===========================================================================
# Round-trip — esquema de blocos
# ===========================================================================

def test_default_blocos_le_apenas_desenvolvimento(
    tmp_path: Path,
    g9_pendente: None,
) -> None:
    """Sem ``partitions`` em artefato de blocos, o default é ``BLOCKS_PADRAO_LEITURA``."""
    _persistir_blocos(tmp_path, _frame_blocos())

    loaded, _ = load_supervised_artifact(tmp_path)

    assert set(loaded["bloco_mestre"]) == set(BLOCKS_PADRAO_LEITURA)


def test_roundtrip_blocos_completo_apos_g9(
    tmp_path: Path,
    g9_aprovado: None,
) -> None:
    """Com G9 aprovado e todos os blocos pedidos, o round-trip devolve tudo."""
    frame = _frame_blocos()
    _persistir_blocos(tmp_path, frame)

    loaded, _ = load_supervised_artifact(
        tmp_path,
        partitions=(
            "train_ref", "val_tune", "val_cal", "val_meas",
            "test_ref", "test_pandemic",
        ),
    )

    assert set(loaded["bloco_mestre"]) == {
        "train_ref", "val_tune", "val_cal", "val_meas",
        "test_ref", "test_pandemic",
    }
    assert len(loaded) == len(frame)


def test_manifesto_registra_partition_schema(tmp_path: Path) -> None:
    """O manifesto grava ``partition_schema`` coerente com o esquema gravado."""
    _persistir(tmp_path, _frame_legado())
    manifesto_legado = json.loads(
        _caminho_manifesto(tmp_path).read_text(encoding="utf-8")
    )
    assert manifesto_legado["partition_schema"] == "legado"

    tmp_blocos = tmp_path / "blocos"
    _persistir_blocos(tmp_blocos, _frame_blocos())
    manifesto_blocos = json.loads(
        _caminho_manifesto(tmp_blocos).read_text(encoding="utf-8")
    )
    assert manifesto_blocos["partition_schema"] == "blocos"


# ===========================================================================
# Tipo de coorte
# ===========================================================================

def test_tipo_de_coorte_incorreto_falha(tmp_path: Path) -> None:
    """``expected_kind`` divergente falha antes de tocar nos dados."""
    _persistir(tmp_path, _frame_legado())

    with pytest.raises(RuntimeError, match="SRAG_COHORT_KIND"):
        load_supervised_artifact(tmp_path, expected_kind="final")


# ===========================================================================
# Gate G9 — esquema legado
# ===========================================================================

def test_default_funciona_com_g9_pendente(
    tmp_path: Path,
    g9_pendente: None,
) -> None:
    """Sem ``teste`` na seleção, o loader não consulta o gate."""
    _persistir(tmp_path, _frame_legado())

    loaded, _ = load_supervised_artifact(tmp_path)

    assert set(loaded["particao"]) == {"treino", "validacao"}


def test_load_com_teste_sem_g9_falha(
    tmp_path: Path,
    g9_pendente: None,
) -> None:
    """Pedir ``teste`` sem G9 aprovado levanta antes de materializar o bloco."""
    _persistir(tmp_path, _frame_legado())

    with pytest.raises(GatePendenteError, match="G9_holdout"):
        load_supervised_artifact(
            tmp_path, partitions=("treino", "validacao", "teste"),
        )


def test_holdout_partition_sem_g9_falha(
    tmp_path: Path,
    g9_pendente: None,
) -> None:
    """``holdout_partition`` revalida o gate (defesa em profundidade)."""
    _persistir(tmp_path, _frame_legado())
    loaded, manifest = load_supervised_artifact(tmp_path)

    with pytest.raises(GatePendenteError, match="G9_holdout"):
        holdout_partition(loaded, manifest)


def test_holdout_partition_apos_g9(
    tmp_path: Path,
    g9_aprovado: None,
) -> None:
    """Com G9 aprovado, ``holdout_partition`` devolve o bloco de teste."""
    _persistir(tmp_path, _frame_legado())
    loaded, manifest = load_supervised_artifact(
        tmp_path, partitions=("treino", "validacao", "teste"),
    )

    teste = holdout_partition(loaded, manifest)

    assert set(teste["particao"]) == {"teste"}
    assert len(teste) == 2


# ===========================================================================
# Gate G9 — esquema de blocos
# ===========================================================================

@pytest.mark.parametrize("bloco_teste", ["test_ref", "test_pandemic"])
def test_load_bloco_de_teste_sem_g9_falha(
    tmp_path: Path,
    g9_pendente: None,
    bloco_teste: str,
) -> None:
    """``test_ref`` e ``test_pandemic`` exigem G9 aprovado."""
    _persistir_blocos(tmp_path, _frame_blocos())

    with pytest.raises(GatePendenteError, match="G9_holdout"):
        load_supervised_artifact(tmp_path, partitions=(bloco_teste,))


def test_holdout_partition_blocos_apos_g9(
    tmp_path: Path,
    g9_aprovado: None,
) -> None:
    """``holdout_partition`` agrega ``test_ref + test_pandemic`` no esquema novo."""
    _persistir_blocos(tmp_path, _frame_blocos())
    loaded, manifest = load_supervised_artifact(
        tmp_path,
        partitions=(
            "train_ref", "val_tune", "val_cal", "val_meas",
            "test_ref", "test_pandemic",
        ),
    )

    teste = holdout_partition(loaded, manifest)

    assert set(teste["bloco_mestre"]) == {"test_ref", "test_pandemic"}


# ===========================================================================
# Exploração 2026
# ===========================================================================

def test_exploracao_sem_gate_ativo_falha(
    tmp_path: Path,
    exploracao_inativa: None,
) -> None:
    """``exploracao`` pedida com ``temporal.exploracao_2026.ativa=false`` levanta erro."""
    _persistir_blocos(tmp_path, _frame_blocos_com_exploracao())

    with pytest.raises(RuntimeError, match="exploracao.*ativa"):
        load_supervised_artifact(tmp_path, partitions=("exploracao",))


def test_exploracao_liberada_quando_ativa(
    tmp_path: Path,
    exploracao_ativa: None,
) -> None:
    """Com a flag ativa, ``exploracao`` é devolvida."""
    _persistir_blocos(tmp_path, _frame_blocos_com_exploracao())

    loaded, _ = load_supervised_artifact(tmp_path, partitions=("exploracao",))

    assert set(loaded["bloco_mestre"]) == {"exploracao"}
    assert len(loaded) == 1


# ===========================================================================
# Validação de ``partitions``
# ===========================================================================

def test_partitions_vazias_falham(tmp_path: Path) -> None:
    _persistir(tmp_path, _frame_legado())

    with pytest.raises(ValueError, match="partitions.*vazio"):
        load_supervised_artifact(tmp_path, partitions=())


def test_partitions_desconhecidas_falham(tmp_path: Path) -> None:
    _persistir(tmp_path, _frame_legado())

    with pytest.raises(ValueError, match="Partições desconhecidas"):
        load_supervised_artifact(tmp_path, partitions=("treino", "foo"))


def test_particao_solicitada_ausente_no_artefato_falha(tmp_path: Path) -> None:
    """Pedir um bloco que não existe no artefato falha antes do parquet."""
    _persistir(tmp_path, _frame_legado())

    with pytest.raises(ValueError, match="não existem no artefato"):
        load_supervised_artifact(tmp_path, partitions=("train_ref",))


# ===========================================================================
# ``columns=`` não pula a validação (#18)
# ===========================================================================

def test_load_com_columns_devolve_apenas_o_pedido(tmp_path: Path) -> None:
    """``columns=["idade_anos"]`` devolve só essa coluna; alvo/partição saem."""
    _persistir(tmp_path, _frame_legado())
    loaded, _ = load_supervised_artifact(tmp_path, columns=["idade_anos"])

    assert list(loaded.columns) == ["idade_anos"]
    assert not loaded.empty


def test_load_com_columns_preserva_colunas_pedidas(tmp_path: Path) -> None:
    """Se o chamador pedir alvo/partição, elas continuam no retorno."""
    _persistir(tmp_path, _frame_legado())
    loaded, _ = load_supervised_artifact(
        tmp_path, columns=["idade_anos", "alvo_obito_srag", "particao"],
    )

    assert {"idade_anos", "alvo_obito_srag", "particao"} <= set(loaded.columns)


def test_load_com_columns_valida_alvo_binario(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Artefato com alvo inválido falha mesmo com ``columns=`` (que exclui o alvo)."""
    _persistir(tmp_path, _frame_legado())

    dataset_path = _caminho_dataset(tmp_path)
    frame = pd.read_parquet(dataset_path)
    frame.loc[frame.index[0], "alvo_obito_srag"] = 5
    frame.to_parquet(dataset_path, index=False)
    _rehash_manifesto(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match="binário"):
        load_supervised_artifact(tmp_path, columns=["idade_anos"])


def test_load_com_columns_valida_particoes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Partição desaparecida do parquet é detectada mesmo com ``columns=``."""
    _persistir(tmp_path, _frame_legado())

    dataset_path = _caminho_dataset(tmp_path)
    frame = pd.read_parquet(dataset_path)
    frame.loc[frame["particao"] == "validacao", "particao"] = "treino"
    frame.to_parquet(dataset_path, index=False)
    _rehash_manifesto(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match="Partições esperadas"):
        load_supervised_artifact(tmp_path, columns=["idade_anos"])


# ===========================================================================
# split_partitions — agregação por papel
# ===========================================================================

def test_split_partitions_legado(tmp_path: Path) -> None:
    """No esquema legado, ``split_partitions`` devolve treino/validação literais."""
    _persistir(tmp_path, _frame_legado())
    loaded, manifest = load_supervised_artifact(tmp_path)

    treino, validacao = split_partitions(loaded, manifest)

    assert set(treino["particao"]) == {"treino"}
    assert set(validacao["particao"]) == {"validacao"}
    assert len(treino) == 2
    assert len(validacao) == 2


def test_split_partitions_agrega_blocos(
    tmp_path: Path,
    g9_aprovado: None,
) -> None:
    """No esquema novo, ``split_partitions`` agrega ``val_*`` em ``validacao``."""
    _persistir_blocos(tmp_path, _frame_blocos())
    loaded, manifest = load_supervised_artifact(
        tmp_path,
        partitions=(
            "train_ref", "val_tune", "val_cal", "val_meas",
            "test_ref", "test_pandemic",
        ),
    )

    treino, validacao = split_partitions(loaded, manifest)

    assert set(treino["bloco_mestre"]) == {"train_ref"}
    assert set(validacao["bloco_mestre"]) == {
        "val_tune", "val_cal", "val_meas",
    }
    assert len(treino) == 2
    assert len(validacao) == 3