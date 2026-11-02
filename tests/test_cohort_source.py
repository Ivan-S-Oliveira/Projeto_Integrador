"""Testes do resolvedor de coorte (somente a definitiva é aceita).

Cobrem:
- descoberta do arquivo canônico ``coorte_final.parquet``;
- a variável de ambiente ``SRAG_COHORT_KIND`` (aceita apenas ``final``);
- rejeição dos tipos aposentados (``provisional`` e ``auto``);
- ``explicit_path`` com nome canônico e rejeição de nomes desconhecidos,
  inclusive os nomes antigos da coorte provisória;
- ``load_cohort`` devolvendo dados e metadados da fonte.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.data.cohort_source import (
    CohortSource,
    cohort_candidates,
    load_cohort,
    resolve_cohort_path,
)

_FINAL = "coorte_final.parquet"
_NOMES_ANTIGOS = ("coorte_provisoria.parquet", "coorte_provisoria_b.parquet")


@pytest.fixture(autouse=True)
def _limpar_variavel_de_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove ``SRAG_COHORT_KIND`` antes de cada teste.

    Sem isto, uma variável definida no shell do runner mudaria o default
    ``final`` e tornaria os testes dependentes do ambiente.
    """
    monkeypatch.delenv("SRAG_COHORT_KIND", raising=False)


def _criar(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"conteudo")
    return path


def _coorte_final(root: Path) -> Path:
    return _criar(root / "data" / "analytical" / _FINAL)


# ---------------------------------------------------------------------------
# Descoberta pelo tipo
# ---------------------------------------------------------------------------
def test_candidatos_existem_apenas_para_a_definitiva(tmp_path: Path) -> None:
    candidatos = cohort_candidates(tmp_path)

    assert set(candidatos) == {"final"}
    assert candidatos["final"] == (tmp_path / "data" / "analytical" / _FINAL,)


def test_default_resolve_a_coorte_final(tmp_path: Path) -> None:
    esperado = _coorte_final(tmp_path)

    kind, path = resolve_cohort_path(tmp_path)

    assert kind == "final"
    assert path == esperado.resolve()


def test_kind_final_explicito(tmp_path: Path) -> None:
    _coorte_final(tmp_path)

    kind, path = resolve_cohort_path(tmp_path, kind="final")

    assert kind == "final"
    assert path.name == _FINAL


