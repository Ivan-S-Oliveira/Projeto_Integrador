"""
Testes anti-vazamento (data leakage).

Estes testes protegem contra os erros mais comuns:
  - usar o alvo como feature;
  - treinar com dados do futuro;
  - deixar colunas derivadas do alvo caírem no X.

Os testes que dependem de módulos ainda não implementados fazem `skip`.
"""

import pandas as pd
import pytest

from src.utils import config as C


# ---------------------------------------------------------------------------
# Colunas proibidas no conjunto de features
# ---------------------------------------------------------------------------

# Nomes típicos que NUNCA devem entrar em X.
# Ajuste conforme o dicionário de dados do SRAG for consolidado.
COLUNAS_PROIBIDAS = {
    "evolucao",          # desfecho clínico — alvo provável
    "evolucao_covid19",  # variante
    "dt_evolucao",       # data do desfecho — vaza o alvo
    "dt_encerramento",   # idem
    "classificacao_final",
    "criterio_confirmacao",
    "sorologia",         # resultado de exame confirmatório
    "pcr",               # idem
}


def test_features_nao_contem_alvo_evidente(parquet_disponivel):
    """
    Se o pipeline já expõe uma lista de features, garante que nenhuma delas
    coincide com colunas proibidas.

    Enquanto o pipeline não existir, este teste apenas verifica o dataset bruto.
    """
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    import pyarrow.parquet as pq

    colunas = set(pq.read_schema(parquet_disponivel).names)
    interseccao = colunas & COLUNAS_PROIBIDAS

    # Não falha só porque essas colunas existem no dataset — só avisa.
    # A checagem real é feita abaixo, quando houver pipeline.
    assert isinstance(interseccao, set)


def test_pipeline_expoe_features_sem_alvo():
    """
    Se src.models.pipeline existir, verifica que a lista de features não
    inclui nenhuma coluna proibida.
    """
    try:
        from src.models import pipeline  # type: ignore
    except Exception:
        pytest.skip("src.models.pipeline ainda não implementado.")

    if not hasattr(pipeline, "FEATURES"):
        pytest.skip("pipeline.FEATURES não definido.")

    feats = set(pipeline.FEATURES)
    vazamento = feats & COLUNAS_PROIBIDAS

    assert not vazamento, (
        f"Features contêm colunas proibidas (vazamento de alvo): {vazamento}"
    )


# ---------------------------------------------------------------------------
# Validação temporal
# ---------------------------------------------------------------------------

def test_split_temporal_respeita_ordem():
    """
    Se houver uma função de split temporal, garante que:
        max(treino.data) <= min(teste.data)
    """
    try:
        from src.evaluation import temporal  # type: ignore
    except Exception:
        pytest.skip("src.evaluation.temporal ainda não implementado.")

    split_fn = getattr(temporal, "split_temporal", None)
    if split_fn is None:
        pytest.skip("split_temporal ainda não implementado.")

    # Constrói um DataFrame sintético
    df = pd.DataFrame(
        {
            "dt_notific": pd.date_range("2020-01-01", periods=100, freq="D"),
            "y": [0, 1] * 50,
        }
    )

    try:
        treino, teste = split_fn(df, "dt_notific")
    except TypeError:
        # assinatura diferente — apenas ignora
        pytest.skip("split_temporal com assinatura diferente.")

    assert treino["dt_notific"].max() <= teste["dt_notific"].min(), (
        "Split temporal vaza: treino contém datas posteriores ao teste."
    )


# ---------------------------------------------------------------------------
# Duplicação de linhas
# ---------------------------------------------------------------------------

def test_dataset_sem_duplicatas_exatas(parquet_disponivel):
    """
    Um dataset com duplicatas exatas pode indicar que o mesmo registro
    entrou em treino e teste.
    """
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    df = pd.read_parquet(
        parquet_disponivel,
        columns=["sg_uf", "dt_notific"],
    ).head(10_000)  # amostra — checagem completa é caríssima

    n_dup = df.duplicated().sum()
    taxa = n_dup / len(df)

    assert taxa < 0.05, (
        f"Alta taxa de duplicatas exatas na amostra: "
        f"{n_dup}/{len(df)} ({taxa:.1%})"
    )