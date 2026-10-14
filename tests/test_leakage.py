"""
Testes anti-vazamento de dados.

Protegem contra:
- inclusão do alvo nas features;
- inclusão de colunas posteriores ao desfecho;
- quebra da ordem temporal entre treino, validação e holdout;
- duplicação de identificadores quando houver chave adequada.

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


def _forcar_status_gate(
    monkeypatch: pytest.MonkeyPatch,
    nome_gate: str,
    status: str,
) -> None:
    """
    Faz `C.cfg("gates", nome_gate)` devolver `{"status": status}`,
    ignorando o YAML real apenas para esse gate.
    """
    monkeypatch.setattr(
        C,
        "cfg",
        lambda *chaves, default=None: (
            {"status": status}
            if chaves == ("gates", nome_gate)
            else default
        ),
    )


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


def test_split_temporal_3way_respeita_ordem() -> None:
    from src.evaluation.temporal import split_temporal_3way

    df = pd.DataFrame({
        "dt_notific": pd.date_range("2020-01-01", periods=100, freq="D"),
        "valor": range(100),
    })

    treino, validacao, holdout = split_temporal_3way(
        df,
        coluna_tempo="dt_notific",
        frac_treino=0.70,
        frac_validacao=0.15,
    )

    assert not treino.empty
    assert not validacao.empty
    assert not holdout.empty

    assert treino["dt_notific"].max() <= validacao["dt_notific"].min()
    assert validacao["dt_notific"].max() <= holdout["dt_notific"].min()


def test_split_temporal_3way_rejeita_nat_por_default() -> None:
    from src.evaluation.temporal import split_temporal_3way

    df = pd.DataFrame({
        "dt_notific": [
            pd.Timestamp("2020-01-01"),
            pd.NaT,
            pd.Timestamp("2020-01-03"),
        ],
        "valor": [1, 2, 3],
    })

    with pytest.raises(ValueError, match="data inválida"):
        split_temporal_3way(df, coluna_tempo="dt_notific")


def test_split_temporal_3way_dropa_nat_quando_pedido() -> None:
    from src.evaluation.temporal import split_temporal_3way

    df = pd.DataFrame({
        "dt_notific": pd.date_range("2020-01-01", periods=10, freq="D"),
        "valor": range(10),
    })
    df.loc[3, "dt_notific"] = pd.NaT

    treino, validacao, holdout = split_temporal_3way(
        df,
        coluna_tempo="dt_notific",
        on_nat="drop",
    )

    assert len(treino) + len(validacao) + len(holdout) == 9


def test_temporal_split_bloqueia_holdout_antes_de_concluir() -> None:
    from src.evaluation.temporal import TemporalSplit

    df = pd.DataFrame({
        "dt_notific": pd.date_range("2020-01-01", periods=100, freq="D"),
        "valor": range(100),
    })
    split = TemporalSplit(df=df, coluna_tempo="dt_notific")

    assert not split.holdout_liberado
    with pytest.raises(RuntimeError, match="Holdout bloqueado"):
        split.holdout()


def test_concluir_selecao_exige_gate_g9_holdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    `concluir_selecao` só libera o holdout quando `gates.G9_holdout`
    estiver `aprovado`; com o gate pendente, deve levantar RuntimeError.
    """
    from src.evaluation.temporal import TemporalSplit

    _forcar_status_gate(monkeypatch, "G9_holdout", "pendente")

    df = pd.DataFrame({
        "dt_notific": pd.date_range("2020-01-01", periods=100, freq="D"),
        "valor": range(100),
    })
    split = TemporalSplit(df=df, coluna_tempo="dt_notific")

    with pytest.raises(RuntimeError, match="G9_holdout"):
        split.concluir_selecao()

    assert not split.holdout_liberado


def test_concluir_selecao_libera_holdout_quando_gate_aprovado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Com o gate `G9_holdout` aprovado (simulado), libera o holdout."""
    from src.evaluation.temporal import TemporalSplit

    _forcar_status_gate(monkeypatch, "G9_holdout", "aprovado")

    df = pd.DataFrame({
        "dt_notific": pd.date_range("2020-01-01", periods=100, freq="D"),
        "valor": range(100),
    })
    split = TemporalSplit(df=df, coluna_tempo="dt_notific")

    split.concluir_selecao()
    assert split.holdout_liberado
    assert not split.holdout().empty


def test_dataset_sem_identificadores_duplicados(parquet_disponivel) -> None:
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