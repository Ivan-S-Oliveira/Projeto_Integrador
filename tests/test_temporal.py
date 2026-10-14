"""
Testes anti-vazamento de dados.

Protegem contra:
- inclusão do alvo nas features;
- inclusão de colunas posteriores ao desfecho;
- duplicação de identificadores quando houver chave adequada.

Split temporal e trava do gate ``G9_holdout`` são testados em
``tests/test_temporal.py`` — não duplicar aqui.

Fonte única de verdade: `configs/supervised.yaml`, lido via
`src.utils.config` (`features.proibidas`) — nada hard-coded aqui.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.utils import config as C


@pytest.fixture
def proibidas() -> set[str]:
    """Colunas proibidas declaradas em `features.proibidas` do YAML."""
    return set(C.cfg("features", "proibidas") or [])


@pytest.fixture
def features_finais() -> set[str]:
    """Lista final de features exposta por `src.models.pipeline`."""
    from src.models import pipeline
    return set(pipeline.FEATURES)


def test_proibidas_nao_vazia(proibidas: set[str]) -> None:
    assert proibidas, (
        "features.proibidas está vazia no supervised.yaml — "
        "ao menos o alvo e as colunas posteriores ao desfecho precisam "
        "estar listadas."
    )


def test_alvo_esta_entre_proibidas(proibidas: set[str]) -> None:
    alvo = C.cfg("target", "coluna")
    assert alvo in proibidas, (
        f"target.coluna ({alvo!r}) precisa estar em features.proibidas."
    )


def test_features_finais_sem_proibidas(
    features_finais: set[str],
    proibidas: set[str],
) -> None:
    vazamento = features_finais & proibidas
    assert not vazamento, (
        f"FEATURES contém colunas proibidas: {sorted(vazamento)}"
    )


def test_features_finais_nao_inclui_alvo(features_finais: set[str]) -> None:
    alvo = C.cfg("target", "coluna")
    assert alvo not in features_finais


def test_check_leakage_passa_quando_X_limpo() -> None:
    from src.evaluation.leakage import check_leakage

    X = pd.DataFrame({"feat_a": [1, 2, 3], "feat_b": [4, 5, 6]})
    check_leakage(X)


def test_check_leakage_levanta_para_proibida(proibidas: set[str]) -> None:
    from src.evaluation.leakage import LeakageError, check_leakage

    coluna = sorted(proibidas)[0]
    X = pd.DataFrame({coluna: [1, 2, 3], "feat_ok": [4, 5, 6]})

    with pytest.raises(LeakageError) as exc:
        check_leakage(X)

    assert coluna in str(exc.value), (
        "A mensagem de erro precisa citar a coluna problemática."
    )


def test_check_leakage_levanta_para_alvo() -> None:
    from src.evaluation.leakage import LeakageError, check_leakage

    alvo = C.cfg("target", "coluna")
    X = pd.DataFrame({alvo: [0, 1, 0], "feat_ok": [1, 2, 3]})

    with pytest.raises(LeakageError):
        check_leakage(X)


def test_check_leakage_lista_vazia_ainda_verifica_alvo() -> None:
    """Lista vazia desliga proibidas, mas o alvo continua sendo checado."""
    from src.evaluation.leakage import LeakageError, check_leakage

    alvo = C.cfg("target", "coluna")
    X = pd.DataFrame({alvo: [0, 1, 0], "feat_ok": [1, 2, 3]})

    with pytest.raises(LeakageError):
        check_leakage(X, forbidden_columns=[])


def test_dataset_sem_identificadores_duplicados(
    parquet_disponivel,
) -> None:
    """
    Checa duplicidade apenas se houver coluna que sirva como
    identificador da notificação. UF e data não formam chave única.
    """
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    import pyarrow.parquet as pq

    colunas = set(pq.read_schema(parquet_disponivel).names)

    candidatas = [
        "nu_notific",
        "numero_notificacao",
        "id_notificacao",
        "id",
    ]
    coluna_id = next((c for c in candidatas if c in colunas), None)

    if coluna_id is None:
        pytest.skip(
            "O Parquet não possui uma coluna identificadora adequada "
            "para o teste de duplicidade."
        )

    df = pd.read_parquet(parquet_disponivel, columns=[coluna_id])
    ids = df[coluna_id].dropna().astype("string").str.strip()
    ids = ids[ids.ne("")]

    if ids.empty:
        pytest.skip(f"A coluna {coluna_id} não possui identificadores válidos.")

    quantidade_duplicada = int(ids.duplicated().sum())
    taxa_duplicada = quantidade_duplicada / len(ids)

    assert taxa_duplicada < 0.05, (
        f"Alta taxa de identificadores duplicados em {coluna_id}: "
        f"{quantidade_duplicada}/{len(ids)} ({taxa_duplicada:.1%})"
    )