"""
Split temporal em três blocos + trava do holdout.

Regra de ouro:
    ┌──────────────┬──────────────┬──────────────────┐
    │   treino     │  validação   │     holdout      │
    └──────────────┴──────────────┴──────────────────┘
     mais antigo ───────────────────────► mais recente

    - `treino` + `validação` → escolha de modelo, hiperparâmetros, limiar
    - `holdout`               → UMA ÚNICA vez, no fim, após `concluir_selecao()`

A classe `TemporalSplit` bloqueia o acesso ao holdout enquanto a seleção
não for explicitamente marcada como concluída. Isso impede o erro clássico
de "espionar" o holdout durante a fase de modelagem.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


# ---------------------------------------------------------------------------
# Split em 3 blocos (função pura, sem trava)
# ---------------------------------------------------------------------------

def split_temporal_3way(
    df: pd.DataFrame,
    coluna_tempo: str,
    frac_treino: float = 0.7,
    frac_validacao: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split temporal em treino / validação / holdout, **sem embaralhar**.

    Parâmetros
    ----------
    df : pd.DataFrame
        Base completa.
    coluna_tempo : str
        Coluna usada para ordenar (ex.: "dt_notific").
    frac_treino, frac_validacao : float
        Frações do total. `frac_holdout = 1 - frac_treino - frac_validacao`.

    Retorno
    -------
    (treino, validacao, holdout) : tuple de DataFrames

    Garantias
    ---------
        max(treino[coluna_tempo]) <= min(validacao[coluna_tempo])
        max(validacao[coluna_tempo]) <= min(holdout[coluna_tempo])
    """
    if coluna_tempo not in df.columns:
        raise KeyError(f"Coluna temporal ausente: {coluna_tempo!r}")

    if not (0 < frac_treino < 1):
        raise ValueError("frac_treino deve estar em (0, 1).")
    if not (0 < frac_validacao < 1):
        raise ValueError("frac_validacao deve estar em (0, 1).")
    if frac_treino + frac_validacao >= 1:
        raise ValueError(
            "frac_treino + frac_validacao deve ser < 1 "
            "(o restante vira holdout)."
        )

    ordenado = (
        df.sort_values(coluna_tempo, kind="mergesort")
          .reset_index(drop=True)
    )

    n = len(ordenado)
    if n < 3:
        raise ValueError(f"Dataset pequeno demais para split 3-way: n={n}")

    corte_treino = int(n * frac_treino)
    corte_valid = int(n * (frac_treino + frac_validacao))

    treino = ordenado.iloc[:corte_treino].reset_index(drop=True)
    validacao = ordenado.iloc[corte_treino:corte_valid].reset_index(drop=True)
    holdout = ordenado.iloc[corte_valid:].reset_index(drop=True)

    return treino, validacao, holdout


# ---------------------------------------------------------------------------
# Split com trava do holdout
# ---------------------------------------------------------------------------

