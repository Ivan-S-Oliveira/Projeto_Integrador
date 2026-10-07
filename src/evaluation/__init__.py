"""Avaliação: splits temporais, métricas, calibração e análise de erros."""

from src.evaluation.temporal import (
    TemporalSplit,
    split_temporal_3way,
)
from src.evaluation.metrics import (
    auc,
    brier,
    f1,
    precision,
    recall,
    accuracy,
    metricas_completas,
    metricas_por_limiar,
    ic_bootstrap,
)
from src.evaluation.calibration import (
    curva_confiabilidade,
    ece,
    mce,
    brier_decomposicao,
)
from src.evaluation.errors import (
    matriz_confusao,
    extrair_falsos_positivos,
    extrair_falsos_negativos,
    metricas_por_grupo,
    top_erros,
)

__all__ = [
    "TemporalSplit", "split_temporal_3way",
    "auc", "brier", "f1", "precision", "recall", "accuracy",
    "metricas_completas", "metricas_por_limiar", "ic_bootstrap",
    "curva_confiabilidade", "ece", "mce", "brier_decomposicao",
    "matriz_confusao", "extrair_falsos_positivos", "extrair_falsos_negativos",
    "metricas_por_grupo", "top_erros",
]