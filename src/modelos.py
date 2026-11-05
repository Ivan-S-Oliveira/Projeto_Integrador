"""Pipelines, modelos e calibração."""

from __future__ import annotations

import logging
from typing import Iterable, Literal, cast, Any, get_args
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.dummy import DummyClassifier
from importlib import metadata
from packaging.version import Version
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, roc_auc_score
import inspect
import warnings

from src import config as C
from src.avaliacao import metricas_completas, metricas_por_limiar


# --- pipeline ---

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


SaidaPreprocessador = Literal["esparsa", "ordinal"]


def _para_float32() -> FunctionTransformer:
    return FunctionTransformer(
        lambda values: values.astype(np.float32),
        feature_names_out="one-to-one",
    )


def _normalizar_ausentes_categoricos(
    values: pd.DataFrame,
) -> pd.DataFrame:
    """Converte ausências pandas em valores aceitos pelo scikit-learn."""

    normalized = values.astype("object")
    return normalized.where(
        pd.notna(normalized),
        np.nan,
    )


def _normalizador_categorico() -> FunctionTransformer:
    """Cria a transformação aplicada antes da imputação categórica."""

    return FunctionTransformer(
        _normalizar_ausentes_categoricos,
        feature_names_out="one-to-one",
    )


def build_preprocessor(
    numericas: Iterable[str] | None = None,
    categoricas: Iterable[str] | None = None,
    *,
    saida: SaidaPreprocessador = "esparsa",
) -> ColumnTransformer:
    """Constrói o pré-processamento central dos modelos supervisionados."""
    num = list(numericas) if numericas is not None else list(FEATURES_NUMERICAS)
    cat = list(categoricas) if categoricas is not None else list(FEATURES_CATEGORICAS)

    imputer_categorico = SimpleImputer(
        strategy="constant",
        fill_value=AUSENTE,
    )

    if saida == "esparsa":
        pipe_num = Pipeline(
            steps=[
                ("float32", _para_float32()),
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler(with_mean=False)),
            ]
        )
        pipe_cat = Pipeline(
            steps=[
                (
                    "normalizar_ausentes",
                    _normalizador_categorico(),
                ),
                (
                    "imputer",
                    imputer_categorico,
                ),
                (
                    "encoder",
                    OneHotEncoder(
                        handle_unknown="ignore",
                        sparse_output=True,
                        dtype=np.float32,
                    ),
                ),
            ]
        )
    elif saida == "ordinal":
        pipe_num = Pipeline(
            steps=[
                ("float32", _para_float32()),
                ("imputer", SimpleImputer(strategy="median")),
            ]
        )
        pipe_cat = Pipeline(
            steps=[
                (
                    "normalizar_ausentes",
                    _normalizador_categorico(),
                ),
                (
                    "imputer",
                    imputer_categorico,
                ),
                (
                    "encoder",
                    OrdinalEncoder(
                        handle_unknown="use_encoded_value",
                        unknown_value=np.nan,
                        dtype=np.float32,
                    ),
                ),
            ]
        )
    else:
        raise ValueError(
            f"saida inválida: {saida!r}. Use 'esparsa' ou 'ordinal'."
        )

    return ColumnTransformer(
        transformers=[
            ("num", pipe_num, num),
            ("cat", pipe_cat, cat),
        ],
        remainder="drop",
        sparse_threshold=1.0 if saida == "esparsa" else 0.0,
        verbose_feature_names_out=False,
    )

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

    - ``classifier=None`` → devolve só o pré-processamento (útil no notebook 06).
    - ``classifier`` passado (notebook 07+) → anexa como etapa final.
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


# --- baseline ---

DummyStrategy = Literal[
    "most_frequent",
    "prior",
    "stratified",
    "uniform",
    "constant",
]


