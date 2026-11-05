"""Leitura do Parquet do GitHub e alvo binário."""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest
from src.dados import get_parquet, read_srag
import numpy as np
from src.modelos import criar_alvo_binario, filtrar_rotulos_validos
from src import config as C


@pytest.mark.slow
def test_read_srag_retorna_dataframe(parquet_disponivel: Path | None) -> None:
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    df = read_srag(columns=["sg_uf", "dt_notific"])

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert {"sg_uf", "dt_notific"}.issubset(set(df.columns))


@pytest.mark.slow
def test_get_parquet_reaproveita_arquivo(parquet_disponivel: Path | None) -> None:
    """``force=False`` reutiliza o arquivo existente (mesmo mtime e tamanho)."""
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    caminho_1 = get_parquet(force=False)
    estado_1 = caminho_1.stat()
    caminho_2 = get_parquet(force=False)
    estado_2 = caminho_2.stat()

    assert caminho_1.resolve() == caminho_2.resolve()
    assert estado_1.st_mtime_ns == estado_2.st_mtime_ns
    assert estado_1.st_size == estado_2.st_size


def test_get_parquet_usa_srag_parquet_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``get_parquet`` deve usar ``C.srag_parquet_url``, não montar a URL à mão."""
    from src import dados as storage

    url_customizada = "https://example.org/dados/srag_teste.parquet"
    monkeypatch.setenv("SRAG_PARQUET_URL", url_customizada)

    chamadas: list[tuple[str, Path]] = []

    def fake_download_file(url, dest, **kwargs):
        chamadas.append((url, Path(dest)))
        Path(dest).write_bytes(b"PAR1" + b"\x00" * 64 + b"PAR1")
        return "0" * 64

    monkeypatch.setattr(storage, "download_file", fake_download_file)
    monkeypatch.setattr(storage, "PROCESSED", tmp_path)

    storage.get_parquet(force=True)

    assert chamadas, "download_file não foi chamado"
    assert chamadas[0][0] == url_customizada, (
        f"get_parquet usou {chamadas[0][0]!r} em vez de {url_customizada!r}. "
        "Provavelmente a URL está sendo remontada à mão em vez de usar "
        "C.srag_parquet_url()."
    )


def _df(valores: list[float | None]) -> pd.DataFrame:
    """DataFrame ``{"evolucao": valores, "feat": range(n)}``.

    A coluna ``feat`` serve como índice rastreável nas asserts.
    """
    return pd.DataFrame({"evolucao": valores, "feat": range(len(valores))})


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ([2.0],       [1.0]),
        ([1.0],       [0.0]),
        ([3.0],       [float("nan")]),
        ([9.0],       [float("nan")]),
        ([np.nan],    [float("nan")]),
    ],
    ids=["positivo", "negativo", "codigo_3", "codigo_9", "nan_entrada"],
)
def test_mapeamento_puro(entrada, esperado) -> None:
    """``2.0``→1, ``1.0``→0, qualquer outro→NaN."""
    y = criar_alvo_binario(_df(entrada))
    for obtido, esperado_valor in zip(y, esperado):
        if pd.isna(esperado_valor):
            assert pd.isna(obtido)
        else:
            assert obtido == esperado_valor


def test_mistura_completa() -> None:
    y = criar_alvo_binario(_df([1.0, 2.0, 3.0, 9.0, np.nan]))
    assert y.iloc[0] == 0.0
    assert y.iloc[1] == 1.0
    assert y.iloc[2:].isna().all()


def test_filtrar_remove_nan() -> None:
    df = _df([1.0, 2.0, 3.0, 9.0, np.nan])
    X_ok, y_ok = filtrar_rotulos_validos(df[["feat"]], criar_alvo_binario(df))

    assert len(y_ok) == 2
    assert y_ok.dtype == np.int8
    assert y_ok.tolist() == [0, 1]
    assert list(X_ok["feat"]) == [0, 1]


def test_positivos_e_negativos_nao_se_sobrepoem() -> None:
    with pytest.raises(ValueError, match="sobrepor"):
        criar_alvo_binario(_df([1.0, 2.0]), positivos=[1.0, 2.0], negativos=[1.0])
