"""Testes do resolvedor de coorte (provisória, final, auto)."""

from pathlib import Path

import pandas as pd
import pytest

from src.data.cohort_source import cohort_candidates, load_cohort, resolve_cohort_path


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


def test_padrao_permanece_provisorio(tmp_path: Path) -> None:
    paths = cohort_candidates(tmp_path)
    _write(paths["provisional"][1], 1)   # coorte_provisoria_b.parquet
    _write(paths["final"][0], 2)         # coorte_final.parquet (existe, mas não é o default)

    kind, path = resolve_cohort_path(tmp_path)

    assert kind == "provisional"
    assert path.name == "coorte_provisoria_b.parquet"


def test_final_exige_escolha_explicita(tmp_path: Path) -> None:
    path = cohort_candidates(tmp_path)["final"][0]
    _write(path, 2)

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


def test_tipo_invalido_falha(tmp_path: Path) -> None:
    # Valor viola intencionalmente o Literal CohortKind.
    with pytest.raises(ValueError, match="provisional, final ou auto"):
        resolve_cohort_path(tmp_path, kind="desconhecida")  # type: ignore[arg-type]