"""Persistência e leitura do dataset supervisionado canônico.

O artefato pode existir em **dois esquemas**:

- **legado** (coorte provisória): ``treino``, ``validacao``, ``teste``;
- **blocos** (partição-mestre): ``train_ref``, ``val_tune``, ``val_cal``,
  ``val_meas``, ``test_ref``, ``test_pandemic`` (+ ``exploracao`` opcional
  para 2026).

O esquema é detectado pelos valores de ``partition_counts`` no manifesto;
nunca é preciso informá-lo ao chamador.

Proteção do teste:

- qualquer partição de teste (``teste``, ``test_ref`` ou ``test_pandemic``)
  exige ``G9_holdout`` aprovado — ``GatePendenteError`` é levantado antes
  de tocar no arquivo;
- ``exploracao`` exige ``temporal.exploracao_2026.ativa: true``.
"""

from __future__ import annotations

import gc
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from src.data.cohort_source import load_cohort
from src.data.split import criar_group_id, criar_particao_mestra
from src.features.engineering import montar_features, regiao_residencia
from src.utils import config as C
from src.utils.config import GatePendenteError, exigir_gate
from src.utils.hashing import sha256_file

__all__ = [
    "ALLOWED_PARTITIONS",
    "BLOCKS_PADRAO_LEITURA",
    "BLOCKS_TESTE",
    "BLOCOS_MESTRE",
    "DATASET_NAME",
    "MANIFEST_NAME",
    "SCHEMA_VERSION",
    "GatePendenteError",
    "gerar_artefato_supervisionado",
    "holdout_partition",
    "load_supervised_artifact",
    "persist_supervised_artifact",
    "split_partitions",
    "validate_supervised_frame",
]

# DONO ÚNICO deste arquivo: gerar_artefato_supervisionado.
# Nenhum notebook A deve gravar aqui (ver #73).
DATASET_NAME = "dataset_supervisionado.parquet"
MANIFEST_NAME = "manifesto_supervisionado.json"
SCHEMA_VERSION = 2

# --- Esquema legado --------------------------------------------------------
_PARTITION_TREINO = "treino"
_PARTITION_VALIDACAO = "validacao"
_PARTITION_TESTE = "teste"
_PARTICOES_LEGADAS: frozenset[str] = frozenset(
    {_PARTITION_TREINO, _PARTITION_VALIDACAO, _PARTITION_TESTE}
)

# --- Esquema de blocos da partição-mestre ---------------------------------
_BLOCK_TRAIN_REF = "train_ref"
_BLOCK_VAL_TUNE = "val_tune"
_BLOCK_VAL_CAL = "val_cal"
_BLOCK_VAL_MEAS = "val_meas"
_BLOCK_TEST_REF = "test_ref"
_BLOCK_TEST_PANDEMIC = "test_pandemic"
_BLOCK_EXPLORACAO = "exploracao"

BLOCOS_MESTRE: tuple[str, ...] = (
    _BLOCK_TRAIN_REF,
    _BLOCK_VAL_TUNE,
    _BLOCK_VAL_CAL,
    _BLOCK_VAL_MEAS,
    _BLOCK_TEST_REF,
    _BLOCK_TEST_PANDEMIC,
    _BLOCK_EXPLORACAO,
)

BLOCKS_TESTE: frozenset[str] = frozenset({_BLOCK_TEST_REF, _BLOCK_TEST_PANDEMIC})

BLOCKS_PADRAO_LEITURA: tuple[str, ...] = (
    _BLOCK_TRAIN_REF,
    _BLOCK_VAL_TUNE,
    _BLOCK_VAL_CAL,
    _BLOCK_VAL_MEAS,
)

_BLOCOS_OBRIGATORIOS: frozenset[str] = frozenset(BLOCOS_MESTRE) - {_BLOCK_EXPLORACAO}

# Toda string reconhecida como partição (qualquer um dos dois esquemas).
ALLOWED_PARTITIONS: frozenset[str] = _PARTICOES_LEGADAS | frozenset(BLOCOS_MESTRE)

# Combinações de partição consideradas artefatos completos.
_ESQUEMAS_COMPLETOS: frozenset[frozenset[str]] = frozenset(
    {
        _PARTICOES_LEGADAS,
        _BLOCOS_OBRIGATORIOS,
        frozenset(BLOCOS_MESTRE),
    }
)

# Partições que acionam o gate de teste.
_PARTICOES_DE_TESTE: frozenset[str] = BLOCKS_TESTE | {_PARTITION_TESTE}


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _paths(root: Path) -> tuple[Path, Path]:
    output_dir = Path(root).resolve() / "data" / "analytical"
    return output_dir / DATASET_NAME, output_dir / MANIFEST_NAME


