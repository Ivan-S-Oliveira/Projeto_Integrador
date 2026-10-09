"""
Contrato oficial de acesso ao Parquet de SRAG.

Fluxo:
    GitHub Release → data/processed/<DATA_VERSION>/srag.parquet

- Tenta primeiro o download **público** via URL de release.
- Se falhar (4xx/5xx ou asset inválido) e houver `GITHUB_TOKEN`, cai no
  asset **privado** via API do GitHub.
- Grava um sidecar `<arquivo>.sha256` com o hash do Parquet baixado —
  reprodutibilidade e registro no `Run`.
- `force=True` rebaixa e descarta o sidecar antigo.

Requisitos:
    - `requests` e `pandas` no ambiente.
    - Constantes `C.HTTP_TIMEOUT`, `C.HTTP_TENTATIVAS` e `C.HTTP_BACKOFF`
      em `src.utils.config` controlam o comportamento de rede.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

from src.utils import config as C
from src.utils.env import PROCESSED, get_secret


PARQUET_MAGIC: bytes = b"PAR1"
_CHUNK: int = 8 * 1024 * 1024  # 8 MiB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _token() -> str | None:
    """Devolve `GITHUB_TOKEN` se definido; caso contrário, `None`."""
    return get_secret("GITHUB_TOKEN", obrigatorio=False)


def sha256_path(parquet_path: Path) -> Path:
    """Caminho do sidecar `.sha256` associado a um Parquet."""
    return parquet_path.with_suffix(parquet_path.suffix + ".sha256")


def read_sha256(parquet_path: Path) -> str | None:
    """Lê o SHA-256 do sidecar, ou `None` se ele não existir."""
    sidecar = sha256_path(parquet_path)
    if not sidecar.exists():
        return None
    linha = sidecar.read_text(encoding="utf-8").strip()
    return linha.split()[0] if linha else None


def _abrir_stream(
    url: str,
    *,
    headers: dict[str, str] | None,
    tentativas: int,
    backoff: float,
    timeout: float,
) -> requests.Response:
    """
    Abre um stream HTTP com retry linear.

    - 4xx permanente (exceto 429) falha sem retentar — erro do cliente.
    - 5xx, 429 e erros de conexão são retentados até `tentativas` vezes,
      esperando `backoff * tentativa` segundos entre as tentativas.
    """
    last_exc: Exception | None = None

    for tentativa in range(1, tentativas + 1):
        try:
            r = requests.get(
                url,
                headers=headers or {},
                stream=True,
                timeout=timeout,
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            last_exc = exc
            if tentativa < tentativas:
                time.sleep(backoff * tentativa)
            continue

        # 2xx → entrega.
        if r.ok:
            return r

        # 4xx permanente (exceto 429) → não retenta.
        if 400 <= r.status_code < 500 and r.status_code != 429:
            r.close()
            r.raise_for_status()

        # 5xx ou 429 → fecha, retenta.
        status = r.status_code
        r.close()
        last_exc = requests.HTTPError(f"HTTP {status} em {url}")
        if tentativa < tentativas:
            time.sleep(backoff * tentativa)

    assert last_exc is not None
    raise last_exc


def _download(
    url: str,
    dest: Path,
    *,
    headers: dict[str, str] | None = None,
    expected_magic: bytes | None = None,
    expected_sha256: str | None = None,
) -> str:
    """
    Baixa `url` para `dest` com verificação de magic bytes e SHA-256.

    Retorna o SHA-256 hex do conteúdo baixado e grava um sidecar
    `<dest>.sha256` no formato `sha256sum`.

    Parâmetros
    ----------
    url : str
        Origem do arquivo.
    dest : Path
        Destino final (o download passa por `<dest>.part`).
    headers : dict | None
        Cabeçalhos HTTP adicionais (ex.: `Authorization`).
    expected_magic : bytes | None
        Se informado, valida que os primeiros bytes do arquivo começam
        com esse valor (ex.: `b"PAR1"` para Parquet).
    expected_sha256 : str | None
        Se informado, valida o hash após o download.

    Levanta
    ------
    RuntimeError
        Se o content-type indicar HTML/JSON, se o magic não bater, ou
        se o SHA-256 divergir. O `.part` é removido em qualquer falha.
    """
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.unlink(missing_ok=True)

    h = hashlib.sha256()
    first_bytes = b""
    total = 0
    done = 0

    r = _abrir_stream(
        url,
        headers=headers,
        tentativas=C.HTTP_TENTATIVAS,
        backoff=C.HTTP_BACKOFF,
        timeout=C.HTTP_TIMEOUT,
    )
    try:
        ctype = r.headers.get("content-type", "").lower()
        if "text/html" in ctype or "application/json" in ctype:
            preview = next(r.iter_content(256), b"")
            raise RuntimeError(
                f"Download retornou {ctype!r} em vez de binário. "
                f"URL: {url}\nPrimeiros bytes: {preview[:80]!r}"
            )

        total = int(r.headers.get("content-length", 0))
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(_CHUNK):
                if not chunk:
                    continue
                if not first_bytes:
                    first_bytes = chunk[:16]
                f.write(chunk)
                h.update(chunk)
                done += len(chunk)
                if total:
                    print(
                        f"\rBaixando: {done / 1e6:.0f}/{total / 1e6:.0f} MB",
                        end="",
                        flush=True,
                    )
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    finally:
        r.close()

    print()

    if expected_magic and not first_bytes.startswith(expected_magic):
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"Arquivo baixado não é válido. Esperado começar com "
            f"{expected_magic!r}, recebido {first_bytes[:16]!r}. URL: {url}"
        )

    digest = h.hexdigest()

    if expected_sha256 and digest.lower() != expected_sha256.lower():
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"SHA-256 divergente para {url}.\n"
            f"  esperado: {expected_sha256}\n"
            f"  obtido:   {digest}"
        )

    tmp.replace(dest)
    sha256_path(dest).write_text(
        f"{digest}  {dest.name}\n", encoding="utf-8"
    )
    return digest


def _private_asset_url(token: str) -> str:
    """URL do asset Parquet via API do GitHub (repositório privado)."""
    h = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    url = (
        f"https://api.github.com/repos/{C.GITHUB_REPO}/releases/tags/"
        f"{C.DATA_VERSION}"
    )
    r = requests.get(url, headers=h, timeout=C.HTTP_TIMEOUT)
    r.raise_for_status()

    assets = r.json().get("assets", [])
    asset = next((a for a in assets if a["name"] == C.PARQUET_NAME), None)
    if asset is None:
        nomes = [a["name"] for a in assets]
        raise RuntimeError(
            f"Asset {C.PARQUET_NAME!r} não encontrado na release "
            f"{C.DATA_VERSION!r}. Disponíveis: {nomes}"
        )
    return asset["url"]


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def get_parquet(
    force: bool = False,
    *,
    expected_sha256: str | None = None,
) -> Path:
    """
    Devolve o caminho local do Parquet de SRAG, baixando se necessário.

    Ordem de tentativas:
        1. Release pública do GitHub.
        2. Se (1) falhar e `GITHUB_TOKEN` estiver definido, asset privado
           via API do GitHub.

    Parâmetros
    ----------
    force : bool
        Se True, rebaixa mesmo que o arquivo já exista localmente e
        descarta o sidecar `.sha256` antigo.
    expected_sha256 : str | None
        Se informado, valida o hash do arquivo baixado — divergência
        interrompe o pipeline com `RuntimeError`.

    Retorno
    -------
    Path
        Caminho absoluto do Parquet baixado.

    Efeitos colaterais
    ------------------
    - Parquet gravado em `data/processed/<DATA_VERSION>/<PARQUET_NAME>`.
    - Sidecar `<arquivo>.sha256` com o hash do conteúdo.
    - SHA-256 impresso no stdout para uso em logs/manifests.
    """
    folder = PROCESSED / C.DATA_VERSION
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / C.PARQUET_NAME

    if path.exists() and not force:
        return path

    if force and path.exists():
        path.unlink()
        sha256_path(path).unlink(missing_ok=True)

    public_url = (
        f"https://github.com/{C.GITHUB_REPO}/releases/download/"
        f"{C.DATA_VERSION}/{C.PARQUET_NAME}"
    )

    try:
        digest = _download(
            public_url,
            path,
            expected_magic=PARQUET_MAGIC,
            expected_sha256=expected_sha256,
        )
    except (requests.HTTPError, RuntimeError):
        token = _token()
        if not token:
            raise RuntimeError(
                "Download falhou. Repositório privado ou asset inválido? "
                "Cadastre o segredo GITHUB_TOKEN."
            )
        h = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
        }
        digest = _download(
            _private_asset_url(token),
            path,
            headers=h,
            expected_magic=PARQUET_MAGIC,
            expected_sha256=expected_sha256,
        )

    print(f"[storage] SHA-256: {digest}")
    return path


def read_srag(
    columns: Iterable[str] | None = None,
    filters: list[tuple] | None = None,
) -> pd.DataFrame:
    """
    Lê o Parquet de SRAG como DataFrame.

    Parâmetros
    ----------
    columns : iterable de str | None
        Subconjunto de colunas a carregar (pushdown do Parquet). Se None,
        carrega todas.
    filters : list | None
        Filtros no formato aceito por `pd.read_parquet(filters=...)`.
        Deixe None para carregar o arquivo inteiro.
    """
    return pd.read_parquet(
        get_parquet(),
        columns=list(columns) if columns is not None else None,
        filters=filters,
    )