"""
Fundação dos modelos supervisionados.
...
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.utils import config as C

# ---------------------------------------------------------------------------
# Fonte única da verdade
# ---------------------------------------------------------------------------

FEATURES_NUMERICAS: list[str] = [
    "nu_idade_n",
]

FEATURES_CATEGORICAS: list[str] = [
    "sg_uf",
    "cs_sexo",
    "tp_gestante",
    "febre",
    "tosse",
    "dispneia",
    "saturacao",
    "internado",
    "utilizouvni",
    "vacina_cov",
]

FEATURES: list[str] = FEATURES_NUMERICAS + FEATURES_CATEGORICAS

COLUNA_TEMPO: str = "dt_notific"
ALVO: str = "evolucao"

# Valores de `evolucao` que contam como "óbito" no alvo binário.
#   1.0 = Cura | 2.0 = Óbito por SRAG | 3.0 = Óbito por outras causas | 9 = Ignorado
ALVO_POSITIVO: list[float] = [2.0]

# Códigos de `evolucao` que jamais viram rótulo (nem 0 nem 1).
ALVO_IGNORADO: set[float] = {9.0}


# ---------------------------------------------------------------------------
# Pré-processador
# ---------------------------------------------------------------------------

def build_preprocessor(
    numericas: Iterable[str] | None = None,
    categoricas: Iterable[str] | None = None,
) -> ColumnTransformer:
    num = list(numericas) if numericas is not None else FEATURES_NUMERICAS
    cat = list(categoricas) if categoricas is not None else FEATURES_CATEGORICAS

    pipe_num = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    pipe_cat = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    return ColumnTransformer(
        transformers=[
            ("num", pipe_num, num),
            ("cat", pipe_cat, cat),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


# ---------------------------------------------------------------------------
# Alvo binário
# ---------------------------------------------------------------------------

def criar_alvo_binario(
    df: pd.DataFrame,
    alvo: str = ALVO,
    positivos: Iterable[float] = ALVO_POSITIVO,
    ignorados: Iterable[float] = ALVO_IGNORADO,
    *,
    descartar_nao_rotulados: bool = True,
) -> pd.Series:
    """
    Converte `evolucao` em alvo binário (float64, com NaN onde indefinido).

        1 = óbito SRAG   (valores em `positivos`)
        0 = cura         (valor 1.0)
        NaN = qualquer outro valor (3.0, 9.0, ...) → será descartado em
              `filtrar_rotulos_validos` se `descartar_nao_rotulados=True`.

    Parâmetros
    ----------
    positivos : iterable de float
        Códigos de `evolucao` que contam como positivo (default {2.0}).
    ignorados : iterable de float
        Códigos que sabemos serem "ignorado" (default {9.0}). Servem apenas
        para documentação/estatística; o comportamento é o mesmo dos demais
        não-rotulados.
    descartar_nao_rotulados : bool
        Se False, mantém os NaN (o chamador decide o que fazer). Se True,
        eles permanecem como NaN e serão removidos adiante.

    Retorna
    -------
    pd.Series dtype float64 (usa NaN para indefinidos).
    """
    positivos_set = {float(v) for v in positivos}
    ignorados_set = {float(v) for v in ignorados}

    if positivos_set & {1.0}:
        raise ValueError("`positivos` não pode conter 1.0 (reservado para 'cura').")

    valores = df[alvo].astype("float64")

    y = pd.Series(float("nan"), index=df.index, dtype="float64")
    y[valores == 1.0] = 0
    y[valores.isin(positivos_set)] = 1

    # 3.0, 9.0, NaN, ... continuam NaN por construção — nada a fazer aqui.
    # `ignorados_set` é mantido só para eventuais relatórios/asserts.
    _ = ignorados_set  # noqa: F841 (documenta a intenção)

    if not descartar_nao_rotulados:
        # Mantém o NaN explícito — útil se o chamador quiser inspecionar.
        pass

    return y


def filtrar_rotulos_validos(
    X: pd.DataFrame,
    y: pd.Series,
) -> tuple[pd.DataFrame, pd.Series]:
    """Remove linhas em que y é NaN. Retorna X, y alinhados (int8)."""
    if not y.index.equals(X.index):
        raise ValueError("X e y precisam ter o mesmo índice.")

    mascara = y.notna()
    X_ok = X.loc[mascara].reset_index(drop=True)
    y_ok = y.loc[mascara].astype("int8").reset_index(drop=True)
    return X_ok, y_ok


# ---------------------------------------------------------------------------
# Split temporal
# ---------------------------------------------------------------------------

def split_temporal(
    df: pd.DataFrame,
    coluna_tempo: str = COLUNA_TEMPO,
    frac_treino: float = 0.8,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split temporal **sem embaralhar** (treino = mais antigo, teste = recente).

    Garante `max(treino[coluna_tempo]) <= min(teste[coluna_tempo])` **desde que
    não haja timestamps duplicados exatamente na fronteira** (nesse caso, uma
    ou outra linha pode empatar).
    """
    if not 0.0 < frac_treino < 1.0:
        raise ValueError("frac_treino deve estar em (0, 1).")

    if coluna_tempo not in df.columns:
        raise KeyError(f"Coluna temporal ausente: {coluna_tempo!r}")

    ordenado = df.sort_values(coluna_tempo, kind="mergesort").reset_index(drop=True)
    n = len(ordenado)
    corte = int(n * frac_treino)

    treino = ordenado.iloc[:corte].reset_index(drop=True)
    teste = ordenado.iloc[corte:].reset_index(drop=True)
    return treino, teste


# ---------------------------------------------------------------------------
# Conveniência
# ---------------------------------------------------------------------------

def separar_xy(
    df: pd.DataFrame,
    features: Iterable[str] | None = None,
) -> tuple[pd.DataFrame, pd.Series]:
    feats = list(features) if features is not None else FEATURES

    faltando = [c for c in feats if c not in df.columns]
    if faltando:
        raise KeyError(f"Features ausentes no DataFrame: {faltando}")

    X = df[feats].copy()
    y = criar_alvo_binario(df)
    return filtrar_rotulos_validos(X, y)


def random_state() -> int:
    """Seed canônica do projeto (vem de `config.SEED`)."""
    return int(C.SEED)