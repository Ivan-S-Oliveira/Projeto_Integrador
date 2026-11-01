"""Pré-processamento para agrupamento (clustering) das fichas de SRAG.

Numéricas: mediana e padronização. Categóricas: resposta vazia vira a categoria
explícita ``AUSENTE`` e, depois, one-hot esparso em que cada variável pesa
1/sqrt(k), com k igual ao número de categorias da variável. Assim, uma variável
com muitas categorias não domina a distância só por ter mais colunas.

As numéricas padronizadas têm variância 1, bem acima da variância de uma variável
categórica ponderada. Por isso, por padrão, cada numérica é multiplicada por um
peso que iguala a sua variância à variância média de uma variável categórica.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.models.pipeline import _normalizador_categorico

__all__ = ["OneHotPonderado", "PreprocessadorClustering", "construir_preprocessador_clustering"]


class OneHotPonderado(BaseEstimator, TransformerMixin):
    """One-hot esparso em que cada variável pesa 1/sqrt(k) (k = categorias da variável)."""

    def fit(self, X, y=None):
        self.encoder_ = OneHotEncoder(handle_unknown="ignore", dtype=np.float32, sparse_output=True).fit(X)
        pesos = [np.full(len(categorias), 1.0 / np.sqrt(len(categorias)), dtype=np.float32)
                 for categorias in self.encoder_.categories_]
        self.pesos_ = np.concatenate(pesos)
        return self

    def transform(self, X):
        codificado = sparse.csr_matrix(self.encoder_.transform(X))
        return (codificado @ sparse.diags(self.pesos_, dtype=np.float32)).tocsr()

    def get_feature_names_out(self, input_features=None):
        return self.encoder_.get_feature_names_out(input_features)


class PreprocessadorClustering(BaseEstimator, TransformerMixin):
    """Numéricas e categóricas lado a lado, em uma matriz esparsa.

    Com ``equilibrar_numericas=True``, cada numérica é multiplicada por ``peso_numericas_``, a raiz da
    variância média de uma variável categórica depois do one-hot ponderado. Sem isso, os grupos
    tendem a seguir as numéricas, mesmo quando elas não têm estrutura.
    """

    def __init__(self, numericas, categoricas, valor_ausente="AUSENTE", equilibrar_numericas=True):
        self.numericas = numericas
        self.categoricas = categoricas
        self.valor_ausente = valor_ausente
        self.equilibrar_numericas = equilibrar_numericas

    def fit(self, X, y=None):
        self.numericas_ = list(self.numericas)
        self.categoricas_ = list(self.categoricas)
        self.pipe_num_ = None
        self.pipe_cat_ = None
        if self.numericas_:
            self.pipe_num_ = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]).fit(X[self.numericas_])
        if self.categoricas_:
            self.pipe_cat_ = Pipeline([
                ("normalizar_ausentes", _normalizador_categorico()),
                ("imputer", SimpleImputer(strategy="constant", fill_value=self.valor_ausente)),
                ("onehot", OneHotPonderado()),
            ]).fit(X[self.categoricas_])

        self.variancia_media_categorica_ = float("nan")
        self.peso_numericas_ = 1.0
        if self.categoricas_:
            categoricas = self.pipe_cat_.transform(X[self.categoricas_])
            media = np.asarray(categoricas.mean(axis=0)).ravel()
            media_quadrados = np.asarray(categoricas.multiply(categoricas).mean(axis=0)).ravel()
            self.variancia_media_categorica_ = float((media_quadrados - media**2).sum() / len(self.categoricas_))
            if self.equilibrar_numericas and self.numericas_ and self.variancia_media_categorica_ > 0:
                self.peso_numericas_ = float(np.sqrt(self.variancia_media_categorica_))
        return self

    def transform(self, X):
        partes = []
        if self.pipe_num_ is not None:
            partes.append(sparse.csr_matrix(self.pipe_num_.transform(X[self.numericas_]) * self.peso_numericas_))
        if self.pipe_cat_ is not None:
            partes.append(sparse.csr_matrix(self.pipe_cat_.transform(X[self.categoricas_])))
        return sparse.hstack(partes, format="csr")

    def get_feature_names_out(self, input_features=None):
        nomes = []
        if self.numericas_:
            nomes.append(np.asarray(self.numericas_, dtype=object))
        if self.categoricas_:
            nomes.append(self.pipe_cat_.get_feature_names_out(self.categoricas_))
        return np.concatenate(nomes)


def construir_preprocessador_clustering(numericas, categoricas, valor_ausente="AUSENTE", equilibrar_numericas=True):
    """Pré-processador de agrupamento: numéricas padronizadas e categóricas em one-hot ponderado com AUSENTE explícito."""
    return PreprocessadorClustering(numericas, categoricas, valor_ausente, equilibrar_numericas)
