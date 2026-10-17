"""
Testes anti-vazamento de dados.

Cobrem:

- consistência entre ``features.proibidas`` e ``pipeline.FEATURES``;
- proibição do alvo nas features;
- contrato de ``check_leakage`` (coluna proibida, alvo, lista vazia);
- duplicidade de identificadores no Parquet (slow).
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.evaluation.leakage import LeakageError, check_leakage
from src.utils import config as C


# ---------------------------------------------------------------------------
# Contrato de configuração (features.proibidas ↔ FEATURES)
# ---------------------------------------------------------------------------

@pytest.fixture
def proibidas() -> set[str]:
    """Conjunto ``features.proibidas`` do ``supervised.yaml``."""
    return set(C.cfg("features", "proibidas") or [])


@pytest.fixture
def features_finais() -> set[str]:
    """``pipeline.FEATURES`` — features efetivamente usadas pelo modelo."""
    from src.models import pipeline
    return set(pipeline.FEATURES)


def test_proibidas_nao_vazia(proibidas: set[str]) -> None:
    assert proibidas


def test_alvo_esta_entre_proibidas(proibidas: set[str]) -> None:
    assert C.cfg("target", "coluna") in proibidas


def test_features_finais_sem_proibidas(
    features_finais: set[str],
    proibidas: set[str],
) -> None:
    vazamento = features_finais & proibidas
    assert not vazamento, f"FEATURES contém colunas proibidas: {sorted(vazamento)}"


def test_features_finais_nao_inclui_alvo(features_finais: set[str]) -> None:
    assert C.cfg("target", "coluna") not in features_finais


# ---------------------------------------------------------------------------
# Contrato de check_leakage
# ---------------------------------------------------------------------------

def test_check_leakage_passa_com_X_limpo() -> None:
    X = pd.DataFrame({"feat_a": [1, 2, 3], "feat_b": [4, 5, 6]})
    check_leakage(X)


def test_check_leakage_levanta_para_proibida(proibidas: set[str]) -> None:
    coluna = sorted(proibidas)[0]
    X = pd.DataFrame({coluna: [1, 2, 3], "feat_ok": [4, 5, 6]})

    with pytest.raises(LeakageError) as exc:
        check_leakage(X)

    assert coluna in str(exc.value)


def test_check_leakage_levanta_para_alvo() -> None:
    alvo = C.cfg("target", "coluna")
    X = pd.DataFrame({alvo: [0, 1, 0], "feat_ok": [1, 2, 3]})

    with pytest.raises(LeakageError):
        check_leakage(X)


def test_check_leakage_lista_vazia_ainda_verifica_alvo() -> None:
    """``forbidden_columns=[]`` ainda soma ``DEFAULT_LEAKAGE_COLUMNS`` + alvo."""
    alvo = C.cfg("target", "coluna")
    X = pd.DataFrame({alvo: [0, 1, 0], "feat_ok": [1, 2, 3]})

    with pytest.raises(LeakageError):
        check_leakage(X, forbidden_columns=[])


# ---------------------------------------------------------------------------
# Identificadores no Parquet (slow)
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_dataset_sem_identificadores_duplicados(parquet_disponivel) -> None:
    """Taxa de ``nu_notific`` (ou equivalente) duplicado deve ser < 5%."""
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    import pyarrow.parquet as pq

    colunas = set(pq.read_schema(parquet_disponivel).names)
    candidatas = ("nu_notific", "numero_notificacao", "id_notificacao", "id")
    coluna_id = next((c for c in candidatas if c in colunas), None)

    if coluna_id is None:
        pytest.skip("Sem coluna identificadora adequada.")

    df = pd.read_parquet(parquet_disponivel, columns=[coluna_id])
    ids = df[coluna_id].dropna().astype("string").str.strip()
    ids = ids[ids.ne("")]

    if ids.empty:
        pytest.skip(f"Coluna {coluna_id} sem identificadores válidos.")

    taxa = int(ids.duplicated().sum()) / len(ids)
    assert taxa < 0.05, f"Taxa alta de duplicados em {coluna_id}: {taxa:.1%}"