"""Geração dos datasets analíticos (clustering e supervisionado).

Recebe a coorte provisória da Pessoa A e produz dois artefatos:

- ``dataset_clustering.parquet``
    Variáveis de apresentação na admissão, sem alvo, sem itens de
    ``features.proibidas`` e sem colunas pós-admissão.

- ``dataset_supervisionado.parquet``
    Features finais + coluna de alvo (``evolucao`` bruto) + coluna de
    tempo + identificador de linha. É o arquivo consumido pelo
    ``notebooks/C/C2_pipeline_supervisionado.ipynb``.

Cada geração grava também ``manifest.json`` com SHA-256 da coorte de
origem, SHA-256 do ``supervised.yaml``, contagens, contagem por ano,
ausência por coluna, data de geração e seed. A execução é registrada
por ``Run`` em ``outputs/runs/<RUN_ID>/``.

Pré-condição
------------
A coorte provisória precisa existir em ``data/analytical/`` (ou ser
indicada explicitamente). Este módulo NÃO constrói a coorte — apenas
consome a que a Pessoa A produz. Use ``carregar_coorte_provisoria()``
para localizá-la com uma mensagem clara quando ela ainda não existir.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.evaluation.leakage import LeakageError, check_leakage
from src.features.engineering import montar_features
from src.utils import config as C
from src.utils.reproducibility import Run
from src.utils.storage import read_sha256


__all__ = [
    "COLUNA_ID",
    "ARQUIVO_CLUSTERING",
    "ARQUIVO_SUPERVISIONADO",
    "ARQUIVO_MANIFESTO",
    "carregar_coorte_provisoria",
    "gerar_datasets",
]


# Identificador de linha. Reconstruído como `0..N-1` após `reset_index`,
# de modo que aponta para a posição da linha na coorte como recebida.
COLUNA_ID: str = "linha_id"

ARQUIVO_CLUSTERING: str = "dataset_clustering.parquet"
ARQUIVO_SUPERVISIONADO: str = "dataset_supervisionado.parquet"
ARQUIVO_MANIFESTO: str = "manifest.json"

# Colunas exigidas para `montar_features` funcionar.
_ENTRADAS_DERIVACAO: tuple[str, ...] = (
    "nu_idade_n",
    "tp_idade",
    "dt_sin_pri",
    "dt_interna",
)

# Locais convencionais onde a coorte provisória pode aparecer.
_COORTE_CANDIDATOS: tuple[Path, ...] = (
    C.ANALYTICAL_DIR / "coorte_provisoria.parquet",
    C.ANALYTICAL_DIR / "coorte.parquet",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256_file(path: Path) -> str:
    """SHA-256 hex do conteúdo de ``path`` (lido em blocos de 1 MiB)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _clustering_features() -> list[str]:
    """
    Lista de features de clustering (``clustering.features`` do YAML).

    Levanta ``ValueError`` se o bloco estiver ausente ou vazio.
    """
    bruto = C.cfg("clustering", "features")
    if not bruto:
        raise ValueError(
            "`clustering.features` não está definido em "
            "`configs/supervised.yaml`. Declare a lista de variáveis "
            "de apresentação na admissão antes de gerar o dataset de "
            "clustering."
        )
    return list(bruto)


def _validar_entradas_derivacao(df: pd.DataFrame, coluna_tempo: str) -> None:
    """Garante que a coorte tem as colunas exigidas por ``montar_features``."""
    faltando = [c for c in _ENTRADAS_DERIVACAO if c not in df.columns]
    if coluna_tempo not in df.columns:
        faltando.append(coluna_tempo)
    if faltando:
        raise KeyError(
            "Colunas necessárias para `montar_features` ausentes na "
            f"coorte: {sorted(faltando)}. Verifique a coorte da Pessoa A "
            "antes de chamar `gerar_datasets`."
        )


