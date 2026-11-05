"""Leitura dos dados, coorte, partição e artefato supervisionado."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import hashlib
import time
from typing import Iterable, Mapping, Sequence, Any, Literal, get_args, cast
import requests
from dataclasses import dataclass, asdict
import yaml
import os
import json
import platform
import sys
from datetime import datetime, timezone
import pyarrow.compute as pc
import gc

from src import config as C
from src.config import PROCESSED, get_secret, sha256_file, GatePendenteError, exigir_gate
from src.features import montar_features, regiao_residencia


def metadados_parquet(caminho):
    arq=pq.ParquetFile(caminho); meta=arq.metadata
    return {"caminho":str(caminho),"linhas":int(meta.num_rows),"colunas":int(meta.num_columns),
            "row_groups":int(meta.num_row_groups),"nomes_colunas":list(arq.schema_arrow.names),
            "tamanho_mb":Path(caminho).stat().st_size/1_048_576}

def amostra_parquet(caminho,n=5,columns=None):
    arq=pq.ParquetFile(caminho)
    lote=next(arq.iter_batches(batch_size=n,columns=list(columns) if columns else None),None)
    return pd.DataFrame(columns=columns or arq.schema_arrow.names) if lote is None else lote.to_pandas()

def compactar_dataframe(df, limite_categoria=1000, colunas_texto_livre=()):
    livres=set(colunas_texto_livre)
    for col in list(df.columns):
        s=df[col]
        if col in livres:
            df[col]=s.astype("string[pyarrow]"); continue
        if isinstance(s.dtype,pd.CategoricalDtype): continue
        if pd.api.types.is_datetime64_any_dtype(s.dtype):
            df[col]=pd.to_datetime(s,errors="coerce").astype("datetime64[ns]"); continue
        if pd.api.types.is_object_dtype(s.dtype) or pd.api.types.is_string_dtype(s.dtype):
            df[col]=s.astype("category") if s.nunique(dropna=True)<=limite_categoria else s.astype("string[pyarrow]")
        elif pd.api.types.is_float_dtype(s.dtype): df[col]=s.astype("float32")
        elif pd.api.types.is_integer_dtype(s.dtype) and not pd.api.types.is_extension_array_dtype(s.dtype):
            df[col]=pd.to_numeric(s,downcast="integer")
    return df

def ler_parquet_enxuto(caminho,columns=None,filters=None,colunas_texto_livre=(),colunas_por_lote=12):
    nomes=list(columns) if columns else pq.read_schema(caminho).names
    tamanho=max(1,int(colunas_por_lote))
    partes=[]
    for inicio in range(0,len(nomes),tamanho):
        lote=nomes[inicio:inicio+tamanho]
        tabela=pq.read_table(caminho,columns=lote,filters=filters)
        parte=tabela.to_pandas(strings_to_categorical=True,self_destruct=True,split_blocks=True)
        del tabela
        partes.append(compactar_dataframe(parte,colunas_texto_livre=colunas_texto_livre))
    if not partes:
        return pd.DataFrame()
    if len(partes)==1:
        return partes[0]
    return pd.concat(partes,axis=1)


PARQUET_MAGIC: bytes = b"PAR1"
_CHUNK: int = 8 * 1024 * 1024


def _token() -> str | None:
    """``GITHUB_TOKEN`` se definido; caso contrário, ``None``."""
    return get_secret("GITHUB_TOKEN", obrigatorio=False)


def sha256_path(parquet_path: Path) -> Path:
    """Caminho do sidecar ``.sha256`` associado a um Parquet."""
    return parquet_path.with_suffix(parquet_path.suffix + ".sha256")


def read_sha256(parquet_path: Path) -> str | None:
    """Lê o SHA-256 do sidecar, ou ``None`` se ele não existir."""
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
    """Abre um stream HTTP com retry linear."""
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

    if last_exc is None:
        raise RuntimeError(f"Nenhuma tentativa executada para {url}")
    raise last_exc


def _baixar_para_part(
    r: requests.Response,
    tmp: Path,
) -> tuple[str, bytes]:
    """Streama ``r`` para ``tmp``; devolve ``(sha256_hex, primeiros_16_bytes)``."""
    h = hashlib.sha256()
    first = b""
    total = int(r.headers.get("content-length", 0))
    done = 0

    with open(tmp, "wb") as f:
        for chunk in r.iter_content(_CHUNK):
            if not chunk:
                continue
            if not first:
                first = chunk[:16]
            f.write(chunk)
            h.update(chunk)
            done += len(chunk)
            if total:
                print(
                    f"\rBaixando: {done / 1e6:.0f}/{total / 1e6:.0f} MB",
                    end="",
                    flush=True,
                )

    if total:
        print()
    return h.hexdigest(), first


def download_file(
    url: str,
    dest: Path,
    *,
    headers: dict[str, str] | None = None,
    expected_magic: bytes | None = None,
    expected_sha256: str | None = None,
) -> str:
    """Baixa ``url`` para ``dest`` com verificação de magic bytes e SHA-256."""
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.unlink(missing_ok=True)

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
        digest, first_bytes = _baixar_para_part(r, tmp)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    finally:
        r.close()

    if expected_magic and not first_bytes.startswith(expected_magic):
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"Arquivo baixado não é válido. Esperado começar com "
            f"{expected_magic!r}, recebido {first_bytes!r}. URL: {url}"
        )

    if expected_sha256 and digest.lower() != expected_sha256.lower():
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"SHA-256 divergente para {url}.\n"
            f"  esperado: {expected_sha256}\n"
            f"  obtido:   {digest}"
        )

    tmp.replace(dest)
    sha256_path(dest).write_text(f"{digest}  {dest.name}\n", encoding="utf-8")
    return digest


def _private_asset_url(token: str) -> str:
    """URL do asset Parquet via API do GitHub (repositório privado)."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    url = (
        f"https://api.github.com/repos/{C.GITHUB_REPO}/releases/tags/"
        f"{C.DATA_VERSION}"
    )
    r = requests.get(url, headers=headers, timeout=C.HTTP_TIMEOUT)
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
    """Devolve o caminho local do Parquet de SRAG, baixando se necessário."""
    folder = PROCESSED / C.DATA_VERSION
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / C.PARQUET_NAME

    if path.exists() and not force:
        return path

    if force and path.exists():
        path.unlink()
        sha256_path(path).unlink(missing_ok=True)

    public_url = C.srag_parquet_url()

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
        digest = download_file(
            _private_asset_url(token),
            path,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/octet-stream",
            },
            expected_magic=PARQUET_MAGIC,
            expected_sha256=expected_sha256,
        )

    print(f"[storage] SHA-256: {digest}")
    return path


def read_srag(
    columns: Iterable[str] | None = None,
    filters: list[tuple] | None = None,
    *,
    compactar: bool = False,
    colunas_texto_livre: Iterable[str] = (),
) -> pd.DataFrame:
    """Lê o Parquet de SRAG como DataFrame."""
    caminho = get_parquet()
    columns_list = list(columns) if columns is not None else None

    if compactar:
        return ler_parquet_enxuto(
            caminho,
            columns=columns_list,
            filters=filters,
            colunas_texto_livre=tuple(colunas_texto_livre),
        )

    return pd.read_parquet(caminho, columns=columns_list, filters=filters)


DEFAULT_RULE_ORDER: tuple[str, ...] = (
    "hospital_nao_confirmado",
    "dt_interna_invalida",
    "evolucao_fora_alvo_principal",
    "dt_interna_antes_periodo",
    "dt_interna_apos_periodo",
    "intervalo_sintomas_negativo",
    "intervalo_sintomas_maior_limite",
)

REQUIRED_COLUMNS: frozenset[str] = frozenset(
    {
        "hospital",
        "dt_interna",
        "dt_sin_pri",
        "evolucao",
    }
)


@dataclass(frozen=True)
class CohortAuditParameters:
    """Parâmetros necessários para avaliar as regras populacionais."""

    period_start: pd.Timestamp
    period_end: pd.Timestamp
    max_symptom_to_admission_days: int

    def __post_init__(self) -> None:
        period_start = pd.Timestamp(self.period_start)
        period_end = pd.Timestamp(self.period_end)

        if pd.isna(period_start):
            raise ValueError("period_start precisa ser uma data valida.")

        if pd.isna(period_end):
            raise ValueError("period_end precisa ser uma data valida.")

        if period_start > period_end:
            raise ValueError(
                "period_start nao pode ser posterior a period_end."
            )

        if self.max_symptom_to_admission_days < 0:
            raise ValueError(
                "max_symptom_to_admission_days nao pode ser negativo."
            )

        object.__setattr__(self, "period_start", period_start)
        object.__setattr__(self, "period_end", period_end)


@dataclass(frozen=True)
class CohortAuditEvaluation:
    """Resultado imutavel da avaliacao das regras."""

    masks: Mapping[str, pd.Series]
    normalized: pd.DataFrame

    @property
    def row_count(self) -> int:
        return int(len(self.normalized))

    @property
    def rule_ids(self) -> tuple[str, ...]:
        return tuple(self.masks.keys())


def validate_audit_schema(frame: pd.DataFrame) -> None:
    """Valida se as colunas mínimas para auditoria estão disponíveis."""

    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame precisa ser um pandas.DataFrame.")

    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))

    if missing:
        raise ValueError(
            "Colunas obrigatorias ausentes para auditoria: "
            + ", ".join(missing)
        )


def normalize_srag_code(series: pd.Series) -> pd.Series:
    """Normaliza códigos sem fundir ausente, não, ignorado ou não se aplica."""

    normalized = series.astype("string").str.strip()
    normalized = normalized.str.replace(r"\.0$", "", regex=True)

    lowered = normalized.str.lower()
    null_like = lowered.isin(
        {
            "",
            "nan",
            "none",
            "null",
            "<na>",
            "nat",
        }
    )

    return normalized.mask(null_like, pd.NA)


def parse_srag_date(series: pd.Series) -> pd.Series:
    """Converte datas SRAG no formato ISO e preserva inválidos como NaT."""

    if pd.api.types.is_datetime64_any_dtype(series.dtype):
        return pd.to_datetime(
            series,
            errors="coerce",
        )

    normalized = (
        series.astype("string")
        .str.strip()
        .replace(
            {
                "": pd.NA,
                "nan": pd.NA,
                "NaN": pd.NA,
                "None": pd.NA,
                "<NA>": pd.NA,
            }
        )
    )

    return pd.to_datetime(
        normalized,
        format="%Y-%m-%d",
        errors="coerce",
    )


