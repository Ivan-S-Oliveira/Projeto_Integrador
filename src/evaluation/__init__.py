"""Avaliação: splits temporais, métricas, calibração e análise de erros."""

from src.evaluation.calibration import (
    brier_decomposicao,
    curva_confiabilidade,
    ece,
    mce,
)
from src.evaluation.errors import (
    CriterioTop,
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
    ArrayLike,
    accuracy,
    auc,
    average_precision,
    brier,
    especificidade,
    f1,
    ic_bootstrap,
    log_loss,
    metricas_completas,
    metricas_por_limiar,
    precision,
    recall,
    sensibilidade,
)
from src.evaluation.temporal import (
    TemporalSplit,
    split_temporal_3way,
)

__all__ = [
    # metrics
    "ArrayLike",
    "accuracy",
    "auc",
    "average_precision",
    "brier",
    "especificidade",
    "f1",
    "ic_bootstrap",
    "log_loss",
    "metricas_completas",
    "metricas_por_limiar",
    "precision",
    "recall",
    "sensibilidade",
    # calibration
    "brier_decomposicao",
    "curva_confiabilidade",
    "ece",
    "mce",
    # errors
    "CriterioTop",
    "extrair_falsos_negativos",
    "extrair_falsos_positivos",
    "matriz_confusao",
    "metricas_por_grupo",
    "top_erros",
    # leakage
    "LeakageError",
    "check_leakage",
    # temporal
    "TemporalSplit",
    "split_temporal_3way",
]