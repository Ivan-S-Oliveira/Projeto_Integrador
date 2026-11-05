"""Artefato supervisionado e bloqueio do teste."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import pandas as pd
import pytest
from src.dados import BLOCKS_PADRAO_LEITURA, DATASET_NAME, MANIFEST_NAME, GatePendenteError, holdout_partition, load_supervised_artifact, persist_supervised_artifact, split_partitions


_DATASET_REL = Path("data") / "analytical" / DATASET_NAME


_MANIFEST_REL = Path("data") / "analytical" / MANIFEST_NAME


def _frame_blocos() -> pd.DataFrame:
    """8 registos: 2 em train_ref, 1 em cada val_*, 1 em test_ref, 2 em test_pandemic."""
    return pd.DataFrame({
        "idade_anos":      [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0],
        "alvo_obito_srag": [0, 1, 0, 1, 0, 1, 0, 1],
        "bloco_mestre": [
            "train_ref", "train_ref",
            "val_ref", "val_ref", "val_ref",
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


def _params_persistencia(**overrides: Any) -> dict[str, Any]:
    """Kwargs base de ``persist_supervised_artifact``; ``overrides`` sobrepõe."""
    base: dict[str, Any] = {
        "source":           {},
        "feature_columns":  ["idade_anos"],
        "target_column":    "alvo_obito_srag",
        "partition_column": "bloco_mestre",
        "cohort_kind":      "final",
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


def _caminho_dataset(tmp_path: Path) -> Path:
    return tmp_path / _DATASET_REL


def _caminho_manifesto(tmp_path: Path) -> Path:
    return tmp_path / _MANIFEST_REL


def _rehash_manifesto(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mantém o hash do manifesto válido depois de adulterar o parquet."""
    manifest_hash = json.loads(
        _caminho_manifesto(tmp_path).read_text(encoding="utf-8")
    )["dataset_sha256"]
    monkeypatch.setattr(
        "src.dados.sha256_file",
        lambda _path: manifest_hash,
    )


@pytest.fixture
def g9_aprovado(monkeypatch: pytest.MonkeyPatch) -> None:
    """``exigir_gate`` aceita qualquer gate."""
    monkeypatch.setattr("src.config.gate_aprovado", lambda _nome: True)


@pytest.fixture
def g9_pendente(monkeypatch: pytest.MonkeyPatch) -> None:
    """``exigir_gate`` rejeita qualquer gate."""
    monkeypatch.setattr("src.config.gate_aprovado", lambda _nome: False)


@pytest.fixture
def exploracao_inativa(monkeypatch: pytest.MonkeyPatch) -> None:
    """``temporal.exploracao_2026.ativa`` responde ``False``."""
    original = __import__("src.config", fromlist=["cfg"]).cfg

    def _cfg(*args: Any, **kwargs: Any) -> Any:
        if args[:3] == ("temporal", "exploracao_2026", "ativa"):
            return False
        return original(*args, **kwargs)

    monkeypatch.setattr("src.config.cfg", _cfg)


def test_default_nao_carrega_teste(tmp_path: Path) -> None:
    """Sem ``partitions``, o loader devolve só ``train_ref`` e ``val_ref``."""
    _persistir_blocos(tmp_path, _frame_blocos(), source={"kind": "final", "sha256": "abc"})
    loaded, manifest = load_supervised_artifact(tmp_path, expected_kind="final")
    assert set(loaded["bloco_mestre"]) == set(BLOCKS_PADRAO_LEITURA)
    assert manifest["test_opened"] is False
    assert manifest["seed"] == 42


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
            "train_ref", "val_ref",
            "test_ref", "test_pandemic",
        ),
    )

    assert set(loaded["bloco_mestre"]) == {
        "train_ref", "val_ref",
        "test_ref", "test_pandemic",
    }
    assert len(loaded) == len(frame)


def test_tipo_de_coorte_incorreto_falha(tmp_path: Path) -> None:
    """``expected_kind`` divergente falha antes de tocar nos dados."""
    _persistir_blocos(tmp_path, _frame_blocos(), cohort_kind="outra")
    with pytest.raises(RuntimeError, match="SRAG_COHORT_KIND"):
        load_supervised_artifact(tmp_path, expected_kind="final")