def build_baseline_pipeline(
    *,
    strategy: DummyStrategy = "prior",
    preprocessor=None,
) -> Pipeline:
    """``Pipeline`` com pré-processamento + ``DummyClassifier``.

    Estratégias mais úteis como piso:

    - ``"prior"``         → probabilidade constante = prevalência do treino
      (AUC ≈ 0.5 por construção; Brier ainda informativo);
    - ``"most_frequent"`` → sempre a classe majoritária
      (F1/recall = 0 se a positiva for minoria);
    - ``"stratified"``    → amostra respeitando o prior.

    ``preprocessor=None`` usa ``build_preprocessor()``.
    """
    pre = preprocessor if preprocessor is not None else build_preprocessor()

    return Pipeline([
        ("pre", pre),
        ("clf", DummyClassifier(
            strategy=strategy,
            random_state=random_state(),
        )),
    ])


# --- logistic ---

Solver  = Literal["lbfgs", "liblinear", "newton-cg", "newton-cholesky", "sag", "saga"]
Penalty = Literal["l1", "l2", "elasticnet"]

_L1_RATIO_SOLVERS: dict[str, frozenset[str]] = {
    "l2":         frozenset({"lbfgs", "liblinear", "newton-cg", "newton-cholesky", "sag", "saga"}),
    "l1":         frozenset({"liblinear", "saga"}),
    "elasticnet": frozenset({"saga"}),
}

_PENALTIES_VALIDAS = ("l1", "l2", "elasticnet")

SKLEARN_L1_RATIO_MIN = "1.8"


def _verificar_sklearn_minima() -> None:
    """Levanta ``RuntimeError`` se scikit-learn for anterior a 1.8.

    Versões anteriores ignoram ``l1_ratio`` em ``LogisticRegression``:
    ``penalty: l1`` do YAML viraria L2 sem aviso.
    """
    try:
        instalada = metadata.version("scikit-learn")
    except metadata.PackageNotFoundError as exc:
        raise RuntimeError(
            f"scikit-learn>={SKLEARN_L1_RATIO_MIN} é necessário; "
            "nenhuma versão instalada. "
            f"Instale com: pip install \"scikit-learn>={SKLEARN_L1_RATIO_MIN}\""
        ) from exc

    if Version(instalada) < Version(SKLEARN_L1_RATIO_MIN):
        raise RuntimeError(
            f"scikit-learn>={SKLEARN_L1_RATIO_MIN} é necessário "
            f"(instalado: {instalada}). "
            "A API de l1_ratio só existe a partir da 1.8; versões "
            "anteriores ignoram o parâmetro silenciosamente. "
            f"Atualize: pip install \"scikit-learn>={SKLEARN_L1_RATIO_MIN}\""
        )


def _penalty_do_yaml() -> Penalty | None:
    """Lê ``models.logistic.penalty`` do YAML.

    Devolve ``None`` quando a chave está ausente, vazia ou nula — o
    ``l1_ratio`` passado explicitamente é usado sem alteração. Levanta
    ``ValueError`` se a chave existir mas tiver valor desconhecido.
    """
    valor = C.cfg("models", "logistic", "penalty")
    if not valor:
        return None
    if valor not in _PENALTIES_VALIDAS:
        raise ValueError(
            f"models.logistic.penalty inválido: {valor!r}. "
            f"Use uma de {_PENALTIES_VALIDAS}."
        )
    return cast(Penalty, valor)


def _tipo_penalidade(l1_ratio: float) -> str:
    """Classifica o ``l1_ratio`` em ``"l2"``, ``"l1"`` ou ``"elasticnet"``."""
    if l1_ratio == 0.0:
        return "l2"
    if l1_ratio == 1.0:
        return "l1"
    return "elasticnet"