def evaluate_audit_rules(
    frame: pd.DataFrame,
    parameters: CohortAuditParameters,
) -> CohortAuditEvaluation:
    """Avalia todas as regras sem remover registros."""

    validate_audit_schema(frame)

    hospital = normalize_srag_code(frame["hospital"])
    evolucao = normalize_srag_code(frame["evolucao"])
    dt_interna = parse_srag_date(frame["dt_interna"])
    dt_sin_pri = parse_srag_date(frame["dt_sin_pri"])

    intervalo_dias = (dt_interna - dt_sin_pri).dt.total_seconds() / 86_400.0

    masks: dict[str, pd.Series] = {
        "hospital_nao_confirmado": hospital.isna() | hospital.ne("1"),
        "dt_interna_invalida": dt_interna.isna(),
        "evolucao_fora_alvo_principal": ~evolucao.isin(["1", "2"]),
        "dt_interna_antes_periodo": (
            dt_interna.notna()
            & dt_interna.lt(parameters.period_start)
        ),
        "dt_interna_apos_periodo": (
            dt_interna.notna()
            & dt_interna.gt(parameters.period_end)
        ),
        "intervalo_sintomas_negativo": (
            dt_interna.notna()
            & dt_sin_pri.notna()
            & intervalo_dias.lt(0)
        ),
        "intervalo_sintomas_maior_limite": (
            dt_interna.notna()
            & dt_sin_pri.notna()
            & intervalo_dias.gt(
                parameters.max_symptom_to_admission_days
            )
        ),
    }

    normalized = pd.DataFrame(
        {
            "hospital_normalizado": hospital,
            "evolucao_normalizada": evolucao,
            "dt_interna_parseada": dt_interna,
            "dt_sin_pri_parseada": dt_sin_pri,
            "intervalo_sintomas_internacao_dias": intervalo_dias,
        },
        index=frame.index,
    )

    return CohortAuditEvaluation(
        masks=masks,
        normalized=normalized,
    )


def summarize_audit_rules(
    evaluation: CohortAuditEvaluation,
) -> pd.DataFrame:
    """Resume cada regra sem assumir que os conjuntos são disjuntos."""

    rows: list[dict[str, object]] = []

    for rule_id, mask in evaluation.masks.items():
        flagged = int(mask.sum())

        rows.append(
            {
                "regra": rule_id,
                "linhas_sinalizadas": flagged,
                "total_linhas": evaluation.row_count,
                "proporcao_fonte": (
                    flagged / evaluation.row_count
                    if evaluation.row_count > 0
                    else 0.0
                ),
            }
        )

    return pd.DataFrame(rows)


def build_rule_overlap(
    evaluation: CohortAuditEvaluation,
    rule_order: Sequence[str] = DEFAULT_RULE_ORDER,
) -> pd.DataFrame:
    """Cria uma matriz simétrica de sobreposição entre regras."""

    validated_order = _validate_rule_order(
        evaluation=evaluation,
        rule_order=rule_order,
    )

    overlap = pd.DataFrame(
        0,
        index=validated_order,
        columns=validated_order,
        dtype="int64",
    )
    overlap.index.name = "regra"

    for left_rule in validated_order:
        for right_rule in validated_order:
            overlap.loc[left_rule, right_rule] = int(
                (
                    evaluation.masks[left_rule]
                    & evaluation.masks[right_rule]
                ).sum()
            )

    return overlap


def build_simulated_waterfall(
    evaluation: CohortAuditEvaluation,
    rule_order: Sequence[str] = DEFAULT_RULE_ORDER,
) -> pd.DataFrame:
    """Simula exclusões sequenciais sem modificar ou devolver uma coorte."""

    validated_order = _validate_rule_order(
        evaluation=evaluation,
        rule_order=rule_order,
    )

    active = pd.Series(
        True,
        index=evaluation.normalized.index,
        dtype=bool,
    )
    rows: list[dict[str, object]] = []

    for order, rule_id in enumerate(validated_order, start=1):
        mask = evaluation.masks[rule_id]
        excluded_now = active & mask
        excluded_count = int(excluded_now.sum())

        active = active & ~mask
        remaining_count = int(active.sum())

        rows.append(
            {
                "ordem": order,
                "regra": rule_id,
                "excluidas_na_etapa": excluded_count,
                "restantes_apos_etapa": remaining_count,
            }
        )

    return pd.DataFrame(rows)


def build_approved_exclusion_mask(
    evaluation: CohortAuditEvaluation,
    approved_rule_ids: Sequence[str],
) -> pd.Series:
    """Combina somente regras explicitamente aprovadas."""

    approved = tuple(approved_rule_ids)

    unknown = sorted(set(approved).difference(evaluation.masks))

    if unknown:
        raise ValueError(
            "Regras aprovadas desconhecidas: " + ", ".join(unknown)
        )

    if len(approved) != len(set(approved)):
        raise ValueError(
            "approved_rule_ids nao pode conter regras duplicadas."
        )

    combined = pd.Series(
        False,
        index=evaluation.normalized.index,
        dtype=bool,
    )

    for rule_id in approved:
        combined = combined | evaluation.masks[rule_id]

    return combined


def _validate_rule_order(
    evaluation: CohortAuditEvaluation,
    rule_order: Sequence[str],
) -> tuple[str, ...]:
    """Valida uma ordem de regras antes de produzir relatórios."""

    normalized_order = tuple(rule_order)

    if not normalized_order:
        raise ValueError("rule_order nao pode ser vazio.")

    if len(normalized_order) != len(set(normalized_order)):
        raise ValueError("rule_order nao pode conter regras duplicadas.")

    unknown = sorted(set(normalized_order).difference(evaluation.masks))

    if unknown:
        raise ValueError(
            "rule_order contem regras desconhecidas: "
            + ", ".join(unknown)
        )

    return normalized_order


VALID_CONTRACT_STATUSES: frozenset[str] = frozenset(
    {
        "candidate",
        "approved",
        "retired",
    }
)

VALID_RULE_ACTIONS: frozenset[str] = frozenset(
    {
        "audit_only",
        "approved_exclusion",
        "quarantine",
    }
)


@dataclass(frozen=True)
class CohortRuleContract:
    """Decisão declarada para uma regra de auditoria."""

    rule_id: str
    action: str
    rationale: str
    decision_id: str | None

    @property
    def removes_rows(self) -> bool:
        return self.action in {
            "approved_exclusion",
            "quarantine",
        }


@dataclass(frozen=True)
class CohortContract:
    """Contrato populacional validado da coorte."""

    contract_id: str
    version: int
    status: str
    description: str
    source_path: Path
    source_manifest_path: Path
    audit_parameters: CohortAuditParameters
    rule_order: tuple[str, ...]
    rules: Mapping[str, CohortRuleContract]
    required_columns: tuple[str, ...]
    target_source_column: str
    target_output_column: str
    target_mapping: Mapping[str, int]
    target_excluded_codes: tuple[str, ...]
    target_exclude_missing: bool
    outputs: Mapping[str, Path]

    @property
    def approved_exclusion_rule_ids(self) -> tuple[str, ...]:
        return tuple(
            rule_id
            for rule_id in self.rule_order
            if self.rules[rule_id].action == "approved_exclusion"
        )

    @property
    def quarantine_rule_ids(self) -> tuple[str, ...]:
        return tuple(
            rule_id
            for rule_id in self.rule_order
            if self.rules[rule_id].action == "quarantine"
        )

    @property
    def audit_only_rule_ids(self) -> tuple[str, ...]:
        return tuple(
            rule_id
            for rule_id in self.rule_order
            if self.rules[rule_id].action == "audit_only"
        )


def load_cohort_contract(path: Path) -> CohortContract:
    """Carrega e valida integralmente um contrato YAML."""

    contract_path = Path(path)

    if not contract_path.is_file():
        raise FileNotFoundError(
            f"Contrato de coorte nao encontrado: {contract_path}"
        )

    with contract_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if not isinstance(raw, dict):
        raise ValueError(
            "O contrato precisa ter um objeto YAML no nivel raiz."
        )

    return parse_cohort_contract(raw)


def parse_cohort_contract(raw: Mapping[str, Any]) -> CohortContract:
    """Valida um contrato já carregado e cria sua representação imutável."""

    contract_section = _require_mapping(raw, "contract")
    source_section = _require_mapping(raw, "source")
    period_section = _require_mapping(raw, "period")
    target_section = _require_mapping(raw, "target")
    audit_section = _require_mapping(raw, "audit")
    outputs_section = _require_mapping(raw, "outputs")

    contract_id = _require_nonempty_string(contract_section, "id")
    version = _require_positive_integer(contract_section, "version")
    status = _require_nonempty_string(contract_section, "status")
    description = _require_nonempty_string(
        contract_section,
        "description",
    )

    if status not in VALID_CONTRACT_STATUSES:
        raise ValueError(
            f"Status de contrato invalido: {status!r}. "
            f"Permitidos: {sorted(VALID_CONTRACT_STATUSES)}"
        )

    source_path = Path(
        _require_nonempty_string(source_section, "path")
    )
    source_manifest_path = Path(
        _require_nonempty_string(source_section, "manifest_path")
    )

    period_start = _parse_contract_date(
        period_section,
        "start",
    )
    period_end = _parse_contract_date(
        period_section,
        "end",
    )

    max_interval = _require_nonnegative_integer(
        audit_section,
        "max_symptom_to_admission_days",
    )

    audit_parameters = CohortAuditParameters(
        period_start=period_start,
        period_end=period_end,
        max_symptom_to_admission_days=max_interval,
    )

    rule_order = _require_unique_string_sequence(
        audit_section,
        "rule_order",
    )

    rules_raw = _require_mapping(audit_section, "rules")
    rules = _parse_rules(rules_raw)

    expected_rules = set(DEFAULT_RULE_ORDER)
    ordered_rules = set(rule_order)
    declared_rules = set(rules)

    if ordered_rules != expected_rules:
        missing = sorted(expected_rules - ordered_rules)
        extra = sorted(ordered_rules - expected_rules)
        raise ValueError(
            "rule_order diverge das regras implementadas. "
            f"Ausentes: {missing}. Extras: {extra}."
        )

    if declared_rules != ordered_rules:
        missing = sorted(ordered_rules - declared_rules)
        extra = sorted(declared_rules - ordered_rules)
        raise ValueError(
            "A secao audit.rules diverge de rule_order. "
            f"Ausentes: {missing}. Extras: {extra}."
        )

    required_columns = _require_unique_string_sequence(
        raw,
        "required_columns",
    )

    minimum_required_columns = {
        "hospital",
        "dt_interna",
        "dt_sin_pri",
        "evolucao",
    }
    missing_required = sorted(
        minimum_required_columns.difference(required_columns)
    )

    if missing_required:
        raise ValueError(
            "required_columns nao inclui as colunas minimas: "
            + ", ".join(missing_required)
        )

    target_source_column = _require_nonempty_string(
        target_section,
        "source_column",
    )
    target_output_column = _require_nonempty_string(
        target_section,
        "output_column",
    )

    target_mapping = _parse_target_mapping(
        _require_mapping(target_section, "mapping")
    )

    target_excluded_codes = _require_unique_string_sequence(
        target_section,
        "excluded_codes",
    )

    target_exclude_missing = target_section.get("exclude_missing")

    if not isinstance(target_exclude_missing, bool):
        raise ValueError(
            "target.exclude_missing precisa ser booleano."
        )

    if target_source_column not in required_columns:
        raise ValueError(
            "A coluna de origem do alvo precisa estar em required_columns."
        )

    if set(target_mapping).intersection(target_excluded_codes):
        raise ValueError(
            "Um codigo do alvo nao pode estar simultaneamente em mapping "
            "e excluded_codes."
        )

    outputs = _parse_outputs(outputs_section)

    return CohortContract(
        contract_id=contract_id,
        version=version,
        status=status,
        description=description,
        source_path=source_path,
        source_manifest_path=source_manifest_path,
        audit_parameters=audit_parameters,
        rule_order=rule_order,
        rules=rules,
        required_columns=required_columns,
        target_source_column=target_source_column,
        target_output_column=target_output_column,
        target_mapping=target_mapping,
        target_excluded_codes=target_excluded_codes,
        target_exclude_missing=target_exclude_missing,
        outputs=outputs,
    )


