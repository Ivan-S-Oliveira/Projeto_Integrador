"""Invariantes da partição-mestra sobre o artefato real (§28.4 do decisoes.md).

Provam, sobre ``partitions_master.parquet``, as cinco garantias do protocolo:

(a) cada ``group_id`` em um único bloco;
(b) 2020–2022 somente em ``test_pandemic``;
(c) 2026 somente em ``exploracao``;
(d) prevalência dos blocos de 2019/2023–2025 a no máximo 0,5 p.p. de 8,44%;
(e) SHA-256 do arquivo igual ao do manifesto.

Se o artefato não existir, a classe é pulada (``pytest.skip``): não falha o CI
de quem ainda não gerou o artefato supervisionado.
"""
import ast
import json
from pathlib import Path

import pandas as pd
import pytest

from src.utils.hashing import sha256_file


_ARTEFATO_PARTICAO = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "analytical"
    / "partitions_master.parquet"
)
_MANIFESTO_PARTICAO = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "analytical"
    / "manifesto_particao.json"
)
_PREVALENCIA_ESPERADA = 0.0844      # 8,44% (§29.1, coorte definitiva)
_TOLERANCIA_PP        = 0.005       # 0,5 ponto percentual
_BLOCOS_DESENVOLVIMENTO = (
    "train_ref", "val_ref", "test_ref",
)
_ANOS_DESENVOLVIMENTO = (2019, 2023, 2024, 2025)


@pytest.fixture(scope="class")
def particao_mestra_real():
    """Carrega o artefato real da partição-mestra (só 4 colunas).

    Faz ``pytest.skip`` se o artefato ou o manifesto ainda não existirem —
    o artefato é produzido pela geração do artefato supervisionado e não é versionado no Git.
    """
    if not _ARTEFATO_PARTICAO.is_file() or not _MANIFESTO_PARTICAO.is_file():
        pytest.skip(
            "Artefato da partição-mestra ausente: "
            f"{_ARTEFATO_PARTICAO} / {_MANIFESTO_PARTICAO}. "
            "Gere o artefato supervisionado antes desta auditoria."
        )

    df = pd.read_parquet(
        _ARTEFATO_PARTICAO,
        columns=[
            "bloco_mestre",
            "group_id",
            "ano_internacao",
            "alvo_obito_srag",
        ],
    )
    manifesto = json.loads(
        _MANIFESTO_PARTICAO.read_text(encoding="utf-8")
    )
    return df, manifesto


@pytest.mark.slow
class TestParticaoMestraArtefatoReal:
    """Auditoria do §28.4 sobre o artefato real do #142 (não sintético)."""

    def test_a_cada_group_id_em_um_unico_bloco(
        self,
        particao_mestra_real,
    ) -> None:
        """(a) Nenhum ``group_id`` aparece em mais de um bloco."""
        df, _ = particao_mestra_real
        n_blocos_por_grupo = (
            df.groupby("group_id", observed=True)["bloco_mestre"].nunique()
        )
        conflitos = n_blocos_por_grupo[n_blocos_por_grupo > 1]
        assert conflitos.empty, (
            "Grupos em mais de um bloco "
            f"({len(conflitos)}): {conflitos.head(10).to_dict()}"
        )

    def test_b_2020_2022_somente_em_test_pandemic(
        self,
        particao_mestra_real,
    ) -> None:
        """(b) Anos 2020–2022 exclusivamente em ``test_pandemic``."""
        df, _ = particao_mestra_real
        m = df["ano_internacao"].isin([2020, 2021, 2022])
        assert m.any(), "Nenhum registro de 2020–2022 no artefato."
        blocos = set(df.loc[m, "bloco_mestre"].astype(str).unique())
        assert blocos == {"test_pandemic"}, (
            "Anos pandêmicos fora de test_pandemic: "
            f"{sorted(blocos)}"
        )

    def test_c_2026_somente_em_exploracao(
        self,
        particao_mestra_real,
    ) -> None:
        """(c) Ano 2026 exclusivamente em ``exploracao``."""
        df, _ = particao_mestra_real
        m = df["ano_internacao"].eq(2026)
        if not m.any():
            pytest.skip("Artefato não contém 2026 (cobertura parcial).")
        blocos = set(df.loc[m, "bloco_mestre"].astype(str).unique())
        assert blocos == {"exploracao"}, (
            "2026 fora de exploracao: "
            f"{sorted(blocos)}"
        )

    def test_d_prevalencia_por_bloco_proxima_de_8_44_pct(
        self,
        particao_mestra_real,
    ) -> None:
        """(d) Prevalência dos blocos de desenvolvimento a ≤ 0,5 p.p. de 8,44%."""
        df, _ = particao_mestra_real
        sub = df[
            df["bloco_mestre"].astype(str).isin(_BLOCOS_DESENVOLVIMENTO)
            & df["ano_internacao"].isin(_ANOS_DESENVOLVIMENTO)
        ]
        prev = sub.groupby("bloco_mestre", observed=True)[
            "alvo_obito_srag"
        ].mean()
        desvio_pp = (prev - _PREVALENCIA_ESPERADA).abs() * 100
        fora = desvio_pp[desvio_pp > _TOLERANCIA_PP * 100]
        assert fora.empty, (
            "Prevalência fora de ±0,5 p.p. de 8,44%: "
            f"{prev.round(4).to_dict()} "
            f"(desvios em p.p.: {desvio_pp.round(3).to_dict()})"
        )

    def test_e_sha256_do_artefato_igual_ao_manifesto(
        self,
        particao_mestra_real,
    ) -> None:
        """(e) SHA-256 do ``partitions_master.parquet`` bate com o manifesto."""
        _, manifesto = particao_mestra_real
        esperado = manifesto.get("partition_sha256")
        assert esperado, (
            "Manifesto não contém 'partition_sha256'. "
            "Regere o artefato supervisionado."
        )
        obtido = sha256_file(_ARTEFATO_PARTICAO)
        assert obtido == esperado, (
            "SHA-256 divergente:\n"
            f"  esperado={esperado}\n"
            f"  obtido  ={obtido}"
        )

def test_src_sem_funcoes_duplicadas():
    """Duas funções de topo com o mesmo nome no mesmo arquivo: a última apaga a primeira."""
    pasta_src = Path(__file__).resolve().parents[1] / "src"
    for arquivo in pasta_src.rglob("*.py"):
        arvore = ast.parse(arquivo.read_text(encoding="utf-8-sig"))
        nomes = [n.name for n in arvore.body if isinstance(n, ast.FunctionDef)]
        repetidos = sorted({n for n in nomes if nomes.count(n) > 1})
        assert not repetidos, f"{arquivo.name}: funções definidas mais de uma vez: {repetidos}"
