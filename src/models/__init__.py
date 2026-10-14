"""Modelos supervisionados do Projeto Integrador."""

from src.models.baseline import build_baseline_pipeline, evaluate_baseline
from src.models.boosting import build_boosting_pipeline
from src.models.calibration import calibrar, escolher_limiar
from src.models.logistic import build_logistic_pipeline
from src.models.pipeline import (
    ALVO,
    COLUNA_TEMPO,
    FEATURES,
    FEATURES_CATEGORICAS,
    FEATURES_NUMERICAS,
    build_preprocessor,
    criar_alvo_binario,
    filtrar_rotulos_validos,
    random_state,
)

__all__ = [
    "ALVO",
    "COLUNA_TEMPO",
    "FEATURES",
    "FEATURES_CATEGORICAS",
    "FEATURES_NUMERICAS",
    "build_baseline_pipeline",
    "build_boosting_pipeline",
    "build_logistic_pipeline",
    "build_preprocessor",
    "calibrar",
    "criar_alvo_binario",
    "escolher_limiar",
    "evaluate_baseline",
    "filtrar_rotulos_validos",
    "random_state",
]