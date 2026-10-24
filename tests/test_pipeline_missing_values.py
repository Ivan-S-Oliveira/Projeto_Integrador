from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import sparse

from src.models.pipeline import build_preprocessor


def test_preprocessor_accepts_pd_na_in_categorical_columns() -> None:
    frame = pd.DataFrame(
        {
            "idade_anos": pd.Series(
                [20.0, np.nan, 40.0],
                dtype="float32",
            ),
            "asma": pd.Series(
                ["1", pd.NA, "2"],
                dtype="string",
            ),
        }
    )

    preprocessor = build_preprocessor(
        numericas=["idade_anos"],
        categoricas=["asma"],
        saida="esparsa",
    )

    transformed = preprocessor.fit_transform(frame)

    assert sparse.issparse(transformed)
    assert transformed.shape[0] == len(frame)
    assert transformed.dtype == np.float32


def test_ordinal_preprocessor_accepts_pd_na() -> None:
    frame = pd.DataFrame(
        {
            "idade_anos": pd.Series(
                [20.0, np.nan, 40.0],
                dtype="float32",
            ),
            "asma": pd.Series(
                ["1", pd.NA, "2"],
                dtype="string",
            ),
        }
    )

    preprocessor = build_preprocessor(
        numericas=["idade_anos"],
        categoricas=["asma"],
        saida="ordinal",
    )

    transformed = preprocessor.fit_transform(frame)

    assert transformed.shape[0] == len(frame)
    assert transformed.dtype == np.float32
    assert np.isfinite(transformed).all()