def _n_por_ano(df: pd.DataFrame, coluna_tempo: str) -> dict[str, int]:
    """Contagem de linhas por ano da coluna temporal (ordenada)."""
    anos = pd.to_datetime(df[coluna_tempo], errors="coerce").dt.year
    contagem = anos.value_counts(dropna=False).sort_index()
    return {str(k): int(v) for k, v in contagem.items()}


def _ausencia_pct(df: pd.DataFrame) -> dict[str, float]:
    """Percentual de valores ausentes por coluna (0 a 100)."""
    n = len(df)
    if n == 0:
        return {c: 0.0 for c in df.columns}
    return {
        c: float(df[c].isna().sum()) / n * 100.0
        for c in df.columns
    }


# ---------------------------------------------------------------------------
# Carregamento da coorte provisória
# ---------------------------------------------------------------------------

def carregar_coorte_provisoria(caminho: Path | None = None) -> pd.DataFrame:
    """
    Carrega a coorte provisória da Pessoa A.

    Se ``caminho`` for None, procura em locais convencionais
    (``data/analytical/coorte_provisoria.parquet`` e
    ``data/analytical/coorte.parquet``). Se não encontrar, levanta
    ``FileNotFoundError`` com a lista do que é esperado.

    Parâmetros
    ----------
    caminho : Path | None
        Caminho explícito do Parquet.

    Retorno
    -------
    pd.DataFrame
        Coorte carregada em memória.

    Levanta
    ------
    FileNotFoundError
        Quando nenhum candidato existe e ``caminho`` é None.
    """
    if caminho is not None:
        p = Path(caminho)
        if not p.exists():
            raise FileNotFoundError(
                f"Coorte provisória não encontrada em {p}."
            )
        return pd.read_parquet(p)

    for p in _COORTE_CANDIDATOS:
        if p.exists():
            return pd.read_parquet(p)

    coluna_tempo = C.cfg("coluna_tempo")
    alvo = C.cfg("target", "coluna")

    raise FileNotFoundError(
        "Coorte provisória da Pessoa A não encontrada. Procurado em:\n"
        + "\n".join(f"  - {p}" for p in _COORTE_CANDIDATOS)
        + "\n\nO que é esperado no arquivo:\n"
        + f"  - Colunas de derivação: {list(_ENTRADAS_DERIVACAO)}\n"
        + f"  - Coluna temporal: {coluna_tempo!r}\n"
        + f"  - Alvo bruto (rótulo original): {alvo!r}\n"
        + "  - Features declaradas em `features.numericas` (exceto "
        + "derivadas) e `features.categoricas` do supervised.yaml.\n"
        + "\nSe a coorte já existe em outro caminho, passe-o "
        + "explicitamente: `carregar_coorte_provisoria(Path(...))`."
    )


# ---------------------------------------------------------------------------
# Geração dos datasets
# ---------------------------------------------------------------------------

