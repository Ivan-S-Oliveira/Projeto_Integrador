"""Testes do registro de execuções (``src.utils.reproducibility``)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.utils import config as C
from src.utils import reproducibility as R


# Campos que ``registrar_execucao`` deve sempre gravar no metadata.
# Serve como armadilha contra remoções silenciosas na estrutura do dict.
_CAMPOS_METADATA: tuple[str, ...] = (
    "run_id", "timestamp", "modelo", "seed", "status",
    "parametros", "dataset", "metricas", "features",
    "duracao_s", "erro", "data_version", "gates", "versoes",
    "git", "env", "notas", "dataset_sha256", "supervised_yaml_sha256",
)


def _ler_meta(pasta: Path) -> dict[str, Any]:
    """Lê ``metadata.json`` de uma execução."""
    return json.loads((pasta / "metadata.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# registrar_execucao — estrutura e conteúdo
# ---------------------------------------------------------------------------

def test_registrar_execucao_cria_pasta(tmp_path: Path) -> None:
    pasta = R.registrar_execucao(
        modelo="teste",
        seed=42,
        parametros={"C": 1.0},
        dataset={"nome": "srag", "n_rows": 100},
        metricas={"auc": 0.5},
        duracao_s=1.23,
        output_dir=tmp_path,
    )
    assert pasta.exists()
    assert (pasta / "metadata.json").exists()
    assert (pasta / "summary.txt").exists()


def test_metadata_tem_campos_obrigatorios(tmp_path: Path) -> None:
    pasta = R.registrar_execucao(
        modelo="teste",
        seed=7,
        parametros={"x": 1},
        metricas={"auc": 0.9},
        output_dir=tmp_path,
    )
    meta = _ler_meta(pasta)

    for chave in _CAMPOS_METADATA:
        assert chave in meta

    assert meta["seed"] == 7
    assert meta["modelo"] == "teste"
    assert meta["metricas"]["auc"] == 0.9


def test_metadata_grava_data_version(tmp_path: Path) -> None:
    pasta = R.registrar_execucao(modelo="dv", output_dir=tmp_path)
    assert _ler_meta(pasta)["data_version"] == C.DATA_VERSION


def test_metadata_grava_gates(tmp_path: Path) -> None:
    meta = _ler_meta(R.registrar_execucao(modelo="gates", output_dir=tmp_path))
    assert isinstance(meta["gates"], dict)
    assert "G9_holdout" in meta["gates"]


def test_seed_padrao_vem_do_config(tmp_path: Path) -> None:
    """Sem ``seed`` explícito, usa ``config.SEED``."""
    pasta = R.registrar_execucao(modelo="seed_default", output_dir=tmp_path)
    assert _ler_meta(pasta)["seed"] == C.SEED


# ---------------------------------------------------------------------------
# Run como context manager
# ---------------------------------------------------------------------------

def test_run_context_manager_sucesso(tmp_path: Path) -> None:
    r: R.Run | None = None
    with R.Run(modelo="ctx", seed=1, output_dir=tmp_path) as r:
        r.metrica(auc=0.77)
        r.anotar("nota de teste")

    assert r is not None
    assert r.pasta is not None
    meta = _ler_meta(r.pasta)
    assert meta["metricas"]["auc"] == 0.77
    assert "nota de teste" in meta["notas"]
    assert meta["duracao_s"] is not None
    assert meta["status"] == "success"
    assert meta["erro"] is None


def test_run_registra_excecao(tmp_path: Path) -> None:
    """Mesmo em exceção, o metadata é gravado — com status e erro."""
    r: R.Run | None = None
    with pytest.raises(RuntimeError, match="boom"):
        with R.Run(modelo="erro", output_dir=tmp_path) as r:
            raise RuntimeError("boom")

    assert r is not None
    assert r.pasta is not None
    meta = _ler_meta(r.pasta)
    assert meta["status"] == "error"
    assert meta["erro"]["tipo"] == "RuntimeError"
    assert "boom" in meta["erro"]["mensagem"]
    assert "Traceback" in meta["erro"]["traceback"]


def test_run_nao_suprime_excecao(tmp_path: Path) -> None:
    """O ``__exit__`` devolve ``False`` — a exceção propaga."""
    with pytest.raises(ValueError):
        with R.Run(modelo="propaga", output_dir=tmp_path):
            raise ValueError("propaga")


# ---------------------------------------------------------------------------
# gerar_run_id
# ---------------------------------------------------------------------------

def test_run_id_unico(tmp_path: Path) -> None:
    """Sufixo ``_NN`` evita colisão quando o ID base já existe."""
    a = R.gerar_run_id(modelo="dup", base_dir=tmp_path)
    (tmp_path / a).mkdir()
    b = R.gerar_run_id(modelo="dup", base_dir=tmp_path)
    assert a != b


# ---------------------------------------------------------------------------
# listar_runs / carregar_run
# ---------------------------------------------------------------------------

def test_listar_e_carregar(tmp_path: Path) -> None:
    R.registrar_execucao(modelo="a", output_dir=tmp_path)
    R.registrar_execucao(modelo="b", output_dir=tmp_path)

    runs = R.listar_runs(output_dir=tmp_path)
    assert len(runs) == 2

    meta = R.carregar_run(runs[0]["run_id"], output_dir=tmp_path)
    assert meta["modelo"] in {"a", "b"}