@dataclass
class TemporalSplit:
    """
    Guarda os três blocos e controla o acesso ao holdout.

    Uso típico
    ----------
        split = TemporalSplit(df, coluna_tempo="dt_notific")

        # Fase 1 — escolha de modelo (SOMENTE treino + validação)
        tr, va = split.treino_validacao()
        modelo = ...
        modelo.fit(tr[FEATURES], y_tr)

        # Ao terminar a seleção:
        split.concluir_selecao()

        # Fase 2 — avaliação final, UMA única vez
        ho = split.holdout()
        y_prob = modelo.predict_proba(ho[FEATURES])[:, 1]

    Atributos
    ---------
    n_treino, n_validacao, n_holdout : int
        Tamanhos de cada bloco (útil para logging).
    """

    df: pd.DataFrame
    coluna_tempo: str
    frac_treino: float = 0.7
    frac_validacao: float = 0.15

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
        )
        self._treino = tr
        self._validacao = va
        self._holdout = ho

    # ------------------------------------------------------------------
    # Acesso aos blocos de modelagem
    # ------------------------------------------------------------------

    def treino_validacao(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retorna (treino, validação).

        Este é o único caminho para treinar e comparar modelos durante a
        fase de seleção. O holdout NÃO é exposto aqui.
        """
        return self._treino, self._validacao

    @property
    def treino(self) -> pd.DataFrame:
        return self._treino

    @property
    def validacao(self) -> pd.DataFrame:
        return self._validacao

    # ------------------------------------------------------------------
    # Ciclo de vida do holdout
    # ------------------------------------------------------------------

    def concluir_selecao(self) -> None:
        """
        Marca a fase de seleção como encerrada e libera o holdout.

        Deve ser chamada **uma única vez**, depois que o modelo final foi
        escolhido, o limiar foi definido e a calibração foi ajustada.
        """
        self._holdout_liberado = True

    @property
    def holdout_liberado(self) -> bool:
        return self._holdout_liberado

    def holdout(self) -> pd.DataFrame:
        """
        Retorna o bloco de holdout.

        Levanta `RuntimeError` se `concluir_selecao()` ainda não foi
        chamada. Isso impede que o holdout seja consultado durante a
        escolha de modelo.
        """
        if not self._holdout_liberado:
            raise RuntimeError(
                "Holdout bloqueado.\n"
                "Finalize a seleção de modelo e chame `split.concluir_selecao()` "
                "antes de acessar o holdout."
            )
        return self._holdout

    # ------------------------------------------------------------------
    # Diagnóstico
    # ------------------------------------------------------------------

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
        """Resumo legível do split — bom para log no `Run`."""
        def _periodo(d: pd.DataFrame) -> str:
            if d.empty:
                return "vazio"
            ini = d[self.coluna_tempo].min()
            fim = d[self.coluna_tempo].max()
            return f"{ini} .. {fim}"

        return (
            f"TemporalSplit(coluna={self.coluna_tempo!r})\n"
            f"  treino    : {self.n_treino:>10,}  {_periodo(self._treino)}\n"
            f"  validacao : {self.n_validacao:>10,}  {_periodo(self._validacao)}\n"
            f"  holdout   : {self.n_holdout:>10,}  {_periodo(self._holdout)}  "
            f"({'liberado' if self._holdout_liberado else 'bloqueado'})"
        )

# ---------------------------------------------------------------------------
# Compatibilidade com o C2 (nome histórico)
# ---------------------------------------------------------------------------

def temporal_split(
    df: pd.DataFrame,
    *,
    date_column: str | None = None,
    coluna_tempo: str | None = None,
    fracao: dict | None = None,
    frac_treino: float | None = None,
    frac_validacao: float | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Compat: aceita tanto `date_column` (nome usado no C2) quanto
    `coluna_tempo` (nome usado no resto do projeto).

    Se `fracao` for passado ({'treino': .., 'validacao': ..}), sobrescreve
    `frac_treino` / `frac_validacao`. Se nenhum for passado, lê do
    `supervised.yaml`.

    Retorna (treino, validacao, holdout).
    """
    from src.utils import config as C

    col = coluna_tempo or date_column or C.cfg("coluna_tempo") or "dt_notific"

    # --- resolve frações ---
    if fracao is None:
        fracao = C.cfg("temporal", "fracao") or {"treino": 0.70, "validacao": 0.15}

    if not isinstance(fracao, dict) or "treino" not in fracao or "validacao" not in fracao:
        raise ValueError(
            "Frações inválidas: esperado dict com chaves 'treino' e 'validacao', "
            f"recebido {fracao!r}."
        )

    ft = float(frac_treino) if frac_treino is not None else float(fracao["treino"])
    fv = float(frac_validacao) if frac_validacao is not None else float(fracao["validacao"])

    if not (0 < ft < 1):
        raise ValueError(f"frac_treino deve estar em (0, 1); recebido {ft!r}.")
    if not (0 < fv < 1):
        raise ValueError(f"frac_validacao deve estar em (0, 1); recebido {fv!r}.")
    if ft + fv >= 1:
        raise ValueError(
            "frac_treino + frac_validacao deve ser < 1 "
            "(o restante vira holdout)."
        )

    return split_temporal_3way(
        df,
        coluna_tempo=col,
        frac_treino=ft,
        frac_validacao=fv,
    )