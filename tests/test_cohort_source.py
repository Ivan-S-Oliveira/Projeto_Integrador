"""Testes do resolvedor de coorte (provisória, final, auto, explicit_path).

Cobrem:
- descoberta automática por ``kind`` e fallback dentro da família provisória;
- ``auto`` preferindo a final e caindo em provisional quando só ela existe;
- validação de ``explicit_path`` (nome canônico + coerência com ``kind``);
- regressão da #30: ``coorte.parquet`` não é mais engolido como provisório.
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
# Fixtures e helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _sem_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Limpa ``SRAG_COHORT_KIND`` do ambiente antes de cada teste.

    Sem isto, um ``SRAG_COHORT_KIND`` definido no shell do runner
    tornaria os testes dependentes do estado local.
    """
    monkeypatch.delenv("SRAG_COHORT_KIND", raising=False)


def _write(path: Path, value: int) -> None:
    """Grava um Parquet 1×1 com uma única coluna ``value``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"value": [value]}).to_parquet(path, index=False)


# ---------------------------------------------------------------------------
# Descoberta automática por kind
# ---------------------------------------------------------------------------

def test_padrao_permanece_provisorio(tmp_path: Path) -> None:
    """Sem ``kind``, o padrão é ``provisional``, mesmo com a final presente.

    Quando ``coorte_provisoria.parquet`` não existe, o resolver cai no
    próximo candidato provisório (``coorte_provisoria_b.parquet``).
    """
    paths = cohort_candidates(tmp_path)
    _write(paths["provisional"][1], 1)   # coorte_provisoria_b.parquet
    _write(paths["final"][0], 2)         # coorte_final.parquet (não é o default)

    kind, path = resolve_cohort_path(tmp_path)

    assert kind == "provisional"
    assert path.name == "coorte_provisoria_b.parquet"


def test_final_exige_escolha_explicita(tmp_path: Path) -> None:
    """Só existe a coorte final; sem ``kind`` a busca falha em vez de devolvê-la."""
    path = cohort_candidates(tmp_path)["final"][0]
    _write(path, 2)

    with pytest.raises(FileNotFoundError, match="provisional"):
        resolve_cohort_path(tmp_path)

    frame, source = load_cohort(tmp_path, kind="final")

    assert frame["value"].tolist() == [2]
    assert source.kind == "final"
    assert source.rows == 1
    assert len(source.sha256) == 64


def test_auto_prefere_final(tmp_path: Path) -> None:
    paths = cohort_candidates(tmp_path)
    _write(paths["provisional"][0], 1)
    _write(paths["final"][0], 2)

    kind, path = resolve_cohort_path(tmp_path, kind="auto")

    assert kind == "final"
    assert path.name == "coorte_final.parquet"


def test_auto_cai_em_provisional_quando_so_ela_existe(tmp_path: Path) -> None:
    """``auto`` só prefere a final quando ela existe; senão usa a provisória."""
    paths = cohort_candidates(tmp_path)
    _write(paths["provisional"][0], 1)

    kind, path = resolve_cohort_path(tmp_path, kind="auto")

    assert kind == "provisional"
    assert path.name == "coorte_provisoria.parquet"


def test_tipo_invalido_falha(tmp_path: Path) -> None:
    # Valor viola intencionalmente o Literal CohortKind.
    with pytest.raises(ValueError, match="provisional, final ou auto"):
        resolve_cohort_path(tmp_path, kind="desconhecida")  # type: ignore[arg-type]


def test_nenhum_candidato_falha(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Nenhuma coorte"):
        resolve_cohort_path(tmp_path, kind="provisional")


# ---------------------------------------------------------------------------
# Regressão da #30: nomes ambíguos não são mais aceitos
# ---------------------------------------------------------------------------

def test_coorte_parquet_nao_e_mais_candidato(tmp_path: Path) -> None:
    """``coorte.parquet`` não deve ser engolido como provisório (regressão #30)."""
    _write(tmp_path / "data" / "analytical" / "coorte.parquet", 2)

    with pytest.raises(FileNotFoundError):
        resolve_cohort_path(tmp_path, kind="provisional")


# ---------------------------------------------------------------------------
# explicit_path: nome canônico + coerência com `kind`
# ---------------------------------------------------------------------------

def test_explicit_path_sem_kind_usa_nome(tmp_path: Path) -> None:
    path = cohort_candidates(tmp_path)["final"][0]
    _write(path, 2)

    kind, resolved = resolve_cohort_path(tmp_path, explicit_path=path)

    assert kind == "final"
    assert resolved.name == "coorte_final.parquet"


def test_explicit_path_com_kind_consistente_ok(tmp_path: Path) -> None:
    path = cohort_candidates(tmp_path)["final"][0]
    _write(path, 2)

    kind, resolved = resolve_cohort_path(tmp_path, kind="final", explicit_path=path)

    assert kind == "final"
    assert resolved.name == "coorte_final.parquet"


def test_explicit_path_com_kind_conflitante_falha(tmp_path: Path) -> None:
    """Coorte final passada como ``provisional`` → falha em vez de mascarar o tipo."""
    path = cohort_candidates(tmp_path)["final"][0]
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