def test_holdout_partition_sem_g9_falha(
    tmp_path: Path,
    g9_pendente: None,
) -> None:
    """``holdout_partition`` revalida o gate verificação extra."""
    _persistir_blocos(tmp_path, _frame_blocos())
    loaded, manifest = load_supervised_artifact(tmp_path)
    with pytest.raises(GatePendenteError, match="G9_holdout"):
        holdout_partition(loaded, manifest)


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
            "train_ref", "val_ref",
            "test_ref", "test_pandemic",
        ),
    )

    teste = holdout_partition(loaded, manifest)

    assert set(teste["bloco_mestre"]) == {"test_ref", "test_pandemic"}


def test_exploracao_sem_gate_ativo_falha(
    tmp_path: Path,
    exploracao_inativa: None,
) -> None:
    """``exploracao`` pedida com ``temporal.exploracao_2026.ativa=false`` levanta erro."""
    _persistir_blocos(tmp_path, _frame_blocos_com_exploracao())

    with pytest.raises(RuntimeError, match="exploracao.*ativa"):
        load_supervised_artifact(tmp_path, partitions=("exploracao",))


def test_load_com_columns_valida_alvo_binario(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Artefato com alvo inválido falha mesmo com ``columns=`` (que exclui o alvo)."""
    _persistir_blocos(tmp_path, _frame_blocos())
    dataset_path = _caminho_dataset(tmp_path)
    frame = pd.read_parquet(dataset_path)
    frame.loc[frame.index[0], "alvo_obito_srag"] = 5
    frame.to_parquet(dataset_path, index=False)
    _rehash_manifesto(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="binário"):
        load_supervised_artifact(tmp_path, columns=["idade_anos"])


def test_split_partitions_agrega_blocos(
    tmp_path: Path,
    g9_aprovado: None,
) -> None:
    """No esquema novo, ``split_partitions`` agrega ``val_*`` em ``validacao``."""
    _persistir_blocos(tmp_path, _frame_blocos())
    loaded, manifest = load_supervised_artifact(
        tmp_path,
        partitions=(
            "train_ref", "val_ref",
            "test_ref", "test_pandemic",
        ),
    )

    treino, validacao = split_partitions(loaded, manifest)

    assert set(treino["bloco_mestre"]) == {"train_ref"}
    assert set(validacao["bloco_mestre"]) == {
        "val_ref",
    }
    assert len(treino) == 2
    assert len(validacao) == 3


def test_gerar_artefato_supervisionado_ponta_a_ponta_sintetico(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercita a orquestração central sem acessar a coorte populacional."""
    from src.dados import CohortSource
    from src import dados as sa
    from src.config import sha256_file

    n_base = 42
    ids = list(range(1, n_base + 1))

    anos = (
        [2019] * 30
        + [2020] * 6
        + [2026] * 6
    )

    base = pd.DataFrame(
        {
            "id_registro": ids,
            "nu_notific": [f"{valor:012d}" for valor in ids],
            "sg_uf": ["SP", "BA", "DF", "RS", "AM", "XX"] * 7,
            "nu_idade_n": [20 + valor % 70 for valor in ids],
            "tp_idade": [3] * n_base,
            "cs_sexo": ["M", "F", "I"] * 14,
            "dt_sin_pri": [
                f"{ano}-01-01"
                for ano in anos
            ],
            "dt_interna": [
                f"{ano}-01-05"
                for ano in anos
            ],
            "evolucao": [
                1 if valor % 2 == 0 else 2
                for valor in ids
            ],
            "fator_risc": ["1", "2", None] * 14,
            "vacina": ["1", "2", "9"] * 14,
            "saturacao": ["1", "2", None] * 14,
        }
    )

    conflito = base.iloc[[0]].copy()
    conflito["id_registro"] = 10_001
    conflito["dt_sin_pri"] = "2023-01-01"
    conflito["dt_interna"] = "2023-01-05"

    frame_sintetico = pd.concat(
        [base, conflito],
        ignore_index=True,
    )

    source = CohortSource(
        kind="final",
        path=str(
            tmp_path
            / "data"
            / "analytical"
            / "coorte_final.parquet"
        ),
        sha256="hash-coorte-sintetica",
        size_bytes=1234,
        rows=len(frame_sintetico),
        columns=frame_sintetico.shape[1],
    )

    temporal_cfg = {
        "seed": 42,
        "coluna_particao": "particao",
        "min_grupos_por_estrato": 5,
        "blocos": {
            "train_ref": {
                "anos": [2019, 2023, 2024, 2025],
                "fracao": 0.70,
            },
            "val_ref": {
                "anos": [2019, 2023, 2024, 2025],
                "fracao": 0.15,
            },
            "test_ref": {
                "anos": [2019, 2023, 2024, 2025],
                "fracao": 0.15,
            },
            "test_pandemic": {
                "anos": [2020, 2021, 2022],
            },
        },
    }

    config_sintetica = {
        "seed": 42,
        "target": {
            "coluna": "evolucao",
            "coluna_modelagem": "alvo_obito_srag",
            "positivos": [2],
            "negativos": [1],
            "descartar_outros": True,
        },
        "features": {
            "final": [
                "idade_anos",
                "sexo_categoria",
            ],
            "numericas": [
                "idade_anos",
            ],
            "categoricas": [
                "sexo_categoria",
            ],
            "engenharia": {
                "entradas": [
                    "nu_idade_n",
                    "tp_idade",
                    "cs_sexo",
                    "dt_sin_pri",
                    "dt_interna",
                ],
                "derivadas": [
                    "idade_anos",
                    "sexo_categoria",
                ],
            },
            "contexto_incremental": ["vacina", "sg_uf"],
            "sensibilidade_gravidade_admissao": ["saturacao"],
        },
        "temporal": temporal_cfg,
    }

    artefato_cfg = {
        "config": config_sintetica,
        "features_cfg": config_sintetica["features"],
        "feature_columns": [
            "idade_anos",
            "sexo_categoria",
        ],
        "numeric_columns": [
            "idade_anos",
        ],
        "categorical_columns": [
            "sexo_categoria",
        ],
        "target_cfg": config_sintetica["target"],
        "target_column": "alvo_obito_srag",
        "source_target_column": "evolucao",
        "temporal_cfg": temporal_cfg,
        "partition_column": "particao",
        "seed": 42,
    }

    def fake_load_cohort(
        root: Path,
        *,
        kind: str,
        columns: list[str] | None = None,
        **_kwargs: Any,
    ) -> tuple[pd.DataFrame, CohortSource]:
        assert root == tmp_path.resolve()
        assert kind == "final"

        if columns is None:
            selected = frame_sintetico.copy()
        else:
            selected = frame_sintetico.loc[:, columns].copy()

        return selected, source

    def fake_criar_particao_mestra(
        frame: pd.DataFrame,
        *,
        temporal_cfg: dict[str, Any],
        group_column: str,
        year_column: str,
        target_column: str,
        region_column: str | None,
        partition_column: str,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        assert temporal_cfg == artefato_cfg["temporal_cfg"]
        assert group_column == "group_id"
        assert year_column == "ano_internacao"
        assert target_column == "alvo_obito_srag"
        assert region_column == "regiao_residencia"

        out = frame.copy()
        out[partition_column] = "exploracao"

        pandemic_mask = out[year_column].isin([2020, 2021, 2022])
        out.loc[pandemic_mask, partition_column] = "test_pandemic"

        shared_mask = out[year_column].isin(
            [2019, 2023, 2024, 2025]
        )
        shared_blocks = [
            "train_ref",
            "val_ref",
            "test_ref",
        ]

        shared_index = out.index[shared_mask]
        assignment = [
            shared_blocks[position % len(shared_blocks)]
            for position in range(len(shared_index))
        ]
        out.loc[shared_index, partition_column] = assignment

        blocks_manifest = {}
        for block in [
            "train_ref",
            "val_ref",
            "test_ref",
            "test_pandemic",
            "exploracao",
        ]:
            subset = out.loc[out[partition_column].eq(block)]
            blocks_manifest[block] = {
                "n_linhas": int(len(subset)),
                "n_grupos": int(
                    subset[group_column].nunique()
                ),
            }

        return out, {
            "metodo": "particao_sintetica_deterministica",
            "seed": 42,
            "partition_column": partition_column,
            "blocos": blocks_manifest,
        }

    monkeypatch.setattr(
        sa,
        "_configuracao_artefato",
        lambda: artefato_cfg,
    )
    monkeypatch.setattr(
        sa,
        "load_cohort",
        fake_load_cohort,
    )
    monkeypatch.setattr(
        sa,
        "criar_particao_mestra",
        fake_criar_particao_mestra,
    )
    monkeypatch.setattr(
        sa.C,
        "supervised_yaml_sha256",
        lambda: "hash-configuracao-sintetica",
    )

    resultado = sa.gerar_artefato_supervisionado(
        tmp_path,
        cohort_kind="final",
        exportar_particao=True,
        overwrite=False,
    )

    analytical = tmp_path / "data" / "analytical"
    dataset_path = analytical / DATASET_NAME
    manifest_path = analytical / MANIFEST_NAME
    partition_path = analytical / "partitions_master.parquet"
    partition_manifest_path = (
        analytical / "manifesto_particao.json"
    )

    assert dataset_path.is_file()
    assert manifest_path.is_file()
    assert partition_path.is_file()
    assert partition_manifest_path.is_file()

    dataset = pd.read_parquet(dataset_path)
    partitions = pd.read_parquet(partition_path)

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )
    partition_manifest = json.loads(
        partition_manifest_path.read_text(encoding="utf-8")
    )

    assert {
        "id_registro",
        "group_id",
        "regiao_residencia",
        "alvo_obito_srag",
        "particao",
    }.issubset(dataset.columns)

    assert {
        "id_registro",
        "group_id",
        "ano_internacao",
        "alvo_obito_srag",
        "particao",
        "bloco_mestre",
        "regiao_residencia",
    }.issubset(partitions.columns)
    assert (
        partitions["bloco_mestre"].astype(str)
        == partitions["particao"].astype(str)
    ).all()

    for coluna in ("fator_risc", "vacina", "saturacao", "sg_uf"):
        assert coluna in dataset.columns
        assert coluna in manifest["audit_columns"]
        assert coluna not in manifest["feature_columns"]
    assert set(resultado["prevalence_by_partition"]) == set(
        resultado["partition_counts"]
    )
    assert resultado["rows_exploracao"] == 6
    assert len(manifest["audit_columns"]) == len(set(manifest["audit_columns"]))

    assert manifest["cohort_kind"] == "final"
    assert manifest["test_opened"] is False
    assert manifest["dataset_sha256"] == sha256_file(dataset_path)

    assert (
        partition_manifest["partition_sha256"]
        == sha256_file(partition_path)
    )

    assert resultado["cohort_kind"] == "final"
    assert resultado["test_opened"] is False
    assert resultado["rows_loaded"] == len(frame_sintetico)
    assert resultado["rows_quarantined"] == 2
    assert resultado["groups_quarantined"] == 1
    assert resultado["rows_modelable"] == 35

    assert not any(
        isinstance(value, pd.DataFrame)
        for value in resultado.values()
    )

    group_block_counts = (
        partitions.groupby("group_id", observed=True)["particao"]
        .nunique()
    )
    assert int((group_block_counts > 1).sum()) == 0

    conflict_group = base.loc[0, "nu_notific"]
    assert conflict_group not in set(partitions["group_id"])

    assert set(dataset["particao"]) == {
        "train_ref",
        "val_ref",
        "test_ref",
        "test_pandemic",
    }

    assert "exploracao" not in set(dataset["particao"])
    assert "exploracao" in set(partitions["particao"])

    with pytest.raises(FileExistsError):
        sa.gerar_artefato_supervisionado(
            tmp_path,
            cohort_kind="final",
            exportar_particao=True,
            overwrite=False,
        )