def _normalizar_kind(kind: Any) -> str:
    return str(kind or "").strip().lower()


def _esquema_do_manifest(manifest: Mapping[str, Any]) -> str:
    """Devolve ``"blocos"`` ou ``"legado"`` a partir do ``partition_counts``."""
    valores = {str(k) for k in (manifest.get("partition_counts") or {})}
    if valores & set(BLOCOS_MESTRE):
        return "blocos"
    if valores & _PARTICOES_LEGADAS:
        return "legado"
    raise ValueError(
        f"Manifesto sem partições reconhecidas: {sorted(valores)}. "
        f"Esperado algum de {sorted(ALLOWED_PARTITIONS)}."
    )


def _validar_particoes_completas(observed: set[str]) -> None:
    """Exige que ``observed`` seja exatamente um dos esquemas completos."""
    observed_fs = frozenset(observed)

    if observed_fs in _ESQUEMAS_COMPLETOS:
        return

    tem_legado = bool(observed_fs & _PARTICOES_LEGADAS)
    tem_blocos = bool(observed_fs & set(BLOCOS_MESTRE))

    if tem_legado and tem_blocos:
        raise ValueError(
            "Artefato misturou esquemas de partição: "
            f"legado={sorted(observed_fs & _PARTICOES_LEGADAS)}, "
            f"blocos={sorted(observed_fs & set(BLOCOS_MESTRE))}."
        )

    esperados = "; ".join(str(sorted(esquema)) for esquema in sorted(_ESQUEMAS_COMPLETOS, key=len))
    raise ValueError(
        f"Partições incompletas. Observado: {sorted(observed_fs)}. "
        f"Esquemas completos válidos: {esperados}."
    )


