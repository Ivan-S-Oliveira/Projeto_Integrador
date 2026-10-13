"""
Fábrica de modelos finalistas.

Ponto único de construção dos pipelines finalistas usados em C5 e C6.
Antes desta fábrica, cada notebook duplicava a leitura de hiperparâmetros
do `supervised.yaml` e o `if/elif` de despacho por nome de modelo.

Convenções
----------
- Os hiperparâmetros de cada finalista vivem em uma seção própria do
  `supervised.yaml`, com o mesmo nome do modelo (ex.: `boosting:`,
  `logistic:`). Chaves ausentes caem nos defaults do construtor
  correspondente.
- Overrides explícitos passados em `**overrides` têm precedência sobre o
  YAML — útil em testes e em varreduras pontuais.
- O `preprocessor` é opcional. Quando None, cada construtor monta o seu
  via `build_preprocessor()`.

Finalistas suportados: `"boosting"` e `"logistic"`.
"""

from __future__ import annotations

from typing import Any, Literal

from sklearn.pipeline import Pipeline

from src.models.boosting import build_boosting_pipeline
from src.models.logistic import build_logistic_pipeline
from src.utils import config as C

__all__ = ["Finalista", "build_finalista", "finalistas_disponiveis"]


Finalista = Literal["boosting", "logistic"]

_FINALISTAS_VALIDOS: tuple[str, ...] = ("boosting", "logistic")


def finalistas_disponiveis() -> tuple[str, ...]:
    """Nomes canônicos dos finalistas registrados nesta fábrica."""
    return _FINALISTAS_VALIDOS


def _kwargs_do_yaml(nome: str) -> dict[str, Any]:
    """
    Lê a seção `nome` do `supervised.yaml` e devolve o dict de kwargs.

    Retorna `{}` quando a seção não existir ou não for um mapping — nesse
    caso os defaults do construtor do modelo são usados. Chaves cujo valor
    seja `None` são descartadas para não sobrepor defaults com `None`.
    """
    try:
        secao = C.cfg(nome)
    except (KeyError, TypeError):
        return {}
    if not isinstance(secao, dict):
        return {}
    return {k: v for k, v in secao.items() if v is not None}


def build_finalista(
    nome: str,
    *,
    preprocessor=None,
    **overrides: Any,
) -> Pipeline:
    """
    Constrói o `Pipeline` de um modelo finalista pelo nome.

    Parâmetros
    ----------
    nome : {"boosting", "logistic"}
        Identificador do finalista. Precisa estar em
        `finalistas_disponiveis()`.
    preprocessor : ColumnTransformer | None
        Pré-processador a injetar no pipeline. Se None, cada construtor
        usa o default (`build_preprocessor()`).
    **overrides :
        Hiperparâmetros que sobrepõem os valores lidos do
        `supervised.yaml`. Passados direto ao construtor do modelo.

    Retorno
    -------
    `Pipeline` (pré-processamento + classificador) ainda **não ajustado**.

    Levanta
    ------
    ValueError
        Se `nome` não for um finalista registrado.
    """
    if nome not in _FINALISTAS_VALIDOS:
        raise ValueError(
            f"finalista desconhecido: {nome!r}. "
            f"Use um destes: {list(_FINALISTAS_VALIDOS)}."
        )

    params: dict[str, Any] = _kwargs_do_yaml(nome)
    params.update(overrides)
    if preprocessor is not None:
        params["preprocessor"] = preprocessor

    if nome == "boosting":
        return build_boosting_pipeline(**params)
    # `nome` é validado acima; este ramo cobre "logistic".
    return build_logistic_pipeline(**params)