def build_logistic_pipeline(
    *,
    C: float = 1.0,
    l1_ratio: float = 0.0,
    penalty: Penalty | None = None,
    solver: Solver = "lbfgs",
    max_iter: int = 1000,
    class_weight: str | dict | None = "balanced",
    preprocessor=None,
) -> Pipeline:
    """``Pipeline`` de pré-processamento + ``LogisticRegression``.

    ``penalty=None`` (default) lê ``models.logistic.penalty`` do YAML.
    Quando definido, sobrepõe ``l1_ratio``:

    - ``"l2"``          → força ``l1_ratio=0.0``;
    - ``"l1"``          → força ``l1_ratio=1.0``;
    - ``"elasticnet"``  → exige ``0 < l1_ratio < 1``.

    ``l1_ratio`` (0..1) só tem efeito quando ``penalty`` é ``None`` ou
    ``"elasticnet"``. O ``solver`` precisa ser compatível com o tipo
    resultante (ver ``_L1_RATIO_SOLVERS``).

    Levanta ``RuntimeError`` se scikit-learn for anterior a 1.8, e
    ``ValueError`` para ``l1_ratio`` fora de ``[0, 1]``, combinação
    ``solver`` × tipo inválida, ou ``penalty="elasticnet"`` com
    ``l1_ratio`` nos extremos.
    """
    _verificar_sklearn_minima()

    if not 0.0 <= l1_ratio <= 1.0:
        raise ValueError(
            f"l1_ratio deve estar em [0, 1]; "
            f"recebido {l1_ratio!r}."
        )

    penalty_configurada = penalty

    if penalty_configurada is None and l1_ratio == 0.0:
        penalty_configurada = _penalty_do_yaml()

    if penalty_configurada == "l2":
        l1_ratio = 0.0

    elif penalty_configurada == "l1":
        l1_ratio = 1.0

    elif penalty_configurada == "elasticnet":
        if not 0.0 < l1_ratio < 1.0:
            raise ValueError(
                "penalty='elasticnet' requer "
                "0 < l1_ratio < 1; "
                f"recebido l1_ratio={l1_ratio!r}."
            )

    tipo            = _tipo_penalidade(l1_ratio)
    solvers_validos = _L1_RATIO_SOLVERS[tipo]
    if solver not in solvers_validos:
        raise ValueError(
            f"combinação inválida: l1_ratio={l1_ratio!r} ({tipo}) "
            f"com solver={solver!r}. Use um destes: {sorted(solvers_validos)}."
        )

    pre = preprocessor if preprocessor is not None else build_preprocessor()

    return Pipeline([
        ("pre", pre),
        ("clf", LogisticRegression(
            C=C,
            l1_ratio=l1_ratio,
            solver=solver,
            max_iter=max_iter,
            class_weight=class_weight,
            random_state=random_state(),
        )),
    ])


# --- boosting ---

def build_boosting_pipeline(
    learning_rate: float = 0.08,
    max_iter: int = 150,
    max_depth: int | None = None,
    max_leaf_nodes: int = 31,
    min_samples_leaf: int = 100,
    l2_regularization: float = 0.10,
    early_stopping: bool = True,
    validation_fraction: float = 0.1,
    n_iter_no_change: int = 20,
    class_weight: str | dict | None = "balanced",
    preprocessor=None,
) -> Pipeline:
    """Constrói o pipeline ordinal do HistGradientBoostingClassifier."""

    categorical_features = None

    if preprocessor is None:
        preprocessor = build_preprocessor(
            numericas=FEATURES_NUMERICAS,
            categoricas=FEATURES_CATEGORICAS,
            saida="ordinal",
        )

        categorical_features = [
            False
            for _ in FEATURES_NUMERICAS
        ]

        categorical_features.extend(
            True
            for _ in FEATURES_CATEGORICAS
        )

    if categorical_features is not None:
        quantidade_features_esperada = sum(
            (
                len(FEATURES_NUMERICAS),
                len(FEATURES_CATEGORICAS),
            )
        )

        if len(categorical_features) != quantidade_features_esperada:
            raise RuntimeError(
                "A máscara categórica não possui o mesmo tamanho "
                "do contrato de features."
            )

    classificador = HistGradientBoostingClassifier(
        learning_rate=learning_rate,
        max_iter=max_iter,
        max_depth=max_depth,
        max_leaf_nodes=max_leaf_nodes,
        min_samples_leaf=min_samples_leaf,
        l2_regularization=l2_regularization,
        early_stopping=early_stopping,
        validation_fraction=validation_fraction,
        n_iter_no_change=n_iter_no_change,
        class_weight=class_weight,
        categorical_features=categorical_features,
        random_state=random_state(),
    )

    return Pipeline(
        steps=[
            ("pre", preprocessor),
            ("clf", classificador),
        ]
    )


