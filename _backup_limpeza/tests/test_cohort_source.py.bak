"""Testes do resolvedor de coorte (provisória, final, auto, explicit_path).

Cobrem:

- descoberta por ``kind`` (``provisional``, ``final``, ``auto``);
- o uso de ``final`` como valor padrão de ``_DEFAULT_KIND``;
- a variável de ambiente ``SRAG_COHORT_KIND`` sobrescrevendo o default;
- validação de ``explicit_path`` (nome canônico + coerência com ``kind``);
- rejeição do nome ambíguo ``coorte.parquet`` como origem provisória.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.data.cohort_source import (
    cohort_candidates,
    load_cohort,
    resolve_cohort_path,
)


# ---------------------------------------------------------------------------
# Constantes dos nomes canônicos (evitam strings mágicas nos asserts)
# ---------------------------------------------------------------------------

_CANONICAL_PROVISIONAL = "coorte_provisoria.parquet"
_CANONICAL_PROVISIONAL_B = "coorte_provisoria_b.parquet"
_CANONICAL_FINAL = "coorte_final.parquet"


# ---------------------------------------------------------------------------
# Fixtures e helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _sem_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Limpa ``SRAG_COHORT_KIND`` antes de cada teste.

    Sem isto, um ``SRAG_COHORT_KIND`` definido no shell do runner tornaria
    os testes dependentes do estado local. Cada teste decide explicitamente
    qual ``kind`` quer exercitar (parâmetro ou ``monkeypatch.setenv``).
    """
    monkeypatch.delenv("SRAG_COHORT_KIND", raising=False)


def _write(path: Path, value: int) -> None:
    """Grava um Parquet 1×1 com uma coluna ``value``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"value": [value]}).to_parquet(path, index=False)


def _candidatos(tmp_path: Path) -> dict[str, tuple[Path, ...]]:
    """Atalho para ``cohort_candidates`` (evita a repetição de 4 caracteres)."""
    return cohort_candidates(tmp_path)


# ---------------------------------------------------------------------------
# A coorte final é a origem padrão
# ---------------------------------------------------------------------------

def test_default_busca_final(tmp_path: Path) -> None:
    """Sem ``kind`` e sem env var, o default é ``final``."""
    _write(_candidatos(tmp_path)["final"][0], 2)

    kind, path = resolve_cohort_path(tmp_path)

    assert kind == "final"
    assert path.name == _CANONICAL_FINAL


def test_default_final_nao_cai_em_provisional(tmp_path: Path) -> None:
    """Sem ``kind`` e sem coorte final, falha — não há fallback para provisória."""
    _write(_candidatos(tmp_path)["provisional"][0], 1)

    with pytest.raises(FileNotFoundError, match="final"):
        resolve_cohort_path(tmp_path)


def test_provisional_exige_kind_explicito(tmp_path: Path) -> None:
    """Para carregar a provisória, é preciso informar ``kind='provisional'``."""
    _write(_candidatos(tmp_path)["provisional"][0], 1)

    kind, path = resolve_cohort_path(tmp_path, kind="provisional")

    assert kind == "provisional"
    assert path.name == _CANONICAL_PROVISIONAL


def test_provisional_usa_fallback_b(tmp_path: Path) -> None:
    """Sem ``coorte_provisoria.parquet``, cai em ``coorte_provisoria_b.parquet``."""
    _write(_candidatos(tmp_path)["provisional"][1], 1)

    kind, path = resolve_cohort_path(tmp_path, kind="provisional")

    assert kind == "provisional"
    assert path.name == _CANONICAL_PROVISIONAL_B


# ---------------------------------------------------------------------------
# ``kind="auto"``
# ---------------------------------------------------------------------------

def test_auto_prefere_final(tmp_path: Path) -> None:
    paths = _candidatos(tmp_path)
    _write(paths["provisional"][0], 1)
    _write(paths["final"][0], 2)

    kind, path = resolve_cohort_path(tmp_path, kind="auto")

    assert kind == "final"
    assert path.name == _CANONICAL_FINAL


def test_auto_cai_em_provisional_quando_so_ela_existe(tmp_path: Path) -> None:
    _write(_candidatos(tmp_path)["provisional"][0], 1)

    kind, path = resolve_cohort_path(tmp_path, kind="auto")

    assert kind == "provisional"
    assert path.name == _CANONICAL_PROVISIONAL


# ---------------------------------------------------------------------------
# ``kind="final"`` explícito + metadados de ``load_cohort``
# ---------------------------------------------------------------------------

def test_load_cohort_final_expoe_metadados(tmp_path: Path) -> None:
    _write(_candidatos(tmp_path)["final"][0], 2)

    frame, source = load_cohort(tmp_path, kind="final")

    assert frame["value"].tolist() == [2]
    assert source.kind == "final"
    assert source.rows == 1
    assert len(source.sha256) == 64


# ---------------------------------------------------------------------------
# ``SRAG_COHORT_KIND`` (env var) — contrato explícito do resolvedor
# ---------------------------------------------------------------------------

def test_env_var_sobrescreve_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``SRAG_COHORT_KIND=provisional`` vence o default ``final``."""
    paths = _candidatos(tmp_path)
    _write(paths["provisional"][0], 1)
    _write(paths["final"][0], 2)

    monkeypatch.setenv("SRAG_COHORT_KIND", "provisional")

    kind, path = resolve_cohort_path(tmp_path)

    assert kind == "provisional"
    assert path.name == _CANONICAL_PROVISIONAL


