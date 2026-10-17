"""
Fábrica de finalistas — ponto único de construção dos modelos de C5/C6.

Hiperparâmetros vêm de ``models.<nome>`` no ``supervised.yaml``; overrides
em ``**overrides`` têm precedência. ``preprocessor=None`` faz cada
construtor usar o default (``build_preprocessor()``).
"""

from __future__ import annotations

from typing import Any, Literal, get_args

from sklearn.pipeline import Pipeline

from src.models.boosting import build_boosting_pipeline
from src.models.logistic import build_logistic_pipeline
from src.utils import config as C

__all__ = ["Finalista", "build_finalista", "finalistas_disponiveis"]

Finalista = Literal["boosting", "logistic"]
_FINALISTAS_VALIDOS = frozenset(get_args(Finalista))


def finalistas_disponiveis() -> tuple[str, ...]:
    """Nomes canônicos dos finalistas registrados, em ordem estável."""
    return tuple(sorted(_FINALISTAS_VALIDOS))


def _kwargs_do_yaml(nome: str) -> dict[str, Any]:
    """Lê ``models.<nome>`` do YAML e devolve kwargs aceitos pelo construtor.

    Descartados: chaves ``busca_*`` (grid de tuning) e valores ``None``
    (deixa o default do construtor agir). Devolve ``{}`` se a secção não
    existir ou não for mapping.
    """
    secao = C.cfg("models", nome)
    if not isinstance(secao, dict):
        return {}
    return {
        k: v
        for k, v in secao.items()
        if v is not None and not k.startswith("busca_")
    }


def build_finalista(
    nome: str,
    *,
    preprocessor=None,
    **overrides: Any,
) -> Pipeline:
    """Constrói o ``Pipeline`` de um finalista pelo nome.

    Levanta ``ValueError`` se ``nome`` não estiver em
    ``finalistas_disponiveis()``. O ``Pipeline`` devolvido **não está
    ajustado** — o caller faz ``fit``.
    """
    if nome not in _FINALISTAS_VALIDOS:
        raise ValueError(
            f"finalista desconhecido: {nome!r}. "
            f"Use um destes: {sorted(_FINALISTAS_VALIDOS)}."
        )

    params = _kwargs_do_yaml(nome) | overrides
    if preprocessor is not None:
        params["preprocessor"] = preprocessor

    if nome == "boosting":
        return build_boosting_pipeline(**params)
    return build_logistic_pipeline(**params)