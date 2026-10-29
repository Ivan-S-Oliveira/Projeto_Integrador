"""Para src/evaluation/errors.py (card: a análise por subgrupo não calcula PR-AUC nem Brier).

ATENÇÃO: não vi a versão atual de metricas_por_grupo. Esta é a função completa; ajuste a
assinatura para a que o resto do código já usa, ou chame esta a partir da existente.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

COLUNAS_METRICAS = ["pr_auc", "pr_auc_sobre_prev", "roc_auc", "brier", "o_e"]


def metricas_por_grupo(y_true, y_prob, grupos, min_n: int = 100) -> pd.DataFrame:
    """Métricas por grupo (ano, sexo, faixa etária, UF...).

    Colunas: grupo, n, obitos, prevalencia, pr_auc, pr_auc_sobre_prev, roc_auc, brier,
    o_e (óbitos observados ÷ soma das probabilidades previstas) e suprimido.

    - Grupo com menos de `min_n` fichas: suprimido=True e métricas vazias (NaN).
    - Grupo com uma classe só (só curas ou só óbitos): métricas vazias, sem erro.
    - o_e só faz sentido com probabilidades calibradas (G7); sem calibração fica distante de 1.
    """
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_prob, dtype=float)
    g = pd.Series(grupos).astype("object").where(lambda s: s.notna(), "ausente").to_numpy()
    if not (len(y) == len(p) == len(g)):
        raise ValueError("y_true, y_prob e grupos precisam ter o mesmo tamanho")

    linhas = []
    for nome in pd.unique(g):
        m = g == nome
        yy, pp = y[m], p[m]
        n = int(m.sum())
        obitos = int(yy.sum())
        linha = {"grupo": nome, "n": n, "obitos": obitos,
                 "prevalencia": obitos / n if n else np.nan,
                 "suprimido": n < min_n}
        linha.update({c: np.nan for c in COLUNAS_METRICAS})
        duas_classes = 0 < obitos < n
        if not linha["suprimido"] and duas_classes:
            ap = average_precision_score(yy, pp)
            linha.update(pr_auc=ap, pr_auc_sobre_prev=ap / linha["prevalencia"],
                         roc_auc=roc_auc_score(yy, pp), brier=brier_score_loss(yy, pp),
                         o_e=obitos / pp.sum() if pp.sum() > 0 else np.nan)
        linhas.append(linha)
    cols = ["grupo", "n", "obitos", "prevalencia"] + COLUNAS_METRICAS + ["suprimido"]
    return pd.DataFrame(linhas, columns=cols)
