"""
Fundação dos modelos supervisionados.

Fonte única de verdade para o pré-processamento e para a derivação do
alvo binário a partir de ``evolucao``, além da leitura da config canônica
(``configs/supervised.yaml``) e da conveniência ``build_pipeline``.

Notebooks e demais modelos devem importar este módulo em vez de
reimplementar o pré-processamento.
"""

from __future__ import annotations

import logging
from typing import Iterable
from typing import Iterable, Literal

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    FunctionTransformer,
    OneHotEncoder,
    OrdinalEncoder,
    StandardScaler,
)
from src.utils import config as C

__all__ = [
    "ALVO",
    "AUSENTE",
    "COLUNA_TEMPO",
    "FEATURES",
    "FEATURES_CATEGORICAS",
    "FEATURES_NUMERICAS",
    "build_pipeline",
    "build_preprocessor",
    "criar_alvo_binario",
    "filtrar_rotulos_validos",
    "random_state",
]

logger = logging.getLogger(__name__)

# Sem defaults próprios: se a config falhar, o import falha — decisão
# deliberada para que um YAML inválido impeça a modelagem cedo.
ALVO: str = C.cfg("target", "coluna")
COLUNA_TEMPO: str = C.cfg("coluna_tempo")

FEATURES_NUMERICAS: list[str] = list(C.cfg("features", "numericas") or [])
FEATURES_CATEGORICAS: list[str] = list(C.cfg("features", "categoricas") or [])

AUSENTE: str = C.cfg("missingness", "categoricas", "valor_ausente")

if _final := C.cfg("features", "final"):
    _fs = set(_final)
    FEATURES_NUMERICAS = [c for c in FEATURES_NUMERICAS if c in _fs]
    FEATURES_CATEGORICAS = [c for c in FEATURES_CATEGORICAS if c in _fs]

FEATURES: list[str] = FEATURES_NUMERICAS + FEATURES_CATEGORICAS


def _alvo_cfg_positivos() -> list[float]:
    """Códigos de ``target.positivos`` do YAML, como floats."""
    return [float(v) for v in (C.cfg("target", "positivos") or [])]


def _alvo_cfg_negativos() -> list[float]:
    """Códigos de ``target.negativos`` do YAML, como floats."""
    return [float(v) for v in (C.cfg("target", "negativos") or [])]


# SUBSTITUA build_preprocessor EM src/models/pipeline.py.
# Garanta também os imports: Literal, numpy as np, FunctionTransformer, OrdinalEncoder.
SaidaPreprocessador = Literal["esparsa", "ordinal"]

def build_preprocessor(numericas=None,categoricas=None,*,saida: SaidaPreprocessador="esparsa"):
    num=list(numericas) if numericas is not None else FEATURES_NUMERICAS
    cat=list(categoricas) if categoricas is not None else FEATURES_CATEGORICAS
    pipe_num=Pipeline([("imputer",SimpleImputer(strategy="median")),
                       ("scaler",StandardScaler(with_mean=False) if saida=="esparsa" else StandardScaler())])
    if saida=="esparsa":
        pipe_cat=Pipeline([("imputer",SimpleImputer(strategy="constant",fill_value=AUSENTE)),
                           ("encoder",OneHotEncoder(handle_unknown="ignore",sparse_output=True,dtype=np.float32))])
    elif saida=="ordinal":
        pipe_cat=Pipeline([("imputer",SimpleImputer(strategy="constant",fill_value=AUSENTE)),
                           ("encoder",OrdinalEncoder(handle_unknown="use_encoded_value",unknown_value=np.nan,dtype=np.float32))])
    else: raise ValueError("saida deve ser 'esparsa' ou 'ordinal'")
    return ColumnTransformer([("num",pipe_num,num),("cat",pipe_cat,cat)],remainder="drop",
                             sparse_threshold=1.0 if saida=="esparsa" else 0.0,
                             verbose_feature_names_out=False)