def test_sem_coorte_final_falha_com_candidatos(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Nenhuma coorte do tipo 'final'"):
        resolve_cohort_path(tmp_path)


def test_coorte_provisoria_nao_e_usada_nem_como_fallback(tmp_path: Path) -> None:
    for nome in _NOMES_ANTIGOS:
        _criar(tmp_path / "data" / "analytical" / nome)

    with pytest.raises(FileNotFoundError):
        resolve_cohort_path(tmp_path)


# ---------------------------------------------------------------------------
# Tipos aposentados
# ---------------------------------------------------------------------------
def test_kind_provisional_e_rejeitado(tmp_path: Path) -> None:
    _coorte_final(tmp_path)

    with pytest.raises(ValueError, match="não é mais aceito"):
        resolve_cohort_path(tmp_path, kind="provisional")  # type: ignore[arg-type]


def test_kind_auto_e_rejeitado(tmp_path: Path) -> None:
    _coorte_final(tmp_path)

    with pytest.raises(ValueError, match="não é mais aceito"):
        resolve_cohort_path(tmp_path, kind="auto")  # type: ignore[arg-type]


def test_kind_desconhecido_e_rejeitado(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="deve ser final"):
        resolve_cohort_path(tmp_path, kind="desconhecida")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# SRAG_COHORT_KIND (variável de ambiente)
# ---------------------------------------------------------------------------
def test_variavel_de_ambiente_final_e_aceita_em_maiusculas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _coorte_final(tmp_path)
    monkeypatch.setenv("SRAG_COHORT_KIND", "FINAL")

    kind, _ = resolve_cohort_path(tmp_path)

    assert kind == "final"


def test_variavel_de_ambiente_provisional_e_rejeitada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _coorte_final(tmp_path)
    monkeypatch.setenv("SRAG_COHORT_KIND", "provisional")

    with pytest.raises(ValueError, match="não é mais aceito"):
        resolve_cohort_path(tmp_path)


def test_parametro_kind_vence_a_variavel_de_ambiente(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _coorte_final(tmp_path)
    monkeypatch.setenv("SRAG_COHORT_KIND", "provisional")

    kind, _ = resolve_cohort_path(tmp_path, kind="final")

    assert kind == "final"


# ---------------------------------------------------------------------------
# explicit_path
# ---------------------------------------------------------------------------
def test_explicit_path_com_nome_canonico(tmp_path: Path) -> None:
    caminho = _criar(tmp_path / "qualquer_pasta" / _FINAL)

    kind, resolvido = resolve_cohort_path(tmp_path, explicit_path=caminho)

    assert kind == "final"
    assert resolvido == caminho.resolve()


def test_explicit_path_com_kind_final(tmp_path: Path) -> None:
    caminho = _criar(tmp_path / _FINAL)

    kind, _ = resolve_cohort_path(tmp_path, kind="final", explicit_path=caminho)

    assert kind == "final"


def test_explicit_path_com_kind_provisional_e_rejeitado(tmp_path: Path) -> None:
    caminho = _criar(tmp_path / _FINAL)

    with pytest.raises(ValueError, match="não é mais aceito"):
        resolve_cohort_path(
            tmp_path, kind="provisional", explicit_path=caminho  # type: ignore[arg-type]
        )


def test_explicit_path_com_nome_ambiguo_e_rejeitado(tmp_path: Path) -> None:
    caminho = _criar(tmp_path / "coorte.parquet")

    with pytest.raises(ValueError, match="não reconhecido"):
        resolve_cohort_path(tmp_path, explicit_path=caminho)


@pytest.mark.parametrize("nome", _NOMES_ANTIGOS)
def test_explicit_path_com_nome_da_coorte_provisoria_e_rejeitado(
    tmp_path: Path, nome: str
) -> None:
    caminho = _criar(tmp_path / nome)

    with pytest.raises(ValueError, match="aposentada"):
        resolve_cohort_path(tmp_path, explicit_path=caminho)


def test_explicit_path_inexistente(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="não encontrada"):
        resolve_cohort_path(tmp_path, explicit_path=tmp_path / _FINAL)


# ---------------------------------------------------------------------------
# load_cohort
# ---------------------------------------------------------------------------
def test_load_cohort_devolve_dados_e_metadados(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    caminho = _coorte_final(tmp_path)
    quadro = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    chamadas: dict[str, object] = {}

    def _ler(path: object, columns: list[str] | None = None) -> pd.DataFrame:
        chamadas["path"] = Path(str(path))
        chamadas["columns"] = columns
        return quadro if columns is None else quadro[columns]

    monkeypatch.setattr(pd, "read_parquet", _ler)

    frame, fonte = load_cohort(tmp_path)

    assert isinstance(fonte, CohortSource)
    assert chamadas["path"] == caminho.resolve()
    assert chamadas["columns"] is None
    assert fonte.kind == "final"
    assert fonte.path == str(caminho.resolve())
    assert fonte.rows == 3
    assert fonte.columns == 2
    assert fonte.size_bytes == len(b"conteudo")
    assert len(fonte.sha256) == 64
    assert fonte.to_dict()["kind"] == "final"
    assert list(frame.columns) == ["a", "b"]


def test_load_cohort_respeita_a_lista_de_colunas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _coorte_final(tmp_path)
    quadro = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    monkeypatch.setattr(
        pd, "read_parquet",
        lambda path, columns=None: quadro if columns is None else quadro[columns],
    )

    frame, fonte = load_cohort(tmp_path, columns=["a"])

    assert list(frame.columns) == ["a"]
    assert fonte.columns == 1
