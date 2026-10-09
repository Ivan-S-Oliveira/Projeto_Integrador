"""Modelos supervisionados do Projeto Integrador."""

from src.models.pipeline import (
    FEATURES,
    FEATURES_CATEGORICAS,
    FEATURES_NUMERICAS,
    ALVO,
    COLUNA_TEMPO,
    build_preprocessor,
    criar_alvo_binario,
    filtrar_rotulos_validos,
    separar_xy,
    random_state,
)
from src.models.baseline import build_baseline_pipeline, evaluate_baseline
from src.models.logistic import build_logistic_pipeline
from src.models.boosting import build_boosting_pipeline
from src.models.calibration import (
    calibrar,
    escolher_limiar,
)

__all__ = [
    # pipeline
    "FEATURES", "FEATURES_CATEGORICAS", "FEATURES_NUMERICAS",
    "ALVO", "COLUNA_TEMPO",
    "build_preprocessor", "criar_alvo_binario", "filtrar_rotulos_validos",
    "separar_xy", "random_state",
    # modelos
    "build_baseline_pipeline", "evaluate_baseline",
    "build_logistic_pipeline", "build_boosting_pipeline",
    # calibração
    "calibrar", "escolher_limiar",
]