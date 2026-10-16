"""
Split temporal em três blocos + trava do holdout.

⚠️  Ferramenta de **sensibilidade temporal** — NÃO é o split oficial.
O split oficial do projeto é o **aleatório estratificado**, gerado no
Notebook 03 e persistido em `dataset_supervisionado.parquet` (usado por
C2, C3, C5, C6). Este módulo serve para perguntas do tipo "o desempenho
se mantém se eu treinar no passado e testar no futuro?".

Regra de ouro (quando usado):
    treino + validacao → escolha de modelo
    holdout            → UMA ÚNICA vez, após ``concluir_selecao()``

A classe ``TemporalSplit`` bloqueia o acesso ao holdout enquanto o gate
``G9_holdout`` não estiver aprovado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, get_args

import pandas as pd

from src.utils import config as C

OnNat = Literal["raise", "drop"]
_ON_NAT_VALORES = frozenset(get_args(OnNat))


def _validar_fracao(nome: str, valor: float) -> None:
    if not 0 < valor < 1:
        raise ValueError(f"{nome} deve estar em (0, 1); recebido {valor!r}.")


def _validar_coluna_tempo(df: pd.DataFrame, coluna_tempo: str) -> None:
    if coluna_tempo not in df.columns:
        raise KeyError(f"Coluna temporal ausente: {coluna_tempo!r}")
    if not pd.api.types.is_datetime64_any_dtype(df[coluna_tempo]):
        raise TypeError(
            f"Coluna temporal {coluna_tempo!r} não é datetime "
            f"(dtype atual: {df[coluna_tempo].dtype}). "
            "Converta com pd.to_datetime antes do split."
        )


def _tratar_nat(
    df: pd.DataFrame,
    coluna_tempo: str,
    on_nat: OnNat,
) -> pd.DataFrame:
    """Remove ``NaT`` em ``coluna_tempo`` conforme ``on_nat``."""
    nat_mask = df[coluna_tempo].isna()
    n_nat    = int(nat_mask.sum())

    if not n_nat:
        return df
    if on_nat == "raise":
        raise ValueError(
            f"{n_nat} linha(s) com data inválida (NaT) em "
            f"{coluna_tempo!r}. Remova-as antes ou use on_nat='drop'."
        )
    return df.loc[~nat_mask].reset_index(drop=True)


def split_temporal_3way(
    df: pd.DataFrame,
    coluna_tempo: str,
    frac_treino: float = 0.7,
    frac_validacao: float = 0.15,
    *,
    on_nat: OnNat = "raise",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Divide em treino / validação / holdout, **sem embaralhar**.

    Garante, na ordem temporal::

        max(treino[coluna_tempo]) <= min(validacao[coluna_tempo])
        max(validacao[coluna_tempo]) <= min(holdout[coluna_tempo])

    ``on_nat='raise'`` (default) falha se houver ``NaT``; ``'drop'``
    remove essas linhas antes de ordenar.
    """
    if on_nat not in _ON_NAT_VALORES:
        raise ValueError(
            f"on_nat inválido: {on_nat!r}. Use {sorted(_ON_NAT_VALORES)}."
        )

    _validar_fracao("frac_treino",    frac_treino)
    _validar_fracao("frac_validacao", frac_validacao)
    if frac_treino + frac_validacao >= 1:
        raise ValueError(
            "frac_treino + frac_validacao deve ser < 1 (resto vira holdout)."
        )

    _validar_coluna_tempo(df, coluna_tempo)
    df = _tratar_nat(df, coluna_tempo, on_nat)

    ordenado = df.sort_values(coluna_tempo, kind="mergesort").reset_index(drop=True)
    n = len(ordenado)
    if n < 3:
        raise ValueError(f"Dataset pequeno demais para split 3-way: n={n}")

    corte_treino = int(n * frac_treino)
    corte_valid  = int(n * (frac_treino + frac_validacao))

    return (
        ordenado.iloc[:corte_treino].reset_index(drop=True),
        ordenado.iloc[corte_treino:corte_valid].reset_index(drop=True),
        ordenado.iloc[corte_valid:].reset_index(drop=True),
    )