def _parse_rules(
    rules_raw: Mapping[str, Any],
) -> dict[str, CohortRuleContract]:
    rules: dict[str, CohortRuleContract] = {}

    for rule_id, value in rules_raw.items():
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise ValueError(
                "Todo identificador de regra precisa ser texto nao vazio."
            )

        if not isinstance(value, dict):
            raise ValueError(
                f"A regra {rule_id!r} precisa ser um objeto YAML."
            )

        action = _require_nonempty_string(value, "action")
        rationale = _require_nonempty_string(value, "rationale")
        decision_id_raw = value.get("decision_id")

        if action not in VALID_RULE_ACTIONS:
            raise ValueError(
                f"Acao invalida para {rule_id!r}: {action!r}. "
                f"Permitidas: {sorted(VALID_RULE_ACTIONS)}"
            )

        if decision_id_raw is not None:
            if (
                not isinstance(decision_id_raw, str)
                or not decision_id_raw.strip()
            ):
                raise ValueError(
                    f"decision_id invalido para {rule_id!r}."
                )
            decision_id = decision_id_raw.strip()
        else:
            decision_id = None

        if action in {"approved_exclusion", "quarantine"}:
            if decision_id is None:
                raise ValueError(
                    f"A regra {rule_id!r} remove registros e exige "
                    "decision_id."
                )

        rules[rule_id] = CohortRuleContract(
            rule_id=rule_id,
            action=action,
            rationale=rationale,
            decision_id=decision_id,
        )

    return rules


def _parse_target_mapping(
    mapping_raw: Mapping[str, Any],
) -> dict[str, int]:
    mapping: dict[str, int] = {}

    for source_code, target_value in mapping_raw.items():
        normalized_code = str(source_code).strip()

        if not normalized_code:
            raise ValueError(
                "O mapeamento do alvo contem codigo vazio."
            )

        if isinstance(target_value, bool) or target_value not in {0, 1}:
            raise ValueError(
                "Os valores produzidos pelo alvo precisam ser 0 ou 1."
            )

        mapping[normalized_code] = int(target_value)

    if set(mapping.values()) != {0, 1}:
        raise ValueError(
            "O mapeamento do alvo precisa produzir as classes 0 e 1."
        )

    return mapping


def _parse_outputs(
    outputs_raw: Mapping[str, Any],
) -> dict[str, Path]:
    required_output_keys = {
        "candidate_directory",
        "candidate_parquet",
        "audit_summary",
        "simulated_waterfall",
        "effective_waterfall",
        "manifest",
        "publication_validation",
        "published_parquet",
    }

    missing = sorted(required_output_keys.difference(outputs_raw))
    extra = sorted(set(outputs_raw).difference(required_output_keys))

    if missing or extra:
        raise ValueError(
            "A secao outputs possui chaves invalidas. "
            f"Ausentes: {missing}. Extras: {extra}."
        )

    return {
        key: Path(_require_nonempty_string(outputs_raw, key))
        for key in sorted(required_output_keys)
    }


def _require_mapping(
    mapping: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any]:
    value = mapping.get(key)

    if not isinstance(value, dict):
        raise ValueError(
            f"A chave {key!r} precisa conter um objeto YAML."
        )

    return value


def _require_nonempty_string(
    mapping: Mapping[str, Any],
    key: str,
) -> str:
    value = mapping.get(key)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"A chave {key!r} precisa ser texto nao vazio."
        )

    return value.strip()


def _require_positive_integer(
    mapping: Mapping[str, Any],
    key: str,
) -> int:
    value = mapping.get(key)

    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(
            f"A chave {key!r} precisa ser inteiro positivo."
        )

    return value


def _require_nonnegative_integer(
    mapping: Mapping[str, Any],
    key: str,
) -> int:
    value = mapping.get(key)

    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(
            f"A chave {key!r} precisa ser inteiro nao negativo."
        )

    return value


def _require_unique_string_sequence(
    mapping: Mapping[str, Any],
    key: str,
) -> tuple[str, ...]:
    value = mapping.get(key)

    if not isinstance(value, list) or not value:
        raise ValueError(
            f"A chave {key!r} precisa ser uma lista nao vazia."
        )

    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(
            f"A chave {key!r} aceita somente textos nao vazios."
        )

    normalized = tuple(item.strip() for item in value)

    if len(normalized) != len(set(normalized)):
        raise ValueError(
            f"A chave {key!r} nao pode conter duplicatas."
        )

    return normalized


def _parse_contract_date(
    mapping: Mapping[str, Any],
    key: str,
) -> pd.Timestamp:
    raw_value = _require_nonempty_string(mapping, key)
    parsed = pd.to_datetime(raw_value, errors="coerce")

    if pd.isna(parsed):
        raise ValueError(
            f"A chave {key!r} precisa conter uma data valida."
        )

    return pd.Timestamp(parsed)


CohortKind = Literal["final"]

_ENV_VAR: str = "SRAG_COHORT_KIND"
_DEFAULT_KIND: str = "final"
_VALID_KINDS: frozenset[str] = frozenset(get_args(CohortKind))
_RETIRED_KINDS: frozenset[str] = frozenset({"provisional", "auto"})
_ANALYTICAL_DIR = Path("data") / "analytical"

_FILENAMES_BY_KIND: dict[str, tuple[str, ...]] = {
    "final": ("coorte_final.parquet",),
}

_KIND_BY_FILENAME: dict[str, str] = {
    name.lower(): kind
    for kind, names in _FILENAMES_BY_KIND.items()
    for name in names
}


@dataclass(frozen=True)
class CohortSource:
    """Metadados imutáveis da coorte selecionada."""

    kind: str
    path: str
    sha256: str
    size_bytes: int
    rows: int
    columns: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def cohort_candidates(root: Path) -> dict[str, tuple[Path, ...]]:
    """Candidatos de coorte por tipo, na ordem de preferência."""
    analytical = root / _ANALYTICAL_DIR
    return {
        kind: tuple(analytical / name for name in names)
        for kind, names in _FILENAMES_BY_KIND.items()
    }


def resolve_cohort_path(
    root: Path,
    *,
    kind: CohortKind | None = None,
    explicit_path: Path | None = None,
) -> tuple[str, Path]:
    """Resolve o caminho da coorte definitiva."""
    if explicit_path is not None:
        return _resolve_explicit_path(explicit_path, requested_kind=kind)

    selected = _resolve_kind(kind)
    candidates = cohort_candidates(root)
    preference = (selected,)

    for effective_kind in preference:
        for path in candidates[effective_kind]:
            if path.is_file():
                return effective_kind, path.resolve()

    raise FileNotFoundError(_not_found_message(selected, preference, candidates))


def load_cohort(
    root: Path,
    *,
    kind: CohortKind | None = None,
    explicit_path: Path | None = None,
    columns: list[str] | None = None,
) -> tuple[pd.DataFrame, CohortSource]:
    """Carrega a coorte selecionada e devolve dados + metadados da fonte."""
    effective_kind, path = resolve_cohort_path(
        root, kind=kind, explicit_path=explicit_path,
    )
    frame = pd.read_parquet(path, columns=columns)
    for col in frame.select_dtypes(include=["object", "string"]).columns:
        if frame[col].nunique(dropna=True) <= 1000:
            frame[col] = frame[col].astype("category")
    source = CohortSource(
        kind=effective_kind,
        path=str(path),
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        rows=int(len(frame)),
        columns=int(frame.shape[1]),
    )
    return frame, source


def _resolve_kind(kind: CohortKind | None) -> str:
    """Normaliza o tipo solicitado (parâmetro ou env var)."""
    selected = (kind or os.getenv(_ENV_VAR, _DEFAULT_KIND)).lower()
    if selected in _RETIRED_KINDS:
        raise ValueError(
            f"Tipo de coorte {selected!r} não é mais aceito: a coorte "
            "provisória foi aposentada e o projeto usa apenas a definitiva. "
            f"Use 'final' (parâmetro kind ou variável {_ENV_VAR})."
        )
    if selected not in _VALID_KINDS:
        raise ValueError(
            f"{_ENV_VAR} deve ser final. Recebido: {selected!r}."
        )
    return selected


def _kind_from_path(path: Path) -> str:
    """Classifica uma coorte pelo nome canônico."""
    kind = _KIND_BY_FILENAME.get(path.name.lower())
    if kind is not None:
        return kind
    raise ValueError(_unknown_filename_message(path))