# --- calibration ---

Metrica          = Literal["f1", "precision", "recall", "accuracy", "youden_j"]
MetodoCalibracao = Literal["isotonic", "sigmoid"]

_METRICAS_VALIDAS = frozenset(get_args(Metrica))
_METODOS_VALIDOS  = frozenset(get_args(MetodoCalibracao))


def calibrar(
    pipeline,
    X_cal: pd.DataFrame,
    y_cal: pd.Series,
    *,
    method: MetodoCalibracao = "isotonic",
):
    """Ajusta um ``CalibratedClassifierCV`` sobre um pipeline congelado.

    Use uma base de calibração distinta do treino do ``pipeline``. O
    pipeline não é re-treinado — o calibrador aprende só o mapeamento
    probabilidade → probabilidade.

    ``"isotonic"`` é não-paramétrico (requer mais dados); ``"sigmoid"``
    (Platt) é paramétrico e mais estável em amostras pequenas.

    Levanta ``RuntimeError`` se ``sklearn.frozen`` não estiver disponível
    (scikit-learn anterior a 1.6).
    """
    if method not in _METODOS_VALIDOS:
        raise ValueError(
            f"method inválido: {method!r}. Use {sorted(_METODOS_VALIDOS)}."
        )

    try:
        from sklearn.frozen import FrozenEstimator
    except ImportError as exc:
        try:
            instalada = metadata.version("scikit-learn")
        except metadata.PackageNotFoundError:
            instalada = "não instalado"

        raise RuntimeError(
            "calibrar() requer scikit-learn>=1.6 (FrozenEstimator); "
            f"o projeto exige >=1.8. Versão instalada: {instalada}. "
            "Atualize: pip install \"scikit-learn>=1.8\""
        ) from exc

    modelo = CalibratedClassifierCV(
        estimator=FrozenEstimator(pipeline),
        method=method,
    )
    modelo.fit(X_cal, y_cal)
    return modelo


def escolher_limiar(
    y_true: pd.Series | np.ndarray,
    y_prob: pd.Series | np.ndarray,
    *,
    metrica: Metrica = "f1",
    n_limiares: int = 101,
    min_precision: float | None = None,
    min_recall: float | None = None,
) -> dict[str, Any]:
    """Devolve o limiar ótimo segundo ``metrica`` e um resumo associado.

    Restrições opcionais de ``min_precision`` / ``min_recall`` filtram
    candidatos antes de maximizar ``metrica``; se nada sobrar, levanta
    ``ValueError``.

    Retorna dict com ``limiar``, ``valor`` (da métrica escolhida),
    ``metrica``, ``auc``, ``brier`` e ``tabela`` (grade completa de
    ``metricas_por_limiar``).
    """
    if metrica not in _METRICAS_VALIDAS:
        raise ValueError(
            f"metrica inválida: {metrica!r}. Use {sorted(_METRICAS_VALIDAS)}."
        )

    y_true_arr = np.asarray(y_true).ravel().astype(int)
    y_prob_arr = np.asarray(y_prob).ravel()

    tabela = metricas_por_limiar(y_true_arr, y_prob_arr, n_limiares=n_limiares)

    candidatos = tabela
    filtros: list[str] = []
    if min_precision is not None:
        filtros.append(f"precision ≥ {min_precision}")
        candidatos = candidatos[candidatos["precision"] >= min_precision]
    if min_recall is not None:
        filtros.append(f"recall ≥ {min_recall}")
        candidatos = candidatos[candidatos["recall"] >= min_recall]
    if candidatos.empty:
        restricao = " e ".join(filtros) if filtros else "sem restrição"
        raise ValueError(f"Nenhum limiar atende à(s) restrição(ões): {restricao}.")

    if metrica not in candidatos.columns:
        raise ValueError(
            f"A métrica {metrica!r} não foi produzida por metricas_por_limiar. "
            f"Colunas disponíveis: {sorted(candidatos.columns)}"
        )

    idx_melhor   = candidatos[metrica].idxmax()
    linha_melhor = tabela.loc[[idx_melhor]].iloc[0]

    return {
        "limiar":  float(linha_melhor["limiar"]),
        "valor":   float(linha_melhor[metrica]),
        "metrica": metrica,
        "auc":     float(roc_auc_score(y_true_arr, y_prob_arr)),
        "brier":   float(brier_score_loss(y_true_arr, y_prob_arr)),
        "tabela":  tabela,
    }