@dataclass
class TemporalSplit:
    """Guarda os três blocos e controla o acesso ao holdout.

    ⚠️  Ferramenta de **sensibilidade temporal**, não o split oficial.
    Uso típico::

        split = TemporalSplit(df, coluna_tempo="dt_notific")
        tr, va = split.treino_validacao()  # seleção
        split.concluir_selecao()           # exige G9_holdout aprovado
        ho = split.holdout()               # avaliação, uma vez
    """

    df: pd.DataFrame
    coluna_tempo: str
    frac_treino: float = 0.7
    frac_validacao: float = 0.15
    on_nat: OnNat = "raise"

    _treino: pd.DataFrame = field(init=False, repr=False)
    _validacao: pd.DataFrame = field(init=False, repr=False)
    _holdout: pd.DataFrame = field(init=False, repr=False)
    _holdout_liberado: bool = field(init=False, default=False, repr=False)

    def __post_init__(self) -> None:
        tr, va, ho = split_temporal_3way(
            self.df,
            coluna_tempo=self.coluna_tempo,
            frac_treino=self.frac_treino,
            frac_validacao=self.frac_validacao,
            on_nat=self.on_nat,
        )
        self._treino    = tr
        self._validacao = va
        self._holdout   = ho

    def treino_validacao(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """``(treino, validacao)`` — único par para a fase de seleção."""
        return self._treino, self._validacao

    @property
    def treino(self) -> pd.DataFrame:
        return self._treino

    @property
    def validacao(self) -> pd.DataFrame:
        return self._validacao

    def concluir_selecao(self) -> None:
        """Libera o holdout após o gate ``G9_holdout`` estar aprovado.

        O gate é a autorização explícita — G7 e G8 tratam de decisões da
        fase de seleção e devem ter sido fechados *antes* deste ponto.
        Chamar **uma única vez**, após congelar modelo, calibração e limiar.
        """
        gate   = C.cfg("gates", "G9_holdout") or {}
        status = gate.get("status")
        if status != "aprovado":
            raise RuntimeError(
                "Holdout bloqueado: gate `G9_holdout` ainda não aprovado "
                f"(status atual: {status!r}). Feche o gate em "
                "`configs/supervised.yaml` antes de chamar `concluir_selecao()`."
            )
        self._holdout_liberado = True

    @property
    def holdout_liberado(self) -> bool:
        return self._holdout_liberado

    def holdout(self) -> pd.DataFrame:
        """Bloco de holdout. Levanta ``RuntimeError`` se ainda bloqueado."""
        if not self._holdout_liberado:
            raise RuntimeError(
                "Holdout bloqueado. Chame `split.concluir_selecao()` antes."
            )
        return self._holdout

    @property
    def n_treino(self) -> int:
        return len(self._treino)

    @property
    def n_validacao(self) -> int:
        return len(self._validacao)

    @property
    def n_holdout(self) -> int:
        return len(self._holdout)

    def resumo(self) -> str:
        """Resumo legível — bom para log no ``Run``."""

        def _periodo(d: pd.DataFrame) -> str:
            if d.empty:
                return "vazio"
            return f"{d[self.coluna_tempo].min()} .. {d[self.coluna_tempo].max()}"

        estado = "liberado" if self._holdout_liberado else "bloqueado"
        return (
            f"TemporalSplit(coluna={self.coluna_tempo!r}, "
            f"papel='sensibilidade_temporal')\n"
            f"  treino    : {self.n_treino:>10,}  {_periodo(self._treino)}\n"
            f"  validacao : {self.n_validacao:>10,}  {_periodo(self._validacao)}\n"
            f"  holdout   : {self.n_holdout:>10,}  {_periodo(self._holdout)}  ({estado})"
        )