def _resolve_explicit_path(
    explicit_path: Path,
    *,
    requested_kind: CohortKind | None,
) -> tuple[str, Path]:
    """Valida o tipo pedido, a existência e o nome canônico do arquivo."""
    if requested_kind is not None:
        _resolve_kind(requested_kind)

    path = Path(explicit_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Coorte explícita não encontrada: {path}")

    return _kind_from_path(path), path


def _unknown_filename_message(path: Path) -> str:
    known = ", ".join(
        f"{name} ({kind})"
        for kind, names in _FILENAMES_BY_KIND.items()
        for name in names
    )
    aposentada = ""
    if path.name.lower().startswith("coorte_provisoria"):
        aposentada = " A coorte provisória foi aposentada."
    return (
        f"Nome de coorte não reconhecido: {path.name!r}. "
        f"Esperado um de: {known}.{aposentada} "
        "Renomeie o arquivo para o nome canônico da coorte definitiva."
    )


def _not_found_message(
    selected: str,
    preference: tuple[str, ...],
    candidates: dict[str, tuple[Path, ...]],
) -> str:
    paths = "\n".join(
        f"- {path}" for kind in preference for path in candidates[kind]
    )
    return f"Nenhuma coorte do tipo {selected!r} encontrada. Candidatos:\n{paths}"


@dataclass(frozen=True)
class FinalCohortCandidate:
    """Resultado da construção em memória da candidata."""

    frame: pd.DataFrame
    audit_evaluation: CohortAuditEvaluation
    audit_summary: pd.DataFrame
    rule_overlap: pd.DataFrame
    simulated_waterfall: pd.DataFrame
    effective_waterfall: pd.DataFrame
    excluded_mask: pd.Series
    total_source_rows: int
    total_excluded_rows: int
    total_candidate_rows: int

    @property
    def exclusion_rate(self) -> float:
        """Retorna a proporção excluída em relação à fonte."""

        if self.total_source_rows == 0:
            return 0.0

        return (
            self.total_excluded_rows
            / self.total_source_rows
        )


def build_final_cohort_candidate(
    frame: pd.DataFrame,
    contract: CohortContract,
) -> FinalCohortCandidate:
    """Constrói uma candidata sem modificar o DataFrame recebido."""

    _validate_candidate_input(
        frame=frame,
        contract=contract,
    )

    source = frame.copy(deep=True)

    audit_evaluation = evaluate_audit_rules(
        frame=source,
        parameters=contract.audit_parameters,
    )

    audit_summary = summarize_audit_rules(
        audit_evaluation
    )

    rule_overlap = build_rule_overlap(
        evaluation=audit_evaluation,
        rule_order=contract.rule_order,
    )

    simulated_waterfall = build_simulated_waterfall(
        evaluation=audit_evaluation,
        rule_order=contract.rule_order,
    )

    approved_rule_ids = (
        contract.approved_exclusion_rule_ids
    )

    excluded_mask = build_approved_exclusion_mask(
        evaluation=audit_evaluation,
        approved_rule_ids=approved_rule_ids,
    )

    effective_waterfall = build_simulated_waterfall(
        evaluation=audit_evaluation,
        rule_order=approved_rule_ids,
    )

    candidate = (
        source.loc[~excluded_mask]
        .copy()
    )

    normalized_target = normalize_srag_code(
        candidate[contract.target_source_column]
    )

    candidate[contract.target_output_column] = (
        normalized_target.map(
            contract.target_mapping
        )
    )

    _validate_candidate_output(
        source=source,
        candidate=candidate,
        contract=contract,
        excluded_mask=excluded_mask,
    )

    candidate[contract.target_output_column] = (
        candidate[contract.target_output_column]
        .astype("int8")
    )

    total_source_rows = int(len(source))
    total_excluded_rows = int(excluded_mask.sum())
    total_candidate_rows = int(len(candidate))

    if (
        total_source_rows
        != total_excluded_rows + total_candidate_rows
    ):
        raise RuntimeError(
            "A contagem da candidata não fecha com a fonte "
            "e a máscara de exclusão."
        )

    return FinalCohortCandidate(
        frame=candidate,
        audit_evaluation=audit_evaluation,
        audit_summary=audit_summary,
        rule_overlap=rule_overlap,
        simulated_waterfall=simulated_waterfall,
        effective_waterfall=effective_waterfall,
        excluded_mask=excluded_mask.copy(),
        total_source_rows=total_source_rows,
        total_excluded_rows=total_excluded_rows,
        total_candidate_rows=total_candidate_rows,
    )


def _validate_candidate_input(
    frame: pd.DataFrame,
    contract: CohortContract,
) -> None:
    """Valida o contrato mínimo antes de avaliar qualquer regra."""

    if not isinstance(frame, pd.DataFrame):
        raise TypeError(
            "frame precisa ser um pandas.DataFrame."
        )

    if frame.empty:
        raise ValueError(
            "A fonte da candidata não pode estar vazia."
        )

    missing_columns = sorted(
        set(contract.required_columns)
        - set(frame.columns)
    )

    if missing_columns:
        raise ValueError(
            "A fonte não contém todas as colunas exigidas "
            "pelo contrato: "
            + ", ".join(missing_columns)
        )

    if (
        contract.target_source_column
        not in frame.columns
    ):
        raise ValueError(
            "A coluna de origem do alvo não existe "
            "na fonte."
        )

    if (
        contract.target_output_column
        in frame.columns
    ):
        raise ValueError(
            "A coluna de saída do alvo já existe na fonte: "
            f"{contract.target_output_column!r}."
        )

    duplicated_columns = (
        frame.columns[
            frame.columns.duplicated()
        ]
        .tolist()
    )

    if duplicated_columns:
        raise ValueError(
            "A fonte contém colunas duplicadas: "
            f"{duplicated_columns}"
        )

    if not frame.index.is_unique:
        raise ValueError(
            "O índice da fonte precisa ser único antes "
            "da construção da candidata."
        )


def _validate_candidate_output(
    source: pd.DataFrame,
    candidate: pd.DataFrame,
    contract: CohortContract,
    excluded_mask: pd.Series,
) -> None:
    """Valida invariantes populacionais após as exclusões."""

    if len(excluded_mask) != len(source):
        raise RuntimeError(
            "A máscara de exclusão não possui o mesmo "
            "tamanho da fonte."
        )

    if not excluded_mask.index.equals(source.index):
        raise RuntimeError(
            "A máscara de exclusão não está alinhada "
            "ao índice da fonte."
        )

    if candidate.empty:
        raise ValueError(
            "As regras aprovadas removeram todos os registros."
        )

    if not candidate.index.is_unique:
        raise RuntimeError(
            "A candidata possui índice duplicado."
        )

    if not candidate.index.isin(source.index).all():
        raise RuntimeError(
            "A candidata contém índices inexistentes na fonte."
        )

    target = candidate[
        contract.target_output_column
    ]

    if target.isna().any():
        unexpected_codes = sorted(
            normalize_srag_code(
                candidate[
                    contract.target_source_column
                ]
            )
            .loc[target.isna()]
            .dropna()
            .unique()
            .tolist()
        )

        raise RuntimeError(
            "A candidata contém valores sem mapeamento "
            "no alvo principal. "
            f"Códigos observados: {unexpected_codes}"
        )

    observed_target_values = set(
        pd.to_numeric(
            target,
            errors="coerce",
        )
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    if not observed_target_values.issubset(
        {0, 1}
    ):
        raise RuntimeError(
            "O alvo produzido contém valores fora de 0 e 1: "
            f"{sorted(observed_target_values)}"
        )

    if contract.target_exclude_missing:
        normalized_source_target = normalize_srag_code(
            candidate[
                contract.target_source_column
            ]
        )

        if normalized_source_target.isna().any():
            raise RuntimeError(
                "A candidata preservou valores ausentes "
                "na coluna de origem do alvo."
            )

    excluded_codes_present = sorted(
        set(
            normalize_srag_code(
                candidate[
                    contract.target_source_column
                ]
            )
            .dropna()
            .unique()
            .tolist()
        )
        .intersection(
            contract.target_excluded_codes
        )
    )

    if excluded_codes_present:
        raise RuntimeError(
            "A candidata preservou códigos explicitamente "
            "excluídos do alvo: "
            f"{excluded_codes_present}"
        )


ROOT_DIR = Path(__file__).resolve().parents[1]

DEFAULT_CONTRACT_PATH = (
    ROOT_DIR
    / "configs"
    / "final_cohort_v1.yaml"
)


def resolve_project_path(path: Path) -> Path:
    """Resolve caminhos relativos a partir da raiz do projeto."""

    normalized_path = Path(path)

    if normalized_path.is_absolute():
        return normalized_path

    return ROOT_DIR / normalized_path


def validate_audit_outputs(
    output_paths: Sequence[Path],
    overwrite: bool,
) -> None:
    """Impede a substituição acidental de auditorias anteriores."""

    existing_paths = [
        path
        for path in output_paths
        if path.exists()
    ]

    if existing_paths and not overwrite:
        formatted_paths = "\n".join(
            f"- {path}"
            for path in existing_paths
        )

        raise FileExistsError(
            "Já existem artefatos da auditoria:\n"
            f"{formatted_paths}\n"
            "Use --overwrite somente após revisar "
            "a execução anterior."
        )


def build_rules_by_year(
    evaluation: CohortAuditEvaluation,
) -> pd.DataFrame:
    """Resume cada regra pelo ano da internação."""

    years = (
        evaluation.normalized[
            "dt_interna_parseada"
        ]
        .dt.year
        .astype("Int64")
        .astype("string")
        .fillna("SEM_ANO_VALIDO")
    )

    rows: list[dict[str, object]] = []

    for rule_id, mask in evaluation.masks.items():
        counts = (
            years.loc[mask]
            .value_counts(dropna=False)
            .sort_index()
        )

        for year, count in counts.items():
            rows.append(
                {
                    "ano_internacao": str(year),
                    "regra": rule_id,
                    "linhas_sinalizadas": int(count),
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "ano_internacao",
            "regra",
            "linhas_sinalizadas",
        ],
    )


def build_rules_by_outcome(
    evaluation: CohortAuditEvaluation,
) -> pd.DataFrame:
    """Resume cada regra pelo código normalizado de evolução."""

    outcome = (
        evaluation.normalized[
            "evolucao_normalizada"
        ]
        .fillna("AUSENTE")
    )

    rows: list[dict[str, object]] = []

    for rule_id, mask in evaluation.masks.items():
        counts = (
            outcome.loc[mask]
            .value_counts(dropna=False)
            .sort_index()
        )

        for value, count in counts.items():
            rows.append(
                {
                    "evolucao_normalizada": str(value),
                    "regra": rule_id,
                    "linhas_sinalizadas": int(count),
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "evolucao_normalizada",
            "regra",
            "linhas_sinalizadas",
        ],
    )


def resolve_audit_output_paths(
    contract: CohortContract,
) -> dict[str, Path]:
    """Resolve todos os caminhos produzidos pelo modo de auditoria."""

    output_directory = resolve_project_path(
        contract.outputs[
            "candidate_directory"
        ]
    )

    return {
        "output_directory": output_directory,
        "audit_summary": resolve_project_path(
            contract.outputs[
                "audit_summary"
            ]
        ),
        "simulated_waterfall": resolve_project_path(
            contract.outputs[
                "simulated_waterfall"
            ]
        ),
        "rule_overlap": (
            output_directory
            / "sobreposicao_regras.csv"
        ),
        "rules_by_year": (
            output_directory
            / "regras_por_ano.csv"
        ),
        "rules_by_outcome": (
            output_directory
            / "regras_por_evolucao.csv"
        ),
        "audit_manifest": (
            output_directory
            / "manifesto_auditoria.json"
        ),
    }


def write_audit_outputs(
    audit_summary: pd.DataFrame,
    simulated_waterfall: pd.DataFrame,
    rule_overlap: pd.DataFrame,
    rules_by_year: pd.DataFrame,
    rules_by_outcome: pd.DataFrame,
    output_paths: dict[str, Path],
) -> None:
    """Grava os relatórios tabulares produzidos pela auditoria."""

    for key, path in output_paths.items():
        if key == "output_directory":
            continue

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    audit_summary.to_csv(
        output_paths["audit_summary"],
        index=False,
        encoding="utf-8-sig",
    )

    simulated_waterfall.to_csv(
        output_paths["simulated_waterfall"],
        index=False,
        encoding="utf-8-sig",
    )

    rule_overlap.to_csv(
        output_paths["rule_overlap"],
        encoding="utf-8-sig",
    )

    rules_by_year.to_csv(
        output_paths["rules_by_year"],
        index=False,
        encoding="utf-8-sig",
    )

    rules_by_outcome.to_csv(
        output_paths["rules_by_outcome"],
        index=False,
        encoding="utf-8-sig",
    )


def build_audit_manifest(
    contract: CohortContract,
    contract_path: Path,
    source_path: Path,
    source: pd.DataFrame,
    columns_read: list[str],
    evaluation: CohortAuditEvaluation,
    output_paths: dict[str, Path],
) -> dict[str, object]:
    """Monta o manifesto da auditoria sem alterar a fonte."""

    approved_exclusion_counts = {
        rule_id: int(
            evaluation.masks[
                rule_id
            ].sum()
        )
        for rule_id
        in contract.approved_exclusion_rule_ids
    }

    audit_only_counts = {
        rule_id: int(
            evaluation.masks[
                rule_id
            ].sum()
        )
        for rule_id
        in contract.audit_only_rule_ids
    }

    return {
        "schema_version": 1,
        "kind": "final_cohort_pre_exclusion_audit",
        "generated_at_utc": (
            datetime.now(timezone.utc).isoformat()
        ),
        "contract": {
            "id": contract.contract_id,
            "version": contract.version,
            "status": contract.status,
            "path": str(contract_path),
        },
        "source": {
            "path": str(source_path),
            "rows": int(len(source)),
            "columns_read": columns_read,
        },
        "execution_guarantees": {
            "source_modified": False,
            "candidate_generated": False,
            "cohort_published": False,
            "exclusions_applied": False,
            "partitions_created": False,
            "test_consulted": False,
        },
        "approved_exclusion_counts": (
            approved_exclusion_counts
        ),
        "audit_only_counts": (
            audit_only_counts
        ),
        "outputs": {
            key: str(path)
            for key, path in output_paths.items()
            if key != "output_directory"
        },
        "environment": {
            "python": sys.version,
            "pandas": pd.__version__,
        },
    }


def execute_audit(
    contract: CohortContract,
    contract_path: Path,
    overwrite: bool,
) -> None:
    """Executa a auditoria real sem aplicar exclusões."""

    source_path = resolve_project_path(
        contract.source_path
    )

    if not source_path.is_file():
        raise FileNotFoundError(
            "A fonte declarada no contrato não foi encontrada: "
            f"{source_path}"
        )

    output_paths = resolve_audit_output_paths(
        contract
    )

    output_paths["output_directory"].mkdir(
        parents=True,
        exist_ok=True,
    )

    paths_to_validate = [
        path
        for key, path in output_paths.items()
        if key != "output_directory"
    ]

    validate_audit_outputs(
        output_paths=paths_to_validate,
        overwrite=overwrite,
    )

    columns_to_read = list(
        dict.fromkeys(
            contract.required_columns
        )
    )

    print(
        "Fonte:",
        source_path,
    )

    print(
        "Contrato:",
        contract_path,
    )

    print(
        "Colunas da auditoria:",
        columns_to_read,
    )

    source = pd.read_parquet(
        source_path,
        columns=columns_to_read,
    )

    if source.empty:
        raise ValueError(
            "A fonte foi carregada, mas não contém registros."
        )

    print(
        "Linhas carregadas:",
        len(source),
    )

    evaluation = evaluate_audit_rules(
        frame=source,
        parameters=contract.audit_parameters,
    )

    audit_summary = summarize_audit_rules(
        evaluation
    )

    rule_overlap = build_rule_overlap(
        evaluation=evaluation,
        rule_order=contract.rule_order,
    )

    simulated_waterfall = build_simulated_waterfall(
        evaluation=evaluation,
        rule_order=contract.rule_order,
    )

    rules_by_year = build_rules_by_year(
        evaluation
    )

    rules_by_outcome = build_rules_by_outcome(
        evaluation
    )

    write_audit_outputs(
        audit_summary=audit_summary,
        simulated_waterfall=simulated_waterfall,
        rule_overlap=rule_overlap,
        rules_by_year=rules_by_year,
        rules_by_outcome=rules_by_outcome,
        output_paths=output_paths,
    )

    manifest = build_audit_manifest(
        contract=contract,
        contract_path=contract_path,
        source_path=source_path,
        source=source,
        columns_read=columns_to_read,
        evaluation=evaluation,
        output_paths=output_paths,
    )

    output_paths[
        "audit_manifest"
    ].write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("Auditoria concluída.")

    print(
        "Regras aprovadas para exclusão:",
        manifest[
            "approved_exclusion_counts"
        ],
    )

    print(
        "Regras pendentes de decisão:",
        manifest[
            "audit_only_counts"
        ],
    )

    print(
        "Diretório dos resultados:",
        output_paths[
            "output_directory"
        ],
    )

    print("Nenhuma exclusão foi aplicada.")
    print("Nenhuma candidata foi gerada.")
    print("Nenhuma coorte foi publicada.")


def resolve_candidate_output_paths(
    contract: CohortContract,
) -> dict[str, Path]:
    """Resolve os arquivos produzidos pelo modo candidate."""

    candidate_path = resolve_project_path(
        contract.outputs["candidate_parquet"]
    )

    return {
        "candidate_parquet": candidate_path,
        "effective_waterfall": resolve_project_path(
            contract.outputs["effective_waterfall"]
        ),
        "manifest": resolve_project_path(
            contract.outputs["manifest"]
        ),
        "publication_validation": resolve_project_path(
            contract.outputs["publication_validation"]
        ),
        "temporary_candidate": candidate_path.with_suffix(
            candidate_path.suffix + ".tmp"
        ),
    }


def validate_candidate_preconditions(
    contract: CohortContract,
    output_paths: dict[str, Path],
    overwrite: bool,
) -> None:
    """Recusa decisões pendentes, saídas existentes e temporários abandonados."""

    if contract.audit_only_rule_ids:
        raise ValueError(
            "A candidata não pode ser gerada enquanto existirem "
            "regras audit_only: "
            f"{contract.audit_only_rule_ids}."
        )

    temporary_path = output_paths["temporary_candidate"]

    if temporary_path.exists():
        raise FileExistsError(
            "Existe um arquivo temporário de execução anterior: "
            f"{temporary_path}. Revise e remova o arquivo antes de continuar."
        )

    final_paths = [
        output_paths["candidate_parquet"],
        output_paths["effective_waterfall"],
        output_paths["manifest"],
        output_paths["publication_validation"],
    ]
    existing_paths = [path for path in final_paths if path.exists()]

    if existing_paths and not overwrite:
        formatted = "\n".join(f"- {path}" for path in existing_paths)
        raise FileExistsError(
            "Já existem artefatos da candidata:\n"
            f"{formatted}\n"
            "Use --overwrite somente após revisar a execução anterior."
        )


def build_global_effective_waterfall(
    rule_order: Sequence[str],
    excluded_by_rule: dict[str, int],
    total_source_rows: int,
) -> pd.DataFrame:
    """Consolida o waterfall efetivo acumulado entre os row groups."""

    remaining = total_source_rows
    rows: list[dict[str, object]] = []

    for order, rule_id in enumerate(rule_order, start=1):
        excluded = int(excluded_by_rule[rule_id])
        remaining -= excluded
        rows.append(
            {
                "ordem": order,
                "regra": rule_id,
                "excluidas_na_etapa": excluded,
                "restantes_apos_etapa": remaining,
            }
        )

    return pd.DataFrame(rows)


def validate_temporary_candidate(
    path: Path,
    contract: CohortContract,
    expected_rows: int,
    expected_columns: int,
) -> dict[str, object]:
    """Valida a candidata temporária antes da promoção do arquivo."""

    parquet_file = pq.ParquetFile(path)
    metadata = parquet_file.metadata

    if metadata.num_rows != expected_rows:
        raise ValueError(
            "A contagem física da candidata diverge da execução: "
            f"esperado={expected_rows}, observado={metadata.num_rows}."
        )

    if metadata.num_columns != expected_columns:
        raise ValueError(
            "A quantidade de colunas da candidata diverge do esperado: "
            f"esperado={expected_columns}, observado={metadata.num_columns}."
        )

    required_validation_columns = [
        "id_registro",
        "hospital",
        "dt_interna",
        "dt_sin_pri",
        "evolucao",
        contract.target_output_column,
    ]
    available_columns = set(parquet_file.schema_arrow.names)
    missing_columns = sorted(
        set(required_validation_columns) - available_columns
    )

    if missing_columns:
        raise ValueError(
            "A candidata não contém colunas obrigatórias para validação: "
            f"{missing_columns}."
        )

    table = pq.read_table(
        path,
        columns=required_validation_columns,
    )
    frame = table.to_pandas(types_mapper=pd.ArrowDtype)

    if frame["id_registro"].isna().any():
        raise ValueError("A candidata contém id_registro ausente.")

    distinct_ids = int(
        pc.count_distinct(table["id_registro"]).as_py()
    )

    if distinct_ids != expected_rows:
        raise ValueError(
            "A candidata contém id_registro duplicado: "
            f"linhas={expected_rows}, distintos={distinct_ids}."
        )

    evaluation = evaluate_audit_rules(
        frame=frame,
        parameters=contract.audit_parameters,
    )
    surviving_violations = {
        rule_id: int(evaluation.masks[rule_id].sum())
        for rule_id in contract.approved_exclusion_rule_ids
    }

    if any(surviving_violations.values()):
        raise ValueError(
            "A candidata temporária ainda contém violações aprovadas: "
            f"{surviving_violations}."
        )

    target = frame[contract.target_output_column]

    if target.isna().any():
        raise ValueError("O alvo da candidata contém valores ausentes.")

    observed_target = set(
        pd.to_numeric(target, errors="coerce")
        .dropna()
        .astype("int8")
        .unique()
        .tolist()
    )

    if not observed_target <= {0, 1}:
        raise ValueError(
            "O alvo da candidata contém valores fora de 0 e 1: "
            f"{sorted(observed_target)}."
        )

    return {
        "physical_rows": int(metadata.num_rows),
        "physical_columns": int(metadata.num_columns),
        "row_groups": int(parquet_file.num_row_groups),
        "id_registro_missing": 0,
        "id_registro_distinct": distinct_ids,
        "approved_rule_violations": surviving_violations,
        "target_missing": 0,
        "target_values": sorted(observed_target),
    }


def execute_candidate(
    contract: CohortContract,
    contract_path: Path,
    overwrite: bool,
) -> None:
    """Materializa a candidata por row group sem criar partições ou publicar."""

    source_path = resolve_project_path(contract.source_path)

    if not source_path.is_file():
        raise FileNotFoundError(
            "A fonte declarada no contrato não foi encontrada: "
            f"{source_path}"
        )

    output_paths = resolve_candidate_output_paths(contract)
    validate_candidate_preconditions(
        contract=contract,
        output_paths=output_paths,
        overwrite=overwrite,
    )

    for path in output_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = output_paths["temporary_candidate"]
    parquet_file = pq.ParquetFile(source_path)
    source_columns = parquet_file.schema_arrow.names

    if contract.target_output_column in source_columns:
        raise ValueError(
            "A coluna de alvo já existe na fonte: "
            f"{contract.target_output_column}."
        )

    if "id_registro" not in source_columns:
        raise ValueError(
            "A fonte não contém o identificador técnico id_registro."
        )

    source_rows = int(parquet_file.metadata.num_rows)
    excluded_by_rule = {
        rule_id: 0
        for rule_id in contract.approved_exclusion_rule_ids
    }
    raw_rule_counts = {
        rule_id: 0
        for rule_id in contract.rule_order
    }
    candidate_rows = 0
    writer: pq.ParquetWriter | None = None
    candidate_schema: pa.Schema | None = None

    print("Fonte:", source_path)
    print("Contrato:", contract_path)
    print("Row groups:", parquet_file.num_row_groups)
    print("Linhas da fonte:", source_rows)

    try:
        for row_group_index in range(parquet_file.num_row_groups):
            table = parquet_file.read_row_group(row_group_index)
            frame = table.to_pandas(types_mapper=pd.ArrowDtype)
            result = build_final_cohort_candidate(
                frame=frame,
                contract=contract,
            )

            for rule_id in contract.rule_order:
                raw_rule_counts[rule_id] += int(
                    result.audit_evaluation.masks[rule_id].sum()
                )

            for row in result.effective_waterfall.itertuples(index=False):
                excluded_by_rule[str(row.regra)] += int(
                    row.excluidas_na_etapa
                )

            candidate_table = pa.Table.from_pandas(
                result.frame,
                preserve_index=False,
            )

            if writer is None:
                candidate_schema = candidate_table.schema
                writer = pq.ParquetWriter(
                    temporary_path,
                    candidate_schema,
                    compression="zstd",
                    version="2.6",
                )
            elif candidate_table.schema != candidate_schema:
                candidate_table = candidate_table.cast(candidate_schema)

            writer.write_table(candidate_table)
            candidate_rows += int(candidate_table.num_rows)

            print(
                f"Row group {row_group_index + 1}/{parquet_file.num_row_groups}: "
                f"fonte={len(frame)}, candidata={candidate_table.num_rows}"
            )

        if writer is None:
            raise ValueError("Nenhum row group foi gravado na candidata.")

        writer.close()
        writer = None

        total_excluded_rows = int(sum(excluded_by_rule.values()))

        if source_rows != total_excluded_rows + candidate_rows:
            raise ValueError(
                "As contagens globais não fecham: "
                f"fonte={source_rows}, excluídas={total_excluded_rows}, "
                f"candidata={candidate_rows}."
            )

        effective_waterfall = build_global_effective_waterfall(
            rule_order=contract.approved_exclusion_rule_ids,
            excluded_by_rule=excluded_by_rule,
            total_source_rows=source_rows,
        )
        expected_columns = len(source_columns) + 1
        validation = validate_temporary_candidate(
            path=temporary_path,
            contract=contract,
            expected_rows=candidate_rows,
            expected_columns=expected_columns,
        )
        source_hash = sha256_file(source_path)
        candidate_hash = sha256_file(temporary_path)
        temporary_parquet = pq.ParquetFile(temporary_path)
        schema = temporary_parquet.schema_arrow
        temporary_row_groups = temporary_parquet.num_row_groups
        temporary_parquet.close()
        generated_at = datetime.now(timezone.utc).isoformat()

        manifest = {
            "schema_version": 1,
            "kind": "final_cohort_candidate",
            "generated_at_utc": generated_at,
            "publication_performed": False,
            "legacy_parity_reviewed": False,
            "provisional_comparison_reviewed": False,
            "contract": {
                "id": contract.contract_id,
                "version": contract.version,
                "status": contract.status,
                "path": str(contract_path),
                "sha256": sha256_file(contract_path),
            },
            "source": {
                "path": str(source_path),
                "sha256": source_hash,
                "rows": source_rows,
                "columns": len(source_columns),
                "row_groups": parquet_file.num_row_groups,
            },
            "rules": [
                {
                    "rule_id": rule_id,
                    "action": contract.rules[rule_id].action,
                    "decision_id": contract.rules[rule_id].decision_id,
                    "raw_count": raw_rule_counts[rule_id],
                    "incremental_count": excluded_by_rule.get(rule_id, 0),
                }
                for rule_id in contract.rule_order
            ],
            "candidate": {
                "path": str(output_paths["candidate_parquet"]),
                "sha256": candidate_hash,
                "rows": candidate_rows,
                "columns": len(schema),
                "row_groups": temporary_row_groups,
                "column_names": schema.names,
                "dtypes": {
                    field.name: str(field.type)
                    for field in schema
                },
            },
            "population": {
                "source_rows": source_rows,
                "excluded_rows": total_excluded_rows,
                "candidate_rows": candidate_rows,
                "exclusion_rate": total_excluded_rows / source_rows,
            },
            "target": {
                "source_column": contract.target_source_column,
                "output_column": contract.target_output_column,
                "mapping": contract.target_mapping,
                "excluded_codes": list(contract.target_excluded_codes),
                "exclude_missing": contract.target_exclude_missing,
            },
            "period": {
                "start": contract.audit_parameters.period_start.isoformat(),
                "end": contract.audit_parameters.period_end.isoformat(),
            },
            "environment": {
                "python": platform.python_version(),
                "pandas": pd.__version__,
                "pyarrow": pa.__version__,
            },
            "execution_guarantees": {
                "source_modified": False,
                "candidate_generated": True,
                "cohort_published": False,
                "exclusions_applied": True,
                "partitions_created": False,
                "test_consulted": False,
            },
        }
        validation_document = {
            "schema_version": 1,
            "generated_at_utc": generated_at,
            "status": "approved_for_comparison",
            "candidate_sha256": candidate_hash,
            "checks": validation,
            "population_reconciliation": {
                "source_rows": source_rows,
                "excluded_rows": total_excluded_rows,
                "candidate_rows": candidate_rows,
                "closed": source_rows == total_excluded_rows + candidate_rows,
            },
            "publication_performed": False,
            "legacy_parity_reviewed": False,
            "provisional_comparison_reviewed": False,
        }

        waterfall_temporary = output_paths["effective_waterfall"].with_suffix(
            ".csv.tmp"
        )
        manifest_temporary = output_paths["manifest"].with_suffix(
            ".json.tmp"
        )
        validation_temporary = output_paths[
            "publication_validation"
        ].with_suffix(".json.tmp")

        effective_waterfall.to_csv(
            waterfall_temporary,
            index=False,
            encoding="utf-8-sig",
        )
        manifest_temporary.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        validation_temporary.write_text(
            json.dumps(
                validation_document,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        os.replace(temporary_path, output_paths["candidate_parquet"])
        os.replace(
            waterfall_temporary,
            output_paths["effective_waterfall"],
        )
        os.replace(manifest_temporary, output_paths["manifest"])
        os.replace(
            validation_temporary,
            output_paths["publication_validation"],
        )

        print()
        print("Candidata gerada e validada.")
        print("Linhas da fonte:", source_rows)
        print("Linhas excluídas:", total_excluded_rows)
        print("Linhas da candidata:", candidate_rows)
        print("Arquivo:", output_paths["candidate_parquet"])
        print("Nenhuma partição foi criada.")
        print("Nenhum conjunto de teste foi consultado.")
        print("A coorte ainda não foi publicada.")
    except Exception:
        if writer is not None:
            writer.close()

        if temporary_path.exists():
            try:
                temporary_path.unlink()
            except PermissionError:
                pass

        raise


def gerar_coorte(modo: str, sobrescrever: bool = False, contrato: Path = DEFAULT_CONTRACT_PATH) -> None:
    """Roda a auditoria ("audit") ou gera a candidata ("candidate")."""
    caminho = resolve_project_path(contrato)
    contract = load_cohort_contract(caminho)
    if modo == "audit":
        execute_audit(contract=contract, contract_path=caminho, overwrite=sobrescrever)
    elif modo == "candidate":
        execute_candidate(contract=contract, contract_path=caminho, overwrite=sobrescrever)
    else:
        raise ValueError(f"Modo inválido: {modo!r}. Use 'audit' ou 'candidate'.")


PARTICOES_CANONICAS: tuple[str, ...] = ("treino", "validacao", "teste")

MASTER_BLOCKS: tuple[str, ...] = (
    "train_ref",
    "val_ref",
    "test_ref",
    "test_pandemic",
)

DEFAULT_FRACOES_MASTER: dict[str, float] = {
    "train_ref": 0.70,
    "val_ref": 0.15,
    "test_ref": 0.15,
}

_VALORES_TEXTUAIS_AUSENTES = frozenset({"", "nan", "none", "null", "<na>"})


def criar_group_id(df: pd.DataFrame) -> pd.Series:
    """Cria o identificador estável usado no particionamento agrupado."""
    if "nu_notific" not in df.columns:
        raise KeyError("Coluna necessária para criar group_id ausente: 'nu_notific'")

    nu_notific = df["nu_notific"].astype("string").str.replace(r"\s+", "", regex=True)
    notific_normalizada = nu_notific.str.lower()
    notific_valida = nu_notific.notna() & ~notific_normalizada.isin(_VALORES_TEXTUAIS_AUSENTES)

    if notific_valida.all():
        return nu_notific.rename("group_id")

    if "id_registro" not in df.columns:
        raise KeyError("Coluna necessária para fallback de group_id ausente: 'id_registro'")

    id_registro = df["id_registro"].astype("string").str.strip()
    id_normalizado = id_registro.str.lower()
    id_invalido = id_registro.isna() | id_normalizado.isin(_VALORES_TEXTUAIS_AUSENTES)

    fallback_invalido = ~notific_valida & id_invalido
    if fallback_invalido.any():
        quantidade = int(fallback_invalido.sum())
        raise ValueError(
            f"id_registro ausente ou inválido em {quantidade} registro(s) "
            "que exigem fallback de group_id."
        )

    fallback = "sem_notific:" + id_registro
    group_id = nu_notific.where(notific_valida, fallback)
    return group_id.astype("string").rename("group_id")


def _hash_codes(
    grupos_unicos: pd.Index,
    estrato_grupo: np.ndarray,
    sal: str,
) -> np.ndarray:
    """Ordem estável dos grupos por hash dentro de cada estrato."""
    chaves = sal + "|" + pd.Series(grupos_unicos.astype(str), dtype=object)
    hashes = pd.util.hash_pandas_object(chaves, index=False).to_numpy(dtype=np.uint64)
    return np.lexsort((hashes, estrato_grupo))


def _validar_estratos(
    grupos: pd.Series,
    estratos: pd.Series,
    min_grupos_por_estrato: int,
    n_blocos: int,
) -> tuple[np.ndarray, pd.Index, np.ndarray]:
    """Fatoriza grupos/estratos e devolve (codigo_grupo, grupos_unicos, estrato_grupo)."""
    if grupos.isna().any():
        raise ValueError(f"'{grupos.name}' contém valores ausentes.")
    if estratos.isna().any():
        raise ValueError(f"'{estratos.name}' contém valores ausentes.")
    if min_grupos_por_estrato < n_blocos:
        raise ValueError(
            f"min_grupos_por_estrato deve ser >= {n_blocos}; "
            f"recebido {min_grupos_por_estrato!r}."
        )

    codigo_grupo, grupos_unicos = pd.factorize(grupos, sort=False)
    codigo_estrato_linha, estratos_unicos = pd.factorize(estratos, sort=True)
    n_grupos = len(grupos_unicos)

    estrato_min = np.full(n_grupos, np.iinfo(np.int64).max, dtype=np.int64)
    estrato_max = np.full(n_grupos, -1, dtype=np.int64)
    np.minimum.at(estrato_min, codigo_grupo, codigo_estrato_linha)
    np.maximum.at(estrato_max, codigo_grupo, codigo_estrato_linha)
    if int((estrato_min != estrato_max).sum()):
        raise ValueError("Há grupos com mais de um estrato.")
    estrato_grupo = estrato_min

    grupos_por_estrato = np.bincount(estrato_grupo, minlength=len(estratos_unicos))
    pequenos = [
        (str(estratos_unicos[i]), int(q))
        for i, q in enumerate(grupos_por_estrato)
        if q < min_grupos_por_estrato
    ]
    if pequenos:
        raise ValueError(f"Estratos abaixo de {min_grupos_por_estrato} grupos: {pequenos}")
    return codigo_grupo, grupos_unicos, estrato_grupo


def _posicao_no_estrato(
    grupos_unicos: pd.Index,
    estrato_grupo: np.ndarray,
    sal: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Devolve (posicao_dentro_do_estrato, tamanho_do_estrato) por grupo único."""
    ordem = _hash_codes(grupos_unicos, estrato_grupo, sal)
    n_grupos = len(grupos_unicos)
    tamanho_por_estrato = np.bincount(
        estrato_grupo, minlength=estrato_grupo.max() + 1 if n_grupos else 1
    )
    inicio = np.concatenate(([0], np.cumsum(tamanho_por_estrato)[:-1]))
    posicao = np.empty(n_grupos, dtype=np.int64)
    posicao[ordem] = np.arange(n_grupos) - inicio[estrato_grupo[ordem]]
    return posicao, tamanho_por_estrato[estrato_grupo]


def atribuir_blocos_por_hash(
    grupos: pd.Series,
    estratos: pd.Series,
    *,
    sal: str,
    fracoes: dict[str, float],
    min_grupos_por_estrato: int = 5,
) -> pd.Categorical:
    """Atribui cada grupo a um dos blocos definidos em ``fracoes``."""
    nomes = list(fracoes)
    valores = list(fracoes.values())
    if abs(sum(valores) - 1.0) > 1e-6:
        raise ValueError(f"Frações devem somar 1; soma={sum(valores):.6f}.")

    codigo_grupo, grupos_unicos, estrato_grupo = _validar_estratos(
        grupos, estratos, min_grupos_por_estrato, len(nomes)
    )
    posicao, tamanho = _posicao_no_estrato(grupos_unicos, estrato_grupo, sal)

    restante = len(nomes) - 1
    acumulado = 0.0
    codigo_bloco = np.zeros(len(grupos_unicos), dtype=np.int8)
    for fracao in valores[:-1]:
        acumulado += fracao
        corte = np.minimum(
            np.floor(tamanho * acumulado).astype(np.int64),
            tamanho - restante,
        )
        codigo_bloco = np.where(posicao >= corte, codigo_bloco + 1, codigo_bloco)
        restante -= 1

    return pd.Categorical.from_codes(
        codigo_bloco[codigo_grupo].astype(np.int64),
        categories=cast(Any, nomes),
    )


def _resolver_fracoes_master(
    blocos_cfg: dict[str, Any],
    blocos_compartilhados: list[str],
) -> dict[str, float]:
    fracoes = {
        nome: float(
            (blocos_cfg.get(nome) or {}).get("fracao", DEFAULT_FRACOES_MASTER[nome])
        )
        for nome in blocos_compartilhados
    }
    if abs(sum(fracoes.values()) - 1.0) > 1e-6:
        raise ValueError(
            f"Frações dos blocos compartilhados devem somar 1; recebido {fracoes}."
        )
    return fracoes


def _hash_bloco(grupos: pd.Series) -> str | None:
    if grupos.empty:
        return None
    chaves = sorted(grupos.astype(str).unique().tolist())
    return hashlib.sha256("|".join(chaves).encode()).hexdigest()


def _estrato_inteiro(
    sub: pd.DataFrame,
    year_column: str,
    target_column: str,
    region_column: str | None,
) -> pd.Series:
    """Códigos inteiros de (ano × alvo [× região])."""
    cod_ano, _ = pd.factorize(sub[year_column], sort=True)
    cod_alvo, _ = pd.factorize(sub[target_column], sort=True)
    cod = cod_ano.astype("int32") * 1000 + cod_alvo.astype("int32")
    if region_column is not None:
        regiao = sub[region_column].astype("string").fillna("__NA__")
        cod_regiao, _ = pd.factorize(regiao, sort=True)
        cod = cod * 100 + cod_regiao.astype("int32")
    return pd.Series(cod, index=sub.index, name="estrato")


def criar_particao_mestra(
    df: pd.DataFrame,
    *,
    temporal_cfg: dict[str, Any],
    group_column: str = "group_id",
    year_column: str = "ano_internacao",
    target_column: str = "alvo_obito_srag",
    region_column: str | None = "regiao_residencia",
    partition_column: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Materializa os quatro blocos de ``temporal.blocos`` no DataFrame."""
    partition_column = str(
        partition_column or temporal_cfg.get("coluna_particao") or "particao"
    )
    seed = int(temporal_cfg.get("seed", 42))
    sal = f"srag_particao_mestra_v1_seed{seed}"
    blocos_cfg = temporal_cfg.get("blocos") or {}
    if not blocos_cfg:
        raise ValueError("temporal.blocos vazio no supervised.yaml.")
    anos_por_bloco = {
        nome: {int(a) for a in cfg.get("anos", [])}
        for nome, cfg in blocos_cfg.items()
    }
    if set(anos_por_bloco) != set(MASTER_BLOCKS):
        raise ValueError(
            f"Blocos do YAML {sorted(anos_por_bloco)} "
            f"não conferem com MASTER_BLOCKS {sorted(MASTER_BLOCKS)}."
        )

    anos_pandemia = anos_por_bloco["test_pandemic"]
    blocos_compartilhados = [n for n in MASTER_BLOCKS if n != "test_pandemic"]
    anos_compartilhados = set().union(*(anos_por_bloco[n] for n in blocos_compartilhados))

    if anos_pandemia & anos_compartilhados:
        raise ValueError(
            "Anos em test_pandemic e nos blocos compartilhados ao mesmo tempo: "
            f"{sorted(anos_pandemia & anos_compartilhados)}. Verifique o YAML."
        )

    fracoes = _resolver_fracoes_master(blocos_cfg, blocos_compartilhados)
    min_grupos = int(temporal_cfg.get("min_grupos_por_estrato", 5))
    if min_grupos < len(blocos_compartilhados):
        raise ValueError(
            f"temporal.min_grupos_por_estrato={min_grupos} insuficiente "
            f"para {len(blocos_compartilhados)} blocos compartilhados; "
            f"use >= {len(blocos_compartilhados)}."
        )

    usar_regiao = bool(region_column and region_column in df.columns)
    colunas_estrato = [group_column, year_column, target_column]
    if usar_regiao and region_column is not None:
        colunas_estrato.append(region_column)

    out = df.copy(deep=False)
    out[partition_column] = pd.NA

    mascara_pandemia = out[year_column].isin(anos_pandemia)
    out.loc[mascara_pandemia, partition_column] = "test_pandemic"

    mascara_compartilhada = out[year_column].isin(anos_compartilhados)
    usado_fallback = False
    if mascara_compartilhada.any():
        sub = df.loc[mascara_compartilhada, colunas_estrato]
        estrato = _estrato_inteiro(
            sub, year_column, target_column,
            region_column if usar_regiao else None,
        )
        try:
            blocos = atribuir_blocos_por_hash(
                sub[group_column], estrato,
                sal=sal, fracoes=fracoes, min_grupos_por_estrato=min_grupos,
            )
        except ValueError as exc:
            if "Estratos abaixo de" not in str(exc):
                raise
            estrato = _estrato_inteiro(sub, year_column, target_column, None)
            blocos = atribuir_blocos_por_hash(
                sub[group_column], estrato,
                sal=sal, fracoes=fracoes, min_grupos_por_estrato=min_grupos,
            )
            usado_fallback = True
        del sub, estrato
        out.loc[mascara_compartilhada, partition_column] = blocos

    mascara_fora = ~(mascara_pandemia | mascara_compartilhada)
    out.loc[mascara_fora, partition_column] = "exploracao"

    if out[partition_column].isna().any():
        raise RuntimeError("Há linhas sem bloco atribuído.")

    blocos_por_grupo = (
        out[[group_column, partition_column]]
        .groupby(group_column)[partition_column]
        .nunique()
    )
    cruzados = blocos_por_grupo[blocos_por_grupo > 1]
    if not cruzados.empty:
        raise RuntimeError(
            f"{len(cruzados)} grupos em mais de um bloco; exemplos: "
            f"{cruzados.index.tolist()[:5]}. Verifique se algum group_id "
            "tem linhas em anos pandêmicos e não pandêmicos."
        )

    manifesto: dict[str, Any] = {
        "metodo": "hash_grupo_estratificado_mestre_v1",
        "salt": sal,
        "seed": seed,
        "min_grupos_por_estrato": min_grupos,
        "group_column": group_column,
        "year_column": year_column,
        "target_column": target_column,
        "region_column": region_column,
        "partition_column": partition_column,
        "fracoes": fracoes,
        "estratificacao": (
            "ano × alvo (fallback)" if usado_fallback else "ano × alvo × região"
        ),
        "blocos": {},
    }
    resumo = out[[group_column, year_column, target_column, partition_column]]
    for nome in (*MASTER_BLOCKS, "exploracao"):
        sub = resumo.loc[resumo[partition_column] == nome]
        manifesto["blocos"][nome] = {
            "n_linhas": int(len(sub)),
            "n_grupos": int(sub[group_column].nunique()) if len(sub) else 0,
            "anos": sorted(int(a) for a in sub[year_column].dropna().unique()),
            "prevalencia_alvo": (
                float(pd.to_numeric(sub[target_column], errors="coerce").mean())
                if len(sub) else None
            ),
            "hash_bloco": _hash_bloco(sub[group_column]),
        }
    return out, manifesto


DATASET_NAME = "dataset_supervisionado.parquet"
MANIFEST_NAME = "manifesto_supervisionado.json"
SCHEMA_VERSION = 2

_BLOCK_TRAIN_REF = "train_ref"
_BLOCK_VAL_REF = "val_ref"
_BLOCK_TEST_REF = "test_ref"
_BLOCK_TEST_PANDEMIC = "test_pandemic"
_BLOCK_EXPLORACAO = "exploracao"

BLOCOS_MESTRE: tuple[str, ...] = (
    _BLOCK_TRAIN_REF,
    _BLOCK_VAL_REF,
    _BLOCK_TEST_REF,
    _BLOCK_TEST_PANDEMIC,
    _BLOCK_EXPLORACAO,
)

BLOCKS_TESTE: frozenset[str] = frozenset({_BLOCK_TEST_REF, _BLOCK_TEST_PANDEMIC})

BLOCKS_PADRAO_LEITURA: tuple[str, ...] = (
    _BLOCK_TRAIN_REF,
    _BLOCK_VAL_REF,
)

_BLOCOS_OBRIGATORIOS: frozenset[str] = frozenset(BLOCOS_MESTRE) - {_BLOCK_EXPLORACAO}

ALLOWED_PARTITIONS: frozenset[str] = frozenset(BLOCOS_MESTRE)

_ESQUEMAS_COMPLETOS: frozenset[frozenset[str]] = frozenset(
    {
        _BLOCOS_OBRIGATORIOS,
        frozenset(BLOCOS_MESTRE),
    }
)

_PARTICOES_DE_TESTE: frozenset[str] = BLOCKS_TESTE


def _paths(root: Path) -> tuple[Path, Path]:
    output_dir = Path(root).resolve() / "data" / "analytical"
    return output_dir / DATASET_NAME, output_dir / MANIFEST_NAME


def _normalizar_kind(kind: Any) -> str:
    return str(kind or "").strip().lower()


def _validar_particoes_completas(observed: set[str]) -> None:
    """Exige que ``observed`` seja exatamente um dos esquemas completos de blocos."""
    observed_fs = frozenset(observed)
    if observed_fs in _ESQUEMAS_COMPLETOS:
        return
    esperados = "; ".join(str(sorted(esquema)) for esquema in sorted(_ESQUEMAS_COMPLETOS, key=len))
    raise ValueError(
        f"Partições incompletas. Observado: {sorted(observed_fs)}. "
        f"Esquemas completos válidos: {esperados}."
    )


def _particoes_por_papel() -> dict[str, tuple[str, ...]]:
    """Mapeia o papel agregado (treino/validacao/teste) para os blocos do artefato."""
    return {
        "treino": (_BLOCK_TRAIN_REF,),
        "validacao": (_BLOCK_VAL_REF,),
        "teste": (_BLOCK_TEST_REF, _BLOCK_TEST_PANDEMIC),
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
    """Resolve o par (numéricas, categóricas)."""
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


def validate_supervised_frame(
    frame: pd.DataFrame,
    *,
    feature_columns: Sequence[str],
    target_column: str,
    partition_column: str,
    audit_columns: Sequence[str] | None = None,
    required_partitions: Sequence[str] | None = None,
) -> None:
    """Valida schema mínimo, alvo binário e partições do dataset."""
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
    """Validação mínima quando ``columns=`` restringe a leitura."""
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
    schema = "blocos"
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
    """Colunas físicas guardadas para auditoria e análises de sensibilidade."""
    features_cfg = artefato_cfg["features_cfg"]
    feature_columns = set(artefato_cfg["feature_columns"])
    candidatas = [
        "fator_risc",
        *(features_cfg.get("contexto_incremental") or []),
        *(features_cfg.get("sensibilidade_gravidade_admissao") or []),
        *(features_cfg.get("sensibilidade_marcador_periodo") or []),
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
    """Separa grupos que não podem receber uma única partição-mestre."""
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
    codigos_grupo, _ = pd.factorize(frame[group_column])
    codigos = {
        "grupo": codigos_grupo,
        "periodo": pd.factorize(periodo)[0],
        "ano": pd.factorize(
            pd.to_numeric(frame[year_column], errors="coerce")
        )[0],
        "alvo": pd.factorize(
            pd.to_numeric(frame[target_column], errors="coerce")
        )[0],
    }
    del periodo
    if region_column:
        codigos["regiao"] = pd.factorize(
            frame[region_column].astype("string").fillna("AUSENTE")
        )[0]
    estrato = pd.DataFrame(
        {nome: valores.astype("int32") for nome, valores in codigos.items()}
    )
    estratos_por_grupo = estrato.drop_duplicates().groupby("grupo").size()
    del estrato, codigos
    grupos_incompativeis = estratos_por_grupo.index[
        estratos_por_grupo.to_numpy() > 1
    ]
    if len(grupos_incompativeis) == 0:
        return frame, frame.iloc[0:0]
    mascara = pd.Series(codigos_grupo, index=frame.index).isin(
        grupos_incompativeis
    )
    return frame.loc[~mascara], frame.loc[mascara]


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
    """Gera e persiste o artefato supervisionado canônico."""
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
    rows_loaded = int(len(frame))
    rows_quarantined = int(len(quarentena))
    groups_quarantined = (
        int(quarentena["group_id"].nunique()) if not quarentena.empty else 0
    )
    del frame, quarentena
    gc.collect()
    particionado, manifesto_particao = criar_particao_mestra(
        frame_modelavel,
        temporal_cfg=dict(temporal_cfg),
        group_column="group_id",
        year_column="ano_internacao",
        target_column=target_column,
        region_column="regiao_residencia",
        partition_column=partition_column,
    )
    del frame_modelavel
    gc.collect()
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
        if coluna in particionado.columns
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
    mascara_modelavel = particionado[partition_column].astype(str) != "exploracao"
    modelavel = particionado.loc[mascara_modelavel, output_columns]
    rows_partitioned = int(len(particionado))
    particao_mestre = None
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
        particao_mestre = particionado[partition_columns].copy()
        particao_mestre["bloco_mestre"] = (
            particao_mestre[partition_column].astype("string")
        )
    del particionado, mascara_modelavel
    gc.collect()
    rows_modelable = int(len(modelavel))
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
    del alvo_modelavel, blocos_modelaveis
    analytical_dir = root / "data" / "analytical"
    partition_path = analytical_dir / "partitions_master.parquet"
    partition_manifest_path = analytical_dir / "manifesto_particao.json"
    if exportar_particao and not overwrite and (
        partition_path.exists() or partition_manifest_path.exists()
    ):
        raise FileExistsError(
            "Partição-mestre já existe. Use overwrite=True somente "
            "em reconstrução deliberada."
        )
    dataset_path, manifest_path = persist_supervised_artifact(
        modelavel,
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
    del modelavel
    gc.collect()
    if exportar_particao and particao_mestre is not None:
        particao_mestre.to_parquet(
            partition_path,
            index=False,
        )
        del particao_mestre
        gc.collect()
        manifesto_particao = {
            **manifesto_particao,
            "source": source.to_dict(),
            "rows_before_quarantine": rows_loaded,
            "rows_quarantined": rows_quarantined,
            "groups_quarantined": groups_quarantined,
            "rows_partitioned": rows_partitioned,
            "rows_modelable": rows_modelable,
            "partition_path": str(partition_path),
            "partition_sha256": sha256_file(partition_path),
            "configuration_sha256": C.supervised_yaml_sha256(),
        }
        _escrever_json(partition_manifest_path, manifesto_particao)
    rows_exploracao = rows_partitioned - rows_modelable
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
    """Carrega o artefato canônico e valida hash, tipo de coorte e schema."""
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
        else BLOCKS_PADRAO_LEITURA
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


def split_partitions(
    frame: pd.DataFrame,
    manifest: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devolve ``(treino, validacao)`` agregando os blocos correspondentes."""
    col = manifest["partition_column"]
    papeis = _particoes_por_papel()

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
    """Devolve o bloco de teste."""
    exigir_gate("G9_holdout")

    col = manifest["partition_column"]
    papeis = _particoes_por_papel()
    teste = _filtrar_particoes(frame, col, papeis["teste"])

    if teste.empty:
        raise ValueError(
            "Bloco de teste ausente no DataFrame. Carregue o artefato "
            "incluindo test_ref/test_pandemic."
        )
    return teste