# --- factory ---

Finalista = Literal["boosting", "logistic"]
_FINALISTAS_VALIDOS = frozenset(get_args(Finalista))

_FINALISTA_ALIASES: dict[str, str] = {
    "hist_gradient_boosting": "boosting",
}

_CONSTRUTORES: dict[str, Any] = {
    "boosting": build_boosting_pipeline,
    "logistic": build_logistic_pipeline,
}


def finalistas_aceitos() -> tuple[str, ...]:
    """Nomes canônicos + apelidos aceitos por ``build_finalista``."""
    return tuple(sorted(_FINALISTAS_VALIDOS | set(_FINALISTA_ALIASES)))


def resolver_finalista(nome: str) -> str:
    """Devolve o nome canônico para ``nome`` (que pode ser um apelido)."""
    return _FINALISTA_ALIASES.get(nome, nome)


def _kwargs_do_yaml(nome: str) -> dict[str, Any]:
    """Lê ``models.<nome>`` do YAML e devolve só kwargs aceitos pelo construtor.

    Filtra: chaves ``busca_*``, valores ``None`` e chaves que o construtor
    não reconhece (administrativas ou typos), avisando via ``RuntimeWarning``.
    """
    secao = C.cfg("models", nome)
    if not isinstance(secao, dict):
        return {}

    construtor = _CONSTRUTORES.get(nome)
    if construtor is None:
        return {}

    aceitos = set(inspect.signature(construtor).parameters)
    filtrados: dict[str, Any] = {}
    ignoradas: list[str] = []

    for chave, valor in secao.items():
        if chave.startswith("busca_") or valor is None:
            continue
        if chave in aceitos:
            filtrados[chave] = valor
        else:
            ignoradas.append(chave)

    if ignoradas:
        warnings.warn(
            f"models.{nome}: chave(s) ignorada(s) — não aceita(s) por "
            f"{construtor.__name__}: {sorted(ignoradas)}. "
            f"Aceitas: {sorted(aceitos)}.",
            RuntimeWarning,
            stacklevel=3,
        )

    return filtrados


def build_finalista(
    nome: str,
    *,
    preprocessor=None,
    **overrides: Any,
) -> Pipeline:
    """Constrói o ``Pipeline`` de um finalista pelo nome ou apelido.

    Levanta ``ValueError`` se ``nome`` (após normalização) for desconhecido.
    O ``Pipeline`` devolvido não está ajustado — o caller faz ``fit``.
    """
    nome = resolver_finalista(nome)

    if nome not in _FINALISTAS_VALIDOS:
        raise ValueError(
            f"finalista desconhecido: {nome!r}. "
            f"Use um destes: {sorted(_FINALISTAS_VALIDOS | set(_FINALISTA_ALIASES))}."
        )

    params = _kwargs_do_yaml(nome) | overrides
    if preprocessor is not None:
        params["preprocessor"] = preprocessor

    return _CONSTRUTORES[nome](**params)
