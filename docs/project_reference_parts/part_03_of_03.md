<!-- PROJECT_COMPLETE_REFERENCE part 3/3 -->
## `src/utils/reproducibility.py`

- Git: `tracked` · status `clean`
- Size: `13.1 KB` · modified `2026-10-14 22:03 UTC`
- SHA-256: `3dad1d1621b2ccd9ad50881eeb0a8c1d7da99b3920beb32562e122a016b306cb`

```python
"""
Registro de execuções para reprodutibilidade (critério C1).

Cada execução gera `outputs/runs/<RUN_ID>/` com:
    metadata.json   ← tudo estruturado
    summary.txt     ← versão legível

O metadata captura identificação (run_id, modelo, seed, timestamps),
status (`success` | `error`), erro estruturado quando houver exceção,
versão e SHA-256 do Parquet, estado dos gates, versões de bibliotecas,
commit/branch e ambiente.

Uso:
    from src.utils.reproducibility import Run

    with Run(
        modelo="logistic",
        parametros={"C": 1.0},
        dataset_path=C.ANALYTICAL_DIR / "dataset_supervisionado.parquet",
    ) as r:
        ... treino ...
        r.metrica(auc=0.82, accuracy=0.78)
        r.anotar("split temporal por dt_notific")
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
import traceback

from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

from src.utils import config as C


RUNS_DIR: Path = C.RUNS_DIR


def gerar_run_id(
    modelo: str | None = None,
    base_dir: Path | None = None,
) -> str:
    """
    Gera um identificador único no formato
    `YYYY-MM-DD_HHMMSS_micros[_modelo]`.

    Se `base_dir` for informado, garante unicidade contra o sistema de
    arquivos adicionando sufixo `_NN` em caso de colisão.
    """
    agora = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")
    candidato = f"{agora}_{modelo}" if modelo else agora

    if base_dir is None:
        return candidato

    base = Path(base_dir)
    run_id = candidato
    contador = 1
    while (base / run_id).exists():
        run_id = f"{candidato}_{contador:02d}"
        contador += 1

    return run_id


def _agora() -> dict[str, str]:
    utc = datetime.now(timezone.utc)
    return {
        "utc":   utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "local": utc.astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def _coletar_gates() -> dict[str, str]:
    """Estado atual de cada gate em `supervised.yaml` como `{nome: status}`."""
    gates = C.cfg("gates") or {}
    return {
        nome: (info or {}).get("status", "desconhecido")
        for nome, info in gates.items()
    }


def _resolver_dataset_sha256(
    dataset_sha256: str | None,
    dataset_path: Path | None,
) -> str | None:
    """
    Resolve o SHA-256 do dataset por prioridade: valor explícito, sidecar
    `<dataset_path>.sha256`, ou `None`.
    """
    if dataset_sha256:
        return dataset_sha256
    if dataset_path is None:
        return None
    try:
        from src.utils.storage import read_sha256
        return read_sha256(Path(dataset_path))
    except Exception:
        return None


def _resumo(meta: dict[str, Any]) -> str:
    """`summary.txt` curto e legível a partir do metadata."""
    linhas = [
        f"RUN_ID:   {meta['run_id']}",
        f"MODELO:   {meta['modelo']}",
        f"SEED:     {meta['seed']}",
        f"STATUS:   {meta.get('status', 'desconhecido')}",
    ]

    if meta.get("data_version"):
        linhas.append(f"DADOS:    {meta['data_version']}")
    if meta.get("dataset_sha256"):
        linhas.append(f"SHA-256:  {meta['dataset_sha256']}")

    ds = meta.get("dataset") or {}
    for k in ("n_rows", "train_rows", "valid_rows", "test_rows"):
        if k in ds:
            linhas.append(f"{k.upper():9s} {ds[k]:,}")

    if meta.get("duracao_s") is not None:
        linhas.append(f"DURACAO:  {meta['duracao_s']:.1f}s")

    if meta.get("erro"):
        err = meta["erro"]
        linhas.append("")
        linhas.append("ERRO:")
        linhas.append(f"  tipo:     {err.get('tipo')}")
        linhas.append(f"  mensagem: {err.get('mensagem')}")

    if meta.get("metricas"):
        linhas.append("")
        linhas.append("MÉTRICAS:")
        for k, v in meta["metricas"].items():
            if isinstance(v, float):
                linhas.append(f"  {k:20s} {v:.4f}")
            else:
                linhas.append(f"  {k:20s} {v}")

    if meta.get("parametros"):
        linhas.append("")
        linhas.append("PARÂMETROS:")
        for k, v in meta["parametros"].items():
            linhas.append(f"  {k:20s} {v}")

    if meta.get("gates"):
        linhas.append("")
        linhas.append("GATES:")
        for nome, st in meta["gates"].items():
            linhas.append(f"  {nome:34s} {st}")

    if meta.get("notas"):
        linhas.append("")
        linhas.append(f"NOTAS: {meta['notas']}")

    linhas.append("")
    linhas.append(f"TIMESTAMP_UTC: {meta['timestamp']['utc']}")
    return "\n".join(linhas) + "\n"


def _versoes() -> dict[str, str | None]:
    """Versões das bibliotecas fundamentais da execução."""
    pacotes = [
        "numpy",
        "pandas",
        "pyarrow",
        "scikit-learn",
        "scipy",
        "matplotlib",
        "seaborn",
    ]
    resultado: dict[str, str | None] = {
        "python": platform.python_version(),
    }
    for pacote in pacotes:
        try:
            resultado[pacote] = metadata.version(pacote)
        except metadata.PackageNotFoundError:
            resultado[pacote] = None
    return resultado


def _git_info() -> dict[str, str | bool | None]:
    """Commit, branch e estado da árvore de trabalho."""

    def executar_git(args: list[str]) -> str | None:
        try:
            proc = subprocess.run(
                ["git", *args],
                cwd=C.ROOT_DIR,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except OSError:
            return None
        return proc.stdout.strip() if proc.returncode == 0 else None

    status = executar_git(["status", "--porcelain"])
    return {
        "commit": executar_git(["rev-parse", "HEAD"]),
        "branch": executar_git(["branch", "--show-current"]),
        "dirty":  bool(status) if status is not None else None,
    }


def _env_info() -> dict[str, str | bool]:
    """Informações não sensíveis do ambiente."""
    return {
        "python_executable": sys.executable,
        "python_version":    platform.python_version(),
        "platform":          platform.platform(),
        "cwd":               str(Path.cwd()),
        "ci":                bool(os.getenv("CI") or os.getenv("GITHUB_ACTIONS")),
    }


def registrar_execucao(
    modelo: str,
    *,
    seed: int | None = None,
    parametros: dict[str, Any] | None = None,
    dataset: dict[str, Any] | None = None,
    features: dict[str, Any] | None = None,
    metricas: dict[str, Any] | None = None,
    duracao_s: float | None = None,
    notas: str | None = None,
    run_id: str | None = None,
    output_dir: Path | None = None,
    status: str = "success",
    erro: dict[str, Any] | None = None,
    dataset_sha256: str | None = None,
) -> Path:
    """
    Grava `metadata.json` + `summary.txt` em `outputs/runs/<RUN_ID>/`.

    `status` deve ser `"success"` ou `"error"`; este último deve vir
    acompanhado de `erro` (dict com `tipo`, `mensagem` e opcionalmente
    `traceback`). Se `dataset_sha256` for None, fica ausente do metadata.
    """
    base = Path(output_dir) if output_dir is not None else RUNS_DIR

    if run_id is None:
        run_id = gerar_run_id(modelo=modelo, base_dir=base)

    pasta = base / run_id
    pasta.mkdir(parents=True, exist_ok=False)

    meta: dict[str, Any] = {
        "run_id":         pasta.name,
        "timestamp":      _agora(),
        "modelo":         modelo,
        "seed":           seed if seed is not None else C.SEED,
        "status":         status,
        "erro":           erro,
        "duracao_s":      duracao_s,
        "parametros":     parametros or {},
        "dataset":        dataset or {},
        "dataset_sha256": dataset_sha256,
        "data_version":   C.DATA_VERSION,
        "features":       features or {},
        "metricas":       metricas or {},
        "gates":          _coletar_gates(),
        "notas":          notas,
        "versoes":        _versoes(),
        "git":            _git_info(),
        "env":            _env_info(),
        "supervised_yaml_sha256": C.supervised_yaml_sha256(),
    }

    (pasta / "metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    (pasta / "summary.txt").write_text(_resumo(meta), encoding="utf-8")

    print(f"[reproducibility] run registrado em: {pasta}")
    return pasta


def listar_runs(
    output_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Lista os metadados das execuções registradas, ordenados por `run_id`
    decrescente. Cada item inclui o caminho da pasta em `"pasta"`.
    """
    raiz = Path(output_dir) if output_dir is not None else RUNS_DIR
    if not raiz.exists():
        return []

    runs: list[dict[str, Any]] = []
    for pasta in raiz.iterdir():
        if not pasta.is_dir():
            continue
        metadata_path = pasta / "metadata.json"
        if not metadata_path.exists():
            continue
        try:
            meta = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        meta["pasta"] = str(pasta)
        runs.append(meta)

    return sorted(
        runs,
        key=lambda item: str(item.get("run_id", "")),
        reverse=True,
    )


def carregar_run(
    run: str | Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Carrega o `metadata.json` de uma execução."""
    caminho = Path(run)
    if not caminho.is_absolute():
        caminho = (Path(output_dir) if output_dir else RUNS_DIR) / caminho

    metadata_path = caminho / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata.json não encontrado em {caminho}")

    return json.loads(metadata_path.read_text(encoding="utf-8"))


class Run:
    """
    Context manager de registro de execução.

    Uso::

        with Run(modelo="logistic", parametros={"C": 1.0}) as r:
            ...
            r.metrica(auc=0.82)

    O metadata é gravado sempre ao sair do bloco, inclusive em caso de
    exceção — com `status="error"` e `erro` estruturado. A exceção não
    é suprimida.
    """

    def __init__(
        self,
        modelo: str,
        *,
        seed: int | None = None,
        parametros: dict[str, Any] | None = None,
        dataset: dict[str, Any] | None = None,
        features: dict[str, Any] | None = None,
        notas: str | None = None,
        output_dir: Path | None = None,
        dataset_path: Path | None = None,
        dataset_sha256: str | None = None,
    ) -> None:
        self.modelo         = modelo
        self.seed           = seed
        self.parametros     = dict(parametros or {})
        self.dataset        = dict(dataset or {})
        self.features       = dict(features or {})
        self.notas          = notas
        self.output_dir     = output_dir
        self.dataset_path   = dataset_path
        self.dataset_sha256 = dataset_sha256
        self._metricas: dict[str, Any] = {}
        self._inicio: float | None = None
        self.pasta: Path | None = None

    def metrica(self, **kwargs: Any) -> "Run":
        self._metricas.update(kwargs)
        return self

    def anotar(self, texto: str) -> "Run":
        self.notas = f"{self.notas}\n{texto}" if self.notas else texto
        return self

    def add_dataset(self, **kwargs: Any) -> "Run":
        self.dataset.update(kwargs)
        return self

    def __enter__(self) -> "Run":
        self._inicio = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        duracao = time.perf_counter() - self._inicio if self._inicio else None

        status = "success"
        erro: dict[str, Any] | None = None
        if exc_type is not None:
            status = "error"
            erro = {
                "tipo":      exc_type.__name__,
                "modulo":    getattr(exc_type, "__module__", None),
                "mensagem":  str(exc) if exc is not None else None,
                "traceback": (
                    "".join(traceback.format_exception(exc_type, exc, tb))
                    if tb is not None else None
                ),
            }

        sha = _resolver_dataset_sha256(
            self.dataset_sha256,
            self.dataset_path,
        )

        self.pasta = registrar_execucao(
            modelo=self.modelo,
            seed=self.seed,
            parametros=self.parametros,
            dataset=self.dataset,
            features=self.features,
            metricas=self._metricas,
            duracao_s=duracao,
            notas=self.notas,
            output_dir=self.output_dir,
            status=status,
            erro=erro,
            dataset_sha256=sha,
        )
        return False
```

## `src/utils/storage.py`

- Git: `tracked` · status `clean`
- Size: `8.8 KB` · modified `2026-10-14 22:03 UTC`
- SHA-256: `b5facb82321b483072f759728218833587bb88df959287f56851130b80d95ad9`

```python
"""
Contrato oficial de acesso ao Parquet de SRAG.

Fluxo:
    GitHub Release → data/processed/<DATA_VERSION>/srag.parquet

Tenta primeiro o download público via URL de release. Se falhar e houver
`GITHUB_TOKEN`, cai no asset privado via API do GitHub. Grava um sidecar
`<arquivo>.sha256` com o hash do Parquet baixado — reprodutibilidade e
registro no `Run`. `force=True` rebaixa e descarta o sidecar antigo.

Requer `requests` e `pandas`. Constantes `C.HTTP_TIMEOUT`,
`C.HTTP_TENTATIVAS` e `C.HTTP_BACKOFF` controlam o comportamento de rede.
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
_CHUNK: int = 8 * 1024 * 1024


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

    4xx permanente (exceto 429) falha sem retentar. 5xx, 429 e erros de
    conexão são retentados até `tentativas` vezes, com espera
    `backoff * tentativa` entre elas.
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

        if r.ok:
            return r

        if 400 <= r.status_code < 500 and r.status_code != 429:
            r.close()
            r.raise_for_status()

        status = r.status_code
        r.close()
        last_exc = requests.HTTPError(f"HTTP {status} em {url}")
        if tentativa < tentativas:
            time.sleep(backoff * tentativa)

    assert last_exc is not None
    raise last_exc


def download_file(
    url: str,
    dest: Path,
    *,
    headers: dict[str, str] | None = None,
    expected_magic: bytes | None = None,
    expected_sha256: str | None = None,
) -> str:
    """
    Baixa `url` para `dest` com verificação de magic bytes e SHA-256.

    Retorna o SHA-256 hex do conteúdo e grava um sidecar `<dest>.sha256`
    no formato `sha256sum`. O download passa por `<dest>.part`.

    Levanta `RuntimeError` se o content-type indicar HTML/JSON, se o
    magic não bater ou se o SHA-256 divergir; o `.part` é removido em
    qualquer falha.
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


def get_parquet(
    force: bool = False,
    *,
    expected_sha256: str | None = None,
) -> Path:
    """
    Devolve o caminho local do Parquet de SRAG, baixando se necessário.

    Ordem de tentativas: release pública do GitHub; se falhar e
    `GITHUB_TOKEN` estiver definido, asset privado via API do GitHub.

    Com `force=True`, rebaixa mesmo que o arquivo já exista e descarta o
    sidecar `.sha256` antigo. Se `expected_sha256` for informado, valida
    o hash do arquivo baixado.

    Efeitos colaterais: Parquet gravado em
    `data/processed/<DATA_VERSION>/<PARQUET_NAME>`, sidecar `.sha256`
    ao lado, e SHA-256 impresso no stdout para uso em logs/manifests.
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
        digest = download_file(
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
        digest = download_file(
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

    `columns` restringe o subconjunto carregado (pushdown do Parquet);
    `filters` segue o formato de `pd.read_parquet(filters=...)`.
    """
    return pd.read_parquet(
        get_parquet(),
        columns=list(columns) if columns is not None else None,
        filters=filters,
    )
```

## `tests/conftest.py`

- Git: `tracked` · status `clean`
- Size: `619 B` · modified `2026-10-15 01:27 UTC`
- SHA-256: `3a68e574a37978bd6ef167e91f0e1de85c11cceca3e6d0fddc0b53ad597b051a`

```python
"""Fixtures e configuração de testes."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.utils import config as C


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "slow: testes que tocam arquivos grandes (Parquet de SRAG).",
    )


@pytest.fixture(scope="session")
def parquet_disponivel() -> Path | None:
    """Retorna o Parquet processado, ou None se ainda não foi gerado."""
    caminho = C.PROCESSED_DIR / C.DATA_VERSION / C.PARQUET_NAME
    return caminho if caminho.is_file() else None
```

## `tests/test_calibration.py`

- Git: `tracked` · status `clean`
- Size: `2.8 KB` · modified `2026-10-15 01:27 UTC`
- SHA-256: `a358e478c87b8f127d43f57aa8179dda3c0a80d15e5146488c5cef913df73705`

```python
"""Testes de calibração e escolha de limiar."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.models.calibration import calibrar, escolher_limiar


@pytest.fixture
def dados() -> tuple[np.ndarray, np.ndarray]:
    y = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9, 0.6, 0.3, 0.7, 0.4, 0.85, 0.75])
    return y, p


def test_escolher_limiar_retorna_dict(dados):
    y, p = dados
    r = escolher_limiar(y, p, metrica="f1")
    assert {"limiar", "valor", "metrica", "auc", "brier", "tabela"} <= set(r)
    assert r["metrica"] == "f1"
    assert 0 < r["limiar"] < 1


def test_escolher_limiar_metrica_invalida(dados):
    y, p = dados
    with pytest.raises(ValueError, match="metrica inválida"):
        escolher_limiar(y, p, metrica="nao_existe")  # type: ignore[arg-type]


def test_escolher_limiar_min_precision_respeitado():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    r = escolher_limiar(y, p, metrica="recall", min_precision=0.9)
    linha = r["tabela"][r["tabela"]["limiar"] == r["limiar"]]
    assert linha["precision"].iloc[0] >= 0.9


def test_escolher_limiar_min_precision_impossivel():
    y = np.array([1, 0, 0, 0])
    p = np.array([0.1, 0.9, 0.8, 0.85])
    with pytest.raises(ValueError, match="precision"):
        escolher_limiar(y, p, min_precision=0.5)


def test_calibrar_requer_sklearn_16():
    pytest.importorskip("sklearn.frozen")


def test_calibrar_metodo_invalido():
    pytest.importorskip("sklearn.frozen")
    from sklearn.linear_model import LogisticRegression

    X = pd.DataFrame({"a": [0.0, 1.0, 2.0, 3.0]})
    y = pd.Series([0, 0, 1, 1])
    modelo = LogisticRegression().fit(X, y)

    with pytest.raises(ValueError, match="method inválido"):
        calibrar(modelo, X, y, method="nao_existe")


def test_calibrar_sigmoid_preserva_shape():
    pytest.importorskip("sklearn.frozen")
    from sklearn.linear_model import LogisticRegression

    rng = np.random.RandomState(0)
    X = pd.DataFrame({"a": rng.randn(200)})
    y = pd.Series((X["a"] + rng.randn(200) * 0.1 > 0).astype(int))

    modelo = LogisticRegression().fit(X, y)
    cal = calibrar(modelo, X, y, method="sigmoid")

    proba = cal.predict_proba(X)
    assert proba.shape == (len(X), 2)
    assert np.allclose(proba.sum(axis=1), 1.0)
    assert np.all((proba >= 0) & (proba <= 1))


def test_calibrar_isotonic_preserva_shape():
    pytest.importorskip("sklearn.frozen")
    from sklearn.linear_model import LogisticRegression

    rng = np.random.RandomState(1)
    X = pd.DataFrame({"a": rng.randn(500)})
    y = pd.Series((X["a"] > 0).astype(int))

    modelo = LogisticRegression().fit(X, y)
    cal = calibrar(modelo, X, y, method="isotonic")
    assert cal.predict_proba(X).shape == (len(X), 2)
```

## `tests/test_cohort_source.py`

- Git: `tracked` · status `clean`
- Size: `1.6 KB` · modified `2026-10-15 01:27 UTC`
- SHA-256: `4e884913ed712bc5a09ee798d5575881fce2cebf8b614f3a58251d91468b662b`

```python
from pathlib import Path

import pandas as pd
import pytest

from src.data.cohort_source import cohort_candidates, load_cohort, resolve_cohort_path


def _write(path: Path, value: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"value": [value]}).to_parquet(path, index=False)


def test_padrao_permanece_provisorio(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SRAG_COHORT_KIND", raising=False)
    paths = cohort_candidates(tmp_path)
    _write(paths["provisional"][1], 1)
    _write(paths["final"][0], 2)

    kind, path = resolve_cohort_path(tmp_path)

    assert kind == "provisional"
    assert path.name == "coorte_provisoria_b.parquet"


def test_final_exige_escolha_explicita(tmp_path: Path) -> None:
    path = cohort_candidates(tmp_path)["final"][0]
    _write(path, 2)

    frame, source = load_cohort(tmp_path, kind="final")

    assert frame["value"].tolist() == [2]
    assert source.kind == "final"
    assert source.rows == 1
    assert len(source.sha256) == 64


def test_auto_prefere_final(tmp_path: Path) -> None:
    paths = cohort_candidates(tmp_path)
    _write(paths["provisional"][0], 1)
    _write(paths["final"][0], 2)

    kind, path = resolve_cohort_path(tmp_path, kind="auto")

    assert kind == "final"
    assert path.name == "coorte_final.parquet"


def test_tipo_invalido_falha(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="provisional, final ou auto"):
        resolve_cohort_path(tmp_path, kind="desconhecida")  # type: ignore[arg-type]
```

## `tests/test_config.py`

- Git: `tracked` · status `clean`
- Size: `6.6 KB` · modified `2026-10-15 01:27 UTC`
- SHA-256: `dc180168643b3277219edfbf6b17363d88dc7ce49641076b02db2ec9b8aa6818`

```python
"""Valida a integridade do ambiente e da configuração do projeto."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.utils import config as C
from src.utils import env


def test_root_dir_existe() -> None:
    assert C.ROOT_DIR.exists()
    assert C.ROOT_DIR.is_dir()


def test_root_dir_calculado_a_partir_do_arquivo() -> None:
    esperado = Path(C.__file__).resolve().parents[2]
    assert C.ROOT_DIR == esperado


@pytest.mark.parametrize(
    "chave",
    [
        "DATA_DIR",
        "RAW_DIR",
        "PROCESSED_DIR",
        "REPORTS_DIR",
        "MODELS_DIR",
    ],
)
def test_diretorios_derivam_da_raiz(chave: str) -> None:
    """
    Diretórios do projeto devem derivar de ROOT_DIR.

    Caminhos absolutos podem conter C:/Users ou OneDrive porque esse pode
    ser o local real do clone; o que não pode existir é um caminho pessoal
    gravado diretamente em config.py.
    """
    valor = getattr(C, chave)
    assert isinstance(valor, Path)
    assert valor.is_absolute()
    assert C.ROOT_DIR in valor.parents, (
        f"{chave}={valor} não deriva de ROOT_DIR={C.ROOT_DIR}"
    )


def test_config_nao_contem_caminho_pessoal_hardcoded() -> None:
    """
    Examina apenas atribuições de constantes relacionadas a caminhos.

    Comentários, docstrings e mensagens podem mencionar exemplos como
    C:/Users ou /home sem representar configuração real.
    """
    caminho_config = Path(C.__file__)
    fonte = caminho_config.read_text(encoding="utf-8")
    arvore = ast.parse(fonte, filename=str(caminho_config))

    nomes_de_caminho = {
        "ROOT_DIR", "DATA_DIR", "RAW_DIR", "PROCESSED_DIR",
        "TREINO_DIR", "CONFIGS_DIR", "MODELS_DIR", "OUTPUTS_DIR",
        "RUNS_DIR", "LOGS_DIR", "REPORTS_DIR", "FIGURES_DIR",
        "TABLES_DIR", "PREDICTIONS_DIR", "SUPERVISED_YAML",
    }
    proibidos = ["c:/users/", "/home/", "/users/"]

    problemas = []

    for no in ast.walk(arvore):
        nome_alvo = None
        valor = None

        if isinstance(no, ast.Assign):
            if len(no.targets) != 1:
                continue
            alvo = no.targets[0]
            if isinstance(alvo, ast.Name):
                nome_alvo = alvo.id
                valor = no.value
        elif isinstance(no, ast.AnnAssign):
            alvo = no.target
            if isinstance(alvo, ast.Name):
                nome_alvo = alvo.id
                valor = no.value

        if nome_alvo not in nomes_de_caminho or valor is None:
            continue

        for item in ast.walk(valor):
            if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                continue
            texto = item.value.replace("\\", "/").lower()
            encontrados = [t for t in proibidos if t in texto]
            if encontrados:
                problemas.append({
                    "constante": nome_alvo,
                    "valor": item.value,
                    "termos": encontrados,
                })

    assert not problemas, (
        "Foram encontrados caminhos pessoais hard-coded em constantes "
        f"de configuração: {problemas}"
    )


def test_seed_definido() -> None:
    assert isinstance(C.SEED, int)
    assert C.SEED == 42


def test_random_state_igual_ao_seed() -> None:
    assert C.RANDOM_STATE == C.SEED


def test_repo_e_data_version_definidos() -> None:
    assert C.GITHUB_REPO
    assert "/" in C.GITHUB_REPO
    assert C.DATA_VERSION
    assert C.PARQUET_NAME.endswith(".parquet")


def test_srag_parquet_url_padrao(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SRAG_PARQUET_URL", raising=False)

    url_esperada = (
        f"https://github.com/{C.GITHUB_REPO}/releases/download/"
        f"{C.DATA_VERSION}/{C.PARQUET_NAME}"
    )

    assert C.srag_parquet_url() == url_esperada


def test_srag_parquet_url_permite_sobrescrita(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    url_customizada = "https://example.org/dados/srag_teste.parquet"
    monkeypatch.setenv("SRAG_PARQUET_URL", url_customizada)

    assert C.srag_parquet_url() == url_customizada


def test_srag_parquet_url_vazia_volta_ao_padrao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SRAG_PARQUET_URL", "   ")

    url_esperada = (
        f"https://github.com/{C.GITHUB_REPO}/releases/download/"
        f"{C.DATA_VERSION}/{C.PARQUET_NAME}"
    )

    assert C.srag_parquet_url() == url_esperada


def test_parametros_http_razoaveis() -> None:
    assert C.HTTP_TIMEOUT > 0
    assert C.HTTP_TENTATIVAS >= 1
    assert C.HTTP_BACKOFF >= 0


def test_env_aponta_para_mesma_raiz() -> None:
    assert env.ROOT == C.ROOT_DIR


def test_env_diretorios_padrao_existem() -> None:
    env.garantir_diretorios()
    for caminho in (env.RAW, env.PROCESSED, env.TREINO, env.FIGURES):
        assert caminho.exists(), (
            f"{caminho} não foi criado por env.garantir_diretorios()"
        )
        assert caminho.is_dir(), f"{caminho} existe, mas não é um diretório."


def test_env_resumo_nao_quebra() -> None:
    texto = env.resumo()
    assert "ROOT_DIR" in texto
    assert "ENV" in texto


def test_get_secret_obrigatorio_levanta_erro(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    nome = "VAR_QUE_NAO_EXISTE_XYZ"
    monkeypatch.delenv(nome, raising=False)
    with pytest.raises(RuntimeError, match=nome):
        env.get_secret(nome)


def test_get_secret_opcional_retorna_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    nome = "VAR_OPCIONAL_XYZ"
    monkeypatch.delenv(nome, raising=False)
    assert env.get_secret(nome, obrigatorio=False) is None


@pytest.mark.slow
def test_features_finais_existem_no_schema(parquet_disponivel) -> None:
    """
    Verifica se as colunas esperadas existem no Parquet.

    Features derivadas (produzidas por `montar_features`) não existem no
    Parquet bruto — são excluídas da checagem. As colunas de entrada
    exigidas pela derivação são verificadas explicitamente.
    """
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    import pyarrow.parquet as pq
    from src.models import pipeline

    colunas = set(pq.read_schema(parquet_disponivel).names)

    derivadas = set(C.cfg("features", "engenharia", "derivadas") or [])
    base = set(pipeline.FEATURES) - derivadas
    entradas = set(C.cfg("features", "engenharia", "entradas") or [])

    faltando = (base | entradas) - colunas
    assert not faltando, (
        f"Colunas exigidas não existem no Parquet: {sorted(faltando)}"
    )
```

## `tests/test_errors.py`

- Git: `tracked` · status `clean`
- Size: `4.2 KB` · modified `2026-10-15 01:27 UTC`
- SHA-256: `a5fac6c4ac69a36e4ddf2f673b545ffa4805d8ba1b965790a3cefa9fef9b84cc`

```python
"""Testes de análise de erros em `src.evaluation.errors`."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.evaluation.errors import (
    extrair_falsos_negativos,
    extrair_falsos_positivos,
    matriz_confusao,
    metricas_por_grupo,
    top_erros,
)


@pytest.fixture
def dados() -> tuple[np.ndarray, np.ndarray]:
    y_true = np.array([0, 0, 1, 1, 0, 1, 0, 1])
    y_pred = np.array([0, 1, 1, 0, 0, 1, 1, 1])
    return y_true, y_pred


def test_matriz_confusao_shape_e_valores(dados) -> None:
    y_true, y_pred = dados
    m = matriz_confusao(y_true, y_pred)
    assert {"pred_0", "pred_1"}.issubset(m.columns)
    assert {"real_0", "real_1"}.issubset(m.index)
    assert m.loc["real_0", "pred_1"] == 2
    assert m.loc["real_1", "pred_0"] == 1


def test_matriz_confusao_tem_totais(dados) -> None:
    y_true, y_pred = dados
    m = matriz_confusao(y_true, y_pred)
    assert "total" in m.columns
    assert "total" in m.index
    assert m.loc["total", "total"] == len(y_true)


def test_extrair_fp(dados) -> None:
    y_true, y_pred = dados
    df = pd.DataFrame({"x": range(len(y_true))})
    fp = extrair_falsos_positivos(df, y_true, y_pred)
    assert len(fp) == 2
    assert set(fp["x"]) == {1, 6}


def test_extrair_fn(dados) -> None:
    y_true, y_pred = dados
    df = pd.DataFrame({"x": range(len(y_true))})
    fn = extrair_falsos_negativos(df, y_true, y_pred)
    assert len(fn) == 1
    assert fn["x"].iloc[0] == 3


def test_metricas_por_grupo_coluna_renomeada() -> None:
    """A coluna de prevalência chama-se `taxa_positivos`, não `positivos`."""
    n = 300
    df = pd.DataFrame({"grupo": ["A"] * n + ["B"] * n})
    y = pd.Series(np.tile([0, 1], n))
    p = pd.Series(np.tile([0.1, 0.9], n))

    r = metricas_por_grupo(df, y, p, "grupo", min_n=10)
    assert "taxa_positivos" in r.columns
    assert "positivos" not in r.columns


def test_metricas_por_grupo_ignora_abaixo_de_min_n() -> None:
    df = pd.DataFrame({"grupo": ["A"] * 5 + ["B"] * 300})
    y = pd.Series([0, 1] * 152 + [0])
    p = pd.Series([0.1, 0.9] * 152 + [0.5])

    r = metricas_por_grupo(df, y, p, "grupo", min_n=30)
    assert set(r["grupo"]) == {"B"}
    assert r.loc[r["grupo"] == "B", "n"].iloc[0] == 300


def test_metricas_por_grupo_coluna_ausente() -> None:
    df = pd.DataFrame({"outra": [1, 2]})
    y = np.array([0, 1])
    p = np.array([0.1, 0.9])
    with pytest.raises(KeyError):
        metricas_por_grupo(df, y, p, "grupo")


def test_metricas_por_grupo_tamanho_incompativel() -> None:
    df = pd.DataFrame({"grupo": ["A"] * 5})
    y = np.array([0, 1, 0, 1, 0, 1])
    p = np.array([0.1, 0.9, 0.2, 0.8, 0.3, 0.7])
    with pytest.raises(ValueError):
        metricas_por_grupo(df, y, p, "grupo")


def test_top_erros_erro_absoluto() -> None:
    df = pd.DataFrame({"x": range(6)})
    y_true = np.array([0, 0, 1, 1, 0, 1])
    y_prob = np.array([0.1, 0.9, 0.1, 0.9, 0.5, 0.5])

    t = top_erros(df, y_true, y_prob, n=3, criterio="erro_absoluto")
    assert len(t) == 3
    for c in ("y_true", "y_prob", "y_pred", "erro_abs"):
        assert c in t.columns


def test_top_erros_fp_ordena_por_prob_decrescente() -> None:
    df = pd.DataFrame({"x": range(5)})
    y_true = np.array([0, 0, 1, 1, 0])
    y_prob = np.array([0.1, 0.9, 0.1, 0.9, 0.6])

    t = top_erros(df, y_true, y_prob, n=5, criterio="fp")
    assert (t["y_true"] == 0).all()
    assert (t["y_pred"] == 1).all()
    assert t["y_prob"].is_monotonic_decreasing


def test_top_erros_fn_ordena_por_prob_crescente() -> None:
    df = pd.DataFrame({"x": range(5)})
    y_true = np.array([0, 0, 1, 1, 1])
    y_prob = np.array([0.1, 0.9, 0.1, 0.4, 0.9])

    t = top_erros(df, y_true, y_prob, n=5, criterio="fn")
    assert (t["y_true"] == 1).all()
    assert (t["y_pred"] == 0).all()
    assert t["y_prob"].is_monotonic_increasing


def test_top_erros_criterio_invalido() -> None:
    df = pd.DataFrame({"x": [1, 2]})
    y_true = np.array([0, 1])
    y_prob = np.array([0.1, 0.9])
    with pytest.raises(ValueError, match="criterio inválido"):
        top_erros(df, y_true, y_prob, criterio="xxx")  # type: ignore[arg-type]
```

## `tests/test_features.py`

- Git: `tracked` · status `clean`
- Size: `11.5 KB` · modified `2026-10-15 01:27 UTC`
- SHA-256: `657c35d55c5b7e2103d4cefa9a435cd11070573f036fbbb6d6c9fc37ffcd1ddd`

```python
"""
Testes de engenharia de atributos — src/features/engineering.py.

Cobre funções puras e o orquestrador `montar_features`:
contrato de cada derivada, casos inválidos, não-mutação da entrada,
invariante de ponto-no-tempo e ponto único de verdade.

Não testa parsing do YAML — responsabilidade de src/utils/config.py.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.features.engineering import (
    ano_mes_internacao,
    faixa_etaria,
    idade_em_anos,
    intervalo_sintomas_internacao,
    montar_features,
    sazonalidade,
    sexo_categoria,
)


ENTRADAS_OBRIGATORIAS = [
    "nu_idade_n",
    "tp_idade",
    "cs_sexo",
    "dt_sin_pri",
    "dt_interna",
]


@pytest.fixture
def df_base() -> pd.DataFrame:
    """
    DataFrame mínimo com as colunas exigidas por `montar_features`.

    Linhas:
    - 0: adulto (30a), 4 dias até internação, M
    - 1: bebê (6 meses), 5 dias, F
    - 2: adulto (40a), 5 dias, sexo ignorado
    - 3: recém-nascido (1 dia), 5 dias, M
    """
    return pd.DataFrame(
        {
            "nu_idade_n": [30, 6, 40, 1],
            "tp_idade":   [3, 2, 3, 1],
            "cs_sexo":    ["M", "F", "I", "M"],
            "dt_sin_pri": ["2024-01-01", "2024-03-15", "2024-06-20", "2024-09-05"],
            "dt_interna": ["2024-01-05", "2024-03-20", "2024-06-25", "2024-09-10"],
        }
    )


class TestIdadeEmAnos:
    def test_anos_direto(self, df_base: pd.DataFrame) -> None:
        assert idade_em_anos(df_base).iloc[0] == pytest.approx(30.0)

    def test_meses_convertidos(self, df_base: pd.DataFrame) -> None:
        assert idade_em_anos(df_base).iloc[1] == pytest.approx(0.5)

    def test_dias_convertidos(self, df_base: pd.DataFrame) -> None:
        assert idade_em_anos(df_base).iloc[3] == pytest.approx(1 / 365.25)

    def test_retorna_float64(self, df_base: pd.DataFrame) -> None:
        assert idade_em_anos(df_base).dtype == np.float64

    def test_tipo_invalido_vira_nan(self) -> None:
        df = pd.DataFrame({"nu_idade_n": [10], "tp_idade": [9]})
        assert pd.isna(idade_em_anos(df)).all()

    def test_idade_negativa_vira_nan(self) -> None:
        df = pd.DataFrame({"nu_idade_n": [-1], "tp_idade": [3]})
        assert pd.isna(idade_em_anos(df)).all()

    def test_idade_acima_de_120_vira_nan(self) -> None:
        df = pd.DataFrame({"nu_idade_n": [200], "tp_idade": [3]})
        assert pd.isna(idade_em_anos(df)).all()

    def test_nao_muta_entrada(self, df_base: pd.DataFrame) -> None:
        antes = df_base.copy(deep=True)
        idade_em_anos(df_base)
        pd.testing.assert_frame_equal(df_base, antes)


class TestIntervaloSintomasInternacao:
    def test_intervalo_positivo(self, df_base: pd.DataFrame) -> None:
        out = intervalo_sintomas_internacao(df_base)
        assert out["dias_sintomas_ate_internacao"].iloc[0] == pytest.approx(4.0)

    def test_tipos_das_colunas(self, df_base: pd.DataFrame) -> None:
        out = intervalo_sintomas_internacao(df_base)
        assert out["dias_sintomas_ate_internacao"].dtype == np.float64
        assert out["flag_intervalo_invalido"].dtype == np.int8
        assert out["flag_internacao_antes_sintomas"].dtype == np.int8

    def test_negativo_seta_ambas_flags(self) -> None:
        df = pd.DataFrame(
            {"dt_sin_pri": ["2024-01-10"], "dt_interna": ["2024-01-05"]}
        )
        out = intervalo_sintomas_internacao(df)
        assert out["flag_internacao_antes_sintomas"].iloc[0] == 1
        assert out["flag_intervalo_invalido"].iloc[0] == 1

    def test_acima_do_limite_seta_flag_umbrella_sem_marcar_sinal(self) -> None:
        df = pd.DataFrame(
            {"dt_sin_pri": ["2024-01-01"], "dt_interna": ["2024-06-01"]}
        )
        out = intervalo_sintomas_internacao(df)
        assert out["flag_intervalo_invalido"].iloc[0] == 1
        assert out["flag_internacao_antes_sintomas"].iloc[0] == 0

    def test_data_ausente_seta_flag_umbrella(self) -> None:
        df = pd.DataFrame(
            {"dt_sin_pri": [None], "dt_interna": ["2024-01-05"]}
        )
        out = intervalo_sintomas_internacao(df)
        assert pd.isna(out["dias_sintomas_ate_internacao"].iloc[0])
        assert out["flag_intervalo_invalido"].iloc[0] == 1

    def test_politica_sinalizar_mantem_valor_bruto(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Default: valor inválido fica visível, comunicado por flags."""
        df = pd.DataFrame(
            {"dt_sin_pri": ["2024-01-10"], "dt_interna": ["2024-01-05"]}
        )
        monkeypatch.setattr(
            "src.features.engineering._intervalo_politica",
            lambda: "sinalizar",
        )
        out = intervalo_sintomas_internacao(df)
        assert out["dias_sintomas_ate_internacao"].iloc[0] == pytest.approx(-5.0)

    def test_politica_descartar_substitui_por_nan(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        df = pd.DataFrame(
            {"dt_sin_pri": ["2024-01-10"], "dt_interna": ["2024-01-05"]}
        )
        monkeypatch.setattr(
            "src.features.engineering._intervalo_politica",
            lambda: "descartar",
        )
        out = intervalo_sintomas_internacao(df)
        assert pd.isna(out["dias_sintomas_ate_internacao"].iloc[0])
        assert out["flag_intervalo_invalido"].iloc[0] == 1


class TestSazonalidade:
    def test_gera_sin_e_cos_no_intervalo(self, df_base: pd.DataFrame) -> None:
        out = sazonalidade(df_base)
        assert set(out.columns) == {"sin_semana", "cos_semana"}
        for col in out.columns:
            assert out[col].between(-1.0, 1.0, inclusive="both").all()

    def test_mesma_semana_em_anos_diferentes_proxima(self) -> None:
        df = pd.DataFrame(
            {"dt_sin_pri": ["2023-03-15", "2024-03-13"]}  # ~mesma semana ISO
        )
        out = sazonalidade(df)
        assert abs(out["sin_semana"].iloc[0] - out["sin_semana"].iloc[1]) < 0.1
        assert abs(out["cos_semana"].iloc[0] - out["cos_semana"].iloc[1]) < 0.1

    def test_data_nula_vira_nan(self) -> None:
        df = pd.DataFrame({"dt_sin_pri": [None]})
        out = sazonalidade(df)
        assert pd.isna(out["sin_semana"].iloc[0])
        assert pd.isna(out["cos_semana"].iloc[0])

    def test_coluna_ausente_levanta_keyerror(self) -> None:
        df = pd.DataFrame({"outra_data": ["2024-01-01"]})
        with pytest.raises(KeyError, match="Coluna temporal ausente"):
            sazonalidade(df, coluna_data="dt_sin_pri")


class TestFaixaEtaria:
    def test_fronteiras_semiabertas(self) -> None:
        idades = pd.Series([0.0, 0.99, 1.0, 4.99, 5.0, 80.0, 120.0])
        out = faixa_etaria(idades)
        assert list(out) == ["<1", "<1", "1-4", "1-4", "5-11", "80+", "80+"]

    def test_idade_nula_vira_desconhecida(self) -> None:
        out = faixa_etaria(pd.Series([np.nan, 30.0]))
        assert out.iloc[0] == "desconhecida"
        assert out.iloc[1] == "18-39"

    def test_retorna_categoria(self) -> None:
        out = faixa_etaria(pd.Series([30.0]))
        assert isinstance(out.dtype, pd.CategoricalDtype)


class TestSexoCategoria:
    @pytest.mark.parametrize(
        "entrada, esperado",
        [
            ("M", "masculino"),
            ("f", "feminino"),
            (" I ", "ignorado"),
            ("X", "ausente"),
            (None, "ausente"),
        ],
    )
    def test_mapeamento(self, entrada: str | None, esperado: str) -> None:
        df = pd.DataFrame({"cs_sexo": [entrada]})
        assert sexo_categoria(df).iloc[0] == esperado

    def test_retorna_categoria(self) -> None:
        df = pd.DataFrame({"cs_sexo": ["M"]})
        assert isinstance(sexo_categoria(df).dtype, pd.CategoricalDtype)


class TestAnoMesInternacao:
    def test_extrai_ano_e_mes(self, df_base: pd.DataFrame) -> None:
        out = ano_mes_internacao(df_base)
        assert out["ano_internacao"].tolist() == [2024.0] * 4
        assert out["mes_internacao"].tolist() == [1.0, 3.0, 6.0, 9.0]

    def test_data_nula_vira_nan(self) -> None:
        df = pd.DataFrame({"dt_interna": [None]})
        out = ano_mes_internacao(df)
        assert pd.isna(out["ano_internacao"].iloc[0])
        assert pd.isna(out["mes_internacao"].iloc[0])


COLUNAS_DERIVADAS_ESPERADAS = {
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "flag_intervalo_invalido",
    "flag_internacao_antes_sintomas",
    "sin_semana",
    "cos_semana",
    "faixa_etaria",
    "sexo_categoria",
    "ano_internacao",
    "mes_internacao",
}


class TestMontarFeatures:
    def test_gera_todas_as_derivadas_do_yaml(self, df_base: pd.DataFrame) -> None:
        """Trava o contrato entre features.engenharia.derivadas e a função."""
        out = montar_features(df_base)
        faltando = COLUNAS_DERIVADAS_ESPERADAS - set(out.columns)
        assert not faltando, f"Derivadas ausentes: {sorted(faltando)}"

    def test_nao_muta_entrada(self, df_base: pd.DataFrame) -> None:
        antes = df_base.copy(deep=True)
        montar_features(df_base)
        pd.testing.assert_frame_equal(df_base, antes)

    def test_preserva_colunas_originais(self, df_base: pd.DataFrame) -> None:
        out = montar_features(df_base)
        for col in df_base.columns:
            assert col in out.columns

    def test_nao_gera_colunas_proibidas(self, df_base: pd.DataFrame) -> None:
        proibidas = {"evolucao", "alvo_obito_srag", "dt_evoluca", "uti", "cluster"}
        out = montar_features(df_base)
        assert proibidas.isdisjoint(out.columns)


class TestPontoNoTempo:
    """
    Invariantes contra vazamento temporal.

    O ponto de previsão é a admissão hospitalar.
    """

    def test_so_precisa_das_entradas_declaradas(self, df_base: pd.DataFrame) -> None:
        """
        Se `montar_features` só depende de features.engenharia.entradas,
        um df com exatamente essas colunas deve bastar.
        """
        df = df_base[ENTRADAS_OBRIGATORIAS].copy()
        out = montar_features(df)
        assert out is not None
        assert COLUNAS_DERIVADAS_ESPERADAS.issubset(out.columns)

    def test_colunas_pos_admissao_nao_influenciam(
        self, df_base: pd.DataFrame
    ) -> None:
        """Injetar colunas pós-alta não pode alterar a saída."""
        baseline = montar_features(df_base)

        df_contaminado = df_base.copy()
        df_contaminado["evolucao"] = [1.0, 2.0, 1.0, 2.0]
        df_contaminado["dt_evoluca"] = pd.to_datetime(
            ["2024-02-01", "2024-04-01", "2024-07-01", "2024-10-01"]
        )
        df_contaminado["uti"] = [0, 1, 0, 1]
        df_contaminado["suport_ven"] = [0, 1, 0, 0]

        contaminado = montar_features(df_contaminado)

        pd.testing.assert_frame_equal(
            baseline[list(COLUNAS_DERIVADAS_ESPERADAS)].reset_index(drop=True),
            contaminado[list(COLUNAS_DERIVADAS_ESPERADAS)].reset_index(drop=True),
        )

    def test_ordem_das_linhas_nao_altera_derivadas(
        self, df_base: pd.DataFrame
    ) -> None:
        """Derivadas devem ser pointwise — sem dependência de ordem."""
        normal = montar_features(df_base)
        invertido = montar_features(df_base.iloc[::-1].reset_index(drop=True))

        pd.testing.assert_frame_equal(
            normal[list(COLUNAS_DERIVADAS_ESPERADAS)].reset_index(drop=True),
            invertido[list(COLUNAS_DERIVADAS_ESPERADAS)]
            .iloc[::-1]
            .reset_index(drop=True),
        )
```

## `tests/test_leakage.py`

- Git: `tracked` · status `clean`
- Size: `8.2 KB` · modified `2026-10-15 01:27 UTC`
- SHA-256: `1fe6e1ab07debe6766ead96638585f85553e72357180582025ad1af0489d03f0`

```python
"""
Testes anti-vazamento de dados.

Protegem contra:
- inclusão do alvo nas features;
- inclusão de colunas posteriores ao desfecho;
- quebra da ordem temporal entre treino, validação e holdout;
- duplicação de identificadores quando houver chave adequada.

Fonte única de verdade: `configs/supervised.yaml`, lido via
`src.utils.config` (`features.proibidas`) — nada hard-coded aqui.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.utils import config as C


@pytest.fixture
def proibidas() -> set[str]:
    """Colunas proibidas declaradas em `features.proibidas` do YAML."""
    return set(C.cfg("features", "proibidas") or [])


@pytest.fixture
def features_finais() -> set[str]:
    """Lista final de features exposta por `src.models.pipeline`."""
    from src.models import pipeline
    return set(pipeline.FEATURES)


def _forcar_status_gate(
    monkeypatch: pytest.MonkeyPatch,
    nome_gate: str,
    status: str,
) -> None:
    """
    Faz `C.cfg("gates", nome_gate)` devolver `{"status": status}`,
    ignorando o YAML real apenas para esse gate.
    """
    monkeypatch.setattr(
        C,
        "cfg",
        lambda *chaves, default=None: (
            {"status": status}
            if chaves == ("gates", nome_gate)
            else default
        ),
    )


def test_proibidas_nao_vazia(proibidas: set[str]) -> None:
    assert proibidas, (
        "features.proibidas está vazia no supervised.yaml — "
        "ao menos o alvo e as colunas posteriores ao desfecho precisam "
        "estar listadas."
    )


def test_alvo_esta_entre_proibidas(proibidas: set[str]) -> None:
    alvo = C.cfg("target", "coluna")
    assert alvo in proibidas, (
        f"target.coluna ({alvo!r}) precisa estar em features.proibidas."
    )


def test_features_finais_sem_proibidas(
    features_finais: set[str],
    proibidas: set[str],
) -> None:
    vazamento = features_finais & proibidas
    assert not vazamento, (
        f"FEATURES contém colunas proibidas: {sorted(vazamento)}"
    )


def test_features_finais_nao_inclui_alvo(features_finais: set[str]) -> None:
    alvo = C.cfg("target", "coluna")
    assert alvo not in features_finais


def test_check_leakage_passa_quando_X_limpo() -> None:
    from src.evaluation.leakage import check_leakage

    X = pd.DataFrame({"feat_a": [1, 2, 3], "feat_b": [4, 5, 6]})
    check_leakage(X)


def test_check_leakage_levanta_para_proibida(proibidas: set[str]) -> None:
    from src.evaluation.leakage import LeakageError, check_leakage

    coluna = sorted(proibidas)[0]
    X = pd.DataFrame({coluna: [1, 2, 3], "feat_ok": [4, 5, 6]})

    with pytest.raises(LeakageError) as exc:
        check_leakage(X)

    assert coluna in str(exc.value), (
        "A mensagem de erro precisa citar a coluna problemática."
    )


def test_check_leakage_levanta_para_alvo() -> None:
    from src.evaluation.leakage import LeakageError, check_leakage

    alvo = C.cfg("target", "coluna")
    X = pd.DataFrame({alvo: [0, 1, 0], "feat_ok": [1, 2, 3]})

    with pytest.raises(LeakageError):
        check_leakage(X)


def test_check_leakage_lista_vazia_ainda_verifica_alvo() -> None:
    """Lista vazia desliga proibidas, mas o alvo continua sendo checado."""
    from src.evaluation.leakage import LeakageError, check_leakage

    alvo = C.cfg("target", "coluna")
    X = pd.DataFrame({alvo: [0, 1, 0], "feat_ok": [1, 2, 3]})

    with pytest.raises(LeakageError):
        check_leakage(X, forbidden_columns=[])


def test_split_temporal_3way_respeita_ordem() -> None:
    from src.evaluation.temporal import split_temporal_3way

    df = pd.DataFrame({
        "dt_notific": pd.date_range("2020-01-01", periods=100, freq="D"),
        "valor": range(100),
    })

    treino, validacao, holdout = split_temporal_3way(
        df,
        coluna_tempo="dt_notific",
        frac_treino=0.70,
        frac_validacao=0.15,
    )

    assert not treino.empty
    assert not validacao.empty
    assert not holdout.empty

    assert treino["dt_notific"].max() <= validacao["dt_notific"].min()
    assert validacao["dt_notific"].max() <= holdout["dt_notific"].min()


def test_split_temporal_3way_rejeita_nat_por_default() -> None:
    from src.evaluation.temporal import split_temporal_3way

    df = pd.DataFrame({
        "dt_notific": [
            pd.Timestamp("2020-01-01"),
            pd.NaT,
            pd.Timestamp("2020-01-03"),
        ],
        "valor": [1, 2, 3],
    })

    with pytest.raises(ValueError, match="data inválida"):
        split_temporal_3way(df, coluna_tempo="dt_notific")


def test_split_temporal_3way_dropa_nat_quando_pedido() -> None:
    from src.evaluation.temporal import split_temporal_3way

    df = pd.DataFrame({
        "dt_notific": pd.date_range("2020-01-01", periods=10, freq="D"),
        "valor": range(10),
    })
    df.loc[3, "dt_notific"] = pd.NaT

    treino, validacao, holdout = split_temporal_3way(
        df,
        coluna_tempo="dt_notific",
        on_nat="drop",
    )

    assert len(treino) + len(validacao) + len(holdout) == 9


def test_temporal_split_bloqueia_holdout_antes_de_concluir() -> None:
    from src.evaluation.temporal import TemporalSplit

    df = pd.DataFrame({
        "dt_notific": pd.date_range("2020-01-01", periods=100, freq="D"),
        "valor": range(100),
    })
    split = TemporalSplit(df=df, coluna_tempo="dt_notific")

    assert not split.holdout_liberado
    with pytest.raises(RuntimeError, match="Holdout bloqueado"):
        split.holdout()


def test_concluir_selecao_exige_gate_g9_holdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    `concluir_selecao` só libera o holdout quando `gates.G9_holdout`
    estiver `aprovado`; com o gate pendente, deve levantar RuntimeError.
    """
    from src.evaluation.temporal import TemporalSplit

    _forcar_status_gate(monkeypatch, "G9_holdout", "pendente")

    df = pd.DataFrame({
        "dt_notific": pd.date_range("2020-01-01", periods=100, freq="D"),
        "valor": range(100),
    })
    split = TemporalSplit(df=df, coluna_tempo="dt_notific")

    with pytest.raises(RuntimeError, match="G9_holdout"):
        split.concluir_selecao()

    assert not split.holdout_liberado


def test_concluir_selecao_libera_holdout_quando_gate_aprovado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Com o gate `G9_holdout` aprovado (simulado), libera o holdout."""
    from src.evaluation.temporal import TemporalSplit

    _forcar_status_gate(monkeypatch, "G9_holdout", "aprovado")

    df = pd.DataFrame({
        "dt_notific": pd.date_range("2020-01-01", periods=100, freq="D"),
        "valor": range(100),
    })
    split = TemporalSplit(df=df, coluna_tempo="dt_notific")

    split.concluir_selecao()
    assert split.holdout_liberado
    assert not split.holdout().empty


def test_dataset_sem_identificadores_duplicados(parquet_disponivel) -> None:
    """
    Checa duplicidade apenas se houver coluna que sirva como
    identificador da notificação. UF e data não formam chave única.
    """
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    import pyarrow.parquet as pq

    colunas = set(pq.read_schema(parquet_disponivel).names)

    candidatas = [
        "nu_notific",
        "numero_notificacao",
        "id_notificacao",
        "id",
    ]
    coluna_id = next((c for c in candidatas if c in colunas), None)

    if coluna_id is None:
        pytest.skip(
            "O Parquet não possui uma coluna identificadora adequada "
            "para o teste de duplicidade."
        )

    df = pd.read_parquet(parquet_disponivel, columns=[coluna_id])
    ids = df[coluna_id].dropna().astype("string").str.strip()
    ids = ids[ids.ne("")]

    if ids.empty:
        pytest.skip(f"A coluna {coluna_id} não possui identificadores válidos.")

    quantidade_duplicada = int(ids.duplicated().sum())
    taxa_duplicada = quantidade_duplicada / len(ids)

    assert taxa_duplicada < 0.05, (
        f"Alta taxa de identificadores duplicados em {coluna_id}: "
        f"{quantidade_duplicada}/{len(ids)} ({taxa_duplicada:.1%})"
    )
```

## `tests/test_metrics.py`

- Git: `tracked` · status `clean`
- Size: `3.8 KB` · modified `2026-10-15 01:27 UTC`
- SHA-256: `df282a53d2c7cc1bf9cf388f3227f7a2394b98c5e593079353ef83b393b7a510`

```python
"""Testes das métricas em `src.evaluation.metrics`."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.evaluation.metrics import (
    accuracy,
    auc,
    average_precision,
    brier,
    f1,
    ic_bootstrap,
    metricas_completas,
    metricas_por_limiar,
    precision,
    recall,
)


@pytest.fixture
def y_true() -> np.ndarray:
    return np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])


@pytest.fixture
def y_prob() -> np.ndarray:
    return np.array([0.1, 0.2, 0.8, 0.9, 0.6, 0.3, 0.7, 0.4, 0.85, 0.75])


def test_auc_perfeito() -> None:
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    assert auc(y, p) == pytest.approx(1.0)


def test_auc_constante_e_meio() -> None:
    y = np.array([0, 0, 1, 1])
    p = np.array([0.5, 0.5, 0.5, 0.5])
    assert auc(y, p) == pytest.approx(0.5)


def test_metricas_individuais_retornam_float(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    for fn in (auc, average_precision, brier):
        assert isinstance(fn(y_true, y_prob), float)


def test_average_precision_em_intervalo(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    ap = average_precision(y_true, y_prob)
    assert 0.0 <= ap <= 1.0


def test_brier_em_intervalo(y_true: np.ndarray, y_prob: np.ndarray) -> None:
    assert 0.0 <= brier(y_true, y_prob) <= 1.0


def test_f1_precision_recall(y_true: np.ndarray) -> None:
    y_pred = np.array([0, 0, 1, 1, 1, 0, 0, 0, 1, 1])
    for fn in (f1, precision, recall):
        v = fn(y_true, y_pred)
        assert isinstance(v, float)
        assert 0.0 <= v <= 1.0


def test_accuracy_perfeita() -> None:
    y = np.array([0, 1, 0, 1])
    assert accuracy(y, y) == pytest.approx(1.0)


def test_zero_division_nao_quebra() -> None:
    y_true = np.zeros(3, dtype=int)
    y_pred = np.zeros(3, dtype=int)
    assert f1(y_true, y_pred) == 0.0
    assert precision(y_true, y_pred) == 0.0
    assert recall(y_true, y_pred) == 0.0


def test_metricas_completas_chaves(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    d = metricas_completas(y_true, y_prob, limiar=0.5)
    for k in (
        "auc",
        "ap",
        "brier",
        "f1",
        "precision",
        "recall",
        "accuracy",
        "limiar",
        "n",
    ):
        assert k in d
    assert d["limiar"] == 0.5
    assert d["n"] == float(len(y_true))


def test_metricas_completas_aceita_series(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    d = metricas_completas(pd.Series(y_true), pd.Series(y_prob))
    assert "auc" in d


def test_metricas_por_limiar(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    t = metricas_por_limiar(y_true, y_prob, n_limiares=11)
    assert {"limiar", "f1", "precision", "recall", "accuracy"}.issubset(t.columns)
    assert len(t) == 11
    assert (t["limiar"] > 0).all()
    assert (t["limiar"] < 1).all()


def test_ic_bootstrap_retorna_tres_floats(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    est, inf, sup = ic_bootstrap(y_true, y_prob, n_boot=50, seed=42)
    assert isinstance(est, float)
    assert isinstance(inf, float)
    assert isinstance(sup, float)
    assert inf <= sup


def test_ic_bootstrap_deterministico(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    a = ic_bootstrap(y_true, y_prob, n_boot=50, seed=42)
    b = ic_bootstrap(y_true, y_prob, n_boot=50, seed=42)
    assert a == b


def test_ic_bootstrap_metrica_customizada(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> None:
    est, inf, sup = ic_bootstrap(
        y_true,
        y_prob,
        metrica=average_precision,
        n_boot=30,
        seed=1,
    )
    assert inf <= est <= sup
```

## `tests/test_model_pipelines.py`

- Git: `tracked` · status `clean`
- Size: `5.9 KB` · modified `2026-10-15 01:27 UTC`
- SHA-256: `76d3a6c4d6ed6409bbdf2df8dd36fe244ed88b18142620672efed833f1d54e58`

```python
"""
Testes rápidos dos construtores de pipeline de modelos supervisionados.

Cobrem `build_baseline_pipeline`, `build_logistic_pipeline` e
`build_boosting_pipeline`. Não dependem do Parquet nem fazem I/O pesado.

A lista de features vem de `src.models.pipeline`, que por sua vez lê
`configs/supervised.yaml` — sem hard-code.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.models import pipeline as P
from src.models.baseline import build_baseline_pipeline
from src.models.boosting import build_boosting_pipeline
from src.models.logistic import build_logistic_pipeline
from src.utils import config as C


def _df_features(
    n: int = 200,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    DataFrame sintético com exatamente as features exigidas pelo YAML.

    Numéricas recebem distribuição normal; categóricas recebem 3 níveis
    como strings. O alvo é balanceado 50/50 e depois embaralhado — isso
    garante as duas classes para `DummyClassifier(strategy="prior")` e
    para `LogisticRegression(class_weight="balanced")`.
    """
    rng = np.random.default_rng(seed)
    dados: dict[str, np.ndarray] = {}

    for coluna in P.FEATURES_NUMERICAS:
        dados[coluna] = rng.normal(loc=50.0, scale=15.0, size=n)

    for coluna in P.FEATURES_CATEGORICAS:
        dados[coluna] = rng.choice(["0", "1", "2"], size=n)

    X = pd.DataFrame(dados)

    y = pd.Series(
        np.concatenate(
            [
                np.zeros(n // 2, dtype=int),
                np.ones(n - n // 2, dtype=int),
            ]
        ),
        name="alvo",
    ).sample(frac=1, random_state=seed).reset_index(drop=True)

    return X, y


def _colunas_do_pre(pipe: Pipeline) -> set[str]:
    """Colunas declaradas no ColumnTransformer do pipeline."""
    # ColumnTransformer.transformers é uma lista de
    # (nome, transformer, colunas); extraímos a terceira posição.
    colunas: set[str] = set()
    for _, _, cols in pipe.named_steps["pre"].transformers:
        if isinstance(cols, list):
            colunas.update(cols)
    return colunas


# `max_iter` reduzido para manter os testes rápidos — smoke de fit, não tuning.
_CONSTRUTORES: list[tuple[str, Callable[[], Pipeline]]] = [
    ("baseline", lambda: build_baseline_pipeline()),
    ("logistic", lambda: build_logistic_pipeline(max_iter=500)),
    ("boosting", lambda: build_boosting_pipeline(max_iter=30)),
]

_IDS = [nome for nome, _ in _CONSTRUTORES]


def test_build_baseline_pipeline_retorna_pipeline() -> None:
    pipe = build_baseline_pipeline()
    assert isinstance(pipe, Pipeline)
    assert list(pipe.named_steps.keys()) == ["pre", "clf"]
    assert isinstance(pipe.named_steps["clf"], DummyClassifier)


def test_build_logistic_pipeline_retorna_pipeline() -> None:
    pipe = build_logistic_pipeline()
    assert isinstance(pipe, Pipeline)
    assert list(pipe.named_steps.keys()) == ["pre", "clf"]
    assert isinstance(pipe.named_steps["clf"], LogisticRegression)


def test_build_boosting_pipeline_retorna_pipeline() -> None:
    pipe = build_boosting_pipeline()
    assert isinstance(pipe, Pipeline)
    assert list(pipe.named_steps.keys()) == ["pre", "clf"]
    assert isinstance(pipe.named_steps["clf"], HistGradientBoostingClassifier)


@pytest.mark.parametrize(("nome", "ctor"), _CONSTRUTORES, ids=_IDS)
def test_pipelines_fit_predict_proba(
    nome: str,
    ctor: Callable[[], Pipeline],
) -> None:
    X, y = _df_features(n=200)
    pipe = ctor()
    pipe.fit(X, y)

    proba = pipe.predict_proba(X)

    assert proba.shape == (len(X), 2), f"{nome}: shape inesperado {proba.shape}"
    assert np.isfinite(proba).all(), f"{nome}: probabilidades contêm NaN/Inf"
    assert ((proba >= 0) & (proba <= 1)).all(), (
        f"{nome}: probabilidades fora de [0, 1]"
    )
    assert np.allclose(proba.sum(axis=1), 1.0), (
        f"{nome}: linhas de probabilidade não somam 1"
    )


@pytest.mark.parametrize(("nome", "ctor"), _CONSTRUTORES, ids=_IDS)
def test_pipelines_nao_incluem_proibidas(
    nome: str,
    ctor: Callable[[], Pipeline],
) -> None:
    proibidas = set(C.cfg("features", "proibidas") or [])
    assert proibidas, (
        "`features.proibidas` está vazio no supervised.yaml — "
        "ao menos o alvo e as colunas posteriores ao desfecho precisam "
        "estar listadas."
    )

    colisoes = _colunas_do_pre(ctor()) & proibidas
    assert not colisoes, (
        f"{nome}: colunas proibidas presentes no pré-processador: "
        f"{sorted(colisoes)}"
    )


def test_pipelines_usam_features_do_yaml() -> None:
    """
    O pré-processador de cada pipeline precisa expor exatamente o
    conjunto `FEATURES_NUMERICAS + FEATURES_CATEGORICAS` derivado do
    YAML. Serve como canário contra features fora do YAML ou filtros
    silenciosos.
    """
    esperadas = set(P.FEATURES_NUMERICAS) | set(P.FEATURES_CATEGORICAS)
    assert esperadas, "Nenhuma feature declarada em supervised.yaml."

    for nome, ctor in _CONSTRUTORES:
        colunas = _colunas_do_pre(ctor())
        faltando = esperadas - colunas
        extras = colunas - esperadas
        assert colunas == esperadas, (
            f"{nome}: pré-processador divergente do YAML. "
            f"Faltando: {sorted(faltando)}; Extras: {sorted(extras)}"
        )


def test_logistic_pipeline_solver_invalido() -> None:
    """
    `l1_ratio=1.0` (L1 puro) exige `liblinear` ou `saga`; com `lbfgs`,
    o construtor deve levantar `ValueError`.
    """
    with pytest.raises(ValueError, match="combinação inválida"):
        build_logistic_pipeline(l1_ratio=1.0, solver="lbfgs")
```

## `tests/test_pipeline.py`

- Git: `tracked` · status `clean`
- Size: `2.3 KB` · modified `2026-10-15 01:27 UTC`
- SHA-256: `6a36380e4323723c2dd4c82dbdfff7b7ae44ff5eb35bc09f977288b9fa654cda`

```python
"""
Testes do pipeline de ingestão: read_srag, get_parquet e build_pipeline.

Testes que tocam arquivos grandes são marcados com `@pytest.mark.slow`.
Os testes de diretório são rápidos e não recebem esse marcador.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.utils import env


@pytest.mark.slow
def test_read_srag_retorna_dataframe(parquet_disponivel: Path | None) -> None:
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    from src.utils.storage import read_srag

    df = read_srag(columns=["sg_uf", "dt_notific"])

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert {"sg_uf", "dt_notific"}.issubset(set(df.columns))


@pytest.mark.slow
def test_get_parquet_reaproveita_arquivo(parquet_disponivel: Path | None) -> None:
    """`force=False` reutiliza o arquivo existente (mesmo mtime e tamanho)."""
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    from src.utils.storage import get_parquet

    caminho_1 = get_parquet(force=False)
    estado_1 = caminho_1.stat()

    caminho_2 = get_parquet(force=False)
    estado_2 = caminho_2.stat()

    assert caminho_1.resolve() == caminho_2.resolve()
    assert estado_1.st_mtime_ns == estado_2.st_mtime_ns
    assert estado_1.st_size == estado_2.st_size


def test_build_pipeline_falha_feature_ausente() -> None:
    from src.models.pipeline import build_pipeline

    X = pd.DataFrame({"nu_idade_n": [30.0, 40.0, 50.0]})

    with pytest.raises(KeyError, match="ausentes"):
        build_pipeline(X=X)


def test_build_pipeline_strict_false_avisa_mas_continua(
    caplog: pytest.LogCaptureFixture,
) -> None:
    from src.models.pipeline import build_pipeline

    X = pd.DataFrame({"nu_idade_n": [30.0, 40.0, 50.0]})

    with caplog.at_level("WARNING"):
        pipe = build_pipeline(X=X, strict=False)

    assert pipe is not None
    assert "ausentes" in caplog.text.lower()


def test_raw_dir_foi_criado() -> None:
    env.garantir_diretorios()
    assert env.RAW.exists()
    assert env.RAW.is_dir()


def test_processed_dir_foi_criado() -> None:
    env.garantir_diretorios()
    assert env.PROCESSED.exists()
    assert env.PROCESSED.is_dir()
```

## `tests/test_reproducibility.py`

- Git: `tracked` · status `clean`
- Size: `4.0 KB` · modified `2026-10-15 01:27 UTC`
- SHA-256: `c367348592478012dcbca5811d54e17a7ef667ee43f9c2b1eaeedd0dacb63382`

```python
"""Testes do registro de execuções."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.utils import config as C
from src.utils import reproducibility as R


def _ler_meta(pasta: Path) -> dict:
    return json.loads((pasta / "metadata.json").read_text(encoding="utf-8"))


def test_registrar_execucao_cria_pasta(tmp_path: Path) -> None:
    pasta = R.registrar_execucao(
        modelo="teste",
        seed=42,
        parametros={"C": 1.0},
        dataset={"nome": "srag", "n_rows": 100},
        metricas={"auc": 0.5},
        duracao_s=1.23,
        output_dir=tmp_path,
    )
    assert pasta.exists()
    assert (pasta / "metadata.json").exists()
    assert (pasta / "summary.txt").exists()


def test_metadata_tem_campos_obrigatorios(tmp_path: Path) -> None:
    pasta = R.registrar_execucao(
        modelo="teste",
        seed=7,
        parametros={"x": 1},
        metricas={"auc": 0.9},
        output_dir=tmp_path,
    )
    meta = _ler_meta(pasta)

    for chave in (
        "run_id",
        "timestamp",
        "modelo",
        "seed",
        "parametros",
        "dataset",
        "metricas",
        "versoes",
        "git",
        "env",
        "duracao_s",
        "status",
        "data_version",
        "gates",
    ):
        assert chave in meta

    assert meta["seed"] == 7
    assert meta["modelo"] == "teste"
    assert meta["metricas"]["auc"] == 0.9


def test_metadata_grava_data_version(tmp_path: Path) -> None:
    pasta = R.registrar_execucao(modelo="dv", output_dir=tmp_path)
    assert _ler_meta(pasta)["data_version"] == C.DATA_VERSION


def test_metadata_grava_gates(tmp_path: Path) -> None:
    pasta = R.registrar_execucao(modelo="gates", output_dir=tmp_path)
    meta = _ler_meta(pasta)
    assert isinstance(meta["gates"], dict)
    assert "G9_holdout" in meta["gates"]


def test_run_context_manager_sucesso(tmp_path: Path) -> None:
    r: R.Run | None = None
    with R.Run(modelo="ctx", seed=1, output_dir=tmp_path) as r:
        r.metrica(auc=0.77)
        r.anotar("nota de teste")

    assert r is not None
    assert r.pasta is not None
    meta = _ler_meta(r.pasta)
    assert meta["metricas"]["auc"] == 0.77
    assert "nota de teste" in meta["notas"]
    assert meta["duracao_s"] is not None
    assert meta["status"] == "success"
    assert meta["erro"] is None


def test_run_registra_excecao(tmp_path: Path) -> None:
    """Mesmo em exceção, o metadata é gravado — com status e erro."""
    r: R.Run | None = None
    with pytest.raises(RuntimeError, match="boom"):
        with R.Run(modelo="erro", output_dir=tmp_path) as r:
            raise RuntimeError("boom")

    assert r is not None
    assert r.pasta is not None
    meta = _ler_meta(r.pasta)
    assert meta["status"] == "error"
    assert meta["erro"]["tipo"] == "RuntimeError"
    assert "boom" in meta["erro"]["mensagem"]
    assert "Traceback" in meta["erro"]["traceback"]


def test_run_nao_suprime_excecao(tmp_path: Path) -> None:
    """O `__exit__` retorna False — a exceção propaga."""
    with pytest.raises(ValueError):
        with R.Run(modelo="propaga", output_dir=tmp_path):
            raise ValueError("propaga")


def test_run_id_unico(tmp_path: Path) -> None:
    a = R.gerar_run_id(modelo="dup", base_dir=tmp_path)
    (tmp_path / a).mkdir()
    b = R.gerar_run_id(modelo="dup", base_dir=tmp_path)
    assert a != b


def test_listar_e_carregar(tmp_path: Path) -> None:
    R.registrar_execucao(modelo="a", output_dir=tmp_path)
    R.registrar_execucao(modelo="b", output_dir=tmp_path)

    runs = R.listar_runs(output_dir=tmp_path)
    assert len(runs) == 2

    meta = R.carregar_run(runs[0]["run_id"], output_dir=tmp_path)
    assert meta["modelo"] in {"a", "b"}


def test_seed_padrao_vem_do_config(tmp_path: Path) -> None:
    pasta = R.registrar_execucao(modelo="seed_default", output_dir=tmp_path)
    assert _ler_meta(pasta)["seed"] == C.SEED
```

## `tests/test_smoke.py`

- Git: `tracked` · status `clean`
- Size: `2.7 KB` · modified `2026-10-15 01:27 UTC`
- SHA-256: `5cc267b0d1f02be909010b1235e5e1f93753fdbe86b4a3a85f74429424e9c59b`

```python
"""
Smoke tests: o dataset existe, abre, tem colunas e registros?

Todos os testes são marcados como `slow` via `pytestmark`.
Rode com: pytest -m slow
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.utils import config as C


pytestmark = pytest.mark.slow


@pytest.fixture
def parquet(parquet_disponivel: Path | None) -> Path:
    """Versão obrigatória de `parquet_disponivel`, com skip se ausente."""
    if parquet_disponivel is None:
        pytest.skip(
            "Nenhum Parquet encontrado. Rode 00_acesso_dados_parquet.ipynb "
            "ou 01_extracao.ipynb primeiro."
        )
    return parquet_disponivel


def test_parquet_existe(parquet: Path) -> None:
    assert parquet.exists()
    assert parquet.stat().st_size > 0


def test_parquet_tem_magic_bytes(parquet: Path) -> None:
    with open(parquet, "rb") as f:
        magic = f.read(4)
    assert magic == b"PAR1", f"Arquivo não é Parquet válido (magic={magic!r})"


def test_parquet_abre(parquet: Path) -> None:
    import pyarrow.parquet as pq

    schema = pq.read_schema(parquet)
    assert len(schema.names) > 0


def test_parquet_tem_colunas_esperadas(parquet: Path) -> None:
    import pyarrow.parquet as pq

    colunas = set(pq.read_schema(parquet).names)

    # Colunas mínimas esperadas no SRAG; ajustar conforme o dicionário de dados.
    esperadas = {"sg_uf", "dt_notific"}
    faltando = esperadas - colunas

    assert not faltando, f"Colunas ausentes: {faltando}"


def test_parquet_tem_registros(parquet: Path) -> None:
    df = pd.read_parquet(parquet, columns=["sg_uf"])
    assert len(df) > 0


def test_leitura_de_uma_coluna(parquet: Path) -> None:
    df = pd.read_parquet(parquet, columns=["sg_uf"])
    assert df.shape[1] == 1
    assert "sg_uf" in df.columns


def test_produz_saida_pequena(parquet: Path) -> None:
    """Confirma que conseguimos produzir uma saída minúscula — o smoke final."""
    df = pd.read_parquet(parquet, columns=["sg_uf"]).head(10)
    assert len(df) == 10
    assert df["sg_uf"].value_counts().sum() == 10


def test_storage_read_srag(parquet: Path) -> None:
    from src.utils import storage

    df = storage.read_srag(columns=["sg_uf"])
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "sg_uf" in df.columns


def test_storage_read_srag_com_filtro(parquet: Path) -> None:
    from src.utils import storage

    df = storage.read_srag(
        columns=["sg_uf"],
        filters=[("sg_uf", "==", "SP")],
    )
    if len(df) == 0:
        pytest.skip("Nenhum registro de SP no dataset.")
    assert (df["sg_uf"] == "SP").all()
```

## `tests/test_split.py`

- Git: `tracked` · status `clean`
- Size: `8.1 KB` · modified `2026-10-15 01:27 UTC`
- SHA-256: `de8ce98ef31c3f1017ac6bd0204b2df988db9c59b1a4d4b51d058e74f35b9ad5`

```python
"""
Testes para `src.data.split.criar_particoes_agrupadas`.

Invariantes:
    1. nenhum grupo em mais de uma partição;
    2. proporções de linhas próximas de 70/15/15 (com tolerância);
    3. mesma seed → mesma partição.

Cobrem ainda: políticas de estratos pequenos, grupos com alvo
heterogêneo (raise/warn) e validações de parâmetros/colunas.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pytest

from src.data.split import (
    PARTICOES_CANONICAS,
    SplitWarning,
    criar_particoes_agrupadas,
)


def _df_estratificado(
    n_grupos_classe0: int = 30,
    n_grupos_classe1: int = 20,
    linhas_por_grupo: int = 3,
    seed: int = 0,
) -> pd.DataFrame:
    """
    DataFrame com grupos homogêneos (alvo constante por grupo)
    e duas classes bem representadas.
    """
    rng = np.random.default_rng(seed)
    linhas = []
    gid = 0
    for classe, n_grupos in [(0, n_grupos_classe0), (1, n_grupos_classe1)]:
        for _ in range(n_grupos):
            grupo = f"g{gid:04d}"
            gid += 1
            n = int(rng.integers(1, linhas_por_grupo + 1))
            for i in range(n):
                linhas.append(
                    {
                        "nu_notific": grupo,
                        "alvo": classe,
                        "valor": float(rng.normal()),
                        "idx_linha": i,
                    }
                )
    return pd.DataFrame(linhas)


def _df_grande(
    n_grupos_classe0: int = 700,
    n_grupos_classe1: int = 300,
) -> pd.DataFrame:
    """Base grande o bastante para checar proporções com folga."""
    return _df_estratificado(
        n_grupos_classe0=n_grupos_classe0,
        n_grupos_classe1=n_grupos_classe1,
        linhas_por_grupo=2,
        seed=1,
    )


def _split(df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
    """Chama `criar_particoes_agrupadas` com os defaults dos testes."""
    params: dict[str, Any] = {
        "target_column": "alvo",
        "group_column": "nu_notific",
        "partition_column": "particao",
    }
    params.update(kwargs)
    return criar_particoes_agrupadas(df, **params)


def test_grupos_nao_cruzam_particoes() -> None:
    out = _split(_df_estratificado(), seed=42)

    grupos_por_particao = (
        out.groupby("nu_notific", observed=True)["particao"].nunique()
    )
    assert (grupos_por_particao == 1).all(), (
        "Algum grupo aparece em mais de uma partição:\n"
        f"{grupos_por_particao[grupos_por_particao > 1]}"
    )


def test_nenhuma_linha_perdida() -> None:
    df = _df_estratificado()
    out = _split(df, seed=42)

    assert len(out) == len(df)
    assert set(out["particao"].unique()) == set(PARTICOES_CANONICAS)


def test_proporcoes_linhas_proximas_de_70_15_15() -> None:
    out = _split(_df_grande(), seed=42)

    contagem = out["particao"].value_counts(normalize=True)
    # Grupos são atômicos; a proporção real de linhas oscila em torno do alvo.
    tol = 0.05

    assert abs(contagem["treino"] - 0.70) < tol, contagem
    assert abs(contagem["validacao"] - 0.15) < tol, contagem
    assert abs(contagem["teste"] - 0.15) < tol, contagem


def test_proporcoes_grupos_proximas_de_70_15_15() -> None:
    out = _split(_df_grande(), seed=42)

    por_grupo = out.groupby("nu_notific", observed=True)["particao"].first()
    contagem = por_grupo.value_counts(normalize=True)
    tol = 0.05

    assert abs(contagem["treino"] - 0.70) < tol, contagem
    assert abs(contagem["validacao"] - 0.15) < tol, contagem
    assert abs(contagem["teste"] - 0.15) < tol, contagem


def test_estratificacao_preserva_proporcao_aproximada() -> None:
    df = _df_estratificado(n_grupos_classe0=70, n_grupos_classe1=30)
    out = _split(df, seed=42)

    prevalencia_global = df["alvo"].mean()
    for particao in PARTICOES_CANONICAS:
        sub = out[out["particao"] == particao]
        assert abs(sub["alvo"].mean() - prevalencia_global) < 0.10


def test_reprodutibilidade_mesma_seed() -> None:
    df = _df_estratificado()
    a = _split(df, seed=7)
    b = _split(df, seed=7)
    pd.testing.assert_series_equal(a["particao"], b["particao"])


def test_seeds_diferentes_produzem_splits_diferentes() -> None:
    df = _df_estratificado()
    a = _split(df, seed=1)
    b = _split(df, seed=2)
    assert not a["particao"].equals(b["particao"])


def _df_com_estrato_pequeno() -> pd.DataFrame:
    """1 grupo na classe 1 (estrato pequeno) + 20 grupos na classe 0."""
    return _df_estratificado(n_grupos_classe0=20, n_grupos_classe1=1)


def test_estrato_pequeno_raise_e_default() -> None:
    with pytest.raises(ValueError, match="Estrato"):
        _split(_df_com_estrato_pequeno())


def test_estrato_pequeno_warn_teste_manda_para_teste() -> None:
    df = _df_com_estrato_pequeno()
    with pytest.warns(SplitWarning, match="Destinando ao teste"):
        out = _split(df, politica_estratos_pequenos="warn_teste")

    linhas_classe1 = out[out["alvo"] == 1]
    assert (linhas_classe1["particao"] == "teste").all()
    assert len(out) == len(df)


def test_estrato_pequeno_warn_treino_manda_para_treino() -> None:
    with pytest.warns(SplitWarning, match="Destinando ao treino"):
        out = _split(
            _df_com_estrato_pequeno(),
            politica_estratos_pequenos="warn_treino",
        )

    linhas_classe1 = out[out["alvo"] == 1]
    assert (linhas_classe1["particao"] == "treino").all()


def test_estrato_pequeno_drop_remove_linhas() -> None:
    df = _df_com_estrato_pequeno()
    with pytest.warns(SplitWarning, match="Descartando"):
        out = _split(df, politica_estratos_pequenos="drop")

    assert (out["alvo"] == 1).sum() == 0
    assert len(out) < len(df)
    assert set(out["particao"].unique()).issubset(set(PARTICOES_CANONICAS))


def _df_com_grupo_heterogeneo() -> pd.DataFrame:
    df = _df_estratificado(n_grupos_classe0=20, n_grupos_classe1=10)
    idx = df.index[df["nu_notific"] == "g0000"][0]
    df.loc[idx, "alvo"] = 1
    return df


def test_grupo_heterogeneo_raise() -> None:
    with pytest.raises(ValueError, match="mais de um valor distinto"):
        _split(_df_com_grupo_heterogeneo())


def test_grupo_heterogeneo_warn() -> None:
    with pytest.warns(SplitWarning, match="mais de um valor distinto"):
        _split(
            _df_com_grupo_heterogeneo(),
            on_grupo_alvo_heterogeneo="warn",
        )


def test_coluna_alvo_ausente() -> None:
    with pytest.raises(KeyError, match="alvo"):
        criar_particoes_agrupadas(
            _df_estratificado(),
            target_column="nao_existe",
            group_column="nu_notific",
        )


def test_coluna_grupo_ausente() -> None:
    with pytest.raises(KeyError, match="grupo"):
        criar_particoes_agrupadas(
            _df_estratificado(),
            target_column="alvo",
            group_column="nao_existe",
        )


def test_partition_column_ja_existente() -> None:
    df = _df_estratificado()
    df["particao"] = "treino"
    with pytest.raises(ValueError, match="já contém"):
        _split(df)


def test_frac_invalida() -> None:
    df = _df_estratificado()

    with pytest.raises(ValueError, match="frac_treino"):
        _split(df, frac_treino=0.0)

    with pytest.raises(ValueError, match="frac_validacao"):
        _split(df, frac_validacao=1.5)

    with pytest.raises(ValueError, match="< 1"):
        _split(df, frac_treino=0.7, frac_validacao=0.4)


def test_min_grupos_abaixo_de_3() -> None:
    with pytest.raises(ValueError, match="min_grupos_por_estrato"):
        _split(_df_estratificado(), min_grupos_por_estrato=2)


def test_politica_invalida() -> None:
    with pytest.raises(ValueError, match="politica_estratos_pequenos"):
        _split(
            _df_estratificado(),
            politica_estratos_pequenos="qualquer_coisa",  # type: ignore[arg-type]
        )


def test_df_vazio() -> None:
    df = pd.DataFrame({"alvo": [], "nu_notific": []})
    with pytest.raises(ValueError, match="vazio"):
        _split(df)
```

## `tests/test_supervised_artifact.py`

- Git: `tracked` · status `clean`
- Size: `1.9 KB` · modified `2026-10-15 01:27 UTC`
- SHA-256: `dd95bce9cc1e63a8fd9f834a51523e5f66239ae37688c881a057d708a6aa80f3`

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.data.supervised_artifact import (
    load_supervised_artifact,
    persist_supervised_artifact,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "idade_anos": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
            "alvo_obito_srag": [0, 1, 0, 1, 0, 1],
            "particao": [
                "treino",
                "treino",
                "validacao",
                "validacao",
                "teste",
                "teste",
            ],
        }
    )


def _persistir(tmp_path: Path, frame: pd.DataFrame, **kwargs: Any) -> None:
    params: dict[str, Any] = {
        "source": {},
        "feature_columns": ["idade_anos"],
        "target_column": "alvo_obito_srag",
        "partition_column": "particao",
        "cohort_kind": "provisional",
        "seed": 42,
    }
    params.update(kwargs)
    persist_supervised_artifact(frame, root=tmp_path, **params)


def test_roundtrip_preserva_particao(tmp_path: Path) -> None:
    frame = _frame()
    _persistir(tmp_path, frame, source={"kind": "provisional", "sha256": "abc"})

    loaded, manifest = load_supervised_artifact(
        tmp_path, expected_kind="provisional"
    )

    assert loaded["particao"].tolist() == frame["particao"].tolist()
    assert manifest["test_opened"] is False
    assert manifest["seed"] == 42


def test_tipo_de_coorte_incorreto_falha(tmp_path: Path) -> None:
    _persistir(tmp_path, _frame())

    with pytest.raises(RuntimeError, match="SRAG_COHORT_KIND"):
        load_supervised_artifact(tmp_path, expected_kind="final")


def test_particoes_incompletas_falham(tmp_path: Path) -> None:
    frame = _frame().query("particao != 'teste'")

    with pytest.raises(ValueError, match="Particoes esperadas"):
        _persistir(tmp_path, frame)
```

## `tests/test_target.py`

- Git: `tracked` · status `clean`
- Size: `2.7 KB` · modified `2026-10-15 01:27 UTC`
- SHA-256: `c5bfc13ebc0a5452dec02eb1aedad9d1f8ee95274e7d36aef77912207a31c957`

```python
"""Contrato do alvo binário: `evolucao` → {0, 1, NaN}."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.models.pipeline import criar_alvo_binario, filtrar_rotulos_validos


def _df(valores: list) -> pd.DataFrame:
    return pd.DataFrame({"evolucao": valores, "feat": range(len(valores))})


def test_positivo_e_um() -> None:
    y = criar_alvo_binario(_df([2.0, 2.0]))
    assert y.tolist() == [1.0, 1.0]


def test_negativo_e_zero() -> None:
    y = criar_alvo_binario(_df([1.0, 1.0]))
    assert y.tolist() == [0.0, 0.0]


def test_codigos_3_e_9_viram_nan() -> None:
    y = criar_alvo_binario(_df([3.0, 9.0]))
    assert y.isna().all()


def test_nan_de_entrada_permanece_nan() -> None:
    y = criar_alvo_binario(_df([np.nan, 1.0, 2.0]))
    assert pd.isna(y.iloc[0])
    assert y.iloc[1] == 0.0
    assert y.iloc[2] == 1.0


def test_mistura_completa() -> None:
    y = criar_alvo_binario(_df([1.0, 2.0, 3.0, 9.0, np.nan]))
    assert y.iloc[0] == 0.0
    assert y.iloc[1] == 1.0
    assert y.iloc[2:].isna().all()


def test_filtrar_remove_nan() -> None:
    df = _df([1.0, 2.0, 3.0, 9.0, np.nan])
    X = df[["feat"]]
    y = criar_alvo_binario(df)
    X_ok, y_ok = filtrar_rotulos_validos(X, y)

    assert len(y_ok) == 2
    assert y_ok.dtype == np.int8
    assert y_ok.tolist() == [0, 1]
    assert list(X_ok["feat"]) == [0, 1]


def test_filtrar_exige_indice_alinhado() -> None:
    X = pd.DataFrame({"feat": [1, 2]}, index=[0, 1])
    y = pd.Series([0, 1], index=[1, 2])
    with pytest.raises(ValueError, match="mesmo índice"):
        filtrar_rotulos_validos(X, y)


def test_positivos_e_negativos_nao_se_sobrepoem() -> None:
    with pytest.raises(ValueError, match="sobrepor"):
        criar_alvo_binario(_df([1.0, 2.0]), positivos=[1.0, 2.0], negativos=[1.0])


def test_positivos_vazio_levanta() -> None:
    with pytest.raises(ValueError, match="positivos"):
        criar_alvo_binario(_df([1.0, 2.0]), positivos=[], negativos=[1.0])


def test_negativos_vazio_levanta() -> None:
    with pytest.raises(ValueError, match="negativos"):
        criar_alvo_binario(_df([1.0, 2.0]), positivos=[2.0], negativos=[])


def test_default_vem_do_yaml() -> None:
    """Sem argumentos, usa `target.positivos` e `target.negativos` do YAML."""
    from src.utils import config as C

    pos = C.cfg("target", "positivos")
    neg = C.cfg("target", "negativos")
    assert pos, "target.positivos precisa estar definido no YAML"
    assert neg, "target.negativos precisa estar definido no YAML"

    df = _df([float(pos[0]), float(neg[0])])
    y = criar_alvo_binario(df)
    assert y.tolist() == [1.0, 0.0]
```

## `tests/test_temporal.py`

- Git: `tracked` · status `clean`
- Size: `4.5 KB` · modified `2026-10-15 01:27 UTC`
- SHA-256: `43361fd0913d4997cd6e576c48880d882cd9624f8c9ba30d2a5bb5410b0487ed`

```python
"""
Testes anti-vazamento de dados.

Protegem contra:
- inclusão do alvo nas features;
- inclusão de colunas posteriores ao desfecho;
- duplicação de identificadores quando houver chave adequada.

Split temporal e trava do gate ``G9_holdout`` são testados em
``tests/test_temporal.py`` — não duplicar aqui.

Fonte única de verdade: `configs/supervised.yaml`, lido via
`src.utils.config` (`features.proibidas`) — nada hard-coded aqui.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.utils import config as C


@pytest.fixture
def proibidas() -> set[str]:
    """Colunas proibidas declaradas em `features.proibidas` do YAML."""
    return set(C.cfg("features", "proibidas") or [])


@pytest.fixture
def features_finais() -> set[str]:
    """Lista final de features exposta por `src.models.pipeline`."""
    from src.models import pipeline
    return set(pipeline.FEATURES)


def test_proibidas_nao_vazia(proibidas: set[str]) -> None:
    assert proibidas, (
        "features.proibidas está vazia no supervised.yaml — "
        "ao menos o alvo e as colunas posteriores ao desfecho precisam "
        "estar listadas."
    )


def test_alvo_esta_entre_proibidas(proibidas: set[str]) -> None:
    alvo = C.cfg("target", "coluna")
    assert alvo in proibidas, (
        f"target.coluna ({alvo!r}) precisa estar em features.proibidas."
    )


def test_features_finais_sem_proibidas(
    features_finais: set[str],
    proibidas: set[str],
) -> None:
    vazamento = features_finais & proibidas
    assert not vazamento, (
        f"FEATURES contém colunas proibidas: {sorted(vazamento)}"
    )


def test_features_finais_nao_inclui_alvo(features_finais: set[str]) -> None:
    alvo = C.cfg("target", "coluna")
    assert alvo not in features_finais


def test_check_leakage_passa_quando_X_limpo() -> None:
    from src.evaluation.leakage import check_leakage

    X = pd.DataFrame({"feat_a": [1, 2, 3], "feat_b": [4, 5, 6]})
    check_leakage(X)


def test_check_leakage_levanta_para_proibida(proibidas: set[str]) -> None:
    from src.evaluation.leakage import LeakageError, check_leakage

    coluna = sorted(proibidas)[0]
    X = pd.DataFrame({coluna: [1, 2, 3], "feat_ok": [4, 5, 6]})

    with pytest.raises(LeakageError) as exc:
        check_leakage(X)

    assert coluna in str(exc.value), (
        "A mensagem de erro precisa citar a coluna problemática."
    )


def test_check_leakage_levanta_para_alvo() -> None:
    from src.evaluation.leakage import LeakageError, check_leakage

    alvo = C.cfg("target", "coluna")
    X = pd.DataFrame({alvo: [0, 1, 0], "feat_ok": [1, 2, 3]})

    with pytest.raises(LeakageError):
        check_leakage(X)


def test_check_leakage_lista_vazia_ainda_verifica_alvo() -> None:
    """Lista vazia desliga proibidas, mas o alvo continua sendo checado."""
    from src.evaluation.leakage import LeakageError, check_leakage

    alvo = C.cfg("target", "coluna")
    X = pd.DataFrame({alvo: [0, 1, 0], "feat_ok": [1, 2, 3]})

    with pytest.raises(LeakageError):
        check_leakage(X, forbidden_columns=[])


def test_dataset_sem_identificadores_duplicados(
    parquet_disponivel,
) -> None:
    """
    Checa duplicidade apenas se houver coluna que sirva como
    identificador da notificação. UF e data não formam chave única.
    """
    if parquet_disponivel is None:
        pytest.skip("Parquet não disponível.")

    import pyarrow.parquet as pq

    colunas = set(pq.read_schema(parquet_disponivel).names)

    candidatas = [
        "nu_notific",
        "numero_notificacao",
        "id_notificacao",
        "id",
    ]
    coluna_id = next((c for c in candidatas if c in colunas), None)

    if coluna_id is None:
        pytest.skip(
            "O Parquet não possui uma coluna identificadora adequada "
            "para o teste de duplicidade."
        )

    df = pd.read_parquet(parquet_disponivel, columns=[coluna_id])
    ids = df[coluna_id].dropna().astype("string").str.strip()
    ids = ids[ids.ne("")]

    if ids.empty:
        pytest.skip(f"A coluna {coluna_id} não possui identificadores válidos.")

    quantidade_duplicada = int(ids.duplicated().sum())
    taxa_duplicada = quantidade_duplicada / len(ids)

    assert taxa_duplicada < 0.05, (
        f"Alta taxa de identificadores duplicados em {coluna_id}: "
        f"{quantidade_duplicada}/{len(ids)} ({taxa_duplicada:.1%})"
    )
```

## `tools/update_project_reference.py`

- Git: `tracked` · status `M`
- Size: `103.7 KB` · modified `2026-10-15 12:51 UTC`
- SHA-256: `b7e910e208d84ce466c8718e858de196eea7ea6bf306cc87247d1af23f6b7b0d`

```python
#!/usr/bin/env python3
r"""Generate a complete, AI-oriented diagnostic snapshot of the SRAG repository.

Run from anywhere inside the repository, preferably with the project venv
(so installed package versions are the real ones):

    .\.venv\Scripts\python.exe tools\update_project_reference.py
    .\.venv\Scripts\python.exe tools\update_project_reference.py --split-mb 4
    .\.venv\Scripts\python.exe tools\update_project_reference.py --run-tests --pytest-args "-m 'not slow'"

Creates (default):

    docs/PROJECT_COMPLETE_REFERENCE.md     full human/AI-readable snapshot
    docs/PROJECT_COMPLETE_REFERENCE.json   machine-readable summary
    docs/project_reference_parts/          the same Markdown split into parts
                                           (default 1 MB each; --no-split to disable)

What the snapshot contains
--------------------------
1.  Git state: branch, commit, remote, status, recent log, diff stat and the
    full diff of uncommitted changes (capped).
2.  Full path inventory of the working folder, including ignored and local
    folders (data/, outputs/, models/, reports/), with size, modification time
    and Git state. File contents of data are never copied.
3.  Full source of every relevant text file: .py, .ipynb, .md, .yaml, .yml,
    .toml, .json, .csv (capped), .txt, .ini, .cfg, .ps1, .sh, .sql, etc.
4.  Notebooks: every cell source, execution counts and, by default, the TEXT
    outputs (streams, text/plain results, errors and tracebacks). Images and
    HTML are replaced by placeholders. Execution order problems are reported.
5.  Small text artifacts produced by the project (manifests, waterfalls,
    summary tables under outputs/, reports/, data/ manifests), capped by size
    and number of CSV rows. Prediction folders are never included.
6.  Text extracted from .docx and .pptx documents (plans, reports).
7.  Python environment: interpreter, platform and every installed package
    version (scikit-learn, pandas, numpy, ...).
8.  Parsed configuration: full YAML summary, gates table, duplicate YAML keys,
    pyproject.toml validity and dependency lists.
9.  Static API catalog: every module, function, class, method, signature,
    docstring, consumers and tests.
10. Static diagnostics ("attention report"), including:
    - internal imports of modules or names that do not exist;
    - calls to project functions with keyword arguments they do not accept
      or with too many positional arguments;
    - gate names used in code/docs that are absent from the YAML;
    - YAML keys never referenced by code (possible dead configuration);
    - feature contract problems (forbidden features, derived features);
    - third-party imports missing from requirements.txt/pyproject.toml and
      unpinned dependencies;
    - duplicated symbols and notebook-local functions duplicating src/;
    - notebooks executed out of order, never executed, or with saved errors;
    - documents pointing to paths that do not exist;
    - mojibake/encoding problems; TODO/FIXME markers;
    - untracked relevant files.
11. Optional: pytest results (--run-tests). This is the only option that
    imports and executes project code.

Safety
------
Secrets and credentials are redacted. Absolute local paths are replaced by
<REPO> and <HOME>. .env files and binary data (Parquet, models, images) are
never copied. Notebook outputs can be disabled with --no-notebook-outputs.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata as importlib_metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover
    tomllib = None

SCHEMA_VERSION = 4

OUTPUT_DIR = Path("docs")
OUTPUT_MD_NAME = "PROJECT_COMPLETE_REFERENCE.md"
OUTPUT_JSON_NAME = "PROJECT_COMPLETE_REFERENCE.json"
PARTS_DIR_NAME = "project_reference_parts"

DEFAULT_MAX_INLINE_BYTES = 4_000_000
DEFAULT_MAX_OUTPUT_CHARS = 6_000
DEFAULT_MAX_ARTIFACT_BYTES = 300_000
DEFAULT_MAX_CSV_ROWS = 60
DEFAULT_MAX_DIFF_CHARS = 400_000
DEFAULT_GIT_LOG = 40
DEFAULT_SPLIT_MB = 1.0
MAX_INVENTORY_ENTRIES = 30_000
MAX_DOCSTRING_CHARS = 4_000
MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL = 200

# Never walked (tooling, caches, virtual environments).
EXCLUDED_DIRS_ANYWHERE = {
    ".git", ".venv", "venv", "env", ".env", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".tox", ".nox", ".ipynb_checkpoints",
    "node_modules", ".idea", ".vscode", "site-packages", ".eggs",
    "build", "dist",
}
# Walked for the path inventory and small text artifacts, never as source.
ARTIFACT_DIRS_AT_ROOT = {
    "data", "outputs", "models", "logs", "artifacts", "mlruns", "reports",
}
# Never copied, even when small and textual.
ARTIFACT_EXCLUDED_DIR_NAMES = {"predictions", "predicoes", "raw", "cache", "tmp"}
EXCLUDED_FILES = {
    ".env", "pip_inspect-venv.json", OUTPUT_MD_NAME, OUTPUT_JSON_NAME,
}
# Files whose existence and keys are reported, but whose values are redacted.
KEYS_ONLY_FILES = {"paths.local.json"}

TEXT_SUFFIXES = {
    ".py", ".pyi", ".md", ".rst", ".txt", ".yaml", ".yml", ".toml", ".ini",
    ".cfg", ".json", ".json5", ".sql", ".ps1", ".psm1", ".sh", ".bat",
    ".cmd", ".csv", ".tsv", ".html", ".css", ".js", ".r", ".R",
}
ARTIFACT_TEXT_SUFFIXES = {".json", ".yaml", ".yml", ".md", ".txt", ".csv", ".tsv", ".log"}
OFFICE_SUFFIXES = {".docx", ".pptx"}
SPECIAL_NAMES = {
    "README", "LICENSE", "Makefile", "Dockerfile", "requirements.txt",
    "pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini", ".env.example",
    ".gitignore", ".gitattributes", ".pre-commit-config.yaml", "environment.yml",
}
LANG = {
    ".py": "python", ".pyi": "python", ".md": "markdown", ".rst": "rst",
    ".yaml": "yaml", ".yml": "yaml", ".toml": "toml", ".json": "json",
    ".json5": "json5", ".ini": "ini", ".cfg": "ini", ".sql": "sql",
    ".ps1": "powershell", ".psm1": "powershell", ".sh": "bash", ".bat": "bat",
    ".cmd": "bat", ".csv": "csv", ".tsv": "tsv", ".html": "html", ".css": "css",
    ".js": "javascript", ".log": "text", ".r": "r",
}
LIKELY_BINARY_SUFFIXES = {
    ".parquet", ".feather", ".arrow", ".pkl", ".pickle", ".joblib", ".onnx",
    ".pt", ".pth", ".h5", ".hdf5", ".npy", ".npz", ".pdf", ".doc", ".ppt",
    ".xls", ".xlsx", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".zip",
    ".7z", ".gz", ".tar", ".bz2", ".xz", ".dbf", ".db", ".sqlite", ".exe", ".dll",
}
IMPORTANT_UNTRACKED_PREFIXES = (
    "src/", "tests/", "configs/", "docs/", "notebooks/", "tools/", "scripts/",
)

# Import name -> distribution name, for the dependency check.
IMPORT_TO_DIST = {
    "sklearn": "scikit-learn", "yaml": "pyyaml", "dotenv": "python-dotenv",
    "PIL": "pillow", "cv2": "opencv-python", "bs4": "beautifulsoup4",
    "docx": "python-docx", "pptx": "python-pptx", "dateutil": "python-dateutil",
    "IPython": "ipython", "jwt": "pyjwt", "skimage": "scikit-image",
    "google": "google-api-python-client", "snowflake": "snowflake-connector-python",
}
KEY_PACKAGES = (
    "scikit-learn", "pandas", "numpy", "scipy", "pyarrow", "pyyaml", "joblib",
    "matplotlib", "seaborn", "python-dotenv", "requests", "pytest",
    "ipykernel", "jupyter", "nbformat", "statsmodels", "shap",
)

ENV_RE = re.compile(
    r"(?:os\.getenv|os\.environ\.get|os\.environ\[|get_env|get_secret|getenv)"
    r"\(?\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]"
)
SECRET_RE = re.compile(
    r"(?im)^(\s*[A-Za-z_][A-Za-z0-9_.-]*?"
    r"(?:token|secret|password|passwd|pwd|api[_-]?key|private[_-]?key|credential)"
    r"[A-Za-z0-9_.-]*\s*[:=]\s*)([^\n#]+)"
)
PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [^-]+ PRIVATE KEY-----.*?-----END [^-]+ PRIVATE KEY-----",
    re.DOTALL,
)
URL_CREDENTIAL_RE = re.compile(r"(?i)(https?://[^\s/:]+:)([^@\s]+)(@)")
GITHUB_TOKEN_RE = re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")
WINDOWS_USER_RE = re.compile(r"(?i)\b[A-Z]:[\\/]+Users[\\/]+[^\\/\s\"'<>|]+")
POSIX_HOME_RE = re.compile(r"(?<![A-Za-z0-9_])/(?:home|Users)/[^/\s\"'<>|]+")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
BACKTICK_RUN_RE = re.compile(r"`+")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
FILE_LITERAL_RE = re.compile(
    r"['\"]([^'\"\n]+\.(?:parquet|csv|json|yaml|yml|joblib|pkl|png|jpg|md|html|txt))['\"]",
    re.IGNORECASE,
)
GATE_RE = re.compile(r"\bG\d+_[A-Za-z0-9_]+\b")
TODO_RE = re.compile(r"(?i)\b(TODO|FIXME|XXX|HACK|PENDENTE)\b[:\s-]*(.{0,140})")
MOJIBAKE_RE = re.compile(r"(?:├|┤|Ã[\u0080-\u00BF¡-¿]|Â[\u00A0-\u00BF ]|â€|\uFFFD)")

CONTEXT = """# Project Complete Reference

> **Generated file. Do not edit manually.**
> Generated by `tools/update_project_reference.py` (schema v{schema}).
> Static snapshot of the repository and of the local working folder.

## 1. Purpose

This reference lets a person or an AI diagnose the SRAG project without prior
conversation context and without access to the machine. It contains the full
source of code, notebooks (with text outputs), configuration and documentation,
plus the Git state, the local path inventory, installed package versions,
parsed configuration and static consistency checks.

## 2. Methodological guardrails

- Academic retrospective prediction project, not a clinically validated tool.
- Prediction time is hospital admission; later information cannot be a feature.
- Do not make causal claims from predictive associations.
- Never use the final test partition for model, hyperparameter, calibration or
  threshold selection.
- Partition, target, features, seed, calibration, threshold and gates come from
  `configs/supervised.yaml` and executable tests.
- Original data, Parquets, trained models, secrets and local paths are never
  copied into this reference (only their paths, sizes and dates).

## 3. How to use this reference (any AI)

1. Read Sections 6 (executive map) and 7 (attention report).
2. Check Section 8 (configuration and gates) and Section 9 (environment).
3. Search Section 12 (API catalog) before proposing any new function.
4. Check Sections 13 to 15 for imports, tests and notebook orchestration.
5. Read the exact implementation in Section 17 (full source).
6. Use Section 18 (artifacts) and notebook outputs as evidence of what was
   actually executed; use Section 10 (inventory) to know what exists locally.
7. If code, configuration, tests, notebooks and plans disagree, report the
   conflict explicitly; never choose silently.

## 4. Evidence precedence

1. Current executable code and tests.
2. Active configuration and explicit decision records.
3. Notebook sources and saved outputs (outputs may be stale: check execution
   counts and artifact dates).
4. Generated artifacts (manifests, tables).
5. Older plans and roadmaps (historical intent only).

## 5. Status vocabulary

- **Implemented:** executable code exists in the current snapshot.
- **Configured:** an active value, rule or gate exists in configuration.
- **Tested / Consumed:** a static reference was found in tests / other code.
- **Working tree:** relevant but not tracked in the current commit.
- **Local only:** exists in the folder but is ignored by Git.
- **Attention:** mismatch, duplication risk, stale reference or broken contract.
"""


@dataclass
class GitEntry:
    path: str
    tracked: bool
    status: str = ""
    exists: bool = True


@dataclass
class CallSite:
    name: str
    location: str
    keywords: list[str]
    n_positional: int
    has_star_args: bool
    has_star_kwargs: bool


@dataclass
class Symbol:
    module: str
    path: str
    qualname: str
    name: str
    kind: str
    signature: str
    lineno: int
    end_lineno: int | None
    docstring: str
    decorators: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    env_vars: list[str] = field(default_factory=list)
    file_literals: list[str] = field(default_factory=list)
    is_private: bool = False
    params: list[str] = field(default_factory=list)
    n_positional_params: int = 0
    has_varargs: bool = False
    has_varkw: bool = False
    defaults: dict[str, str] = field(default_factory=dict)


@dataclass
class PythonFileAnalysis:
    path: str
    module: str
    docstring: str
    parse_error: str | None
    imports: list[str]
    internal_imports: list[str]
    external_imports: list[str]
    import_from: list[dict[str, Any]]
    calls: list[str]
    call_sites: list[CallSite]
    symbols: list[Symbol]
    top_level_names: list[str]
    constants: dict[str, str]
    env_vars: list[str]
    file_literals: list[str]
    has_star_import: bool = False
    lines: int = 0


@dataclass
class NotebookAnalysis:
    path: str
    cells: int
    code_cells: int
    markdown_cells: int
    kernel: dict[str, Any]
    language_version: str
    headings: list[str]
    imports: list[str]
    internal_imports: list[str]
    import_from: list[dict[str, Any]]
    functions: list[Symbol]
    classes: list[Symbol]
    assignments: list[str]
    file_literals: list[str]
    env_vars: list[str]
    parse_errors: list[str]
    call_sites: list[CallSite]
    code_lines: int
    executed_cells: int
    execution_counts: list[int | None]
    out_of_order: bool
    error_outputs: list[str]
    outputs_included: bool


@dataclass
class Attention:
    severity: str
    category: str
    message: str
    evidence: list[str] = field(default_factory=list)
    recommendation: str = ""


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def run_command(
    args: list[str],
    *,
    cwd: Path,
    check: bool = True,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if check and result.returncode:
        raise RuntimeError(
            result.stderr.strip() or result.stdout.strip()
            or f"Command failed: {' '.join(args)}"
        )
    return result


def git(root: Path, *args: str, check: bool = True) -> str:
    return run_command(["git", "-c", "core.quotepath=false", *args], cwd=root, check=check).stdout


def root_dir() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode:
        raise RuntimeError("Run inside the Git repository.")
    return Path(result.stdout.strip()).resolve()


def module_name(path: Path) -> str:
    parts = list(path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def human_bytes(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"


class Redactor:
    """Removes secrets and replaces absolute local paths."""

    def __init__(self, root: Path) -> None:
        variants = {str(root), root.as_posix(), str(root).replace("\\", "\\\\")}
        self.root_variants = sorted((v for v in variants if v), key=len, reverse=True)
        home = Path.home()
        self.home_variants = sorted(
            {str(home), home.as_posix(), str(home).replace("\\", "\\\\")}, key=len, reverse=True
        )

    def __call__(self, text: str) -> tuple[str, list[str]]:
        warnings: list[str] = []
        if PRIVATE_KEY_RE.search(text):
            text = PRIVATE_KEY_RE.sub("[REDACTED_PRIVATE_KEY]", text)
            warnings.append("private key redacted")
        if GITHUB_TOKEN_RE.search(text):
            text = GITHUB_TOKEN_RE.sub("[REDACTED_TOKEN]", text)
            warnings.append("token redacted")
        if SECRET_RE.search(text):
            text = SECRET_RE.sub(r"\1[REDACTED]", text)
            warnings.append("possible secret assignment redacted")
        if URL_CREDENTIAL_RE.search(text):
            text = URL_CREDENTIAL_RE.sub(r"\1[REDACTED]\3", text)
            warnings.append("credentials in URL redacted")
        for value in self.root_variants:
            text = text.replace(value, "<REPO>")
        for value in self.home_variants:
            text = text.replace(value, "<HOME>")
        text = WINDOWS_USER_RE.sub("<HOME>", text)
        text = POSIX_HOME_RE.sub("<HOME>", text)
        return text, warnings


def fence_for(text: str) -> str:
    longest = max((len(m.group(0)) for m in BACKTICK_RUN_RE.finditer(text)), default=0)
    return "`" * max(3, longest + 1)


def code_block(text: str, lexer: str = "text") -> str:
    fence = fence_for(text)
    return f"{fence}{lexer}\n{text}\n{fence}"


def truncate(text: str, limit: int, label: str = "characters") -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    head = text[: int(limit * 0.7)]
    tail = text[-int(limit * 0.3):]
    return f"{head}\n... [{len(text) - len(head) - len(tail)} {label} omitted] ...\n{tail}"


def safe_unparse(node: ast.AST | None, default: str = "") -> str:
    if node is None:
        return default
    try:
        return ast.unparse(node)
    except Exception:
        return default or "..."


def literal_preview(node: ast.AST, max_chars: int = 300) -> str:
    try:
        text = repr(ast.literal_eval(node))
    except Exception:
        text = safe_unparse(node, "<dynamic>")
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return dotted_name(node.func)
    return None


def env_names(text: str) -> list[str]:
    return sorted(set(ENV_RE.findall(text)))


def file_literals(text: str) -> list[str]:
    return sorted({m.group(1) for m in FILE_LITERAL_RE.finditer(text)})


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    if path.exists() and path.read_bytes() == data:
        return
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=path.parent) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    temporary.replace(path)


# ---------------------------------------------------------------------------
# Git and filesystem inventory
# ---------------------------------------------------------------------------

def parse_porcelain_status(root: Path) -> dict[str, str]:
    raw = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    items = raw.split("\0")
    status: dict[str, str] = {}
    i = 0
    while i < len(items):
        item = items[i]
        if not item:
            i += 1
            continue
        code, path_text = item[:2], item[3:]
        if code[0] in {"R", "C"} and i + 1 < len(items):
            status[path_text] = code
            i += 2
        else:
            status[path_text] = code
            i += 1
    return status


def collect_git_entries(root: Path) -> tuple[list[GitEntry], set[str], set[str]]:
    status_map = parse_porcelain_status(root)
    tracked = {line.strip() for line in git(root, "ls-files").splitlines() if line.strip()}
    untracked = {
        line.strip()
        for line in git(root, "ls-files", "--others", "--exclude-standard").splitlines()
        if line.strip()
    }
    entries = [
        GitEntry(
            path=Path(value).as_posix(),
            tracked=value in tracked,
            status=status_map.get(value, ""),
            exists=(root / value).is_file(),
        )
        for value in sorted(tracked | untracked, key=str.lower)
    ]
    return entries, tracked, untracked


def walk_inventory(
    root: Path,
    tracked: set[str],
    untracked: set[str],
) -> tuple[list[dict[str, Any]], bool]:
    """All files in the working folder, except tooling/caches/venvs."""
    rows: list[dict[str, Any]] = []
    truncated = False
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS_ANYWHERE)
        for name in sorted(files):
            absolute = Path(current) / name
            rel = absolute.relative_to(root).as_posix()
            try:
                stat = absolute.stat()
            except OSError:
                continue
            if rel in tracked:
                state = "tracked"
            elif rel in untracked:
                state = "untracked"
            else:
                state = "ignored"
            rows.append(
                {
                    "path": rel,
                    "git": state,
                    "bytes": stat.st_size,
                    "modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc)
                    .strftime("%Y-%m-%d %H:%M"),
                }
            )
            if len(rows) >= MAX_INVENTORY_ENTRIES:
                return rows, True
    return rows, truncated


def is_artifact_path(path: Path) -> bool:
    return bool(path.parts) and path.parts[0] in ARTIFACT_DIRS_AT_ROOT


def include_source(path: Path, *, tracked: bool) -> bool:
    parts = path.parts
    if any(part in EXCLUDED_DIRS_ANYWHERE for part in parts):
        return False
    if is_artifact_path(path):
        return False
    if path.name in EXCLUDED_FILES or path.parent.name == PARTS_DIR_NAME:
        return False
    if path.name.startswith(".env") and path.name != ".env.example":
        return False
    if not tracked and not path.as_posix().startswith(IMPORTANT_UNTRACKED_PREFIXES):
        if len(parts) != 1:  # untracked root files (pyproject, README) are allowed
            return False
    suffix = path.suffix.lower()
    return (
        suffix in TEXT_SUFFIXES
        or suffix == ".ipynb"
        or suffix in OFFICE_SUFFIXES
        or path.name in SPECIAL_NAMES
        or path.name in KEYS_ONLY_FILES
    )


def include_artifact(path: Path, size: int, max_bytes: int) -> bool:
    if not is_artifact_path(path):
        return False
    if any(part.lower() in ARTIFACT_EXCLUDED_DIR_NAMES for part in path.parts):
        return False
    if path.name.startswith(".env"):
        return False
    if path.suffix.lower() not in ARTIFACT_TEXT_SUFFIXES:
        return False
    # Raw/large CSVs are only previewed (head), so allow them up to 50x.
    limit = max_bytes * 50 if path.suffix.lower() in {".csv", ".tsv"} else max_bytes
    return size <= limit


# ---------------------------------------------------------------------------
# Python AST analysis
# ---------------------------------------------------------------------------

def imported_names(tree: ast.AST) -> tuple[list[str], list[dict[str, Any]], bool]:
    imports: set[str] = set()
    froms: list[dict[str, Any]] = []
    star = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level + (node.module or "")
            names = [alias.name for alias in node.names]
            if "*" in names:
                star = True
            froms.append(
                {"module": prefix, "names": names, "lineno": getattr(node, "lineno", 0)}
            )
            for name in names:
                imports.add(f"{prefix}.{name}".strip("."))
    return sorted(imports), froms, star


def call_names(tree: ast.AST) -> list[str]:
    return sorted(
        {
            name
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            for name in [dotted_name(node.func)]
            if name
        }
    )


def call_sites(tree: ast.AST, label: str) -> list[CallSite]:
    sites: list[CallSite] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = dotted_name(node.func)
        if not name:
            continue
        sites.append(
            CallSite(
                name=name,
                location=f"{label}:{getattr(node, 'lineno', 0)}",
                keywords=[kw.arg for kw in node.keywords if kw.arg],
                n_positional=sum(not isinstance(a, ast.Starred) for a in node.args),
                has_star_args=any(isinstance(a, ast.Starred) for a in node.args),
                has_star_kwargs=any(kw.arg is None for kw in node.keywords),
            )
        )
    return sites


def top_level_names(tree: ast.Module) -> list[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for sub in ast.walk(target):
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, (ast.If, ast.Try)):
            # Conditional definitions (try/except ImportError, if TYPE_CHECKING)
            for sub in ast.walk(node):
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.add(sub.name)
                elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                    names.add(sub.id)
                elif isinstance(sub, ast.alias):
                    names.add((sub.asname or sub.name).split(".")[0])
    return sorted(names)


def assigned_constants(tree: ast.Module) -> dict[str, str]:
    constants: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id.isupper():
                constants[target.id] = literal_preview(node.value)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id.isupper() and node.value:
                constants[node.target.id] = literal_preview(node.value)
    return constants


def function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    returns = f" -> {safe_unparse(node.returns)}" if node.returns else ""
    return f"{prefix} {node.name}({safe_unparse(node.args, '...')}){returns}"


def extract_symbol(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
    *,
    path: Path,
    module: str,
    text: str,
    parent: str = "",
) -> Symbol:
    qualname = f"{parent}.{node.name}" if parent else node.name
    params: list[str] = []
    n_pos = 0
    has_varargs = has_varkw = False
    defaults: dict[str, str] = {}
    if isinstance(node, ast.ClassDef):
        signature, kind = f"class {node.name}({', '.join(safe_unparse(b) for b in node.bases)})", "class"
        # A class call uses __init__ (or dataclass fields): handled loosely.
        init = next(
            (
                child for child in node.body
                if isinstance(child, ast.FunctionDef) and child.name == "__init__"
            ),
            None,
        )
        if init is not None:
            args = init.args
            positional = [a.arg for a in args.posonlyargs + args.args][1:]
            params = positional + [a.arg for a in args.kwonlyargs]
            n_pos = len(positional)
            has_varargs = args.vararg is not None
            has_varkw = args.kwarg is not None
        else:
            has_varargs = has_varkw = True  # unknown (dataclass, inheritance)
    else:
        signature = function_signature(node)
        kind = "method" if parent else "function"
        args = node.args
        positional = [a.arg for a in args.posonlyargs + args.args]
        if parent and positional and positional[0] in {"self", "cls"}:
            positional = positional[1:]
        params = positional + [a.arg for a in args.kwonlyargs]
        n_pos = len(positional)
        has_varargs = args.vararg is not None
        has_varkw = args.kwarg is not None
        pos_defaults = args.defaults
        for arg, default in zip((args.posonlyargs + args.args)[-len(pos_defaults):] if pos_defaults else [], pos_defaults):
            defaults[arg.arg] = literal_preview(default, 120)
        for arg, default in zip(args.kwonlyargs, args.kw_defaults):
            if default is not None:
                defaults[arg.arg] = literal_preview(default, 120)
    doc = (ast.get_docstring(node) or "").strip()
    if len(doc) > MAX_DOCSTRING_CHARS:
        doc = doc[: MAX_DOCSTRING_CHARS - 3] + "..."
    segment = ast.get_source_segment(text, node) or ""
    return Symbol(
        module=module,
        path=path.as_posix(),
        qualname=qualname,
        name=node.name,
        kind=kind,
        signature=signature,
        lineno=node.lineno,
        end_lineno=getattr(node, "end_lineno", None),
        docstring=doc,
        decorators=[safe_unparse(d) for d in node.decorator_list],
        calls=call_names(node),
        env_vars=env_names(segment),
        file_literals=file_literals(segment),
        is_private=node.name.startswith("_"),
        params=params,
        n_positional_params=n_pos,
        has_varargs=has_varargs,
        has_varkw=has_varkw,
        defaults=defaults,
    )


def analyze_python(path: Path, text: str, internal_roots: set[str]) -> PythonFileAnalysis:
    module = module_name(path)
    lines = len(text.splitlines())
    try:
        tree = ast.parse(text, filename=path.as_posix())
    except SyntaxError as exc:
        return PythonFileAnalysis(
            path=path.as_posix(), module=module, docstring="", parse_error=str(exc),
            imports=[], internal_imports=[], external_imports=[], import_from=[],
            calls=[], call_sites=[], symbols=[], top_level_names=[], constants={},
            env_vars=env_names(text), file_literals=file_literals(text), lines=lines,
        )
    imports, froms, star = imported_names(tree)
    internal = sorted(v for v in imports if v.split(".")[0] in internal_roots or v.startswith("."))
    external = sorted(set(imports) - set(internal))
    symbols: list[Symbol] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(extract_symbol(node, path=path, module=module, text=text))
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        symbols.append(
                            extract_symbol(child, path=path, module=module, text=text, parent=node.name)
                        )
    return PythonFileAnalysis(
        path=path.as_posix(),
        module=module,
        docstring=(ast.get_docstring(tree) or "").strip(),
        parse_error=None,
        imports=imports,
        internal_imports=internal,
        external_imports=external,
        import_from=froms,
        calls=call_names(tree),
        call_sites=call_sites(tree, path.as_posix()),
        symbols=symbols,
        top_level_names=top_level_names(tree),
        constants=assigned_constants(tree),
        env_vars=env_names(text),
        file_literals=file_literals(text),
        has_star_import=star,
        lines=lines,
    )


# ---------------------------------------------------------------------------
# Notebooks
# ---------------------------------------------------------------------------

def strip_magics(source: str) -> str:
    """Comment out IPython magics/shell lines so the cell can be parsed."""
    lines = []
    for line in source.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("%", "!", "?")) or stripped.endswith("?"):
            lines.append("# " + line)
        else:
            lines.append(line)
    return "\n".join(lines)


def render_output(output: dict[str, Any], max_chars: int, redactor: Redactor) -> tuple[str, str]:
    """Return (kind, text) for one notebook output."""
    kind = output.get("output_type", "unknown")
    if kind == "stream":
        text = "".join(output.get("text", []))
        label = f"stream:{output.get('name', 'stdout')}"
    elif kind in {"execute_result", "display_data"}:
        data = output.get("data", {})
        omitted = [mime for mime in data if mime != "text/plain"]
        text = "".join(data.get("text/plain", []))
        if omitted:
            text += ("\n" if text else "") + f"[non-text output omitted: {', '.join(sorted(omitted))}]"
        label = kind
    elif kind == "error":
        trace = "\n".join(output.get("traceback", []))
        text = f"{output.get('ename', '')}: {output.get('evalue', '')}\n{trace}"
        label = "error"
    else:
        text, label = json.dumps(output)[:500], kind
    text = ANSI_RE.sub("", text)
    text, _ = redactor(text)
    return label, truncate(text.rstrip(), max_chars)


def analyze_notebook(
    path: Path,
    data: bytes,
    internal_roots: set[str],
) -> tuple[NotebookAnalysis, dict[str, Any]]:
    nb = json.loads(data.decode("utf-8-sig"))
    headings: list[str] = []
    imports: set[str] = set()
    internal_imports: set[str] = set()
    froms: list[dict[str, Any]] = []
    functions: list[Symbol] = []
    classes: list[Symbol] = []
    assignments: set[str] = set()
    literals: set[str] = set()
    envs: set[str] = set()
    parse_errors: list[str] = []
    sites: list[CallSite] = []
    errors: list[str] = []
    counts: list[int | None] = []
    code_lines = code_cells = markdown_cells = executed = 0
    for number, cell in enumerate(nb.get("cells", []), 1):
        kind = cell.get("cell_type", "unknown")
        source = "".join(cell.get("source", []))
        if kind == "markdown":
            markdown_cells += 1
            headings.extend(title.strip() for _, title in HEADING_RE.findall(source))
            continue
        if kind != "code":
            continue
        code_cells += 1
        code_lines += len(source.splitlines())
        count = cell.get("execution_count")
        counts.append(count)
        if count is not None:
            executed += 1
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                errors.append(f"cell {number}: {output.get('ename', '')}: {str(output.get('evalue', ''))[:200]}")
        label = f"{path.as_posix()}#cell-{number}"
        try:
            tree = ast.parse(strip_magics(source), filename=label)
        except SyntaxError as exc:
            parse_errors.append(f"Cell {number}: {exc}")
            continue
        cell_imports, cell_froms, _ = imported_names(tree)
        imports.update(cell_imports)
        internal_imports.update(v for v in cell_imports if v.split(".")[0] in internal_roots)
        for item in cell_froms:
            froms.append({**item, "cell": number})
        sites.extend(call_sites(tree, label))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(extract_symbol(node, path=Path(label), module=f"notebook:{path.as_posix()}", text=source))
            elif isinstance(node, ast.ClassDef):
                classes.append(extract_symbol(node, path=Path(label), module=f"notebook:{path.as_posix()}", text=source))
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and (
                        target.id.isupper() or target.id.lower().endswith(("_dir", "_path", "_file"))
                    ):
                        assignments.add(target.id)
        literals.update(file_literals(source))
        envs.update(env_names(source))
    numeric = [c for c in counts if c is not None]
    out_of_order = any(b < a for a, b in zip(numeric, numeric[1:]))
    meta = nb.get("metadata", {})
    analysis = NotebookAnalysis(
        path=path.as_posix(),
        cells=len(nb.get("cells", [])),
        code_cells=code_cells,
        markdown_cells=markdown_cells,
        kernel=meta.get("kernelspec", {}),
        language_version=str(meta.get("language_info", {}).get("version", "")),
        headings=headings,
        imports=sorted(imports),
        internal_imports=sorted(internal_imports),
        import_from=froms,
        functions=functions,
        classes=classes,
        assignments=sorted(assignments),
        file_literals=sorted(literals),
        env_vars=sorted(envs),
        parse_errors=parse_errors,
        call_sites=sites,
        code_lines=code_lines,
        executed_cells=executed,
        execution_counts=counts,
        out_of_order=out_of_order,
        error_outputs=errors,
        outputs_included=False,
    )
    return analysis, nb


def notebook_source_markdown(
    nb: dict[str, Any],
    analysis: NotebookAnalysis,
    *,
    include_outputs: bool,
    max_output_chars: int,
    reduced: bool,
    redactor: Redactor,
) -> str:
    parts: list[str] = [
        f"- Cells: `{analysis.cells}` (`{analysis.code_cells}` code, `{analysis.markdown_cells}` markdown)",
        f"- Code cells executed: `{analysis.executed_cells}` of `{analysis.code_cells}`"
        + (" — **executed out of order**" if analysis.out_of_order else ""),
        f"- Kernel: `{analysis.kernel.get('display_name', '')}`; Python `{analysis.language_version}`",
        f"- Outputs: `{'text outputs included' if include_outputs else 'omitted'}`"
        + ("; **reduced view** (notebook above size limit)" if reduced else ""),
        "",
    ]
    for number, cell in enumerate(nb.get("cells", []), 1):
        kind = cell.get("cell_type", "unknown")
        source, _ = redactor("".join(cell.get("source", [])).rstrip())
        if kind == "code":
            count = cell.get("execution_count")
            if reduced:
                lines = source.splitlines()
                if len(lines) > MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL:
                    source = "\n".join(lines[:MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL]) + (
                        f"\n# ... {len(lines) - MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL} lines omitted ..."
                    )
            parts.append(f"### Cell {number} [code] · In [{count if count is not None else ' '}]")
            parts.append("")
            parts.append(code_block(source, "python"))
            if include_outputs:
                for out_index, output in enumerate(cell.get("outputs", []), 1):
                    label, text = render_output(output, max_output_chars, redactor)
                    if not text:
                        continue
                    parts.append("")
                    parts.append(f"**Output {out_index} ({label})**")
                    parts.append("")
                    parts.append(code_block(text, "text"))
        else:
            parts.append(f"### Cell {number} [{kind}]")
            parts.append("")
            parts.append(code_block(source, "markdown"))
        parts.append("")
    return "\n".join(parts).rstrip()


# ---------------------------------------------------------------------------
# Office documents and artifacts
# ---------------------------------------------------------------------------

def office_text(data: bytes, suffix: str) -> str:
    """Plain text of .docx/.pptx using only the standard library."""
    import io
    from xml.etree import ElementTree as ET

    texts: list[str] = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if suffix == ".docx":
            names = ["word/document.xml"]
        else:
            names = sorted(
                (n for n in archive.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                key=lambda n: int(re.findall(r"\d+", n)[-1]),
            )
        for index, name in enumerate(names, 1):
            if name not in archive.namelist():
                continue
            root = ET.fromstring(archive.read(name))
            if suffix == ".pptx":
                texts.append(f"--- slide {index} ---")
            for paragraph in root.iter():
                tag = paragraph.tag.rsplit("}", 1)[-1]
                if tag == "p":
                    line = "".join(
                        (node.text or "")
                        for node in paragraph.iter()
                        if node.tag.rsplit("}", 1)[-1] in {"t", "tab"}
                    ).strip()
                    if line:
                        texts.append(line)
                elif tag == "tr" and suffix == ".docx":
                    pass
    return "\n".join(texts)


def csv_preview(text: str, max_rows: int) -> tuple[str, int]:
    lines = text.splitlines()
    total = max(0, len(lines) - 1)
    if len(lines) <= max_rows + 1:
        return text, total
    return "\n".join(lines[: max_rows + 1]) + f"\n... [{total - max_rows} more rows omitted]", total


def keys_only_json(text: str) -> str:
    try:
        data = json.loads(text)
    except Exception:
        return "[could not parse; values hidden]"

    def mask(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: mask(v) for k, v in value.items()}
        if isinstance(value, list):
            return [mask(v) for v in value[:5]]
        return f"<{type(value).__name__}>"

    return json.dumps(mask(data), ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Configuration, environment and dependency files
# ---------------------------------------------------------------------------

def flatten_mapping(value: Any, prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(value, dict) and value:
        for key, child in value.items():
            new_prefix = f"{prefix}.{key}" if prefix else str(key)
            result.update(flatten_mapping(child, new_prefix))
    else:
        result[prefix] = value
    return result


def nested_get(mapping: Any, *keys: str, default: Any = None) -> Any:
    current = mapping
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def load_yaml_strict(text: str) -> tuple[Any | None, str | None, list[str]]:
    """Parse YAML; also report duplicated keys (safe_load silently keeps the last)."""
    if yaml is None:
        return None, "PyYAML not available", []
    duplicates: list[str] = []

    class DupLoader(yaml.SafeLoader):  # type: ignore[misc]
        pass

    def construct_mapping(loader: Any, node: Any, deep: bool = False) -> Any:
        seen: set[Any] = set()
        for key_node, _ in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in seen:
                duplicates.append(f"{key!r} (line {key_node.start_mark.line + 1})")
            seen.add(key)
        return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)

    DupLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    try:
        return yaml.load(text, Loader=DupLoader), None, duplicates  # noqa: S506
    except Exception as exc:
        return None, repr(exc), duplicates


def parse_requirements(text: str) -> dict[str, str]:
    deps: dict[str, str] = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith(("-", "git+", "http")):
            continue
        match = re.match(r"([A-Za-z0-9_.\-\[\]]+)\s*(.*)", line)
        if match:
            name = re.sub(r"\[.*\]", "", match.group(1)).lower().replace("_", "-")
            deps[name] = match.group(2).strip()
    return deps


def parse_pyproject(text: str) -> tuple[dict[str, Any] | None, str | None]:
    if tomllib is None:
        return None, "tomllib unavailable (Python < 3.11)"
    try:
        return tomllib.loads(text), None
    except Exception as exc:
        return None, repr(exc)


def pyproject_dependencies(data: dict[str, Any]) -> dict[str, str]:
    deps: dict[str, str] = {}
    values = list(nested_get(data, "project", "dependencies", default=[]) or [])
    for group in (nested_get(data, "project", "optional-dependencies", default={}) or {}).values():
        values.extend(group or [])
    for item in values:
        match = re.match(r"([A-Za-z0-9_.\-\[\]]+)\s*(.*)", str(item))
        if match:
            name = re.sub(r"\[.*\]", "", match.group(1)).lower().replace("_", "-")
            deps[name] = match.group(2).strip()
    return deps


def installed_packages() -> dict[str, str]:
    packages: dict[str, str] = {}
    for dist in importlib_metadata.distributions():
        try:
            name = (dist.metadata["Name"] or "").lower().replace("_", "-")
        except Exception:
            continue
        if name:
            packages[name] = dist.version
    return dict(sorted(packages.items()))


def top_level_import_map() -> dict[str, str]:
    """Import name -> distribution, from installed metadata when available."""
    mapping = {k: v for k, v in IMPORT_TO_DIST.items()}
    try:
        for top, dists in importlib_metadata.packages_distributions().items():
            if dists:
                mapping.setdefault(top, dists[0].lower().replace("_", "-"))
    except Exception:
        pass
    return mapping


def run_tests(root: Path, extra: str, timeout: int) -> dict[str, Any]:
    args = [sys.executable, "-m", "pytest", "-q", "-rfEs", "--no-header", "-p", "no:cacheprovider"]
    if extra:
        import shlex
        args += shlex.split(extra, posix=(os.name != "nt"))
    try:
        result = run_command(args, cwd=root, check=False, timeout=timeout)
        output = (result.stdout + "\n" + result.stderr).strip()
        return {"command": " ".join(args[1:]), "returncode": result.returncode, "output": output}
    except subprocess.TimeoutExpired:
        return {"command": " ".join(args[1:]), "returncode": None, "output": f"Timeout after {timeout}s"}
    except Exception as exc:
        return {"command": " ".join(args[1:]), "returncode": None, "output": repr(exc)}


# ---------------------------------------------------------------------------
# Static diagnostics
# ---------------------------------------------------------------------------

def index_consumers(
    symbols: list[Symbol],
    python_files: list[PythonFileAnalysis],
    notebooks: list[NotebookAnalysis],
) -> dict[str, list[str]]:
    consumers: dict[str, set[str]] = defaultdict(set)
    by_name: defaultdict[str, list[Symbol]] = defaultdict(list)
    for symbol in symbols:
        by_name[symbol.name].append(symbol)
    sources: list[tuple[str, set[str]]] = [
        (a.path, set(a.calls) | set(a.imports)) for a in python_files
    ] + [
        (n.path, set(n.imports) | {s.name for s in n.call_sites}) for n in notebooks
    ]
    for path, haystack in sources:
        tails = {item.rsplit(".", 1)[-1] for item in haystack}
        for name in tails & set(by_name):
            for match in by_name[name]:
                if path != match.path:
                    consumers[f"{match.module}.{match.qualname}"].add(path)
    return {key: sorted(values) for key, values in sorted(consumers.items())}


def index_tests(symbols: list[Symbol], python_files: list[PythonFileAnalysis]) -> dict[str, list[str]]:
    tests: dict[str, set[str]] = defaultdict(set)
    test_files = [
        f for f in python_files
        if f.path.startswith("tests/") or Path(f.path).name.startswith("test_")
    ]
    for test in test_files:
        tails = {v.rsplit(".", 1)[-1] for v in set(test.calls) | set(test.imports)}
        for symbol in symbols:
            if symbol.name in tails and symbol.path != test.path:
                tests[f"{symbol.module}.{symbol.qualname}"].add(test.path)
    return {key: sorted(values) for key, values in sorted(tests.items())}


def resolve_relative(module: str, current: str, is_package: bool) -> str:
    if not module.startswith("."):
        return module
    level = len(module) - len(module.lstrip("."))
    base = current.split(".")
    if not is_package:
        base = base[:-1]
    base = base[: len(base) - (level - 1)] if level > 1 else base
    rest = module.lstrip(".")
    return ".".join([*base, rest] if rest else base)


def import_integrity_attention(
    python_files: list[PythonFileAnalysis],
    notebooks: list[NotebookAnalysis],
    internal_roots: set[str],
) -> list[Attention]:
    modules = {f.module: f for f in python_files}
    packages = {m.rsplit(".", 1)[0] for m in modules if "." in m}
    missing_modules: defaultdict[str, set[str]] = defaultdict(set)
    missing_names: defaultdict[str, set[str]] = defaultdict(set)

    def check(module: str, names: list[str], where: str) -> None:
        if module.split(".")[0] not in internal_roots:
            return
        if module not in modules and module not in packages:
            missing_modules[module].add(where)
            return
        target = modules.get(module)
        if target is None or target.has_star_import or target.parse_error:
            return
        defined = set(target.top_level_names)
        for name in names:
            if name == "*" or name in defined:
                continue
            if f"{module}.{name}" in modules or f"{module}.{name}" in packages:
                continue
            missing_names[f"{module}.{name}"].add(where)

    for f in python_files:
        is_pkg = f.path.endswith("__init__.py")
        for item in f.import_from:
            module = resolve_relative(item["module"], f.module, is_pkg)
            check(module, item["names"], f"{f.path}:{item['lineno']}")
        for value in f.imports:
            if "." not in value and value in internal_roots:
                continue
    for nb in notebooks:
        for item in nb.import_from:
            check(item["module"], item["names"], f"{nb.path}#cell-{item.get('cell')}")
    attention = [
        Attention(
            "high", "internal-import-missing-module",
            f"Import of internal module `{name}`, which does not exist in the snapshot.",
            sorted(paths),
            "Check branch completeness, renamed modules or stale imports before recreating code.",
        )
        for name, paths in sorted(missing_modules.items())
    ]
    attention += [
        Attention(
            "high", "internal-import-missing-name",
            f"`{name.rsplit('.', 1)[1]}` is imported from `{name.rsplit('.', 1)[0]}`, "
            "but that module does not define or re-export it.",
            sorted(paths),
            "Export the name in the module (or its __init__) or fix the import.",
        )
        for name, paths in sorted(missing_names.items())
    ]
    return attention


def call_signature_attention(
    symbols: list[Symbol],
    python_files: list[PythonFileAnalysis],
    notebooks: list[NotebookAnalysis],
) -> list[Attention]:
    """Calls to project functions with keywords they do not accept."""
    candidates: defaultdict[str, list[Symbol]] = defaultdict(list)
    for symbol in symbols:
        if symbol.kind in {"function", "class"} and symbol.path.startswith("src/"):
            candidates[symbol.name].append(symbol)
    unique = {name: items[0] for name, items in candidates.items() if len(items) == 1}
    local_defs: dict[str, set[str]] = defaultdict(set)
    for f in python_files:
        local_defs[f.path].update(s.name for s in f.symbols if s.kind in {"function", "class"})
    for nb in notebooks:
        local_defs[nb.path].update(s.name for s in nb.functions + nb.classes)

    problems: list[Attention] = []
    sources = [(f.path, f.call_sites) for f in python_files] + [(n.path, n.call_sites) for n in notebooks]
    for path, sites in sources:
        for site in sites:
            tail = site.name.rsplit(".", 1)[-1]
            target = unique.get(tail)
            if target is None or path == target.path or tail in local_defs[path]:
                continue
            if "." in site.name and site.name.split(".")[0] in {"self", "cls"}:
                continue
            issues: list[str] = []
            if not target.has_varkw:
                bad = [k for k in site.keywords if k not in target.params]
                if bad:
                    issues.append(f"unknown keyword(s) {bad}")
            if not target.has_varargs and not site.has_star_args and site.n_positional > target.n_positional_params:
                issues.append(
                    f"{site.n_positional} positional args, accepts {target.n_positional_params}"
                )
            if issues:
                problems.append(
                    Attention(
                        "high", "call-signature-mismatch",
                        f"Call to `{target.module}.{target.name}` does not match its signature: "
                        + "; ".join(issues) + ".",
                        [site.location, f"definition: {target.path}:{target.lineno} `{target.signature}`"],
                        "Fix the call or the function signature; this raises TypeError when executed.",
                    )
                )
    return problems


def gate_attention(
    gate_names: set[str],
    files_text: dict[str, str],
    notebook_sources: dict[str, str],
) -> list[Attention]:
    if not gate_names:
        return []
    found: defaultdict[str, set[str]] = defaultdict(set)
    for path, text in {**files_text, **notebook_sources}.items():
        if path.endswith(("supervised.yaml", OUTPUT_MD_NAME)):
            continue
        for match in GATE_RE.findall(text):
            found[match].add(path)
    stale = {name: paths for name, paths in found.items() if name not in gate_names}
    return [
        Attention(
            "medium", "gate-name-not-in-yaml",
            f"`{name}` is referenced but does not exist in `gates` of the active YAML.",
            sorted(paths),
            "Update the reference (code, docstring, notebook or document) to an existing gate.",
        )
        for name, paths in sorted(stale.items())
    ]


def config_contract_attention(config: Any, python_files: list[PythonFileAnalysis]) -> list[Attention]:
    if not isinstance(config, dict):
        return []
    attention: list[Attention] = []

    def as_list(*keys: str) -> list[str]:
        value = nested_get(config, *keys, default=[])
        return [str(v) for v in value] if isinstance(value, list) else []

    final = as_list("features", "final")
    active = set(final) or set(as_list("features", "numericas")) | set(as_list("features", "categoricas"))
    prohibited = set(as_list("features", "proibidas"))
    if active & prohibited:
        attention.append(Attention(
            "high", "feature-leakage-contract",
            "Configured model features overlap `features.proibidas`.",
            sorted(active & prohibited), "Remove the overlap or revise configuration and tests."))
    target = nested_get(config, "target", "coluna")
    if target and target not in prohibited:
        attention.append(Attention(
            "high", "feature-leakage-contract", "`target.coluna` is not in `features.proibidas`.",
            [str(target)], "Add the raw target to the forbidden list."))
    derived = set(as_list("features", "engenharia", "derivadas"))
    model_features = set(as_list("features", "numericas")) | set(as_list("features", "categoricas"))
    unused_derived = sorted(derived - model_features - set(final))
    if unused_derived:
        attention.append(Attention(
            "low", "derived-not-used-as-feature",
            "Derived columns produced by feature engineering but absent from the model feature lists.",
            unused_derived, "Confirm whether they are intentionally descriptive-only or missing from the model."))
    source_text = "\n".join(
        " ".join(f.calls + list(f.constants) + list(f.constants.values()) + f.file_literals + f.top_level_names)
        for f in python_files if f.path.startswith(("src/features/", "src/data/"))
    )
    absent = sorted(v for v in derived if v not in source_text)
    if absent:
        attention.append(Attention(
            "medium", "derived-feature-contract",
            "Configured derived features not found as static names in src/features or src/data.",
            absent, "Confirm whether names are dynamic, stale or missing from the implementation."))
    fractions = nested_get(config, "temporal", "fracao", default={})
    if isinstance(fractions, dict):
        numeric = [v for v in fractions.values() if isinstance(v, (int, float))]
        if numeric and abs(sum(numeric) - 1.0) > 1e-9:
            attention.append(Attention(
                "high", "split-contract", "Split fractions do not sum to 1.", [repr(fractions)],
                "Correct the split contract."))
    models = nested_get(config, "models", default={}) or {}
    closed = set(as_list("selecao_modelos", "familias_encerradas"))
    for name in sorted(closed):
        if nested_get(models, name, "ativa") is True:
            attention.append(Attention(
                "low", "config-consistency",
                f"`models.{name}.ativa` is true, but the family is in `selecao_modelos.familias_encerradas`.",
                [f"models.{name}.ativa"], "Set `ativa: false` or remove the family from the closed list."))
    finalists = as_list("selecao_modelos", "finalistas")
    for name in finalists:
        if name not in models:
            attention.append(Attention(
                "medium", "config-consistency",
                f"Finalist `{name}` has no section in `models` (factory names must match).",
                [f"selecao_modelos.finalistas: {finalists}", f"models: {sorted(models)}"],
                "Use the same names or declare an explicit alias in code."))
    gates = nested_get(config, "gates", default={}) or {}
    numbers = sorted(int(m.group(1)) for k in gates for m in [re.match(r"G(\d+)_", str(k))] if m)
    if numbers:
        gaps = [f"G{n}" for n in range(numbers[0], numbers[-1] + 1) if n not in numbers]
        if gaps:
            attention.append(Attention(
                "low", "gate-numbering", "Gate numbering has gaps.", gaps,
                "Document why the gate does not exist or renumber."))
    return attention


def unused_config_keys_attention(config: Any, code_text: str) -> list[Attention]:
    if not isinstance(config, dict):
        return []
    unused: list[str] = []
    for key in flatten_mapping(config):
        parts = key.split(".")
        if parts[0] in {"gates", "selecao_modelos"}:
            continue
        leaf = next((p for p in reversed(parts) if not p.isdigit()), parts[-1])
        if not re.search(rf"['\"]{re.escape(leaf)}['\"]", code_text):
            unused.append(key)
    if not unused:
        return []
    return [Attention(
        "low", "config-key-not-referenced",
        f"{len(unused)} YAML keys whose name never appears as a string literal in code or notebooks "
        "(possible dead configuration, or keys read dynamically).",
        unused[:80], "Remove dead keys or make the code read them; keep documentation keys commented.")]


def dependency_attention(
    python_files: list[PythonFileAnalysis],
    notebooks: list[NotebookAnalysis],
    requirements: dict[str, str] | None,
    pyproject_deps: dict[str, str] | None,
    import_map: dict[str, str],
    internal_roots: set[str],
) -> list[Attention]:
    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    used: defaultdict[str, set[str]] = defaultdict(set)
    for f in python_files:
        for value in f.external_imports:
            used[value.split(".")[0]].add(f.path)
    for nb in notebooks:
        for value in nb.imports:
            used[value.split(".")[0]].add(nb.path)
    third_party = {
        top: paths for top, paths in used.items()
        if top and top not in stdlib and top not in internal_roots and not top.startswith("_")
        and top not in {"__future__"}
    }
    attention: list[Attention] = []
    for label, deps in (("requirements.txt", requirements), ("pyproject.toml", pyproject_deps)):
        if deps is None:
            continue
        missing = []
        for top, paths in sorted(third_party.items()):
            dist = import_map.get(top, top).lower().replace("_", "-")
            if dist not in deps and top.lower() not in deps:
                missing.append(f"{top} (distribution `{dist}`) used in {sorted(paths)[0]}")
        if missing:
            attention.append(Attention(
                "medium", "dependency-not-declared",
                f"Third-party imports not declared in `{label}`.", missing,
                "Declare them (with a minimum version) in a single source of dependencies."))
        unpinned = sorted(name for name, spec in deps.items() if not spec)
        if unpinned:
            attention.append(Attention(
                "low", "dependency-unpinned", f"Dependencies without version constraint in `{label}`.",
                unpinned, "Add minimum versions for reproducibility (at least scikit-learn, pandas, numpy)."))
    return attention


def duplicate_symbol_attention(symbols: list[Symbol]) -> list[Attention]:
    grouped: defaultdict[str, set[str]] = defaultdict(set)
    for symbol in symbols:
        if symbol.kind in {"function", "class"} and not symbol.path.startswith("tests/") and symbol.name != "main":
            grouped[symbol.name].add(symbol.path)
    return [
        Attention(
            "medium", "duplicate-symbol-name", f"`{name}` is defined in multiple files.",
            sorted(paths), "Confirm distinct responsibilities or consolidate competing implementations.")
        for name, paths in sorted(grouped.items()) if len(paths) > 1
    ]


def notebook_attention(notebooks: list[NotebookAnalysis], python_files: list[PythonFileAnalysis]) -> list[Attention]:
    canonical: defaultdict[str, list[str]] = defaultdict(list)
    for f in python_files:
        if f.path.startswith("src/"):
            for s in f.symbols:
                if s.kind in {"function", "class"}:
                    canonical[s.name].append(s.path)
    attention: list[Attention] = []
    for nb in notebooks:
        for s in nb.functions + nb.classes:
            if s.name in canonical:
                attention.append(Attention(
                    "medium", "notebook-duplicates-src",
                    f"Notebook defines `{s.name}`, already present in src.",
                    [s.path, *sorted(set(canonical[s.name]))],
                    "Use the src implementation, or extend it if behaviour differs."))
        local = [s.name for s in nb.functions + nb.classes if s.name not in canonical]
        if local:
            attention.append(Attention(
                "low", "notebook-local-functions",
                f"`{nb.path}` defines {len(local)} local functions/classes.",
                local, "Keep single-use orchestration in the notebook; move reusable logic to src with tests."))
        if nb.out_of_order:
            attention.append(Attention(
                "medium", "notebook-execution-order",
                f"`{nb.path}` was saved with cells executed out of order.",
                [str(nb.execution_counts)], "Restart the kernel and run all cells before trusting saved outputs."))
        if nb.code_cells and nb.executed_cells < nb.code_cells:
            attention.append(Attention(
                "low", "notebook-not-fully-executed",
                f"`{nb.path}`: {nb.code_cells - nb.executed_cells} of {nb.code_cells} code cells have no saved execution.",
                [], "Outputs may be partial; re-run before using results."))
        if nb.error_outputs:
            attention.append(Attention(
                "high", "notebook-saved-errors", f"`{nb.path}` was saved with error outputs.",
                nb.error_outputs[:20], "Fix the error and re-run, or clear the stale output."))
        if nb.parse_errors:
            attention.append(Attention(
                "medium", "notebook-parse-error", f"`{nb.path}` has code cells that could not be parsed.",
                nb.parse_errors[:20], "Check syntax (magics are already tolerated)."))
    return attention


def stale_document_attention(files_text: dict[str, str], existing_paths: set[str]) -> list[Attention]:
    path_re = re.compile(
        r"(?<![A-Za-z0-9_./-])((?:src|tests|notebooks|configs|tools|docs|data|outputs)/"
        r"[A-Za-z0-9_./-]+\.(?:py|ipynb|yaml|yml|md|csv|json|parquet|toml))"
    )
    existing_dirs = {str(Path(p).parent.as_posix()) for p in existing_paths}
    attention: list[Attention] = []
    for path, text in files_text.items():
        if not path.lower().endswith((".md", ".rst", ".txt", ".py", ".yaml", ".yml")):
            continue
        refs = sorted({m.group(1) for m in path_re.finditer(text)})
        missing = [
            r for r in refs
            if r not in existing_paths and "{" not in r and "*" not in r and r not in existing_dirs
        ]
        if missing:
            attention.append(Attention(
                "low" if path.endswith(".py") else "medium", "reference-to-missing-path",
                f"`{path}` references paths absent from the working folder.", missing[:40],
                "Confirm whether the reference is historical, generated at runtime, or stale."))
    return attention


def text_quality_attention(files_text: dict[str, str], notebook_sources: dict[str, str]) -> tuple[list[Attention], list[str]]:
    mojibake: list[str] = []
    todos: list[str] = []
    for path, text in {**files_text, **notebook_sources}.items():
        if path.endswith(OUTPUT_MD_NAME):
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if MOJIBAKE_RE.search(line):
                mojibake.append(f"{path}:{number}: {line.strip()[:100]}")
            match = TODO_RE.search(line)
            if match and not path.endswith(".csv"):
                todos.append(f"{path}:{number}: {match.group(1)} {match.group(2).strip()}")
    attention = []
    if mojibake:
        attention.append(Attention(
            "low", "encoding-mojibake", "Text with likely encoding corruption (file saved with the wrong encoding).",
            mojibake[:40], "Fix the characters and save the file as UTF-8."))
    return attention, todos


def working_tree_attention(entries: list[GitEntry]) -> list[Attention]:
    relevant = [e.path for e in entries if not e.tracked and e.exists and e.path.startswith(IMPORTANT_UNTRACKED_PREFIXES)]
    modified = [f"{e.path} ({e.status.strip()})" for e in entries if e.tracked and e.status.strip()]
    attention = []
    if relevant:
        attention.append(Attention(
            "high", "untracked-relevant-files", "Relevant files exist only in the working tree (not committed).",
            relevant, "Commit intentional files or remove them before treating the snapshot as the project state."))
    if modified:
        attention.append(Attention(
            "medium", "uncommitted-changes", "Tracked files with uncommitted changes.", modified[:60],
            "Review Section 16 (diff) and commit or discard."))
    return attention


def symbol_quality_attention(
    symbols: list[Symbol],
    consumers: dict[str, list[str]],
    tests: dict[str, list[str]],
) -> list[Attention]:
    public = [
        s for s in symbols
        if s.path.startswith("src/") and not s.is_private and s.kind in {"function", "class"}
    ]
    orphan = [f"{s.module}.{s.name}" for s in public if not consumers.get(f"{s.module}.{s.qualname}") and not tests.get(f"{s.module}.{s.qualname}")]
    untested = [f"{s.module}.{s.name}" for s in public if not tests.get(f"{s.module}.{s.qualname}")]
    nodoc = [f"{s.module}.{s.name}" for s in public if not s.docstring]
    out = []
    if orphan:
        out.append(Attention("low", "public-symbol-unused",
                             "Public src symbols with no detected consumer and no test (possibly dead code).",
                             orphan, "Remove, test, or document why they exist."))
    if untested:
        out.append(Attention("low", "public-symbol-untested",
                             f"{len(untested)} public src symbols without a detected test.", untested,
                             "Prioritise tests for functions used by notebooks C2–C6."))
    if nodoc:
        out.append(Attention("low", "missing-docstring", "Public src symbols without docstring.", nodoc,
                             "Add a short docstring with purpose, parameters and returned value."))
    return out


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def render_attention(attention: list[Attention]) -> str:
    if not attention:
        return "- No static inconsistencies detected."
    counts = Counter(a.severity for a in attention)
    lines = [
        f"Totals: **{counts.get('high', 0)} high**, {counts.get('medium', 0)} medium, {counts.get('low', 0)} low.",
        "",
        "| # | Severity | Category | Message |",
        "|---|---|---|---|",
    ]
    ordered = sorted(attention, key=lambda a: (SEVERITY_ORDER.get(a.severity, 9), a.category, a.message))
    for i, a in enumerate(ordered, 1):
        lines.append(f"| A{i} | {a.severity.upper()} | {a.category} | {a.message.replace('|', '/')} |")
    lines.append("")
    for i, a in enumerate(ordered, 1):
        lines += [f"### A{i}. {a.severity.upper()} — {a.category}", "", a.message, ""]
        if a.evidence:
            lines += ["**Evidence**", "", *(f"- `{v}`" for v in a.evidence), ""]
        if a.recommendation:
            lines += [f"**Recommended action:** {a.recommendation}", ""]
    return "\n".join(lines).rstrip()


def render_symbol(symbol: Symbol, consumers: dict[str, list[str]], tests: dict[str, list[str]]) -> str:
    key = f"{symbol.module}.{symbol.qualname}"
    lines = [
        f"#### `{symbol.qualname}`",
        "",
        code_block(symbol.signature, "python"),
        "",
        f"- Location: `{symbol.path}:{symbol.lineno}-{symbol.end_lineno}`",
        f"- Visibility: `{'private' if symbol.is_private else 'public'}`",
        "- Tested by: " + (", ".join(f"`{p}`" for p in tests.get(key, [])) or "not found statically"),
        "- Consumed by: " + (", ".join(f"`{p}`" for p in consumers.get(key, [])) or "not found statically"),
    ]
    if symbol.defaults:
        lines.append("- Defaults: " + ", ".join(f"`{k}={v}`" for k, v in symbol.defaults.items()))
    if symbol.decorators:
        lines.append("- Decorators: " + ", ".join(f"`{d}`" for d in symbol.decorators))
    if symbol.calls:
        lines.append("- Calls: " + ", ".join(f"`{c}`" for c in symbol.calls[:40]))
    if symbol.env_vars:
        lines.append("- Environment variables: " + ", ".join(f"`{e}`" for e in symbol.env_vars))
    if symbol.file_literals:
        lines.append("- File literals: " + ", ".join(f"`{e}`" for e in symbol.file_literals))
    lines += ["", symbol.docstring or "_Missing docstring._", ""]
    return "\n".join(lines)


def render_python_api(python_files: list[PythonFileAnalysis], consumers: dict, tests: dict) -> str:
    parts: list[str] = []
    for f in sorted(python_files, key=lambda x: x.path.lower()):
        parts += [f"### `{f.path}`", ""]
        if f.parse_error:
            parts += [f"- **Parse error:** `{f.parse_error}`", ""]
            continue
        parts += [
            f"- Module: `{f.module}` · {f.lines} lines",
            "- Internal imports: " + (", ".join(f"`{v}`" for v in f.internal_imports) or "none"),
            "- External imports: " + (", ".join(f"`{v}`" for v in f.external_imports) or "none"),
        ]
        if f.constants:
            parts.append("- Module constants: " + ", ".join(f"`{k} = {v}`" for k, v in f.constants.items()))
        if f.env_vars:
            parts.append("- Environment variables: " + ", ".join(f"`{e}`" for e in f.env_vars))
        parts.append("")
        if f.docstring:
            parts += [f.docstring, ""]
        for symbol in f.symbols:
            parts.append(render_symbol(symbol, consumers, tests))
    return "\n".join(parts).rstrip()


def render_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "- None."
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in row) + " |" for row in rows]
    return "\n".join(out)


def render_tree(inventory: list[dict[str, Any]]) -> str:
    """Directory tree with file counts and sizes."""
    dirs: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in inventory:
        parent = str(Path(row["path"]).parent.as_posix())
        while True:
            dirs[parent][0] += 1
            dirs[parent][1] += row["bytes"]
            if parent in {".", ""}:
                break
            parent = str(Path(parent).parent.as_posix())
    lines = []
    for d in sorted(dirs):
        depth = 0 if d == "." else d.count("/") + 1
        name = "./" if d == "." else Path(d).name + "/"
        lines.append(f"{'  ' * depth}{name}  ({dirs[d][0]} files, {human_bytes(dirs[d][1])})")
    return code_block("\n".join(lines), "text")


def split_document(document: str, max_bytes: int) -> list[str]:
    """Split on level-2 headings, keeping parts under max_bytes when possible."""
    chunks: list[str] = []
    current: list[str] = []
    in_fence = None
    for line in document.splitlines(keepends=True):
        fence = re.match(r"^(`{3,})", line)
        if fence:
            if in_fence is None:
                in_fence = fence.group(1)
            elif line.strip() == in_fence:
                in_fence = None
        if in_fence is None and line.startswith("## ") and current:
            chunks.append("".join(current))
            current = []
        current.append(line)
    if current:
        chunks.append("".join(current))
    parts: list[str] = []
    buffer = ""
    for chunk in chunks:
        if buffer and len((buffer + chunk).encode("utf-8")) > max_bytes:
            parts.append(buffer)
            buffer = ""
        if len(chunk.encode("utf-8")) > max_bytes:
            lines = chunk.splitlines(keepends=True)
            piece = ""
            for line in lines:
                if piece and len((piece + line).encode("utf-8")) > max_bytes:
                    parts.append(piece + "\n\n_(section continues in the next part)_\n")
                    piece = ""
                piece += line
            buffer = piece
        else:
            buffer += chunk
    if buffer:
        parts.append(buffer)
    return parts


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build_reference(root: Path, args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    redactor = Redactor(root)
    entries, tracked, untracked = collect_git_entries(root)
    inventory, inventory_truncated = walk_inventory(root, tracked, untracked)
    inv_by_path = {row["path"]: row for row in inventory}
    existing_paths = set(inv_by_path)

    internal_roots = {
        Path(e.path).parts[0] for e in entries
        if e.exists and Path(e.path).suffix.lower() in {".py", ".pyi"} and len(Path(e.path).parts) > 1
    } | {"src", "tests", "tools"}

    selected: list[tuple[Path, bool, str]] = []
    seen: set[str] = set()
    for e in entries:
        if e.exists and include_source(Path(e.path), tracked=e.tracked):
            selected.append((Path(e.path), e.tracked, e.status))
            seen.add(e.path)
    ignored_sources: list[str] = []
    for row in inventory:
        rel_path = Path(row["path"])
        if (
            row["git"] == "ignored"
            and row["path"] not in seen
            and row["path"].startswith(IMPORTANT_UNTRACKED_PREFIXES)
            and include_source(rel_path, tracked=True)
        ):
            selected.append((rel_path, False, "!! ignored by .gitignore"))
            ignored_sources.append(row["path"])

    python_files: list[PythonFileAnalysis] = []
    notebooks: list[NotebookAnalysis] = []
    files_text: dict[str, str] = {}
    notebook_text: dict[str, str] = {}
    file_records: list[dict[str, Any]] = []
    source_sections: list[str] = []
    skipped: list[str] = []
    yaml_docs: dict[str, dict[str, Any]] = {}
    config: Any = None
    config_error: str | None = None
    yaml_duplicates: dict[str, list[str]] = {}
    pyproject_data: dict[str, Any] | None = None
    pyproject_error: str | None = None
    requirements: dict[str, str] | None = None

    for rel, is_tracked, status in selected:
        absolute = root / rel
        data = absolute.read_bytes()
        digest = sha256_bytes(data)
        suffix = rel.suffix.lower()
        header = [
            f"## `{rel.as_posix()}`",
            "",
            f"- Git: `{'tracked' if is_tracked else 'untracked (working tree)'}` · status `{status.strip() or 'clean'}`",
            f"- Size: `{human_bytes(len(data))}` · modified `{inv_by_path.get(rel.as_posix(), {}).get('modified_utc', '?')} UTC`",
            f"- SHA-256: `{digest}`",
        ]
        record = {
            "path": rel.as_posix(), "tracked": is_tracked, "status": status, "sha256": digest,
            "bytes": len(data), "type": suffix.lstrip(".") or rel.name,
        }
        if suffix in LIKELY_BINARY_SUFFIXES:
            skipped.append(f"{rel.as_posix()} (binary)")
            continue
        if suffix == ".ipynb":
            try:
                analysis, nb = analyze_notebook(rel, data, internal_roots)
            except Exception as exc:
                skipped.append(f"{rel.as_posix()} (notebook parse error: {exc!r})")
                continue
            reduced = len(data) > args.max_inline_bytes
            analysis.outputs_included = args.notebook_outputs
            notebooks.append(analysis)
            notebook_text[rel.as_posix()] = "\n".join(
                "".join(c.get("source", [])) for c in nb.get("cells", [])
            )
            body = notebook_source_markdown(
                nb, analysis, include_outputs=args.notebook_outputs,
                max_output_chars=args.max_output_chars, reduced=reduced, redactor=redactor,
            )
            source_sections.append("\n".join(header) + "\n\n" + body + "\n")
            file_records.append(record)
            continue
        if suffix in OFFICE_SUFFIXES:
            try:
                text = office_text(data, suffix)
            except Exception as exc:
                skipped.append(f"{rel.as_posix()} (office parse error: {exc!r})")
                continue
            text, warnings = redactor(text)
            files_text[rel.as_posix()] = text
            header.append("- Content: plain text extracted (formatting, tables layout and images not preserved)")
            source_sections.append("\n".join(header) + "\n\n" + code_block(truncate(text, args.max_inline_bytes), "text") + "\n")
            file_records.append(record)
            continue
        if b"\x00" in data[:8192]:
            skipped.append(f"{rel.as_posix()} (binary content)")
            continue
        decoded = data.decode("utf-8-sig", errors="replace")
        text, warnings = redactor(decoded)
        if rel.as_posix() == "tools/update_project_reference.py":
            text, warnings = decoded, []  # the generator's own regexes look like secrets
            for value in redactor.root_variants:
                text = text.replace(value, "<REPO>")
        files_text[rel.as_posix()] = text
        if warnings:
            header.append("- Security: " + "; ".join(warnings))
        if suffix in {".py", ".pyi"}:
            python_files.append(analyze_python(rel, text, internal_roots))
        elif suffix in {".yaml", ".yml"}:
            parsed, error, dups = load_yaml_strict(decoded)
            yaml_docs[rel.as_posix()] = {"error": error, "duplicates": dups}
            if dups:
                yaml_duplicates[rel.as_posix()] = dups
            if rel.as_posix() == args.config:
                config, config_error = parsed, error
        elif rel.name == "pyproject.toml":
            pyproject_data, pyproject_error = parse_pyproject(decoded)
        elif rel.name == "requirements.txt" and len(rel.parts) == 1:
            requirements = parse_requirements(decoded)
        if suffix in {".csv", ".tsv"} and len(data) > args.max_artifact_bytes:
            preview, total = csv_preview(text, args.max_csv_rows)
            header.append(f"- Content: first {args.max_csv_rows} of {total} rows")
            body = code_block(preview, "csv")
        elif len(data) > args.max_inline_bytes:
            body = code_block(truncate(text, args.max_inline_bytes), LANG.get(suffix, "text"))
        else:
            body = code_block(text.rstrip(), LANG.get(suffix, "text"))
        source_sections.append("\n".join(header) + "\n\n" + body + "\n")
        file_records.append(record)

    # Small text artifacts (outputs/, data/ manifests, reports/)
    artifact_sections: list[str] = []
    artifact_records: list[dict[str, Any]] = []
    if args.artifacts:
        for row in inventory:
            rel = Path(row["path"])
            if not include_artifact(rel, row["bytes"], args.max_artifact_bytes):
                continue
            try:
                raw = (root / rel).read_bytes()
            except OSError:
                continue
            if b"\x00" in raw[:8192]:
                continue
            text, _ = redactor(raw.decode("utf-8-sig", errors="replace"))
            suffix = rel.suffix.lower()
            note = ""
            if suffix in {".csv", ".tsv"}:
                text, total = csv_preview(text, args.max_csv_rows)
                note = f" · {total} rows" + (f" (first {args.max_csv_rows} shown)" if total > args.max_csv_rows else "")
            else:
                text = truncate(text, args.max_artifact_bytes)
            artifact_sections.append(
                f"### `{rel.as_posix()}`\n\n- Git: `{row['git']}` · `{human_bytes(row['bytes'])}` · "
                f"modified `{row['modified_utc']} UTC`{note}\n\n"
                + code_block(text.rstrip(), LANG.get(suffix, "text")) + "\n"
            )
            artifact_records.append(row)
            if suffix in {".yaml", ".yml"}:
                files_text[rel.as_posix()] = text

    # Indexes and diagnostics
    symbols = [s for f in python_files for s in f.symbols]
    consumers = index_consumers(symbols, python_files, notebooks)
    tests = index_tests(symbols, python_files)
    import_map = top_level_import_map()
    packages = installed_packages()
    pyproject_deps = pyproject_dependencies(pyproject_data) if pyproject_data else None
    gates = nested_get(config, "gates", default={}) if isinstance(config, dict) else {}
    gate_names = set(gates) if isinstance(gates, dict) else set()
    code_text = "\n".join(
        [t for p, t in files_text.items() if p.endswith(".py")] + list(notebook_text.values())
    )

    attention: list[Attention] = []
    attention += working_tree_attention(entries)
    if ignored_sources:
        attention.append(Attention(
            "high", "source-ignored-by-git",
            "Source/config/test/notebook files are ignored by .gitignore and therefore missing from GitHub.",
            ignored_sources,
            "Fix .gitignore (anchor root folders, e.g. `/data/` instead of `data/`) and commit the files."))
    attention += import_integrity_attention(python_files, notebooks, internal_roots)
    attention += call_signature_attention(symbols, python_files, notebooks)
    attention += config_contract_attention(config, python_files)
    attention += gate_attention(gate_names, files_text, notebook_text)
    attention += unused_config_keys_attention(config, code_text)
    attention += dependency_attention(python_files, notebooks, requirements, pyproject_deps, import_map, internal_roots)
    attention += duplicate_symbol_attention(symbols)
    attention += notebook_attention(notebooks, python_files)
    attention += stale_document_attention(files_text, existing_paths)
    quality, todos = text_quality_attention(files_text, notebook_text)
    attention += quality
    attention += symbol_quality_attention(symbols, consumers, tests)
    for f in python_files:
        if f.parse_error:
            attention.append(Attention("high", "python-parse-error", f"`{f.path}` could not be parsed.",
                                       [f.parse_error], "Fix syntax or check interpreter compatibility."))
    if config_error:
        attention.append(Attention("high", "yaml-error", f"`{args.config}` could not be analysed.",
                                   [config_error], "Fix the YAML (or install PyYAML) and regenerate."))
    for path, dups in yaml_duplicates.items():
        attention.append(Attention("high", "yaml-duplicate-keys",
                                   f"`{path}` has duplicated keys; yaml.safe_load silently keeps the last value.",
                                   dups, "Remove the duplicates."))
    if pyproject_error:
        attention.append(Attention("high", "pyproject-invalid", "`pyproject.toml` is not valid TOML.",
                                   [pyproject_error], "Fix it; `pip install -e .` fails with an invalid pyproject."))
    if inventory_truncated:
        attention.append(Attention("low", "inventory-truncated",
                                   f"Path inventory stopped at {MAX_INVENTORY_ENTRIES} files.", [],
                                   "Exclude large generated folders or raise MAX_INVENTORY_ENTRIES."))

    tests_result = run_tests(root, args.pytest_args, args.test_timeout) if args.run_tests else None
    if tests_result and tests_result["returncode"] not in (0, None):
        attention.append(Attention("high", "tests-failing", "pytest returned a non-zero exit code.",
                                   [tests_result["output"].splitlines()[-1] if tests_result["output"] else ""],
                                   "See Section 11."))

    # Git details
    branch = git(root, "branch", "--show-current").strip() or "detached"
    commit = git(root, "rev-parse", "HEAD", check=False).strip() or "no commits"
    remote, _ = redactor(git(root, "remote", "get-url", "origin", check=False).strip())
    status_text = git(root, "status", "--short", "--branch").rstrip() or "clean"
    log_text = git(root, "log", f"-{args.git_log}", "--date=iso", "--pretty=format:%h %ad %an%n    %s", check=False).rstrip()
    branches = git(root, "branch", "-a", "-vv", check=False).rstrip()
    ahead_behind = git(root, "rev-list", "--left-right", "--count", "HEAD...@{upstream}", check=False).strip()
    diff_stat = git(root, "diff", "HEAD", "--stat", check=False).rstrip()
    diff_text = ""
    if args.include_diff:
        raw_diff = git(root, "diff", "HEAD", "--", ".", ":(exclude)docs/" + OUTPUT_MD_NAME,
                       ":(exclude)docs/" + OUTPUT_JSON_NAME, check=False)
        diff_text = truncate(redactor(raw_diff)[0], args.max_diff_chars)
    gitignore_check = git(root, "check-ignore", "-v", "--no-index", *[
        p for p in ("data/", "outputs/", "models/", ".env", "configs/paths.local.json") if (root / p).exists()
    ], check=False).strip() if any((root / p).exists() for p in ("data", "outputs", "models", ".env")) else ""

    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    counts = Counter(a.severity for a in attention)
    public = [s for s in symbols if s.path.startswith("src/") and not s.is_private and s.kind in {"function", "class"}]

    # ---- Section 6
    sec6 = [
        "## 6. Executive continuation map", "",
        f"- Generated (UTC): `{generated}` · branch `{branch}` · commit `{commit[:12]}`",
        f"- Git status: `{'clean' if status_text.count(chr(10)) == 0 else 'has changes'}`; upstream ahead/behind: `{ahead_behind or 'n/a'}`",
        f"- Files in working folder (inventory): `{len(inventory)}` "
        f"(tracked `{sum(r['git'] == 'tracked' for r in inventory)}`, untracked `{sum(r['git'] == 'untracked' for r in inventory)}`, "
        f"ignored/local `{sum(r['git'] == 'ignored' for r in inventory)}`)",
        f"- Source files with full content: `{len(file_records)}`; artifacts included: `{len(artifact_records)}`",
        f"- Python modules: `{len(python_files)}` · notebooks: `{len(notebooks)}` · public src symbols: `{len(public)}`",
        f"- Public src symbols with tests: `{sum(bool(tests.get(f'{s.module}.{s.qualname}')) for s in public)}` · with consumers: "
        f"`{sum(bool(consumers.get(f'{s.module}.{s.qualname}')) for s in public)}`",
        f"- Attention items: **{counts.get('high', 0)} high**, {counts.get('medium', 0)} medium, {counts.get('low', 0)} low",
        f"- Tests executed: `{'yes, exit ' + str(tests_result['returncode']) if tests_result else 'no (use --run-tests)'}`",
        "",
        "### Canonical responsibility map", "",
        render_table(["Responsibility", "Inspect first"], [
            ["Data access and Parquet", "`src/utils/storage.py`, `src/utils/config.py`"],
            ["Cohort and supervised artifact", "`src/data/`, cohort notebooks, `tests/test_cohort_source.py`"],
            ["Feature engineering", "`src/features/`, `tests/test_features.py`, YAML `features`"],
            ["Split and leakage", "`src/data/split.py`, `src/evaluation/leakage.py`, split tests"],
            ["Models and pipelines", "`src/models/`, `tests/test_model_pipelines.py`"],
            ["Metrics, calibration, errors", "`src/evaluation/`, `src/models/calibration.py`"],
            ["Experiment logging", "`src/utils/reproducibility.py`"],
            ["Decisions and gates", f"`{args.config}`, `docs/decisoes.md`"],
        ]),
    ]

    # ---- Section 8: configuration
    sec8 = ["## 8. Configuration", ""]
    if isinstance(config, dict):
        if gate_names:
            sec8 += ["### Gates", "", render_table(
                ["Gate", "Status", "Approved by", "Date", "Description"],
                [[f"`{k}`", str(nested_get(gates, k, "status")), str(nested_get(gates, k, "aprovado_por")),
                  str(nested_get(gates, k, "data")), str(nested_get(gates, k, "descricao") or "").strip()[:160]]
                 for k in gates]), ""]
        sec8 += ["### Flattened active configuration", "", f"Source: `{args.config}`", ""]
        sec8 += [f"- `{k}`: `{repr(v)[:400]}`" for k, v in flatten_mapping(config).items()]
    else:
        sec8.append(f"- Configuration unavailable: `{config_error}`")
    sec8 += ["", "### YAML files", "", render_table(
        ["File", "Parse", "Duplicated keys"],
        [[f"`{p}`", "ok" if not d["error"] else d["error"][:80], ", ".join(d["duplicates"]) or "none"]
         for p, d in sorted(yaml_docs.items())])]
    sec8 += ["", "### pyproject.toml", ""]
    if pyproject_data is not None:
        sec8 += [
            f"- Valid TOML: yes · name `{nested_get(pyproject_data, 'project', 'name')}` · "
            f"requires-python `{nested_get(pyproject_data, 'project', 'requires-python')}`",
            "- Dependencies: " + (", ".join(f"`{k}{v}`" for k, v in (pyproject_deps or {}).items()) or "none"),
        ]
    else:
        sec8.append(f"- {pyproject_error or 'not found'}")
    sec8 += ["", "### requirements.txt", "",
             "- " + (", ".join(f"`{k}{v}`" for k, v in requirements.items()) if requirements else "not found")]

    # ---- Section 9: environment
    key_rows = []
    declared = {**(requirements or {}), **(pyproject_deps or {})}
    for name in KEY_PACKAGES:
        if name in packages or name in declared:
            key_rows.append([f"`{name}`", packages.get(name, "**not installed**"),
                             (requirements or {}).get(name, "—") if requirements is not None else "n/a",
                             (pyproject_deps or {}).get(name, "—") if pyproject_deps is not None else "n/a"])
    sec9 = [
        "## 9. Python environment", "",
        f"- Interpreter: `{sys.version.split()[0]}` · implementation `{platform.python_implementation()}`",
        f"- Executable inside repo venv: `{'yes' if str(root).lower() in sys.executable.lower() else 'no (results reflect another interpreter)'}`",
        f"- Platform: `{platform.platform()}`",
        f"- PyYAML available: `{yaml is not None}` · tomllib available: `{tomllib is not None}`",
        "", "### Key packages: installed vs declared", "",
        render_table(["Package", "Installed", "requirements.txt", "pyproject.toml"], key_rows),
        "", "### All installed distributions", "",
        code_block("\n".join(f"{k}=={v}" for k, v in packages.items()), "text"),
    ]

    # ---- Section 10: inventory
    sec10 = [
        "## 10. Path inventory of the working folder", "",
        "Contents of data/models are never copied. `ignored` = exists locally but is ignored by Git.", "",
        "### Directory tree", "", render_tree(inventory), "",
        "### All files", "",
        render_table(["Path", "Git", "Size", "Modified (UTC)"],
                     [[f"`{r['path']}`", r["git"], human_bytes(r["bytes"]), r["modified_utc"]] for r in inventory]),
        "", "### Skipped files", "", *(f"- `{s}`" for s in skipped), *([] if skipped else ["- None."]),
        "", "### .gitignore check for local folders", "", code_block(gitignore_check or "n/a", "text"),
    ]

    # ---- Section 11: tests
    test_rows = []
    for f in python_files:
        if f.path.startswith("tests/") or Path(f.path).name.startswith("test_"):
            names = [s.qualname for s in f.symbols if s.name.startswith("test_")]
            test_rows.append([f"`{f.path}`", str(len(names)), ", ".join(f"`{v}`" for v in f.internal_imports) or "none"])
    sec11 = ["## 11. Tests", "", render_table(["Test file", "Tests", "Internal imports"], test_rows), ""]
    if tests_result:
        sec11 += [f"### pytest result (exit `{tests_result['returncode']}`)", "",
                  f"Command: `{tests_result['command']}`", "",
                  code_block(truncate(redactor(tests_result["output"])[0], 60_000), "text")]
    else:
        sec11.append("pytest was not executed. Use `--run-tests` (optionally `--pytest-args \"-m 'not slow'\"`).")

    # ---- Section 13/14/15
    dep_rows = [[f"`{f.module}`", ", ".join(f"`{v}`" for v in f.internal_imports) or "none"]
                for f in sorted(python_files, key=lambda x: x.module)]
    sec13 = ["## 13. Internal dependency map", "", render_table(["Module", "Internal imports"], dep_rows)]
    nb_rows = [[f"`{n.path}`", f"{n.code_cells}/{n.markdown_cells}", f"{n.executed_cells}/{n.code_cells}",
                "yes" if n.out_of_order else "no", str(len(n.error_outputs)),
                ", ".join(f"`{v}`" for v in n.internal_imports) or "none",
                ", ".join(f"`{s.name}`" for s in n.functions + n.classes) or "none"]
               for n in sorted(notebooks, key=lambda x: x.path)]
    sec14 = ["## 14. Notebook orchestration inventory", "",
             render_table(["Notebook", "Code/MD cells", "Executed", "Out of order", "Errors",
                           "Internal imports", "Local functions"], nb_rows), ""]
    for n in sorted(notebooks, key=lambda x: x.path):
        sec14 += [f"### `{n.path}` headings", "", *(f"- {h}" for h in n.headings), ""]
        if n.file_literals:
            sec14 += ["Referenced files: " + ", ".join(f"`{v}`" for v in n.file_literals), ""]
    env_index: defaultdict[str, set[str]] = defaultdict(set)
    for f in python_files:
        for e in f.env_vars:
            env_index[e].add(f.path)
    for n in notebooks:
        for e in n.env_vars:
            env_index[e].add(n.path)
    lit_index: defaultdict[str, set[str]] = defaultdict(set)
    for f in python_files:
        for lit in f.file_literals:
            lit_index[lit].add(f.path)
    for n in notebooks:
        for lit in n.file_literals:
            lit_index[lit].add(n.path)
    sec15 = ["## 15. Environment variables, file literals and TODOs", "",
             "### Environment variables (names only)", "",
             *([f"- `{k}`: " + ", ".join(f"`{p}`" for p in sorted(v)) for k, v in sorted(env_index.items())] or ["- None."]),
             "", "### File names referenced in code", "",
             *([f"- `{k}` ← " + ", ".join(f"`{p}`" for p in sorted(v)) for k, v in sorted(lit_index.items())] or ["- None."]),
             "", "### TODO / FIXME / PENDENTE markers", "", *([f"- `{t}`" for t in todos] or ["- None."])]

    sec16 = ["## 16. Git history and uncommitted changes", "",
             "### Status", "", code_block(status_text, "text"), "",
             "### Branches", "", code_block(redactor(branches)[0] or "n/a", "text"), "",
             f"### Last {args.git_log} commits", "", code_block(redactor(log_text)[0] or "no commits", "text"), "",
             "### Diff stat (working tree vs HEAD)", "", code_block(diff_stat or "no changes", "text")]
    if args.include_diff:
        sec16 += ["", "### Full diff (working tree vs HEAD)", "", code_block(diff_text or "no changes", "diff")]

    document_parts = [
        CONTEXT.format(schema=SCHEMA_VERSION).rstrip(), "",
        *sec6, "",
        "## 7. Static attention report", "", render_attention(attention), "",
        *sec8, "", *sec9, "", *sec10, "", *sec11, "",
        "## 12. Python API and reuse catalog", "",
        "Generated with Python AST; project modules are not imported.", "",
        render_python_api(python_files, consumers, tests), "",
        *sec13, "", *sec14, "", *sec15, "", *sec16, "",
        "## 17. Full source by file", "",
        "Every relevant file of the repository, including untracked files in source folders. "
        "Notebooks include cell sources and, unless disabled, text outputs.", "",
        "\n".join(source_sections).rstrip(), "",
        "## 18. Local artifacts (small text files from data/, outputs/, reports/, models/)", "",
        ("\n".join(artifact_sections).rstrip() if artifact_sections else "- None included (use defaults or check --no-artifacts)."),
        "",
        "## 19. Snapshot provenance", "",
        f"- Generated UTC: `{generated}`",
        f"- Branch / commit: `{branch}` / `{commit}`",
        f"- Origin: `{remote or 'not configured'}`",
        f"- Generator options: `{ {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()} }`",
    ]
    document = "\n".join(document_parts).rstrip() + "\n"

    machine = {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "repository": {"branch": branch, "commit": commit, "origin": remote or None,
                       "status": status_text, "ahead_behind": ahead_behind},
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "packages": packages},
        "inventory": inventory,
        "files": file_records,
        "artifacts": artifact_records,
        "python_files": [asdict(f) for f in python_files],
        "notebooks": [asdict(n) for n in notebooks],
        "consumers": consumers,
        "tests_by_symbol": tests,
        "attention": [asdict(a) for a in attention],
        "environment_variables": {k: sorted(v) for k, v in sorted(env_index.items())},
        "config": config if isinstance(config, (dict, list)) else None,
        "config_error": config_error,
        "yaml_files": yaml_docs,
        "pyproject": {"valid": pyproject_data is not None, "error": pyproject_error, "dependencies": pyproject_deps},
        "requirements": requirements,
        "tests_result": tests_result,
        "todos": todos,
        "skipped": skipped,
    }
    return document, machine


def parse_args() -> argparse.Namespace:
    # argparse rejects values that start with "-" (e.g. --pytest-args "-m 'not slow'").
    argv = sys.argv[1:]
    for index, value in enumerate(argv[:-1]):
        if value == "--pytest-args" and argv[index + 1].startswith("-"):
            argv[index : index + 2] = [f"--pytest-args={argv[index + 1]}"]
            break
    parser = argparse.ArgumentParser(
        description="Generate a complete diagnostic snapshot of the repository for review by a person or an AI.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Destination folder (default: docs).")
    parser.add_argument("--config", default="configs/supervised.yaml", help="Main YAML configuration (relative path).")
    parser.add_argument("--split-mb", type=float, default=DEFAULT_SPLIT_MB,
                        help=f"Size of each part in docs/{PARTS_DIR_NAME}/ (default: {DEFAULT_SPLIT_MB} MB).")
    parser.add_argument("--no-split", dest="split", action="store_false",
                        help=f"Do not write docs/{PARTS_DIR_NAME}/.")
    parser.add_argument("--no-notebook-outputs", dest="notebook_outputs", action="store_false",
                        help="Omit notebook outputs (sources only).")
    parser.add_argument("--max-output-chars", type=int, default=DEFAULT_MAX_OUTPUT_CHARS,
                        help="Maximum characters per notebook output.")
    parser.add_argument("--no-artifacts", dest="artifacts", action="store_false",
                        help="Do not include small text artifacts from data/, outputs/, reports/, models/.")
    parser.add_argument("--max-artifact-bytes", type=int, default=DEFAULT_MAX_ARTIFACT_BYTES)
    parser.add_argument("--max-csv-rows", type=int, default=DEFAULT_MAX_CSV_ROWS)
    parser.add_argument("--max-inline-bytes", type=int, default=DEFAULT_MAX_INLINE_BYTES,
                        help="Files above this size are truncated (notebooks use a reduced view).")
    parser.add_argument("--git-log", type=int, default=DEFAULT_GIT_LOG, help="Number of recent commits to list.")
    parser.add_argument("--no-diff", dest="include_diff", action="store_false", help="Omit the full uncommitted diff.")
    parser.add_argument("--max-diff-chars", type=int, default=DEFAULT_MAX_DIFF_CHARS)
    parser.add_argument("--run-tests", action="store_true", help="Run pytest and include the result (executes project code).")
    parser.add_argument("--pytest-args", default="", help="Extra pytest arguments, e.g. \"-m 'not slow'\".")
    parser.add_argument("--test-timeout", type=int, default=1800)
    parser.add_argument("--fail-on-high", action="store_true", help="Exit with code 2 if HIGH attention items exist.")
    return parser.parse_args(argv)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles
        except Exception:
            pass
    args = parse_args()
    root = root_dir()
    document, machine = build_reference(root, args)
    out_dir = root / args.output_dir
    output_md = out_dir / OUTPUT_MD_NAME
    output_json = out_dir / OUTPUT_JSON_NAME
    atomic_write(output_md, document)
    atomic_write(output_json, json.dumps(machine, ensure_ascii=False, indent=2, default=str) + "\n")

    parts_dir = out_dir / PARTS_DIR_NAME
    if parts_dir.exists():
        for old in parts_dir.glob("part_*.md"):
            old.unlink()
    written_parts: list[Path] = []
    if args.split and args.split_mb > 0:
        parts = split_document(document, int(args.split_mb * 1024 * 1024))
        for index, part in enumerate(parts, 1):
            target = parts_dir / f"part_{index:02d}_of_{len(parts):02d}.md"
            header = f"<!-- PROJECT_COMPLETE_REFERENCE part {index}/{len(parts)} -->\n"
            atomic_write(target, header + part)
            written_parts.append(target)

    high = sum(a.get("severity") == "high" for a in machine["attention"])
    print(f"update_project_reference.py schema v{SCHEMA_VERSION}")
    print(f"Updated: {output_md} ({human_bytes(output_md.stat().st_size)})")
    print(f"Updated: {output_json} ({human_bytes(output_json.stat().st_size)})")
    if written_parts:
        print(f"Parts:   {len(written_parts)} file(s) in {parts_dir}")
        for part in written_parts:
            print(f"         {part.name} ({human_bytes(part.stat().st_size)})")
    else:
        print("Parts:   not written (--no-split)")
    print(f"Inventory: {len(machine['inventory'])} files, full source: {len(machine['files'])}, "
          f"artifacts: {len(machine['artifacts'])}")
    print(f"Python modules: {len(machine['python_files'])}, notebooks: {len(machine['notebooks'])}")
    print(f"Attention items: {len(machine['attention'])} ({high} high)")
    if machine.get("tests_result"):
        print(f"pytest exit code: {machine['tests_result']['returncode']}")
    if args.fail_on_high and high:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## `configs/paths.local.json`

- Git: `untracked (working tree)` · status `!! ignored by .gitignore`
- Size: `45 B` · modified `2026-10-08 01:30 UTC`
- SHA-256: `6a840ee1f558f2fa14ca762c3df41bf82300c680614792cd298d857ea68da198`

```json
{
"parquet_srag": "data/raw/srag.parquet"
}
```

## 18. Local artifacts (small text files from data/, outputs/, reports/, models/)

### `data/manifest_dados-v2.yaml`

- Git: `tracked` · `1.9 KB` · modified `2026-10-10 16:31 UTC`

```yaml
manifest_version: "1.0"

dataset:
  id: "srag-dados-v2"
  versao: "dados-v2"
  arquivo: "srag.parquet"
  formato: "parquet"
  caminho_relativo: "data/processed/dados-v2/srag.parquet"

integridade:
  sha256: "96ED6B9D5CEEBAAEA00659F77511112174B04BB980CB243B560C00DD2A8F316C
  tamanho_bytes: 303573013
  quantidade_linhas: 4666910
  quantidade_colunas: 198

cobertura_temporal:
  periodo_nominal_fontes: "2019-2026"
  periodo_observado_dt_notific:
    inicio: "2018-12-30"
    fim: "2026-09-28"
  observacao:
    - "Foram observados três registros com dt_notific em 2018."
    - "A elegibilidade temporal da coorte será definida por dt_interna, não por dt_notific."
    - "O recorte analítico principal considera internações entre 2019 e 2026."
    - "O ano de 2026 está incompleto na versão atual dos dados e deverá ser identificado como tal nas análises temporais."
    - "Os anos associados à pandemia serão mantidos inicialmente; qualquer exclusão posterior será tratada como análise de sensibilidade."

geracao:
  data_geracao: "2026-10-09"
  motivo_nova_versao: >
    Correção da geração de dt_notific. Na versão dados-v1,
    a coluna não preservava as datas individuais de notificação
    e apresentava valores concentrados em âncoras anuais do
    calendário epidemiológico. A versão dados-v2 preserva os
    valores individuais provenientes das fontes oficiais.

fontes:
  - nome: "Dados Abertos do SUS - SRAG 2019 a 2026"
    url: "https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026"

uso_no_projeto:
  interface_leitura: "src.utils.storage.read_srag"
  versao_configurada: "dados-v2"
  observacao: >
    Os notebooks devem acessar o dataset pela interface de storage
    do repositório, evitando caminhos locais absolutos.

validacao:
  schema_verificado: true
  dimensoes_verificadas: true
  notebook_validacao: "01_eda_primeira_passagem.ipynb"
  hash_confirmado_manualmente: true
```

### `data/analytical/manifesto_supervisionado.json`

- Git: `ignored` · `1.6 KB` · modified `2026-10-14 23:44 UTC`

```json
{
  "schema_version": 2,
  "generated_utc": "2026-10-14T23:44:05.778293+00:00",
  "cohort_kind": "provisional",
  "source": {
    "kind": "provisional",
    "path": "<REPO>\\data\\analytical\\coorte_provisoria_b.parquet",
    "sha256": "da94652dbabd832f512f8346f19ef3fb12adc3e418c27c9229d693b4fe43c7f9",
    "size_bytes": 209678288,
    "rows": 3915136,
    "columns": 125
  },
  "dataset_path": "<REPO>\\data\\analytical\\dataset_supervisionado.parquet",
  "dataset_sha256": "7653e525b944eef54d3b087e4ceb64fa9ba9d611c779325704716a38e95fcf40",
  "rows": 3915132,
  "columns": 36,
  "feature_columns": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
    "puerpera",
    "cardiopati",
    "hematologi",
    "sind_down",
    "hepatica",
    "asma",
    "diabetes",
    "neurologic",
    "pneumopati",
    "imunodepre",
    "renal",
    "obesidade",
    "out_morbi"
  ],
  "numeric_columns": null,
  "categorical_columns": null,
  "audit_columns": [],
  "target_column": "alvo_obito_srag",
  "partition_column": "particao",
  "partition_counts": {
    "treino": 2740587,
    "teste": 587274,
    "validacao": 587271
  },
  "seed": 42,
  "test_opened": false
}
```

### `outputs/runs/2026-10-11_231339_836520_03_supervisionado_pilotos/metadata.json`

- Git: `ignored` · `2.8 KB` · modified `2026-10-12 02:13 UTC`

```json
{
  "run_id": "2026-10-11_231339_836520_03_supervisionado_pilotos",
  "timestamp": {
    "utc": "2026-10-12T02:13:39Z",
    "local": "2026-10-11T23:13:39-0300"
  },
  "modelo": "03_supervisionado_pilotos",
  "seed": 42,
  "status": "success",
  "erro": null,
  "duracao_s": 7.0999376475811005e-06,
  "parametros": {
    "status_coorte": "provisoria",
    "versao_execucao": "piloto_v1",
    "split": "aleatorio_estratificado_por_alvo_ano_com_grupo",
    "teste_aberto": false
  },
  "dataset": {
    "n_rows": 3915132,
    "train_rows": 2740583,
    "valid_rows": 587262,
    "test_rows": 587287
  },
  "dataset_sha256": null,
  "data_version": "dados-v2",
  "features": {
    "n_features": 31,
    "usadas": [
      "idade_anos",
      "dias_sintomas_ate_internacao",
      "sexo_categoria",
      "cs_gestant",
      "cs_raca",
      "cs_zona",
      "ave_suino",
      "febre",
      "tosse",
      "garganta",
      "dispneia",
      "diarreia",
      "vomito",
      "dor_abd",
      "fadiga",
      "perd_olft",
      "perd_pala",
      "outro_sin",
      "puerpera",
      "cardiopati",
      "hematologi",
      "sind_down",
      "hepatica",
      "asma",
      "diabetes",
      "neurologic",
      "pneumopati",
      "imunodepre",
      "renal",
      "obesidade",
      "out_morbi"
    ],
    "features_final_congelada": false
  },
  "metricas": {
    "dummy_pr_auc": 0.21867922664841247,
    "logistica_pr_auc": 0.43942331586040556,
    "logistica_roc_auc": 0.7753013260187773,
    "logistica_brier": 0.19788284048088187
  },
  "gates": {
    "G1_definicao_alvo_features": "pendente",
    "G2_janela_temporal": "aprovado",
    "G3_validacao_coorte": "pendente",
    "G4_baseline": "pendente",
    "G5_pilotos": "pendente",
    "G6_finalistas_tuning": "pendente",
    "G7_calibracao": "pendente",
    "G8_limiar": "pendente",
    "G9_holdout": "pendente"
  },
  "notas": "Piloto provisório. Holdout não consultado. Sem tuning, calibração ou seleção de limiar.",
  "versoes": {
    "python": "3.14.7",
    "numpy": "2.5.3",
    "pandas": "3.0.6",
    "pyarrow": "25.0.1",
    "scikit-learn": "1.9.1",
    "scipy": "1.18.1",
    "matplotlib": "3.11.2",
    "seaborn": "0.13.2"
  },
  "git": {
    "commit": "b12e787837a83922a50ffa899be36ff84455715e",
    "branch": "main",
    "dirty": true
  },
  "env": {
    "python_executable": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\.venv\\Scripts\\python.exe",
    "python_version": "3.14.7",
    "platform": "Windows-11-10.0.22631-SP0",
    "cwd": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\notebooks\\02_eda",
    "ci": false
  },
  "supervised_yaml_sha256": "c359819b5c879f44d3157afe46104a434683e8a3685225c2dce1e5ff950a6d77"
}
```

### `outputs/runs/2026-10-11_231339_836520_03_supervisionado_pilotos/summary.txt`

- Git: `ignored` · `1.1 KB` · modified `2026-10-12 02:13 UTC`

```text
RUN_ID:   2026-10-11_231339_836520_03_supervisionado_pilotos
MODELO:   03_supervisionado_pilotos
SEED:     42
STATUS:   success
DADOS:    dados-v2
N_ROWS    3,915,132
TRAIN_ROWS 2,740,583
VALID_ROWS 587,262
TEST_ROWS 587,287
DURACAO:  0.0s

MÉTRICAS:
  dummy_pr_auc         0.2187
  logistica_pr_auc     0.4394
  logistica_roc_auc    0.7753
  logistica_brier      0.1979

PARÂMETROS:
  status_coorte        provisoria
  versao_execucao      piloto_v1
  split                aleatorio_estratificado_por_alvo_ano_com_grupo
  teste_aberto         False

GATES:
  G1_definicao_alvo_features         pendente
  G2_janela_temporal                 aprovado
  G3_validacao_coorte                pendente
  G4_baseline                        pendente
  G5_pilotos                         pendente
  G6_finalistas_tuning               pendente
  G7_calibracao                      pendente
  G8_limiar                          pendente
  G9_holdout                         pendente

NOTAS: Piloto provisório. Holdout não consultado. Sem tuning, calibração ou seleção de limiar.

TIMESTAMP_UTC: 2026-10-12T02:13:39Z
```

### `outputs/runs/2026-10-12_095946_799810_03_supervisionado_pilotos/metadata.json`

- Git: `ignored` · `2.8 KB` · modified `2026-10-12 12:59 UTC`

```json
{
  "run_id": "2026-10-12_095946_799810_03_supervisionado_pilotos",
  "timestamp": {
    "utc": "2026-10-12T12:59:46Z",
    "local": "2026-10-12T09:59:46-0300"
  },
  "modelo": "03_supervisionado_pilotos",
  "seed": 42,
  "status": "success",
  "erro": null,
  "duracao_s": 9.499955922365189e-06,
  "parametros": {
    "status_coorte": "provisoria",
    "versao_execucao": "piloto_v1",
    "split": "aleatorio_estratificado_por_alvo_ano_com_grupo",
    "teste_aberto": false
  },
  "dataset": {
    "n_rows": 3915132,
    "train_rows": 2740583,
    "valid_rows": 587262,
    "test_rows": 587287
  },
  "dataset_sha256": null,
  "data_version": "dados-v2",
  "features": {
    "n_features": 31,
    "usadas": [
      "idade_anos",
      "dias_sintomas_ate_internacao",
      "sexo_categoria",
      "cs_gestant",
      "cs_raca",
      "cs_zona",
      "ave_suino",
      "febre",
      "tosse",
      "garganta",
      "dispneia",
      "diarreia",
      "vomito",
      "dor_abd",
      "fadiga",
      "perd_olft",
      "perd_pala",
      "outro_sin",
      "puerpera",
      "cardiopati",
      "hematologi",
      "sind_down",
      "hepatica",
      "asma",
      "diabetes",
      "neurologic",
      "pneumopati",
      "imunodepre",
      "renal",
      "obesidade",
      "out_morbi"
    ],
    "features_final_congelada": false
  },
  "metricas": {
    "dummy_pr_auc": 0.21867922664841247,
    "logistica_pr_auc": 0.43942331586040556,
    "logistica_roc_auc": 0.7753013260187773,
    "logistica_brier": 0.19788284048088187
  },
  "gates": {
    "G1_definicao_alvo_features": "pendente",
    "G2_janela_temporal": "aprovado",
    "G4_baseline": "aprovado",
    "G5_pilotos": "aprovado",
    "G6_finalistas_tuning": "pendente",
    "G7_calibracao": "pendente",
    "G8_limiar": "pendente",
    "G9_holdout": "pendente"
  },
  "notas": "Piloto provisório. Holdout não consultado. Sem tuning, calibração ou seleção de limiar.",
  "versoes": {
    "python": "3.14.7",
    "numpy": "2.5.3",
    "pandas": "3.0.6",
    "pyarrow": "25.0.1",
    "scikit-learn": "1.9.1",
    "scipy": "1.18.1",
    "matplotlib": "3.11.2",
    "seaborn": "0.13.2"
  },
  "git": {
    "commit": "c8a9997c290da12199cb93e859f639bbfb3d2e74",
    "branch": "main",
    "dirty": true
  },
  "env": {
    "python_executable": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\.venv\\Scripts\\python.exe",
    "python_version": "3.14.7",
    "platform": "Windows-11-10.0.22631-SP0",
    "cwd": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\notebooks\\02_eda",
    "ci": false
  },
  "supervised_yaml_sha256": "f00fb401da7cf2e8e8ee7f1317e7f21f7040fbe255cfbc5288c56bbdbbd73e9e"
}
```

### `outputs/runs/2026-10-12_095946_799810_03_supervisionado_pilotos/summary.txt`

- Git: `ignored` · `1.1 KB` · modified `2026-10-12 12:59 UTC`

```text
RUN_ID:   2026-10-12_095946_799810_03_supervisionado_pilotos
MODELO:   03_supervisionado_pilotos
SEED:     42
STATUS:   success
DADOS:    dados-v2
N_ROWS    3,915,132
TRAIN_ROWS 2,740,583
VALID_ROWS 587,262
TEST_ROWS 587,287
DURACAO:  0.0s

MÉTRICAS:
  dummy_pr_auc         0.2187
  logistica_pr_auc     0.4394
  logistica_roc_auc    0.7753
  logistica_brier      0.1979

PARÂMETROS:
  status_coorte        provisoria
  versao_execucao      piloto_v1
  split                aleatorio_estratificado_por_alvo_ano_com_grupo
  teste_aberto         False

GATES:
  G1_definicao_alvo_features         pendente
  G2_janela_temporal                 aprovado
  G4_baseline                        aprovado
  G5_pilotos                         aprovado
  G6_finalistas_tuning               pendente
  G7_calibracao                      pendente
  G8_limiar                          pendente
  G9_holdout                         pendente

NOTAS: Piloto provisório. Holdout não consultado. Sem tuning, calibração ou seleção de limiar.

TIMESTAMP_UTC: 2026-10-12T12:59:46Z
```

### `outputs/runs/2026-10-14_000946_434671_03_supervisionado_pilotos/metadata.json`

- Git: `ignored` · `2.8 KB` · modified `2026-10-14 03:09 UTC`

```json
{
  "run_id": "2026-10-14_000946_434671_03_supervisionado_pilotos",
  "timestamp": {
    "utc": "2026-10-14T03:09:46Z",
    "local": "2026-10-14T00:09:46-0300"
  },
  "modelo": "03_supervisionado_pilotos",
  "seed": 42,
  "status": "success",
  "erro": null,
  "duracao_s": 0.00026490003801882267,
  "parametros": {
    "status_coorte": "provisoria",
    "versao_execucao": "piloto_v1",
    "split": "aleatorio_estratificado_por_alvo_ano_com_grupo",
    "teste_aberto": false
  },
  "dataset": {
    "n_rows": 3915132,
    "train_rows": 2740587,
    "valid_rows": 587271,
    "test_rows": 587274
  },
  "dataset_sha256": null,
  "data_version": "dados-v2",
  "features": {
    "n_features": 31,
    "usadas": [
      "idade_anos",
      "dias_sintomas_ate_internacao",
      "sexo_categoria",
      "cs_gestant",
      "cs_raca",
      "cs_zona",
      "ave_suino",
      "febre",
      "tosse",
      "garganta",
      "dispneia",
      "diarreia",
      "vomito",
      "dor_abd",
      "fadiga",
      "perd_olft",
      "perd_pala",
      "outro_sin",
      "puerpera",
      "cardiopati",
      "hematologi",
      "sind_down",
      "hepatica",
      "asma",
      "diabetes",
      "neurologic",
      "pneumopati",
      "imunodepre",
      "renal",
      "obesidade",
      "out_morbi"
    ],
    "features_final_congelada": false
  },
  "metricas": {
    "dummy_pr_auc": 0.21868609211079723,
    "logistica_pr_auc": 0.4407647509558362,
    "logistica_roc_auc": 0.7752527151170048,
    "logistica_brier": 0.19837290335933982
  },
  "gates": {
    "G1_definicao_alvo_features": "pendente",
    "G2_janela_temporal": "aprovado",
    "G4_baseline": "aprovado",
    "G5_pilotos": "aprovado",
    "G6_finalistas_tuning": "pendente",
    "G7_calibracao": "pendente",
    "G8_limiar": "pendente",
    "G9_holdout": "pendente"
  },
  "notas": "Piloto provisorio. Holdout nao consultado. Sem tuning, calibracao ou selecao de limiar.",
  "versoes": {
    "python": "3.14.7",
    "numpy": "2.5.3",
    "pandas": "3.0.6",
    "pyarrow": "25.0.1",
    "scikit-learn": "1.9.1",
    "scipy": "1.18.1",
    "matplotlib": "3.11.2",
    "seaborn": "0.13.2"
  },
  "git": {
    "commit": "1ff4fc8a619db2b0a5cd5ad237032979e17327bb",
    "branch": "main",
    "dirty": true
  },
  "env": {
    "python_executable": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\.venv\\Scripts\\python.exe",
    "python_version": "3.14.7",
    "platform": "Windows-11-10.0.22631-SP0",
    "cwd": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\notebooks\\02_eda",
    "ci": false
  },
  "supervised_yaml_sha256": "f2be64d77265c73c658864770f251ed5faee644274d1403067ec9c5f3daccb41"
}
```

### `outputs/runs/2026-10-14_000946_434671_03_supervisionado_pilotos/summary.txt`

- Git: `ignored` · `1.1 KB` · modified `2026-10-14 03:09 UTC`

```text
RUN_ID:   2026-10-14_000946_434671_03_supervisionado_pilotos
MODELO:   03_supervisionado_pilotos
SEED:     42
STATUS:   success
DADOS:    dados-v2
N_ROWS    3,915,132
TRAIN_ROWS 2,740,587
VALID_ROWS 587,271
TEST_ROWS 587,274
DURACAO:  0.0s

MÉTRICAS:
  dummy_pr_auc         0.2187
  logistica_pr_auc     0.4408
  logistica_roc_auc    0.7753
  logistica_brier      0.1984

PARÂMETROS:
  status_coorte        provisoria
  versao_execucao      piloto_v1
  split                aleatorio_estratificado_por_alvo_ano_com_grupo
  teste_aberto         False

GATES:
  G1_definicao_alvo_features         pendente
  G2_janela_temporal                 aprovado
  G4_baseline                        aprovado
  G5_pilotos                         aprovado
  G6_finalistas_tuning               pendente
  G7_calibracao                      pendente
  G8_limiar                          pendente
  G9_holdout                         pendente

NOTAS: Piloto provisorio. Holdout nao consultado. Sem tuning, calibracao ou selecao de limiar.

TIMESTAMP_UTC: 2026-10-14T03:09:46Z
```

### `outputs/runs/2026-10-14_204618_338775_03_supervisionado_pilotos/metadata.json`

- Git: `ignored` · `2.8 KB` · modified `2026-10-14 23:46 UTC`

```json
{
  "run_id": "2026-10-14_204618_338775_03_supervisionado_pilotos",
  "timestamp": {
    "utc": "2026-10-14T23:46:18Z",
    "local": "2026-10-14T20:46:18-0300"
  },
  "modelo": "03_supervisionado_pilotos",
  "seed": 42,
  "status": "success",
  "erro": null,
  "duracao_s": 8.819997310638428e-05,
  "parametros": {
    "status_coorte": "provisoria",
    "versao_execucao": "piloto_v1",
    "split": "aleatorio_estratificado_por_alvo_ano_com_grupo",
    "teste_aberto": false
  },
  "dataset": {
    "n_rows": 3915132,
    "train_rows": 2740587,
    "valid_rows": 587271,
    "test_rows": 587274
  },
  "dataset_sha256": null,
  "data_version": "dados-v2",
  "features": {
    "n_features": 31,
    "usadas": [
      "idade_anos",
      "dias_sintomas_ate_internacao",
      "sexo_categoria",
      "cs_gestant",
      "cs_raca",
      "cs_zona",
      "ave_suino",
      "febre",
      "tosse",
      "garganta",
      "dispneia",
      "diarreia",
      "vomito",
      "dor_abd",
      "fadiga",
      "perd_olft",
      "perd_pala",
      "outro_sin",
      "puerpera",
      "cardiopati",
      "hematologi",
      "sind_down",
      "hepatica",
      "asma",
      "diabetes",
      "neurologic",
      "pneumopati",
      "imunodepre",
      "renal",
      "obesidade",
      "out_morbi"
    ],
    "features_final_congelada": false
  },
  "metricas": {
    "dummy_pr_auc": 0.21868609211079723,
    "logistica_pr_auc": 0.4407647509558362,
    "logistica_roc_auc": 0.7752527151170048,
    "logistica_brier": 0.19837290335933982
  },
  "gates": {
    "G1_definicao_alvo_features": "pendente",
    "G2_janela_temporal": "aprovado",
    "G4_baseline": "aprovado",
    "G5_pilotos": "aprovado",
    "G6_finalistas_tuning": "pendente",
    "G7_calibracao": "pendente",
    "G8_limiar": "pendente",
    "G9_holdout": "pendente"
  },
  "notas": "Piloto provisorio. Holdout nao consultado. Sem tuning, calibracao ou selecao de limiar.",
  "versoes": {
    "python": "3.14.7",
    "numpy": "2.5.3",
    "pandas": "3.0.6",
    "pyarrow": "25.0.1",
    "scikit-learn": "1.9.1",
    "scipy": "1.18.1",
    "matplotlib": "3.11.2",
    "seaborn": "0.13.2"
  },
  "git": {
    "commit": "c4a1470aa7a47f4e3910adc9b7225c34f64e1e70",
    "branch": "main",
    "dirty": true
  },
  "env": {
    "python_executable": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\.venv\\Scripts\\python.exe",
    "python_version": "3.14.7",
    "platform": "Windows-11-10.0.22631-SP0",
    "cwd": "<HOME>\\OneDrive - Pfizer\\Documents\\GitHub\\Projeto_Integrador\\notebooks\\02_eda",
    "ci": false
  },
  "supervised_yaml_sha256": "ced8d5cad5268e995a8ba324b0ac3d094665bac9977b43c8a8ef806cc0d03cf8"
}
```

### `outputs/runs/2026-10-14_204618_338775_03_supervisionado_pilotos/summary.txt`

- Git: `ignored` · `1.1 KB` · modified `2026-10-14 23:46 UTC`

```text
RUN_ID:   2026-10-14_204618_338775_03_supervisionado_pilotos
MODELO:   03_supervisionado_pilotos
SEED:     42
STATUS:   success
DADOS:    dados-v2
N_ROWS    3,915,132
TRAIN_ROWS 2,740,587
VALID_ROWS 587,271
TEST_ROWS 587,274
DURACAO:  0.0s

MÉTRICAS:
  dummy_pr_auc         0.2187
  logistica_pr_auc     0.4408
  logistica_roc_auc    0.7753
  logistica_brier      0.1984

PARÂMETROS:
  status_coorte        provisoria
  versao_execucao      piloto_v1
  split                aleatorio_estratificado_por_alvo_ano_com_grupo
  teste_aberto         False

GATES:
  G1_definicao_alvo_features         pendente
  G2_janela_temporal                 aprovado
  G4_baseline                        aprovado
  G5_pilotos                         aprovado
  G6_finalistas_tuning               pendente
  G7_calibracao                      pendente
  G8_limiar                          pendente
  G9_holdout                         pendente

NOTAS: Piloto provisorio. Holdout nao consultado. Sem tuning, calibracao ou selecao de limiar.

TIMESTAMP_UTC: 2026-10-14T23:46:18Z
```

### `outputs/tables/03_cinco_familias_provisoria_20261012T022616Z_amostras.csv`

- Git: `ignored` · `211 B` · modified `2026-10-12 02:26 UTC` · 2 rows

```csv
particao,linhas_originais,linhas_piloto,prevalencia_original,prevalencia_piloto
treino,2740583,300000,0.2186852213561859,0.21868333333333334
validacao,587262,120000,0.21867922664841247,0.21868333333333334
```

### `outputs/tables/03_cinco_familias_provisoria_20261012T022616Z_manifesto.json`

- Git: `ignored` · `2.7 KB` · modified `2026-10-12 02:26 UTC`

```json
{
  "status_coorte": "provisoria",
  "versao_execucao": "piloto_v2_cinco_familias",
  "carater": "comparacao_provisoria_de_integracao",
  "seed": 42,
  "n_treino_piloto": 300000,
  "n_validacao_piloto": 120000,
  "features": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
    "puerpera",
    "cardiopati",
    "hematologi",
    "sind_down",
    "hepatica",
    "asma",
    "diabetes",
    "neurologic",
    "pneumopati",
    "imunodepre",
    "renal",
    "obesidade",
    "out_morbi"
  ],
  "modelos": [
    "dummy_prior_v2",
    "logistica_C1_v2",
    "arvore_rasa_v2",
    "random_forest_contida_v2",
    "hist_gradient_boosting_v2"
  ],
  "shortlist_provisoria": [
    "hist_gradient_boosting_v2",
    "logistica_C1_v2"
  ],
  "teste_aberto": false,
  "limiar_selecionado": false,
  "calibracao_aplicada": false,
  "tuning_realizado": false,
  "observacoes": [
    "Resultados dependem da coorte provisória.",
    "Amostras comparáveis foram usadas para controlar custo.",
    "A shortlist não congela finalistas.",
    "O teste permaneceu fechado.",
    "Calibração e limiar pertencem à próxima etapa."
  ],
  "artefatos": {
    "metricas": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T022616Z_metricas.csv",
    "metricas_por_ano": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T022616Z_metricas_por_ano.csv",
    "variacao_temporal": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T022616Z_variacao_temporal.csv",
    "amostras": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T022616Z_amostras.csv",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_cinco_familias_provisoria_20261012T022616Z_predicoes_validacao.parquet",
    "figura_curvas": "<REPO>\\reports\\figures\\supervisionado_03\\03_pilotos_curvas_pr_roc_calibracao.png",
    "figura_temporal": "<REPO>\\reports\\figures\\supervisionado_03\\03_pilotos_metricas_por_ano.png"
  }
}
```

### `outputs/tables/03_cinco_familias_provisoria_20261012T022616Z_metricas.csv`

- Git: `ignored` · `1.3 KB` · modified `2026-10-12 02:26 UTC` · 5 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,n_treino,duracao_fit_s,duracao_pred_s
0.78610522357088,0.4613001114076733,0.1955623845548722,0.5099550569792124,0.3701688846041283,0.8193735233595001,0.655625,0.5,120000,hist_gradient_boosting_v2,provisoria,piloto_v2_cinco_familias,300000,8.256994000053965,1.2180373000446707
0.7766099783482298,0.4417841314225881,0.19715853705227934,0.5050073674483654,0.37557578008915304,0.7705586464446308,0.6696666666666666,0.5,120000,logistica_C1_v2,provisoria,piloto_v2_cinco_familias,300000,7.147862800047733,2.1252258999738842
0.76861565019124,0.43319219477549786,0.20019895523930883,0.494446958883125,0.3554825037128506,0.811790259888728,0.636975,0.5,120000,random_forest_contida_v2,provisoria,piloto_v2_cinco_familias,300000,46.086997400037944,1.2600113999797031
0.7617160608193709,0.40728455571077143,0.20481653952151763,0.4902320513248163,0.3461025198210221,0.8400655437847725,0.6179416666666666,0.5,120000,arvore_rasa_v2,provisoria,piloto_v2_cinco_familias,300000,7.940202799974941,0.8916802000021562
0.5,0.21868333333333334,0.17086093305555553,0.0,0.0,0.0,0.7813166666666667,0.5,120000,dummy_prior_v2,provisoria,piloto_v2_cinco_familias,300000,3.299485000083223,1.062863599974662
```

### `outputs/tables/03_cinco_familias_provisoria_20261012T022616Z_metricas_por_ano.csv`

- Git: `ignored` · `5.2 KB` · modified `2026-10-12 02:26 UTC` · 40 rows

```csv
modelo,ano_internacao,n,positivos,prevalencia,pr_auc,roc_auc,brier,probabilidade_media
arvore_rasa_v2,2019,1333,160,0.12003000750187547,0.27737472101471217,0.7681852088661552,0.12954414650788715,0.23949372497234633
arvore_rasa_v2,2020,30032,8402,0.2797682472029835,0.46204353444260743,0.7299505005247745,0.23773609663640086,0.518321829786896
arvore_rasa_v2,2021,45369,12790,0.28191055566576295,0.4483744267523131,0.7140094789975968,0.2302788511782179,0.4966641925479579
arvore_rasa_v2,2022,14589,2649,0.18157515936664612,0.3518948208359657,0.7650213759118987,0.21104072104961347,0.42439999828331226
arvore_rasa_v2,2023,7378,706,0.09568988885876932,0.30397052180941103,0.8447818586490581,0.1373402525546229,0.27732819337428366
arvore_rasa_v2,2024,7033,586,0.08332148443054173,0.2505658053327788,0.8298825127542986,0.13229124508468842,0.26003378993627846
arvore_rasa_v2,2025,8886,650,0.07314877335133918,0.22594562783702532,0.826648858669257,0.1338003945232509,0.2586496242453462
arvore_rasa_v2,2026,5380,299,0.05557620817843866,0.18315878363905225,0.8293590325028846,0.11274472989648678,0.2195897214006603
dummy_prior_v2,2019,1333,160,0.12003000750187547,0.12003000750187547,0.5,0.11535528349858296,0.21868333333333334
dummy_prior_v2,2020,30032,8402,0.2797682472029835,0.2797682472029835,0.5,0.20522934176241636,0.21868333333333337
dummy_prior_v2,2021,45369,12790,0.28191055566576295,0.28191055566576295,0.5,0.20643467591385817,0.2186833333333334
dummy_prior_v2,2022,14589,2649,0.18157515936664612,0.18157515936664612,0.5,0.14998263744276508,0.21868333333333334
dummy_prior_v2,2023,7378,706,0.09568988885876932,0.09568988885876932,0.5,0.10166072141268336,0.2186833333333333
dummy_prior_v2,2024,7033,586,0.08332148443054173,0.08332148443054173,0.5,0.09470184480121491,0.21868333333333334
dummy_prior_v2,2025,8886,650,0.07314877335133918,0.07314877335133918,0.5,0.08897833845768624,0.21868333333333334
dummy_prior_v2,2026,5380,299,0.05557620817843866,0.05557620817843866,0.5,0.07909142753923998,0.2186833333333333
hist_gradient_boosting_v2,2019,1333,160,0.12003000750187547,0.30019106734763984,0.7887761082693947,0.13343271932108414,0.25408936855432096
hist_gradient_boosting_v2,2020,30032,8402,0.2797682472029835,0.513564896635687,0.758590941570722,0.23184032785504743,0.5195689558418913
hist_gradient_boosting_v2,2021,45369,12790,0.28191055566576295,0.4943006000217229,0.7388493024029806,0.21806759681874804,0.48068973345573024
hist_gradient_boosting_v2,2022,14589,2649,0.18157515936664612,0.41848426397018734,0.796459205553374,0.19963446669453896,0.4135152875244976
hist_gradient_boosting_v2,2023,7378,706,0.09568988885876932,0.3445968141030262,0.8577794987805789,0.1307166727352439,0.2690956384383633
hist_gradient_boosting_v2,2024,7033,586,0.08332148443054173,0.28939271725997945,0.850534365006133,0.12440206733595124,0.2507788363738982
hist_gradient_boosting_v2,2025,8886,650,0.07314877335133918,0.2522818688880946,0.8410329883812155,0.12552411946881167,0.24823191837117484
hist_gradient_boosting_v2,2026,5380,299,0.05557620817843866,0.2119003176841704,0.8509362376326258,0.10525295433015461,0.20967308079088848
logistica_C1_v2,2019,1333,160,0.12003000750187547,0.2694926891465062,0.7737825021312872,0.13459246107965342,0.27270410476504964
logistica_C1_v2,2020,30032,8402,0.2797682472029835,0.5046763341300456,0.752653755798407,0.22960917874617046,0.5158554414250798
logistica_C1_v2,2021,45369,12790,0.28191055566576295,0.48116482567497293,0.7295302132128889,0.21734862189921175,0.4761036043482677
logistica_C1_v2,2022,14589,2649,0.18157515936664612,0.3890711402032777,0.7849080876889797,0.20650515201756284,0.4289261896671037
logistica_C1_v2,2023,7378,706,0.09568988885876932,0.3343534722267585,0.850611154136181,0.13644891197117298,0.29460685646593465
logistica_C1_v2,2024,7033,586,0.08332148443054173,0.26808600506499275,0.8359572486819544,0.1312028661322752,0.27653700873714565
logistica_C1_v2,2025,8886,650,0.07314877335133918,0.24916350623804895,0.8357842679418688,0.13226669928182114,0.2758266207485521
logistica_C1_v2,2026,5380,299,0.05557620817843866,0.196244141248507,0.8382300379339648,0.11256595352600748,0.23949973283566506
random_forest_contida_v2,2019,1333,160,0.12003000750187547,0.2895065864745612,0.7754422421142371,0.1461234951789033,0.3347532679230221
random_forest_contida_v2,2020,30032,8402,0.2797682472029835,0.4781529511487426,0.7299327521802869,0.23513976149545623,0.5193181861875517
random_forest_contida_v2,2021,45369,12790,0.28191055566576295,0.46587376836437583,0.7168180186582487,0.2242974953186891,0.4912603622133061
random_forest_contida_v2,2022,14589,2649,0.18157515936664612,0.3859098265574093,0.7809732252555086,0.19757991816902387,0.43278305596955313
random_forest_contida_v2,2023,7378,706,0.09568988885876932,0.3277923343690909,0.8479996102268327,0.13806511042439823,0.3243400642135829
random_forest_contida_v2,2024,7033,586,0.08332148443054173,0.27920468615283467,0.8442116104482282,0.13122239292102064,0.30872240177361154
random_forest_contida_v2,2025,8886,650,0.07314877335133918,0.24296993362451258,0.8354937049351815,0.13074882028402598,0.3034677376183782
random_forest_contida_v2,2026,5380,299,0.05557620817843866,0.20378972591100886,0.8382932282969079,0.112520949807053,0.27180233714357155
```

### `outputs/tables/03_cinco_familias_provisoria_20261012T022616Z_variacao_temporal.csv`

- Git: `ignored` · `905 B` · modified `2026-10-12 02:26 UTC` · 4 rows

```csv
modelo,pr_auc_min,pr_auc_max,pr_auc_media,roc_auc_min,roc_auc_max,brier_min,brier_max,amplitude_pr_auc,amplitude_roc_auc
arvore_rasa_v2,0.18315878363905225,0.46204353444260743,0.3129160302079832,0.7140094789975968,0.8447818586490581,0.11274472989648678,0.23773609663640086,0.2788847508035552,0.13077237965146127
hist_gradient_boosting_v2,0.2119003176841704,0.513564896635687,0.3530890682388135,0.7388493024029806,0.8577794987805789,0.10525295433015461,0.23184032785504743,0.30166457895151666,0.11893019637759827
logistica_C1_v2,0.196244141248507,0.5046763341300456,0.3365315142416387,0.7295302132128889,0.850611154136181,0.11256595352600748,0.22960917874617046,0.30843219288153867,0.12108094092329214
random_forest_contida_v2,0.20378972591100886,0.4781529511487426,0.334149976575317,0.7168180186582487,0.8479996102268327,0.112520949807053,0.23513976149545623,0.27436322523773377,0.131181591568584
```

### `outputs/tables/03_cinco_familias_provisoria_20261012T130116Z_amostras.csv`

- Git: `ignored` · `211 B` · modified `2026-10-12 13:01 UTC` · 2 rows

```csv
particao,linhas_originais,linhas_piloto,prevalencia_original,prevalencia_piloto
treino,2740583,300000,0.2186852213561859,0.21868333333333334
validacao,587262,120000,0.21867922664841247,0.21868333333333334
```

### `outputs/tables/03_cinco_familias_provisoria_20261012T130116Z_manifesto.json`

- Git: `ignored` · `2.7 KB` · modified `2026-10-12 13:01 UTC`

```json
{
  "status_coorte": "provisoria",
  "versao_execucao": "piloto_v2_cinco_familias",
  "carater": "comparacao_provisoria_de_integracao",
  "seed": 42,
  "n_treino_piloto": 300000,
  "n_validacao_piloto": 120000,
  "features": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
    "puerpera",
    "cardiopati",
    "hematologi",
    "sind_down",
    "hepatica",
    "asma",
    "diabetes",
    "neurologic",
    "pneumopati",
    "imunodepre",
    "renal",
    "obesidade",
    "out_morbi"
  ],
  "modelos": [
    "dummy_prior_v2",
    "logistica_C1_v2",
    "arvore_rasa_v2",
    "random_forest_contida_v2",
    "hist_gradient_boosting_v2"
  ],
  "shortlist_provisoria": [
    "hist_gradient_boosting_v2",
    "logistica_C1_v2"
  ],
  "teste_aberto": false,
  "limiar_selecionado": false,
  "calibracao_aplicada": false,
  "tuning_realizado": false,
  "observacoes": [
    "Resultados dependem da coorte provisória.",
    "Amostras comparáveis foram usadas para controlar custo.",
    "A shortlist não congela finalistas.",
    "O teste permaneceu fechado.",
    "Calibração e limiar pertencem à próxima etapa."
  ],
  "artefatos": {
    "metricas": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_metricas.csv",
    "metricas_por_ano": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_metricas_por_ano.csv",
    "variacao_temporal": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_variacao_temporal.csv",
    "amostras": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_amostras.csv",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_cinco_familias_provisoria_20261012T130116Z_predicoes_validacao.parquet",
    "figura_curvas": "<REPO>\\reports\\figures\\supervisionado_03\\03_pilotos_curvas_pr_roc_calibracao.png",
    "figura_temporal": "<REPO>\\reports\\figures\\supervisionado_03\\03_pilotos_metricas_por_ano.png"
  }
}
```

### `outputs/tables/03_cinco_familias_provisoria_20261012T130116Z_metricas.csv`

- Git: `ignored` · `1.3 KB` · modified `2026-10-12 13:01 UTC` · 5 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,n_treino,duracao_fit_s,duracao_pred_s
0.78610522357088,0.4613001114076733,0.1955623845548722,0.5099550569792124,0.3701688846041283,0.8193735233595001,0.655625,0.5,120000,hist_gradient_boosting_v2,provisoria,piloto_v2_cinco_familias,300000,10.287957499967888,1.423935899976641
0.7766099783482298,0.4417841314225881,0.19715853705227934,0.5050073674483654,0.37557578008915304,0.7705586464446308,0.6696666666666666,0.5,120000,logistica_C1_v2,provisoria,piloto_v2_cinco_familias,300000,6.043404099997133,0.8790224000113085
0.76861565019124,0.43319219477549786,0.20019895523930883,0.494446958883125,0.3554825037128506,0.811790259888728,0.636975,0.5,120000,random_forest_contida_v2,provisoria,piloto_v2_cinco_familias,300000,48.15164270007517,1.2698520000558347
0.7617160608193709,0.40728455571077143,0.20481653952151763,0.4902320513248163,0.3461025198210221,0.8400655437847725,0.6179416666666666,0.5,120000,arvore_rasa_v2,provisoria,piloto_v2_cinco_familias,300000,8.021366199944168,1.0698978001018986
0.5,0.21868333333333334,0.17086093305555553,0.0,0.0,0.0,0.7813166666666667,0.5,120000,dummy_prior_v2,provisoria,piloto_v2_cinco_familias,300000,3.4979247000301257,0.9371980000287294
```

### `outputs/tables/03_cinco_familias_provisoria_20261012T130116Z_metricas_por_ano.csv`

- Git: `ignored` · `5.2 KB` · modified `2026-10-12 13:01 UTC` · 40 rows

```csv
modelo,ano_internacao,n,positivos,prevalencia,pr_auc,roc_auc,brier,probabilidade_media
arvore_rasa_v2,2019,1333,160,0.12003000750187547,0.27737472101471217,0.7681852088661552,0.12954414650788715,0.23949372497234633
arvore_rasa_v2,2020,30032,8402,0.2797682472029835,0.46204353444260743,0.7299505005247745,0.23773609663640086,0.518321829786896
arvore_rasa_v2,2021,45369,12790,0.28191055566576295,0.4483744267523131,0.7140094789975968,0.2302788511782179,0.4966641925479579
arvore_rasa_v2,2022,14589,2649,0.18157515936664612,0.3518948208359657,0.7650213759118987,0.21104072104961347,0.42439999828331226
arvore_rasa_v2,2023,7378,706,0.09568988885876932,0.30397052180941103,0.8447818586490581,0.1373402525546229,0.27732819337428366
arvore_rasa_v2,2024,7033,586,0.08332148443054173,0.2505658053327788,0.8298825127542986,0.13229124508468842,0.26003378993627846
arvore_rasa_v2,2025,8886,650,0.07314877335133918,0.22594562783702532,0.826648858669257,0.1338003945232509,0.2586496242453462
arvore_rasa_v2,2026,5380,299,0.05557620817843866,0.18315878363905225,0.8293590325028846,0.11274472989648678,0.2195897214006603
dummy_prior_v2,2019,1333,160,0.12003000750187547,0.12003000750187547,0.5,0.11535528349858296,0.21868333333333334
dummy_prior_v2,2020,30032,8402,0.2797682472029835,0.2797682472029835,0.5,0.20522934176241636,0.21868333333333337
dummy_prior_v2,2021,45369,12790,0.28191055566576295,0.28191055566576295,0.5,0.20643467591385817,0.2186833333333334
dummy_prior_v2,2022,14589,2649,0.18157515936664612,0.18157515936664612,0.5,0.14998263744276508,0.21868333333333334
dummy_prior_v2,2023,7378,706,0.09568988885876932,0.09568988885876932,0.5,0.10166072141268336,0.2186833333333333
dummy_prior_v2,2024,7033,586,0.08332148443054173,0.08332148443054173,0.5,0.09470184480121491,0.21868333333333334
dummy_prior_v2,2025,8886,650,0.07314877335133918,0.07314877335133918,0.5,0.08897833845768624,0.21868333333333334
dummy_prior_v2,2026,5380,299,0.05557620817843866,0.05557620817843866,0.5,0.07909142753923998,0.2186833333333333
hist_gradient_boosting_v2,2019,1333,160,0.12003000750187547,0.30019106734763984,0.7887761082693947,0.13343271932108414,0.25408936855432096
hist_gradient_boosting_v2,2020,30032,8402,0.2797682472029835,0.513564896635687,0.758590941570722,0.23184032785504743,0.5195689558418913
hist_gradient_boosting_v2,2021,45369,12790,0.28191055566576295,0.4943006000217229,0.7388493024029806,0.21806759681874804,0.48068973345573024
hist_gradient_boosting_v2,2022,14589,2649,0.18157515936664612,0.41848426397018734,0.796459205553374,0.19963446669453896,0.4135152875244976
hist_gradient_boosting_v2,2023,7378,706,0.09568988885876932,0.3445968141030262,0.8577794987805789,0.1307166727352439,0.2690956384383633
hist_gradient_boosting_v2,2024,7033,586,0.08332148443054173,0.28939271725997945,0.850534365006133,0.12440206733595124,0.2507788363738982
hist_gradient_boosting_v2,2025,8886,650,0.07314877335133918,0.2522818688880946,0.8410329883812155,0.12552411946881167,0.24823191837117484
hist_gradient_boosting_v2,2026,5380,299,0.05557620817843866,0.2119003176841704,0.8509362376326258,0.10525295433015461,0.20967308079088848
logistica_C1_v2,2019,1333,160,0.12003000750187547,0.2694926891465062,0.7737825021312872,0.13459246107965342,0.27270410476504964
logistica_C1_v2,2020,30032,8402,0.2797682472029835,0.5046763341300456,0.752653755798407,0.22960917874617046,0.5158554414250798
logistica_C1_v2,2021,45369,12790,0.28191055566576295,0.48116482567497293,0.7295302132128889,0.21734862189921175,0.4761036043482677
logistica_C1_v2,2022,14589,2649,0.18157515936664612,0.3890711402032777,0.7849080876889797,0.20650515201756284,0.4289261896671037
logistica_C1_v2,2023,7378,706,0.09568988885876932,0.3343534722267585,0.850611154136181,0.13644891197117298,0.29460685646593465
logistica_C1_v2,2024,7033,586,0.08332148443054173,0.26808600506499275,0.8359572486819544,0.1312028661322752,0.27653700873714565
logistica_C1_v2,2025,8886,650,0.07314877335133918,0.24916350623804895,0.8357842679418688,0.13226669928182114,0.2758266207485521
logistica_C1_v2,2026,5380,299,0.05557620817843866,0.196244141248507,0.8382300379339648,0.11256595352600748,0.23949973283566506
random_forest_contida_v2,2019,1333,160,0.12003000750187547,0.2895065864745612,0.7754422421142371,0.1461234951789033,0.3347532679230221
random_forest_contida_v2,2020,30032,8402,0.2797682472029835,0.4781529511487426,0.7299327521802869,0.23513976149545623,0.5193181861875517
random_forest_contida_v2,2021,45369,12790,0.28191055566576295,0.46587376836437583,0.7168180186582487,0.2242974953186891,0.4912603622133061
random_forest_contida_v2,2022,14589,2649,0.18157515936664612,0.3859098265574093,0.7809732252555086,0.19757991816902387,0.43278305596955324
random_forest_contida_v2,2023,7378,706,0.09568988885876932,0.3277923343690909,0.8479996102268327,0.1380651104243982,0.3243400642135829
random_forest_contida_v2,2024,7033,586,0.08332148443054173,0.27920468615283467,0.8442116104482282,0.13122239292102064,0.30872240177361154
random_forest_contida_v2,2025,8886,650,0.07314877335133918,0.24296993362451258,0.8354937049351815,0.13074882028402598,0.3034677376183782
random_forest_contida_v2,2026,5380,299,0.05557620817843866,0.20378972591100886,0.8382932282969079,0.11252094980705302,0.27180233714357155
```

### `outputs/tables/03_cinco_familias_provisoria_20261012T130116Z_variacao_temporal.csv`

- Git: `ignored` · `907 B` · modified `2026-10-12 13:01 UTC` · 4 rows

```csv
modelo,pr_auc_min,pr_auc_max,pr_auc_media,roc_auc_min,roc_auc_max,brier_min,brier_max,amplitude_pr_auc,amplitude_roc_auc
arvore_rasa_v2,0.18315878363905225,0.46204353444260743,0.3129160302079832,0.7140094789975968,0.8447818586490581,0.11274472989648678,0.23773609663640086,0.2788847508035552,0.13077237965146127
hist_gradient_boosting_v2,0.2119003176841704,0.513564896635687,0.3530890682388135,0.7388493024029806,0.8577794987805789,0.10525295433015461,0.23184032785504743,0.30166457895151666,0.11893019637759827
logistica_C1_v2,0.196244141248507,0.5046763341300456,0.3365315142416387,0.7295302132128889,0.850611154136181,0.11256595352600748,0.22960917874617046,0.30843219288153867,0.12108094092329214
random_forest_contida_v2,0.20378972591100886,0.4781529511487426,0.334149976575317,0.7168180186582487,0.8479996102268327,0.11252094980705302,0.23513976149545623,0.27436322523773377,0.131181591568584
```

### `outputs/tables/03_cinco_familias_provisoria_20261014T031127Z_amostras.csv`

- Git: `ignored` · `212 B` · modified `2026-10-14 03:11 UTC` · 2 rows

```csv
particao,linhas_originais,linhas_piloto,prevalencia_original,prevalencia_piloto
treino,2740587,300000,0.21868563194673257,0.21868333333333334
validacao,587271,120000,0.21868609211079723,0.21869166666666667
```

### `outputs/tables/03_cinco_familias_provisoria_20261014T031127Z_manifesto.json`

- Git: `ignored` · `2.7 KB` · modified `2026-10-14 03:11 UTC`

```json
{
  "status_coorte": "provisoria",
  "versao_execucao": "piloto_v2_cinco_familias",
  "carater": "comparacao_provisoria_de_integracao",
  "seed": 42,
  "n_treino_piloto": 300000,
  "n_validacao_piloto": 120000,
  "features": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
    "puerpera",
    "cardiopati",
    "hematologi",
    "sind_down",
    "hepatica",
    "asma",
    "diabetes",
    "neurologic",
    "pneumopati",
    "imunodepre",
    "renal",
    "obesidade",
    "out_morbi"
  ],
  "modelos": [
    "dummy_prior_v2",
    "logistica_C1_v2",
    "arvore_rasa_v2",
    "random_forest_contida_v2",
    "hist_gradient_boosting_v2"
  ],
  "shortlist_provisoria": [
    "hist_gradient_boosting_v2",
    "logistica_C1_v2"
  ],
  "teste_aberto": false,
  "limiar_selecionado": false,
  "calibracao_aplicada": false,
  "tuning_realizado": false,
  "observacoes": [
    "Resultados dependem da coorte provisória.",
    "Amostras comparáveis foram usadas para controlar custo.",
    "A shortlist não congela finalistas.",
    "O teste permaneceu fechado.",
    "Calibração e limiar pertencem à próxima etapa."
  ],
  "artefatos": {
    "metricas": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261014T031127Z_metricas.csv",
    "metricas_por_ano": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261014T031127Z_metricas_por_ano.csv",
    "variacao_temporal": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261014T031127Z_variacao_temporal.csv",
    "amostras": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261014T031127Z_amostras.csv",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_cinco_familias_provisoria_20261014T031127Z_predicoes_validacao.parquet",
    "figura_curvas": "<REPO>\\reports\\figures\\supervisionado_03\\03_pilotos_curvas_pr_roc_calibracao.png",
    "figura_temporal": "<REPO>\\reports\\figures\\supervisionado_03\\03_pilotos_metricas_por_ano.png"
  }
}
```

### `outputs/tables/03_cinco_familias_provisoria_20261014T031127Z_metricas.csv`

- Git: `ignored` · `1.3 KB` · modified `2026-10-14 03:11 UTC` · 5 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,n_treino,duracao_fit_s,duracao_pred_s
0.7837338025141412,0.4577975780425485,0.19719355553237866,0.5098122866894198,0.3699626769405411,0.8196471440003048,0.6553,0.5,120000,hist_gradient_boosting_v2,provisoria,piloto_v2_cinco_familias,300000,13.88727279996965,2.667994700022973
0.7742724458341613,0.43856004509006286,0.19910056824861047,0.5055658052772997,0.37446347995157564,0.7779217315093548,0.6672416666666666,0.5,120000,logistica_C1_v2,provisoria,piloto_v2_cinco_familias,300000,6.573903199983761,0.9535744999302551
0.7665168716317146,0.4299862045991363,0.20138297179217352,0.4940412952099404,0.354431428429407,0.8151126014556263,0.6348833333333334,0.5,120000,random_forest_contida_v2,provisoria,piloto_v2_cinco_familias,300000,47.386392700020224,1.7682791000697762
0.759284397951174,0.40228534443387626,0.2068909780780606,0.4922231331478124,0.3531146454605699,0.8121784856914225,0.6335416666666667,0.5,120000,arvore_rasa_v2,provisoria,piloto_v2_cinco_familias,300000,8.939963600016199,1.316284399945289
0.5,0.21869166666666667,0.17086562166666663,0.0,0.0,0.0,0.7813083333333334,0.5,120000,dummy_prior_v2,provisoria,piloto_v2_cinco_familias,300000,4.3938221000134945,0.957107099937275
```

### `outputs/tables/03_cinco_familias_provisoria_20261014T031127Z_metricas_por_ano.csv`

- Git: `ignored` · `5.2 KB` · modified `2026-10-14 03:11 UTC` · 40 rows

```csv
modelo,ano_internacao,n,positivos,prevalencia,pr_auc,roc_auc,brier,probabilidade_media
arvore_rasa_v2,2019,1355,163,0.12029520295202951,0.25618294661337704,0.7722315436241611,0.13273510512876757,0.25683723310132156
arvore_rasa_v2,2020,29987,8388,0.2797212125254277,0.44608515893392486,0.720250887315007,0.24177495708969896,0.5229989687720558
arvore_rasa_v2,2021,45324,12785,0.2820801341452652,0.43988752846501067,0.7106558775478871,0.2317449500902894,0.49832380157870104
arvore_rasa_v2,2022,14664,2659,0.18132842334969995,0.3603111099229618,0.7745634849713962,0.21051625880764274,0.42780471751149857
arvore_rasa_v2,2023,7363,724,0.09832948526415863,0.2982065466728109,0.8294313320168201,0.14307735417577414,0.2829710385148049
arvore_rasa_v2,2024,7015,585,0.08339272986457591,0.261546747130475,0.8376020523454427,0.13589515715614278,0.2697817184015538
arvore_rasa_v2,2025,8900,651,0.07314606741573033,0.2247244113330193,0.8265799196625612,0.1327358231436628,0.2584164339395812
arvore_rasa_v2,2026,5392,288,0.05341246290801187,0.17873622364881353,0.83846207223093,0.11465230237319544,0.22582339678675914
dummy_prior_v2,2019,1355,163,0.12029520295202951,0.12029520295202951,0.5,0.11550449129868798,0.21868333333333334
dummy_prior_v2,2020,29987,8388,0.2797212125254277,0.2797212125254277,0.5,0.20520287848500085,0.21868333333333334
dummy_prior_v2,2021,45324,12785,0.2820801341452652,0.2820801341452652,0.5,0.2065300864190421,0.21868333333333337
dummy_prior_v2,2022,14664,2659,0.18132842334969995,0.18132842334969995,0.5,0.1498438155350973,0.21868333333333334
dummy_prior_v2,2023,7363,724,0.09832948526415863,0.09832948526415863,0.5,0.10314584633690223,0.21868333333333334
dummy_prior_v2,2024,7015,585,0.08339272986457591,0.08339272986457591,0.5,0.09474192985725033,0.21868333333333334
dummy_prior_v2,2025,8900,651,0.07314606741573033,0.07314606741573033,0.5,0.08897681600811484,0.21868333333333334
dummy_prior_v2,2026,5392,288,0.05341246290801187,0.05341246290801187,0.5,0.07787403232525551,0.2186833333333333
hist_gradient_boosting_v2,2019,1355,163,0.12029520295202951,0.28745930015036397,0.7921367398196566,0.13406375508538068,0.26120407564571707
hist_gradient_boosting_v2,2020,29987,8388,0.2797212125254277,0.510874944902731,0.7539260116490583,0.2337380637317967,0.5212712594470571
hist_gradient_boosting_v2,2021,45324,12785,0.2820801341452652,0.48808251430763916,0.7373332392813592,0.21899203197293501,0.4826943399848201
hist_gradient_boosting_v2,2022,14664,2659,0.18132842334969995,0.4150340682318508,0.7968962255447343,0.20103156704927577,0.41749244464931884
hist_gradient_boosting_v2,2023,7363,724,0.09832948526415863,0.3679242282970099,0.8483983392959233,0.1351947036478361,0.27382611447688543
hist_gradient_boosting_v2,2024,7015,585,0.08339272986457591,0.3117292798082803,0.8570197126184684,0.12791145133160842,0.2595455633776146
hist_gradient_boosting_v2,2025,8900,651,0.07314606741573033,0.25062632936211743,0.8409368244421564,0.12607691261330622,0.2495485096608725
hist_gradient_boosting_v2,2026,5392,288,0.05341246290801187,0.19735505575855672,0.8578361742424242,0.10833146252945079,0.21707997489681424
logistica_C1_v2,2019,1355,163,0.12029520295202951,0.27886648420402027,0.777995944332359,0.13779899060352996,0.28052390755888873
logistica_C1_v2,2020,29987,8388,0.2797212125254277,0.49627806440291294,0.7454688769060491,0.23313232567214978,0.518726405601904
logistica_C1_v2,2021,45324,12785,0.2820801341452652,0.47829952070053683,0.7289671034390512,0.21809318472711914,0.47716017171172576
logistica_C1_v2,2022,14664,2659,0.18132842334969995,0.4002593509577733,0.7912969226342478,0.2068711246693542,0.4328685933134279
logistica_C1_v2,2023,7363,724,0.09832948526415863,0.3358602768626264,0.8418912936199038,0.14186083158917648,0.29932086022575843
logistica_C1_v2,2024,7015,585,0.08339272986457591,0.2773719795919383,0.8435433531389985,0.13530229834466362,0.2859023462082121
logistica_C1_v2,2025,8900,651,0.07314606741573033,0.2389680618999371,0.830904327834552,0.13274754432959163,0.2751367422542223
logistica_C1_v2,2026,5392,288,0.05341246290801187,0.18301817544279506,0.845789522378962,0.11514795261481299,0.2448978904179417
random_forest_contida_v2,2019,1355,163,0.12029520295202951,0.30895800640178117,0.7924429736072796,0.14754883625126058,0.3418388212678265
random_forest_contida_v2,2020,29987,8388,0.2797212125254277,0.4749971817717371,0.7273694186949391,0.23643266359095655,0.5209719249838256
random_forest_contida_v2,2021,45324,12785,0.2820801341452652,0.46129484831425405,0.7161846697293173,0.22442010867181497,0.49154709471432123
random_forest_contida_v2,2022,14664,2659,0.18132842334969995,0.38258765054187344,0.7798093561053836,0.19946632636017927,0.43607756344093007
random_forest_contida_v2,2023,7363,724,0.09832948526415863,0.3160220767092553,0.8320679993242677,0.14260424667953248,0.32754202259906146
random_forest_contida_v2,2024,7015,585,0.08339272986457591,0.299455308465333,0.8461763102976166,0.13410453818733847,0.3145085245659218
random_forest_contida_v2,2025,8900,651,0.07314606741573033,0.2408759653413334,0.8327555972431794,0.131331408138215,0.3041290265394911
random_forest_contida_v2,2026,5392,288,0.05341246290801187,0.20399440218689455,0.8541309512147335,0.11497450065572155,0.2781408670049724
```

### `outputs/tables/03_cinco_familias_provisoria_20261014T031127Z_variacao_temporal.csv`

- Git: `ignored` · `912 B` · modified `2026-10-14 03:11 UTC` · 4 rows

```csv
modelo,pr_auc_min,pr_auc_max,pr_auc_media,roc_auc_min,roc_auc_max,brier_min,brier_max,amplitude_pr_auc,amplitude_roc_auc
arvore_rasa_v2,0.17873622364881353,0.44608515893392486,0.30821008409004913,0.7106558775478871,0.83846207223093,0.11465230237319544,0.24177495708969896,0.26734893528511133,0.12780619468304288
hist_gradient_boosting_v2,0.19735505575855672,0.510874944902731,0.35363571510231867,0.7373332392813592,0.8578361742424242,0.10833146252945079,0.2337380637317967,0.3135198891441743,0.12050293496106501
logistica_C1_v2,0.18301817544279506,0.49627806440291294,0.3361152392578175,0.7289671034390512,0.845789522378962,0.11514795261481299,0.23313232567214978,0.3132598889601179,0.11682241893991074
random_forest_contida_v2,0.20399440218689455,0.4749971817717371,0.33602317996655773,0.7161846697293173,0.8541309512147335,0.11497450065572155,0.23643266359095655,0.27100277958484253,0.1379462814854162
```

### `outputs/tables/03_cinco_familias_provisoria_20261014T234809Z_amostras.csv`

- Git: `ignored` · `212 B` · modified `2026-10-14 23:48 UTC` · 2 rows

```csv
particao,linhas_originais,linhas_piloto,prevalencia_original,prevalencia_piloto
treino,2740587,300000,0.21868563194673257,0.21868333333333334
validacao,587271,120000,0.21868609211079723,0.21869166666666667
```

### `outputs/tables/03_cinco_familias_provisoria_20261014T234809Z_manifesto.json`

- Git: `ignored` · `2.7 KB` · modified `2026-10-14 23:48 UTC`

```json
{
  "status_coorte": "provisoria",
  "versao_execucao": "piloto_v2_cinco_familias",
  "carater": "comparacao_provisoria_de_integracao",
  "seed": 42,
  "n_treino_piloto": 300000,
  "n_validacao_piloto": 120000,
  "features": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
    "puerpera",
    "cardiopati",
    "hematologi",
    "sind_down",
    "hepatica",
    "asma",
    "diabetes",
    "neurologic",
    "pneumopati",
    "imunodepre",
    "renal",
    "obesidade",
    "out_morbi"
  ],
  "modelos": [
    "dummy_prior_v2",
    "logistica_C1_v2",
    "arvore_rasa_v2",
    "random_forest_contida_v2",
    "hist_gradient_boosting_v2"
  ],
  "shortlist_provisoria": [
    "hist_gradient_boosting_v2",
    "logistica_C1_v2"
  ],
  "teste_aberto": false,
  "limiar_selecionado": false,
  "calibracao_aplicada": false,
  "tuning_realizado": false,
  "observacoes": [
    "Resultados dependem da coorte provisória.",
    "Amostras comparáveis foram usadas para controlar custo.",
    "A shortlist não congela finalistas.",
    "O teste permaneceu fechado.",
    "Calibração e limiar pertencem à próxima etapa."
  ],
  "artefatos": {
    "metricas": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261014T234809Z_metricas.csv",
    "metricas_por_ano": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261014T234809Z_metricas_por_ano.csv",
    "variacao_temporal": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261014T234809Z_variacao_temporal.csv",
    "amostras": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261014T234809Z_amostras.csv",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_cinco_familias_provisoria_20261014T234809Z_predicoes_validacao.parquet",
    "figura_curvas": "<REPO>\\reports\\figures\\supervisionado_03\\03_pilotos_curvas_pr_roc_calibracao.png",
    "figura_temporal": "<REPO>\\reports\\figures\\supervisionado_03\\03_pilotos_metricas_por_ano.png"
  }
}
```

### `outputs/tables/03_cinco_familias_provisoria_20261014T234809Z_metricas.csv`

- Git: `ignored` · `1.3 KB` · modified `2026-10-14 23:48 UTC` · 5 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,n_treino,duracao_fit_s,duracao_pred_s
0.7837338025141412,0.4577975780425485,0.19719355553237866,0.5098122866894198,0.3699626769405411,0.8196471440003048,0.6553,0.5,120000,hist_gradient_boosting_v2,provisoria,piloto_v2_cinco_familias,300000,13.10794989997521,1.6257725999457762
0.7742724458341613,0.43856004509006286,0.19910056824861047,0.5055658052772997,0.37446347995157564,0.7779217315093548,0.6672416666666666,0.5,120000,logistica_C1_v2,provisoria,piloto_v2_cinco_familias,300000,6.443985000019893,1.0642294000135735
0.7665168716317146,0.4299862045991363,0.20138297179217352,0.4940412952099404,0.354431428429407,0.8151126014556263,0.6348833333333334,0.5,120000,random_forest_contida_v2,provisoria,piloto_v2_cinco_familias,300000,58.38709880004171,2.2917184999678284
0.759284397951174,0.40228534443387626,0.2068909780780606,0.4922231331478124,0.3531146454605699,0.8121784856914225,0.6335416666666667,0.5,120000,arvore_rasa_v2,provisoria,piloto_v2_cinco_familias,300000,7.5551238000625744,1.02772189991083
0.5,0.21869166666666667,0.17086562166666663,0.0,0.0,0.0,0.7813083333333334,0.5,120000,dummy_prior_v2,provisoria,piloto_v2_cinco_familias,300000,4.861158599960618,1.2276639000046998
```

### `outputs/tables/03_cinco_familias_provisoria_20261014T234809Z_metricas_por_ano.csv`

- Git: `ignored` · `5.2 KB` · modified `2026-10-14 23:48 UTC` · 40 rows

```csv
modelo,ano_internacao,n,positivos,prevalencia,pr_auc,roc_auc,brier,probabilidade_media
arvore_rasa_v2,2019,1355,163,0.12029520295202951,0.25618294661337704,0.7722315436241611,0.13273510512876757,0.25683723310132156
arvore_rasa_v2,2020,29987,8388,0.2797212125254277,0.44608515893392486,0.720250887315007,0.24177495708969896,0.5229989687720558
arvore_rasa_v2,2021,45324,12785,0.2820801341452652,0.43988752846501067,0.7106558775478871,0.2317449500902894,0.49832380157870104
arvore_rasa_v2,2022,14664,2659,0.18132842334969995,0.3603111099229618,0.7745634849713962,0.21051625880764274,0.42780471751149857
arvore_rasa_v2,2023,7363,724,0.09832948526415863,0.2982065466728109,0.8294313320168201,0.14307735417577414,0.2829710385148049
arvore_rasa_v2,2024,7015,585,0.08339272986457591,0.261546747130475,0.8376020523454427,0.13589515715614278,0.2697817184015538
arvore_rasa_v2,2025,8900,651,0.07314606741573033,0.2247244113330193,0.8265799196625612,0.1327358231436628,0.2584164339395812
arvore_rasa_v2,2026,5392,288,0.05341246290801187,0.17873622364881353,0.83846207223093,0.11465230237319544,0.22582339678675914
dummy_prior_v2,2019,1355,163,0.12029520295202951,0.12029520295202951,0.5,0.11550449129868798,0.21868333333333334
dummy_prior_v2,2020,29987,8388,0.2797212125254277,0.2797212125254277,0.5,0.20520287848500085,0.21868333333333334
dummy_prior_v2,2021,45324,12785,0.2820801341452652,0.2820801341452652,0.5,0.2065300864190421,0.21868333333333337
dummy_prior_v2,2022,14664,2659,0.18132842334969995,0.18132842334969995,0.5,0.1498438155350973,0.21868333333333334
dummy_prior_v2,2023,7363,724,0.09832948526415863,0.09832948526415863,0.5,0.10314584633690223,0.21868333333333334
dummy_prior_v2,2024,7015,585,0.08339272986457591,0.08339272986457591,0.5,0.09474192985725033,0.21868333333333334
dummy_prior_v2,2025,8900,651,0.07314606741573033,0.07314606741573033,0.5,0.08897681600811484,0.21868333333333334
dummy_prior_v2,2026,5392,288,0.05341246290801187,0.05341246290801187,0.5,0.07787403232525551,0.2186833333333333
hist_gradient_boosting_v2,2019,1355,163,0.12029520295202951,0.28745930015036397,0.7921367398196566,0.13406375508538068,0.26120407564571707
hist_gradient_boosting_v2,2020,29987,8388,0.2797212125254277,0.510874944902731,0.7539260116490583,0.2337380637317967,0.5212712594470571
hist_gradient_boosting_v2,2021,45324,12785,0.2820801341452652,0.48808251430763916,0.7373332392813592,0.21899203197293501,0.4826943399848201
hist_gradient_boosting_v2,2022,14664,2659,0.18132842334969995,0.4150340682318508,0.7968962255447343,0.20103156704927577,0.41749244464931884
hist_gradient_boosting_v2,2023,7363,724,0.09832948526415863,0.3679242282970099,0.8483983392959233,0.1351947036478361,0.27382611447688543
hist_gradient_boosting_v2,2024,7015,585,0.08339272986457591,0.3117292798082803,0.8570197126184684,0.12791145133160842,0.2595455633776146
hist_gradient_boosting_v2,2025,8900,651,0.07314606741573033,0.25062632936211743,0.8409368244421564,0.12607691261330622,0.2495485096608725
hist_gradient_boosting_v2,2026,5392,288,0.05341246290801187,0.19735505575855672,0.8578361742424242,0.10833146252945079,0.21707997489681424
logistica_C1_v2,2019,1355,163,0.12029520295202951,0.27886648420402027,0.777995944332359,0.13779899060352996,0.28052390755888873
logistica_C1_v2,2020,29987,8388,0.2797212125254277,0.49627806440291294,0.7454688769060491,0.23313232567214978,0.518726405601904
logistica_C1_v2,2021,45324,12785,0.2820801341452652,0.47829952070053683,0.7289671034390512,0.21809318472711914,0.47716017171172576
logistica_C1_v2,2022,14664,2659,0.18132842334969995,0.4002593509577733,0.7912969226342478,0.2068711246693542,0.4328685933134279
logistica_C1_v2,2023,7363,724,0.09832948526415863,0.3358602768626264,0.8418912936199038,0.14186083158917648,0.29932086022575843
logistica_C1_v2,2024,7015,585,0.08339272986457591,0.2773719795919383,0.8435433531389985,0.13530229834466362,0.2859023462082121
logistica_C1_v2,2025,8900,651,0.07314606741573033,0.2389680618999371,0.830904327834552,0.13274754432959163,0.2751367422542223
logistica_C1_v2,2026,5392,288,0.05341246290801187,0.18301817544279506,0.845789522378962,0.11514795261481299,0.2448978904179417
random_forest_contida_v2,2019,1355,163,0.12029520295202951,0.30895800640178117,0.7924429736072796,0.14754883625126058,0.3418388212678265
random_forest_contida_v2,2020,29987,8388,0.2797212125254277,0.4749971817717371,0.7273694186949391,0.23643266359095655,0.5209719249838256
random_forest_contida_v2,2021,45324,12785,0.2820801341452652,0.46129484831425405,0.7161846697293173,0.22442010867181497,0.49154709471432123
random_forest_contida_v2,2022,14664,2659,0.18132842334969995,0.38258765054187344,0.7798093561053836,0.19946632636017927,0.43607756344093007
random_forest_contida_v2,2023,7363,724,0.09832948526415863,0.3160220767092553,0.8320679993242677,0.14260424667953248,0.32754202259906146
random_forest_contida_v2,2024,7015,585,0.08339272986457591,0.299455308465333,0.8461763102976166,0.13410453818733847,0.3145085245659219
random_forest_contida_v2,2025,8900,651,0.07314606741573033,0.2408759653413334,0.8327555972431794,0.131331408138215,0.3041290265394911
random_forest_contida_v2,2026,5392,288,0.05341246290801187,0.20399440218689455,0.8541309512147335,0.11497450065572158,0.2781408670049724
```

### `outputs/tables/03_cinco_familias_provisoria_20261014T234809Z_variacao_temporal.csv`

- Git: `ignored` · `912 B` · modified `2026-10-14 23:48 UTC` · 4 rows

```csv
modelo,pr_auc_min,pr_auc_max,pr_auc_media,roc_auc_min,roc_auc_max,brier_min,brier_max,amplitude_pr_auc,amplitude_roc_auc
arvore_rasa_v2,0.17873622364881353,0.44608515893392486,0.30821008409004913,0.7106558775478871,0.83846207223093,0.11465230237319544,0.24177495708969896,0.26734893528511133,0.12780619468304288
hist_gradient_boosting_v2,0.19735505575855672,0.510874944902731,0.35363571510231867,0.7373332392813592,0.8578361742424242,0.10833146252945079,0.2337380637317967,0.3135198891441743,0.12050293496106501
logistica_C1_v2,0.18301817544279506,0.49627806440291294,0.3361152392578175,0.7289671034390512,0.845789522378962,0.11514795261481299,0.23313232567214978,0.3132598889601179,0.11682241893991074
random_forest_contida_v2,0.20399440218689455,0.4749971817717371,0.33602317996655773,0.7161846697293173,0.8541309512147335,0.11497450065572158,0.23643266359095655,0.27100277958484253,0.1379462814854162
```

### `outputs/tables/03_pilotos_provisional_20261012T124857Z_contrato.csv`

- Git: `ignored` · `213 B` · modified `2026-10-12 12:48 UTC` · 8 rows

```csv
item,resultado
coorte_nao_vazia,True
dt_interna_disponivel,True
dt_interna_sem_nulos,True
ano_disponivel,True
alvo_disponivel,True
alvo_binario,True
features_sem_proibidas,True
features_presentes,True
```

### `outputs/tables/03_pilotos_provisional_20261012T124857Z_manifesto.json`

- Git: `ignored` · `1.7 KB` · modified `2026-10-12 12:48 UTC`

```json
{
  "status_coorte": "provisional",
  "versao_execucao": "piloto_v1",
  "fonte": "<REPO>\\data\\analytical\\coorte_provisoria_b.parquet",
  "seed": 42,
  "features": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
    "puerpera",
    "cardiopati",
    "hematologi",
    "sind_down",
    "hepatica",
    "asma",
    "diabetes",
    "neurologic",
    "pneumopati",
    "imunodepre",
    "renal",
    "obesidade",
    "out_morbi"
  ],
  "features_final_congelada": false,
  "n_base_modelagem": 3915132,
  "n_treino": 2740583,
  "n_validacao": 587262,
  "n_teste_criado_mas_nao_aberto": 587287,
  "artefatos": {
    "contrato": "<REPO>\\outputs\\tables\\03_pilotos_provisional_20261012T124857Z_contrato.csv",
    "particoes": "<REPO>\\outputs\\tables\\03_pilotos_provisional_20261012T124857Z_particoes.csv",
    "metricas_validacao": "<REPO>\\outputs\\tables\\03_pilotos_provisional_20261012T124857Z_metricas_validacao.csv",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_pilotos_provisional_20261012T124857Z_predicoes_validacao.parquet"
  }
}
```

### `outputs/tables/03_pilotos_provisional_20261012T124857Z_metricas_validacao.csv`

- Git: `ignored` · `540 B` · modified `2026-10-12 12:48 UTC` · 2 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_apenas_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,duracao_fit_s,duracao_pred_s
0.7753013260187773,0.43942331586040556,0.19788284048088187,0.5058403237149759,0.3759421563354569,0.7728971671520456,0.6697726057534797,0.5,587262,logistica_piloto_C1,provisoria,piloto_v1,46.745055399951525,4.407911600079387
0.5,0.21867922664841247,0.17085862251680126,0.0,0.0,0.0,0.7813207733515876,0.5,587262,dummy_prior,provisoria,piloto_v1,31.225839799968526,4.341758299968205
```

### `outputs/tables/03_pilotos_provisional_20261012T124857Z_particoes.csv`

- Git: `ignored` · `312 B` · modified `2026-10-12 12:48 UTC` · 3 rows

```csv
particao,n,positivos,prevalencia,ano_minimo,ano_maximo,grupos,percentual
teste,587287,128436,0.2186937562043771,2019,2026,587286,15.000439321075254
treino,2740583,599325,0.2186852213561859,2019,2026,2740574,69.99975990592398
validacao,587262,128422,0.21867922664841247,2019,2026,587259,14.999800773000757
```

### `outputs/tables/03_pilotos_provisoria_20261012T021331Z_contrato.csv`

- Git: `ignored` · `213 B` · modified `2026-10-12 02:13 UTC` · 8 rows

```csv
item,resultado
coorte_nao_vazia,True
dt_interna_disponivel,True
dt_interna_sem_nulos,True
ano_disponivel,True
alvo_disponivel,True
alvo_binario,True
features_sem_proibidas,True
features_presentes,True
```

### `outputs/tables/03_pilotos_provisoria_20261012T021331Z_manifesto.json`

- Git: `ignored` · `1.7 KB` · modified `2026-10-12 02:13 UTC`

```json
{
  "status_coorte": "provisoria",
  "versao_execucao": "piloto_v1",
  "fonte": "<REPO>\\data\\analytical\\coorte_provisoria_b.parquet",
  "seed": 42,
  "features": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
    "puerpera",
    "cardiopati",
    "hematologi",
    "sind_down",
    "hepatica",
    "asma",
    "diabetes",
    "neurologic",
    "pneumopati",
    "imunodepre",
    "renal",
    "obesidade",
    "out_morbi"
  ],
  "features_final_congelada": false,
  "n_base_modelagem": 3915132,
  "n_treino": 2740583,
  "n_validacao": 587262,
  "n_teste_criado_mas_nao_aberto": 587287,
  "artefatos": {
    "contrato": "<REPO>\\outputs\\tables\\03_pilotos_provisoria_20261012T021331Z_contrato.csv",
    "particoes": "<REPO>\\outputs\\tables\\03_pilotos_provisoria_20261012T021331Z_particoes.csv",
    "metricas_validacao": "<REPO>\\outputs\\tables\\03_pilotos_provisoria_20261012T021331Z_metricas_validacao.csv",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_pilotos_provisoria_20261012T021331Z_predicoes_validacao.parquet"
  }
}
```

### `outputs/tables/03_pilotos_provisoria_20261012T021331Z_metricas_validacao.csv`

- Git: `ignored` · `540 B` · modified `2026-10-12 02:13 UTC` · 2 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_apenas_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,duracao_fit_s,duracao_pred_s
0.7753013260187773,0.43942331586040556,0.19788284048088187,0.5058403237149759,0.3759421563354569,0.7728971671520456,0.6697726057534797,0.5,587262,logistica_piloto_C1,provisoria,piloto_v1,46.745055399951525,4.407911600079387
0.5,0.21867922664841247,0.17085862251680126,0.0,0.0,0.0,0.7813207733515876,0.5,587262,dummy_prior,provisoria,piloto_v1,31.225839799968526,4.341758299968205
```

### `outputs/tables/03_pilotos_provisoria_20261012T021331Z_particoes.csv`

- Git: `ignored` · `312 B` · modified `2026-10-12 02:13 UTC` · 3 rows

```csv
particao,n,positivos,prevalencia,ano_minimo,ano_maximo,grupos,percentual
teste,587287,128436,0.2186937562043771,2019,2026,587286,15.000439321075254
treino,2740583,599325,0.2186852213561859,2019,2026,2740574,69.99975990592398
validacao,587262,128422,0.21867922664841247,2019,2026,587259,14.999800773000757
```

### `outputs/tables/03_pilotos_provisoria_20261012T125945Z_contrato.csv`

- Git: `ignored` · `213 B` · modified `2026-10-12 12:59 UTC` · 8 rows

```csv
item,resultado
coorte_nao_vazia,True
dt_interna_disponivel,True
dt_interna_sem_nulos,True
ano_disponivel,True
alvo_disponivel,True
alvo_binario,True
features_sem_proibidas,True
features_presentes,True
```

### `outputs/tables/03_pilotos_provisoria_20261012T125945Z_manifesto.json`

- Git: `ignored` · `1.7 KB` · modified `2026-10-12 12:59 UTC`

```json
{
  "status_coorte": "provisoria",
  "versao_execucao": "piloto_v1",
  "fonte": "<REPO>\\data\\analytical\\coorte_provisoria_b.parquet",
  "seed": 42,
  "features": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
    "puerpera",
    "cardiopati",
    "hematologi",
    "sind_down",
    "hepatica",
    "asma",
    "diabetes",
    "neurologic",
    "pneumopati",
    "imunodepre",
    "renal",
    "obesidade",
    "out_morbi"
  ],
  "features_final_congelada": false,
  "n_base_modelagem": 3915132,
  "n_treino": 2740583,
  "n_validacao": 587262,
  "n_teste_criado_mas_nao_aberto": 587287,
  "artefatos": {
    "contrato": "<REPO>\\outputs\\tables\\03_pilotos_provisoria_20261012T125945Z_contrato.csv",
    "particoes": "<REPO>\\outputs\\tables\\03_pilotos_provisoria_20261012T125945Z_particoes.csv",
    "metricas_validacao": "<REPO>\\outputs\\tables\\03_pilotos_provisoria_20261012T125945Z_metricas_validacao.csv",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_pilotos_provisoria_20261012T125945Z_predicoes_validacao.parquet"
  }
}
```

### `outputs/tables/03_pilotos_provisoria_20261012T125945Z_metricas_validacao.csv`

- Git: `ignored` · `537 B` · modified `2026-10-12 12:59 UTC` · 2 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_apenas_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,duracao_fit_s,duracao_pred_s
0.7753013260187773,0.43942331586040556,0.19788284048088187,0.5058403237149759,0.3759421563354569,0.7728971671520456,0.6697726057534797,0.5,587262,logistica_piloto_C1,provisoria,piloto_v1,51.10458749998361,4.318254200043157
0.5,0.21867922664841247,0.17085862251680126,0.0,0.0,0.0,0.7813207733515876,0.5,587262,dummy_prior,provisoria,piloto_v1,37.4147043999983,5.133523200056516
```

### `outputs/tables/03_pilotos_provisoria_20261012T125945Z_particoes.csv`

- Git: `ignored` · `312 B` · modified `2026-10-12 12:59 UTC` · 3 rows

```csv
particao,n,positivos,prevalencia,ano_minimo,ano_maximo,grupos,percentual
teste,587287,128436,0.2186937562043771,2019,2026,587286,15.000439321075254
treino,2740583,599325,0.2186852213561859,2019,2026,2740574,69.99975990592398
validacao,587262,128422,0.21867922664841247,2019,2026,587259,14.999800773000757
```

### `outputs/tables/03_pilotos_provisoria_20261014T030944Z_contrato.csv`

- Git: `ignored` · `213 B` · modified `2026-10-14 03:09 UTC` · 8 rows

```csv
item,resultado
coorte_nao_vazia,True
dt_interna_disponivel,True
dt_interna_sem_nulos,True
ano_disponivel,True
alvo_disponivel,True
alvo_binario,True
features_sem_proibidas,True
features_presentes,True
```

### `outputs/tables/03_pilotos_provisoria_20261014T030944Z_manifesto.json`

- Git: `ignored` · `2.0 KB` · modified `2026-10-14 03:09 UTC`

```json
{
  "status_coorte": "provisoria",
  "versao_execucao": "piloto_v1",
  "fonte": "<REPO>\\data\\analytical\\coorte_provisoria_b.parquet",
  "seed": 42,
  "features": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
    "puerpera",
    "cardiopati",
    "hematologi",
    "sind_down",
    "hepatica",
    "asma",
    "diabetes",
    "neurologic",
    "pneumopati",
    "imunodepre",
    "renal",
    "obesidade",
    "out_morbi"
  ],
  "features_final_congelada": false,
  "n_base_modelagem": 3915132,
  "n_treino": 2740587,
  "n_validacao": 587271,
  "n_teste_criado_mas_nao_aberto": 587274,
  "teste_aberto": false,
  "quarentena_conflitos_split": {
    "politica": "quarentena_provisoria",
    "grupos_conflitantes": 2,
    "linhas_excluidas": 4,
    "waterfall": "<REPO>\\outputs\\tables\\supervisionado_waterfall_conflitos_split_provisorio.csv"
  },
  "artefatos": {
    "contrato": "<REPO>\\outputs\\tables\\03_pilotos_provisoria_20261014T030944Z_contrato.csv",
    "particoes": "<REPO>\\outputs\\tables\\03_pilotos_provisoria_20261014T030944Z_particoes.csv",
    "metricas_validacao": "<REPO>\\outputs\\tables\\03_pilotos_provisoria_20261014T030944Z_metricas_validacao.csv",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_pilotos_provisoria_20261014T030944Z_predicoes_validacao.parquet"
  }
}
```

### `outputs/tables/03_pilotos_provisoria_20261014T030944Z_metricas_validacao.csv`

- Git: `ignored` · `536 B` · modified `2026-10-14 03:09 UTC` · 2 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_apenas_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,duracao_fit_s,duracao_pred_s
0.7752527151170048,0.4407647509558362,0.19837290335933982,0.5056117549626814,0.3752271784623506,0.774862179587006,0.6686197683863156,0.5,587271,logistica_piloto_C1,provisoria,piloto_v1,60.564727000077255,5.747775800060481
0.5,0.21868609211079723,0.1708624852283169,0.0,0.0,0.0,0.7813139078892027,0.5,587271,dummy_prior,provisoria,piloto_v1,37.23039289994631,5.613179499981925
```

### `outputs/tables/03_pilotos_provisoria_20261014T030944Z_particoes.csv`

- Git: `ignored` · `313 B` · modified `2026-10-14 03:09 UTC` · 3 rows

```csv
particao,n,positivos,prevalencia,ano_minimo,ano_maximo,grupos,percentual
teste,587274,128428,0.21868497498612233,2019,2026,587270,15.000107276076516
treino,2740587,599327,0.21868563194673257,2019,2026,2740582,69.9998620736159
validacao,587271,128428,0.21868609211079723,2019,2026,587267,15.000030650307576
```

### `outputs/tables/03_pilotos_provisoria_20261014T234615Z_contrato.csv`

- Git: `ignored` · `213 B` · modified `2026-10-14 23:46 UTC` · 8 rows

```csv
item,resultado
coorte_nao_vazia,True
dt_interna_disponivel,True
dt_interna_sem_nulos,True
ano_disponivel,True
alvo_disponivel,True
alvo_binario,True
features_sem_proibidas,True
features_presentes,True
```

### `outputs/tables/03_pilotos_provisoria_20261014T234615Z_manifesto.json`

- Git: `ignored` · `2.0 KB` · modified `2026-10-14 23:46 UTC`

```json
{
  "status_coorte": "provisoria",
  "versao_execucao": "piloto_v1",
  "fonte": "<REPO>\\data\\analytical\\coorte_provisoria_b.parquet",
  "seed": 42,
  "features": [
    "idade_anos",
    "dias_sintomas_ate_internacao",
    "sexo_categoria",
    "cs_gestant",
    "cs_raca",
    "cs_zona",
    "ave_suino",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
    "puerpera",
    "cardiopati",
    "hematologi",
    "sind_down",
    "hepatica",
    "asma",
    "diabetes",
    "neurologic",
    "pneumopati",
    "imunodepre",
    "renal",
    "obesidade",
    "out_morbi"
  ],
  "features_final_congelada": false,
  "n_base_modelagem": 3915132,
  "n_treino": 2740587,
  "n_validacao": 587271,
  "n_teste_criado_mas_nao_aberto": 587274,
  "teste_aberto": false,
  "quarentena_conflitos_split": {
    "politica": "quarentena_provisoria",
    "grupos_conflitantes": 2,
    "linhas_excluidas": 4,
    "waterfall": "<REPO>\\outputs\\tables\\supervisionado_waterfall_conflitos_split_provisorio.csv"
  },
  "artefatos": {
    "contrato": "<REPO>\\outputs\\tables\\03_pilotos_provisoria_20261014T234615Z_contrato.csv",
    "particoes": "<REPO>\\outputs\\tables\\03_pilotos_provisoria_20261014T234615Z_particoes.csv",
    "metricas_validacao": "<REPO>\\outputs\\tables\\03_pilotos_provisoria_20261014T234615Z_metricas_validacao.csv",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_pilotos_provisoria_20261014T234615Z_predicoes_validacao.parquet"
  }
}
```

### `outputs/tables/03_pilotos_provisoria_20261014T234615Z_metricas_validacao.csv`

- Git: `ignored` · `534 B` · modified `2026-10-14 23:46 UTC` · 2 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_apenas_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,duracao_fit_s,duracao_pred_s
0.7752527151170048,0.4407647509558362,0.19837290335933982,0.5056117549626814,0.3752271784623506,0.774862179587006,0.6686197683863156,0.5,587271,logistica_piloto_C1,provisoria,piloto_v1,66.1743845999008,7.088190600043163
0.5,0.21868609211079723,0.1708624852283169,0.0,0.0,0.0,0.7813139078892027,0.5,587271,dummy_prior,provisoria,piloto_v1,44.04253809992224,6.498549000010826
```

### `outputs/tables/03_pilotos_provisoria_20261014T234615Z_particoes.csv`

- Git: `ignored` · `313 B` · modified `2026-10-14 23:46 UTC` · 3 rows

```csv
particao,n,positivos,prevalencia,ano_minimo,ano_maximo,grupos,percentual
teste,587274,128428,0.21868497498612233,2019,2026,587270,15.000107276076516
treino,2740587,599327,0.21868563194673257,2019,2026,2740582,69.9998620736159
validacao,587271,128428,0.21868609211079723,2019,2026,587267,15.000030650307576
```

### `outputs/tables/04_handoff_provisional_20261012T123353Z_calibracao_bruta.csv`

- Git: `ignored` · `238 B` · modified `2026-10-12 12:33 UTC` · 2 rows

```csv
modelo,n,prevalencia,probabilidade_media,diferenca_media
hist_gradient_boosting_v2,120000,0.21868333333333334,0.42388773529076346,0.20520440195743012
logistica_C1_v2,120000,0.21868333333333334,0.42976359899451055,0.2110802656611772
```

### `outputs/tables/04_handoff_provisional_20261012T123353Z_manifesto.json`

- Git: `ignored` · `2.5 KB` · modified `2026-10-12 12:33 UTC`

```json
{
  "tipo_coorte": "provisional",
  "fonte_coorte": {
    "kind": "provisional",
    "path": "<REPO>\\data\\analytical\\coorte_provisoria_b.parquet",
    "sha256": "da94652dbabd832f512f8346f19ef3fb12adc3e418c27c9229d693b4fe43c7f9",
    "size_bytes": 209678288,
    "rows": 3915136,
    "columns": 125
  },
  "status_execucao": "provisoria",
  "shortlist_yaml": [
    "hist_gradient_boosting",
    "logistic"
  ],
  "shortlist_execucao": [
    "hist_gradient_boosting_v2",
    "logistica_C1_v2"
  ],
  "teste_consultado": false,
  "tuning_realizado": false,
  "calibracao_escolhida": false,
  "limiar_escolhido": false,
  "gate_g1": "pendente",
  "gate_g6": "pendente",
  "features_final_congelada": false,
  "artefatos_origem_notebook03": {
    "metricas": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T022616Z_metricas.csv",
    "metricas_por_ano": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T022616Z_metricas_por_ano.csv",
    "variacao_temporal": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T022616Z_variacao_temporal.csv",
    "manifesto": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T022616Z_manifesto.json",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_cinco_familias_provisoria_20261012T022616Z_predicoes_validacao.parquet"
  },
  "artefatos_handoff": {
    "shortlist": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261012T123353Z_shortlist.csv",
    "temporal": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261012T123353Z_temporal.csv",
    "calibracao_bruta": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261012T123353Z_calibracao_bruta.csv",
    "transicao": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261012T123353Z_transicao.csv"
  }
}
```

### `outputs/tables/04_handoff_provisional_20261012T123353Z_shortlist.csv`

- Git: `ignored` · `638 B` · modified `2026-10-12 12:33 UTC` · 2 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,n_treino,duracao_fit_s,duracao_pred_s
0.78610522357088,0.4613001114076733,0.1955623845548722,0.5099550569792124,0.3701688846041283,0.8193735233595001,0.655625,0.5,120000,hist_gradient_boosting_v2,provisoria,piloto_v2_cinco_familias,300000,8.256994000053965,1.2180373000446707
0.7766099783482298,0.4417841314225881,0.1971585370522793,0.5050073674483654,0.375575780089153,0.7705586464446308,0.6696666666666666,0.5,120000,logistica_C1_v2,provisoria,piloto_v2_cinco_familias,300000,7.147862800047733,2.125225899973884
```

### `outputs/tables/04_handoff_provisional_20261012T123353Z_temporal.csv`

- Git: `ignored` · `2.1 KB` · modified `2026-10-12 12:33 UTC` · 16 rows

```csv
modelo,ano_internacao,n,positivos,prevalencia,pr_auc,roc_auc,brier,probabilidade_media
hist_gradient_boosting_v2,2019,1333,160,0.1200300075018754,0.3001910673476398,0.7887761082693947,0.1334327193210841,0.2540893685543209
hist_gradient_boosting_v2,2020,30032,8402,0.2797682472029835,0.513564896635687,0.758590941570722,0.2318403278550474,0.5195689558418913
hist_gradient_boosting_v2,2021,45369,12790,0.2819105556657629,0.4943006000217229,0.7388493024029806,0.218067596818748,0.4806897334557302
hist_gradient_boosting_v2,2022,14589,2649,0.1815751593666461,0.4184842639701873,0.796459205553374,0.1996344666945389,0.4135152875244976
hist_gradient_boosting_v2,2023,7378,706,0.0956898888587693,0.3445968141030262,0.8577794987805789,0.1307166727352439,0.2690956384383633
hist_gradient_boosting_v2,2024,7033,586,0.0833214844305417,0.2893927172599794,0.850534365006133,0.1244020673359512,0.2507788363738982
hist_gradient_boosting_v2,2025,8886,650,0.0731487733513391,0.2522818688880946,0.8410329883812155,0.1255241194688116,0.2482319183711748
hist_gradient_boosting_v2,2026,5380,299,0.0555762081784386,0.2119003176841704,0.8509362376326258,0.1052529543301546,0.2096730807908884
logistica_C1_v2,2019,1333,160,0.1200300075018754,0.2694926891465062,0.7737825021312872,0.1345924610796534,0.2727041047650496
logistica_C1_v2,2020,30032,8402,0.2797682472029835,0.5046763341300456,0.752653755798407,0.2296091787461704,0.5158554414250798
logistica_C1_v2,2021,45369,12790,0.2819105556657629,0.4811648256749729,0.7295302132128889,0.2173486218992117,0.4761036043482677
logistica_C1_v2,2022,14589,2649,0.1815751593666461,0.3890711402032777,0.7849080876889797,0.2065051520175628,0.4289261896671037
logistica_C1_v2,2023,7378,706,0.0956898888587693,0.3343534722267585,0.850611154136181,0.1364489119711729,0.2946068564659346
logistica_C1_v2,2024,7033,586,0.0833214844305417,0.2680860050649927,0.8359572486819544,0.1312028661322752,0.2765370087371456
logistica_C1_v2,2025,8886,650,0.0731487733513391,0.2491635062380489,0.8357842679418688,0.1322666992818211,0.2758266207485521
logistica_C1_v2,2026,5380,299,0.0555762081784386,0.196244141248507,0.8382300379339648,0.1125659535260074,0.239499732835665
```

### `outputs/tables/04_handoff_provisional_20261012T123353Z_transicao.csv`

- Git: `ignored` · `671 B` · modified `2026-10-12 12:33 UTC` · 6 rows

```csv
componente,estado_atual,condicao_para_final,troca_de_codigo,pronto
Loader da coorte,provisional,SRAG_COHORT_KIND=final e coorte_final.parquet disponível,nenhuma,False
Schema de features,piloto,features.final preenchida após validação do schema,nenhuma; somente YAML,False
Definição de alvo e features,pendente,G1_definicao_alvo_features aprovado,nenhuma; somente gate,False
Partição fixa,ausente,"treino, validacao e teste persistidos na coorte",nenhuma,False
Pilotos comparáveis,concluídos,rerodar Notebook 03 com a fonte final,nenhuma,False
Tuning dos finalistas,pendente,executar somente após G1 e repetição dos pilotos,Notebook posterior,False
```

### `outputs/tables/04_handoff_provisional_20261012T130545Z_calibracao_bruta.csv`

- Git: `ignored` · `238 B` · modified `2026-10-12 13:05 UTC` · 2 rows

```csv
modelo,n,prevalencia,probabilidade_media,diferenca_media
hist_gradient_boosting_v2,120000,0.21868333333333334,0.42388773529076346,0.20520440195743012
logistica_C1_v2,120000,0.21868333333333334,0.42976359899451055,0.2110802656611772
```

### `outputs/tables/04_handoff_provisional_20261012T130545Z_shortlist.csv`

- Git: `ignored` · `639 B` · modified `2026-10-12 13:05 UTC` · 2 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,n_treino,duracao_fit_s,duracao_pred_s
0.78610522357088,0.4613001114076733,0.1955623845548722,0.5099550569792124,0.3701688846041283,0.8193735233595001,0.655625,0.5,120000,hist_gradient_boosting_v2,provisoria,piloto_v2_cinco_familias,300000,10.287957499967888,1.423935899976641
0.7766099783482298,0.4417841314225881,0.1971585370522793,0.5050073674483654,0.375575780089153,0.7705586464446308,0.6696666666666666,0.5,120000,logistica_C1_v2,provisoria,piloto_v2_cinco_familias,300000,6.043404099997133,0.8790224000113085
```

### `outputs/tables/04_handoff_provisional_20261012T130545Z_temporal.csv`

- Git: `ignored` · `2.1 KB` · modified `2026-10-12 13:05 UTC` · 16 rows

```csv
modelo,ano_internacao,n,positivos,prevalencia,pr_auc,roc_auc,brier,probabilidade_media
hist_gradient_boosting_v2,2019,1333,160,0.1200300075018754,0.3001910673476398,0.7887761082693947,0.1334327193210841,0.2540893685543209
hist_gradient_boosting_v2,2020,30032,8402,0.2797682472029835,0.513564896635687,0.758590941570722,0.2318403278550474,0.5195689558418913
hist_gradient_boosting_v2,2021,45369,12790,0.2819105556657629,0.4943006000217229,0.7388493024029806,0.218067596818748,0.4806897334557302
hist_gradient_boosting_v2,2022,14589,2649,0.1815751593666461,0.4184842639701873,0.796459205553374,0.1996344666945389,0.4135152875244976
hist_gradient_boosting_v2,2023,7378,706,0.0956898888587693,0.3445968141030262,0.8577794987805789,0.1307166727352439,0.2690956384383633
hist_gradient_boosting_v2,2024,7033,586,0.0833214844305417,0.2893927172599794,0.850534365006133,0.1244020673359512,0.2507788363738982
hist_gradient_boosting_v2,2025,8886,650,0.0731487733513391,0.2522818688880946,0.8410329883812155,0.1255241194688116,0.2482319183711748
hist_gradient_boosting_v2,2026,5380,299,0.0555762081784386,0.2119003176841704,0.8509362376326258,0.1052529543301546,0.2096730807908884
logistica_C1_v2,2019,1333,160,0.1200300075018754,0.2694926891465062,0.7737825021312872,0.1345924610796534,0.2727041047650496
logistica_C1_v2,2020,30032,8402,0.2797682472029835,0.5046763341300456,0.752653755798407,0.2296091787461704,0.5158554414250798
logistica_C1_v2,2021,45369,12790,0.2819105556657629,0.4811648256749729,0.7295302132128889,0.2173486218992117,0.4761036043482677
logistica_C1_v2,2022,14589,2649,0.1815751593666461,0.3890711402032777,0.7849080876889797,0.2065051520175628,0.4289261896671037
logistica_C1_v2,2023,7378,706,0.0956898888587693,0.3343534722267585,0.850611154136181,0.1364489119711729,0.2946068564659346
logistica_C1_v2,2024,7033,586,0.0833214844305417,0.2680860050649927,0.8359572486819544,0.1312028661322752,0.2765370087371456
logistica_C1_v2,2025,8886,650,0.0731487733513391,0.2491635062380489,0.8357842679418688,0.1322666992818211,0.2758266207485521
logistica_C1_v2,2026,5380,299,0.0555762081784386,0.196244141248507,0.8382300379339648,0.1125659535260074,0.239499732835665
```

### `outputs/tables/04_handoff_provisional_20261012T130545Z_transicao.csv`

- Git: `ignored` · `689 B` · modified `2026-10-12 13:05 UTC` · 6 rows

```csv
componente,estado_atual,condicao_para_final,troca_de_codigo,pronto
Loader da coorte,provisional,SRAG_COHORT_KIND=final e coorte_final.parquet disponível,nenhuma,False
Schema de features,piloto,features.final preenchida após validação do schema,nenhuma; somente YAML,False
Definição de alvo e features,pendente,G1_definicao_alvo_features aprovado,nenhuma; somente gate,False
Partição fixa,"teste, treino, validacao","treino, validacao e teste persistidos na coorte",nenhuma,True
Pilotos comparáveis,concluídos,rerodar Notebook 03 com a fonte final,nenhuma,False
Tuning dos finalistas,pendente,executar somente após G1 e repetição dos pilotos,Notebook posterior,False
```

### `outputs/tables/04_handoff_provisional_20261012T130652Z_calibracao_bruta.csv`

- Git: `ignored` · `238 B` · modified `2026-10-12 13:06 UTC` · 2 rows

```csv
modelo,n,prevalencia,probabilidade_media,diferenca_media
hist_gradient_boosting_v2,120000,0.21868333333333334,0.42388773529076346,0.20520440195743012
logistica_C1_v2,120000,0.21868333333333334,0.42976359899451055,0.2110802656611772
```

### `outputs/tables/04_handoff_provisional_20261012T130652Z_shortlist.csv`

- Git: `ignored` · `639 B` · modified `2026-10-12 13:06 UTC` · 2 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,n_treino,duracao_fit_s,duracao_pred_s
0.78610522357088,0.4613001114076733,0.1955623845548722,0.5099550569792124,0.3701688846041283,0.8193735233595001,0.655625,0.5,120000,hist_gradient_boosting_v2,provisoria,piloto_v2_cinco_familias,300000,10.287957499967888,1.423935899976641
0.7766099783482298,0.4417841314225881,0.1971585370522793,0.5050073674483654,0.375575780089153,0.7705586464446308,0.6696666666666666,0.5,120000,logistica_C1_v2,provisoria,piloto_v2_cinco_familias,300000,6.043404099997133,0.8790224000113085
```

### `outputs/tables/04_handoff_provisional_20261012T130652Z_temporal.csv`

- Git: `ignored` · `2.1 KB` · modified `2026-10-12 13:06 UTC` · 16 rows

```csv
modelo,ano_internacao,n,positivos,prevalencia,pr_auc,roc_auc,brier,probabilidade_media
hist_gradient_boosting_v2,2019,1333,160,0.1200300075018754,0.3001910673476398,0.7887761082693947,0.1334327193210841,0.2540893685543209
hist_gradient_boosting_v2,2020,30032,8402,0.2797682472029835,0.513564896635687,0.758590941570722,0.2318403278550474,0.5195689558418913
hist_gradient_boosting_v2,2021,45369,12790,0.2819105556657629,0.4943006000217229,0.7388493024029806,0.218067596818748,0.4806897334557302
hist_gradient_boosting_v2,2022,14589,2649,0.1815751593666461,0.4184842639701873,0.796459205553374,0.1996344666945389,0.4135152875244976
hist_gradient_boosting_v2,2023,7378,706,0.0956898888587693,0.3445968141030262,0.8577794987805789,0.1307166727352439,0.2690956384383633
hist_gradient_boosting_v2,2024,7033,586,0.0833214844305417,0.2893927172599794,0.850534365006133,0.1244020673359512,0.2507788363738982
hist_gradient_boosting_v2,2025,8886,650,0.0731487733513391,0.2522818688880946,0.8410329883812155,0.1255241194688116,0.2482319183711748
hist_gradient_boosting_v2,2026,5380,299,0.0555762081784386,0.2119003176841704,0.8509362376326258,0.1052529543301546,0.2096730807908884
logistica_C1_v2,2019,1333,160,0.1200300075018754,0.2694926891465062,0.7737825021312872,0.1345924610796534,0.2727041047650496
logistica_C1_v2,2020,30032,8402,0.2797682472029835,0.5046763341300456,0.752653755798407,0.2296091787461704,0.5158554414250798
logistica_C1_v2,2021,45369,12790,0.2819105556657629,0.4811648256749729,0.7295302132128889,0.2173486218992117,0.4761036043482677
logistica_C1_v2,2022,14589,2649,0.1815751593666461,0.3890711402032777,0.7849080876889797,0.2065051520175628,0.4289261896671037
logistica_C1_v2,2023,7378,706,0.0956898888587693,0.3343534722267585,0.850611154136181,0.1364489119711729,0.2946068564659346
logistica_C1_v2,2024,7033,586,0.0833214844305417,0.2680860050649927,0.8359572486819544,0.1312028661322752,0.2765370087371456
logistica_C1_v2,2025,8886,650,0.0731487733513391,0.2491635062380489,0.8357842679418688,0.1322666992818211,0.2758266207485521
logistica_C1_v2,2026,5380,299,0.0555762081784386,0.196244141248507,0.8382300379339648,0.1125659535260074,0.239499732835665
```

### `outputs/tables/04_handoff_provisional_20261012T130652Z_transicao.csv`

- Git: `ignored` · `742 B` · modified `2026-10-12 13:06 UTC` · 6 rows

```csv
componente,estado_atual,condicao_para_final,troca_de_codigo,pronto_agora,pronto_para_final
Loader da coorte,provisional,SRAG_COHORT_KIND=final e coorte_final.parquet disponivel,nenhuma,True,False
Schema de features,piloto,features.final preenchida apos validacao do schema,nenhuma; somente YAML,True,False
Definicao de alvo e features,pendente,G1_definicao_alvo_features aprovado,nenhuma; somente gate,True,False
Particao fixa,"teste, treino, validacao","treino, validacao e teste persistidos no dataset supervisionado",nenhuma,True,False
Pilotos comparaveis,concluidos,rerodar Notebook 03 com a fonte final,nenhuma,True,False
Tuning dos finalistas,pendente,confirmar o tuning apos G1 e repeticao dos pilotos,Notebook 05,True,False
```

### `outputs/tables/04_handoff_provisional_20261012T130722Z_calibracao_bruta.csv`

- Git: `ignored` · `238 B` · modified `2026-10-12 13:07 UTC` · 2 rows

```csv
modelo,n,prevalencia,probabilidade_media,diferenca_media
hist_gradient_boosting_v2,120000,0.21868333333333334,0.42388773529076346,0.20520440195743012
logistica_C1_v2,120000,0.21868333333333334,0.42976359899451055,0.2110802656611772
```

### `outputs/tables/04_handoff_provisional_20261012T130722Z_manifesto.json`

- Git: `ignored` · `2.9 KB` · modified `2026-10-12 13:07 UTC`

```json
{
  "tipo_coorte": "provisional",
  "fonte_coorte": {
    "kind": "provisional",
    "path": "<REPO>\\data\\analytical\\coorte_provisoria_b.parquet",
    "sha256": "da94652dbabd832f512f8346f19ef3fb12adc3e418c27c9229d693b4fe43c7f9",
    "size_bytes": 209678288,
    "rows": 3915136,
    "columns": 125
  },
  "dataset_supervisionado": {
    "path": "<REPO>\\data\\analytical\\dataset_supervisionado.parquet",
    "sha256": "5dae83d596d07a21c33ac74260f5673506263041d4744b355fa778914b1329cf",
    "rows": 3915132,
    "columns": 36,
    "partition_column": "particao",
    "partition_counts": {
      "treino": 2740583,
      "teste": 587287,
      "validacao": 587262
    },
    "seed": 42,
    "test_opened": false
  },
  "status_execucao": "provisoria",
  "shortlist_yaml": [
    "hist_gradient_boosting",
    "logistic"
  ],
  "shortlist_execucao": [
    "hist_gradient_boosting_v2",
    "logistica_C1_v2"
  ],
  "teste_consultado": false,
  "tuning_realizado": false,
  "calibracao_escolhida": false,
  "limiar_escolhido": false,
  "gate_g1": "pendente",
  "gate_g6": "pendente",
  "features_final_congelada": false,
  "artefatos_origem_notebook03": {
    "metricas": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_metricas.csv",
    "metricas_por_ano": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_metricas_por_ano.csv",
    "variacao_temporal": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_variacao_temporal.csv",
    "manifesto": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_manifesto.json",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_cinco_familias_provisoria_20261012T130116Z_predicoes_validacao.parquet"
  },
  "artefatos_handoff": {
    "shortlist": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261012T130722Z_shortlist.csv",
    "temporal": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261012T130722Z_temporal.csv",
    "calibracao_bruta": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261012T130722Z_calibracao_bruta.csv",
    "transicao": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261012T130722Z_transicao.csv"
  }
}
```

### `outputs/tables/04_handoff_provisional_20261012T130722Z_shortlist.csv`

- Git: `ignored` · `639 B` · modified `2026-10-12 13:07 UTC` · 2 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,n_treino,duracao_fit_s,duracao_pred_s
0.78610522357088,0.4613001114076733,0.1955623845548722,0.5099550569792124,0.3701688846041283,0.8193735233595001,0.655625,0.5,120000,hist_gradient_boosting_v2,provisoria,piloto_v2_cinco_familias,300000,10.287957499967888,1.423935899976641
0.7766099783482298,0.4417841314225881,0.1971585370522793,0.5050073674483654,0.375575780089153,0.7705586464446308,0.6696666666666666,0.5,120000,logistica_C1_v2,provisoria,piloto_v2_cinco_familias,300000,6.043404099997133,0.8790224000113085
```

### `outputs/tables/04_handoff_provisional_20261012T130722Z_temporal.csv`

- Git: `ignored` · `2.1 KB` · modified `2026-10-12 13:07 UTC` · 16 rows

```csv
modelo,ano_internacao,n,positivos,prevalencia,pr_auc,roc_auc,brier,probabilidade_media
hist_gradient_boosting_v2,2019,1333,160,0.1200300075018754,0.3001910673476398,0.7887761082693947,0.1334327193210841,0.2540893685543209
hist_gradient_boosting_v2,2020,30032,8402,0.2797682472029835,0.513564896635687,0.758590941570722,0.2318403278550474,0.5195689558418913
hist_gradient_boosting_v2,2021,45369,12790,0.2819105556657629,0.4943006000217229,0.7388493024029806,0.218067596818748,0.4806897334557302
hist_gradient_boosting_v2,2022,14589,2649,0.1815751593666461,0.4184842639701873,0.796459205553374,0.1996344666945389,0.4135152875244976
hist_gradient_boosting_v2,2023,7378,706,0.0956898888587693,0.3445968141030262,0.8577794987805789,0.1307166727352439,0.2690956384383633
hist_gradient_boosting_v2,2024,7033,586,0.0833214844305417,0.2893927172599794,0.850534365006133,0.1244020673359512,0.2507788363738982
hist_gradient_boosting_v2,2025,8886,650,0.0731487733513391,0.2522818688880946,0.8410329883812155,0.1255241194688116,0.2482319183711748
hist_gradient_boosting_v2,2026,5380,299,0.0555762081784386,0.2119003176841704,0.8509362376326258,0.1052529543301546,0.2096730807908884
logistica_C1_v2,2019,1333,160,0.1200300075018754,0.2694926891465062,0.7737825021312872,0.1345924610796534,0.2727041047650496
logistica_C1_v2,2020,30032,8402,0.2797682472029835,0.5046763341300456,0.752653755798407,0.2296091787461704,0.5158554414250798
logistica_C1_v2,2021,45369,12790,0.2819105556657629,0.4811648256749729,0.7295302132128889,0.2173486218992117,0.4761036043482677
logistica_C1_v2,2022,14589,2649,0.1815751593666461,0.3890711402032777,0.7849080876889797,0.2065051520175628,0.4289261896671037
logistica_C1_v2,2023,7378,706,0.0956898888587693,0.3343534722267585,0.850611154136181,0.1364489119711729,0.2946068564659346
logistica_C1_v2,2024,7033,586,0.0833214844305417,0.2680860050649927,0.8359572486819544,0.1312028661322752,0.2765370087371456
logistica_C1_v2,2025,8886,650,0.0731487733513391,0.2491635062380489,0.8357842679418688,0.1322666992818211,0.2758266207485521
logistica_C1_v2,2026,5380,299,0.0555762081784386,0.196244141248507,0.8382300379339648,0.1125659535260074,0.239499732835665
```

### `outputs/tables/04_handoff_provisional_20261012T130722Z_transicao.csv`

- Git: `ignored` · `742 B` · modified `2026-10-12 13:07 UTC` · 6 rows

```csv
componente,estado_atual,condicao_para_final,troca_de_codigo,pronto_agora,pronto_para_final
Loader da coorte,provisional,SRAG_COHORT_KIND=final e coorte_final.parquet disponivel,nenhuma,True,False
Schema de features,piloto,features.final preenchida apos validacao do schema,nenhuma; somente YAML,True,False
Definicao de alvo e features,pendente,G1_definicao_alvo_features aprovado,nenhuma; somente gate,True,False
Particao fixa,"teste, treino, validacao","treino, validacao e teste persistidos no dataset supervisionado",nenhuma,True,False
Pilotos comparaveis,concluidos,rerodar Notebook 03 com a fonte final,nenhuma,True,False
Tuning dos finalistas,pendente,confirmar o tuning apos G1 e repeticao dos pilotos,Notebook 05,True,False
```

### `outputs/tables/04_handoff_provisional_20261012T130953Z_calibracao_bruta.csv`

- Git: `ignored` · `238 B` · modified `2026-10-12 13:09 UTC` · 2 rows

```csv
modelo,n,prevalencia,probabilidade_media,diferenca_media
hist_gradient_boosting_v2,120000,0.21868333333333334,0.42388773529076346,0.20520440195743012
logistica_C1_v2,120000,0.21868333333333334,0.42976359899451055,0.2110802656611772
```

### `outputs/tables/04_handoff_provisional_20261012T130953Z_manifesto.json`

- Git: `ignored` · `2.9 KB` · modified `2026-10-12 13:09 UTC`

```json
{
  "tipo_coorte": "provisional",
  "fonte_coorte": {
    "kind": "provisional",
    "path": "<REPO>\\data\\analytical\\coorte_provisoria_b.parquet",
    "sha256": "da94652dbabd832f512f8346f19ef3fb12adc3e418c27c9229d693b4fe43c7f9",
    "size_bytes": 209678288,
    "rows": 3915136,
    "columns": 125
  },
  "dataset_supervisionado": {
    "path": "<REPO>\\data\\analytical\\dataset_supervisionado.parquet",
    "sha256": "5dae83d596d07a21c33ac74260f5673506263041d4744b355fa778914b1329cf",
    "rows": 3915132,
    "columns": 36,
    "partition_column": "particao",
    "partition_counts": {
      "treino": 2740583,
      "teste": 587287,
      "validacao": 587262
    },
    "seed": 42,
    "test_opened": false
  },
  "status_execucao": "provisoria",
  "shortlist_yaml": [
    "hist_gradient_boosting",
    "logistic"
  ],
  "shortlist_execucao": [
    "hist_gradient_boosting_v2",
    "logistica_C1_v2"
  ],
  "teste_consultado": false,
  "tuning_realizado": false,
  "calibracao_escolhida": false,
  "limiar_escolhido": false,
  "gate_g1": "pendente",
  "gate_g6": "pendente",
  "features_final_congelada": false,
  "artefatos_origem_notebook03": {
    "metricas": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_metricas.csv",
    "metricas_por_ano": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_metricas_por_ano.csv",
    "variacao_temporal": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_variacao_temporal.csv",
    "manifesto": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_manifesto.json",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_cinco_familias_provisoria_20261012T130116Z_predicoes_validacao.parquet"
  },
  "artefatos_handoff": {
    "shortlist": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261012T130953Z_shortlist.csv",
    "temporal": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261012T130953Z_temporal.csv",
    "calibracao_bruta": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261012T130953Z_calibracao_bruta.csv",
    "transicao": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261012T130953Z_transicao.csv"
  }
}
```

### `outputs/tables/04_handoff_provisional_20261012T130953Z_shortlist.csv`

- Git: `ignored` · `639 B` · modified `2026-10-12 13:09 UTC` · 2 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,n_treino,duracao_fit_s,duracao_pred_s
0.78610522357088,0.4613001114076733,0.1955623845548722,0.5099550569792124,0.3701688846041283,0.8193735233595001,0.655625,0.5,120000,hist_gradient_boosting_v2,provisoria,piloto_v2_cinco_familias,300000,10.287957499967888,1.423935899976641
0.7766099783482298,0.4417841314225881,0.1971585370522793,0.5050073674483654,0.375575780089153,0.7705586464446308,0.6696666666666666,0.5,120000,logistica_C1_v2,provisoria,piloto_v2_cinco_familias,300000,6.043404099997133,0.8790224000113085
```

### `outputs/tables/04_handoff_provisional_20261012T130953Z_temporal.csv`

- Git: `ignored` · `2.1 KB` · modified `2026-10-12 13:09 UTC` · 16 rows

```csv
modelo,ano_internacao,n,positivos,prevalencia,pr_auc,roc_auc,brier,probabilidade_media
hist_gradient_boosting_v2,2019,1333,160,0.1200300075018754,0.3001910673476398,0.7887761082693947,0.1334327193210841,0.2540893685543209
hist_gradient_boosting_v2,2020,30032,8402,0.2797682472029835,0.513564896635687,0.758590941570722,0.2318403278550474,0.5195689558418913
hist_gradient_boosting_v2,2021,45369,12790,0.2819105556657629,0.4943006000217229,0.7388493024029806,0.218067596818748,0.4806897334557302
hist_gradient_boosting_v2,2022,14589,2649,0.1815751593666461,0.4184842639701873,0.796459205553374,0.1996344666945389,0.4135152875244976
hist_gradient_boosting_v2,2023,7378,706,0.0956898888587693,0.3445968141030262,0.8577794987805789,0.1307166727352439,0.2690956384383633
hist_gradient_boosting_v2,2024,7033,586,0.0833214844305417,0.2893927172599794,0.850534365006133,0.1244020673359512,0.2507788363738982
hist_gradient_boosting_v2,2025,8886,650,0.0731487733513391,0.2522818688880946,0.8410329883812155,0.1255241194688116,0.2482319183711748
hist_gradient_boosting_v2,2026,5380,299,0.0555762081784386,0.2119003176841704,0.8509362376326258,0.1052529543301546,0.2096730807908884
logistica_C1_v2,2019,1333,160,0.1200300075018754,0.2694926891465062,0.7737825021312872,0.1345924610796534,0.2727041047650496
logistica_C1_v2,2020,30032,8402,0.2797682472029835,0.5046763341300456,0.752653755798407,0.2296091787461704,0.5158554414250798
logistica_C1_v2,2021,45369,12790,0.2819105556657629,0.4811648256749729,0.7295302132128889,0.2173486218992117,0.4761036043482677
logistica_C1_v2,2022,14589,2649,0.1815751593666461,0.3890711402032777,0.7849080876889797,0.2065051520175628,0.4289261896671037
logistica_C1_v2,2023,7378,706,0.0956898888587693,0.3343534722267585,0.850611154136181,0.1364489119711729,0.2946068564659346
logistica_C1_v2,2024,7033,586,0.0833214844305417,0.2680860050649927,0.8359572486819544,0.1312028661322752,0.2765370087371456
logistica_C1_v2,2025,8886,650,0.0731487733513391,0.2491635062380489,0.8357842679418688,0.1322666992818211,0.2758266207485521
logistica_C1_v2,2026,5380,299,0.0555762081784386,0.196244141248507,0.8382300379339648,0.1125659535260074,0.239499732835665
```

### `outputs/tables/04_handoff_provisional_20261012T130953Z_transicao.csv`

- Git: `ignored` · `742 B` · modified `2026-10-12 13:09 UTC` · 6 rows

```csv
componente,estado_atual,condicao_para_final,troca_de_codigo,pronto_agora,pronto_para_final
Loader da coorte,provisional,SRAG_COHORT_KIND=final e coorte_final.parquet disponivel,nenhuma,True,False
Schema de features,piloto,features.final preenchida apos validacao do schema,nenhuma; somente YAML,True,False
Definicao de alvo e features,pendente,G1_definicao_alvo_features aprovado,nenhuma; somente gate,True,False
Particao fixa,"teste, treino, validacao","treino, validacao e teste persistidos no dataset supervisionado",nenhuma,True,False
Pilotos comparaveis,concluidos,rerodar Notebook 03 com a fonte final,nenhuma,True,False
Tuning dos finalistas,pendente,confirmar o tuning apos G1 e repeticao dos pilotos,Notebook 05,True,False
```

### `outputs/tables/04_handoff_provisional_20261014T030209Z_calibracao_bruta.csv`

- Git: `ignored` · `238 B` · modified `2026-10-14 03:02 UTC` · 2 rows

```csv
modelo,n,prevalencia,probabilidade_media,diferenca_media
hist_gradient_boosting_v2,120000,0.21868333333333334,0.42388773529076346,0.20520440195743012
logistica_C1_v2,120000,0.21868333333333334,0.42976359899451055,0.2110802656611772
```

### `outputs/tables/04_handoff_provisional_20261014T030209Z_manifesto.json`

- Git: `ignored` · `2.9 KB` · modified `2026-10-14 03:02 UTC`

```json
{
  "tipo_coorte": "provisional",
  "fonte_coorte": {
    "kind": "provisional",
    "path": "<REPO>\\data\\analytical\\coorte_provisoria_b.parquet",
    "sha256": "da94652dbabd832f512f8346f19ef3fb12adc3e418c27c9229d693b4fe43c7f9",
    "size_bytes": 209678288,
    "rows": 3915136,
    "columns": 125
  },
  "dataset_supervisionado": {
    "path": "<REPO>\\data\\analytical\\dataset_supervisionado.parquet",
    "sha256": "5dae83d596d07a21c33ac74260f5673506263041d4744b355fa778914b1329cf",
    "rows": 3915132,
    "columns": 36,
    "partition_column": "particao",
    "partition_counts": {
      "treino": 2740583,
      "teste": 587287,
      "validacao": 587262
    },
    "seed": 42,
    "test_opened": false
  },
  "status_execucao": "provisoria",
  "shortlist_yaml": [
    "hist_gradient_boosting",
    "logistic"
  ],
  "shortlist_execucao": [
    "hist_gradient_boosting_v2",
    "logistica_C1_v2"
  ],
  "teste_consultado": false,
  "tuning_realizado": false,
  "calibracao_escolhida": false,
  "limiar_escolhido": false,
  "gate_g1": "pendente",
  "gate_g6": "pendente",
  "features_final_congelada": false,
  "artefatos_origem_notebook03": {
    "metricas": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_metricas.csv",
    "metricas_por_ano": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_metricas_por_ano.csv",
    "variacao_temporal": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_variacao_temporal.csv",
    "manifesto": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261012T130116Z_manifesto.json",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_cinco_familias_provisoria_20261012T130116Z_predicoes_validacao.parquet"
  },
  "artefatos_handoff": {
    "shortlist": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261014T030209Z_shortlist.csv",
    "temporal": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261014T030209Z_temporal.csv",
    "calibracao_bruta": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261014T030209Z_calibracao_bruta.csv",
    "transicao": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261014T030209Z_transicao.csv"
  }
}
```

### `outputs/tables/04_handoff_provisional_20261014T030209Z_shortlist.csv`

- Git: `ignored` · `639 B` · modified `2026-10-14 03:02 UTC` · 2 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,n_treino,duracao_fit_s,duracao_pred_s
0.78610522357088,0.4613001114076733,0.1955623845548722,0.5099550569792124,0.3701688846041283,0.8193735233595001,0.655625,0.5,120000,hist_gradient_boosting_v2,provisoria,piloto_v2_cinco_familias,300000,10.287957499967888,1.423935899976641
0.7766099783482298,0.4417841314225881,0.1971585370522793,0.5050073674483654,0.375575780089153,0.7705586464446308,0.6696666666666666,0.5,120000,logistica_C1_v2,provisoria,piloto_v2_cinco_familias,300000,6.043404099997133,0.8790224000113085
```

### `outputs/tables/04_handoff_provisional_20261014T030209Z_temporal.csv`

- Git: `ignored` · `2.1 KB` · modified `2026-10-14 03:02 UTC` · 16 rows

```csv
modelo,ano_internacao,n,positivos,prevalencia,pr_auc,roc_auc,brier,probabilidade_media
hist_gradient_boosting_v2,2019,1333,160,0.1200300075018754,0.3001910673476398,0.7887761082693947,0.1334327193210841,0.2540893685543209
hist_gradient_boosting_v2,2020,30032,8402,0.2797682472029835,0.513564896635687,0.758590941570722,0.2318403278550474,0.5195689558418913
hist_gradient_boosting_v2,2021,45369,12790,0.2819105556657629,0.4943006000217229,0.7388493024029806,0.218067596818748,0.4806897334557302
hist_gradient_boosting_v2,2022,14589,2649,0.1815751593666461,0.4184842639701873,0.796459205553374,0.1996344666945389,0.4135152875244976
hist_gradient_boosting_v2,2023,7378,706,0.0956898888587693,0.3445968141030262,0.8577794987805789,0.1307166727352439,0.2690956384383633
hist_gradient_boosting_v2,2024,7033,586,0.0833214844305417,0.2893927172599794,0.850534365006133,0.1244020673359512,0.2507788363738982
hist_gradient_boosting_v2,2025,8886,650,0.0731487733513391,0.2522818688880946,0.8410329883812155,0.1255241194688116,0.2482319183711748
hist_gradient_boosting_v2,2026,5380,299,0.0555762081784386,0.2119003176841704,0.8509362376326258,0.1052529543301546,0.2096730807908884
logistica_C1_v2,2019,1333,160,0.1200300075018754,0.2694926891465062,0.7737825021312872,0.1345924610796534,0.2727041047650496
logistica_C1_v2,2020,30032,8402,0.2797682472029835,0.5046763341300456,0.752653755798407,0.2296091787461704,0.5158554414250798
logistica_C1_v2,2021,45369,12790,0.2819105556657629,0.4811648256749729,0.7295302132128889,0.2173486218992117,0.4761036043482677
logistica_C1_v2,2022,14589,2649,0.1815751593666461,0.3890711402032777,0.7849080876889797,0.2065051520175628,0.4289261896671037
logistica_C1_v2,2023,7378,706,0.0956898888587693,0.3343534722267585,0.850611154136181,0.1364489119711729,0.2946068564659346
logistica_C1_v2,2024,7033,586,0.0833214844305417,0.2680860050649927,0.8359572486819544,0.1312028661322752,0.2765370087371456
logistica_C1_v2,2025,8886,650,0.0731487733513391,0.2491635062380489,0.8357842679418688,0.1322666992818211,0.2758266207485521
logistica_C1_v2,2026,5380,299,0.0555762081784386,0.196244141248507,0.8382300379339648,0.1125659535260074,0.239499732835665
```

### `outputs/tables/04_handoff_provisional_20261014T030209Z_transicao.csv`

- Git: `ignored` · `742 B` · modified `2026-10-14 03:02 UTC` · 6 rows

```csv
componente,estado_atual,condicao_para_final,troca_de_codigo,pronto_agora,pronto_para_final
Loader da coorte,provisional,SRAG_COHORT_KIND=final e coorte_final.parquet disponivel,nenhuma,True,False
Schema de features,piloto,features.final preenchida apos validacao do schema,nenhuma; somente YAML,True,False
Definicao de alvo e features,pendente,G1_definicao_alvo_features aprovado,nenhuma; somente gate,True,False
Particao fixa,"teste, treino, validacao","treino, validacao e teste persistidos no dataset supervisionado",nenhuma,True,False
Pilotos comparaveis,concluidos,rerodar Notebook 03 com a fonte final,nenhuma,True,False
Tuning dos finalistas,pendente,confirmar o tuning apos G1 e repeticao dos pilotos,Notebook 05,True,False
```

### `outputs/tables/04_handoff_provisional_20261014T235131Z_calibracao_bruta.csv`

- Git: `ignored` · `239 B` · modified `2026-10-14 23:51 UTC` · 2 rows

```csv
modelo,n,prevalencia,probabilidade_media,diferenca_media
hist_gradient_boosting_v2,120000,0.21869166666666667,0.42677842518300924,0.20808675851634256
logistica_C1_v2,120000,0.21869166666666667,0.43240218481854953,0.21371051815188286
```

### `outputs/tables/04_handoff_provisional_20261014T235131Z_manifesto.json`

- Git: `ignored` · `2.9 KB` · modified `2026-10-14 23:51 UTC`

```json
{
  "tipo_coorte": "provisional",
  "fonte_coorte": {
    "kind": "provisional",
    "path": "<REPO>\\data\\analytical\\coorte_provisoria_b.parquet",
    "sha256": "da94652dbabd832f512f8346f19ef3fb12adc3e418c27c9229d693b4fe43c7f9",
    "size_bytes": 209678288,
    "rows": 3915136,
    "columns": 125
  },
  "dataset_supervisionado": {
    "path": "<REPO>\\data\\analytical\\dataset_supervisionado.parquet",
    "sha256": "7653e525b944eef54d3b087e4ceb64fa9ba9d611c779325704716a38e95fcf40",
    "rows": 3915132,
    "columns": 36,
    "partition_column": "particao",
    "partition_counts": {
      "treino": 2740587,
      "teste": 587274,
      "validacao": 587271
    },
    "seed": 42,
    "test_opened": false
  },
  "status_execucao": "provisoria",
  "shortlist_yaml": [
    "hist_gradient_boosting",
    "logistic"
  ],
  "shortlist_execucao": [
    "hist_gradient_boosting_v2",
    "logistica_C1_v2"
  ],
  "teste_consultado": false,
  "tuning_realizado": false,
  "calibracao_escolhida": false,
  "limiar_escolhido": false,
  "gate_g1": "pendente",
  "gate_g6": "pendente",
  "features_final_congelada": false,
  "artefatos_origem_notebook03": {
    "metricas": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261014T234809Z_metricas.csv",
    "metricas_por_ano": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261014T234809Z_metricas_por_ano.csv",
    "variacao_temporal": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261014T234809Z_variacao_temporal.csv",
    "manifesto": "<REPO>\\outputs\\tables\\03_cinco_familias_provisoria_20261014T234809Z_manifesto.json",
    "predicoes_validacao": "<REPO>\\outputs\\predictions\\03_cinco_familias_provisoria_20261014T234809Z_predicoes_validacao.parquet"
  },
  "artefatos_handoff": {
    "shortlist": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261014T235131Z_shortlist.csv",
    "temporal": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261014T235131Z_temporal.csv",
    "calibracao_bruta": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261014T235131Z_calibracao_bruta.csv",
    "transicao": "<REPO>\\outputs\\tables\\04_handoff_provisional_20261014T235131Z_transicao.csv"
  }
}
```

### `outputs/tables/04_handoff_provisional_20261014T235131Z_shortlist.csv`

- Git: `ignored` · `640 B` · modified `2026-10-14 23:51 UTC` · 2 rows

```csv
roc_auc,pr_auc,brier,f1,precision,recall,accuracy,limiar_diagnostico,n_validacao,modelo,status_coorte,versao_execucao,n_treino,duracao_fit_s,duracao_pred_s
0.7837338025141412,0.4577975780425485,0.1971935555323786,0.5098122866894198,0.3699626769405411,0.8196471440003048,0.6553,0.5,120000,hist_gradient_boosting_v2,provisoria,piloto_v2_cinco_familias,300000,13.10794989997521,1.6257725999457762
0.7742724458341613,0.4385600450900628,0.1991005682486104,0.5055658052772997,0.3744634799515756,0.7779217315093548,0.6672416666666666,0.5,120000,logistica_C1_v2,provisoria,piloto_v2_cinco_familias,300000,6.443985000019893,1.0642294000135737
```

### `outputs/tables/04_handoff_provisional_20261014T235131Z_temporal.csv`

- Git: `ignored` · `2.1 KB` · modified `2026-10-14 23:51 UTC` · 16 rows

```csv
modelo,ano_internacao,n,positivos,prevalencia,pr_auc,roc_auc,brier,probabilidade_media
hist_gradient_boosting_v2,2019,1355,163,0.1202952029520295,0.2874593001503639,0.7921367398196566,0.1340637550853806,0.261204075645717
hist_gradient_boosting_v2,2020,29987,8388,0.2797212125254277,0.510874944902731,0.7539260116490583,0.2337380637317967,0.5212712594470571
hist_gradient_boosting_v2,2021,45324,12785,0.2820801341452652,0.4880825143076391,0.7373332392813592,0.218992031972935,0.4826943399848201
hist_gradient_boosting_v2,2022,14664,2659,0.1813284233496999,0.4150340682318508,0.7968962255447343,0.2010315670492757,0.4174924446493188
hist_gradient_boosting_v2,2023,7363,724,0.0983294852641586,0.3679242282970099,0.8483983392959233,0.1351947036478361,0.2738261144768854
hist_gradient_boosting_v2,2024,7015,585,0.0833927298645759,0.3117292798082803,0.8570197126184684,0.1279114513316084,0.2595455633776146
hist_gradient_boosting_v2,2025,8900,651,0.0731460674157303,0.2506263293621174,0.8409368244421564,0.1260769126133062,0.2495485096608725
hist_gradient_boosting_v2,2026,5392,288,0.0534124629080118,0.1973550557585567,0.8578361742424242,0.1083314625294507,0.2170799748968142
logistica_C1_v2,2019,1355,163,0.1202952029520295,0.2788664842040202,0.777995944332359,0.1377989906035299,0.2805239075588887
logistica_C1_v2,2020,29987,8388,0.2797212125254277,0.4962780644029129,0.7454688769060491,0.2331323256721497,0.518726405601904
logistica_C1_v2,2021,45324,12785,0.2820801341452652,0.4782995207005368,0.7289671034390512,0.2180931847271191,0.4771601717117257
logistica_C1_v2,2022,14664,2659,0.1813284233496999,0.4002593509577733,0.7912969226342478,0.2068711246693542,0.4328685933134279
logistica_C1_v2,2023,7363,724,0.0983294852641586,0.3358602768626264,0.8418912936199038,0.1418608315891764,0.2993208602257584
logistica_C1_v2,2024,7015,585,0.0833927298645759,0.2773719795919383,0.8435433531389985,0.1353022983446636,0.2859023462082121
logistica_C1_v2,2025,8900,651,0.0731460674157303,0.2389680618999371,0.830904327834552,0.1327475443295916,0.2751367422542223
logistica_C1_v2,2026,5392,288,0.0534124629080118,0.183018175442795,0.845789522378962,0.1151479526148129,0.2448978904179417
```

### `outputs/tables/04_handoff_provisional_20261014T235131Z_transicao.csv`

- Git: `ignored` · `742 B` · modified `2026-10-14 23:51 UTC` · 6 rows

```csv
componente,estado_atual,condicao_para_final,troca_de_codigo,pronto_agora,pronto_para_final
Loader da coorte,provisional,SRAG_COHORT_KIND=final e coorte_final.parquet disponivel,nenhuma,True,False
Schema de features,piloto,features.final preenchida apos validacao do schema,nenhuma; somente YAML,True,False
Definicao de alvo e features,pendente,G1_definicao_alvo_features aprovado,nenhuma; somente gate,True,False
Particao fixa,"teste, treino, validacao","treino, validacao e teste persistidos no dataset supervisionado",nenhuma,True,False
Pilotos comparaveis,concluidos,rerodar Notebook 03 com a fonte final,nenhuma,True,False
Tuning dos finalistas,pendente,confirmar o tuning apos G1 e repeticao dos pilotos,Notebook 05,True,False
```

### `outputs/tables/coorte_provisoria_b_auditoria_duplicidades.csv`

- Git: `ignored` · `772 B` · modified `2026-10-11 13:17 UTC` · 15 rows

```csv
nu_notific_normalizado,quantidade_ocorrencias,quantidade_anos_internacao,quantidade_datas_internacao,quantidade_desfechos,quantidade_datas_sintomas,flag_ano_internacao_divergente,flag_dt_interna_divergente,flag_evolucao_divergente,flag_dt_sin_pri_divergente
31736177754051,2,1,1,1,2,0,0,0,1
31736866916969,2,2,2,1,2,1,1,0,1
31738324913116,2,1,1,1,2,0,0,0,1
31741716994694,2,1,1,1,2,0,0,0,1
31743975908104,2,1,1,1,2,0,0,0,1
31744118738694,2,1,1,1,2,0,0,0,1
31744265580768,2,1,1,1,2,0,0,0,1
31744397861067,2,1,1,1,2,0,0,0,1
31745324608735,2,2,2,1,2,1,1,0,1
31745519106567,2,1,1,1,2,0,0,0,1
31746458224089,2,1,1,1,2,0,0,0,1
31746459301774,2,1,1,1,2,0,0,0,1
31746816257499,2,1,1,1,2,0,0,0,1
31748044066509,2,1,1,1,2,0,0,0,1
31750088488779,2,1,2,1,2,0,1,0,1
```

### `outputs/tables/coorte_provisoria_b_auditoria_temporal.csv`

- Git: `ignored` · `448 B` · modified `2026-10-11 13:17 UTC` · 10 rows

```csv
verificacao,quantidade,percentual_coorte
dt_sin_pri_ausente,0,0.0
dt_notific_ausente,0,0.0
internacao_antes_sintomas,20918,0.5342853990257299
intervalo_negativo_sem_nosocomial,0,0.0
notificacao_apos_internacao,1951377,49.841870116389316
notificacao_fora_periodo,0,0.0
sintomas_fora_periodo,61,0.0015580557099421322
nu_notific_repetido,30,0.0007662569065289175
nu_notific_ausente,0,0.0
periodo_incompleto_2026,175521,4.483139283028738
```

### `outputs/tables/coorte_provisoria_b_resumo.csv`

- Git: `ignored` · `512 B` · modified `2026-10-11 13:17 UTC` · 16 rows

```csv
metrica,valor
versao_dados,dados-v2
status_coorte,provisoria_pessoa_b
data_inicial_coorte,2019-01-01
data_final_coorte,2026-09-28
registros_originais,4666910
colunas_originais_carregadas,93
duplicidades_exatas_removidas,0
registros_coorte_provisoria,3915136
colunas_coorte_provisoria,125
alvo_0_cura,3058951
alvo_1_obito_srag,856185
linhas_nu_notific_repetido,30
identificadores_repetidos_distintos,15
internacao_antes_sintomas,20918
intervalo_negativo_sem_nosocomial,0
registros_2026,175521
```

### `outputs/tables/coorte_provisoria_b_waterfall.csv`

- Git: `ignored` · `773 B` · modified `2026-10-11 13:17 UTC` · 6 rows

```csv
etapa,registros_antes,registros_excluidos,registros_depois,percentual_excluido,motivo
registros_originais,4666910,0,4666910,0.0,Total de registros carregados do dataset oficial.
duplicidades_exatas,4666910,0,4666910,0.0,Remoção somente de linhas integralmente idênticas nos campos originais carregados.
hospitalizacao_confirmada,4666910,232253,4434657,4.976590506352169,Manutenção somente de registros com hospital = 1.
data_internacao_valida,4434657,72113,4362544,1.6261235085374133,Manutenção somente de registros com dt_interna válida.
periodo_da_coorte,4362544,44,4362500,0.001008585815982601,Internação entre 01/01/2019 e 28/09/2026.
desfecho_elegivel,4362500,447364,3915136,10.254762177650429,Manutenção somente de evolucao = 1 ou evolucao = 2.
```

### `outputs/tables/dicionario_variaveis_revisao.csv`

- Git: `ignored` · `24.8 KB` · modified `2026-10-14 22:28 UTC` · 119 rows (first 60 shown)

```csv
coluna,nome_amigavel,grupo,uso_inicial_sugerido,aplicabilidade,transformacao_sugerida,risco_temporal,percentual_ausente,percentual_preenchido_aplicavel,valores_distintos_sem_ausente,amplitude_preenchimento_ano,ponto_de_decisao,decisao_final_usuario,justificativa_decisao_final
nu_notific,Numero da notificacao,estrutura_coorte,estrutura_coorte,Populacao geral,Identificador tecnico; nao usar como preditor,baixo,0.0,100.0,4666881,0.0,,,
dt_notific,Data da notificacao,estrutura_coorte,estrutura_coorte,Populacao geral,Auditoria temporal; nao usar data bruta,baixo,0.0,100.0,2829,0.0,,,
dt_sin_pri,Data dos primeiros sintomas,estrutura_coorte,estrutura_coorte,Populacao geral,Derivar intervalo entre sintomas e internacao,baixo,0.0,100.0,2828,0.0,,derivar_atributo,"Fonte para o intervalo entre sintomas e internação e para atributos
sazonais. A data bruta não será fornecida diretamente aos modelos."
sem_pri,Semana epidemiologica dos primeiros sintomas,estrutura_coorte,auditoria_temporal,Populacao geral,Auditar contra a semana derivada de dt_sin_pri; não utilizar diretamente como preditora,baixo,0.0,100.0,53,0.0,,,
hospital,Houve internacao?,estrutura_coorte,estrutura_coorte,Populacao geral,Filtro de elegibilidade,baixo,2.554795,97.445205,3,0.004207,,,
dt_interna,Data da internacao por SRAG,estrutura_coorte,estrutura_coorte,Populacao geral,"Ancora temporal; derivar ano, mes, semana e intervalos",confirmar_momento_medicao,6.519196,93.480804,2953,0.0,,estrutura_coorte,"Âncora temporal da coorte. Intervalos negativos não serão excluídos
automaticamente. A decisão dependerá da avaliação de nosocomial,
magnitude, quantidade e distribuição dos casos."
cs_sexo,Sexo,demografia_contexto_social,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,0.0,100.0,3,0.0,,,
nu_idade_n,Idade informada,demografia_contexto_social,modelo_a_nucleo,Populacao geral,Combinar com tp_idade para criar idade_anos,baixo,0.0,100.0,139,0.0,Alta cardinalidade; evitar uso bruto no primeiro piloto,,
tp_idade,"Unidade da idade: dias, meses ou anos",demografia_contexto_social,modelo_a_nucleo,Populacao geral,Combinar com nu_idade_n,baixo,0.0,100.0,3,0.0,,,
cs_gestant,Situacao gestacional,demografia_contexto_social,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,0.0,100.0,8,0.0,,,
cs_raca,Raca ou cor,demografia_contexto_social,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,0.967257,99.032743,6,3.699653,,,
cs_etinia,Etnia indigena,demografia_contexto_social,exploracao_subgrupo,Registros com raca ou cor indigena,"Categorica; preservar sim, nao, ignorado e vazio",baixo,99.763119,70.879015,310,0.816109,Reavaliar o uso detalhado depois da EDA no denominador indígena. | Confirmar se cs_raca = 5 em todos os anos | Avaliar apenas no denominador aplicavel ou em sensibilidade,,
cs_escol_n,Escolaridade,demografia_contexto_social,modelo_b_ampliado,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,34.043168,65.956832,7,29.625463,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
cs_zona,Zona de residencia,demografia_contexto_social,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,9.943239,90.056761,4,7.92861,,,
ave_suino,"Contato direto com aves, suinos ou outro animal?",exposicao_animal,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,16.876049,83.123951,4,13.492583,,,
out_anim,Especificacao do outro animal,exposicao_animal,exploracao_texto,Registros com contato com outro animal,Categorizar respostas frequentes; nao usar texto bruto,baixo,99.886949,74.921897,575,0.324085,Confirmar se ave_suino = 3 significa outro animal | Avaliar apenas no denominador aplicavel ou em sensibilidade,decidir_depois_da_eda,"Preservar para EDA e possível categorização simples. Não utilizar texto
bruto e não implementar NLP antes do Fine Tuning."
febre,Febre,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,14.844276,85.155724,3,18.039239,,,
tosse,Tosse,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,11.048017,88.951983,3,12.214481,,,
garganta,Dor de garganta,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,27.194075,72.805925,3,28.304763,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
dispneia,Dispneia,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,12.240733,87.759267,3,15.037821,,,
desc_resp,Desconforto respiratorio,sintomas,modelo_b_ampliado,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",confirmar_momento_medicao,17.18364,82.81636,3,20.342508,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,modelo_b_ampliado,"Indicador clínico relevante, mas mais dependente da avaliação e do
momento de registro. Entrará no modelo ampliado e será removido se a
auditoria indicar informação posterior à admissão."
saturacao,Saturacao de oxigenio abaixo de 95%?,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",confirmar_momento_medicao,16.380239,83.619761,3,18.308578,,modelo_a_nucleo,"Medida clínica objetiva e plausivelmente disponível na avaliação inicial.
Será executada análise adicional sem a variável para verificar robustez
e possível incerteza temporal."
diarreia,Diarreia,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,28.277104,71.722896,3,29.808114,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
vomito,Vomito,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,28.683754,71.316246,3,29.275268,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
dor_abd,Dor abdominal,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,37.990598,62.009402,3,81.518308,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
fadiga,Fadiga,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,35.363613,64.636387,3,82.867461,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
perd_olft,Perda do olfato,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,37.834949,62.165051,3,81.09531,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
perd_pala,Perda do paladar,sintomas,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,37.91213,62.08787,3,80.911408,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
puerpera,Puerpera ou parturiente,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,65.655669,34.344331,3,12.660443,,,
cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,56.624255,43.375745,3,21.05926,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,65.453073,34.546927,3,12.513576,,,
sind_down,Sindrome de Down,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,65.570731,34.429269,3,12.425315,,,
hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,65.586159,34.413841,3,12.57102,,,
asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,64.482773,35.517227,3,11.712076,,,
diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,59.456278,40.543722,3,18.748456,,,
neurologic,Doenca neurologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,64.455946,35.544054,3,12.984829,,,
pneumopati,Outra pneumopatia cronica,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,64.448168,35.551832,3,12.840579,,,
imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,65.006803,34.993197,3,12.634167,,,
renal,Doenca renal cronica,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,64.898766,35.101234,3,13.248539,,,
obesidade,Obesidade,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,64.353887,35.646113,3,13.679778,,,
tabag,Tabagismo,comorbidades_fatores_risco,indisponivel_se_100pct_vazio,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,100.0,0.0,0,0.0,Coluna 100% vazia na versao atual; manter documentada e fora dos modelos,,
outro_sin,Apresentou outros sintomas?,sintomas,exploracao_texto,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,28.534962,71.465038,3,23.033708,Preenchimento varia pelo menos 20 pontos percentuais entre 2019 e 2026,,
outro_des,Descricao dos outros sintomas,sintomas,exploracao_texto,Registros com outro sintoma informado,Categorizar respostas frequentes; nao usar texto bruto,baixo,70.493389,98.3981,251506,9.60582,Decidir se os textos frequentes serao categorizados,decidir_depois_da_eda,"Preservar em EDA. Não utilizar texto bruto no primeiro modelo.
Categorizar somente se os termos frequentes acrescentarem informação
não representada pelas variáveis estruturadas."
obes_imc,IMC registrado,comorbidades_fatores_risco,reavaliar_apos_eda,Registros com obesidade informada,Converter para numero e validar faixa plausivel,baixo,98.836404,22.794108,1011,2.171606,Reavaliar somente depois da auditoria de valores e faixas plausíveis. | Decidir se IMC entra no Modelo C ou somente na EDA | Avaliar apenas no denominador aplicavel ou em sensibilidade,,
out_morbi,Outro fator de risco?,comorbidades_fatores_risco,modelo_a_nucleo,Populacao geral,"Categorica; preservar sim, nao, ignorado e vazio",baixo,58.916714,41.083286,3,17.486237,,,
morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,Registros com outro fator de risco informado,Categorizar respostas frequentes; nao usar texto bruto,baixo,77.219938,98.836507,232631,12.355135,Decidir se os textos frequentes serao categorizados,decidir_depois_da_eda,"Preservar em EDA. Não utilizar texto bruto no primeiro modelo.
Categorizar somente se houver ganho claro e suficiente antes do
congelamento das features."
out_antiv,Outro antiviral utilizado,tratamentos,excluir_modelagem,Populacao geral,Exploracao de texto,alto_tratamento,99.628705,0.371295,3273,0.564117,Avaliar apenas no denominador aplicavel ou em sensibilidade,excluir_modelagem,"Campo textual de tratamento com baixa cobertura, alta cardinalidade e
risco temporal. Preservado somente para auditoria ou exploração."
... [59 more rows omitted]
```

### `outputs/tables/eda_01_auditoria_datas_pos_corte.csv`

- Git: `ignored` · `347 B` · modified `2026-10-14 22:27 UTC` · 5 rows

```csv
coluna,data_corte_observada,quantidade_posterior_corte,menor_data_posterior_corte,maior_data_posterior_corte
dt_interna,2026-09-28,17,2026-09-29,2026-12-29
dose_1_cov,2026-09-28,3,2026-11-17,2026-12-23
dose_2_cov,2026-09-28,1,2026-10-30,2026-10-30
dose_ref,2026-09-28,1,2026-12-19,2026-12-19
dt_antivir,2026-09-28,3,2026-09-30,2026-12-03
```

### `outputs/tables/eda_01_auditoria_faixa_datas.csv`

- Git: `ignored` · `408 B` · modified `2026-10-14 22:27 UTC` · 19 rows

```csv
coluna,datas_antes_1900,datas_depois_2026,datas_fora_faixa
dt_notific,0,0,0
dt_sin_pri,0,0,0
dt_interna,21,76,97
dt_ut_dose,0,0,0
dt_vac_mae,0,0,0
dt_doseuni,0,0,0
dt_1_dose,0,0,0
dt_2_dose,0,0,0
dose_1_cov,13,52,65
dose_2_cov,25,43,68
dose_ref,0,4,4
dose_2ref,0,1,1
dose_adic,0,0,0
dos_re_bi,0,0,0
dt_antivir,6,19,25
dt_trt_cov,0,0,0
dt_evoluca,0,0,0
dt_encerra,0,0,0
dt_digita,0,0,0
```

### `outputs/tables/eda_01_auditoria_vazamento.csv`

- Git: `ignored` · `1.3 KB` · modified `2026-10-14 22:27 UTC` · 10 rows

```csv
coluna,uso_nesta_eda,candidata_feature_principal,risco_temporal,justificativa,existe_no_dataframe
evolucao,rotulo,False,desfecho,Fonte utilizada para construir o alvo. Não pode ser utilizada como preditora.,True
dt_evoluca,auditoria,False,posterior_admissao,"Data de alta ou óbito, posterior ao ponto de previsão.",True
dt_encerra,auditoria,False,posterior_admissao,"Data de encerramento do caso, posterior ao ponto de previsão.",True
dt_digita,auditoria,False,administrativo,Data administrativa de inclusão do registro.,True
antiviral,eda_sensibilidade,False,tratamento,A disponibilidade até a admissão precisa ser confirmada.,True
tp_antivir,eda_sensibilidade,False,tratamento,Tipo de tratamento condicionado ao uso de antiviral.,True
dt_antivir,auditoria_temporal,False,tratamento,Somente tratamentos iniciados até a admissão poderão ser avaliados em sensibilidade.,True
trat_cov,eda_sensibilidade,False,tratamento,Pode representar decisão assistencial posterior ao ponto de previsão.,True
tipo_trat,eda_sensibilidade,False,tratamento,Tipo de tratamento condicionado ao registro de tratamento para COVID-19.,True
dt_trt_cov,auditoria_temporal,False,tratamento,Somente tratamentos iniciados até a admissão poderão ser avaliados em sensibilidade.,True
```

### `outputs/tables/eda_01_ausencias.csv`

- Git: `ignored` · `5.2 KB` · modified `2026-10-14 22:27 UTC` · 88 rows (first 60 shown)

```csv
coluna,quantidade_ausente,quantidade_preenchida,percentual_ausente,percentual_preenchido
tabag,4666910,0,100.0,0.0
out_trat,4664116,2794,99.94013169313314,0.05986830686685623
dt_trt_cov,4663077,3833,99.9178685682818,0.08213143171820327
tipo_trat,4662126,4784,99.89749105939477,0.10250894060523986
out_anim,4661634,5276,99.88694875195793,0.11305124804206637
dt_vac_mae,4661265,5645,99.87904202138031,0.12095797861968625
dt_2_dose,4656015,10895,99.76654788714589,0.23345211285411546
cs_etinia,4655855,11055,99.7631194944835,0.23688050551649806
tp_pov_ct,4654353,12557,99.7309354583654,0.2690645416346148
out_antiv,4649582,17328,99.62870507466396,0.37129492533603603
dt_doseuni,4649309,17601,99.62285537968377,0.37714462031622636
dt_1_dose,4648284,18626,99.60089223919039,0.3991077608096149
dose_adic,4645758,21152,99.54676649003302,0.4532335099669803
obes_imc,4612606,54304,98.83640353038734,1.163596469612656
pac_cocbo,4583721,83189,98.21747151755659,1.7825284824434153
pac_dscbo,4583721,83189,98.21747151755659,1.7825284824434153
m_amamenta,4573155,93755,97.9910690371145,2.0089309628855068
mae_vac,4562552,104358,97.76387374086923,2.236126259130774
dos_re_bi,4555994,110916,97.62335249661982,2.376647503380181
dose_2ref,4471761,195149,95.81845375205435,4.181546247945643
dt_antivir,4319198,347712,92.54941706611012,7.4505829338898755
tp_antivir,4300025,366885,92.13858848788598,7.861411512114011
dt_ut_dose,4276869,390041,91.64241435982267,8.357585640177334
dose_ref,4193370,473540,89.85324336659588,10.146756633404115
trat_cov,3673788,993122,78.7199238896829,21.280076110317108
dose_2_cov,3642101,1024809,78.04095215035215,21.95904784964784
morb_desc,3603785,1063125,77.21993781752808,22.780062182471912
dose_1_cov,3455748,1211162,74.04788178902099,25.952118210979
outro_des,3289863,1377047,70.49338855902514,29.50661144097486
puerpera,3064091,1602819,65.6556693829536,34.344330617046396
hepatica,3060847,1606063,65.58615872172379,34.4138412782762
sind_down,3060127,1606783,65.57073095474307,34.42926904525693
hematologi,3054636,1612274,65.45307280406092,34.54692719593907
imunodepre,3033809,1633101,65.0068032166894,34.99319678331059
renal,3028767,1638143,64.89876599291608,35.10123400708392
asma,3009353,1657557,64.48277339824423,35.517226601755766
neurologic,3008101,1658809,64.45594622566108,35.544053774338906
pneumopati,3007738,1659172,64.44816805980831,35.55183194019169
obesidade,3003338,1663572,64.35388726159279,35.64611273840721
diabetes,2774771,1892139,59.456278351200254,40.54372164879974
out_morbi,2749590,1917320,58.91671362850366,41.08328637149634
cardiopati,2642603,2024307,56.62425459243911,43.37574540756089
dor_abd,1772987,2893923,37.990597633123414,62.009402366876586
perd_pala,1769325,2897585,37.91213029606313,62.087869703936875
perd_olft,1765723,2901187,37.834948606251245,62.16505139374875
estrang,1753176,2913734,37.566098339158025,62.433901660841975
fadiga,1650388,3016522,35.363613183026885,64.63638681697311
cs_escol_n,1588764,3078146,34.043167749110225,65.95683225088978
vacina_cov,1531225,3135685,32.81025346535502,67.18974653464498
vomito,1338645,3328265,28.68375434709476,71.31624565290524
outro_sin,1331701,3335209,28.53496210554735,71.46503789445265
diarreia,1319667,3347243,28.277104122427904,71.7228958775721
garganta,1269123,3397787,27.194074880381237,72.80592511961876
vacina,1194387,3472523,25.592672667782324,74.40732733221768
pov_ct,1066268,3600642,22.84740867083359,77.15259132916641
co_rg_inte,1010405,3656505,21.650406800216846,78.34959319978316
desc_resp,801945,3864965,17.18363971021511,82.81636028978488
ave_suino,787590,3879320,16.87604860603697,83.12395139396303
antiviral,776808,3890102,16.645017795500664,83.35498220449934
saturacao,764451,3902459,16.380238744694026,83.61976125530597
... [28 more rows omitted]
```

### `outputs/tables/eda_01_cardinalidade.csv`

- Git: `ignored` · `1.5 KB` · modified `2026-10-14 22:27 UTC` · 88 rows (first 60 shown)

```csv
coluna,valores_distintos_sem_na,valores_distintos_com_na
nu_notific,4666881,4666881
outro_des,251506,251507
morb_desc,232631,232632
co_mun_res,5604,5605
co_mun_not,3661,3662
out_antiv,3273,3274
dt_ut_dose,3072,3073
co_mu_inte,3028,3029
dt_interna,2953,2954
dt_antivir,2856,2857
dt_notific,2829,2829
dt_sin_pri,2828,2828
dt_evoluca,2827,2828
dt_encerra,2820,2821
dt_digita,2764,2765
dose_1_cov,2060,2061
dose_2_cov,1960,1961
dt_1_dose,1820,1821
dt_vac_mae,1767,1768
dt_2_dose,1732,1733
pac_dscbo,1628,1629
pac_cocbo,1628,1629
dt_doseuni,1561,1562
dt_trt_cov,1378,1379
dose_ref,1205,1206
obes_imc,1011,1012
dos_re_bi,773,774
dose_adic,773,774
dose_2ref,757,758
out_anim,575,576
out_trat,555,556
co_rg_resi,320,321
co_rg_inte,312,313
co_regiona,312,313
cs_etinia,310,311
nu_idade_n,139,139
co_pais,57,58
sem_pri,53,53
tp_pov_ct,46,47
sg_uf_not,27,28
sg_uf,27,28
sg_uf_inte,27,28
cs_gestant,8,8
cs_escol_n,7,8
cs_raca,6,7
cs_zona,4,5
evolucao,4,5
ave_suino,4,5
febre,3,4
desc_resp,3,4
hospital,3,4
vomito,3,4
dispneia,3,4
garganta,3,4
tosse,3,4
diarreia,3,4
vacina_cov,3,4
perd_olft,3,4
saturacao,3,4
outro_sin,3,4
... [28 more rows omitted]
```

### `outputs/tables/eda_01_duplicidades_nu_notific.csv`

- Git: `ignored` · `4.0 KB` · modified `2026-10-14 22:27 UTC` · 58 rows

```csv
nu_notific,dt_notific,dt_sin_pri,hospital,dt_interna,evolucao,dt_evoluca,dt_encerra
31735935004234,2024-01-03,2024-01-01,1,2024-01-03,,,
31735935004234,2025-01-03,2025-01-01,1,2025-01-03,1,2025-01-10,2025-07-25
31736177754051,2025-01-06,2025-01-02,1,2025-01-02,1,2025-01-05,2025-01-06
31736177754051,2025-01-06,2024-01-02,1,2025-01-02,1,2025-01-05,2025-01-06
31736344210476,2025-01-08,2025-01-03,1,2025-01-03,1,2025-02-07,2025-02-08
31736344210476,2025-01-08,2024-12-25,1,2025-01-05,,,
31736722248953,2025-01-12,2025-01-09,2,,3,2025-01-12,2025-01-12
31736722248953,2025-01-12,2024-01-09,2,,2,2025-01-12,2025-01-12
31736866916969,2025-01-14,2024-01-13,1,2024-01-14,1,2025-01-23,2025-01-24
31736866916969,2025-01-14,2025-01-13,1,2025-01-14,1,2025-01-23,2025-01-24
31737727549117,2025-01-20,2025-01-11,1,2025-01-12,1,,2025-09-25
31737727549117,2025-01-20,2024-01-11,1,2025-01-12,,,
31738324913116,2025-01-30,2025-01-27,1,2025-01-30,1,2025-02-03,2025-02-04
31738324913116,2025-01-30,2024-01-27,1,2025-01-30,1,2025-02-03,2025-02-04
31738932515531,2024-02-07,2024-02-06,1,2024-02-06,,,
31738932515531,2025-02-07,2025-02-06,1,2025-02-06,1,2025-02-08,2025-08-18
31739904591826,2025-02-06,2025-02-05,1,2025-02-06,3,2025-02-06,2025-02-08
31739904591826,2025-02-06,2024-02-05,1,2025-02-06,3,2025-02-06,2025-02-08
31741286280540,2025-02-24,2024-02-02,1,2024-12-02,3,2025-02-27,2025-02-27
31741286280540,2025-02-24,2025-02-10,1,2025-02-14,3,2025-02-27,2025-02-27
31741716994694,2025-03-02,2025-03-01,1,2025-03-02,1,2025-03-10,2025-03-10
31741716994694,2025-03-02,2024-03-01,1,2025-03-02,1,2025-03-10,2025-03-02
31743770891762,2024-04-04,2024-04-04,2,,,,
31743770891762,2025-04-04,2025-04-03,2,,2,2025-04-03,2025-05-04
31743975908104,2025-04-06,2025-04-01,1,2025-04-01,1,2025-04-30,2025-04-11
31743975908104,2025-04-06,2024-04-05,1,2025-04-01,1,2025-04-30,2025-04-11
31744118738694,2025-04-02,2025-03-26,1,2025-03-27,2,2025-04-05,2025-04-09
31744118738694,2025-04-02,2024-03-26,1,2025-03-27,2,2025-04-05,2025-04-09
31744265580768,2025-04-10,2025-04-10,1,2025-04-10,1,2025-04-10,2025-04-10
31744265580768,2025-04-10,2024-04-10,1,2025-04-10,1,2025-04-10,2025-04-10
31744397861067,2025-04-11,2025-04-07,1,2025-04-08,1,2025-06-03,2025-06-03
31744397861067,2025-04-11,2024-04-07,1,2025-04-08,1,2025-06-03,2025-06-03
31744638947734,2025-04-07,2025-04-02,1,2025-04-02,1,2025-04-30,2025-07-07
31744638947734,2025-04-07,2024-05-02,1,2025-04-02,,,
31744827529781,2025-04-14,2025-03-31,1,2025-04-13,1,2025-04-22,2025-04-16
31744827529781,2025-04-14,2024-03-31,1,2025-04-13,,,
31745324608735,2025-04-20,2024-08-15,1,2024-08-15,2,2025-04-20,2025-04-24
31745324608735,2025-04-20,2025-04-16,1,2025-04-16,2,2025-04-20,2025-04-24
31745519106567,2025-04-24,2025-04-15,1,2025-04-20,1,2025-04-30,2025-05-02
31745519106567,2025-04-24,2024-04-15,1,2025-04-20,1,2025-04-30,2025-05-02
31746458224089,2025-05-05,2025-05-02,1,2025-04-14,1,2025-05-26,2025-06-10
31746458224089,2025-05-05,2024-05-02,1,2025-04-14,1,2025-05-26,2025-06-10
31746459301774,2025-05-05,2025-04-29,1,2025-04-30,2,2025-05-04,2025-05-05
31746459301774,2025-05-05,2024-04-29,1,2025-04-30,2,2025-05-04,2025-05-05
31746816257499,2025-04-28,2025-04-26,1,2025-04-28,1,2025-05-06,2025-05-06
31746816257499,2025-04-28,2022-04-26,1,2025-04-28,1,2025-05-06,
31747221217548,2025-04-24,2025-04-23,1,2025-04-23,1,2025-05-13,2025-10-16
31747221217548,2025-04-24,2024-04-23,1,2025-04-23,,,
31748044066509,2025-05-23,2025-05-20,1,2025-05-20,1,,2025-09-26
31748044066509,2025-05-23,2023-05-20,1,2025-05-20,1,,2025-06-06
31748270369373,2025-05-26,2025-05-23,1,2025-05-23,1,2025-05-30,2025-12-02
31748270369373,2025-05-26,2024-05-23,1,2025-05-23,,,
31749232662324,2025-05-23,2025-05-20,1,2025-05-21,1,2025-05-22,2025-07-29
31749232662324,2025-05-23,2023-05-20,1,2025-05-23,,,
31750088488779,2025-05-06,2024-12-28,1,2025-01-02,1,,2025-05-06
31750088488779,2025-05-06,2025-05-06,1,2025-05-06,1,,2025-05-06
31750216000318,2024-06-17,2024-06-16,1,2024-06-17,,,
31750216000318,2025-06-17,2025-06-16,1,2025-06-17,1,,2025-08-01
```

### `outputs/tables/eda_01_frequencias_categoricas.csv`

- Git: `ignored` · `10.2 KB` · modified `2026-10-14 22:27 UTC` · 275 rows (first 60 shown)

```csv
coluna,valor,quantidade,percentual
sg_uf_not,SP,1306611,27.997347281177483
sg_uf_not,MG,521998,11.185088206114967
sg_uf_not,RJ,385820,8.267140356252852
sg_uf_not,PR,380639,8.156124716354075
sg_uf_not,RS,256895,5.504605831267369
sg_uf_not,CE,197156,4.224551148404405
sg_uf_not,SC,187571,4.019169000473546
sg_uf_not,PE,176695,3.7861240092480895
sg_uf_not,BA,176306,3.7777887295876713
sg_uf_not,GO,137685,2.9502390232509303
sg_uf_not,DF,121098,2.594821841432554
sg_uf_not,PA,103062,2.208356278565475
sg_uf_not,MS,95598,2.048421760865326
sg_uf_not,AM,78321,1.6782196356904249
sg_uf_not,PB,72324,1.5497191932134966
sg_uf_not,MT,70767,1.516356647117686
sg_uf_not,MA,54497,1.167731968261655
sg_uf_not,SE,49040,1.0508023510202682
sg_uf_not,ES,45763,0.9805845838038445
sg_uf_not,AL,43497,0.9320299727228509
sg_uf_not,RN,42488,0.9104096714957006
sg_uf_not,PI,41981,0.8995459522467757
sg_uf_not,RO,31827,0.6819715829103197
sg_uf_not,TO,29217,0.6260459276052034
sg_uf_not,AC,20991,0.4497836898504578
sg_uf_not,AP,17444,0.37378051001626345
sg_uf_not,RR,10998,0.2356591406305243
sg_uf_not,,10621,0.22758099041978527
sg_uf,SP,1301367,27.88498171166789
sg_uf,MG,524022,11.228457373294107
sg_uf,RJ,386412,8.279825409103667
sg_uf,PR,379585,8.13354017969063
sg_uf,RS,257423,5.515919527053232
sg_uf,CE,196933,4.219772826131209
sg_uf,SC,187448,4.01653342361434
sg_uf,BA,177563,3.8047230394415146
sg_uf,PE,175844,3.767889245775042
sg_uf,GO,151110,3.237902595078971
sg_uf,DF,105934,2.2698959268552423
sg_uf,PA,105265,2.2555609600356554
sg_uf,MS,96096,2.0590926330269923
sg_uf,AM,80338,1.7214388106905854
sg_uf,MT,78606,1.6843264601202939
sg_uf,PB,72426,1.5519047935357657
sg_uf,MA,56431,1.2091726645682046
sg_uf,SE,48395,1.0369816431000383
sg_uf,ES,45952,0.9846343726362841
sg_uf,AL,43932,0.9413509152737035
sg_uf,RN,42662,0.9141380485160416
sg_uf,PI,40410,0.8658834217930065
sg_uf,RO,34657,0.742611278126212
sg_uf,TO,29024,0.6219104289562044
sg_uf,AC,20399,0.4370986369996422
sg_uf,AP,16631,0.35635998980053185
sg_uf,RR,11161,0.23915181565532656
sg_uf,,884,0.01894186945966389
sg_uf_inte,SP,1155790,24.76563722034494
sg_uf_inte,,514107,11.016004165497083
sg_uf_inte,MG,483408,10.358202750856563
sg_uf_inte,PR,364385,7.807842876764283
... [215 more rows omitted]
```

### `outputs/tables/eda_01_preenchimento_por_ano_internacao.csv`

- Git: `ignored` · `12.2 KB` · modified `2026-10-14 22:27 UTC` · 8 rows

```csv
ano_internacao,nu_notific,dt_notific,dt_sin_pri,sem_pri,hospital,dt_interna,cs_sexo,nu_idade_n,tp_idade,cs_gestant,cs_raca,cs_etinia,cs_escol_n,cs_zona,ave_suino,out_anim,febre,tosse,garganta,dispneia,desc_resp,saturacao,diarreia,vomito,dor_abd,fadiga,perd_olft,perd_pala,puerpera,cardiopati,hematologi,sind_down,hepatica,asma,diabetes,neurologic,pneumopati,imunodepre,renal,obesidade,tabag,outro_sin,outro_des,obes_imc,out_morbi,morb_desc,out_antiv,out_trat,sg_uf_not,co_regiona,co_mun_not,co_pais,sg_uf,co_rg_resi,co_mun_res,sg_uf_inte,co_rg_inte,co_mu_inte,vacina,dt_ut_dose,mae_vac,dt_vac_mae,m_amamenta,dt_doseuni,dt_1_dose,dt_2_dose,vacina_cov,dose_1_cov,dose_2_cov,dose_ref,dose_2ref,dose_adic,dos_re_bi,pac_cocbo,pac_dscbo,pov_ct,tp_pov_ct,estrang,antiviral,tp_antivir,dt_antivir,trat_cov,tipo_trat,dt_trt_cov,evolucao,dt_evoluca,dt_encerra,dt_digita
2019,100.0,100.0,100.0,100.0,99.99579345882847,100.0,100.0,100.0,100.0,100.0,96.30034703964665,0.5447470817120622,92.33568198548743,97.57072247344621,96.64318014512567,0.0,99.65506362393522,99.58986223577662,97.6464402145336,99.22389315385425,99.12714270690924,98.30055736670522,97.16689452098012,97.24471553265329,0.29866442317804187,0.5300241876117362,0.2944578820065201,0.2944578820065201,37.68009254390577,38.59922178988327,37.75581028499316,37.87149016721001,37.62961404984752,38.199600378588705,38.21222000210327,38.16174150804501,38.226942896203596,37.957724261226204,37.56441266168893,37.57072247344621,0.0,92.04543064465244,21.827742139026185,1.4996319276474919,37.95562099064045,17.644336943947838,0.2650120938058681,0.0,99.91586917656956,89.98632874119255,99.91586917656956,99.99369018824271,99.92848880008412,91.20201913976234,99.92848880008412,95.65674624040382,86.21306131033758,95.65674624040382,81.19465769271217,16.479125039436322,12.714270690924387,2.288358397307814,11.39762330423809,0.49637185823956254,0.6141550110421705,0.42906719949521505,1.3145441161005362,0.10516352928804291,0.07571774108739089,0.025239247029130295,0.01051635292880429,0.004206541171521716,0.006309811757282574,0.016826164686086865,0.016826164686086865,1.7162687979808602,0.0,0.47113261121043226,98.87054369544643,61.236723104427384,61.23461983384162,0.20191397623304236,0.0,0.0,94.35902828898938,84.61247239457356,96.52960353349458,65.51898201703649
2020,100.0,100.0,100.0,100.0,99.99897805132969,100.0,100.0,100.0,100.0,100.0,96.503727790036,0.15998141911508534,71.42269190570201,90.21521309952387,84.03205202647777,0.03762629195215422,87.96581117175705,89.92869585414005,76.58697015445361,90.19458831726861,85.20924399024503,85.74623156427825,75.83463012425968,74.97591452792939,45.69178957147834,46.89099988386947,46.10623620949948,46.01342468935083,42.12621066078272,53.63892695389618,42.4288003716177,42.24791545697364,42.325490651492274,43.19498316107305,50.18241783764952,43.56390663105331,43.600232261061436,42.880130066194404,43.23836952734874,43.32746487051446,0.0,75.52860294971549,31.433561723377075,2.384020438973406,49.54128440366973,27.14286377888747,0.7004993612820811,0.0011148530948786436,99.83537335965626,86.30523748693531,99.83537335965626,100.0,99.99098827081639,86.6736964347927,99.99098827081639,94.18195331552666,81.69132504935548,94.18195331552666,80.78169782835907,9.017767971199628,0.7577284868191847,0.05054000696783184,0.5667169898966439,0.010126582278481013,0.010405295552200673,0.007896876088723725,12.811798861920797,2.2180002322610615,2.091743119266055,1.2298687725002904,0.4846823829984903,0.03465335036581117,0.1093485077226803,1.7885959818836374,1.7885959818836374,22.790477296481246,0.035954012309836254,6.14209731738474,88.41723377075833,15.679015213099524,15.354778771338983,1.0600394843804437,0.025920334455928465,0.0008361398211589827,94.35577749390315,88.82954360701429,94.67629775868076,100.0
2021,100.0,100.0,100.0,100.0,99.99975865726556,100.0,100.0,100.0,100.0,100.0,100.0,0.08724539849908954,65.94334237966349,89.64211285910291,83.15059665957521,0.08983983289429068,83.28393852035182,87.56101446004993,70.11036603245819,88.37391712531843,81.35192959549751,84.93514517368833,69.10776797792197,68.05527231304083,66.79166209121065,71.09148458362948,67.586826065498,67.55315875404399,34.64601657783243,45.28796411716225,34.62393371763142,34.512554045688596,34.50989927560978,35.355503881394526,42.054031811385826,35.422778168618926,35.45807454353039,34.95867609029597,35.20834514907138,37.03971415366533,0.0,70.50423737505989,31.20199542172833,1.3273247037216256,42.71760365972123,24.29832616746531,0.34023291987300547,0.0009653709377492618,99.85501335228678,88.51419758971011,99.85501335228678,100.0,99.98527809319933,88.84670754208113,99.98527809319933,91.8934785573014,81.69698937005926,91.8934785573014,74.38454585934305,4.389481318262284,0.9677240294100257,0.0328226118834749,0.7723570858830188,0.005671554259276913,0.005068197423183624,0.004042490801825034,74.6216047602441,20.435997716897734,13.687994526346783,1.9845009695944356,0.4784619710219779,0.02914213518330584,0.08706439144826154,2.3897154207146882,2.3897154207146882,93.25205714513267,0.26330492327111116,72.61604663707,84.11916538855577,2.359788921644461,2.0313817957588842,1.12284707196961,0.007421289083947449,0.0031374555476851008,92.92467572586844,87.28950388380795,93.48097072874644,100.0
2022,100.0,100.0,100.0,100.0,99.9996269596277,100.0,100.0,100.0,100.0,100.0,100.0,0.18148414112117284,63.26634149980882,90.70140916000634,85.02019081015042,0.0880375278614528,81.61582437259273,87.37538120063044,69.34167700299365,84.1860725377004,78.78463446706519,79.99197963199566,67.35878090406334,67.9694479935091,66.52522219217175,68.9885942906171,65.5775131263581,65.5260335549815,34.99976684976732,44.38844693967005,35.281412330849506,35.1314501011872,35.09992818972834,36.481856248892534,41.105132102921836,36.92596081210889,36.757160043645726,35.961464929542,36.101168548966214,35.57853898738191,0.0,69.01172279369935,28.90055676275565,0.4291829483245824,43.41984761300792,25.71945498801608,0.2284872280302536,0.11377731354975892,99.9287492888918,89.54106708198495,99.9287492888918,100.0,99.97649845654546,90.07582045566882,99.97649845654546,94.74423419474573,85.05618920607682,94.74423419474573,61.57889337573559,3.490165723185392,2.8360394303673515,0.10967386945452172,2.4995570145579005,0.021076781034627474,0.019957659917744598,0.01660029656709597,99.83996568028574,56.99422720023875,53.25878743226986,28.327939791283914,5.006574836561687,0.09139489121210143,0.1620860417618697,1.4552304923200314,1.4552304923200314,99.99925391925541,0.23874583826834658,91.33725647458196,82.69596277057084,3.7145495071204078,3.382730095964636,17.762876887351133,0.18819886782247008,0.156117395805161,93.68162869426544,87.73424603877754,93.56206925494511,100.0
2023,100.0,100.0,100.0,100.0,99.99924718919266,100.0,100.0,100.0,100.0,100.0,100.0,0.3560795118774725,64.89492643156385,92.68456097955742,85.66384739019314,0.32408505256501463,86.55291695367579,91.70063725434842,72.62215296362795,87.5741048138487,84.65470450293783,82.6985256200338,72.1840170737491,73.0034516375517,71.38076794230457,73.37910423042034,70.47927700050062,70.41942854131614,29.46576781056269,35.05350602813254,29.952836402919402,29.822600133247512,29.75447075518216,31.698981070572252,33.01941122666757,31.21680574846333,31.117434721892867,30.672899940151545,30.28219113113588,29.73113362015425,0.0,71.76959472430187,28.403928166792763,0.24052305294894813,34.97935416360837,19.180866560520343,0.2969838635003444,0.23600618810483642,99.98155613521988,87.07085078913393,99.98155613521988,100.0,99.97515724335739,88.16920175706042,99.97515724335739,96.41850258402309,84.12359647835105,96.41850258402309,55.814522473284626,3.7023235505568914,6.2727960522601265,0.22546683680190913,5.860255729831257,0.11593286433220036,0.11932051296528413,0.08280918880871453,99.98306175683457,49.45289474575697,45.10353030628107,30.313432779640987,17.575121108438633,1.7947009647270498,7.433253911793157,0.7377545912049114,0.7377545912049114,100.0,0.333118782253238,92.30250949482631,83.23189207704266,5.9618851888237705,5.493260461247182,77.1006244565647,0.39296724143771805,0.3278491066017744,95.5911635067433,89.56754783171668,95.10447131979026,100.0
2024,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,0.4475720989710578,62.71021877355773,92.04118926300583,85.81306957891123,0.23483721242308586,89.91541913508863,93.94988297607819,75.98819104303244,89.49784304980523,88.46337526197176,85.49811143519085,76.30512260870594,77.01713324939712,75.43129136785768,77.06725816700676,74.61113720413472,74.47654982693089,29.915892756357376,34.836423054304625,30.427403726610013,30.316102728453192,30.19611867370257,31.907470191461396,32.91549412512285,31.433848922708957,31.474106730552915,31.02732400036311,30.58567216725146,30.219799737140196,0.0,73.64060828758284,27.05877245260827,0.2158923616729882,33.98508882372211,17.327828801698722,0.1898431918916039,0.25101927243879435,99.99960531560937,87.37641445018491,99.99960531560937,100.0,99.9707933550936,88.38483306823699,99.9707933550936,96.22405443487115,84.26985361155953,96.22405443487115,77.27446747208595,13.423216125225462,5.60570240007578,0.2679907012357568,5.311662529058638,0.5778179478779794,0.5643986785966602,0.44717741458043075,99.98658073071867,45.579337482781895,41.42765237777611,20.577660074121727,12.152727071797036,1.935926936025607,9.961834019426366,0.6950392118942088,0.6950392118942088,100.0,0.4294166170022142,93.88515473601534,82.61336322409785,8.373624031543176,7.7733090733994565,77.1568515236791,0.36271495498624523,0.3252199378766769,95.08341654595903,89.08381912403746,94.6350550782067,100.0
2025,100.0,100.0,100.0,100.0,99.99968315928217,100.0,100.0,100.0,100.0,100.0,100.0,0.605165771063571,64.93397039440333,93.82604177228025,88.40141184223867,0.2341452904795701,92.22979823583088,95.77271114265436,81.5896532495184,92.53459900638751,91.92784903173477,88.74201561391058,81.57824698367637,82.12162881476223,80.88246476731217,82.4137559566055,80.27761583696645,80.15499847916455,31.220216972523573,34.73809946263815,31.600425833924767,31.597574267464264,31.424579235526718,33.09844874784548,33.50844063672311,32.28195021798641,32.418191726655174,32.063013281962895,31.714488492345126,31.3764194464159,0.0,76.18340008111122,25.655860285917065,0.24586839703944036,33.84080654973132,16.41741863530366,0.18756970495792355,0.18345077562607726,99.99683159282165,86.87107117509886,99.99683159282165,100.0,99.96799908749874,87.94832961573557,99.96799908749874,95.5940129777958,82.85511507654871,95.5940129777958,94.069375443577,26.965996654162023,5.222168711345432,0.29687975261076754,5.088778769137179,1.822467808983068,1.9023116698773193,1.2223714894048463,99.99239582277197,44.33298692081517,40.27900993612491,21.961814356686606,12.877040454222852,1.8227846497009024,10.833417824191423,0.7379220318361553,0.7379220318361553,99.99968315928217,0.5224703437088107,95.30156899523472,87.51045574368852,12.115038527831288,11.14487224982257,81.5399092568184,0.2766019466693704,0.2544230964209672,96.23308070566765,88.19324749062152,95.95489455540911,100.0
2026,100.0,100.0,100.0,100.0,99.99952480065387,100.0,100.0,100.0,100.0,100.0,100.0,0.9033539569849551,65.15505754664082,94.02484342181545,89.78368925764359,0.23142208156321578,92.99461123941494,95.99359431281422,82.39148822931219,92.69381005331738,92.59781978539998,89.14882293121966,82.43330577177126,82.9408186734335,81.81697221984624,83.3974852450603,81.38976800767922,81.20586586072858,29.603493665592715,32.579667170377974,29.91522443665118,29.919501230766304,29.77456543019797,31.482907079519855,31.43396154686891,30.57907792318878,30.759653674716542,30.245963181554664,29.98983073399291,29.647687204782407,0.0,77.5601364772522,26.514222716429543,0.21241410771818775,32.0550470922552,14.78772845208565,0.13638221233807582,0.11262224503179084,99.99952480065387,87.37062697801727,99.99952480065387,100.0,99.95628166015644,88.2492705690037,99.95628166015644,95.99929670496773,83.72537279388703,95.99929670496773,95.7084747051388,21.487088833765764,4.062954409374733,0.25138045410049514,3.973616932303101,4.041570438799076,4.445014683659795,2.2182305477147666,99.9833680228856,36.97573632138682,33.74105437230918,21.72183731075186,12.478734829260874,1.4550603978368926,10.561305467643676,0.8605860158336422,0.8605860158336422,100.0,0.7826533230690275,95.86861688478317,89.2034708560241,12.875526283275834,12.130413708550737,83.00972257862173,0.1705965652591262,0.15396458814472672,87.90997823586994,79.48231783233066,87.85437991237323,100.0
```

### `outputs/tables/eda_01_preenchimento_por_ano_notificacao.csv`

- Git: `ignored` · `12.9 KB` · modified `2026-10-14 22:27 UTC` · 9 rows

```csv
ano_notificacao,nu_notific,dt_notific,dt_sin_pri,sem_pri,hospital,dt_interna,cs_sexo,nu_idade_n,tp_idade,cs_gestant,cs_raca,cs_etinia,cs_escol_n,cs_zona,ave_suino,out_anim,febre,tosse,garganta,dispneia,desc_resp,saturacao,diarreia,vomito,dor_abd,fadiga,perd_olft,perd_pala,puerpera,cardiopati,hematologi,sind_down,hepatica,asma,diabetes,neurologic,pneumopati,imunodepre,renal,obesidade,tabag,outro_sin,outro_des,obes_imc,out_morbi,morb_desc,out_antiv,out_trat,sg_uf_not,co_regiona,co_mun_not,co_pais,sg_uf,co_rg_resi,co_mun_res,sg_uf_inte,co_rg_inte,co_mu_inte,vacina,dt_ut_dose,mae_vac,dt_vac_mae,m_amamenta,dt_doseuni,dt_1_dose,dt_2_dose,vacina_cov,dose_1_cov,dose_2_cov,dose_ref,dose_2ref,dose_adic,dos_re_bi,pac_cocbo,pac_dscbo,pov_ct,tp_pov_ct,estrang,antiviral,tp_antivir,dt_antivir,trat_cov,tipo_trat,dt_trt_cov,evolucao,dt_evoluca,dt_encerra,dt_digita
2018,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,33.33333333333333,0.0,66.66666666666666,100.0,33.33333333333333,0.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,66.66666666666666,33.33333333333333,0.0,0.0,0.0,0.0,0.0,100.0,66.66666666666666,100.0,66.66666666666666,100.0,66.66666666666666,100.0,100.0,66.66666666666666,100.0,100.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,100.0,66.66666666666666,66.66666666666666,0.0,0.0,0.0,100.0,100.0,100.0,66.66666666666666
2019,100.0,100.0,100.0,100.0,99.44072048361228,97.31874820084715,100.0,100.0,100.0,100.0,96.25570588477197,0.5901221367767406,92.26467080643171,97.46062425463667,96.44076160710614,0.0,99.57642801332402,99.50446189908294,97.50174774848871,99.13435045441462,99.0150923222437,98.16177982481392,97.01854669572727,97.09668133404614,0.2570218365752354,0.48320105276144265,0.25290948719003165,0.25085331249742976,37.4470535016655,38.35999506518073,37.52107579059917,37.63827774807748,37.397705309043054,37.967265698893776,37.983715096434594,37.91380515688613,37.983715096434594,37.724637085166755,37.31545832133898,37.3401324176502,0.0,91.90689640991899,21.916766048443474,1.4968951762141711,37.73286178393717,17.56590039889789,0.2755274088086524,0.0,99.91364066291072,89.90006990993955,99.91364066291072,99.99383147592219,99.92597771106632,91.12760620142288,99.92597771106632,94.2200929390961,84.84599251552412,94.2200929390961,80.96804704527698,16.437060492659455,12.637249660731175,2.2535674630916644,11.32129785746597,0.49142575153185014,0.6147962330879632,0.42974051075379366,1.2624912612575565,0.09664021055228852,0.07196611424106593,0.0246740963112226,0.008224698770407534,0.0020561746926018834,0.00616852407780565,0.016449397540815067,0.016449397540815067,1.6552206275445163,0.0,0.43796520952420115,98.60385738372332,60.76201834107826,60.75996216638566,0.19328042110457705,0.0,0.0,94.18925031870707,84.08109552987622,96.41814368548752,65.41925401982152
2020,100.0,100.0,100.0,100.0,97.62462493047013,92.57077247566346,100.0,100.0,100.0,100.0,96.22924005929733,0.16321563527442426,70.38589399079203,89.47324438734073,82.38846713968734,0.03638620562384498,87.15941249335168,89.1636134461828,75.65588747087145,89.04044004676237,83.85714671214072,84.30483631865611,74.57161336261639,73.65551664494811,44.04228111912826,45.22570328529136,44.52365843276429,44.42555495492202,40.46955614922523,51.825360140739754,40.76465001780139,40.58863827672145,40.669854376833996,41.51935911531032,48.47043011454691,41.87573501441085,41.91394923514977,41.21390649441541,41.558269722759746,41.63287014912251,0.0,74.39577571821408,31.333310700765242,2.2831038303880526,47.7880581865916,26.240112396815075,0.6676607586959115,0.0010445800657563151,99.50965670746622,86.08401731565556,99.50965670746622,100.0,99.99033763439175,86.75637868464737,99.99033763439175,88.37861152676693,76.75583028011285,88.37861152676693,79.22016875190963,8.992093399385613,0.7400849765883493,0.04866002139648168,0.5538885798672861,0.010358752318750126,0.010271703979937099,0.007747302154359337,12.441296776512965,2.1529665638625786,2.0264853275672516,1.1856854229722307,0.47232428639948054,0.03656030230147103,0.10619897335189205,1.9161950822911473,1.9161950822911473,22.373773380095702,0.0348193355252105,5.833283280538516,86.34638100883801,14.819022151190778,14.513047240262992,1.01393905049413,0.01627803935803591,0.0007834350493172365,93.64120589804725,87.27240123713099,94.05564303913606,100.0
2021,100.0,100.0,100.0,100.0,97.37247551264886,93.65924881967445,100.0,100.0,100.0,100.0,100.0,0.0911563667112959,64.92667183426116,88.79870340356564,81.27539990134592,0.08670283982806004,82.16294834754422,86.47542808822493,68.93991966739482,87.07716158128392,79.97491367768303,83.38654076527376,67.72816573884856,66.65869917553378,65.36819110703968,69.64098372207738,66.20753999013459,66.16734550066944,33.59069832992742,44.2212670002114,33.579310830808254,33.4677471636953,33.46915650764569,34.28753435275879,40.999506729617366,34.3697272919456,34.40039461630611,33.9005285039814,34.15776196180678,35.951744063138605,0.0,69.13209780847016,30.772856035515467,1.265703614967233,41.53697413853851,23.698287647100276,0.3354802339510958,0.0009583538862659432,99.7614262560778,88.15057430765978,99.7614262560778,100.0,99.985568317948,88.5567472341625,99.985568317948,87.46179973222465,77.66071453738284,87.46179973222465,72.47043901064055,4.271552392361356,0.9292086533718553,0.03196392079486999,0.7408075540835741,0.005524628285533084,0.005130011979423578,0.004115284335141992,73.15521104925658,20.068775984779087,13.424339370023256,1.929617363117469,0.4672820801916708,0.029652596716228597,0.08726657740821649,2.418659713903178,2.418659713903178,92.85879782961032,0.2788246071453738,71.69479247410331,81.77904305545769,2.246043266859277,1.9292227468113592,1.0788809809033895,0.007328588542033683,0.002987809174829117,91.9290254386583,85.79899936579523,92.46553449369318,100.0
2022,100.0,100.0,100.0,100.0,96.70646144551846,92.8628556129174,100.0,100.0,100.0,100.0,100.0,0.1766050637082601,62.066811291739896,89.61239565026362,82.86364510105449,0.08478416080843584,80.18453427065026,86.0090688159051,67.90078536906854,82.38840756810193,76.91262082601055,77.92848610500879,65.49318980667839,66.070545913884,64.6154849516696,67.1063200241652,63.69676103910369,63.64269826449912,33.58293744507909,42.93047698813709,33.840379228910365,33.69295090070299,33.663774165202106,35.000411906854126,39.695291904657296,35.47393316124781,35.2690095013181,34.50183298550088,34.64617201230229,34.14862285808436,0.0,67.07285259226714,28.337818541300525,0.40641476274165206,41.89350148286468,24.914357699912127,0.22037016695957823,0.10263345782073813,99.91281304920913,89.4242915202109,99.91281304920913,100.0,99.97734512302284,89.96388949912127,99.97734512302284,89.16358880711776,79.88573017355009,89.16358880711776,59.630038993848856,3.372830623901582,2.681685248242531,0.10434973637961337,2.3605695298769773,0.02008045913884007,0.019565575571177503,0.01596139059753954,99.83026005052724,56.67924126757469,52.8512535698594,27.512631810193323,4.705177669156415,0.07757579086115993,0.1515473967486819,1.5228539652899824,1.5228539652899824,100.0,0.24886039103690685,90.75063159050967,79.99591525702988,3.612766366432337,3.2717418167838312,16.454820683216166,0.17145622803163446,0.14073484182776802,91.92233496265378,85.64281497144113,91.87101823374341,100.0
2023,100.0,100.0,100.0,100.0,97.21502340153947,94.23277762735466,100.0,100.0,100.0,100.0,100.0,0.36253925164303075,64.09701001817972,91.9323588259495,84.40940562551206,0.31225495194860453,85.74703832507569,90.81450016351188,71.88685680930294,86.66692453487023,83.67483288382218,81.57766111195114,71.23386419019421,72.03454496225162,70.4089203644381,72.3875899754908,69.50028658534441,69.43347527805811,28.86142983230362,34.5045238287802,29.35337203700643,29.212365014786396,29.152234838228726,31.02470963454215,32.43372494136429,30.5918426910188,30.48459296090132,30.080208732589504,29.68672529651913,29.133597999880443,0.0,70.3864155030364,27.978114022286842,0.2380592370148708,34.35331929123752,19.025047207463174,0.29256319822211596,0.22575189093581544,99.94268293111755,87.35261953070331,99.94268293111755,100.0,99.97573694630128,88.43355615490377,99.97573694630128,91.80858208824016,80.14719585910551,91.80858208824016,54.84153412827067,3.6004261858127946,6.000007032769188,0.2162576525319727,5.597732635213778,0.11111775317089981,0.11393086084611247,0.07982193028415904,99.98206643857051,49.91437603513572,45.54104851555824,30.461736461040218,17.568912347081227,1.777884050734397,7.195929433193967,0.8154495873522679,0.8154495873522679,100.0,0.35199009786098323,91.85394344950296,81.14936546840002,5.872713910465816,5.345256221363443,74.88422303724202,0.42020795898489005,0.318584444217833,94.98774539968986,88.15330030276071,94.46169426442509,100.0
2024,100.0,100.0,100.0,100.0,97.84074869934716,94.31995501249446,100.0,100.0,100.0,100.0,100.0,0.4495026422711242,62.2011850185648,91.64677359888871,84.81113068348981,0.23275820333011815,89.38287421001866,93.43100488233608,75.42557509896879,88.75237878883804,87.85039419929316,84.63497927520957,75.60135409412369,76.31787694725513,74.68894193706963,76.29515974661011,73.85846066758776,73.72178505059233,29.311892268331107,34.17039390136266,29.823215489406707,29.713353617434894,29.591574525452575,31.274881851935987,32.32918340974009,30.82612403591552,30.861130869696375,30.412745466801233,29.969946260786017,29.627326185484083,0.0,72.56097333894435,26.708724522287064,0.21413754706370872,33.44009176259408,17.243100115820482,0.191047933293361,0.24914438084455848,99.99776552124803,87.76995296422227,99.99776552124803,100.0,99.97132418934973,88.7162547156812,99.97132418934973,92.05642803674972,80.71197941300244,92.05642803674972,76.36591824042247,13.129424733445305,5.457341938559282,0.2584547089777632,5.163135569550013,0.5552679698643299,0.5422335104778433,0.4327440516313557,99.98510347498687,46.23211020449205,42.062945266442966,20.499852896815497,12.054268040622823,1.928355162949363,9.806010003016546,0.7723848219306642,0.7723848219306642,100.0,0.43833024851127855,93.60194250686172,81.12870970024467,8.117861305903865,7.524234784130732,75.59725754974508,0.3593786659417024,0.3202752877822426,94.41789966445577,87.87832518369278,93.96094875967809,100.0
2025,100.0,100.0,100.0,100.0,97.96090971578852,94.57547592719882,100.0,100.0,100.0,100.0,100.0,0.6057798631242342,64.59131526254446,93.33552493948179,87.77591823316698,0.23699231941663432,91.83736290009264,95.40121335285855,81.06243088969248,91.89593855533307,91.33379157825529,88.02695675562595,80.86160007172529,81.40312602731538,80.15450823346583,81.68883177430442,79.54215355189623,79.41065718298915,30.596515346223963,34.12569857445982,30.975762828367355,30.975463972983476,30.8054152595559,32.46555691700786,32.90427662054332,31.674785571262063,31.789247183288005,31.45034517796838,31.09321299423209,30.755805265831864,0.0,75.22010699022744,25.486387137264277,0.2354980424972356,33.21658049669765,16.27835390454559,0.18439377185379993,0.17931323032784435,99.99671259077732,87.32434774812468,99.99671259077732,100.0,99.96772361854099,88.33926063178028,99.96772361854099,91.51669107318968,79.39870296763397,91.51669107318968,93.76318699381369,26.75054541107558,5.076357550581274,0.28600460237291175,4.937688652461074,1.840949164699202,1.885777472281163,1.2151459908550253,99.992528615403,44.611936284032154,40.5370431248319,22.161620991602163,12.955082035802876,1.8463285616090372,10.927049400794955,0.8666806132512478,0.8666806132512478,100.0,0.525387764860584,95.04587430142554,86.04883296972595,11.776097546397299,10.798541585726667,79.98864349541257,0.27345267624996267,0.2495442455395834,95.45171991273422,86.43674725800186,95.26732614088043,100.0
2026,100.0,100.0,100.0,100.0,97.635766025115,93.91021233748664,100.0,100.0,100.0,100.0,100.0,0.8791579246195268,64.71791095753694,93.35397417529043,88.68183975550362,0.2306569731595126,92.532924065063,95.43299193144165,81.83665050589283,92.08003796968634,91.91325523524793,88.36113784859144,81.7155555949841,82.20437094964137,81.09366890965788,82.65193419179127,80.67804278686852,80.47887936196733,28.833895929347996,31.78364375917638,29.139959989886577,29.14395212980665,29.000235092684186,30.66495743935274,30.66407029714828,29.799550218902336,29.962784384522916,29.48461473631916,29.21137493734558,28.882245179491044,0.0,76.31108528541583,26.12057149700811,0.21646269788815797,31.24647915437605,14.514533607164559,0.14504775042915505,0.11355420217083698,99.98846715134202,87.79425397994171,99.98846715134202,100.0,99.95786074528816,88.61219909245352,99.95786074528816,91.47057127522255,79.88138908726374,91.47057127522255,95.51860115417202,21.43291208864325,3.947339238743274,0.2435205351241777,3.85285859396832,4.019197757304507,4.397563907506554,2.2072098046956437,99.98181358480858,37.60418376263623,34.2982483377173,21.976730259977025,12.568587181682286,1.4819710525498684,10.603123627701901,0.9306121724781874,0.9306121724781874,100.0,0.8095172615694433,95.5363439982612,87.3391500290539,12.552175050899784,11.804757743642517,81.06971607013746,0.17432344317632395,0.15524988578044116,86.7904525755956,77.36412308210944,86.69064907759389,100.0
```

### `outputs/tables/eda_01_resumo_datas.csv`

- Git: `ignored` · `1.8 KB` · modified `2026-10-14 22:27 UTC` · 19 rows

```csv
coluna,data_minima_convertida,data_maxima_convertida,quantidade_total,quantidade_original_preenchida,quantidade_ausente_original,quantidade_convertida,quantidade_formato_iso,quantidade_formato_br,quantidade_formato_nao_reconhecido,quantidade_data_calendario_invalida,datas_antes_1900,datas_depois_2026,datas_fora_faixa
dt_notific,2018-12-30,2026-09-28,4666910,4666910,0,4666910,4666910,0,0,0,0,0,0
dt_sin_pri,2018-12-30,2026-09-26,4666910,4666910,0,4666910,4666910,0,0,0,0,0,0
dt_interna,1917-09-01,2026-12-29,4666910,4362665,304245,4362568,4362665,0,0,0,21,76,97
dt_ut_dose,2009-03-02,2026-09-23,4666910,390041,4276869,390041,390041,0,0,0,0,0,0
dt_vac_mae,1955-11-16,2026-09-21,4666910,5645,4661265,5645,5645,0,0,0,0,0,0
dt_doseuni,2013-04-25,2026-09-18,4666910,17601,4649309,17601,17601,0,0,0,0,0,0
dt_1_dose,2012-08-06,2026-09-22,4666910,18626,4648284,18626,18626,0,0,0,0,0,0
dt_2_dose,2012-09-14,2026-09-22,4666910,10895,4656015,10895,10895,0,0,0,0,0,0
dose_1_cov,1900-01-01,2026-12-23,4666910,1211162,3455748,1211097,0,1211162,0,0,13,52,65
dose_2_cov,1900-04-20,2026-10-30,4666910,1024809,3642101,1024741,0,1024809,0,0,25,43,68
dose_ref,1982-02-09,2026-12-19,4666910,473540,4193370,473536,0,473540,0,0,0,4,4
dose_2ref,2020-04-12,2025-11-28,4666910,195149,4471761,195148,0,195149,0,0,0,1,1
dose_adic,2021-01-19,2026-05-24,4666910,21152,4645758,21152,0,21152,0,0,0,0,0
dos_re_bi,2021-03-27,2026-02-04,4666910,110916,4555994,110916,0,110916,0,0,0,0,0
dt_antivir,2018-12-30,2026-12-03,4666910,347712,4319198,347687,347712,0,0,0,6,19,25
dt_trt_cov,2020-03-15,2026-09-27,4666910,3833,4663077,3833,3833,0,0,0,0,0,0
dt_evoluca,2019-01-01,2026-09-27,4666910,4014740,652170,4014740,4014740,0,0,0,0,0,0
dt_encerra,2019-01-05,2026-09-27,4666910,4338057,328853,4338057,4338057,0,0,0,0,0,0
dt_digita,2019-01-18,2026-09-28,4666910,4650091,16819,4650091,4650091,0,0,0,0,0,0
```

### `outputs/tables/eda_01_resumo_primeira_passagem.csv`

- Git: `ignored` · `288 B` · modified `2026-10-10 18:58 UTC` · 10 rows

```csv
metrica,valor
versao_dados,dados-v2
arquivo,srag.parquet
linhas_parquet,4666910
colunas_parquet,198
linhas_carregadas,4666910
colunas_carregadas,88
memoria_mb,3847.05
data_minima_notificacao,2018-12-30 00:00:00
data_maxima_notificacao,2026-09-28 00:00:00
colunas_ausentes,0
```

### `outputs/tables/eda_01_status_colunas.csv`

- Git: `ignored` · `3.1 KB` · modified `2026-10-10 18:58 UTC` · 88 rows (first 60 shown)

```csv
coluna,grupo,existe_no_parquet
nu_notific,estrutura,True
dt_notific,estrutura,True
dt_sin_pri,estrutura,True
sem_pri,estrutura,True
hospital,estrutura,True
dt_interna,estrutura,True
cs_sexo,candidatas_principais,True
nu_idade_n,candidatas_principais,True
tp_idade,candidatas_principais,True
cs_gestant,candidatas_principais,True
cs_raca,candidatas_principais,True
cs_etinia,candidatas_principais,True
cs_escol_n,candidatas_principais,True
cs_zona,candidatas_principais,True
ave_suino,candidatas_principais,True
out_anim,candidatas_principais,True
febre,candidatas_principais,True
tosse,candidatas_principais,True
garganta,candidatas_principais,True
dispneia,candidatas_principais,True
desc_resp,candidatas_principais,True
saturacao,candidatas_principais,True
diarreia,candidatas_principais,True
vomito,candidatas_principais,True
dor_abd,candidatas_principais,True
fadiga,candidatas_principais,True
perd_olft,candidatas_principais,True
perd_pala,candidatas_principais,True
puerpera,candidatas_principais,True
cardiopati,candidatas_principais,True
hematologi,candidatas_principais,True
sind_down,candidatas_principais,True
hepatica,candidatas_principais,True
asma,candidatas_principais,True
diabetes,candidatas_principais,True
neurologic,candidatas_principais,True
pneumopati,candidatas_principais,True
imunodepre,candidatas_principais,True
renal,candidatas_principais,True
obesidade,candidatas_principais,True
tabag,candidatas_principais,True
outro_sin,complementares_texto,True
outro_des,complementares_texto,True
obes_imc,complementares_texto,True
out_morbi,complementares_texto,True
morb_desc,complementares_texto,True
out_antiv,complementares_texto,True
out_trat,complementares_texto,True
sg_uf_not,geografia,True
co_regiona,geografia,True
co_mun_not,geografia,True
co_pais,geografia,True
sg_uf,geografia,True
co_rg_resi,geografia,True
co_mun_res,geografia,True
sg_uf_inte,geografia,True
co_rg_inte,geografia,True
co_mu_inte,geografia,True
vacina,condicionais_vacinacao,True
dt_ut_dose,condicionais_vacinacao,True
... [28 more rows omitted]
```

### `outputs/tables/eda_01_status_periodos.csv`

- Git: `ignored` · `1.4 KB` · modified `2026-10-14 22:27 UTC` · 18 rows

```csv
ano_internacao,quantidade_registros_int,percentual,status_periodo,dentro_periodo_coorte,observacao
1917.0,4,8.570981655956511e-05,fora_periodo,False,Ano fora do período definido para a coorte
1918.0,1,2.1427454139891278e-05,fora_periodo,False,Ano fora do período definido para a coorte
1941.0,4,8.570981655956511e-05,fora_periodo,False,Ano fora do período definido para a coorte
2009.0,1,2.1427454139891278e-05,fora_periodo,False,Ano fora do período definido para a coorte
2011.0,1,2.1427454139891278e-05,fora_periodo,False,Ano fora do período definido para a coorte
2012.0,2,4.2854908279782555e-05,fora_periodo,False,Ano fora do período definido para a coorte
2016.0,1,2.1427454139891278e-05,fora_periodo,False,Ano fora do período definido para a coorte
2017.0,2,4.2854908279782555e-05,fora_periodo,False,Ano fora do período definido para a coorte
2018.0,11,0.00023570199553880403,fora_periodo,False,Ano fora do período definido para a coorte
2019.0,47545,1.0187683070811309,completo,True,
2020.0,1076375,23.063975949825473,completo,True,
2021.0,1657394,35.513733926730964,completo,True,
2022.0,536135,11.488008125290609,completo,True,
2023.0,265671,5.692653168799056,completo,True,
2024.0,253367,5.429009773061833,completo,True,
2025.0,315616,6.762847365815926,completo,True,
2026.0,210438,4.509150594290441,incompleto,True,Ano incompleto na versão atual dos dados
,304342,6.521274247842792,sem_data_valida,False,Registro sem dt_interna válida
```

### `outputs/tables/eda_01_tipos_memoria.csv`

- Git: `ignored` · `2.9 KB` · modified `2026-10-14 22:27 UTC` · 88 rows (first 60 shown)

```csv
coluna,tipo_pandas,memoria_mb
nu_notific,str,92.27620506286621
dt_notific,str,80.11294555664062
dt_sin_pri,str,80.11294555664062
dt_digita,str,79.95838165283203
dt_interna,str,77.7677812576294
dt_encerra,str,77.53310108184814
dt_evoluca,str,74.44970989227295
co_mun_res,str,62.86055564880371
co_mun_not,str,62.805665016174316
co_mu_inte,str,59.92469501495361
outro_des,str,55.45233154296875
co_rg_resi,str,51.882933616638184
co_regiona,str,51.770304679870605
co_rg_inte,str,50.11062526702881
morb_desc,str,48.541239738464355
dose_1_cov,str,47.712706565856934
dose_2_cov,str,45.935505867004395
sg_uf,str,45.061079025268555
sg_uf_not,str,45.04333209991455
sem_pri,str,44.50724792480469
sg_uf_inte,str,44.083008766174316
nu_idade_n,str,43.637024879455566
dose_ref,str,40.678194999694824
hospital,str,40.49917125701904
evolucao,str,40.28829383850098
cs_zona,str,40.17033290863037
cs_raca,str,40.1631965637207
tosse,str,40.12116241455078
dispneia,str,40.06807804107666
co_pais,str,40.06374645233154
cs_sexo,str,40.056535720825195
cs_gestant,str,40.056535720825195
tp_idade,str,40.056535720825195
febre,str,39.95220184326172
saturacao,str,39.883840560913086
dt_ut_dose,str,39.88188648223877
antiviral,str,39.872056007385254
ave_suino,str,39.86177349090576
desc_resp,str,39.84808349609375
dt_antivir,str,39.47820568084717
vacina,str,39.47382164001465
garganta,str,39.40254783630371
pov_ct,str,39.39747428894043
diarreia,str,39.35434532165527
outro_sin,str,39.34286880493164
vomito,str,39.336246490478516
vacina_cov,str,39.152587890625
cs_escol_n,str,39.0977144241333
fadiga,str,39.03894519805908
estrang,str,38.940918922424316
perd_olft,str,38.92895317077637
perd_pala,str,38.92551803588867
dor_abd,str,38.92202568054199
pac_dscbo,str,38.161781311035156
cardiopati,str,38.092695236206055
dose_2ref,str,38.0232515335083
out_morbi,str,37.9906644821167
diabetes,str,37.96665000915527
obesidade,str,37.748671531677246
pneumopati,str,37.74447536468506
... [28 more rows omitted]
```

### `outputs/tables/eda_01_volume_por_ano_internacao.csv`

- Git: `ignored` · `647 B` · modified `2026-10-14 22:27 UTC` · 18 rows

```csv
ano_internacao,quantidade_registros_int,percentual
1917.0,4,8.570981655956511e-05
1918.0,1,2.1427454139891278e-05
1941.0,4,8.570981655956511e-05
2009.0,1,2.1427454139891278e-05
2011.0,1,2.1427454139891278e-05
2012.0,2,4.2854908279782555e-05
2016.0,1,2.1427454139891278e-05
2017.0,2,4.2854908279782555e-05
2018.0,11,0.00023570199553880403
2019.0,47545,1.0187683070811309
2020.0,1076375,23.063975949825473
2021.0,1657394,35.513733926730964
2022.0,536135,11.488008125290609
2023.0,265671,5.692653168799056
2024.0,253367,5.429009773061833
2025.0,315616,6.762847365815926
2026.0,210438,4.509150594290441
,304342,6.521274247842792
```

### `outputs/tables/eda_01_volume_por_ano_notificacao.csv`

- Git: `ignored` · `333 B` · modified `2026-10-14 22:27 UTC` · 9 rows

```csv
ano_notificacao,quantidade_registros,percentual
2018,3,6.428236241967383e-05
2019,48634,1.0421028046394725
2020,1148787,24.61558075900328
2021,1773875,38.00962521239964
2022,582656,12.484834719332492
2023,284383,6.093603690664701
2024,268519,5.753678558189466
2025,334610,7.169840429749021
2026,225443,4.830669543659509
```

### `outputs/tables/eda_02_alvo_por_ano.csv`

- Git: `ignored` · `608 B` · modified `2026-10-14 23:22 UTC` · 8 rows

```csv
ano_internacao,quantidade_cura,quantidade_obito_srag,quantidade_total,percentual_cura,percentual_obito_srag
2019,38292,5221,43513,88.0012869717096,11.998713028290396
2020,705699,274113,979812,72.02391887423302,27.97608112576698
2021,1062924,417291,1480215,71.80875751157771,28.19124248842229
2022,389547,86433,475980,81.84104374133368,18.158956258666333
2023,217667,23037,240704,90.42932398298325,9.570676017016751
2024,210358,19120,229478,91.66804661013256,8.331953389867438
2025,268686,21227,289913,92.67814827206783,7.321851727932173
2026,165778,9743,175521,94.44909725901745,5.55090274098256
```

### `outputs/tables/eda_02_auditoria_idade.csv`

- Git: `ignored` · `331 B` · modified `2026-10-14 23:22 UTC` · 3 rows

```csv
tipo_idade,quantidade_registros,quantidade_valor_informado,quantidade_idade_convertida,quantidade_idade_ausente,quantidade_nao_convertida,quantidade_tipo_invalido,percentual_convertido
1,26669,26669,26668,0,1,0,99.9962503280963
2,355242,355242,355227,0,15,0,99.995777526306
3,3533225,3533225,3533217,0,8,0,99.99977357796348
```

### `outputs/tables/eda_02_ausencia_por_desfecho.csv`

- Git: `ignored` · `4.2 KB` · modified `2026-10-14 23:28 UTC` · 32 rows

```csv
coluna,nome_amigavel,quantidade_cura,ausente_cura,percentual_ausente_cura,quantidade_obito,ausente_obito,percentual_ausente_obito,diferenca_pp_obito_menos_cura,diferenca_absoluta_pp
cardiopati,Doenca cardiovascular cronica,3058951,1824837,59.65564665795562,856185,331032,38.663606580353544,-20.992040077602077,20.992040077602077
diabetes,Diabetes mellitus,3058951,1898839,62.07484199648834,856185,366939,42.85744319276792,-19.21739880372042,19.21739880372042
out_morbi,Outro fator de risco?,3058951,1874080,61.26544688031943,856185,364372,42.557624812394515,-18.707822067924916,18.707822067924916
renal,Doenca renal cronica,3058951,2032866,66.45631133025668,856185,440595,51.460256837015365,-14.996054493241317,14.996054493241317
obesidade,Obesidade,3058951,2015083,65.87496824891932,856185,435685,50.88678264627388,-14.988185602645437,14.988185602645437
neurologic,Doenca neurologica cronica,3058951,2018213,65.9772909078962,856185,438174,51.177490846020426,-14.799800061875779,14.799800061875779
pneumopati,Outra pneumopatia cronica,3058951,2016957,65.93623108052401,856185,438583,51.225260895717625,-14.710970184806385,14.710970184806385
imunodepre,Imunodeficiencia ou imunodepressao,3058951,2031395,66.40822294963208,856185,446538,52.15438252246886,-14.253840427163219,14.253840427163219
hepatica,Doenca hepatica cronica,3058951,2047407,66.93167036673682,856185,453221,52.934938126689914,-13.99673224004691,13.99673224004691
hematologi,Doenca hematologica cronica,3058951,2042358,66.76661378361406,856185,452872,52.89417590824414,-13.872437875369926,13.872437875369926
puerpera,Puerpera ou parturiente,3058951,2047771,66.94356987084788,856185,454781,53.117141739226916,-13.826428131620965,13.826428131620965
sind_down,Sindrome de Down,3058951,2045025,66.85380053488925,856185,454593,53.09518386797246,-13.758616666916787,13.758616666916787
asma,Asma,3058951,2004879,65.5413898424656,856185,451326,52.713607456332454,-12.827782386133151,12.827782386133151
vacina_cov,Recebeu vacina contra COVID-19?,3058951,904011,29.55297420586338,856185,357156,41.71481630722332,12.161842101359944,12.161842101359944
dor_abd,Dor abdominal,3058951,1061739,34.709251635609725,856185,349829,40.85904331423699,6.149791678627267,6.149791678627267
perd_olft,Perda do olfato,3058951,1057820,34.58113582074378,856185,348117,40.65908652919637,6.07795070845259,6.07795070845259
perd_pala,Perda do paladar,3058951,1060020,34.65305590053584,856185,348634,40.71947067514614,6.066414774610301,6.066414774610301
fadiga,Fadiga,3058951,985594,32.21999960117047,856185,322940,37.718483738911566,5.4984841377410945,5.4984841377410945
tosse,Tosse,3058951,263141,8.60232805298287,856185,118414,13.830422163434305,5.228094110451435,5.228094110451435
febre,Febre,3058951,379907,12.419518978891784,856185,144159,16.83736575623259,4.417846777340806,4.417846777340806
vomito,Vomito,3058951,782772,25.589556681359067,856185,256373,29.943645357019804,4.354088675660737,4.354088675660737
garganta,Dor de garganta,3058951,750713,24.54151766406196,856185,243313,28.41827408795996,3.8767564238980015,3.8767564238980015
diarreia,Diarreia,3058951,774678,25.32495616961501,856185,249086,29.092544251534424,3.7675880819194134,3.7675880819194134
outro_sin,Apresentou outros sintomas?,3058951,778040,25.43486312791542,856185,249920,29.189953105929213,3.7550899780137925,3.7550899780137925
saturacao,Saturacao de oxigenio abaixo de 95%?,3058951,461890,15.09962075234288,856185,104118,12.16068957059514,-2.938931181747739,2.938931181747739
dispneia,Dispneia,3058951,339613,11.102270026554855,856185,79534,9.289347512511899,-1.8129225140429561,1.8129225140429561
cs_escol_n,Escolaridade,3058951,1001269,32.73243016968889,856185,266269,31.09947032475458,-1.6329598449343088,1.6329598449343088
vacina,Recebeu vacina contra influenza?,3058951,720472,23.552910785429386,856185,192208,22.449353819560024,-1.1035569658693625,1.1035569658693625
desc_resp,Desconforto respiratorio,3058951,473204,15.469486108146224,856185,129163,15.08587513212682,-0.38361097601940486,0.38361097601940486
sg_uf,UF de residencia,3058951,562,0.018372311292335183,856185,195,0.02277545156712626,0.004403140274791079,0.004403140274791079
nu_idade_n,Idade informada,3058951,0,0.0,856185,0,0.0,0.0,0.0
tp_idade,"Unidade da idade: dias, meses ou anos",3058951,0,0.0,856185,0,0.0,0.0,0.0
```

### `outputs/tables/eda_02_cluster_ano_sensibilidade.csv`

- Git: `ignored` · `1.6 KB` · modified `2026-10-14 23:29 UTC` · 32 rows

```csv
matriz,cluster_rotulo,ano_internacao,quantidade,percentual_dentro_cluster
nucleo,Cluster 1,2019,6704,16.857775095554214
nucleo,Cluster 1,2020,1685,4.237075035204184
nucleo,Cluster 1,2021,1761,4.428183464091732
nucleo,Cluster 1,2022,3722,9.35928384630859
nucleo,Cluster 1,2023,6079,15.286159726413196
nucleo,Cluster 1,2024,6349,15.965097565882116
nucleo,Cluster 1,2025,6422,16.148662240997787
nucleo,Cluster 1,2026,7046,17.71776302554818
nucleo,Cluster 2,2019,3296,8.192483595148142
nucleo,Cluster 2,2020,8315,20.66762775899781
nucleo,Cluster 2,2021,8239,20.47872340425532
nucleo,Cluster 2,2022,6278,15.604493935175977
nucleo,Cluster 2,2023,3921,9.745973354543647
nucleo,Cluster 2,2024,3651,9.074865778484789
nucleo,Cluster 2,2025,3578,8.893418174587394
nucleo,Cluster 2,2026,2954,7.3424139988069195
ampliada,Cluster 1,2019,6452,16.627580341726155
ampliada,Cluster 1,2020,1368,3.5255006056232765
ampliada,Cluster 1,2021,1782,4.592428420482952
ampliada,Cluster 1,2022,3623,9.336906940185036
ampliada,Cluster 1,2023,5994,15.447259232533566
ampliada,Cluster 1,2024,6263,16.14050460015978
ampliada,Cluster 1,2025,6329,16.31059454165915
ampliada,Cluster 1,2026,6992,18.01922531763008
ampliada,Cluster 2,2019,3548,8.612277593028619
ampliada,Cluster 2,2020,8632,20.952982013253393
ampliada,Cluster 2,2021,8218,19.948054469985678
ampliada,Cluster 2,2022,6377,15.47928247202466
ampliada,Cluster 2,2023,4006,9.724009029783721
ampliada,Cluster 2,2024,3737,9.071048862781272
ampliada,Cluster 2,2025,3671,8.910843022550186
ampliada,Cluster 2,2026,3008,7.30150253659247
```

### `outputs/tables/eda_02_cluster_desfecho_sensibilidade.csv`

- Git: `ignored` · `365 B` · modified `2026-10-14 23:29 UTC` · 4 rows

```csv
matriz,cluster_rotulo,quantidade_registros,quantidade_obitos,proporcao_obito,percentual_obito
nucleo,Cluster 1,39768,1039,0.02612653389660028,2.612653389660028
nucleo,Cluster 2,40232,10762,0.267498508649831,26.7498508649831
ampliada,Cluster 1,38803,964,0.024843439940210807,2.4843439940210805
ampliada,Cluster 2,41197,10837,0.26305313493701,26.305313493701
```

### `outputs/tables/eda_02_comorbidades_por_ano.csv`

- Git: `ignored` · `14.8 KB` · modified `2026-10-14 23:26 UTC` · 104 rows (first 60 shown)

```csv
ano_internacao,grupo_clinico,coluna,nome_amigavel,quantidade_total,quantidade_sim,quantidade_nao,quantidade_ignorado,quantidade_ausente,quantidade_inesperado,quantidade_respostas_validas,percentual_sim_validos,percentual_nao_validos,percentual_sem_resposta_valida
2019,comorbidades,asma,Asma,43513,2504,14109,259,26641,0,16613,15.072533558056945,84.92746644194305,61.820605336336264
2020,comorbidades,asma,Asma,979812,38401,380622,11662,549127,0,419023,9.164413409287796,90.8355865907122,57.23434699717905
2021,comorbidades,asma,Asma,1480215,46306,480519,10731,942659,0,526825,8.789636027143738,91.21036397285626,64.40888654688676
2022,comorbidades,asma,Asma,475980,23147,151272,2484,299077,0,174419,13.270916585922404,86.72908341407759,63.3558132694651
2023,comorbidades,asma,Asma,240704,16950,57824,748,165182,0,74774,22.66830716559232,77.33169283440769,68.93528981653816
2024,comorbidades,asma,Asma,229478,15656,56016,515,157291,0,71672,21.84395579863824,78.15604420136177,68.76737639337975
2025,comorbidades,asma,Asma,289913,21168,73108,480,195157,0,94276,22.453222453222455,77.54677754677755,67.48127886641855
2026,comorbidades,asma,Asma,175521,13998,40239,213,121071,0,54237,25.808949610044802,74.1910503899552,69.09942400054693
2019,comorbidades,cardiopati,Doenca cardiovascular cronica,43513,4699,12134,191,26489,0,16833,27.915404265431,72.084595734569,61.31500930756326
2020,comorbidades,cardiopati,Doenca cardiovascular cronica,979812,324584,199994,6493,448741,0,524578,61.87525973258505,38.12474026741495,46.46136197556266
2021,comorbidades,cardiopati,Doenca cardiovascular cronica,1480215,421658,252532,6646,799379,0,674190,62.54290333585488,37.457096664145126,54.453238212016494
2022,comorbidades,cardiopati,Doenca cardiovascular cronica,475980,123882,88039,1718,262341,0,211921,58.45668904922117,41.543310950778825,55.4769107945712
2023,comorbidades,cardiopati,Doenca cardiovascular cronica,240704,39973,42468,633,157630,0,82441,48.48679661818755,51.513203381812446,65.75004985376229
2024,comorbidades,cardiopati,Doenca cardiovascular cronica,229478,36489,41603,390,150996,0,78092,46.72565691748194,53.27434308251806,65.9697225877862
2025,comorbidades,cardiopati,Doenca cardiovascular cronica,289913,42965,55616,441,190891,0,98581,43.58344914334405,56.416550856655945,65.99635062932673
2026,comorbidades,cardiopati,Doenca cardiovascular cronica,175521,22336,33575,208,119402,0,55911,39.9492049864964,60.0507950135036,68.1456919684824
2019,comorbidades,diabetes,Diabetes mellitus,43513,3257,13412,191,26653,0,16669,19.539264502969584,80.46073549703041,61.691908165375864
2020,comorbidades,diabetes,Diabetes mellitus,979812,227313,262733,8005,481761,0,490046,46.38605355415614,53.613946445843865,49.98571154466367
2021,comorbidades,diabetes,Diabetes mellitus,1480215,289134,337285,7860,845936,0,626419,46.15664595103278,53.84335404896723,57.68053965133444
2022,comorbidades,diabetes,Diabetes mellitus,475980,77827,118313,2014,277826,0,196140,39.67931069644132,60.32068930355868,58.79238623471574
2023,comorbidades,diabetes,Diabetes mellitus,240704,24216,53370,637,162481,0,77586,31.211816564844174,68.78818343515583,67.76704998670566
2024,comorbidades,diabetes,Diabetes mellitus,229478,21613,52032,408,155425,0,73645,29.347545658225272,70.65245434177473,67.90759898552366
2025,comorbidades,diabetes,Diabetes mellitus,289913,26275,68840,455,194343,0,95115,27.624454607580297,72.37554539241971,67.19188170244178
2026,comorbidades,diabetes,Diabetes mellitus,175521,13487,40483,198,121353,0,53970,24.989809153233278,75.01019084676672,69.25154255046405
2019,comorbidades,hematologi,Doenca hematologica cronica,43513,441,16002,246,26824,0,16443,2.681992337164751,97.31800766283524,62.21129317675178
2020,comorbidades,hematologi,Doenca hematologica cronica,979812,9316,401644,12385,556467,0,410960,2.2668872883005644,97.73311271169943,58.057259964156394
2021,comorbidades,hematologi,Doenca hematologica cronica,1480215,9016,506018,11745,953436,0,515034,1.7505640404322822,98.24943595956772,65.20546001763257
2022,comorbidades,hematologi,Doenca hematologica cronica,475980,4832,163535,2825,304788,0,168367,2.869921065291892,97.13007893470811,64.62729526450691
2023,comorbidades,hematologi,Doenca hematologica cronica,240704,2340,68077,874,169413,0,70417,3.3230611926097393,96.67693880739026,70.74539683594789
2024,comorbidades,hematologi,Doenca hematologica cronica,229478,2444,65639,586,160809,0,68083,3.589736057459278,96.41026394254072,70.33136074046314
2025,comorbidades,hematologi,Doenca hematologica cronica,289913,2595,87107,576,199635,0,89702,2.8929120866870304,97.10708791331297,69.05899356013701
2026,comorbidades,hematologi,Doenca hematologica cronica,175521,1459,49938,266,123858,0,51397,2.8386870829036717,97.16131291709632,70.71746400715584
2019,comorbidades,hepatica,Doenca hepatica cronica,43513,335,16071,236,26871,0,16406,2.0419358771181275,97.95806412288186,62.296325236136326
2020,comorbidades,hepatica,Doenca hepatica cronica,979812,10167,399852,12280,557513,0,410019,2.4796411873596105,97.5203588126404,58.15329879609558
2021,comorbidades,hepatica,Doenca hepatica cronica,1480215,10305,503010,11758,955142,0,513315,2.007539230297186,97.99246076970282,65.32159179578643
2022,comorbidades,hepatica,Doenca hepatica cronica,475980,4128,163434,2804,305614,0,167562,2.463565724925699,97.5364342750743,64.7964200176478
2023,comorbidades,hepatica,Doenca hepatica cronica,240704,1552,68386,866,169900,0,69938,2.219108353112757,97.78089164688724,70.94439643711779
2024,comorbidades,hepatica,Doenca hepatica cronica,229478,1308,66259,565,161346,0,67567,1.935856261192594,98.0641437388074,70.55621889680056
2025,comorbidades,hepatica,Doenca hepatica cronica,289913,1429,87741,591,200152,0,89170,1.6025569137602331,98.39744308623976,69.24249688699713
2026,comorbidades,hepatica,Doenca hepatica cronica,175521,774,50376,281,124090,0,51150,1.5131964809384164,98.48680351906158,70.85818790913908
2019,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,43513,1684,14839,253,26737,0,16523,10.19185377957998,89.80814622042001,62.02744007537977
2020,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,979812,32709,382862,11964,552277,0,415571,7.870857206109185,92.12914279389082,57.586659481614845
2021,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,1480215,30940,489082,11680,948513,0,520022,5.949748279880467,94.05025172011953,64.86848194350145
2022,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,475980,16502,155125,2784,301569,0,171627,9.615037261037017,90.38496273896298,63.94239253750158
2023,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,240704,7041,65094,857,167712,0,72135,9.76086504470784,90.23913495529216,70.03165713905875
2024,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,229478,6330,63087,606,159455,0,69417,9.11880375124249,90.88119624875752,69.75004139830398
2025,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,289913,6855,84080,622,198356,0,90935,7.5383515698026065,92.4616484301974,68.63369355634276
2026,comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,175521,3915,47966,326,123314,0,51881,7.546115148127446,92.45388485187256,70.4417135271563
2019,comorbidades,neurologic,Doenca neurologica cronica,43513,2051,14585,211,26666,0,16636,12.328684779995191,87.67131522000481,61.767747569691814
2020,comorbidades,neurologic,Doenca neurologica cronica,979812,49276,373606,11476,545454,0,422882,11.652423134586007,88.34757686541398,56.840495931872645
2021,comorbidades,neurologic,Doenca neurologica cronica,1480215,48912,478226,11203,941874,0,527138,9.278784682568892,90.72121531743112,64.38774097006178
2022,comorbidades,neurologic,Doenca neurologica cronica,475980,29637,146898,2555,296890,0,176535,16.78817231710426,83.21182768289574,62.91125677549477
2023,comorbidades,neurologic,Doenca neurologica cronica,240704,12286,61158,781,166479,0,73444,16.728391699798486,83.27160830020152,69.48783568199947
2024,comorbidades,neurologic,Doenca neurologica cronica,229478,11012,59366,523,158577,0,70378,15.646935121771008,84.35306487822899,69.33126487070655
2025,comorbidades,neurologic,Doenca neurologica cronica,289913,12458,79193,547,197715,0,91651,13.592868599360619,86.40713140063939,68.38672291342576
2026,comorbidades,neurologic,Doenca neurologica cronica,175521,7613,44927,249,122732,0,52540,14.489912447658925,85.51008755234108,70.06625987773543
2019,comorbidades,obesidade,Obesidade,43513,667,15574,372,26900,0,16241,4.106889969829444,95.89311003017056,62.67552225771609
2020,comorbidades,obesidade,Obesidade,979812,49907,365428,16830,547647,0,415335,12.016083402554564,87.98391659744543,57.610745734896085
2021,comorbidades,obesidade,Obesidade,1480215,124189,425917,13021,917088,0,550106,22.575467273580003,77.42453272642,62.83607448917894
2022,comorbidades,obesidade,Obesidade,475980,16485,152772,3394,303329,0,169257,9.739626721494531,90.26037327850547,64.44031261817723
... [44 more rows omitted]
```

### `outputs/tables/eda_02_comparacao_original_sensibilidade.csv`

- Git: `ignored` · `825 B` · modified `2026-10-14 23:29 UTC` · 2 rows

```csv
matriz,k_original,silhouette_original,ari_estabilidade_original,menor_cluster_percentual_original,maior_cluster_percentual_original,k_sem_indicadores_ausencia,indicadores_ausencia_excluidos,features_sensibilidade,componentes_pca_90,silhouette_sem_indicadores_ausencia,menor_cluster_percentual_sem_ausencia,maior_cluster_percentual_sem_ausencia,ari_original_vs_sem_ausencia,queda_silhouette,queda_silhouette_percentual,rotulo_matriz
ampliada,2,0.2935044765472412,0.9999797474460079,33.29125,66.70875000000001,2,28,69,30,0.16932816803455353,48.503750000000004,51.496249999999996,0.08798891737376612,0.12417630851268768,42.30814806420876,Ampliada
nucleo,2,0.36442187428474426,0.9999493687268458,33.28875,66.71125,2,26,31,15,0.23322749137878418,49.71,50.29,0.09417414798684123,0.13119438290596008,36.00068825820543,Núcleo
```

### `outputs/tables/eda_02_contadores_clinicos_por_ano.csv`

- Git: `ignored` · `1.2 KB` · modified `2026-10-14 23:26 UTC` · 8 rows

```csv
ano_internacao,quantidade_registros,sintomas_confirmados_media,sintomas_confirmados_mediana,sintomas_avaliados_media,comorbidades_confirmadas_media,comorbidades_confirmadas_mediana,comorbidades_avaliadas_media,quantidade_multimorbidade,percentual_multimorbidade
2019,43513,4.794015581550341,5.0,8.634132328269713,0.6506561257555213,0.0,4.938753935605451,6820,15.67347689196332
2020,979812,4.030769167962833,4.0,9.062353798483791,1.137412074969484,1.0,5.771504125281177,328202,33.49642584495801
2021,1480215,4.32198633306648,4.0,9.667717865310108,0.9781815479508045,1.0,4.845769026796783,418132,28.24805855906068
2022,475980,3.7105970839110887,4.0,9.457418378923483,0.9927139795789739,1.0,4.889522669019707,135639,28.49678557922602
2023,240704,3.994835981122042,4.0,9.974711679074714,0.7327422892847647,0.0,3.9753473145440044,47028,19.53768944429673
2024,229478,4.123950879822902,4.0,10.38484734920123,0.6940970376245218,0.0,3.9917203392046297,42437,18.492840272270108
2025,289913,4.193044120132591,4.0,10.934221645804087,0.6607568477439784,0.0,4.120194679093383,50429,17.394528703438617
2026,175521,4.279755698748298,4.0,11.056016089242883,0.6074714706502355,0.0,3.894890070134058,27357,15.586169176337874
```

### `outputs/tables/eda_02_dbscan_varredura_minima.csv`

- Git: `ignored` · `502 B` · modified `2026-10-14 23:30 UTC` · 3 rows

```csv
metodo,eps,min_samples,quantidade_registros,quantidade_clusters_sem_ruido,quantidade_ruido,percentual_ruido,silhouette_sem_ruido,calinski_harabasz_sem_ruido,davies_bouldin_sem_ruido,menor_cluster_percentual_sem_ruido,ari_dbscan_vs_kmeans,tempo_segundos
DBSCAN,1.401609,10,8000,1,220,2.75,,,,,0.0006927723173552484,0.7283188999863341
DBSCAN,1.479287,10,8000,1,100,1.25,,,,,2.9349417913744897e-05,2.0070788000011817
DBSCAN,1.656968,10,8000,1,54,0.675,,,,,-8.569456750579377e-06,1.4081339000258595
```

### `outputs/tables/eda_02_decisao_clustering.csv`

- Git: `ignored` · `706 B` · modified `2026-10-14 23:29 UTC` · 1 rows

```csv
status,matriz_principal_documentada,quantidade_clusters_documentada,usar_cluster_como_preditor_supervisionado,aplicar_clusters_na_coorte_completa,justificativa,encaminhamento,ari_nucleo_vs_ampliada_sem_ausencia
encerrar_como_exploratorio,nucleo,2,False,False,"A solução original foi dominada por indicadores de ausência. Sem esses indicadores, a concordância com a solução original foi baixa, o silhouette diminuiu e a composição dos grupos passou a acompanhar fortemente o período de internação.",Preservar o clustering como achado exploratório de qualidade e drift temporal. Prosseguir para a modelagem supervisionada com divisão temporal e avaliação por período.,0.9186733075232211
```

### `outputs/tables/eda_02_decisao_clustering.json`

- Git: `ignored` · `766 B` · modified `2026-10-14 23:29 UTC`

```json
{
  "status": "encerrar_como_exploratorio",
  "matriz_principal_documentada": "nucleo",
  "quantidade_clusters_documentada": 2,
  "usar_cluster_como_preditor_supervisionado": false,
  "aplicar_clusters_na_coorte_completa": false,
  "justificativa": "A solução original foi dominada por indicadores de ausência. Sem esses indicadores, a concordância com a solução original foi baixa, o silhouette diminuiu e a composição dos grupos passou a acompanhar fortemente o período de internação.",
  "encaminhamento": "Preservar o clustering como achado exploratório de qualidade e drift temporal. Prosseguir para a modelagem supervisionada com divisão temporal e avaliação por período.",
  "ari_nucleo_vs_ampliada_sem_ausencia": 0.9186733075232211
}
```

### `outputs/tables/eda_02_diagnostico_final_clustering.csv`

- Git: `ignored` · `534 B` · modified `2026-10-14 23:29 UTC` · 2 rows

```csv
matriz,silhouette_sem_indicadores_ausencia,ari_original_vs_sem_indicadores_ausencia,menor_cluster_percentual,nmi_cluster_ano,interpretacao
nucleo,0.23322749137878418,0.09417414798684123,49.71,0.06736268232984413,A partição mudou substancialmente após retirar os indicadores de ausência e permaneceu associada ao período.
ampliada,0.16932816803455353,0.08798891737376612,48.503750000000004,0.06904843374127206,A partição mudou substancialmente após retirar os indicadores de ausência e permaneceu associada ao período.
```

### `outputs/tables/eda_02_escolaridade_por_ano.csv`

- Git: `ignored` · `2.5 KB` · modified `2026-10-14 23:26 UTC` · 64 rows (first 60 shown)

```csv
ano_internacao,categoria_escolaridade,quantidade,percentual_ano,flag_ausente
2019,0,1804,4.145887435938685,False
2019,1,3999,9.190356904833038,False
2019,2,2207,5.0720474341001545,False
2019,3,3334,7.6620779996782575,False
2019,4,1489,3.42196584928642,False
2019,5,19192,44.1063590191437,False
2019,9,8264,18.992025371727987,False
2019,ausente,3224,7.409279985291752,True
2020,0,30829,3.146419925455087,False
2020,1,101136,10.321980134964667,False
2020,2,63870,6.518597445224186,False
2020,3,99791,10.18470890334064,False
2020,4,47085,4.805513710793499,False
2020,5,29043,2.9641400595216227,False
2020,9,334942,34.18431290900703,False
2020,ausente,273116,27.874326911693263,True
2021,0,42055,2.841141320686522,False
2021,1,136505,9.221971132571957,False
2021,2,95064,6.422310272494198,False
2021,3,160007,10.809713453788808,False
2021,4,67527,4.561972416169273,False
2021,5,40755,2.7533162412217145,False
2021,9,447177,30.21027350756478,False
2021,ausente,491125,33.17930165550275,True
2022,0,26567,5.581537039371402,False
2022,1,42951,9.02369847472583,False
2022,2,22096,4.642211857641077,False
2022,3,25812,5.422916929282743,False
2022,4,11178,2.3484180007563342,False
2022,5,42247,8.875793100550442,False
2022,9,134761,28.312324047228877,False
2022,ausente,170368,35.7931005504433,True
2023,0,17407,7.231703669236905,False
2023,1,19815,8.232102499335284,False
2023,2,7949,3.3023963041744215,False
2023,3,9170,3.8096583355490563,False
2023,4,3984,1.6551449082690775,False
2023,5,42260,17.55683328901888,False
2023,9,55948,23.243485775059824,False
2023,ausente,84171,34.968675219356555,True
2024,0,17084,7.444722369900382,False
2024,1,17266,7.524032804887614,False
2024,2,7909,3.446517748978115,False
2024,3,9419,4.104532896399655,False
2024,4,3620,1.5774932673284585,False
2024,5,36713,15.998483514759585,False
2024,9,51658,22.51109038774959,False
2024,ausente,85809,37.393127009996604,True
2025,0,26708,9.212418898083218,False
2025,1,24893,8.586369014152522,False
2025,2,10763,3.7124930582623064,False
2025,3,12764,4.402700120380942,False
2025,4,4270,1.4728556497983878,False
2025,5,49580,17.101682228806574,False
2025,9,60019,20.702417621838276,False
2025,ausente,100916,34.80906340867777,True
2026,0,18721,10.665960198494767,False
2026,1,16456,9.375516319984504,False
2026,2,7134,4.064470918009811,False
2026,3,7760,4.4211233983398,False
... [4 more rows omitted]
```

### `outputs/tables/eda_02_faixa_etaria_por_ano.csv`

- Git: `ignored` · `3.1 KB` · modified `2026-10-14 23:22 UTC` · 70 rows (first 60 shown)

```csv
ano_internacao,faixa_etaria,quantidade,percentual_ano
2019,1 a 4 anos,8211,18.870222692069035
2019,10 a 19 anos,1736,3.9896122997724817
2019,20 a 39 anos,4718,10.842736653413922
2019,40 a 59 anos,5323,12.233125732539701
2019,5 a 9 anos,2299,5.283478500677958
2019,60 a 79 anos,5611,12.894996897478913
2019,80 anos ou mais,2486,5.713235125135017
2019,Menor de 1 ano,13129,30.172592098912972
2020,1 a 4 anos,24466,2.4970096304188965
2020,10 a 19 anos,17292,1.7648283548272525
2020,20 a 39 anos,124732,12.7301972215078
2020,40 a 59 anos,273535,27.917090217306995
2020,5 a 9 anos,14382,1.4678326046221113
2020,60 a 79 anos,352938,36.02099178209697
2020,80 anos ou mais,153028,15.618098165770578
2020,Idade ausente ou inválida,4,0.00040824158103799506
2020,Menor de 1 ano,19435,1.9835437818683583
2021,1 a 4 anos,47421,3.203656225615873
2021,10 a 19 anos,19030,1.2856240478579126
2021,20 a 39 anos,213066,14.394260293268207
2021,40 a 59 anos,501489,33.879470212097566
2021,5 a 9 anos,17681,1.1944886384748161
2021,60 a 79 anos,474259,32.039872586077024
2021,80 anos ou mais,164098,11.086092223089214
2021,Idade ausente ou inválida,8,0.0005404620274757383
2021,Menor de 1 ano,43163,2.9159953114919115
2022,1 a 4 anos,57955,12.175931761838733
2022,10 a 19 anos,13032,2.7379301651329886
2022,20 a 39 anos,35546,7.4679608386907015
2022,40 a 59 anos,61612,12.944241354678768
2022,5 a 9 anos,22482,4.723307702004286
2022,60 a 79 anos,132755,27.890877767973443
2022,80 anos ou mais,98551,20.70486154880457
2022,Idade ausente ou inválida,4,0.0008403714441783268
2022,Menor de 1 ano,54043,11.35404848943233
2023,1 a 4 anos,46857,19.46664783302313
2023,10 a 19 anos,8903,3.6987337144376498
2023,20 a 39 anos,11807,4.905194762031375
2023,40 a 59 anos,19820,8.234179739431003
2023,5 a 9 anos,22260,9.247872906141984
2023,60 a 79 anos,41453,17.221566737569795
2023,80 anos ou mais,29699,12.338390720553043
2023,Idade ausente ou inválida,3,0.001246344057431534
2023,Menor de 1 ano,59902,24.88616724275459
2024,1 a 4 anos,44872,19.553944168939942
2024,10 a 19 anos,10067,4.3869129066838655
2024,20 a 39 anos,11831,5.155614045790882
2024,40 a 59 anos,18301,7.9750564324248945
2024,5 a 9 anos,21810,9.50417904984356
2024,60 a 79 anos,37044,16.142723921247352
2024,80 anos ou mais,25677,11.18930790751183
2024,Idade ausente ou inválida,4,0.0017430864832358658
2024,Menor de 1 ano,59872,26.090518481074437
2025,1 a 4 anos,58583,20.20709661174214
2025,10 a 19 anos,11765,4.058113985919913
2025,20 a 39 anos,13752,4.743492013121178
2025,40 a 59 anos,22988,7.929275334324435
2025,5 a 9 anos,24691,8.516692938916158
2025,60 a 79 anos,46556,16.058610686654273
2025,80 anos ou mais,30507,10.522812016018598
... [10 more rows omitted]
```

### `outputs/tables/eda_02_hca_dbscan_resumo_minimo.csv`

- Git: `ignored` · `627 B` · modified `2026-10-14 23:30 UTC` · 2 rows

```csv
metodo,matriz,quantidade_registros,quantidade_clusters,percentual_ruido,silhouette,calinski_harabasz,davies_bouldin,menor_cluster_percentual,ari_vs_kmeans,tempo_segundos,parametros,decisao
HCA_Ward,nucleo_sem_indicadores_ausencia,5000,2,0.0,0.2103562355041504,1400.8716617335656,1.7601060730978162,46.160000000000004,0.7842444162553112,0.9755442999303341,linkage=ward; k=2,nao aprofundar: comparacao minima registrada; K-Means permanece como referencia
DBSCAN,nucleo_sem_indicadores_ausencia,8000,0,100.0,,,,,,,eps=nan; min_samples=10,descartar: a varredura curta nao produziu ao menos dois clusters avaliaveis sem ruido
```

### `outputs/tables/eda_02_idade_por_ano.csv`

- Git: `ignored` · `951 B` · modified `2026-10-14 23:22 UTC` · 8 rows

```csv
ano_internacao,quantidade_registros,quantidade_idade_valida,quantidade_idade_ausente,percentual_idade_ausente,idade_media,idade_mediana,idade_q1,idade_q3,idade_iqr,idade_minima,idade_maxima
2019,43513,43513,0,0.0,24.590190265151314,5.0,0.6666666666666666,50.0,49.333333333333336,0.0,108.0
2020,979812,979808,4,0.00040824158103799506,56.897618532015855,60.0,43.0,74.0,31.0,0.0,120.0
2021,1480215,1480207,8,0.0005404620274757383,53.57439593341799,56.0,41.0,70.0,29.0,0.0,119.0
2022,475980,475976,4,0.0008403714441783268,47.423172459247304,58.0,5.0,77.0,72.0,0.0,118.0
2023,240704,240701,3,0.001246344057431534,30.035234843706462,7.0,1.0,66.0,65.0,0.0,117.0
2024,229478,229474,4,0.0017430864832358658,28.289975096127495,6.0,0.9166666666666666,63.0,62.083333333333336,0.0,114.0
2025,289913,289912,1,0.00034493106552655454,27.4152186671472,5.0,0.75,62.0,61.25,0.0,114.0
2026,175521,175521,0,0.0,23.672497067603732,3.0,0.75,53.0,52.25,0.0,115.0
```

### `outputs/tables/eda_02_obito_comorbidades.csv`

- Git: `ignored` · `3.8 KB` · modified `2026-10-14 23:28 UTC` · 13 rows

```csv
grupo_indicador,coluna,nome_amigavel,quantidade_sim,obito_sim,cura_sim,percentual_obito_sim,ic95_obito_sim_inferior,ic95_obito_sim_superior,quantidade_nao,obito_nao,cura_nao,percentual_obito_nao,ic95_obito_nao_inferior,ic95_obito_nao_superior,odds_ratio_bruta,ic95_or_inferior,ic95_or_superior,quantidade_ignorado,quantidade_ausente,quantidade_inesperado
comorbidades,renal,Doenca renal cronica,125182,51917,73265,41.47321499896151,41.2005588472639,41.746394457337765,1289010,353901,935109,27.45525635953173,27.378280190293392,27.532366902353246,1.872377795378616,1.8502458652196698,1.8947744591828404,27483,2473461,0
comorbidades,hepatica,Doenca hepatica cronica,29998,12365,17633,41.21941462764184,40.66355469091473,41.777523110157446,1355129,379894,975235,28.033788665138154,27.958226433065793,28.10947543451595,1.8001751319653052,1.7587276613304137,1.8425993842019206,29381,2500628,0
comorbidades,cardiopati,Doenca cardiovascular cronica,1016586,345365,671221,33.97302343333471,33.88101718317478,34.06515080799932,725961,174180,551781,23.99302441866712,23.894928460744936,24.09139560954837,1.62997612592386,1.6189749242326557,1.641052082595416,16720,2155869,0
comorbidades,diabetes,Diabetes mellitus,683122,240882,442240,35.26192978706585,35.148712441915045,35.37531288700555,946468,241584,704884,25.524793231255572,25.43705475998722,25.612730378268544,1.5892631441369018,1.5785224831538285,1.6000768872582307,19768,2265778,0
comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,105976,36125,69851,34.087906695855665,33.8031057426785,34.37386118257916,1302135,362987,939148,27.876295468595806,27.799345590166553,27.953375881953008,1.3380680297360732,1.3204334697942015,1.355938101509065,29092,2477933,0
comorbidades,neurologic,Doenca neurologica cronica,173245,58699,114546,33.88207451874513,33.659558580962994,34.105305224331666,1257959,349335,908624,27.769982964468635,27.6917870337004,27.848314663468194,1.3328856078122973,1.3187173966146282,1.347206041320112,27545,2456387,0
comorbidades,obesidade,Obesidade,210819,70572,140247,33.4751611572012,33.27402351949005,33.676901001841095,1216471,336522,879949,27.663791409741783,27.584368664214367,27.743355224566464,1.3157788042059022,1.3028435656823645,1.328842469810072,37078,2450768,0
comorbidades,out_morbi,Outro fator de risco?,930468,291415,639053,31.319185614121064,31.22502614690555,31.41349932905479,724021,193059,530962,26.66483430729219,26.56309962011751,26.766816613258236,1.2541469106266776,1.2456397671636512,1.262712153944741,22195,2238452,0
comorbidades,pneumopati,Outra pneumopatia cronica,180160,57360,122800,31.838365896980463,31.623643259068736,32.0538630207042,1251179,350048,901131,27.977451667587133,27.898864310635158,28.056174254514676,1.2024612929770748,1.1897192454430583,1.215339809493989,28257,2455540,0
comorbidades,hematologi,Doenca hematologica cronica,32443,9228,23215,28.44373208396264,27.955393399448457,28.937174964250843,1357960,383281,974679,28.224763616012254,28.149123345222794,28.30052708400525,1.0108418547567384,0.9864685146717442,1.0358174033238718,29503,2495230,0
comorbidades,sind_down,Sindrome de Down,17905,3354,14551,18.732197710136834,18.167428827018078,19.310380523485115,1371001,388705,982296,28.35191221596483,28.276529304836938,28.427416439921465,0.5824953543455293,0.5609303923117962,0.6048893810794292,26612,2499618,0
comorbidades,puerpera,Puerpera ou parturiente,12999,1549,11450,11.916301253942612,11.370576906380899,12.484527907778842,1372975,391306,981669,28.50059178062237,28.425143672707904,28.576160194966686,0.3393864511980115,0.32180613790246815,0.3579271794116293,26610,2502552,0
comorbidades,asma,Asma,178130,20249,157881,11.367540560264976,11.220968923614333,11.515778415988475,1253709,374422,879287,29.865144144295048,29.785093678226275,29.945317999416037,0.30119170392217276,0.29667138629419587,0.30578089665035074,27092,2456205,0
```

### `outputs/tables/eda_02_obito_faixa_etaria.csv`

- Git: `ignored` · `925 B` · modified `2026-10-14 23:28 UTC` · 9 rows

```csv
faixa_etaria,quantidade_total,quantidade_obito_srag,quantidade_cura,percentual_obito_srag,ic95_inferior,ic95_superior
Menor de 1 ano,381952,6722,375230,1.7599070040214475,1.7186898574688039,1.8020944843699709
1 a 4 anos,330768,3621,327147,1.0947250036279204,1.0598278233794314,1.1307581185387119
5 a 9 anos,140432,1608,138824,1.1450381679389312,1.0907144950789642,1.202034581918472
10 a 19 anos,89775,3890,85885,4.333054859370649,4.201814484358208,4.46820323066315
20 a 39 anos,423572,48252,375320,11.391687835834286,11.296358968057598,11.487716990203355
40 a 59 anos,914523,193140,721383,21.11920640596245,21.035676023017103,21.202979415748857
60 a 79 anos,1114229,383573,730656,34.42497009142645,34.33680395589146,34.51324362073731
80 anos ou mais,519861,215377,304484,41.429728331227,41.29588641809588,41.56369690168545
Idade ausente ou inválida,24,2,22,8.333333333333332,2.315881529704331,25.84880219321068
```

### `outputs/tables/eda_02_obito_numero_comorbidades.csv`

- Git: `ignored` · `576 B` · modified `2026-10-14 23:28 UTC` · 4 rows

```csv
grupo_numero_comorbidades,quantidade_total,quantidade_obito_srag,quantidade_cura,percentual_obito_srag,ic95_inferior,ic95_superior
Nenhuma comorbidade confirmada,1751582,219109,1532473,12.509205963523259,12.460295749070244,12.558280622490543
Uma comorbidade confirmada,1107510,265687,841823,23.989580229523888,23.910142151445317,24.069198744094926
Duas comorbidades confirmadas,691829,228494,463335,33.02752558797044,32.91679582110583,33.13844383695857
Três ou mais comorbidades confirmadas,364215,142895,221320,39.23369438381176,39.075235384707156,39.39238048989145
```

### `outputs/tables/eda_02_obito_sintomas.csv`

- Git: `ignored` · `3.7 KB` · modified `2026-10-14 23:28 UTC` · 13 rows

```csv
grupo_indicador,coluna,nome_amigavel,quantidade_sim,obito_sim,cura_sim,percentual_obito_sim,ic95_obito_sim_inferior,ic95_obito_sim_superior,quantidade_nao,obito_nao,cura_nao,percentual_obito_nao,ic95_obito_nao_inferior,ic95_obito_nao_superior,odds_ratio_bruta,ic95_or_inferior,ic95_or_superior,quantidade_ignorado,quantidade_ausente,quantidade_inesperado
sintomas,saturacao,Saturacao de oxigenio abaixo de 95%?,2311260,618091,1693169,26.742599274854406,26.68557540452633,26.799700455566146,997117,122100,875017,12.245303209151984,12.181106556729752,12.309790765358352,2.616091550840492,2.5987301802775664,2.6335689077378626,40751,566008,0
sintomas,dispneia,Dispneia,2682695,663856,2018839,24.745861903794506,24.694258959301,24.79753717301567,783396,103596,679800,13.223963359526984,13.14913038338162,13.299157003680856,2.15779594309479,2.1425281296972924,2.1731725560560875,29898,419147,0
sintomas,desc_resp,Desconforto respiratorio,2300240,558432,1741808,24.2771189093312,24.22175374635577,24.332569987883655,975538,157151,818387,16.10916232888929,16.036346738063497,16.18224482832275,1.6695967437915027,1.65930637671044,1.6799509276915383,36991,602367,0
sintomas,fadiga,Fadiga,733292,172047,561245,23.462276964701648,23.36542491058367,23.559407060953433,1805281,340584,1464697,18.865982636498142,18.808977723628345,18.923120049284712,1.3183118912620826,1.3096880146702052,1.3269925533224372,68029,1308534,0
sintomas,perd_olft,Perda do olfato,191692,40851,150841,21.310748492373182,21.128007166515566,21.494639645764085,2216502,440257,1776245,19.862693559491486,19.81022269617673,19.91526888562289,1.092647025536152,1.0802411781379349,1.1051953457939327,101005,1405937,0
sintomas,perd_pala,Perda do paladar,194924,41196,153728,21.13439083950668,20.95372055679628,21.316198836030495,2209221,439090,1770131,19.875331621417686,19.82276184410635,19.928006161875704,1.0803237750515509,1.0681157471330678,1.0926713346135457,102337,1408654,0
sintomas,diarreia,Diarreia,421101,87025,334076,20.66606348595705,20.544035039760857,20.78862712005931,2406519,496955,1909564,20.650366774581876,20.599270221042307,20.701557027965464,1.0009581243967502,0.9928970695100992,1.0090846247438434,63752,1023764,0
sintomas,dor_abd,Dor abdominal,205578,39830,165748,19.37464125538725,19.204365153596036,19.54606187513443,2221677,443816,1777861,19.976621264027127,19.924098461698858,20.029247891865275,0.9626243828167531,0.9516927988623076,0.9736815320039038,76313,1411568,0
sintomas,garganta,Dor de garganta,569484,112121,457363,19.688173855630712,19.585102376764503,19.791654269063862,2265572,475699,1789873,20.996860836910063,20.943875531622535,21.0499444963226,0.9223928185049454,0.9157094761770133,0.9291249394748314,86054,994026,0
sintomas,outro_sin,Apresentou outros sintomas?,1201597,237211,964386,19.741310938692425,19.670236782777796,19.812578565689936,1604620,344431,1260189,21.464957435405267,21.40149872870601,21.52855276750935,0.8999479232313568,0.89468664579503,0.9052401400366705,80959,1027960,0
sintomas,febre,Febre,2209872,424633,1785239,19.215275816879892,19.163383305548958,19.267275355264598,1141670,271719,869951,23.800134890117107,23.72210629882234,23.878339793944008,0.7615390190878549,0.7573965060159404,0.7657041892679217,39528,524066,0
sintomas,vomito,Vomito,383652,61999,321653,16.160218114332782,16.04408329044029,16.277030598328764,2426912,514150,1912762,21.185358183568255,21.133994425310053,21.236813160696173,0.7170809306724982,0.7105627745484236,0.7236588793452112,65427,1039145,0
sintomas,tosse,Tosse,2790984,527269,2263715,18.89186752772499,18.845986424063263,18.93783426458662,711130,196769,514361,27.669905643131354,27.56604955915098,27.774002976038247,0.6088661684983051,0.6052252388657167,0.6125290013294685,31467,381555,0
```

### `outputs/tables/eda_02_perfis_binarios_clusters_sensibilidade.csv`

- Git: `ignored` · `11.9 KB` · modified `2026-10-14 23:30 UTC` · 104 rows (first 60 shown)

```csv
cluster_rotulo,quantidade_registros,quantidade_respostas_validas,quantidade_sim,quantidade_sem_resposta_valida,percentual_preenchido_valido,percentual_sem_resposta_valida,percentual_sim_entre_validos,variavel,grupo_clinico,matriz
Cluster 1,39768,36908,29142,2860,92.8082880708107,7.191711929189299,78.9584913839818,febre,sintoma,nucleo
Cluster 2,40232,34269,20549,5963,85.17846490355936,14.821535096440645,59.9638156934839,febre,sintoma,nucleo
Cluster 1,39768,37951,33681,1817,95.43099979883324,4.569000201166768,88.74864957445126,tosse,sintoma,nucleo
Cluster 2,40232,36123,28111,4109,89.78673692583018,10.213263074169815,77.82022534119535,tosse,sintoma,nucleo
Cluster 1,39768,30668,4557,9100,77.11728022530679,22.88271977469322,14.859136559280032,garganta,sintoma,nucleo
Cluster 2,40232,30154,5995,10078,74.95028832769934,25.049711672300656,19.881276115938185,garganta,sintoma,nucleo
Cluster 1,39768,35823,25837,3945,90.0799637899819,9.920036210018104,72.12405437847194,dispneia,sintoma,nucleo
Cluster 2,40232,36214,29157,4018,90.01292503479817,9.98707496520183,80.51306124703153,dispneia,sintoma,nucleo
Cluster 1,39768,35796,27887,3972,90.012070006035,9.987929993964997,77.90535255335791,desc_resp,sintoma,nucleo
Cluster 2,40232,34138,24040,6094,84.85285344999006,15.147146550009943,70.42005975745504,desc_resp,sintoma,nucleo
Cluster 1,39768,34322,20703,5446,86.30557231945282,13.694427680547175,60.319911427073016,saturacao,sintoma,nucleo
Cluster 2,40232,34696,25284,5536,86.23980910717836,13.760190892821633,72.87295365459995,saturacao,sintoma,nucleo
Cluster 1,39768,31696,3696,8072,79.70227318446993,20.297726815530073,11.66077738515901,diarreia,sintoma,nucleo
Cluster 2,40232,29881,3830,10351,74.27172400079539,25.728275999204612,12.8175094541682,diarreia,sintoma,nucleo
Cluster 1,39768,32032,6029,7736,80.54717360692014,19.452826393079864,18.821803196803195,vomito,sintoma,nucleo
Cluster 2,40232,29658,3155,10574,73.71743885464306,26.28256114535693,10.637939173241621,vomito,sintoma,nucleo
Cluster 1,39768,24025,1773,15743,60.41289478978072,39.58710521021927,7.379812695109261,dor_abd,sintoma,nucleo
Cluster 2,40232,23950,2056,16282,59.5297275800358,40.47027241996421,8.584551148225469,dor_abd,sintoma,nucleo
Cluster 1,39768,24558,4326,15210,61.75316837658419,38.24683162341581,17.615440996823846,fadiga,sintoma,nucleo
Cluster 2,40232,25134,8003,15098,62.47265858023464,37.52734141976536,31.841330468687833,fadiga,sintoma,nucleo
Cluster 1,39768,23322,438,16446,58.64514182257091,41.35485817742909,1.8780550553125805,perd_olft,sintoma,nucleo
Cluster 2,40232,23745,1539,16487,59.02018293895407,40.97981706104593,6.4813644977890075,perd_olft,sintoma,nucleo
Cluster 1,39768,23261,451,16507,58.491752162542745,41.508247837457255,1.9388676325179484,perd_pala,sintoma,nucleo
Cluster 2,40232,23709,1594,16523,58.93070192881289,41.06929807118711,6.723185288287148,perd_pala,sintoma,nucleo
Cluster 1,39768,30496,11406,9272,76.68477167571918,23.315228324280827,37.40162644281217,outro_sin,sintoma,nucleo
Cluster 2,40232,29307,11224,10925,72.84499900576655,27.155000994233447,38.29801753847204,outro_sin,sintoma,nucleo
Cluster 1,39768,7071,193,32697,17.78062764031382,82.21937235968618,2.7294583510111723,puerpera,comorbidade,nucleo
Cluster 2,40232,19471,99,20761,48.396798568303836,51.603201431696164,0.5084484618150069,puerpera,comorbidade,nucleo
Cluster 1,39768,7316,939,32452,18.3967008650171,81.6032991349829,12.834882449425915,cardiopati,comorbidade,nucleo
Cluster 2,40232,24100,14886,16132,59.90256512229072,40.09743487770929,61.76763485477178,cardiopati,comorbidade,nucleo
Cluster 1,39768,7135,293,32633,17.941561054113862,82.05843894588614,4.106517168885775,hematologi,comorbidade,nucleo
Cluster 2,40232,19547,430,20685,48.585702923046334,51.414297076953666,2.199826060265002,hematologi,comorbidade,nucleo
Cluster 1,39768,7144,440,32624,17.964192315429493,82.0358076845705,6.159014557670773,sind_down,comorbidade,nucleo
Cluster 2,40232,19561,120,20671,48.62050109365679,51.379498906343215,0.6134655692449261,sind_down,comorbidade,nucleo
Cluster 1,39768,7056,101,32712,17.742908871454436,82.25709112854557,1.43140589569161,hepatica,comorbidade,nucleo
Cluster 2,40232,19542,454,20690,48.573275004971165,51.42672499502883,2.323201309998977,hepatica,comorbidade,nucleo
Cluster 1,39768,7905,3070,31863,19.877791188895593,80.1222088111044,38.83617963314358,asma,comorbidade,nucleo
Cluster 2,40232,19786,1632,20446,49.17975740703917,50.82024259296083,8.248256342868695,asma,comorbidade,nucleo
Cluster 1,39768,7102,231,32666,17.858579762623215,82.14142023737678,3.252604900028161,diabetes,comorbidade,nucleo
Cluster 2,40232,22728,10072,17504,56.4923444024657,43.5076555975343,44.31538190777895,diabetes,comorbidade,nucleo
Cluster 1,39768,7376,1299,32392,18.547575940454635,81.45242405954536,17.611171366594363,neurologic,comorbidade,nucleo
Cluster 2,40232,20109,2481,20123,49.98260091469477,50.01739908530523,12.337759212293003,neurologic,comorbidade,nucleo
Cluster 1,39768,7192,628,32576,18.08489237577952,81.91510762422047,8.731924360400445,pneumopati,comorbidade,nucleo
Cluster 2,40232,20319,3532,19913,50.50457347385166,49.49542652614834,17.38274521383926,pneumopati,comorbidade,nucleo
Cluster 1,39768,7235,593,32533,18.193019513176424,81.80698048682358,8.19626814098134,imunodepre,comorbidade,nucleo
Cluster 2,40232,19814,1710,20418,49.24935374826009,50.75064625173991,8.630261431311194,imunodepre,comorbidade,nucleo
Cluster 1,39768,7085,231,32683,17.815831824582578,82.18416817541741,3.2604093154551874,renal,comorbidade,nucleo
Cluster 2,40232,19940,1995,20292,49.562537283754224,50.437462716245776,10.005015045135405,renal,comorbidade,nucleo
Cluster 1,39768,7081,302,32687,17.805773486220076,82.19422651377992,4.264934331309137,obesidade,comorbidade,nucleo
Cluster 2,40232,19749,2352,20483,49.087790813282965,50.912209186717035,11.909463770317483,obesidade,comorbidade,nucleo
Cluster 1,39768,7977,4209,31791,20.05884127942064,79.94115872057937,52.764197066566375,out_morbi,comorbidade,nucleo
Cluster 2,40232,22347,11961,17885,55.5453370451382,44.4546629548618,53.52396294804672,out_morbi,comorbidade,nucleo
Cluster 1,38803,36029,28467,2774,92.85106821637503,7.1489317836249775,79.01135196647145,febre,sintoma,ampliada
Cluster 2,41197,35148,21224,6049,85.31689200669952,14.683107993300485,60.38465915557073,febre,sintoma,ampliada
Cluster 1,38803,37047,32947,1756,95.47457670798649,4.525423292013504,88.93297702917916,tosse,sintoma,ampliada
Cluster 2,41197,37027,28845,4170,89.87790373085419,10.12209626914581,77.9026116077457,tosse,sintoma,ampliada
Cluster 1,38803,29876,4339,8927,76.99404685204753,23.00595314795248,14.52336323470344,garganta,sintoma,ampliada
Cluster 2,41197,30946,6213,10251,75.11712017865378,24.882879821346215,20.07690816260583,garganta,sintoma,ampliada
Cluster 1,38803,34957,25231,3846,90.08839522717315,9.911604772826843,72.17724633120692,dispneia,sintoma,ampliada
Cluster 2,41197,37080,29763,4117,90.00655387528218,9.99344612471782,80.26699029126215,dispneia,sintoma,ampliada
... [44 more rows omitted]
```

### `outputs/tables/eda_02_perfis_numericos_clusters_sensibilidade.csv`

- Git: `ignored` · `2.7 KB` · modified `2026-10-14 23:30 UTC` · 24 rows

```csv
cluster_rotulo,quantidade_registros,quantidade_preenchida,media,desvio_padrao,mediana,p25,p75,variavel,matriz,percentual_preenchido
Cluster 1,39768,39768,6.022081400321729,9.549172989351487,1.0,0.5,7.0,idade_anos,nucleo,100.0
Cluster 2,40232,40232,66.76455102074634,15.732651991662259,68.0,55.0,79.0,idade_anos,nucleo,100.0
Cluster 1,39768,39768,3.6171042043854356,6.647296654516078,3.0,1.0,5.0,dias_sintomas_ate_internacao,nucleo,100.0
Cluster 2,40232,40232,5.435871942732153,16.820979588570726,3.0,1.0,7.0,dias_sintomas_ate_internacao,nucleo,100.0
Cluster 1,39768,39768,4.272933011466506,1.568733410310557,4.0,3.0,5.0,n_sintomas_confirmados,nucleo,100.0
Cluster 2,40232,40232,4.089704712666534,1.8005303012481249,4.0,3.0,5.0,n_sintomas_confirmados,nucleo,100.0
Cluster 1,39768,39768,10.079913498290082,3.7710925482249964,13.0,8.0,13.0,n_sintomas_avaliados,nucleo,100.0
Cluster 2,40232,40232,9.71808510638298,4.154358443085973,12.0,6.0,13.0,n_sintomas_avaliados,nucleo,100.0
Cluster 1,39768,39768,0.31505230335948503,0.609884747980405,0.0,0.0,1.0,n_comorbidades_confirmadas,nucleo,100.0
Cluster 2,40232,40232,1.2856432690395705,1.1417558241865937,1.0,0.0,2.0,n_comorbidades_confirmadas,nucleo,100.0
Cluster 1,39768,39768,2.3806829611748137,4.892131997601032,0.0,0.0,1.0,n_comorbidades_avaliadas,nucleo,100.0
Cluster 2,40232,40232,6.636831378007556,6.085915870548763,3.0,0.0,13.0,n_comorbidades_avaliadas,nucleo,100.0
Cluster 1,38803,38803,5.3561915262907815,8.661931790309335,1.0,0.4166666666666667,6.0,idade_anos,ampliada,100.0
Cluster 2,41197,41197,65.96891157123092,16.378472831534076,67.0,54.0,79.0,idade_anos,ampliada,100.0
Cluster 1,38803,38803,3.60554596294101,6.710221531293958,3.0,1.0,5.0,dias_sintomas_ate_internacao,ampliada,100.0
Cluster 2,41197,41197,5.404155642401146,16.63122370472312,3.0,1.0,7.0,dias_sintomas_ate_internacao,ampliada,100.0
Cluster 1,38803,38803,4.278612478416617,1.5647207829835041,4.0,3.0,5.0,n_sintomas_confirmados,ampliada,100.0
Cluster 2,41197,41197,4.088647231594534,1.7984027252336405,4.0,3.0,5.0,n_sintomas_confirmados,ampliada,100.0
Cluster 1,38803,38803,10.094064891889802,3.7735999077423994,13.0,8.0,13.0,n_sintomas_avaliados,ampliada,100.0
Cluster 2,41197,41197,9.713231545986359,4.1428168305503945,12.0,6.0,13.0,n_sintomas_avaliados,ampliada,100.0
Cluster 1,38803,38803,0.30902249826044376,0.6031443309426237,0.0,0.0,0.0,n_comorbidades_confirmadas,ampliada,100.0
Cluster 2,41197,41197,1.2685875185086293,1.140263552310428,1.0,0.0,2.0,n_comorbidades_confirmadas,ampliada,100.0
Cluster 1,38803,38803,2.34311780017009,4.86277792885031,0.0,0.0,1.0,n_comorbidades_avaliadas,ampliada,100.0
Cluster 2,41197,41197,6.572517416316722,6.092517054557381,3.0,0.0,13.0,n_comorbidades_avaliadas,ampliada,100.0
```

### `outputs/tables/eda_02_perfis_sexo_clusters_sensibilidade.csv`

- Git: `ignored` · `696 B` · modified `2026-10-14 23:30 UTC` · 12 rows

```csv
matriz,cluster_rotulo,sexo_categoria,quantidade,percentual_cluster
nucleo,Cluster 1,Feminino,18070,45.43854355260511
nucleo,Cluster 1,Ignorado,8,0.020116676725005028
nucleo,Cluster 1,Masculino,21690,54.541339770669886
nucleo,Cluster 2,Feminino,20243,50.31566911910916
nucleo,Cluster 2,Ignorado,6,0.014913501690196859
nucleo,Cluster 2,Masculino,19983,49.66941737920064
ampliada,Cluster 1,Feminino,17634,45.44493982424039
ampliada,Cluster 1,Ignorado,8,0.020616962605984075
ampliada,Cluster 1,Masculino,21161,54.53444321315363
ampliada,Cluster 2,Feminino,20679,50.19540257785761
ampliada,Cluster 2,Ignorado,6,0.014564167293734982
ampliada,Cluster 2,Masculino,20512,49.79003325484865
```

### `outputs/tables/eda_02_preenchimento_por_variavel_ano.csv`

- Git: `ignored` · `88.1 KB` · modified `2026-10-14 23:23 UTC` · 704 rows (first 60 shown)

```csv
ano_internacao,coluna,nome_amigavel,grupo,uso_inicial_sugerido,quantidade_registros_ano,quantidade_preenchida,quantidade_ausente,percentual_preenchido,percentual_ausente
2019,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,43513,16872,26641,38.774619079355595,61.225380920644405
2020,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,979812,430685,549127,43.95588133233723,56.04411866766277
2021,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,1480215,537556,942659,36.316075705218495,63.683924294781505
2022,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,475980,176903,299077,37.16605739736964,62.83394260263036
2023,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,240704,75522,165182,31.375465301781443,68.62453469821855
2024,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,229478,72187,157291,31.457045991336862,68.54295400866314
2025,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,289913,94756,195157,32.6842880450342,67.31571195496579
2026,asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,175521,54450,121071,31.021928999948724,68.97807100005127
2019,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,43513,17024,26489,39.1239399719624,60.8760600280376
2020,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,979812,531071,448741,54.20131617085726,45.79868382914274
2021,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,1480215,680836,799379,45.99575061730897,54.00424938269103
2022,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,475980,213639,262341,44.88402874070339,55.11597125929661
2023,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,240704,83074,157630,34.51292874235576,65.48707125764423
2024,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,229478,78482,150996,34.200228344329304,65.7997716556707
2025,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,289913,99022,190891,34.15576397057048,65.84423602942951
2026,cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,175521,56119,119402,31.972812370029796,68.0271876299702
2019,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,43513,16860,26653,38.747041114149795,61.252958885850205
2020,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,979812,498051,481761,50.831281919388616,49.168718080611384
2021,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,1480215,634279,845936,42.850464290660476,57.149535709339524
2022,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,475980,198154,277826,41.630740787428046,58.369259212571954
2023,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,240704,78223,162481,32.49759040148897,67.50240959851104
2024,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,229478,74053,155425,32.270195835766394,67.7298041642336
2025,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,289913,95570,194343,32.96506193237281,67.0349380676272
2026,diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,175521,54168,121353,30.861264464081223,69.13873553591878
2019,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,43513,16689,26824,38.35405510996714,61.64594489003286
2020,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,979812,423345,556467,43.2067580311325,56.7932419688675
2021,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,1480215,526779,953436,35.58800579645525,64.41199420354475
2022,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,475980,171192,304788,35.96621706794403,64.03378293205597
2023,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,240704,71291,169413,29.617704732783835,70.38229526721616
2024,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,229478,68669,160809,29.924001429330914,70.07599857066909
2025,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,289913,90278,199635,31.139686733606286,68.86031326639372
2026,hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,175521,51663,123858,29.43408481036457,70.56591518963543
2019,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,43513,16642,26871,38.24604141291108,61.75395858708892
2020,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,979812,422299,557513,43.10000285769107,56.89999714230893
2021,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,1480215,525073,955142,35.47275226909604,64.52724773090395
2022,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,475980,170366,305614,35.79268036472121,64.2073196352788
2023,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,240704,70804,169900,29.415381547460782,70.58461845253922
2024,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,229478,68132,161346,29.6899920689565,70.3100079310435
2025,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,289913,89761,200152,30.961357372729058,69.03864262727095
2026,hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,175521,51431,124090,29.30190689433173,70.69809310566828
2019,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,43513,16776,26737,38.55399535770919,61.44600464229081
2020,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,979812,427535,552277,43.634391087269805,56.365608912730195
2021,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,1480215,531702,948513,35.92059261661313,64.07940738338687
2022,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,475980,174411,301569,36.64250598764654,63.35749401235346
2023,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,240704,72992,167712,30.32438181334751,69.67561818665249
2024,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,229478,70023,159455,30.514036203906258,69.48596379609374
2025,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,289913,91557,198356,31.580853566414753,68.41914643358524
2026,imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,175521,52207,123314,29.744019234165712,70.2559807658343
2019,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,43513,7726,35787,17.755613265001262,82.24438673499874
2020,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,979812,269076,710736,27.46200291484489,72.53799708515511
2021,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,1480215,364531,1115684,24.626895417219796,75.3731045827802
2022,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,475980,123215,352765,25.886591873608133,74.11340812639187
2023,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,240704,45139,195565,18.752908136134007,81.24709186386599
2024,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,229478,38647,190831,16.841265829404126,83.15873417059588
2025,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,289913,46401,243512,16.005146371497656,83.99485362850234
2026,morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,175521,25148,150373,14.327630312042434,85.67236968795757
2019,neurologic,Doenca neurologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,43513,16847,26666,38.717164985176844,61.282835014823156
2020,neurologic,Doenca neurologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,979812,434358,545454,44.33074916412536,55.66925083587464
2021,neurologic,Doenca neurologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,1480215,538341,941874,36.36910854166456,63.63089145833544
2022,neurologic,Doenca neurologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,475980,179090,296890,37.62553048447414,62.37446951552586
... [644 more rows omitted]
```

### `outputs/tables/eda_02_resumo_analise_desfecho.csv`

- Git: `ignored` · `367 B` · modified `2026-10-14 23:28 UTC` · 10 rows

```csv
metrica,valor
origem_analise,coorte_sem_particao
quantidade_registros,3915136
quantidade_curas,3058951
quantidade_obitos_srag,856185
percentual_obito_srag,21.86858898388204
ic95_obito_inferior,21.8276718791117
ic95_obito_superior,21.90956129263557
quantidade_sintomas_analisados,13
quantidade_comorbidades_analisadas,13
quantidade_variaveis_ausencia,32
```

### `outputs/tables/eda_02_resumo_fonte.csv`

- Git: `ignored` · `237 B` · modified `2026-10-14 23:22 UTC` · 4 rows

```csv
metrica,valor
nome_coorte,coorte_desenvolvimento
caminho_coorte,<REPO>\data\analytical\coorte_provisoria_b.parquet
quantidade_linhas,3915136
quantidade_colunas,125
```

### `outputs/tables/eda_02_resumo_fonte_provisorio.csv`

- Git: `ignored` · `261 B` · modified `2026-10-11 13:27 UTC` · 5 rows

```csv
metrica,valor
nome_coorte,coorte_desenvolvimento
caminho_coorte,<REPO>\data\analytical\coorte_provisoria_b.parquet
coorte_provisoria,True
quantidade_linhas,3915136
quantidade_colunas,125
```

### `outputs/tables/eda_02_resumo_preenchimento_variaveis.csv`

- Git: `ignored` · `11.1 KB` · modified `2026-10-14 23:23 UTC` · 88 rows (first 60 shown)

```csv
coluna,nome_amigavel,grupo,uso_inicial_sugerido,quantidade_registros,quantidade_preenchida,quantidade_ausente,percentual_preenchido,percentual_ausente
tabag,Tabagismo,comorbidades_fatores_risco,indisponivel_se_100pct_vazio,3915136,0,3915136,0.0,100.0
out_trat,Outro tratamento para COVID-19,tratamentos,excluir_modelagem,3915136,2471,3912665,0.06311402720109852,99.9368859727989
dt_trt_cov,Data de inicio do tratamento para COVID-19,tratamentos,exploracao_eda,3915136,3344,3911792,0.08541210318109001,99.91458789681892
tipo_trat,Tipo de tratamento para COVID-19,tratamentos,exploracao_eda,3915136,4075,3911061,0.10408322980351128,99.8959167701965
out_anim,Especificacao do outro animal,exposicao_animal,exploracao_texto,3915136,4612,3910524,0.11779922843037892,99.88220077156961
dt_vac_mae,Data da vacinacao materna,vacinacao_influenza,modelo_c_sensibilidade,3915136,5194,3909942,0.13266461241703992,99.86733538758295
dt_2_dose,Data da segunda dose infantil,vacinacao_influenza,modelo_c_sensibilidade,3915136,8592,3906544,0.21945597802988198,99.78054402197012
cs_etinia,Etnia indigena,demografia_contexto_social,exploracao_subgrupo,3915136,8988,3906148,0.22957056919606367,99.77042943080393
tp_pov_ct,Povo ou comunidade tradicional,demografia_contexto_social,exploracao_subgrupo,3915136,9502,3905634,0.24269910419459248,99.75730089580541
dt_doseuni,Data da dose unica infantil,vacinacao_influenza,modelo_c_sensibilidade,3915136,14066,3901070,0.35927232157452516,99.64072767842548
out_antiv,Outro antiviral utilizado,tratamentos,excluir_modelagem,3915136,14561,3900575,0.3719155605322523,99.62808443946774
dt_1_dose,Data da primeira dose infantil,vacinacao_influenza,modelo_c_sensibilidade,3915136,14830,3900306,0.3787863307941282,99.62121366920587
dose_adic,Data da dose adicional,vacinacao_covid,modelo_c_sensibilidade,3915136,17594,3897542,0.44938413378232583,99.55061586621767
obes_imc,IMC registrado,comorbidades_fatores_risco,reavaliar_apos_eda,3915136,50513,3864623,1.290197837316507,98.70980216268349
pac_cocbo,Codigo da ocupacao,demografia_contexto_social,reavaliar_apos_modelo_principal,3915136,64480,3850656,1.6469415110994867,98.35305848890052
pac_dscbo,Descricao da ocupacao,demografia_contexto_social,apoio_interpretacao,3915136,64480,3850656,1.6469415110994867,98.35305848890052
m_amamenta,Mae amamenta a crianca?,vacinacao_influenza,modelo_c_sensibilidade,3915136,84061,3831075,2.147077393990911,97.85292260600909
dos_re_bi,Data do reforco bivalente,vacinacao_covid,modelo_c_sensibilidade,3915136,91356,3823780,2.33340553176186,97.66659446823815
mae_vac,Mae vacinada contra influenza?,vacinacao_influenza,modelo_c_sensibilidade,3915136,93116,3822020,2.3783592702782226,97.62164072972178
dose_2ref,Data da segunda dose de reforco,vacinacao_covid,modelo_c_sensibilidade,3915136,161245,3753891,4.11850316310851,95.88149683689149
dt_antivir,Data de inicio do antiviral,tratamentos,exploracao_eda,3915136,315448,3599688,8.057140288357798,91.9428597116422
tp_antivir,Tipo de antiviral utilizado,tratamentos,exploracao_eda,3915136,331007,3584129,8.454546661980581,91.54545333801941
dt_ut_dose,Data da ultima dose contra influenza,vacinacao_influenza,modelo_c_sensibilidade,3915136,336934,3578202,8.60593348481381,91.39406651518618
dose_ref,Data da dose de reforco,vacinacao_covid,modelo_c_sensibilidade,3915136,393149,3521987,10.04177121816458,89.95822878183542
dose_2_cov,Data da segunda dose contra COVID-19,vacinacao_covid,modelo_c_sensibilidade,3915136,847592,3067544,21.649107463955275,78.35089253604473
trat_cov,Recebeu tratamento antiviral para COVID-19?,tratamentos,exploracao_eda,3915136,865502,3049634,22.10656283715304,77.89343716284696
morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,3915136,919883,2995253,23.49555673161801,76.50444326838199
dose_1_cov,Data da primeira dose contra COVID-19,vacinacao_covid,modelo_c_sensibilidade,3915136,1006619,2908517,25.710958699774416,74.28904130022559
outro_des,Descricao dos outros sintomas,sintomas,exploracao_texto,3915136,1183041,2732095,30.217111231895906,69.7828887681041
puerpera,Puerpera ou parturiente,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1412584,2502552,36.08007486840815,63.91992513159185
hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1414508,2500628,36.12921747801354,63.87078252198646
sind_down,Sindrome de Down,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1415518,2499618,36.15501479386668,63.84498520613332
hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1419906,2495230,36.267092637394974,63.732907362605026
imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1437203,2477933,36.70889082780266,63.29110917219734
renal,Doenca renal cronica,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1441675,2473461,36.82311419066924,63.17688580933076
neurologic,Doenca neurologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1458749,2456387,37.25921653807173,62.74078346192827
asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1458931,2456205,37.26386516330467,62.73613483669533
pneumopati,Outra pneumopatia cronica,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1459596,2455540,37.28085052473273,62.71914947526727
obesidade,Obesidade,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1464368,2450768,37.4027364566646,62.5972635433354
diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1649358,2265778,42.12773196129074,57.87226803870926
out_morbi,Outro fator de risco?,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1676684,2238452,42.82568983555105,57.17431016444895
cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,3915136,1759267,2155869,44.935016305946974,55.064983694053026
estrang,Paciente estrangeiro?,demografia_contexto_social,modelo_b_ampliado,3915136,2459733,1455403,62.82624664890313,37.17375335109687
dor_abd,Dor abdominal,sintomas,modelo_a_nucleo,3915136,2503568,1411568,63.94587569882629,36.05412430117371
perd_pala,Perda do paladar,sintomas,modelo_a_nucleo,3915136,2506482,1408654,64.02030478634714,35.97969521365286
perd_olft,Perda do olfato,sintomas,modelo_a_nucleo,3915136,2509199,1405937,64.08970212018178,35.910297879818216
fadiga,Fadiga,sintomas,modelo_a_nucleo,3915136,2606602,1308534,66.57755950240298,33.42244049759702
cs_escol_n,Escolaridade,demografia_contexto_social,modelo_b_ampliado,3915136,2647598,1267538,67.62467510707162,32.375324892928376
vacina_cov,Recebeu vacina contra COVID-19?,vacinacao_covid,modelo_a_nucleo,3915136,2653969,1261167,67.78740253212149,32.21259746787851
vomito,Vomito,sintomas,modelo_a_nucleo,3915136,2875991,1039145,73.45826556216693,26.54173443783307
outro_sin,Apresentou outros sintomas?,sintomas,exploracao_texto,3915136,2887176,1027960,73.7439516788178,26.256048321182206
diarreia,Diarreia,sintomas,modelo_a_nucleo,3915136,2891372,1023764,73.85112547814431,26.14887452185569
garganta,Dor de garganta,sintomas,modelo_a_nucleo,3915136,2921110,994026,74.61069040768955,25.389309592310454
vacina,Recebeu vacina contra influenza?,vacinacao_influenza,modelo_a_nucleo,3915136,3002456,912680,76.68842155163958,23.31157844836042
pov_ct,Pertence a povo ou comunidade tradicional?,demografia_contexto_social,modelo_b_ampliado,3915136,3018493,896643,77.09803695197306,22.901963048026943
co_rg_inte,Regional de saude de internacao,geografia_internacao,exploracao_eda,3915136,3263378,651758,83.3528643704842,16.6471356295158
desc_resp,Desconforto respiratorio,sintomas,modelo_b_ampliado,3915136,3312769,602367,84.61440419949652,15.38559580050348
saturacao,Saturacao de oxigenio abaixo de 95%?,sintomas,modelo_a_nucleo,3915136,3349128,566008,85.54308202831268,14.456917971687318
ave_suino,"Contato direto com aves, suinos ou outro animal?",exposicao_animal,modelo_a_nucleo,3915136,3352831,562305,85.63766367247524,14.362336327524758
antiviral,Usou antiviral contra influenza?,tratamentos,exploracao_eda,3915136,3379034,536102,86.30693799653447,13.693062003465528
... [28 more rows omitted]
```

### `outputs/tables/eda_02_resumo_rupturas_temporais.csv`

- Git: `ignored` · `771 B` · modified `2026-10-14 23:26 UTC` · 9 rows

```csv
tipo_indicador,grupo_indicador,quantidade_indicadores,quantidade_destaques,maior_amplitude,amplitude_mediana,percentual_indicadores_destacados
qualidade_dados,preenchimento,88,22,98.62178747183194,11.185375960892992,25.0
clinico,sintomas,13,9,28.726919171929584,12.003363973507568,69.23076923076923
clinico,comorbidades,13,5,34.62749907042388,7.509387634535367,38.46153846153847
territorio,uf_residencia,10,3,8.528311660459739,2.794892732490122,30.0
contexto,vacinacao,2,2,45.48807599371179,29.001747326609213,100.0
demografia,idade,1,1,55.0,55.0,100.0
composicao,volume,1,1,38.41844681872332,38.41844681872332,100.0
qualidade_dados,escolaridade,1,1,29.98384702470485,29.98384702470485,100.0
desfecho,desfecho,1,1,20.869390760490116,20.869390760490116,100.0
```

### `outputs/tables/eda_02_resumo_temporal.csv`

- Git: `ignored` · `836 B` · modified `2026-10-14 23:22 UTC` · 8 rows

```csv
ano_internacao,quantidade_registros,percentual_coorte,quantidade_cura,quantidade_obito_srag,percentual_cura,percentual_obito_srag,periodo_completo
2019,43513,1.1114045591264263,38292,5221,88.0012869717096,11.998713028290396,True
2020,979812,25.026257069997058,705699,274113,72.02391887423302,27.97608112576698,True
2021,1480215,37.807498896590054,1062924,417291,71.80875751157771,28.19124248842229,True
2022,475980,12.157432078987805,389547,86433,81.84104374133368,18.158956258666333,True
2023,240704,6.148036747637885,217667,23037,90.42932398298325,9.570676017016751,True
2024,229478,5.861303413214764,210358,19120,91.66804661013256,8.331953389867438,True
2025,289913,7.404927951417268,268686,21227,92.67814827206783,7.321851727932173,True
2026,175521,4.483139283028738,165778,9743,94.44909725901745,5.55090274098256,False
```

### `outputs/tables/eda_02_resumo_uf_residencia.csv`

- Git: `ignored` · `981 B` · modified `2026-10-14 23:26 UTC` · 28 rows

```csv
uf_residencia_categoria,quantidade,percentual_coorte,ordem_frequencia
SP,1158797,29.597873483833,1
MG,472256,12.062314054990681,2
PR,336568,8.596585150554157,3
RJ,300618,7.678353957563671,4
RS,235248,6.008680158237159,5
SC,166751,4.259136847353451,6
BA,142962,3.6515206623729037,7
GO,142693,3.644649892111027,8
CE,129855,3.3167430199104198,9
PE,101230,2.5856062215974105,10
DF,100575,2.568876279138196,11
MS,89937,2.2971615800830416,12
PA,84009,2.145749215352928,13
AM,63253,1.6156016036224539,14
PB,59052,1.5083000948115213,15
MT,50033,1.2779377268120444,16
MA,39880,1.0186108477457743,17
RN,34468,0.8803781018079576,18
ES,33443,0.854197657501553,19
AL,33202,0.8480420603524373,20
PI,32473,0.8294220175237846,21
SE,28293,0.722656888547422,22
RO,20888,0.5335191421192009,23
AC,17061,0.43577030274299544,24
TO,16084,0.4108158694870369,25
AP,15117,0.38611685519992156,26
RR,9633,0.24604509268643543,27
Ausente ou inesperada,757,0.01933521594141302,28
```

### `outputs/tables/eda_02_rupturas_temporais.csv`

- Git: `ignored` · `21.6 KB` · modified `2026-10-14 23:26 UTC` · 130 rows (first 60 shown)

```csv
tipo_indicador,grupo_indicador,indicador,unidade,periodo_avaliado,ano_minimo,valor_minimo,ano_maximo,valor_maximo,amplitude,limite_destaque,flag_destaque,ordem_destaque,quantidade_anos
demografia,idade,Idade mediana,anos,2019-2025,2019,5.0,2020,60.0,55.0,5.0,True,11.0,7
composicao,volume,Participação no volume do período,pontos_percentuais,2019-2025,2019,1.1635689770203617,2021,39.58201579574368,38.41844681872332,5.0,True,7.683689363744664,7
qualidade_dados,preenchimento,Recebeu vacina contra COVID-19?,pontos_percentuais,2019-2025,2019,1.3720037689885782,2025,99.99379124082051,98.62178747183194,20.0,True,4.931089373591597,7
qualidade_dados,preenchimento,Pertence a povo ou comunidade tradicional?,pontos_percentuais,2019-2025,2019,1.7787787557741366,2023,100.0,98.22122124422586,20.0,True,4.911061062211293,7
qualidade_dados,preenchimento,Paciente estrangeiro?,pontos_percentuais,2019-2025,2019,0.48950888240296003,2025,95.36240182399548,94.87289294159253,20.0,True,4.743644647079626,7
contexto,vacinacao,Recebeu vacina contra COVID-19?,pontos_percentuais,2019-2025,2019,16.272189349112427,2022,61.76026534282422,45.48807599371179,10.0,True,4.5488075993711785,7
desfecho,desfecho,Óbito por SRAG,pontos_percentuais,2019-2025,2025,7.321851727932173,2021,28.19124248842229,20.869390760490116,5.0,True,4.173878152098023,7
qualidade_dados,preenchimento,Fadiga,pontos_percentuais,2019-2025,2019,0.5538574678831614,2025,82.60202198590612,82.04816451802296,20.0,True,4.102408225901148,7
qualidade_dados,preenchimento,Recebeu tratamento antiviral para COVID-19?,pontos_percentuais,2019-2025,2019,0.2091329028106543,2025,82.23191095259612,82.02277804978547,20.0,True,4.101138902489273,7
qualidade_dados,preenchimento,Dor abdominal,pontos_percentuais,2019-2025,2019,0.30105945349665614,2025,81.07708174521322,80.77602229171656,20.0,True,4.038801114585828,7
qualidade_dados,preenchimento,Perda do olfato,pontos_percentuais,2019-2025,2019,0.2964631259623561,2025,80.48069593291781,80.18423280695545,20.0,True,4.009211640347773,7
qualidade_dados,preenchimento,Perda do paladar,pontos_percentuais,2019-2025,2019,0.2964631259623561,2025,80.35997005998351,80.06350693402115,20.0,True,4.003175346701058,7
clinico,comorbidades,Doenca cardiovascular cronica,pontos_percentuais,2019-2025,2019,27.915404265431,2021,62.54290333585488,34.62749907042388,10.0,True,3.462749907042388,7
qualidade_dados,preenchimento,Data de inicio do antiviral,pontos_percentuais,2019-2025,2021,2.0252463324584604,2019,62.15154091880587,60.12629458634741,20.0,True,3.0063147293173706,7
qualidade_dados,preenchimento,Tipo de antiviral utilizado,pontos_percentuais,2019-2025,2021,2.3266890282830537,2019,62.15383908257303,59.82715005428997,20.0,True,2.9913575027144987,7
clinico,sintomas,Fadiga,pontos_percentuais,2019-2025,2024,21.273080828070416,2019,50.0,28.726919171929584,10.0,True,2.8726919171929586,7
qualidade_dados,preenchimento,Data da primeira dose contra COVID-19,pontos_percentuais,2019-2025,2019,0.11490818835750236,2022,56.78389848312955,56.668990294772044,20.0,True,2.8334495147386023,7
clinico,sintomas,Febre,pontos_percentuais,2019-2025,2022,61.38461498738701,2019,88.72229163774354,27.337676650356528,10.0,True,2.7337676650356526,7
clinico,comorbidades,Diabetes mellitus,pontos_percentuais,2019-2025,2019,19.539264502969584,2020,46.38605355415614,26.84678905118656,10.0,True,2.684678905118656,7
qualidade_dados,preenchimento,Data da segunda dose contra COVID-19,pontos_percentuais,2019-2025,2019,0.0827338956174017,2022,53.10307155762847,53.020337662011066,20.0,True,2.6510168831005534,7
clinico,sintomas,Desconforto respiratorio,pontos_percentuais,2019-2025,2022,63.90864654416326,2019,85.05905099117147,21.150404447008214,10.0,True,2.1150404447008215,7
clinico,sintomas,Apresentou outros sintomas?,pontos_percentuais,2019-2025,2019,25.14156579562575,2021,46.095983867734105,20.954418072108357,10.0,True,2.0954418072108356,7
qualidade_dados,preenchimento,Recebeu vacina contra influenza?,pontos_percentuais,2019-2025,2023,56.22216498271736,2025,94.20515809915389,37.98299311643653,20.0,True,1.8991496558218266,7
clinico,comorbidades,Obesidade,pontos_percentuais,2019-2025,2019,4.106889969829444,2021,22.575467273580003,18.468577303750557,10.0,True,1.8468577303750557,7
qualidade_dados,preenchimento,Data de inclusao do registro no sistema,pontos_percentuais,2019-2025,2019,64.15324155999357,2020,100.0,35.846758440006425,20.0,True,1.7923379220003213,7
clinico,sintomas,Tosse,pontos_percentuais,2019-2025,2020,76.0662108853592,2019,93.37900071740992,17.312789832050726,10.0,True,1.7312789832050726,7
territorio,uf_residencia,UF PR,pontos_percentuais,2019-2025,2020,6.5361518332088195,2019,15.064463493668558,8.528311660459739,5.0,True,1.7056623320919477,7
territorio,uf_residencia,UF SP,pontos_percentuais,2019-2025,2025,24.39007564338267,2020,32.0495156213641,7.659439977981432,5.0,True,1.5318879955962863,7
qualidade_dados,escolaridade,Preenchimento da escolaridade,pontos_percentuais,2019-2025,2024,62.6068729900034,2019,92.59072001470825,29.98384702470485,20.0,True,1.4991923512352425,7
qualidade_dados,preenchimento,Escolaridade,pontos_percentuais,2019-2025,2024,62.6068729900034,2019,92.59072001470825,29.98384702470485,20.0,True,1.4991923512352425,7
clinico,sintomas,Saturacao de oxigenio abaixo de 95%?,pontos_percentuais,2019-2025,2025,62.097120924306026,2021,76.99078255707443,14.8936616327684,10.0,True,1.48936616327684,7
qualidade_dados,preenchimento,Data da dose de reforco,pontos_percentuais,2019-2025,2019,0.027577965205800567,2023,29.40582624302047,29.37824827781467,20.0,True,1.4689124138907335,7
qualidade_dados,preenchimento,Diarreia,pontos_percentuais,2019-2025,2022,68.48859195764528,2019,97.6030151908625,29.11442323321721,20.0,True,1.4557211616608605,7
qualidade_dados,preenchimento,Vomito,pontos_percentuais,2019-2025,2022,69.08630614731712,2019,97.6857490864799,28.599442939162785,20.0,True,1.4299721469581392,7
clinico,comorbidades,Asma,pontos_percentuais,2019-2025,2021,8.789636027143738,2023,22.66830716559232,13.878671138448583,10.0,True,1.3878671138448584,7
qualidade_dados,preenchimento,Dor de garganta,pontos_percentuais,2019-2025,2022,70.38425984285054,2019,98.03736814285386,27.653108300003325,20.0,True,1.3826554150001662,7
clinico,comorbidades,Outro fator de risco?,pontos_percentuais,2019-2025,2019,47.286821705426355,2022,59.968219573853375,12.68139786842702,10.0,True,1.268139786842702,7
contexto,vacinacao,Recebeu vacina contra influenza?,pontos_percentuais,2019-2025,2021,19.93422802020895,2020,32.449646679715585,12.515418659506636,10.0,True,1.2515418659506636,7
clinico,sintomas,Perda do olfato,pontos_percentuais,2019-2025,2019,0.7936507936507936,2021,12.797014767158363,12.003363973507568,10.0,True,1.2003363973507568,7
qualidade_dados,preenchimento,Data da ultima dose contra influenza,pontos_percentuais,2019-2025,2022,3.615067859994117,2025,27.031557743185026,23.41648988319091,20.0,True,1.1708244941595454,7
clinico,sintomas,Perda do paladar,pontos_percentuais,2019-2025,2019,1.574803149606299,2021,13.049298893290151,11.474495743683853,10.0,True,1.1474495743683852,7
qualidade_dados,preenchimento,Apresentou outros sintomas?,pontos_percentuais,2019-2025,2022,70.30106306987689,2019,92.6114034886126,22.310340418735706,20.0,True,1.1155170209367853,7
clinico,sintomas,Dispneia,pontos_percentuais,2019-2025,2022,72.57666416413274,2019,83.65496396186933,11.078299797736591,10.0,True,1.107829979773659,7
territorio,uf_residencia,UF MG,pontos_percentuais,2019-2025,2019,8.443453680509274,2022,13.733980419345352,5.290526738836078,5.0,True,1.0581053477672158,7
qualidade_dados,preenchimento,Doenca cardiovascular cronica,pontos_percentuais,2019-2025,2025,34.15576397057048,2020,54.20131617085726,20.045552200286778,20.0,True,1.002277610014339,7
qualidade_dados,preenchimento,Desconforto respiratorio,pontos_percentuais,2019-2025,2022,79.49241564771629,2019,99.28067474088203,19.78825909316575,20.0,False,0.9894129546582875,7
clinico,sintomas,Dor de garganta,pontos_percentuais,2019-2025,2025,13.37345688380503,2021,23.249005879339368,9.875548995534338,10.0,False,0.9875548995534338,7
qualidade_dados,preenchimento,Diabetes mellitus,pontos_percentuais,2019-2025,2024,32.270195835766394,2020,50.831281919388616,18.56108608362222,20.0,False,0.9280543041811111,7
clinico,comorbidades,Outra pneumopatia cronica,pontos_percentuais,2019-2025,2021,9.063950734249172,2019,18.11307166006482,9.049120925815647,10.0,False,0.9049120925815647,7
qualidade_dados,preenchimento,Saturacao de oxigenio abaixo de 95%?,pontos_percentuais,2019-2025,2022,80.70612210597083,2019,98.51998253395537,17.813860427984537,20.0,False,0.8906930213992268,7
qualidade_dados,preenchimento,Febre,pontos_percentuais,2019-2025,2022,82.36984747258288,2019,99.724220347942,17.354372875359118,20.0,False,0.8677186437679559,7
clinico,sintomas,Diarreia,pontos_percentuais,2019-2025,2019,9.454563139848746,2021,18.105316101164206,8.65075296131546,10.0,False,0.865075296131546,7
qualidade_dados,preenchimento,Data da segunda dose de reforco,pontos_percentuais,2019-2025,2019,0.011490818835750236,2023,17.06826641850572,17.05677559966997,20.0,False,0.8528387799834984,7
qualidade_dados,preenchimento,Outro fator de risco?,pontos_percentuais,2019-2025,2025,33.337932414207025,2020,50.27178683257605,16.933854418369023,20.0,False,0.8466927209184512,7
territorio,uf_residencia,UF RJ,pontos_percentuais,2019-2025,2019,5.076643761634454,2020,9.302396786322275,4.225753024687821,5.0,False,0.8451506049375641,7
qualidade_dados,preenchimento,Usou antiviral contra influenza?,pontos_percentuais,2019-2025,2024,83.16875691787448,2019,99.17725737136028,16.00850045348581,20.0,False,0.8004250226742904,7
clinico,comorbidades,Doenca neurologica cronica,pontos_percentuais,2019-2025,2021,9.278784682568892,2022,16.78817231710426,7.509387634535367,10.0,False,0.7509387634535367,7
qualidade_dados,preenchimento,Dispneia,pontos_percentuais,2019-2025,2022,84.4730871045002,2019,99.34042699882794,14.867339894327742,20.0,False,0.7433669947163871,7
qualidade_dados,preenchimento,Obesidade,pontos_percentuais,2019-2025,2023,29.39170101036958,2020,44.106930717321276,14.715229706951696,20.0,False,0.7357614853475848,7
clinico,sintomas,Dor abdominal,pontos_percentuais,2019-2025,2019,2.2900763358778624,2021,9.448363736797415,7.158287400919552,10.0,False,0.7158287400919552,7
... [70 more rows omitted]
```

### `outputs/tables/eda_02_sexo_por_ano.csv`

- Git: `ignored` · `1014 B` · modified `2026-10-14 23:22 UTC` · 24 rows

```csv
ano_internacao,sexo_categoria,quantidade,percentual_ano
2019,Feminino,21171,48.65442511433365
2019,Ignorado,12,0.027577965205800567
2019,Masculino,22330,51.31799692046055
2020,Feminino,446843,45.60497319894021
2020,Ignorado,221,0.022555347352349226
2020,Masculino,532748,54.37247145370745
2021,Feminino,670315,45.28497549342494
2021,Ignorado,175,0.011822606851031776
2021,Masculino,809725,54.70320189972403
2022,Feminino,235553,49.488003697634355
2022,Ignorado,52,0.01092482877431825
2022,Masculino,240375,50.50107147359133
2023,Feminino,116318,48.32408269077373
2023,Ignorado,14,0.005816272268013826
2023,Masculino,124372,51.67010103695826
2024,Feminino,111138,48.43078639346691
2024,Ignorado,35,0.015252006728313824
2024,Masculino,118305,51.55396159980478
2025,Feminino,140063,48.3120798308458
2025,Ignorado,33,0.0113827251623763
2025,Masculino,149817,51.67653744399182
2026,Feminino,83546,47.5988628141362
2026,Ignorado,11,0.006267056363626005
2026,Masculino,91964,52.39487012950017
```

### `outputs/tables/eda_02_sintomas_por_ano.csv`

- Git: `ignored` · `13.8 KB` · modified `2026-10-14 23:26 UTC` · 104 rows (first 60 shown)

```csv
ano_internacao,grupo_clinico,coluna,nome_amigavel,quantidade_total,quantidade_sim,quantidade_nao,quantidade_ignorado,quantidade_ausente,quantidade_inesperado,quantidade_respostas_validas,percentual_sim_validos,percentual_nao_validos,percentual_sem_resposta_valida
2019,sintomas,desc_resp,Desconforto respiratorio,43513,36515,6414,271,313,0,42929,85.05905099117147,14.94094900882853,1.3421276400156275
2020,sintomas,desc_resp,Desconforto respiratorio,979812,560899,264215,13473,141225,0,825114,67.97836420179515,32.021635798204855,15.78853902585394
2021,sintomas,desc_resp,Desconforto respiratorio,1480215,832352,367371,15770,264722,0,1199723,69.37868157899781,30.62131842100218,18.949409376340597
2022,sintomas,desc_resp,Desconforto respiratorio,475980,239003,134973,4392,97612,0,373976,63.90864654416326,36.09135345583674,21.430312197991512
2023,sintomas,desc_resp,Desconforto respiratorio,240704,149928,53657,1115,36004,0,203585,73.64393250976251,26.356067490237496,15.421015022600374
2024,sintomas,desc_resp,Desconforto respiratorio,229478,152371,49920,666,26521,0,202291,75.32267871531604,24.677321284683945,11.847323054933371
2025,sintomas,desc_resp,Desconforto respiratorio,289913,202424,63374,697,23418,0,265798,76.15708169361696,23.842918306383044,8.318012645172862
2026,sintomas,desc_resp,Desconforto respiratorio,175521,126748,35614,607,12552,0,162362,78.06506448553233,21.93493551446767,7.497108608086782
2019,sintomas,diarreia,Diarreia,43513,3888,37235,1347,1043,0,41123,9.454563139848746,90.54543686015126,5.492611403488612
2020,sintomas,diarreia,Diarreia,979812,121536,604896,23746,229634,0,726432,16.730540504823576,83.26945949517642,25.8600629508518
2021,sintomas,diarreia,Diarreia,1480215,183587,830408,25609,440611,0,1013995,18.105316101164206,81.8946838988358,31.496775806217343
2022,sintomas,diarreia,Diarreia,475980,36619,283078,6295,149988,0,319697,11.454283274475518,88.54571672552449,32.83394260263036
2023,sintomas,diarreia,Diarreia,240704,18748,154161,1979,65816,0,172909,10.842697603941957,89.15730239605804,28.165298457856952
2024,sintomas,diarreia,Diarreia,229478,19455,154134,1596,54293,0,173589,11.207507388140954,88.79249261185905,24.354840115392324
2025,sintomas,diarreia,Diarreia,289913,23038,212264,1824,52787,0,235302,9.79082200746275,90.20917799253725,18.83703041947067
2026,sintomas,diarreia,Diarreia,175521,14230,130343,1356,29592,0,144573,9.842778388772453,90.15722161122754,17.632078212863416
2019,sintomas,dispneia,Dispneia,43513,35980,7030,216,287,0,43010,83.65496396186933,16.345036038130665,1.1559763748764738
2020,sintomas,dispneia,Dispneia,979812,680930,195967,10373,92542,0,876897,77.65222141254903,22.34777858745098,10.503545578131316
2021,sintomas,dispneia,Dispneia,1480215,1052319,252173,11597,164126,0,1304492,80.66887340052679,19.331126599473205,11.871451106764894
2022,sintomas,dispneia,Dispneia,475980,289046,109217,3812,73905,0,398263,72.57666416413274,27.423335835867253,16.327786881801757
2023,sintomas,dispneia,Dispneia,240704,157205,52397,1313,29789,0,209602,75.00166983139474,24.99833016860526,12.921264291411857
2024,sintomas,dispneia,Dispneia,229478,151730,52362,921,24465,0,204092,74.3439233286949,25.6560766713051,11.06249836585642
2025,sintomas,dispneia,Dispneia,289913,196590,70639,1063,21621,0,267229,73.56611744982767,26.43388255017232,7.824416290404362
2026,sintomas,dispneia,Dispneia,175521,118895,43611,603,12412,0,162506,73.16345242637195,26.83654757362805,7.41506714296295
2019,sintomas,dor_abd,Dor abdominal,43513,3,128,0,43382,0,131,2.2900763358778624,97.70992366412213,99.69894054650335
2020,sintomas,dor_abd,Dor abdominal,979812,33816,395535,20002,530459,0,429351,7.876073422444573,92.12392657755542,56.18026723493895
2021,sintomas,dor_abd,Dor abdominal,1480215,92023,881934,32085,474173,0,973957,9.448363736797415,90.55163626320258,34.20165313822654
2022,sintomas,dor_abd,Dor abdominal,475980,27852,285864,8339,153925,0,313716,8.87809356233026,91.12190643766974,34.09050800453801
2023,sintomas,dor_abd,Dor abdominal,240704,13607,154986,4379,67732,0,168593,8.070916348840106,91.9290836511599,29.958372108481786
2024,sintomas,dor_abd,Dor abdominal,229478,13416,156312,3433,56317,0,169728,7.904411764705882,92.09558823529412,26.037354343335746
2025,sintomas,dor_abd,Dor abdominal,289913,15891,214408,4754,54860,0,230299,6.900160226488174,93.09983977351183,20.562720540300024
2026,sintomas,dor_abd,Dor abdominal,175521,8970,132510,3321,30720,0,141480,6.340118744698897,93.6598812553011,19.39426051583571
2019,sintomas,fadiga,Fadiga,43513,120,120,1,43272,0,240,50.0,50.0,99.44844069588399
2020,sintomas,fadiga,Fadiga,979812,110891,330823,19316,518782,0,441714,25.10470575983555,74.89529424016445,54.918494568345764
2021,sintomas,fadiga,Fadiga,1480215,378505,662761,28740,410209,0,1041266,36.35046184164277,63.64953815835723,29.65440831230598
2022,sintomas,fadiga,Fadiga,475980,85051,241474,7177,142278,0,326525,26.047316438251283,73.95268356174873,31.39942854741796
2023,sintomas,fadiga,Fadiga,240704,38447,135984,3374,62899,0,174431,22.04138025924291,77.95861974075709,27.53298657272002
2024,sintomas,fadiga,Fadiga,229478,37086,137247,2594,52551,0,174333,21.273080828070416,78.7269191719296,24.030626029510454
2025,sintomas,fadiga,Fadiga,289913,51777,183932,3765,50439,0,235709,21.96649258195487,78.03350741804513,18.696643475801363
2026,sintomas,fadiga,Fadiga,175521,31415,112940,3062,28104,0,144355,21.76232205327145,78.23767794672855,17.75627987534255
2019,sintomas,febre,Febre,43513,38344,4874,175,120,0,43218,88.72229163774354,11.277708362256467,0.6779583113092639
2020,sintomas,febre,Febre,979812,565476,286663,14129,113544,0,852139,66.35959626305097,33.64040373694902,13.030356843965984
2021,sintomas,febre,Febre,1480215,787029,437554,16986,238646,0,1224583,64.26914304706173,35.73085695293827,17.269923625959745
2022,sintomas,febre,Febre,475980,237742,149557,4765,83916,0,387299,61.38461498738701,38.615385012613,18.63124501029455
2023,sintomas,febre,Febre,240704,139532,68262,1346,31564,0,207794,67.14919583818589,32.850804161814104,13.67239431002393
2024,sintomas,febre,Febre,229478,143886,62074,752,22766,0,205960,69.86113808506506,30.13886191493494,10.248476978185273
2025,sintomas,febre,Febre,289913,181501,85642,850,21920,0,267143,67.94151446977837,32.058485530221645,7.854080362039646
2026,sintomas,febre,Febre,175521,116362,47044,525,11590,0,163406,71.21035947272438,28.789640527275623,6.902307985939005
2019,sintomas,garganta,Dor de garganta,43513,7515,32189,2955,854,0,39704,18.92756397340318,81.07243602659682,8.75370578907453
2020,sintomas,garganta,Dor de garganta,979812,158804,573086,25461,222461,0,731890,21.69779611690281,78.30220388309719,25.30301731352545
2021,sintomas,garganta,Dor de garganta,1480215,238250,786525,28030,427410,0,1024775,23.249005879339368,76.75099412066064,30.768503224193783
2022,sintomas,garganta,Dor de garganta,475980,64636,261589,8790,140965,0,326225,19.813319028278027,80.18668097172197,31.46245640573133
2023,sintomas,garganta,Dor de garganta,240704,25913,144903,4943,64945,0,170816,15.170124578493818,84.82987542150619,29.034831161925016
2024,sintomas,garganta,Dor de garganta,229478,23923,145960,4519,55076,0,169883,14.082044701353286,85.91795529864672,25.969809742110357
2025,sintomas,garganta,Dor de garganta,289913,30842,199779,6574,52718,0,230621,13.37345688380503,86.62654311619497,20.451652737200472
2026,sintomas,garganta,Dor de garganta,175521,19601,121541,4782,29597,0,141142,13.887432514772357,86.11256748522764,19.586830065918036
2019,sintomas,outro_sin,Apresentou outros sintomas?,43513,9679,28819,1800,3215,0,38498,25.14156579562575,74.85843420437426,11.525291292257487
2020,sintomas,outro_sin,Apresentou outros sintomas?,979812,316919,402383,28311,232199,0,719302,44.05924076396284,55.94075923603717,26.58775356905202
2021,sintomas,outro_sin,Apresentou outros sintomas?,1480215,473639,553867,31743,420966,0,1027506,46.095983867734105,53.904016132265895,30.58400299956425
2022,sintomas,outro_sin,Apresentou outros sintomas?,475980,141819,184576,8224,141361,0,326395,43.45011412552275,56.54988587447725,31.426740619353755
... [44 more rows omitted]
```

### `outputs/tables/eda_02_uf_residencia_por_ano.csv`

- Git: `ignored` · `7.4 KB` · modified `2026-10-14 23:26 UTC` · 224 rows (first 60 shown)

```csv
ano_internacao,uf_residencia_categoria,quantidade,percentual_ano
2019,SP,10795,24.80867786638476
2019,PR,6555,15.064463493668558
2019,MG,3674,8.443453680509274
2019,RS,3427,7.875807230023211
2019,RJ,2209,5.076643761634454
2019,SC,2176,5.000804357318502
2019,AM,1921,4.414772596695241
2019,MS,1656,3.8057591984004784
2019,PE,1608,3.6954473375772756
2019,DF,1500,3.4472456507250704
2019,BA,1345,3.091030266816813
2019,GO,1294,2.973823914692161
2019,PA,996,2.288971112081447
2019,CE,963,2.2131317077654953
2019,ES,657,1.5098935950175811
2019,PI,414,0.9514397996001196
2019,AC,314,0.7216234228851148
2019,MT,307,0.7055362765150645
2019,RN,293,0.6733619837749638
2019,PB,278,0.6388895272677131
2019,SE,252,0.5791372693218119
2019,TO,233,0.5354721577459609
2019,MA,227,0.5216831751430607
2019,RO,156,0.35851354767540733
2019,AL,155,0.3562153839082573
2019,AP,47,0.10801369705605221
2019,Ausente ou inesperada,33,0.07583940431595156
2019,RR,28,0.06434858548020132
2020,SP,314025,32.0495156213641
2020,MG,98025,10.004470245312366
2020,RJ,91146,9.302396786322275
2020,PR,64042,6.5361518332088195
2020,RS,52287,5.336431886933412
2020,PE,40759,4.15987965038191
2020,CE,35257,3.5983433556641478
2020,BA,34485,3.5195527305238143
2020,GO,31476,3.212453001187983
2020,SC,29282,2.9885324939886426
2020,PA,27557,2.8124783121660073
2020,DF,23281,2.3760680620363903
2020,AM,20696,2.1122419402905863
2020,MS,16455,1.6794038039950523
2020,PB,14964,1.5272317546631395
2020,MT,13840,1.4125158703914629
2020,PI,11728,1.1969643156034013
2020,MA,11194,1.1424640645348292
2020,AL,9566,0.9763097410523651
2020,RN,9267,0.9457936828697749
2020,ES,8051,0.8216882422342244
2020,RO,5906,0.6027686944025997
2020,SE,5445,0.5557188521879707
2020,TO,4287,0.4375329144774712
2020,AC,2467,0.2517829951051835
2020,AP,2423,0.2472923377137655
2020,RR,1813,0.18503549660547125
2020,Ausente ou inesperada,88,0.00898131478283589
2021,SP,448900,30.326675516732365
2021,MG,191958,12.968251233773472
2021,PR,119005,8.03971044746878
2021,RJ,110165,7.44249990710809
... [164 more rows omitted]
```

### `outputs/tables/eda_02_vacinacao_por_ano.csv`

- Git: `ignored` · `2.6 KB` · modified `2026-10-14 23:26 UTC` · 16 rows

```csv
ano_internacao,grupo_clinico,coluna,nome_amigavel,quantidade_total,quantidade_sim,quantidade_nao,quantidade_ignorado,quantidade_ausente,quantidade_inesperado,quantidade_respostas_validas,percentual_sim_validos,percentual_nao_validos,percentual_sem_resposta_valida
2019,vacinacao,vacina,Recebeu vacina contra influenza?,43513,9073,19227,7241,7972,0,28300,32.06007067137809,67.9399293286219,34.96196538965366
2020,vacinacao,vacina,Recebeu vacina contra influenza?,979812,133125,277126,386783,182778,0,410251,32.449646679715585,67.5503533202844,58.12962078439538
2021,vacinacao,vacina,Recebeu vacina contra influenza?,1480215,124445,499833,493503,362434,0,624278,19.93422802020895,80.06577197979105,57.825180801437625
2022,vacinacao,vacina,Recebeu vacina contra influenza?,475980,41385,107033,149120,178442,0,148418,27.88408414073765,72.11591585926236,68.81843774948527
2023,vacinacao,vacina,Recebeu vacina contra influenza?,240704,16719,54881,63729,105375,0,71600,23.350558659217878,76.64944134078212,70.25392182930071
2024,vacinacao,vacina,Recebeu vacina contra influenza?,229478,34502,118213,24881,51882,0,152715,22.59241069966932,77.40758930033068,33.45113692815869
2025,vacinacao,vacina,Recebeu vacina contra influenza?,289913,77684,189362,6067,16800,0,267046,29.090119305288226,70.90988069471177,7.887538675395723
2026,vacinacao,vacina,Recebeu vacina contra influenza?,175521,36806,130225,1493,6997,0,167031,22.03543054882028,77.96456945117973,4.837028047925889
2019,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,43513,55,283,259,42916,0,338,16.272189349112427,83.72781065088756,99.22322064670328
2020,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,979812,24284,65967,36376,853185,0,90251,26.907181083866107,73.0928189161339,90.78894726743498
2021,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,1480215,343199,528311,243981,364724,0,871510,39.37981205034939,60.62018794965061,41.12274230432742
2022,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,475980,286756,177549,11427,248,0,464305,61.76026534282422,38.23973465717578,2.452834152695491
2023,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,240704,121641,115227,3802,34,0,236868,51.35391863822889,48.64608136177112,1.5936586014357883
2024,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,229478,109937,114985,4536,20,0,224922,48.87783320439974,51.12216679560026,1.985375504405651
2025,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,289913,175324,111918,2653,18,0,287242,61.037034973994054,38.962965026005946,0.9213108760214271
2026,vacinacao,vacina_cov,Recebeu vacina contra COVID-19?,175521,65900,107505,2094,22,0,173405,38.00351777630403,61.99648222369597,1.2055537514029662
```

### `outputs/tables/eda_02_variacao_comorbidades.csv`

- Git: `ignored` · `2.0 KB` · modified `2026-10-14 23:26 UTC` · 13 rows

```csv
grupo_clinico,coluna,nome_amigavel,percentual_sim_minimo,percentual_sim_maximo,percentual_sim_medio,percentual_sem_resposta_valida_maximo,quantidade_anos_observados,amplitude_percentual_sim,flag_variacao_10_pp
comorbidades,cardiopati,Doenca cardiovascular cronica,27.915404265431,62.54290333585488,48.691920506075256,68.1456919684824,8,34.62749907042388,True
comorbidades,diabetes,Diabetes mellitus,19.539264502969584,46.38605355415614,33.11686258606036,69.25154255046405,8,26.84678905118656,True
comorbidades,obesidade,Obesidade,4.106889969829444,22.575467273580003,9.581222489434838,71.07650890720552,8,18.468577303750557,True
comorbidades,asma,Asma,8.789636027143738,25.808949610044802,17.383991825988588,69.09942400054693,8,17.019313582901063,True
comorbidades,out_morbi,Outro fator de risco?,46.379868358849414,59.968219573853375,52.95513627159808,68.66585764666337,8,13.58835121500396,True
comorbidades,pneumopati,Outra pneumopatia cronica,9.063950734249172,18.11307166006482,15.490135863076581,69.94718580682652,8,9.049120925815647,False
comorbidades,neurologic,Doenca neurologica cronica,9.278784682568892,16.78817231710426,13.813271597855422,70.06625987773543,8,7.509387634535367,False
comorbidades,renal,Doenca renal cronica,5.950635386119258,10.730760315252667,8.180654361040396,70.6285857532717,8,4.780124929133409,False
comorbidades,imunodepre,Imunodeficiencia ou imunodepressao,5.949748279880467,10.19185377957998,8.448954005060878,70.4417135271563,8,4.2421054996995124,False
comorbidades,sind_down,Sindrome de Down,0.7262040243400194,3.7271958439047967,2.195611885124995,70.81062217495348,8,3.0009918195647773,False
comorbidades,hematologi,Doenca hematologica cronica,1.7505640404322822,3.589736057459278,2.776720143856151,70.74539683594789,8,1.8391720170269958,False
comorbidades,hepatica,Doenca hepatica cronica,1.5131964809384164,2.4796411873596105,2.032925003588078,70.94439643711779,8,0.9664447064211941,False
comorbidades,puerpera,Puerpera ou parturiente,0.7066460796357448,1.5632603406326033,0.9626067797983271,71.16167575113002,8,0.8566142609968586,False
```

### `outputs/tables/eda_02_variacao_preenchimento.csv`

- Git: `ignored` · `12.6 KB` · modified `2026-10-14 23:23 UTC` · 88 rows (first 60 shown)

```csv
coluna,nome_amigavel,grupo,uso_inicial_sugerido,preenchimento_minimo,preenchimento_maximo,preenchimento_medio,quantidade_anos_observados,amplitude_pontos_percentuais,flag_variacao_20_pp
vacina_cov,Recebeu vacina contra COVID-19?,vacinacao_covid,modelo_a_nucleo,1.3720037689885782,99.99379124082051,73.69524810117095,8,98.62178747183194,True
pov_ct,Pertence a povo ou comunidade tradicional?,demografia_contexto_social,modelo_b_ampliado,1.7787787557741366,100.0,77.24939208684502,8,98.22122124422586,True
estrang,Paciente estrangeiro?,demografia_contexto_social,modelo_b_ampliado,0.48950888240296003,96.14234194198986,68.7212896734563,8,95.6528330595869,True
trat_cov,Recebeu tratamento antiviral para COVID-19?,tratamentos,exploracao_eda,0.2091329028106543,84.40357564052164,42.821559686499626,8,84.19444273771099,True
fadiga,Fadiga,sintomas,modelo_a_nucleo,0.5538574678831614,83.98824072333225,63.4451417800059,8,83.43438325544909,True
dor_abd,Dor abdominal,sintomas,modelo_a_nucleo,0.30105945349665614,82.49782077358265,61.58550311325197,8,82.19676132008598,True
perd_olft,Perda do olfato,sintomas,modelo_a_nucleo,0.2964631259623561,82.12179739176509,61.28934723589909,8,81.82533426580272,True
perd_pala,Perda do paladar,sintomas,modelo_a_nucleo,0.2964631259623561,81.92808837688938,61.20698715442671,8,81.63162525092702,True
dt_antivir,Data de inicio do antiviral,tratamentos,exploracao_eda,2.0252463324584604,62.15154091880587,15.129731478932602,8,60.12629458634741,True
tp_antivir,Tipo de antiviral utilizado,tratamentos,exploracao_eda,2.3266890282830537,62.15383908257303,15.59245270829318,8,59.82715005428997,True
dose_1_cov,Data da primeira dose contra COVID-19,vacinacao_covid,modelo_c_sensibilidade,0.11490818835750236,56.78389848312955,31.503610601659787,8,56.668990294772044,True
dose_2_cov,Data da segunda dose contra COVID-19,vacinacao_covid,modelo_c_sensibilidade,0.0827338956174017,53.10307155762847,28.16627182870427,8,53.020337662011066,True
vacina,Recebeu vacina contra influenza?,vacinacao_influenza,modelo_a_nucleo,56.22216498271736,96.01358242033716,78.11027858451898,8,39.7914174376198,True
dt_digita,Data de inclusao do registro no sistema,desfecho_auditoria,auditoria,64.15324155999357,100.0,95.5191551949992,8,35.846758440006425,True
cs_escol_n,Escolaridade,demografia_contexto_social,modelo_b_ampliado,62.6068729900034,92.59072001470825,69.38346659273792,8,29.98384702470485,True
dose_ref,Data da dose de reforco,vacinacao_covid,modelo_c_sensibilidade,0.027577965205800567,29.40582624302047,15.387413718079475,8,29.37824827781467,True
diarreia,Diarreia,sintomas,modelo_a_nucleo,68.48859195764528,97.6030151908625,78.35231354619049,8,29.11442323321721,True
vomito,Vomito,sintomas,modelo_a_nucleo,69.08630614731712,97.6857490864799,78.52156672280701,8,28.599442939162785,True
garganta,Dor de garganta,sintomas,modelo_a_nucleo,70.38425984285054,98.03736814285386,78.85175449401551,8,27.653108300003325,True
dt_ut_dose,Data da ultima dose contra influenza,vacinacao_influenza,modelo_c_sensibilidade,3.615067859994117,27.031557743185026,12.421953651158011,8,23.41648988319091,True
outro_sin,Apresentou outros sintomas?,sintomas,exploracao_texto,70.30106306987689,92.6114034886126,76.6190544545802,8,22.310340418735706,True
cardiopati,Doenca cardiovascular cronica,comorbidades_fatores_risco,modelo_a_nucleo,31.972812370029796,54.20131617085726,39.88084611601467,8,22.228503800827465,True
diabetes,Diabetes mellitus,comorbidades_fatores_risco,modelo_a_nucleo,30.861264464081223,50.831281919388616,37.831705093167045,8,19.970017455307392,False
desc_resp,Desconforto respiratorio,sintomas,modelo_b_ampliado,79.49241564771629,99.28067474088203,88.09147763635902,8,19.78825909316575,False
out_morbi,Outro fator de risco?,comorbidades_fatores_risco,modelo_a_nucleo,31.59678898821224,50.27178683257605,38.67093063173505,8,18.67499784436381,False
saturacao,Saturacao de oxigenio abaixo de 95%?,sintomas,modelo_a_nucleo,80.70612210597083,98.51998253395537,87.20295551110405,8,17.813860427984537,False
febre,Febre,sintomas,modelo_a_nucleo,82.36984747258288,99.724220347942,89.64815865568102,8,17.354372875359118,False
dose_2ref,Data da segunda dose de reforco,vacinacao_covid,modelo_c_sensibilidade,0.011490818835750236,17.06826641850572,7.393951409341573,8,17.05677559966997,False
antiviral,Usou antiviral contra influenza?,tratamentos,exploracao_eda,83.16875691787448,99.17725737136028,87.79467548154338,8,16.00850045348581,False
obesidade,Obesidade,comorbidades_fatores_risco,modelo_a_nucleo,29.189669612183156,44.106930717321276,34.477271994400375,8,14.91726110513812,False
dispneia,Dispneia,sintomas,modelo_a_nucleo,84.4730871045002,99.34042699882794,90.71430629302054,8,14.867339894327742,False
renal,Doenca renal cronica,comorbidades_fatores_risco,modelo_a_nucleo,29.509289486728086,44.01293309328728,34.484323304899206,8,14.503643606559194,False
neurologic,Doenca neurologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,30.075603489041196,44.33074916412536,35.08167299397847,8,14.255145675084162,False
pneumopati,Outra pneumopatia cronica,comorbidades_fatores_risco,modelo_a_nucleo,30.224873376974838,44.36840944997612,35.11054682651589,8,14.143536073001282,False
imunodepre,Imunodeficiencia ou imunodepressao,comorbidades_fatores_risco,modelo_a_nucleo,29.744019234165712,43.634391087269805,34.61434698338411,8,13.890371853104092,False
hepatica,Doenca hepatica cronica,comorbidades_fatores_risco,modelo_a_nucleo,29.30190689433173,43.10000285769107,33.99751434848719,8,13.798095963359337,False
hematologi,Doenca hematologica cronica,comorbidades_fatores_risco,modelo_a_nucleo,29.43408481036457,43.2067580311325,34.15381421394807,8,13.772673220767931,False
puerpera,Puerpera ou parturiente,comorbidades_fatores_risco,modelo_a_nucleo,29.14949481520872,42.91476324029508,33.87844337445482,8,13.765268425086362,False
sind_down,Sindrome de Down,comorbidades_fatores_risco,modelo_a_nucleo,29.455164909042225,43.02723379587105,34.09069125051857,8,13.572068886828824,False
morb_desc,Descricao de outro fator de risco,comorbidades_fatores_risco,exploracao_texto,14.327630312042434,27.46200291484489,20.20725676496904,8,13.134372602802458,False
asma,Asma,comorbidades_fatores_risco,modelo_a_nucleo,31.021928999948724,43.95588133233723,35.34392023154777,8,12.933952332388504,False
ave_suino,"Contato direto com aves, suinos ou outro animal?",exposicao_animal,modelo_a_nucleo,84.30113193015879,97.09971732585664,88.01868326298013,8,12.798585395697856,False
mae_vac,Mae vacinada contra influenza?,vacinacao_influenza,modelo_c_sensibilidade,0.7310586112437897,12.761703398984212,4.923902874079337,8,12.030644787740423,False
tosse,Tosse,sintomas,modelo_a_nucleo,87.88562544644734,99.65987176246179,93.04977621340292,8,11.774246316014455,False
m_amamenta,Mae amamenta a crianca?,vacinacao_influenza,modelo_c_sensibilidade,0.5424510008042359,11.456346379242985,4.555187515347466,8,10.913895378438749,False
dos_re_bi,Data do reforco bivalente,vacinacao_covid,modelo_c_sensibilidade,0.006894491301450142,10.596627264041283,4.744728731219468,8,10.589732772739833,False
outro_des,Descricao dos outros sintomas,sintomas,exploracao_texto,21.745225564773747,31.817838524125037,28.016747509063443,8,10.07261295935129,False
cs_zona,Zona de residencia,demografia_contexto_social,modelo_a_nucleo,90.26607621190165,97.66046928504124,92.88527194536411,8,7.394393073139597,False
dt_1_dose,Data da primeira dose infantil,vacinacao_influenza,modelo_c_sensibilidade,0.004256138466371439,4.155058369084042,0.921300198896669,8,4.15080223061767,False
co_mu_inte,Municipio de internacao,geografia_internacao,exploracao_eda,92.45785240657607,96.59498803509705,95.3173196342878,8,4.13713562852098,False
sg_uf_inte,UF de internacao,geografia_internacao,derivar_atributo,92.45785240657607,96.59498803509705,95.3173196342878,8,4.13713562852098,False
co_rg_inte,Regional de saude de internacao,geografia_internacao,exploracao_eda,82.4095504513423,86.39487049847172,84.00134941445134,8,3.98532004712942,False
dt_evoluca,Data da alta ou do obito,desfecho_auditoria,auditoria,92.4367430423092,96.30830656357354,94.65558083818499,8,3.871563521264335,False
dt_doseuni,Data da dose unica infantil,vacinacao_influenza,modelo_c_sensibilidade,0.004256138466371439,3.85196073404322,0.8601828967129729,8,3.8477045955768485,False
co_rg_resi,Regional de saude de residencia,geografia_residencia,exploracao_eda,87.49321298371524,91.12219336749938,88.85143013154557,8,3.628980383784139,False
co_regiona,Regional de saude da notificacao,geografia_notificacao,exploracao_eda,86.37349825637347,89.97540964769149,87.99494897634035,8,3.6019113913180263,False
cs_raca,Raca ou cor,demografia_contexto_social,modelo_a_nucleo,96.54815802174063,100.0,99.14130769571072,8,3.451841978259367,False
dt_vac_mae,Data da vacinacao materna,vacinacao_influenza,modelo_c_sensibilidade,0.03391399222410258,2.387792154068899,0.4621145951128455,8,2.3538781618447966,False
pac_cocbo,Codigo da ocupacao,demografia_contexto_social,reavaliar_apos_modelo_principal,0.01608714637005033,2.319730579679303,1.0227116064525472,8,2.3036434333092526,False
pac_dscbo,Descricao da ocupacao,demografia_contexto_social,apoio_interpretacao,0.01608714637005033,2.319730579679303,1.0227116064525472,8,2.3036434333092526,False
... [28 more rows omitted]
```

### `outputs/tables/eda_02_variacao_sintomas.csv`

- Git: `ignored` · `1.9 KB` · modified `2026-10-14 23:26 UTC` · 13 rows

```csv
grupo_clinico,coluna,nome_amigavel,percentual_sim_minimo,percentual_sim_maximo,percentual_sim_medio,percentual_sem_resposta_valida_maximo,quantidade_anos_observados,amplitude_percentual_sim,flag_variacao_10_pp
sintomas,fadiga,Fadiga,21.273080828070416,50.0,28.068219970283657,99.44844069588399,8,28.726919171929584,True
sintomas,febre,Febre,61.38461498738701,88.72229163774354,69.61223172512462,18.63124501029455,8,27.337676650356528,True
sintomas,desc_resp,Desconforto respiratorio,63.90864654416326,85.05905099117147,73.68918759004444,21.430312197991512,8,21.150404447008214,True
sintomas,outro_sin,Apresentou outros sintomas?,25.14156579562575,46.095983867734105,38.57198951252496,31.426740619353755,8,20.954418072108357,True
sintomas,tosse,Tosse,76.0662108853592,93.37900071740992,83.2678499659398,12.946497637167573,8,17.312789832050726,True
sintomas,saturacao,Saturacao de oxigenio abaixo de 95%?,61.01212055103913,76.99078255707443,66.69674051217274,20.202949703769065,8,15.978662006035293,True
sintomas,perd_olft,Perda do olfato,0.7936507936507936,12.797014767158363,4.201351397889889,99.71043136533909,8,12.003363973507568,True
sintomas,perd_pala,Perda do paladar,1.574803149606299,13.049298893290151,4.377449342323514,99.70813320157194,8,11.474495743683853,True
sintomas,dispneia,Dispneia,72.57666416413274,83.65496396186933,76.32848574692089,16.327786881801757,8,11.078299797736591,True
sintomas,garganta,Dor de garganta,13.37345688380503,23.249005879339368,17.525092959543485,31.46245640573133,8,9.875548995534338,False
sintomas,diarreia,Diarreia,9.454563139848746,18.105316101164206,12.17856355107877,32.83394260263036,8,8.65075296131546,False
sintomas,dor_abd,Dor abdominal,2.2900763358778624,9.448363736797415,7.213526767772896,99.69894054650335,8,7.158287400919552,False
sintomas,vomito,Vomito,12.228737980517804,16.03842412451362,14.638187728743688,32.642825535479645,8,3.809686143995817,False
```

### `outputs/tables/eda_02_volume_por_ano.csv`

- Git: `ignored` · `368 B` · modified `2026-10-14 23:22 UTC` · 8 rows

```csv
ano_internacao,quantidade_registros,percentual_coorte,periodo_completo
2019,43513,1.1114045591264263,True
2020,979812,25.026257069997058,True
2021,1480215,37.807498896590054,True
2022,475980,12.157432078987805,True
2023,240704,6.148036747637885,True
2024,229478,5.861303413214764,True
2025,289913,7.404927951417268,True
2026,175521,4.483139283028738,False
```

### `outputs/tables/supervisionado_registros_conflitantes_split_provisorio.csv`

- Git: `ignored` · `376 B` · modified `2026-10-14 23:31 UTC` · 4 rows

```csv
indice_original,grupo_split,estrato_split,nu_notific,ano_internacao,alvo_obito_srag,evolucao,dt_interna
653105,31736866916969,2024__y0,31736866916969,2024,0,1,2024-01-14
263526,31736866916969,2025__y0,31736866916969,2025,0,1,2025-01-14
483104,31745324608735,2024__y1,31745324608735,2024,1,2,2024-08-15
196104,31745324608735,2025__y1,31745324608735,2025,1,2,2025-04-16
```

### `outputs/tables/supervisionado_resumo_conflitos_split_provisorio.csv`

- Git: `ignored` · `154 B` · modified `2026-10-14 23:31 UTC` · 2 rows

```csv
grupo_split,quantidade_linhas,quantidade_estratos,estratos_observados
31736866916969,2,2,2024__y0 | 2025__y0
31745324608735,2,2,2024__y1 | 2025__y1
```

### `outputs/tables/supervisionado_waterfall_conflitos_split_provisorio.csv`

- Git: `ignored` · `181 B` · modified `2026-10-14 23:31 UTC` · 1 rows

```csv
etapa,politica,grupos_conflitantes,linhas_excluidas,linhas_restantes,status
quarentena_conflitos_split,quarentena_provisoria,2,4,3915132,provisoria_pendente_validacao_pessoa_a
```

## 19. Snapshot provenance

- Generated UTC: `2026-10-15T12:52:01+00:00`
- Branch / commit: `main` / `77e533263f91aeee3430dcd5cfd5560fed7e8c53`
- Origin: `https://github.com/Ivan-S-Oliveira/Projeto_Integrador.git`
- Generator options: `{'output_dir': 'docs', 'config': 'configs/supervised.yaml', 'split_mb': 1.0, 'split': True, 'notebook_outputs': True, 'max_output_chars': 6000, 'artifacts': True, 'max_artifact_bytes': 300000, 'max_csv_rows': 60, 'max_inline_bytes': 4000000, 'git_log': 40, 'include_diff': True, 'max_diff_chars': 400000, 'run_tests': False, 'pytest_args': '', 'test_timeout': 1800, 'fail_on_high': False}`
