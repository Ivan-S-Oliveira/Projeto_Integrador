import os
import requests

from src.utils.env import PROCESSED, get_secret
from src import config as C


def _token():
    try:
        return get_secret("GITHUB_TOKEN")
    except Exception:
        return os.environ.get("GITHUB_TOKEN")


def _download(url, dest, headers=None):
    tmp = dest.with_suffix(".part")
    with requests.get(url, headers=headers or {}, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(8 * 1024 * 1024):
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\rBaixando: {done / 1e6:.0f}/{total / 1e6:.0f} MB", end="", flush=True)
    print()
    tmp.replace(dest)

def _private_asset_url(token):
    h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/repos/{C.GITHUB_REPO}/releases/tags/{C.DATA_VERSION}"
    r = requests.get(url, headers=h, timeout=30)
    r.raise_for_status()
    asset = next(a for a in r.json()["assets"] if a["name"] == C.PARQUET_NAME)
    return asset["url"]


def get_parquet(force=False):
    folder = PROCESSED / C.DATA_VERSION
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / C.PARQUET_NAME
    if path.exists() and not force:
        return path

    public_url = (
        f"https://github.com/{C.GITHUB_REPO}/releases/download/"
        f"{C.DATA_VERSION}/{C.PARQUET_NAME}"
    )
    try:
        _download(public_url, path)
    except requests.HTTPError:
        token = _token()
        if not token:
            raise RuntimeError("Download falhou. Repositório privado? Cadastre o segredo GITHUB_TOKEN.")
        h = {"Authorization": f"Bearer {token}", "Accept": "application/octet-stream"}
        _download(_private_asset_url(token), path, h)
    return path


def read_srag(columns=None, filters=None):
    import pandas as pd
    return pd.read_parquet(get_parquet(), columns=columns, filters=filters)
