"""Hashing de arquivos para verificação de integridade.

Centraliza ``sha256_file``, usado tanto pela resolução de coorte
(``src/data/cohort_source.py``) quanto pela persistência do artefato
supervisionado (``src/data/supervised_artifact.py``).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

__all__ = ["sha256_file"]

_DEFAULT_CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path, chunk_size: int = _DEFAULT_CHUNK_SIZE) -> str:
    """Calcula SHA-256 de um arquivo sem carregá-lo integralmente em memória.

    Lê em blocos de ``chunk_size`` bytes (default 1 MiB), permitindo
    hashear arquivos grandes com memória constante.
    """
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()