"""
Fábrica de finalistas — ponto único de construção dos modelos de C5/C6.

Aceita nomes canônicos (`boosting`, `logistic`) e apelidos documentados
do YAML (`hist_gradient_boosting` → `boosting`). A normalização vive
**somente** aqui: notebooks e testes importam `build_finalista` e passam
o nome como está no YAML.

Hiperparâmetros vêm de `models.<nome>` no `supervised.yaml`; overrides em
`**overrides` têm precedência. `preprocessor=None` faz cada construtor
usar o default (`build_preprocessor()`).
"""

from __future__ import annotations

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

# Apelidos do YAML → nome canônico interno. Este é o único mapeamento
# autorizado no projeto; não duplicar em notebooks nem em testes.
_FINALISTA_ALIASES: dict[str, str] = {
    "hist_gradient_boosting": "boosting",
}


def finalistas_disponiveis() -> tuple[str, ...]:
    """Nomes canônicos dos finalistas registrados, em ordem estável."""
    return tuple(sorted(_FINALISTAS_VALIDOS))


def finalistas_aceitos() -> tuple[str, ...]:
    """Nomes canônicos + apelidos aceitos por ``build_finalista``.

    Use quando precisar validar um nome que vem do YAML antes de
    construir o pipeline (ex.: C_16 checando ``finalista_escolhido``).
    """
    return tuple(sorted(_FINALISTAS_VALIDOS | set(_FINALISTA_ALIASES)))


def resolver_finalista(nome: str) -> str:
    """Devolve o nome canônico para ``nome`` (que pode ser um apelido)."""
    return _FINALISTA_ALIASES.get(nome, nome)


def _kwargs_do_yaml(nome: str) -> dict[str, Any]:
    """Lê ``models.<nome>`` do YAML e devolve kwargs aceitos pelo construtor.

    ``nome`` aqui deve ser **canônico** — ``build_finalista`` já normalizou
    antes de chamar. Descartados: chaves ``busca_*`` (grid de tuning) e
    valores ``None`` (deixa o default do construtor agir).
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
    """Constrói o ``Pipeline`` de um finalista pelo nome ou apelido.

    Aceita nomes canônicos (``boosting``, ``logistic``) e apelidos do YAML
    (``hist_gradient_boosting`` → ``boosting``). A normalização acontece
    **antes** de `_kwargs_do_yaml`, então o alias lê `models.boosting`
    (que é onde os hiperparâmetros realmente moram).

    Levanta ``ValueError`` se ``nome`` (após normalização) não estiver em
    ``finalistas_disponiveis()``. O ``Pipeline`` devolvido **não está
    ajustado** — o caller faz ``fit``.
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

    if nome == "boosting":
        return build_boosting_pipeline(**params)
    return build_logistic_pipeline(**params)