import os

import pandas as pd
import requests

from src.utils.env import PROCESSED, get_secret
from src.utils import config as C


PARQUET_MAGIC = b"PAR1"


def _token():
    try:
        return get_secret("GITHUB_TOKEN")
    except Exception:
        return os.environ.get("GITHUB_TOKEN")


def _download(url, dest, headers=None, expected_magic=None):
    tmp = dest.with_suffix(".part")

    with requests.get(
        url,
        headers=headers or {},
        stream=True,
        timeout=60,
        allow_redirects=True,
    ) as r:
        r.raise_for_status()

        ctype = r.headers.get("content-type", "").lower()
        if "text/html" in ctype or "application/json" in ctype:
            # Lê só o comecinho pra mostrar no erro
            preview = next(r.iter_content(256), b"")
            tmp.unlink(missing_ok=True)
            raise RuntimeError(
                f"Download retornou {ctype!r} em vez de binário. "
                f"URL: {url}\n"
                f"Primeiros bytes: {preview[:80]!r}"
            )

        total = int(r.headers.get("content-length", 0))
        done = 0
        first_bytes = b""

        with open(tmp, "wb") as f:
            for chunk in r.iter_content(8 * 1024 * 1024):
                if not first_bytes:
                    first_bytes = chunk[:16]
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(
                        f"\rBaixando: {done / 1e6:.0f}/"
                        f"{total / 1e6:.0f} MB",
                        end="",
                        flush=True,
                    )
    print()

    if expected_magic and not first_bytes.startswith(expected_magic):
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"Arquivo baixado não é válido. "
            f"Esperado começar com {expected_magic!r}, "
            f"recebido {first_bytes[:16]!r}. "
            f"URL: {url}"
        )

    tmp.replace(dest)


def _private_asset_url(token):
    h = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    url = (
        f"https://api.github.com/repos/{C.GITHUB_REPO}/releases/tags/"
        f"{C.DATA_VERSION}"
    )
    r = requests.get(url, headers=h, timeout=30)
    r.raise_for_status()

    assets = r.json().get("assets", [])
    asset = next(
        (a for a in assets if a["name"] == C.PARQUET_NAME),
        None,
    )
    if asset is None:
        nomes = [a["name"] for a in assets]
        raise RuntimeError(
            f"Asset {C.PARQUET_NAME!r} não encontrado na release "
            f"{C.DATA_VERSION!r}. Disponíveis: {nomes}"
        )
    return asset["url"]


def get_parquet(force=False):
    folder = PROCESSED / C.DATA_VERSION
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / C.PARQUET_NAME

    if path.exists() and not force:
        return path

    # Se forçar, remove o arquivo antigo (pode estar corrompido)
    if force and path.exists():
        path.unlink()

    public_url = (
        f"https://github.com/{C.GITHUB_REPO}/releases/download/"
        f"{C.DATA_VERSION}/{C.PARQUET_NAME}"
    )

    try:
        _download(
            public_url,
            path,
            expected_magic=PARQUET_MAGIC,
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
        _download(
            _private_asset_url(token),
            path,
            h,
            expected_magic=PARQUET_MAGIC,
        )

    return path


def read_srag(columns=None, filters=None):
    return pd.read_parquet(
        get_parquet(),
        columns=columns,
        filters=filters,
    )