"""Modelos supervisionados do Projeto Integrador."""

from src.models.pipeline import (
    FEATURES,
    FEATURES_CATEGORICAS,
    FEATURES_NUMERICAS,
    ALVO,
    ALVO_POSITIVO,
    ALVO_IGNORADO,
    COLUNA_TEMPO,
    build_preprocessor,
    criar_alvo_binario,
    filtrar_rotulos_validos,
    separar_xy,
    split_temporal,
    random_state,
)
from src.models.baseline import build_baseline_pipeline
from src.models.logistic import build_logistic_pipeline
from src.models.boosting import build_boosting_pipeline
from src.models.calibration import (
    calibrar,
    curva_confiabilidade,
    escolher_limiar,
    metricas_completas,
)

__all__ = [
    # pipeline
    "FEATURES", "FEATURES_CATEGORICAS", "FEATURES_NUMERICAS",
    "ALVO", "ALVO_POSITIVO", "ALVO_IGNORADO", "COLUNA_TEMPO",
    "build_preprocessor", "criar_alvo_binario", "filtrar_rotulos_validos",
    "separar_xy", "split_temporal", "random_state",
    # modelos
    "build_baseline_pipeline", "build_logistic_pipeline", "build_boosting_pipeline",
    # calibração
    "calibrar", "curva_confiabilidade", "escolher_limiar", "metricas_completas",
]