def criar_alvo_binario(
    df: pd.DataFrame,
    alvo: str | None = None,
    positivos: Iterable[float] | None = None,
    negativos: Iterable[float] | None = None,
) -> pd.Series:
    """Converte ``evolucao`` em alvo binário (``float64``, NaN onde indefinido).

    ``1`` = óbito SRAG (``target.positivos`` do YAML), ``0`` = cura
    (``target.negativos``). Qualquer outro valor (``3.0``, ``9.0``, nulos)
    vira ``NaN`` — descartado adiante por ``filtrar_rotulos_validos``.

    Argumentos explícitos sobrepõem o YAML. Levanta ``ValueError`` se os
    conjuntos se sobrepuserem ou se algum estiver vazio.
    """
    alvo = alvo if alvo is not None else ALVO

    positivos_set = {
        float(v) for v in (positivos if positivos is not None else _alvo_cfg_positivos())
    }
    negativos_set = {
        float(v) for v in (negativos if negativos is not None else _alvo_cfg_negativos())
    }

    if overlap := positivos_set & negativos_set:
        raise ValueError(
            f"`positivos` e `negativos` não podem se sobrepor: {sorted(overlap)}"
        )
    if not positivos_set:
        raise ValueError("`target.positivos` está vazio na config.")
    if not negativos_set:
        raise ValueError("`target.negativos` está vazio na config.")

    valores = df[alvo].astype("float64")
    y = pd.Series(float("nan"), index=df.index, dtype="float64")
    y[valores.isin(negativos_set)] = 0
    y[valores.isin(positivos_set)] = 1
    return y


def filtrar_rotulos_validos(
    X: pd.DataFrame,
    y: pd.Series,
) -> tuple[pd.DataFrame, pd.Series]:
    """Remove linhas em que ``y`` é NaN. Devolve ``(X, y)`` alinhados (int8)."""
    if not y.index.equals(X.index):
        raise ValueError("X e y precisam ter o mesmo índice.")

    mascara = y.notna()
    return (
        X.loc[mascara].reset_index(drop=True),
        y.loc[mascara].astype("int8").reset_index(drop=True),
    )


def random_state() -> int:
    """Seed canônica do projeto (``config.SEED``)."""
    return int(C.SEED)


def build_pipeline(
    X: pd.DataFrame | None = None,
    y: pd.Series | None = None,
    *,
    classifier: object | None = None,
    features: Iterable[str] | None = None,
    strict: bool = True,
) -> Pipeline:
    """Constrói o ``Pipeline`` sklearn.

    - ``classifier=None`` → devolve só o pré-processamento (útil no C2).
    - ``classifier`` passado (C3+) → anexa como etapa final.
    - ``features=None`` → usa ``FEATURES`` do módulo.
    - ``strict=True`` → levanta ``KeyError`` se alguma feature configurada
      estiver ausente em ``X``; ``False`` → emite warning e segue só com
      as presentes.
    """
    num = list(FEATURES_NUMERICAS)
    cat = list(FEATURES_CATEGORICAS)

    if features is not None:
        fs = set(features)
        num = [c for c in num if c in fs]
        cat = [c for c in cat if c in fs]

    if X is not None:
        if ausentes := sorted((set(num) | set(cat)) - set(X.columns)):
            msg = (
                f"Features configuradas ausentes em X: {ausentes}. "
                "Verifique `features` no supervised.yaml ou o DataFrame "
                "de entrada."
            )
            if strict:
                raise KeyError(msg)
            logger.warning(msg)
            num = [c for c in num if c in X.columns]
            cat = [c for c in cat if c in X.columns]

    pre = build_preprocessor(numericas=num, categoricas=cat)

    etapas: list[tuple[str, object]] = [("pre", pre)]
    if classifier is not None:
        etapas.append(("clf", classifier))

    return Pipeline(etapas)