def _particoes_por_papel(manifest: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    """Mapeia papel agregado (treino/validacao/teste) para nomes reais no artefato."""
    if _esquema_do_manifest(manifest) == "blocos":
        return {
            "treino": (_BLOCK_TRAIN_REF,),
            "validacao": (_BLOCK_VAL_TUNE, _BLOCK_VAL_CAL, _BLOCK_VAL_MEAS),
            "teste": (_BLOCK_TEST_REF, _BLOCK_TEST_PANDEMIC),
        }
    return {
        "treino": (_PARTITION_TREINO,),
        "validacao": (_PARTITION_VALIDACAO,),
        "teste": (_PARTITION_TESTE,),
    }


def _filtrar_particoes(
    frame: pd.DataFrame,
    coluna: str,
    particoes: Sequence[str],
) -> pd.DataFrame:
    if coluna not in frame.columns:
        raise KeyError(f"Coluna de partição ausente no DataFrame: {coluna!r}")
    mascara = frame[coluna].astype(str).isin(tuple(particoes))
    return frame.loc[mascara].reset_index(drop=True)


def _exigir_exploracao_ativa() -> None:
    ativa = bool(C.cfg("temporal", "exploracao_2026", "ativa") or False)
    if not ativa:
        raise RuntimeError(
            "Bloco 'exploracao' (2026) pedido, mas "
            "temporal.exploracao_2026.ativa=false no configs/supervised.yaml."
        )


def _validar_grupos(num_set: set[str], cat_set: set[str], feats_set: set[str]) -> None:
    if overlap := num_set & cat_set:
        raise ValueError(
            f"Colunas em numeric_columns E categorical_columns: {sorted(overlap)}"
        )
    if fora := (num_set | cat_set) - feats_set:
        raise ValueError(
            f"numeric_columns/categorical_columns contém colunas fora de "
            f"feature_columns: {sorted(fora)}"
        )
    if faltando := feats_set - (num_set | cat_set):
        raise ValueError(
            "Cada feature precisa estar em numeric_columns ou categorical_columns. "
            f"Faltando: {sorted(faltando)}"
        )


def _resolver_grupos(
    feature_columns: Sequence[str],
    numeric_columns: Sequence[str] | None,
    categorical_columns: Sequence[str] | None,
) -> tuple[list[str] | None, list[str] | None]:
    """Resolve o par (numéricas, categóricas).

    - ambas ``None`` → ``(None, None)``
    - apenas uma informada → o complemento é inferido dentro de ``feature_columns``
    - ambas informadas → valida disjunção e cobertura exata
    """
    if numeric_columns is None and categorical_columns is None:
        return None, None

    if numeric_columns is not None and categorical_columns is not None:
        num = list(numeric_columns)
        cat = list(categorical_columns)
    elif categorical_columns is not None:
        cat = list(categorical_columns)
        cat_set = set(cat)
        num = [c for c in feature_columns if c not in cat_set]
    else:
        assert numeric_columns is not None
        num = list(numeric_columns)
        num_set = set(num)
        cat = [c for c in feature_columns if c not in num_set]

    _validar_grupos(set(num), set(cat), set(feature_columns))
    return num, cat


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------

def validate_supervised_frame(
    frame: pd.DataFrame,
    *,
    feature_columns: Sequence[str],
    target_column: str,
    partition_column: str,
    audit_columns: Sequence[str] | None = None,
    required_partitions: Sequence[str] | None = None,
) -> None:
    """Valida schema mínimo, alvo binário e partições do dataset.

    ``required_partitions=None`` aceita qualquer um dos esquemas completos
    (legado, blocos sem ``exploracao`` ou blocos com ``exploracao``).
    Um subconjunto permite validar leituras parciais.
    """
    required = set(feature_columns) | {target_column, partition_column}
    if audit_columns:
        required |= set(audit_columns)

    if missing := sorted(required - set(frame.columns)):
        raise KeyError(f"Colunas ausentes no dataset supervisionado: {missing}")

    if frame.empty:
        raise ValueError("O dataset supervisionado não pode ser vazio.")

    target_values = set(
        pd.to_numeric(frame[target_column], errors="coerce")
        .dropna().astype(int).unique()
    )
    if not target_values or not target_values.issubset({0, 1}):
        raise ValueError(
            f"Alvo deve ser binário 0/1. Observado: {sorted(target_values)}"
        )

    observed = set(frame[partition_column].dropna().astype(str).unique())

    if required_partitions is not None:
        expected = frozenset(required_partitions)
        if unknown := expected - ALLOWED_PARTITIONS:
            raise ValueError(f"Partições desconhecidas: {sorted(unknown)}")
        if observed != expected:
            raise ValueError(
                f"Partições esperadas {sorted(expected)}. "
                f"Observado: {sorted(observed)}"
            )
    else:
        _validar_particoes_completas(observed)


def _validate_partial_load(
    frame: pd.DataFrame,
    *,
    target_column: str,
    partition_column: str,
    expected_partitions: set[str],
) -> None:
    """Validação mínima quando ``columns=`` restringe a leitura.

    Não substitui ``validate_supervised_frame`` (features não foram lidas).
    Confere apenas o que sustenta a integridade das partições e do alvo.
    """
    if frame.empty:
        raise ValueError("O dataset supervisionado não pode ser vazio.")

    if target_column not in frame.columns:
        raise KeyError(f"Coluna de alvo ausente na leitura: {target_column!r}")
    if partition_column not in frame.columns:
        raise KeyError(f"Coluna de partição ausente na leitura: {partition_column!r}")

    target_numeric = pd.to_numeric(frame[target_column], errors="coerce")
    n_nulos_alvo = int(target_numeric.isna().sum())
    if n_nulos_alvo:
        raise ValueError(
            f"Alvo {target_column!r} contém {n_nulos_alvo} valor(es) nulo(s); "
            "o dataset supervisionado deve ter alvo binário sem nulos."
        )
    target_values = set(target_numeric.astype(int).unique())
    if not target_values or not target_values.issubset({0, 1}):
        raise ValueError(
            f"Alvo deve ser binário 0/1. Observado: {sorted(target_values)}"
        )

    n_nulos_part = int(frame[partition_column].isna().sum())
    if n_nulos_part:
        raise ValueError(
            f"Partição {partition_column!r} contém {n_nulos_part} valor(es) nulo(s)."
        )

    observed = set(frame[partition_column].astype(str).unique())
    if observed != expected_partitions:
        raise ValueError(
            f"Partições esperadas {sorted(expected_partitions)}. "
            f"Observado: {sorted(observed)}"
        )


# ---------------------------------------------------------------------------
# Persistência
# ---------------------------------------------------------------------------

def _build_manifest(
    *,
    frame: pd.DataFrame,
    dataset_path: Path,
    source: Mapping[str, Any],
    feature_columns: Sequence[str],
    numeric_columns: list[str] | None,
    categorical_columns: list[str] | None,
    audit_columns: Sequence[str] | None,
    target_column: str,
    partition_column: str,
    cohort_kind: str,
    seed: int,
) -> dict[str, Any]:
    partition_counts = {
        str(k): int(v)
        for k, v in sorted(
            frame[partition_column].value_counts(dropna=False).items()
        )
    }
    schema = (
        "blocos"
        if (set(partition_counts) & set(BLOCOS_MESTRE))
        else "legado"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cohort_kind": str(cohort_kind),
        "source": dict(source),
        "dataset_path": str(dataset_path),
        "dataset_sha256": sha256_file(dataset_path),
        "rows": int(len(frame)),
        "columns": int(frame.shape[1]),
        "feature_columns": list(feature_columns),
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "audit_columns": list(audit_columns) if audit_columns else [],
        "target_column": target_column,
        "partition_column": partition_column,
        "partition_schema": schema,
        "partition_counts": partition_counts,
        "seed": int(seed),
        "test_opened": False,
    }


def persist_supervised_artifact(
    frame: pd.DataFrame,
    *,
    root: Path,
    source: Mapping[str, Any],
    feature_columns: Sequence[str],
    target_column: str,
    partition_column: str,
    cohort_kind: str,
    seed: int,
    numeric_columns: Sequence[str] | None = None,
    categorical_columns: Sequence[str] | None = None,
    audit_columns: Sequence[str] | None = None,
    overwrite: bool = False,
) -> tuple[Path, Path]:
    """Grava dataset e manifesto, exigindo um dos esquemas completos."""
    num, cat = _resolver_grupos(feature_columns, numeric_columns, categorical_columns)

    validate_supervised_frame(
        frame,
        feature_columns=feature_columns,
        target_column=target_column,
        partition_column=partition_column,
        audit_columns=audit_columns,
    )

    dataset_path, manifest_path = _paths(root)
    dataset_path.parent.mkdir(parents=True, exist_ok=True)

    if not overwrite and (dataset_path.exists() or manifest_path.exists()):
        raise FileExistsError(
            "Artefato supervisionado já existe. Use overwrite=True somente em "
            "uma reconstrução deliberada da mesma etapa."
        )

    frame.to_parquet(dataset_path, index=False)

    manifest = _build_manifest(
        frame=frame,
        dataset_path=dataset_path,
        source=source,
        feature_columns=feature_columns,
        numeric_columns=num,
        categorical_columns=cat,
        audit_columns=audit_columns,
        target_column=target_column,
        partition_column=partition_column,
        cohort_kind=cohort_kind,
        seed=seed,
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return dataset_path, manifest_path



def _configuracao_artefato() -> dict[str, Any]:
    """Resolve o contrato ativo do artefato a partir do supervised.yaml."""
    config = C.carregar_supervised()

    features_cfg = config.get("features") or {}
    feature_columns = list(
        features_cfg.get("final")
        or [
            *features_cfg.get("numericas", []),
            *features_cfg.get("categoricas", []),
        ]
    )
    numeric_columns = list(features_cfg.get("numericas") or [])
    categorical_columns = list(features_cfg.get("categoricas") or [])

    if not feature_columns:
        raise ValueError("Nenhuma feature definida em features.final.")

    target_cfg = config.get("target") or {}
    target_column = str(
        target_cfg.get("coluna_modelagem") or "alvo_obito_srag"
    )
    source_target_column = str(
        target_cfg.get("coluna") or target_column
    )

    temporal_cfg = config.get("temporal") or {}
    partition_column = str(
        temporal_cfg.get("coluna_particao") or "particao"
    )
    seed = int(temporal_cfg.get("seed", config.get("seed", 42)))

    return {
        "config": config,
        "features_cfg": features_cfg,
        "feature_columns": feature_columns,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "target_cfg": target_cfg,
        "target_column": target_column,
        "source_target_column": source_target_column,
        "temporal_cfg": temporal_cfg,
        "partition_column": partition_column,
        "seed": seed,
    }


def _colunas_auditoria_extras(
    artefato_cfg: Mapping[str, Any],
) -> list[str]:
    """Colunas físicas guardadas para auditoria e análises de sensibilidade.

    ``fator_risc`` (indicador agregado de fatores de risco),
    ``features.contexto_incremental`` e
    ``features.sensibilidade_gravidade_admissao``. Nenhuma delas entra em
    ``feature_columns``: ficam em ``audit_columns`` para as análises de
    sensibilidade previstas em ``sensibilidades`` no YAML.
    """
    features_cfg = artefato_cfg["features_cfg"]
    feature_columns = set(artefato_cfg["feature_columns"])
    candidatas = [
        "fator_risc",
        *(features_cfg.get("contexto_incremental") or []),
        *(features_cfg.get("sensibilidade_gravidade_admissao") or []),
    ]
    return [
        str(coluna)
        for coluna in dict.fromkeys(candidatas)
        if str(coluna) not in feature_columns
    ]


def _colunas_fisicas_necessarias(
    artefato_cfg: Mapping[str, Any],
) -> list[str]:
    """Lista colunas físicas necessárias antes da engenharia."""
    features_cfg = artefato_cfg["features_cfg"]
    engenharia_cfg = features_cfg.get("engenharia") or {}

    derivadas = set(engenharia_cfg.get("derivadas") or [])
    entradas = set(engenharia_cfg.get("entradas") or [])

    feature_columns = set(artefato_cfg["feature_columns"])
    features_fisicas = feature_columns - derivadas

    obrigatorias = {
        "id_registro",
        "nu_notific",
        "sg_uf",
        artefato_cfg["source_target_column"],
    }
    extras = set(_colunas_auditoria_extras(artefato_cfg))

    return sorted(features_fisicas | entradas | obrigatorias | extras)


def _construir_alvo(
    frame: pd.DataFrame,
    *,
    source_column: str,
    target_column: str,
    target_cfg: Mapping[str, Any],
) -> pd.DataFrame:
    """Constrói o alvo binário de acordo com a configuração ativa."""
    if target_column in frame.columns:
        target = pd.to_numeric(frame[target_column], errors="coerce")
    else:
        if source_column not in frame.columns:
            raise KeyError(
                "Não foi possível construir o alvo: "
                f"coluna fonte {source_column!r} ausente."
            )

        source = pd.to_numeric(frame[source_column], errors="coerce")
        positivos = {
            float(valor) for valor in target_cfg.get("positivos", [])
        }
        negativos = {
            float(valor) for valor in target_cfg.get("negativos", [])
        }

        if not positivos or not negativos:
            raise ValueError(
                "target.positivos e target.negativos devem estar preenchidos."
            )

        target = pd.Series(pd.NA, index=frame.index, dtype="Int8")
        target.loc[source.isin(positivos)] = 1
        target.loc[source.isin(negativos)] = 0

    out = frame.copy(deep=False)
    out[target_column] = pd.to_numeric(target, errors="coerce").astype("Int8")

    descartar_outros = bool(target_cfg.get("descartar_outros", True))
    if descartar_outros:
        out = out.loc[out[target_column].notna()].copy(deep=False)
    elif out[target_column].isna().any():
        raise ValueError(
            f"Alvo {target_column!r} contém valores não classificados."
        )

    return out


def _periodo_do_ano(
    anos: pd.Series,
    temporal_cfg: Mapping[str, Any],
) -> pd.Series:
    """Classifica anos em compartilhado, pandêmico ou exploração."""
    blocos = temporal_cfg.get("blocos") or {}

    anos_pandemia = {
        int(ano)
        for ano in (blocos.get("test_pandemic") or {}).get("anos", [])
    }
    anos_compartilhados = {
        int(ano)
        for nome, bloco in blocos.items()
        if nome != "test_pandemic"
        for ano in (bloco or {}).get("anos", [])
    }

    ano_numeric = pd.to_numeric(anos, errors="coerce")
    periodo = pd.Series("exploracao", index=anos.index, dtype="string")
    periodo.loc[ano_numeric.isin(anos_compartilhados)] = "compartilhado"
    periodo.loc[ano_numeric.isin(anos_pandemia)] = "pandemico"
    periodo.loc[ano_numeric.isna()] = "ano_ausente"
    return periodo


def _separar_grupos_temporais_incompativeis(
    frame: pd.DataFrame,
    *,
    temporal_cfg: Mapping[str, Any],
    group_column: str,
    year_column: str,
    target_column: str,
    region_column: str | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa grupos que não podem receber uma única partição-mestre.

    Um grupo é incompatível quando suas linhas pertencem a categorias
    temporais diferentes ou, dentro dos anos compartilhados, formam mais
    de um estrato de ano, alvo e região. A separação ocorre antes da
    partição para impedir que registros do mesmo grupo sejam distribuídos
    entre blocos diferentes.
    """
    required = {group_column, year_column, target_column}
    if region_column:
        required.add(region_column)

    missing = sorted(required - set(frame.columns))
    if missing:
        raise KeyError(
            "Colunas ausentes para auditar grupos temporais: "
            f"{missing}"
        )

    periodo = _periodo_do_ano(frame[year_column], temporal_cfg)

    estrato = pd.DataFrame(
        {
            "periodo": periodo,
            "ano": pd.to_numeric(
                frame[year_column],
                errors="coerce",
            ).astype("Int64"),
            "alvo": pd.to_numeric(
                frame[target_column],
                errors="coerce",
            ).astype("Int8"),
        },
        index=frame.index,
    )

    if region_column:
        estrato["regiao"] = (
            frame[region_column]
            .astype("string")
            .fillna("AUSENTE")
        )

    assinatura = estrato.astype("string").agg("|".join, axis=1)
    n_estratos = assinatura.groupby(
        frame[group_column],
        observed=True,
    ).nunique()

    grupos_incompativeis = n_estratos[n_estratos > 1].index
    mascara = frame[group_column].isin(grupos_incompativeis)

    quarentena = frame.loc[mascara].copy()
    modelavel = frame.loc[~mascara].copy()

    return modelavel, quarentena


def _escrever_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def gerar_artefato_supervisionado(
    root: Path,
    *,
    cohort_kind: str = "final",
    exportar_particao: bool = True,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Gera e persiste o artefato supervisionado canônico.

    A função aceita exclusivamente a coorte final, aplica a engenharia
    central, cria identificadores estáveis, separa grupos temporalmente
    incompatíveis, materializa a partição-mestre e persiste dataset e
    manifestos sem expor os blocos de teste para modelagem.
    """
    root = Path(root).resolve()

    kind_normalizado = str(cohort_kind).strip().lower()
    if kind_normalizado != "final":
        raise ValueError(
            "A geração definitiva exige cohort_kind='final'. "
            f"Recebido: {cohort_kind!r}."
        )

    artefato_cfg = _configuracao_artefato()
    temporal_cfg = artefato_cfg["temporal_cfg"]
    target_column = artefato_cfg["target_column"]
    source_target_column = artefato_cfg["source_target_column"]
    partition_column = artefato_cfg["partition_column"]
    seed = artefato_cfg["seed"]

    colunas_fisicas = _colunas_fisicas_necessarias(artefato_cfg)
    frame, source = load_cohort(
        root,
        kind="final",
        columns=colunas_fisicas,
    )

    if source.kind != "final":
        raise RuntimeError(
            f"Fonte resolvida como {source.kind!r}; esperado 'final'."
        )

    frame = montar_features(frame)

    if "sg_uf" not in frame.columns:
        raise KeyError("Coluna obrigatória ausente: 'sg_uf'.")

    frame["regiao_residencia"] = regiao_residencia(frame["sg_uf"])
    frame["group_id"] = criar_group_id(frame)

    frame = _construir_alvo(
        frame,
        source_column=source_target_column,
        target_column=target_column,
        target_cfg=artefato_cfg["target_cfg"],
    )

    if "ano_internacao" not in frame.columns:
        raise KeyError(
            "montar_features não produziu a coluna 'ano_internacao'."
        )

    frame_modelavel, quarentena = _separar_grupos_temporais_incompativeis(
        frame,
        temporal_cfg=temporal_cfg,
        group_column="group_id",
        year_column="ano_internacao",
        target_column=target_column,
        region_column="regiao_residencia",
    )

    particionado, manifesto_particao = criar_particao_mestra(
        frame_modelavel,
        temporal_cfg=dict(temporal_cfg),
        group_column="group_id",
        year_column="ano_internacao",
        target_column=target_column,
        region_column="regiao_residencia",
        partition_column=partition_column,
    )

    modelavel = particionado.loc[
        particionado[partition_column].astype(str) != "exploracao"
    ].copy()

    feature_columns = list(artefato_cfg["feature_columns"])
    numeric_columns = list(artefato_cfg["numeric_columns"])
    categorical_columns = list(artefato_cfg["categorical_columns"])

    audit_candidates = [
        "id_registro",
        "nu_notific",
        "group_id",
        "ano_internacao",
        "sg_uf",
        "regiao_residencia",
        "faixa_etaria",
        "sexo_categoria",
        *_colunas_auditoria_extras(artefato_cfg),
    ]
    audit_columns = [
        coluna
        for coluna in dict.fromkeys(audit_candidates)
        if coluna in modelavel.columns
        and coluna not in feature_columns
        and coluna not in {target_column, partition_column}
    ]

    output_columns = list(
        dict.fromkeys(
            [
                *feature_columns,
                *audit_columns,
                target_column,
                partition_column,
            ]
        )
    )
    dataset_frame = modelavel[output_columns].copy()

    analytical_dir = root / "data" / "analytical"
    partition_path = analytical_dir / "partitions_master.parquet"
    partition_manifest_path = analytical_dir / "manifesto_particao.json"

    # Confere a sobrescrita antes de gravar qualquer arquivo, para não
    # deixar dataset novo ao lado de partição-mestre antiga.
    if exportar_particao and not overwrite and (
        partition_path.exists() or partition_manifest_path.exists()
    ):
        raise FileExistsError(
            "Partição-mestre já existe. Use overwrite=True somente "
            "em reconstrução deliberada."
        )

    dataset_path, manifest_path = persist_supervised_artifact(
        dataset_frame,
        root=root,
        source=source.to_dict(),
        feature_columns=feature_columns,
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
        audit_columns=audit_columns,
        target_column=target_column,
        partition_column=partition_column,
        cohort_kind="final",
        seed=seed,
        overwrite=overwrite,
    )

    del dataset_frame
    gc.collect()

    if exportar_particao:
        partition_columns = [
            coluna
            for coluna in [
                "id_registro",
                "group_id",
                "ano_internacao",
                "regiao_residencia",
                target_column,
                partition_column,
            ]
            if coluna in particionado.columns
        ]
                # Preserva o nome explícito do bloco mestre e mantém a coluna de
        # partição configurada para compatibilidade com os consumidores.
        particao_mestre = particionado[partition_columns].copy()
        particao_mestre["bloco_mestre"] = (
            particao_mestre[partition_column].astype("string")
        )
        particao_mestre.to_parquet(
            partition_path,
            index=False,
        )
        del particao_mestre
        gc.collect()

        manifesto_particao = {
            **manifesto_particao,
            "source": source.to_dict(),
            "rows_before_quarantine": int(len(frame)),
            "rows_quarantined": int(len(quarentena)),
            "groups_quarantined": int(
                quarentena["group_id"].nunique()
            ) if not quarentena.empty else 0,
            "rows_partitioned": int(len(particionado)),
            "rows_modelable": int(len(modelavel)),
            "partition_path": str(partition_path),
            "partition_sha256": sha256_file(partition_path),
            "configuration_sha256": C.supervised_yaml_sha256(),
            }
        _escrever_json(partition_manifest_path, manifesto_particao)

    alvo_modelavel = pd.to_numeric(
        modelavel[target_column], errors="coerce"
    )
    blocos_modelaveis = modelavel[partition_column].astype(str)
    partition_counts = {
        str(nome): int(quantidade)
        for nome, quantidade in blocos_modelaveis.value_counts().sort_index().items()
    }
    prevalence_by_partition = {
        str(nome): float(valor)
        for nome, valor in alvo_modelavel.groupby(blocos_modelaveis).mean().sort_index().items()
    }
    rows_loaded = int(len(frame))
    rows_quarantined = int(len(quarentena))
    groups_quarantined = (
        int(quarentena["group_id"].nunique()) if not quarentena.empty else 0
    )
    rows_exploracao = int(len(particionado) - len(modelavel))
    rows_modelable = int(len(modelavel))

    del frame, frame_modelavel, quarentena, particionado, modelavel
    del alvo_modelavel, blocos_modelaveis
    gc.collect()

    return {
        "dataset_path": str(dataset_path),
        "manifest_path": str(manifest_path),
        "partition_path": (
            str(partition_path) if exportar_particao else None
        ),
        "partition_manifest_path": (
            str(partition_manifest_path) if exportar_particao else None
        ),
        "cohort_kind": source.kind,
        "source_path": source.path,
        "source_sha256": source.sha256,
        "dataset_sha256": sha256_file(dataset_path),
        "rows_loaded": rows_loaded,
        "rows_quarantined": rows_quarantined,
        "groups_quarantined": groups_quarantined,
        "rows_exploracao": rows_exploracao,
        "rows_modelable": rows_modelable,
        "partition_counts": partition_counts,
        "prevalence_by_partition": prevalence_by_partition,
        "audit_columns": list(audit_columns),
        "estratificacao": manifesto_particao.get("estratificacao"),
        "test_opened": False,
    }


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------

def _selecionar_particoes_padrao(manifest: Mapping[str, Any]) -> tuple[str, ...]:
    """Default depende do esquema do artefato."""
    if _esquema_do_manifest(manifest) == "blocos":
        return BLOCKS_PADRAO_LEITURA
    return (_PARTITION_TREINO, _PARTITION_VALIDACAO)


def _validar_particoes_solicitadas(
    selected: Sequence[str],
    manifest: Mapping[str, Any],
) -> None:
    if not selected:
        raise ValueError("``partitions`` não pode ser vazio.")

    if unknown := set(selected) - ALLOWED_PARTITIONS:
        raise ValueError(
            f"Partições desconhecidas: {sorted(unknown)}. "
            f"Use subconjunto de {sorted(ALLOWED_PARTITIONS)}."
        )

    disponiveis = {str(k) for k in (manifest.get("partition_counts") or {})}
    if ausentes := set(selected) - disponiveis:
        raise ValueError(
            f"Partições solicitadas que não existem no artefato: {sorted(ausentes)}. "
            f"Disponíveis: {sorted(disponiveis)}."
        )


def _exigir_gates_para(selected: Sequence[str]) -> None:
    if set(selected) & _PARTICOES_DE_TESTE:
        exigir_gate("G9_holdout")
    if _BLOCK_EXPLORACAO in selected:
        _exigir_exploracao_ativa()


def load_supervised_artifact(
    root: Path,
    *,
    expected_kind: str | None = None,
    columns: Sequence[str] | None = None,
    partitions: Sequence[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Carrega o artefato canônico e valida hash, tipo de coorte e schema.

    ``partitions`` restringe o subconjunto carregado (pushdown no Parquet).
    Default: ``BLOCKS_PADRAO_LEITURA`` quando o artefato é de blocos, senão
    ``("treino", "validacao")``.

    Qualquer partição de teste (``teste``, ``test_ref`` ou ``test_pandemic``)
    exige ``G9_holdout`` aprovado. ``exploracao`` exige
    ``temporal.exploracao_2026.ativa``.

    ``columns`` restringe as colunas devolvidas; alvo e partição são
    **sempre lidos internamente** para validar e descartados no retorno
    caso o chamador não os tenha pedido.
    """
    dataset_path, manifest_path = _paths(root)

    if not dataset_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError(
            f"Execute o Notebook 03 adaptado para gerar "
            f"{DATASET_NAME} e {MANIFEST_NAME}."
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if expected_kind and _normalizar_kind(manifest.get("cohort_kind")) != _normalizar_kind(expected_kind):
        raise RuntimeError(
            f"Artefato de coorte {manifest.get('cohort_kind')!r}, mas "
            f"SRAG_COHORT_KIND={expected_kind!r}. Reconstrua no Notebook 03."
        )

    if sha256_file(dataset_path) != manifest.get("dataset_sha256"):
        raise RuntimeError("Hash do dataset supervisionado difere do manifesto.")

    selected = (
        tuple(partitions) if partitions is not None
        else _selecionar_particoes_padrao(manifest)
    )
    _validar_particoes_solicitadas(selected, manifest)
    _exigir_gates_para(selected)

    target_column = manifest["target_column"]
    partition_column = manifest["partition_column"]
    filters = [(partition_column, "in", list(selected))]

    if columns is None:
        frame = pd.read_parquet(dataset_path, filters=filters)
        validate_supervised_frame(
            frame,
            feature_columns=manifest["feature_columns"],
            target_column=target_column,
            partition_column=partition_column,
            audit_columns=manifest.get("audit_columns") or None,
            required_partitions=selected,
        )
    else:
        requested = list(columns)
        read_cols = list(dict.fromkeys([*requested, target_column, partition_column]))
        frame = pd.read_parquet(dataset_path, columns=read_cols, filters=filters)
        _validate_partial_load(
            frame,
            target_column=target_column,
            partition_column=partition_column,
            expected_partitions=set(selected),
        )
        frame = frame[requested]

    manifest["dataset_path"] = str(dataset_path)
    return frame, manifest


# ---------------------------------------------------------------------------
# Visões agregadas (compatíveis com notebooks C_11..C_15)
# ---------------------------------------------------------------------------

def split_partitions(
    frame: pd.DataFrame,
    manifest: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devolve ``(treino, validacao)`` agregando os blocos correspondentes.

    - legado: ``treino``, ``validacao``;
    - blocos: ``train_ref`` → treino; ``val_tune + val_cal + val_meas`` → validação.

    O bloco de teste nunca é exposto aqui — use ``holdout_partition`` após
    ``G9_holdout``.
    """
    col = manifest["partition_column"]
    papeis = _particoes_por_papel(manifest)

    treino = _filtrar_particoes(frame, col, papeis["treino"])
    validacao = _filtrar_particoes(frame, col, papeis["validacao"])

    if treino.empty:
        raise ValueError(
            f"Partição 'treino' vazia (blocos esperados: {papeis['treino']})."
        )
    if validacao.empty:
        raise ValueError(
            f"Partição 'validacao' vazia (blocos esperados: {papeis['validacao']})."
        )

    return treino, validacao


def holdout_partition(
    frame: pd.DataFrame,
    manifest: Mapping[str, Any],
) -> pd.DataFrame:
    """Devolve o bloco de teste. Exige ``G9_holdout`` aprovado."""
    exigir_gate("G9_holdout")

    col = manifest["partition_column"]
    papeis = _particoes_por_papel(manifest)
    teste = _filtrar_particoes(frame, col, papeis["teste"])

    if teste.empty:
        raise ValueError(
            "Bloco de teste ausente no DataFrame. Carregue o artefato "
            "incluindo test_ref/test_pandemic (ou 'teste' no legado)."
        )
    return teste