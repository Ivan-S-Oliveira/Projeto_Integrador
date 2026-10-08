"""
Testes anti-vazamento de dados.

Os testes protegem contra:
- inclusao do alvo no conjunto de features;
- inclusao de colunas posteriores ao desfecho;
- quebra da ordem temporal entre treino, validacao e holdout;
- duplicacao de identificadores quando houver uma chave adequada.
"""

import pandas as pd
import pytest

from src.utils import config as C


COLUNAS_PROIBIDAS = {
    "evolucao",
    "evolucao_covid19",
    "dt_evolucao",
    "dt_encerramento",
    "classificacao_final",
    "criterio_confirmacao",
    "sorologia",
    "pcr",
}


def test_config_features_proibidas_definidas():
    configuracao = C.carregar_supervised()

    proibidas_config = set(
        configuracao["features"]["proibidas"]
    )

    faltantes = (
        COLUNAS_PROIBIDAS
        - proibidas_config
    )

    assert not faltantes, (
        "As seguintes colunas proibidas nao estao "
        f"declaradas no YAML: {faltantes}"
    )


def test_pipeline_expoe_features_sem_alvo():
    from src.models import pipeline

    assert hasattr(pipeline, "FEATURES")

    features = set(pipeline.FEATURES)

    vazamento = (
        features
        & COLUNAS_PROIBIDAS
    )

    assert not vazamento, (
        "FEATURES contem colunas proibidas: "
        f"{vazamento}"
    )


def test_pipeline_nao_inclui_coluna_alvo():
    from src.models import pipeline

    features = set(pipeline.FEATURES)

    assert pipeline.ALVO not in features


def test_split_temporal_3way_respeita_ordem():
    from src.evaluation.temporal import (
        split_temporal_3way,
    )

    df = pd.DataFrame(
        {
            "dt_notific": pd.date_range(
                "2020-01-01",
                periods=100,
                freq="D",
            ),
            "valor": range(100),
        }
    )

    treino, validacao, holdout = (
        split_temporal_3way(
            df,
            coluna_tempo="dt_notific",
            frac_treino=0.70,
            frac_validacao=0.15,
        )
    )

    assert not treino.empty
    assert not validacao.empty
    assert not holdout.empty

    assert (
        treino["dt_notific"].max()
        <= validacao["dt_notific"].min()
    )

    assert (
        validacao["dt_notific"].max()
        <= holdout["dt_notific"].min()
    )


def test_temporal_split_bloqueia_holdout():
    from src.evaluation.temporal import (
        TemporalSplit,
    )

    df = pd.DataFrame(
        {
            "dt_notific": pd.date_range(
                "2020-01-01",
                periods=100,
                freq="D",
            ),
            "valor": range(100),
        }
    )

    split = TemporalSplit(
        df=df,
        coluna_tempo="dt_notific",
    )

    assert not split.holdout_liberado

    with pytest.raises(RuntimeError):
        split.holdout()

    split.concluir_selecao()

    assert split.holdout_liberado
    assert not split.holdout().empty


def test_dataset_sem_identificadores_duplicados(
    parquet_disponivel,
):
    """
    Testa duplicidade somente se houver uma coluna que possa
    funcionar como identificador da notificacao.

    UF e data nao formam uma chave unica e nao devem ser usadas
    isoladamente para declarar duplicacao de registros.
    """
    if parquet_disponivel is None:
        pytest.skip("Parquet nao disponivel.")

    import pyarrow.parquet as pq

    schema = pq.read_schema(
        parquet_disponivel
    )

    colunas = set(schema.names)

    candidatas = [
        "nu_notific",
        "numero_notificacao",
        "id_notificacao",
        "id",
    ]

    coluna_id = next(
        (
            coluna
            for coluna in candidatas
            if coluna in colunas
        ),
        None,
    )

    if coluna_id is None:
        pytest.skip(
            "O Parquet nao possui uma coluna identificadora "
            "adequada para o teste de duplicidade."
        )

    df = pd.read_parquet(
        parquet_disponivel,
        columns=[coluna_id],
    )

    ids = (
        df[coluna_id]
        .dropna()
        .astype("string")
        .str.strip()
    )

    ids = ids[
        ids.ne("")
    ]

    if ids.empty:
        pytest.skip(
            f"A coluna {coluna_id} nao possui "
            "identificadores validos."
        )

    quantidade_duplicada = int(
        ids.duplicated().sum()
    )

    taxa_duplicada = (
        quantidade_duplicada
        / len(ids)
    )

    assert taxa_duplicada < 0.05, (
        "Alta taxa de identificadores duplicados em "
        f"{coluna_id}: "
        f"{quantidade_duplicada}/{len(ids)} "
        f"({taxa_duplicada:.1%})"
    )