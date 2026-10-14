"""Avaliação: splits temporais, métricas, calibração e análise de erros."""

from src.evaluation.calibration import (
    brier_decomposicao,
    curva_confiabilidade,
    ece,
    mce,
)
from src.evaluation.errors import (
    extrair_falsos_negativos,
    extrair_falsos_positivos,
    matriz_confusao,
    metricas_por_grupo,
    top_erros,
)
from src.evaluation.leakage import (
    LeakageError,
    check_leakage,
)
from src.evaluation.metrics import (
    accuracy,
    auc,
    average_precision,
    brier,
    f1,
    ic_bootstrap,
    metricas_completas,
    metricas_por_limiar,
    precision,
    recall,
)
from src.evaluation.temporal import (
    TemporalSplit,
    split_temporal_3way,
)

__all__ = [
    "TemporalSplit",
    "split_temporal_3way",
    "average_precision",
    "auc",
    "brier",
    "f1",
    "precision",
    "recall",
    "accuracy",
    "metricas_completas",
    "metricas_por_limiar",
    "ic_bootstrap",
    "curva_confiabilidade",
    "ece",
    "mce",
    "brier_decomposicao",
    "LeakageError",
    "check_leakage",
    "matriz_confusao",
    "extrair_falsos_positivos",
    "extrair_falsos_negativos",
    "metricas_por_grupo",
    "top_erros",
]