def gerar_datasets(
    df_coorte: pd.DataFrame,
    *,
    coorte_path: Path | None = None,
    salvar: bool = True,
    registrar: bool = True,
    output_dir: Path | None = None,
    run_output_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Gera os datasets de clustering e supervisionado a partir da coorte.

    O ``linha_id`` é reconstruído como ``0..N-1`` após ``reset_index``,
    apontando para a posição da linha na coorte **como recebida**. Esse
    identificador é preservado nos dois DataFrames, permitindo cruzar
    clustering ↔ supervisionado linha a linha.

    O dataset de clustering NÃO contém o alvo nem qualquer coluna em
    ``features.proibidas``; o dataset supervisionado contém as features
    finais, a coluna de tempo e o alvo bruto (``evolucao``).

    Parâmetros
    ----------
    df_coorte : pd.DataFrame
        Coorte provisória da Pessoa A. Precisa conter as colunas
        exigidas por ``montar_features`` (``nu_idade_n``, ``tp_idade``,
        ``dt_sin_pri``, ``dt_interna``, ``coluna_tempo``), o alvo bruto
        e as features do YAML.
    coorte_path : Path | None
        Caminho do Parquet de origem, se conhecido. Usado no manifesto
        (SHA-256 da origem) e no ``Run``. Se None, o manifesto registra
        ``null`` nesses campos.
    salvar : bool
        Se True (default), grava os Parquets e o manifesto.
    registrar : bool
        Se True (default), registra a execução com ``Run``.
    output_dir : Path | None
        Diretório de saída dos Parquets e do manifesto. Se None, usa
        ``C.ANALYTICAL_DIR``.
    run_output_dir : Path | None
        Diretório de runs do ``Run``. Se None, usa ``C.RUNS_DIR``.

    Retorno
    -------
    dict[str, pd.DataFrame]
        ``{"clustering": df_clust, "supervisionado": df_super}``.

    Levanta
    ------
    KeyError
        Quando a coorte não contém colunas exigidas.
    LeakageError
        Quando o dataset de clustering (ou o X do supervisionado)
        contém alguma coluna de ``features.proibidas`` — o que só pode
        acontecer se ``clustering.features`` do YAML incluir uma delas.
    ValueError
        Quando o alvo aparece no dataset de clustering ou quando
        ``linha_id`` deixa de ser único.
    """
    if not isinstance(df_coorte, pd.DataFrame):
        raise TypeError(
            f"`df_coorte` deve ser um DataFrame; veio "
            f"{type(df_coorte).__name__}."
        )
    if df_coorte.empty:
        raise ValueError("`df_coorte` está vazio.")

    coluna_tempo = C.cfg("coluna_tempo")
    if not coluna_tempo:
        raise ValueError("`coluna_tempo` ausente no supervised.yaml.")
    alvo = C.cfg("target", "coluna")
    if not alvo:
        raise ValueError("`target.coluna` ausente no supervised.yaml.")

    _validar_entradas_derivacao(df_coorte, coluna_tempo)

    if alvo not in df_coorte.columns:
        raise KeyError(
            f"Coluna de alvo {alvo!r} ausente na coorte. "
            "A coorte precisa carregar o rótulo bruto para que este "
            "módulo possa gerar o dataset supervisionado."
        )

    # Import tardio para evitar ciclo na importação de src.models.
    from src.models.pipeline import FEATURES

    clustering_features = _clustering_features()

    # ------------------------------------------------------------------
    # Vazamento: `clustering.features` não pode tocar em proibidas
    # ------------------------------------------------------------------
    proibidas = set(C.cfg("features", "proibidas") or [])
    vazamento = proibidas.intersection(clustering_features)
    if vazamento:
        raise LeakageError(
            "`clustering.features` contém colunas proibidas: "
            f"{sorted(vazamento)}. Essas colunas vazam o alvo — remova-as "
            "de `clustering.features` no configs/supervised.yaml."
        )

    # ------------------------------------------------------------------
    # Derivação
    # ------------------------------------------------------------------
    df_base = df_coorte.reset_index(drop=True).copy()
    df_feat = montar_features(df_base)
    df_feat[COLUNA_ID] = range(len(df_feat))

    # ------------------------------------------------------------------
    # Dataset de clustering
    # ------------------------------------------------------------------
    faltando_clust = [c for c in clustering_features if c not in df_feat.columns]
    if faltando_clust:
        raise KeyError(
            "`clustering.features` referencia colunas que não existem "
            f"após `montar_features`: {sorted(faltando_clust)}."
        )
    colunas_clust = [COLUNA_ID] + clustering_features
    df_clust = df_feat[colunas_clust].copy()

    # ------------------------------------------------------------------
    # Dataset supervisionado
    # ------------------------------------------------------------------
    faltando_sup = [c for c in FEATURES if c not in df_feat.columns]
    if faltando_sup:
        raise KeyError(
            "`features` do YAML referenciam colunas que não existem "
            f"após `montar_features`: {sorted(faltando_sup)}."
        )
    colunas_sup = [COLUNA_ID, coluna_tempo] + list(FEATURES) + [alvo]
    colunas_sup = list(dict.fromkeys(colunas_sup))  # remove duplicatas
    df_super = df_feat[colunas_sup].copy()

    # ------------------------------------------------------------------
    # Validações explícitas
    # ------------------------------------------------------------------
    if alvo in df_clust.columns:
        raise ValueError(
            f"Coluna de alvo {alvo!r} presente no dataset de clustering — "
            "isso não pode acontecer."
        )
    check_leakage(df_clust)

    X_sup = df_super.drop(columns=[alvo])
    check_leakage(X_sup)

    if not df_clust[COLUNA_ID].is_unique:
        raise ValueError("`linha_id` duplicado no dataset de clustering.")
    if not df_super[COLUNA_ID].is_unique:
        raise ValueError("`linha_id` duplicado no dataset supervisionado.")

    # ------------------------------------------------------------------
    # Manifesto
    # ------------------------------------------------------------------
    source_sha256: str | None = None
    if coorte_path is not None:
        cp = Path(coorte_path)
        source_sha256 = read_sha256(cp)
        if source_sha256 is None and cp.exists():
            source_sha256 = _sha256_file(cp)

    manifest: dict[str, Any] = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "seed": int(C.SEED),
        "supervised_yaml_sha256": C.supervised_yaml_sha256(),
        "coorte_origem": {
            "caminho": str(coorte_path) if coorte_path is not None else None,
            "sha256": source_sha256,
            "n_linhas": int(len(df_coorte)),
            "n_colunas": int(df_coorte.shape[1]),
            "n_por_ano": _n_por_ano(df_coorte, coluna_tempo),
        },
        "clustering": {
            "arquivo": ARQUIVO_CLUSTERING,
            "n_linhas": int(len(df_clust)),
            "n_colunas": int(df_clust.shape[1]),
            "colunas": list(df_clust.columns),
            "ausencia_pct": _ausencia_pct(df_clust),
        },
        "supervisionado": {
            "arquivo": ARQUIVO_SUPERVISIONADO,
            "n_linhas": int(len(df_super)),
            "n_colunas": int(df_super.shape[1]),
            "colunas": list(df_super.columns),
            "ausencia_pct": _ausencia_pct(df_super),
        },
    }

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------
    if salvar:
        destino = Path(output_dir) if output_dir is not None else C.ANALYTICAL_DIR
        destino.mkdir(parents=True, exist_ok=True)

        path_clust = destino / ARQUIVO_CLUSTERING
        path_super = destino / ARQUIVO_SUPERVISIONADO

        df_clust.to_parquet(path_clust, index=False)
        df_super.to_parquet(path_super, index=False)

        manifest["clustering"]["sha256"] = _sha256_file(path_clust)
        manifest["supervisionado"]["sha256"] = _sha256_file(path_super)

        (destino / ARQUIVO_MANIFESTO).write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Registro
    # ------------------------------------------------------------------
    if registrar:
        with Run(
            modelo="analitico",
            parametros={
                "coluna_tempo": coluna_tempo,
                "alvo": alvo,
                "n_features_supervisionado": len(FEATURES),
                "n_features_clustering": len(clustering_features),
            },
            notas=(
                "Geração dos datasets analíticos a partir da coorte "
                "provisória da Pessoa A."
            ),
            output_dir=run_output_dir,
            dataset_path=Path(coorte_path) if coorte_path is not None else None,
            dataset_sha256=source_sha256,
        ) as r:
            r.add_dataset(
                n_coorte=int(len(df_coorte)),
                n_clustering=int(len(df_clust)),
                n_supervisionado=int(len(df_super)),
            )
            r.metrica(
                n_colunas_clustering=int(df_clust.shape[1]),
                n_colunas_supervisionado=int(df_super.shape[1]),
            )

    return {"clustering": df_clust, "supervisionado": df_super}