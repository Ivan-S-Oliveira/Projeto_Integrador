"""
Fábrica de finalistas — ponto único de construção dos modelos de C5/C6.

Aceita nomes canônicos (`boosting`, `logistic`) e apelidos do YAML
(`hist_gradient_boosting` → `boosting`). A normalização vive **somente**
aqui: notebooks e testes chamam `build_finalista` com o nome do YAML.
"""

from __future__ import annotations

import inspect
import warnings
from typing import Any, Literal, get_args

from sklearn.pipeline import Pipeline

from src.models.boosting import build_boosting_pipeline
from src.models.logistic import build_logistic_pipeline
from src.utils import config as C

__all__ = [
    "Finalista",
    "build_finalista",
    "finalistas_aceitos",
    "finalistas_disponiveis",
    "resolver_finalista",
]

Finalista = Literal["boosting", "logistic"]
_FINALISTAS_VALIDOS = frozenset(get_args(Finalista))

_FINALISTA_ALIASES: dict[str, str] = {
    "hist_gradient_boosting": "boosting",
}

_CONSTRUTORES: dict[str, Any] = {
    "boosting": build_boosting_pipeline,
    "logistic": build_logistic_pipeline,
}


def finalistas_disponiveis() -> tuple[str, ...]:
    """Nomes canônicos dos finalistas registrados, em ordem estável."""
    return tuple(sorted(_FINALISTAS_VALIDOS))


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