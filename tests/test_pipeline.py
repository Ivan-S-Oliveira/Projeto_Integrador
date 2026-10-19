"""
Testes do pipeline de ingestão: ``read_srag``, ``get_parquet`` e
``build_pipeline``.

Testes que tocam no Parquet são marcados com ``@pytest.mark.slow``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.models.pipeline import build_pipeline
from src.utils import env
from src.utils.storage import get_parquet, read_srag


# ---------------------------------------------------------------------------
# Ingestão do Parquet (slow)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# build_pipeline
# ---------------------------------------------------------------------------

def test_build_pipeline_falha_feature_ausente() -> None:
    X = pd.DataFrame({"nu_idade_n": [30.0, 40.0, 50.0]})
    with pytest.raises(KeyError, match="ausentes"):
        build_pipeline(X=X)


def test_build_pipeline_strict_false_avisa_mas_continua(
    caplog: pytest.LogCaptureFixture,
) -> None:
    X = pd.DataFrame({"nu_idade_n": [30.0, 40.0, 50.0]})
    with caplog.at_level("WARNING"):
        pipe = build_pipeline(X=X, strict=False)

    assert pipe is not None
    assert "ausentes" in caplog.text.lower()


# ---------------------------------------------------------------------------
# Diretórios padrão
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("nome_dir", ["RAW", "PROCESSED"])
def test_diretorio_padrao_foi_criado(nome_dir: str) -> None:
    """``env.garantir_diretorios`` cria os diretórios esperados."""
    env.garantir_diretorios()
    caminho = getattr(env, nome_dir)
    assert caminho.is_dir(), f"{caminho} não é diretório"

def test_get_parquet_usa_srag_parquet_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``get_parquet`` deve usar ``C.srag_parquet_url()``, não montar a URL à mão.

    Regressão do card #14: ``SRAG_PARQUET_URL`` era descrita no
    ``01_extracao.ipynb`` como override, mas ``get_parquet`` ignorava.
    """
    from src.utils import storage

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


def test_get_parquet_usa_url_padrao_sem_env_var(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sem ``SRAG_PARQUET_URL``, o default continua sendo a URL da release."""
    from src.utils import config as C
    from src.utils import storage

    monkeypatch.delenv("SRAG_PARQUET_URL", raising=False)
    esperado = (
        f"https://github.com/{C.GITHUB_REPO}/releases/download/"
        f"{C.DATA_VERSION}/{C.PARQUET_NAME}"
    )

    chamadas: list[str] = []

    def fake_download_file(url, dest, **kwargs):
        chamadas.append(url)
        Path(dest).write_bytes(b"PAR1" + b"\x00" * 64 + b"PAR1")
        return "0" * 64

    monkeypatch.setattr(storage, "download_file", fake_download_file)
    monkeypatch.setattr(storage, "PROCESSED", tmp_path)

    storage.get_parquet(force=True)

    assert chamadas[0] == esperado