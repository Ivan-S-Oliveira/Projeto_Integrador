"""Modelos supervisionados do Projeto Integrador."""

from src.models.baseline import (
    DummyStrategy,
    build_baseline_pipeline,
    evaluate_baseline,
)
from src.models.boosting import build_boosting_pipeline
from src.models.calibration import (
    MetodoCalibracao,
    Metrica,
    calibrar,
    escolher_limiar,
)
from src.models.factory import (
    Finalista,
    build_finalista,
    finalistas_disponiveis,
)
from src.models.logistic import (
    Penalty,
    Solver,
    build_logistic_pipeline,
)
from src.models.pipeline import (
    ALVO,
    AUSENTE,
    COLUNA_TEMPO,
    FEATURES,
    FEATURES_CATEGORICAS,
    FEATURES_NUMERICAS,
    build_pipeline,
    build_preprocessor,
    criar_alvo_binario,
    filtrar_rotulos_validos,
    random_state,
)

__all__ = [
    # pipeline (constantes + pré-processamento + alvo)
    "ALVO",
    "AUSENTE",
    "COLUNA_TEMPO",
    "FEATURES",
    "FEATURES_CATEGORICAS",
    "FEATURES_NUMERICAS",
    "build_pipeline",
    "build_preprocessor",
    "criar_alvo_binario",
    "filtrar_rotulos_validos",
    "random_state",
    # baseline
    "DummyStrategy",
    "build_baseline_pipeline",
    "evaluate_baseline",
    # logistic
    "Penalty",
    "Solver",
    "build_logistic_pipeline",
    # boosting
    "build_boosting_pipeline",
    # calibração
    "MetodoCalibracao",
    "Metrica",
    "calibrar",
    "escolher_limiar",
    # fábrica
    "Finalista",
    "build_finalista",
    "finalistas_disponiveis",
]