def test_env_var_case_insensitive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write(_candidatos(tmp_path)["final"][0], 2)

    monkeypatch.setenv("SRAG_COHORT_KIND", "FINAL")

    kind, _ = resolve_cohort_path(tmp_path)

    assert kind == "final"


# ---------------------------------------------------------------------------
# Validações de ``kind``
# ---------------------------------------------------------------------------

def test_tipo_invalido_falha(tmp_path: Path) -> None:
    # Valor viola intencionalmente o Literal CohortKind.
    with pytest.raises(ValueError, match="provisional, final ou auto"):
        resolve_cohort_path(tmp_path, kind="desconhecida")  # type: ignore[arg-type]


def test_nenhum_candidato_falha(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Nenhuma coorte"):
        resolve_cohort_path(tmp_path, kind="provisional")


# ---------------------------------------------------------------------------
# Nomes ambíguos não são aceitos
# ---------------------------------------------------------------------------

def test_coorte_parquet_nao_e_mais_candidato(tmp_path: Path) -> None:
    """``coorte.parquet`` não é classificado como origem provisória."""
    _write(tmp_path / "data" / "analytical" / "coorte.parquet", 2)

    with pytest.raises(FileNotFoundError):
        resolve_cohort_path(tmp_path, kind="provisional")


# ---------------------------------------------------------------------------
# ``explicit_path``: nome canônico + coerência com ``kind``
# ---------------------------------------------------------------------------

def test_explicit_path_sem_kind_usa_nome(tmp_path: Path) -> None:
    path = _candidatos(tmp_path)["final"][0]
    _write(path, 2)

    kind, resolved = resolve_cohort_path(tmp_path, explicit_path=path)

    assert kind == "final"
    assert resolved.name == _CANONICAL_FINAL


def test_explicit_path_com_kind_consistente_ok(tmp_path: Path) -> None:
    path = _candidatos(tmp_path)["final"][0]
    _write(path, 2)

    kind, resolved = resolve_cohort_path(tmp_path, kind="final", explicit_path=path)

    assert kind == "final"
    assert resolved.name == _CANONICAL_FINAL


def test_explicit_path_com_kind_conflitante_falha(tmp_path: Path) -> None:
    """Coorte final passada como ``provisional`` falha em vez de mascarar o tipo."""
    path = _candidatos(tmp_path)["final"][0]
    _write(path, 2)

    with pytest.raises(ValueError, match="classificada como"):
        resolve_cohort_path(tmp_path, kind="provisional", explicit_path=path)


def test_explicit_path_com_nome_desconhecido_falha(tmp_path: Path) -> None:
    path = tmp_path / "coorte_definitiva.parquet"
    _write(path, 2)

    with pytest.raises(ValueError, match="Nome de coorte não reconhecido"):
        resolve_cohort_path(tmp_path, explicit_path=path)


def test_explicit_path_inexistente_falha(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Coorte explícita"):
        resolve_cohort_path(tmp_path, explicit_path=tmp_path / "nao_existe.parquet")