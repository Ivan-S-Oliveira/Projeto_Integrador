"""
Fundação dos modelos supervisionados.
...
"""

from __future__ import annotations

import logging
from typing import Iterable

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.utils import config as C

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fonte única da verdade — tudo vem de `configs/supervised.yaml`
# ---------------------------------------------------------------------------
# Sem defaults próprios neste módulo: se a config falhar, o import falha.

ALVO: str = C.cfg("target", "coluna")
COLUNA_TEMPO: str = C.cfg("coluna_tempo")

FEATURES_NUMERICAS: list[str] = list(C.cfg("features", "numericas") or [])
FEATURES_CATEGORICAS: list[str] = list(C.cfg("features", "categoricas") or [])

# Se `features.final` estiver preenchido no YAML, restringe as listas a ele.
_final = C.cfg("features", "final")
if _final:
    _fs = set(_final)
    FEATURES_NUMERICAS = [c for c in FEATURES_NUMERICAS if c in _fs]
    FEATURES_CATEGORICAS = [c for c in FEATURES_CATEGORICAS if c in _fs]

FEATURES: list[str] = FEATURES_NUMERICAS + FEATURES_CATEGORICAS


def _alvo_cfg_positivos() -> list[float]:
    return [float(v) for v in (C.cfg("target", "positivos") or [])]


def _alvo_cfg_negativos() -> list[float]:
    return [float(v) for v in (C.cfg("target", "negativos") or [])]


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
    alvo: str | None = None,
    positivos: Iterable[float] | None = None,
    negativos: Iterable[float] | None = None,
) -> pd.Series:
    """
    Converte `evolucao` em alvo binário (float64, com NaN onde indefinido).

        1 = óbito SRAG   (valores em `positivos`, default do YAML)
        0 = cura         (valores em `negativos`, default do YAML)
        NaN = qualquer outro valor (3.0, 9.0, nulos) → descartado adiante
              por `filtrar_rotulos_validos`.

    Por padrão, lê `target.coluna`, `target.positivos` e `target.negativos`
    do `supervised.yaml`. Argumentos explícitos sobrepõem a config.

    Parâmetros
    ----------
    alvo : str | None
        Coluna de `df` usada como rótulo. Se None, usa `ALVO` (config).
    positivos : iterable de float | None
        Códigos que contam como positivo. Se None, lê do YAML.
    negativos : iterable de float | None
        Códigos que contam como negativo. Se None, lê do YAML.

    Retorna
    -------
    pd.Series dtype float64 (usa NaN para indefinidos).
    """
    alvo = alvo if alvo is not None else ALVO

    positivos_set = {
        float(v) for v in (positivos if positivos is not None else _alvo_cfg_positivos())
    }
    negativos_set = {
        float(v) for v in (negativos if negativos is not None else _alvo_cfg_negativos())
    }

    if positivos_set & negativos_set:
        raise ValueError(
            "`positivos` e `negativos` não podem se sobrepor: "
            f"{sorted(positivos_set & negativos_set)}"
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
    """Remove linhas em que y é NaN. Retorna X, y alinhados (int8)."""
    if not y.index.equals(X.index):
        raise ValueError("X e y precisam ter o mesmo índice.")

    mascara = y.notna()
    X_ok = X.loc[mascara].reset_index(drop=True)
    y_ok = y.loc[mascara].astype("int8").reset_index(drop=True)
    return X_ok, y_ok


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


# ---------------------------------------------------------------------------
# Pipeline completo (pré-processamento + classificador opcional)
# ---------------------------------------------------------------------------

def build_pipeline(
    X: pd.DataFrame | None = None,
    y: pd.Series | None = None,
    *,
    classifier: object | None = None,
    features: Iterable[str] | None = None,
    strict: bool = True,
) -> Pipeline:
    """
    Constrói o Pipeline sklearn.

    - Se `classifier` for None, devolve só o pré-processamento (útil no C2,
      que só inspeciona o pipeline).
    - Se `classifier` for passado (C3+), anexa como etapa final.
    - `features`: se None, usa `FEATURES` do módulo (que vem do YAML).
    - `strict`: se True (default), levanta `KeyError` quando alguma feature
      configurada estiver ausente em `X`. Se False, emite warning e segue
      apenas com as features presentes.

    As listas numéricas/categóricas vêm do `supervised.yaml`; se `X` for
    passado, é feita uma verificação de presença das colunas.
    """
    num = list(FEATURES_NUMERICAS)
    cat = list(FEATURES_CATEGORICAS)

    if features is not None:
        fs = set(features)
        num = [c for c in num if c in fs]
        cat = [c for c in cat if c in fs]

    if X is not None:
        ausentes = sorted((set(num) | set(cat)) - set(X.columns))
        if ausentes:
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