"""Publica a coorte definitiva após validar os gates anteriores."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


@dataclass(frozen=True)
class CohortPublicationResult:
    """Resultado consolidado da publicação da coorte."""

    published_path: Path
    publication_manifest_path: Path
    candidate_sha256: str
    published_sha256: str
    rows: int
    columns: int
    row_groups: int


def sha256_file(
    path: Path,
    chunk_size: int = 1024 * 1024,
) -> str:
    """Calcula o SHA-256 em blocos."""

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


def _read_json(
    path: Path,
) -> dict[str, Any]:
    """Lê um manifesto JSON e exige um objeto na raiz."""

    document = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(document, dict):
        raise ValueError(
            "O JSON precisa conter um objeto: "
            f"{path}"
        )

    return document


def _require_files(
    paths: tuple[Path, ...],
) -> None:
    """Exige que todos os arquivos de entrada existam."""

    missing = [
        path
        for path in paths
        if not path.is_file()
    ]

    if missing:
        formatted = "\n".join(
            f"- {path}"
            for path in missing
        )

        raise FileNotFoundError(
            "Arquivos obrigatórios ausentes:\n"
            f"{formatted}"
        )


def validate_publication_gates(
    candidate_path: Path,
    candidate_manifest_path: Path,
    candidate_validation_path: Path,
    parity_manifest_path: Path,
    transition_manifest_path: Path,
) -> dict[str, Any]:
    """Consolida e valida as evidências exigidas para publicação."""

    _require_files(
        (
            candidate_path,
            candidate_manifest_path,
            candidate_validation_path,
            parity_manifest_path,
            transition_manifest_path,
        )
    )

    candidate_manifest = _read_json(
        candidate_manifest_path
    )

    candidate_validation = _read_json(
        candidate_validation_path
    )

    parity_manifest = _read_json(
        parity_manifest_path
    )

    transition_manifest = _read_json(
        transition_manifest_path
    )

    candidate_sha256 = sha256_file(
        candidate_path
    )

    registered_hashes = {
        "candidate_manifest": (
            candidate_manifest[
                "candidate"
            ]["sha256"]
        ),
        "candidate_validation": (
            candidate_validation[
                "candidate_sha256"
            ]
        ),
        "parity_manifest": (
            parity_manifest[
                "candidate"
            ]["sha256"]
        ),
        "transition_manifest": (
            transition_manifest[
                "candidate"
            ]["sha256"]
        ),
    }

    divergent_hashes = {
        name: value
        for name, value
        in registered_hashes.items()
        if value != candidate_sha256
    }

    if divergent_hashes:
        raise ValueError(
            "O SHA-256 da candidata diverge dos "
            "artefatos de controle: "
            f"{divergent_hashes}."
        )

    checks = candidate_validation[
        "checks"
    ]

    population_reconciliation = (
        candidate_validation[
            "population_reconciliation"
        ]
    )

    approved_rule_violations = checks[
        "approved_rule_violations"
    ]

    parity_totals = parity_manifest[
        "totals"
    ]

    transition_population = (
        transition_manifest[
            "population"
        ]
    )

    failures: list[str] = []

    if (
        candidate_validation.get("status")
        != "approved_for_comparison"
    ):
        failures.append(
            "status da candidata não aprovado "
            "para comparação"
        )

    if not population_reconciliation.get(
        "closed",
        False,
    ):
        failures.append(
            "reconciliação populacional da "
            "candidata não fechada"
        )

    if checks.get(
        "id_registro_missing"
    ) != 0:
        failures.append(
            "id_registro ausente na candidata"
        )

    if (
        checks.get("id_registro_distinct")
        != checks.get("physical_rows")
    ):
        failures.append(
            "id_registro não é único na candidata"
        )

    if checks.get(
        "target_missing"
    ) != 0:
        failures.append(
            "alvo ausente na candidata"
        )

    if checks.get(
        "target_values"
    ) != [0, 1]:
        failures.append(
            "alvo da candidata não está "
            "limitado a [0, 1]"
        )

    if any(
        int(value) != 0
        for value
        in approved_rule_violations.values()
    ):
        failures.append(
            "há violações populacionais "
            "sobreviventes"
        )

    if (
        parity_manifest.get(
            "population_parity_status"
        )
        != "explained"
    ):
        failures.append(
            "paridade populacional não explicada"
        )

    if (
        parity_manifest.get(
            "target_parity_status"
        )
        != "passed"
    ):
        failures.append(
            "paridade do alvo não aprovada"
        )

    if not parity_manifest.get(
        "publication_gate_passed",
        False,
    ):
        failures.append(
            "gate da paridade não aprovado"
        )

    if parity_totals.get(
        "only_legacy_unexplained"
    ) != 0:
        failures.append(
            "há registros legados "
            "sem explicação"
        )

    if parity_totals.get(
        "only_candidate_unexplained"
    ) != 0:
        failures.append(
            "há registros da candidata "
            "sem explicação"
        )

    if parity_totals.get(
        "target_mismatches"
    ) != 0:
        failures.append(
            "há divergências de alvo "
            "na paridade"
        )

    if (
        transition_manifest.get(
            "transition_status"
        )
        != "explained"
    ):
        failures.append(
            "transição da coorte provisória "
            "não explicada"
        )

    if not transition_manifest.get(
        "transition_gate_passed",
        False,
    ):
        failures.append(
            "gate de transição não aprovado"
        )

    if transition_population.get(
        "only_candidate_rows"
    ) != 0:
        failures.append(
            "a candidata introduziu registros "
            "na transição"
        )

    if transition_population.get(
        "target_mismatches"
    ) != 0:
        failures.append(
            "há divergências de alvo "
            "na transição"
        )

    if (
        transition_manifest.get(
            "annual_removed_rows"
        )
        != transition_population.get(
            "only_provisional_rows"
        )
    ):
        failures.append(
            "o fechamento anual da transição "
            "diverge da reconciliação populacional"
        )

    guarantees = (
        candidate_manifest.get(
            "execution_guarantees",
            {},
        ),
        parity_manifest.get(
            "execution_guarantees",
            {},
        ),
        transition_manifest.get(
            "execution_guarantees",
            {},
        ),
    )

    if any(
        item.get("test_consulted")
        is not False
        for item in guarantees
    ):
        failures.append(
            "um artefato não confirma "
            "que o teste permaneceu fechado"
        )

    if any(
        item.get("partitions_created")
        is not False
        for item in guarantees
    ):
        failures.append(
            "um artefato não confirma "
            "a ausência de partições"
        )

    if failures:
        formatted = "\n".join(
            f"- {failure}"
            for failure in failures
        )

        raise ValueError(
            "Gates de publicação não aprovados:\n"
            f"{formatted}"
        )

    parquet_file = pq.ParquetFile(
        candidate_path
    )

    if (
        parquet_file.metadata.num_rows
        != checks["physical_rows"]
    ):
        raise ValueError(
            "A contagem física da candidata "
            "diverge da validação."
        )

    if (
        parquet_file.metadata.num_columns
        != checks["physical_columns"]
    ):
        raise ValueError(
            "O número de colunas da candidata "
            "diverge da validação."
        )

    if (
        parquet_file.num_row_groups
        != checks["row_groups"]
    ):
        raise ValueError(
            "Os row groups da candidata "
            "divergem da validação."
        )

    return {
        "candidate_sha256": (
            candidate_sha256
        ),
        "rows": int(
            parquet_file.metadata.num_rows
        ),
        "columns": int(
            parquet_file.metadata.num_columns
        ),
        "row_groups": int(
            parquet_file.num_row_groups
        ),
        "schema": (
            parquet_file.schema_arrow
        ),
        "candidate_manifest": (
            candidate_manifest
        ),
        "candidate_validation": (
            candidate_validation
        ),
        "parity_manifest": (
            parity_manifest
        ),
        "transition_manifest": (
            transition_manifest
        ),
    }


def _validate_published_copy(
    published_path: Path,
    expected_sha256: str,
    expected_rows: int,
    expected_columns: int,
    expected_schema: pa.Schema,
) -> tuple[str, int]:
    """Valida a cópia antes e depois da promoção."""

    observed_sha256 = sha256_file(
        published_path
    )

    if observed_sha256 != expected_sha256:
        raise ValueError(
            "O SHA-256 da cópia publicada "
            "diverge da candidata."
        )

    parquet_file = pq.ParquetFile(
        published_path
    )

    if (
        parquet_file.metadata.num_rows
        != expected_rows
    ):
        raise ValueError(
            "A cópia publicada possui contagem "
            "de linhas divergente."
        )

    if (
        parquet_file.metadata.num_columns
        != expected_columns
    ):
        raise ValueError(
            "A cópia publicada possui número "
            "de colunas divergente."
        )

    if not parquet_file.schema_arrow.equals(
        expected_schema
    ):
        raise ValueError(
            "O schema da cópia publicada "
            "diverge da candidata."
        )

    table = pq.read_table(
        published_path,
        columns=[
            "id_registro",
            "alvo_obito_srag",
        ],
    )

    if table[
        "id_registro"
    ].null_count:
        raise ValueError(
            "A cópia publicada contém "
            "id_registro ausente."
        )

    distinct_ids = int(
        pc.count_distinct(
            table["id_registro"]
        ).as_py()
    )

    if distinct_ids != expected_rows:
        raise ValueError(
            "A cópia publicada contém "
            "id_registro duplicado."
        )

    if table[
        "alvo_obito_srag"
    ].null_count:
        raise ValueError(
            "A cópia publicada contém "
            "alvo ausente."
        )

    target_values = set(
        table[
            "alvo_obito_srag"
        ].to_pylist()
    )

    if target_values != {0, 1}:
        raise ValueError(
            "A cópia publicada contém "
            "alvo fora de {0, 1}."
        )

    return (
        observed_sha256,
        distinct_ids,
    )


def publish_final_cohort(
    candidate_path: Path,
    published_path: Path,
    candidate_manifest_path: Path,
    candidate_validation_path: Path,
    parity_manifest_path: Path,
    transition_manifest_path: Path,
    publication_manifest_path: Path,
    overwrite: bool = False,
) -> CohortPublicationResult:
    """Publica a candidata por cópia e promoção atômica."""

    evidence = validate_publication_gates(
        candidate_path=candidate_path,
        candidate_manifest_path=(
            candidate_manifest_path
        ),
        candidate_validation_path=(
            candidate_validation_path
        ),
        parity_manifest_path=(
            parity_manifest_path
        ),
        transition_manifest_path=(
            transition_manifest_path
        ),
    )

    temporary_path = (
        published_path.with_suffix(
            published_path.suffix + ".tmp"
        )
    )

    publication_manifest_temp = (
        publication_manifest_path.with_suffix(
            publication_manifest_path.suffix
            + ".tmp"
        )
    )

    validation_temp = (
        candidate_validation_path.with_suffix(
            candidate_validation_path.suffix
            + ".tmp"
        )
    )

    temporary_paths = (
        temporary_path,
        publication_manifest_temp,
        validation_temp,
    )

    abandoned = [
        path
        for path in temporary_paths
        if path.exists()
    ]

    if abandoned:
        formatted = "\n".join(
            f"- {path}"
            for path in abandoned
        )

        raise FileExistsError(
            "Existem arquivos temporários "
            "de publicação:\n"
            f"{formatted}\n"
            "Revise e remova-os antes "
            "de continuar."
        )

    existing = [
        path
        for path in (
            published_path,
            publication_manifest_path,
        )
        if path.exists()
    ]

    if existing and not overwrite:
        formatted = "\n".join(
            f"- {path}"
            for path in existing
        )

        raise FileExistsError(
            "Já existem artefatos publicados:\n"
            f"{formatted}\n"
            "Use overwrite somente após revisar "
            "a publicação anterior."
        )

    if overwrite:
        raise ValueError(
            "A sobrescrita de uma coorte publicada "
            "não é permitida neste incremento. "
            "Versione ou remova explicitamente "
            "a publicação anterior após revisão."
        )

    published_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    publication_manifest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    candidate_validation_before = (
        candidate_validation_path.read_text(
            encoding="utf-8"
        )
    )

    published_promoted = False
    manifest_promoted = False

    try:
        shutil.copyfile(
            candidate_path,
            temporary_path,
        )

        (
            temporary_sha256,
            distinct_ids,
        ) = _validate_published_copy(
            published_path=temporary_path,
            expected_sha256=evidence[
                "candidate_sha256"
            ],
            expected_rows=evidence["rows"],
            expected_columns=evidence[
                "columns"
            ],
            expected_schema=evidence[
                "schema"
            ],
        )

        generated_at = datetime.now(
            timezone.utc
        ).isoformat()

        publication_manifest = {
            "schema_version": 1,
            "generated_at_utc": generated_at,
            "status": "published",
            "candidate": {
                "path": str(
                    candidate_path
                ),
                "sha256": evidence[
                    "candidate_sha256"
                ],
            },
            "published": {
                "path": str(
                    published_path
                ),
                "sha256": (
                    temporary_sha256
                ),
                "rows": evidence["rows"],
                "columns": evidence[
                    "columns"
                ],
                "row_groups": evidence[
                    "row_groups"
                ],
                "id_registro_distinct": (
                    distinct_ids
                ),
                "target_values": [0, 1],
            },
            "evidence": {
                "candidate_manifest_path": str(
                    candidate_manifest_path
                ),
                "candidate_manifest_sha256": (
                    sha256_file(
                        candidate_manifest_path
                    )
                ),
                "candidate_validation_path": str(
                    candidate_validation_path
                ),
                "candidate_validation_sha256": (
                    sha256_file(
                        candidate_validation_path
                    )
                ),
                "parity_manifest_path": str(
                    parity_manifest_path
                ),
                "parity_manifest_sha256": (
                    sha256_file(
                        parity_manifest_path
                    )
                ),
                "transition_manifest_path": str(
                    transition_manifest_path
                ),
                "transition_manifest_sha256": (
                    sha256_file(
                        transition_manifest_path
                    )
                ),
            },
            "publication_performed": True,
            "legacy_parity_reviewed": True,
            "provisional_comparison_reviewed": True,
            "execution_guarantees": {
                "candidate_modified": False,
                "partitions_created": False,
                "test_consulted": False,
            },
        }

        consolidated_validation = dict(
            evidence[
                "candidate_validation"
            ]
        )

        consolidated_validation.update(
            {
                "generated_at_utc": (
                    generated_at
                ),
                "status": "published",
                "publication_performed": True,
                "legacy_parity_reviewed": True,
                "provisional_comparison_reviewed": True,
                "published_path": str(
                    published_path
                ),
                "published_sha256": (
                    temporary_sha256
                ),
                "publication_manifest_path": str(
                    publication_manifest_path
                ),
            }
        )

        publication_manifest_temp.write_text(
            json.dumps(
                publication_manifest,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        validation_temp.write_text(
            json.dumps(
                consolidated_validation,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        os.replace(
            temporary_path,
            published_path,
        )
        published_promoted = True

        os.replace(
            publication_manifest_temp,
            publication_manifest_path,
        )
        manifest_promoted = True

        os.replace(
            validation_temp,
            candidate_validation_path,
        )

        (
            published_sha256,
            _,
        ) = _validate_published_copy(
            published_path=published_path,
            expected_sha256=evidence[
                "candidate_sha256"
            ],
            expected_rows=evidence["rows"],
            expected_columns=evidence[
                "columns"
            ],
            expected_schema=evidence[
                "schema"
            ],
        )

        return CohortPublicationResult(
            published_path=published_path,
            publication_manifest_path=(
                publication_manifest_path
            ),
            candidate_sha256=evidence[
                "candidate_sha256"
            ],
            published_sha256=(
                published_sha256
            ),
            rows=evidence["rows"],
            columns=evidence["columns"],
            row_groups=evidence[
                "row_groups"
            ],
        )

    except Exception:
        for path in temporary_paths:
            if path.exists():
                path.unlink()

        if manifest_promoted:
            publication_manifest_path.unlink(
                missing_ok=True
            )

        if published_promoted:
            published_path.unlink(
                missing_ok=True
            )

        candidate_validation_path.write_text(
            candidate_validation_before,
            encoding="utf-8",
        )

        raise