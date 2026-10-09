"""Testes de geração dos datasets analíticos (src/data/analitico.py)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.data.analitico import (
    ARQUIVO_CLUSTERING,
    ARQUIVO_MANIFESTO,
    ARQUIVO_SUPERVISIONADO,
    COLUNA_ID,
    carregar_coorte_provisoria,
    gerar_datasets,
)
from src.evaluation.leakage import LeakageError
from src.utils import config as C


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def coorte_sintetica() -> pd.DataFrame:
    """Coorte pequena com todas as colunas exigidas pela derivação."""
    n = 60
    rng = np.random.default_rng(42)
    return pd.DataFrame(
        {
            "nu_idade_n": rng.integers(0, 90, size=n).astype("float64"),
            "tp_idade": np.full(n, 3.0),
            "dt_sin_pri": pd.date_range("2023-01-01", periods=n, freq="7D"),
            "dt_interna": pd.date_range("2023-01-03", periods=n, freq="7D"),
            "dt_notific": pd.date_range("2023-01-02", periods=n, freq="7D"),
            "evolucao": rng.choice([1.0, 2.0], size=n),
            "sg_uf": rng.choice(["SP", "RJ", "MG"], size=n),
            "cs_sexo": rng.choice(["M", "F"], size=n),
            "cs_gestant": rng.choice(
                np.array([pd.NA, "1", "2"], dtype=object), size=n
            ),
            "febre": rng.choice(["0", "1"], size=n),
            "tosse": rng.choice(["0", "1"], size=n),
            "dispneia": rng.choice(["0", "1"], size=n),
            "saturacao": rng.choice(["0", "1"], size=n),
            "vacina_cov": rng.choice(["0", "1"], size=n),
        }
    )


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------

def test_clustering_sem_alvo(coorte_sintetica):
    r = gerar_datasets(coorte_sintetica, salvar=False, registrar=False)
    alvo = C.cfg("target", "coluna")
    assert alvo not in r["clustering"].columns


def test_clustering_com_id_e_features(coorte_sintetica):
    r = gerar_datasets(coorte_sintetica, salvar=False, registrar=False)
    feats = list(C.cfg("clustering", "features") or [])
    assert list(r["clustering"].columns) == [COLUNA_ID] + feats


# ---------------------------------------------------------------------------
# Supervisionado
# ---------------------------------------------------------------------------

def test_supervisionado_tem_alvo_tempo_e_id(coorte_sintetica):
    r = gerar_datasets(coorte_sintetica, salvar=False, registrar=False)
    alvo = C.cfg("target", "coluna")
    coluna_tempo = C.cfg("coluna_tempo")
    df = r["supervisionado"]
    assert alvo in df.columns
    assert coluna_tempo in df.columns
    assert COLUNA_ID in df.columns


# ---------------------------------------------------------------------------
# Identificadores
# ---------------------------------------------------------------------------

def test_identificadores_unicos_e_alinhados(coorte_sintetica):
    r = gerar_datasets(coorte_sintetica, salvar=False, registrar=False)
    a = r["clustering"][COLUNA_ID]
    b = r["supervisionado"][COLUNA_ID]
    assert a.is_unique
    assert b.is_unique
    assert a.tolist() == b.tolist()
    assert a.tolist() == list(range(len(coorte_sintetica)))


# ---------------------------------------------------------------------------
# Leakage
# ---------------------------------------------------------------------------

def test_leakage_dispara_com_proibida(monkeypatch, coorte_sintetica):
    """Se `clustering.features` incluir uma coluna proibida, dispara."""
    original = C.cfg

    def fake_cfg(*chaves, default=None):
        if chaves == ("clustering", "features"):
            return ["idade_anos", "evolucao"]  # `evolucao` é proibida
        return original(*chaves, default=default)

    monkeypatch.setattr(C, "cfg", fake_cfg)

    with pytest.raises(LeakageError):
        gerar_datasets(coorte_sintetica, salvar=False, registrar=False)


def test_supervisionado_x_sem_proibidas(coorte_sintetica):
    """O X do supervisionado (sem o alvo) não contém itens proibidos."""
    r = gerar_datasets(coorte_sintetica, salvar=False, registrar=False)
    alvo = C.cfg("target", "coluna")
    proibidas = set(C.cfg("features", "proibidas") or [])
    X = r["supervisionado"].drop(columns=[alvo])
    assert not (set(X.columns) & proibidas)


# ---------------------------------------------------------------------------
# Manifesto
# ---------------------------------------------------------------------------

def test_manifesto_gerado(coorte_sintetica, tmp_path):
    gerar_datasets(
        coorte_sintetica,
        salvar=True,
        registrar=False,
        output_dir=tmp_path,
    )
    manif = tmp_path / ARQUIVO_MANIFESTO
    assert manif.exists()

    dados = json.loads(manif.read_text(encoding="utf-8"))
    for chave in (
        "gerado_em_utc",
        "seed",
        "supervised_yaml_sha256",
        "coorte_origem",
        "clustering",
        "supervisionado",
    ):
        assert chave in dados

    assert (tmp_path / ARQUIVO_CLUSTERING).exists()
    assert (tmp_path / ARQUIVO_SUPERVISIONADO).exists()

    assert dados["clustering"]["sha256"]
    assert dados["supervisionado"]["sha256"]
    assert dados["seed"] == C.SEED


def test_manifesto_registra_ausencia_e_por_ano(coorte_sintetica, tmp_path):
    gerar_datasets(
        coorte_sintetica,
        salvar=True,
        registrar=False,
        output_dir=tmp_path,
    )
    dados = json.loads(
        (tmp_path / ARQUIVO_MANIFESTO).read_text(encoding="utf-8")
    )
    assert "n_por_ano" in dados["coorte_origem"]
    assert isinstance(dados["coorte_origem"]["n_por_ano"], dict)

    assert isinstance(dados["clustering"]["ausencia_pct"], dict)
    assert isinstance(dados["supervisionado"]["ausencia_pct"], dict)
    for pct in dados["clustering"]["ausencia_pct"].values():
        assert 0.0 <= pct <= 100.0


# ---------------------------------------------------------------------------
# Coorte ausente — placeholder claro
# ---------------------------------------------------------------------------

def test_carregar_coorte_inexistente_levanta(tmp_path, monkeypatch):
    """Se o arquivo não existe, a mensagem lista o que é esperado."""
    fantasma = tmp_path / "coorte_provisoria.parquet"
    with pytest.raises(FileNotFoundError, match="não encontrada"):
        carregar_coorte_provisoria(fantasma)


def test_carregar_coorte_sem_candidatos_lista_requisitos(monkeypatch, tmp_path):
    """
    Quando nenhum candidato existe, a mensagem deve listar as colunas
    esperadas — placeholder claro pedido na tarefa.
    """
    from src.data import analitico as A

    # Redireciona os candidatos para um diretório vazio.
    vazio = tmp_path / "vazio"
    vazio.mkdir()
    monkeypatch.setattr(
        A,
        "_COORTE_CANDIDATOS",
        (
            vazio / "coorte_provisoria.parquet",
            vazio / "coorte.parquet",
        ),
    )

    with pytest.raises(FileNotFoundError) as exc:
        carregar_coorte_provisoria()

    msg = str(exc.value)
    assert "nu_idade_n" in msg
    assert "tp_idade" in msg
    assert "dt_sin_pri" in msg
    assert "dt_interna" in msg
    assert C.cfg("coluna_tempo") in msg
    assert C.cfg("target", "coluna") in msg


# ---------------------------------------------------------------------------
# Round-trip dos parquets salvos
# ---------------------------------------------------------------------------

def test_round_trip_parquet(coorte_sintetica, tmp_path):
    r = gerar_datasets(
        coorte_sintetica,
        salvar=True,
        registrar=False,
        output_dir=tmp_path,
    )
    lido = pd.read_parquet(tmp_path / ARQUIVO_SUPERVISIONADO)
    assert list(lido.columns) == list(r["supervisionado"].columns)
    assert len(lido) == len(r["supervisionado"])
    assert lido[COLUNA_ID].is_unique

    lido_c = pd.read_parquet(tmp_path / ARQUIVO_CLUSTERING)
    assert list(lido_c.columns) == list(r["clustering"].columns)