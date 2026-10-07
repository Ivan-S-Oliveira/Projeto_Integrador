"""Testes do registro de execuções."""

import json
from pathlib import Path

import pytest

from src.utils import reproducibility as R


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
                  "versoes", "git", "env", "duracao_s"):
        assert chave in meta

    assert meta["seed"] == 7
    assert meta["modelo"] == "teste"
    assert meta["metricas"]["auc"] == 0.9


def test_run_context_manager(tmp_path):
    with R.Run(modelo="ctx", seed=1, output_dir=tmp_path) as r:
        r.metrica(auc=0.77)
        r.anotar("nota de teste")

    assert r.pasta is not None
    meta = json.loads((r.pasta / "metadata.json").read_text(encoding="utf-8"))
    assert meta["metricas"]["auc"] == 0.77
    assert "nota de teste" in meta["notas"]
    assert meta["duracao_s"] is not None


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