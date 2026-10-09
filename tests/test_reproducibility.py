"""Testes do registro de execuções."""

from __future__ import annotations

import json

import pytest

from src.utils import reproducibility as R


# ---------------------------------------------------------------------------
# Registrar execução
# ---------------------------------------------------------------------------

def test_registrar_execucao_cria_pasta(tmp_path):
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


def test_metadata_tem_campos_obrigatorios(tmp_path):
    pasta = R.registrar_execucao(
        modelo="teste",
        seed=7,
        parametros={"x": 1},
        metricas={"auc": 0.9},
        output_dir=tmp_path,
    )
    meta = json.loads((pasta / "metadata.json").read_text(encoding="utf-8"))

    for chave in ("run_id", "timestamp", "modelo", "seed",
                  "parametros", "dataset", "metricas",
                  "versoes", "git", "env", "duracao_s",
                  "status", "data_version", "gates"):
        assert chave in meta

    assert meta["seed"] == 7
    assert meta["modelo"] == "teste"
    assert meta["metricas"]["auc"] == 0.9


def test_metadata_grava_data_version(tmp_path):
    from src.utils import config as C

    pasta = R.registrar_execucao(modelo="dv", output_dir=tmp_path)
    meta = json.loads((pasta / "metadata.json").read_text(encoding="utf-8"))
    assert meta["data_version"] == C.DATA_VERSION


def test_metadata_grava_gates(tmp_path):
    pasta = R.registrar_execucao(modelo="gates", output_dir=tmp_path)
    meta = json.loads((pasta / "metadata.json").read_text(encoding="utf-8"))
    assert isinstance(meta["gates"], dict)
    assert "G7_limiar" in meta["gates"]


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

def test_run_context_manager_sucesso(tmp_path):
    r = None
    with R.Run(modelo="ctx", seed=1, output_dir=tmp_path) as r:
        r.metrica(auc=0.77)
        r.anotar("nota de teste")

    assert r is not None
    assert r.pasta is not None
    meta = json.loads((r.pasta / "metadata.json").read_text(encoding="utf-8"))
    assert meta["metricas"]["auc"] == 0.77
    assert "nota de teste" in meta["notas"]
    assert meta["duracao_s"] is not None
    assert meta["status"] == "success"
    assert meta["erro"] is None


def test_run_registra_excecao(tmp_path):
    """Mesmo em exceção, o metadata é gravado — com status e erro."""
    r = None
    with pytest.raises(RuntimeError, match="boom"):
        with R.Run(modelo="erro", output_dir=tmp_path) as r:
            raise RuntimeError("boom")

    assert r is not None
    assert r.pasta is not None
    meta = json.loads((r.pasta / "metadata.json").read_text(encoding="utf-8"))
    assert meta["status"] == "error"
    assert meta["erro"]["tipo"] == "RuntimeError"
    assert "boom" in meta["erro"]["mensagem"]
    assert "Traceback" in meta["erro"]["traceback"]


def test_run_nao_suprime_excecao(tmp_path):
    """O __exit__ retorna False — a exceção propaga."""
    with pytest.raises(ValueError):
        with R.Run(modelo="propaga", output_dir=tmp_path):
            raise ValueError("propaga")


# ---------------------------------------------------------------------------
# run_id / listar / carregar
# ---------------------------------------------------------------------------

def test_run_id_unico(tmp_path):
    a = R.gerar_run_id(modelo="dup", base_dir=tmp_path)
    (tmp_path / a).mkdir()
    b = R.gerar_run_id(modelo="dup", base_dir=tmp_path)
    assert a != b


def test_listar_e_carregar(tmp_path):
    R.registrar_execucao(modelo="a", output_dir=tmp_path)
    R.registrar_execucao(modelo="b", output_dir=tmp_path)

    runs = R.listar_runs(output_dir=tmp_path)
    assert len(runs) == 2

    meta = R.carregar_run(runs[0]["run_id"], output_dir=tmp_path)
    assert meta["modelo"] in {"a", "b"}


def test_seed_padrao_vem_do_config(tmp_path):
    from src.utils import config as C

    pasta = R.registrar_execucao(modelo="seed_default", output_dir=tmp_path)
    meta = json.loads((pasta / "metadata.json").read_text(encoding="utf-8"))
    assert meta["seed"] == C.SEED