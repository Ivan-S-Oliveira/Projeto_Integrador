#!/usr/bin/env python3
r"""Generate a complete, AI-oriented diagnostic snapshot of the SRAG repository.

Run from anywhere inside the repository, preferably with the project venv
(so installed package versions are the real ones):

    .\.venv\Scripts\python.exe tools\update_project_reference.py
    .\.venv\Scripts\python.exe tools\update_project_reference.py --split-mb 4
    .\.venv\Scripts\python.exe tools\update_project_reference.py --run-tests --pytest-args "-m 'not slow'"

Creates (default):

    docs/PROJECT_COMPLETE_REFERENCE.md          full human/AI-readable snapshot
    docs/PROJECT_COMPLETE_REFERENCE.json        machine-readable summary
    docs/project_reference_parts/00_INDEX.md    entry point: usage rules and the
                                                part where each section and file is
    docs/project_reference_parts/part_*.md      the same Markdown split into parts
                                                (default 1 MB each; --no-split to disable)

What the snapshot contains
--------------------------
1.  Git state: branch, commit, remote, status, recent log, diff stat and the
    optional uncommitted diff, disabled by default for speed.
2.  Full path inventory of the working folder, including ignored and local
    folders (data/, outputs/, models/, reports/), with size, modification time
    and Git state. File contents of data are never copied.
3.  Full, untruncated source of every relevant text file: .py, .ipynb, .md,
    .yaml, .yml, .toml, .json, .csv (capped), .txt, .ini, .cfg, .ps1, .sh, .sql.
    Lines are numbered so they can be cited as `path:line`.
4.  Notebooks: every cell source (numbered, citable as `path#cell-N:line`),
    execution counts and, by default, the text outputs (streams, text/plain
    results, errors and tracebacks). Images and HTML are replaced by
    placeholders. Execution order problems are reported.
5.  Optional small text artifacts produced by the project (manifests,
    waterfalls, summary tables), capped by size and number of CSV rows.
    Prediction folders are never included.
6.  Text extracted from .docx and .pptx documents (plans, reports).
7.  Python environment: interpreter, platform and every installed package.
8.  Parsed configuration: YAML summary, gates table, duplicate YAML keys,
    pyproject.toml validity and dependency lists.
9.  Static API catalog: every module, function, class, method, signature,
    docstring, consumers and tests. Consumers and tests are resolved through
    imports, aliases, relative imports and package re-exports.
10. Static diagnostics ("attention report"), including:
    - internal imports of modules or names that do not exist;
    - calls to project functions with keyword arguments they do not accept
      or with too many positional arguments;
    - gate names used in code/docs that are absent from the YAML;
    - YAML keys never referenced by code (possible dead configuration);
    - feature contract problems (forbidden features, derived features);
    - third-party imports missing from requirements.txt/pyproject.toml and
      unpinned dependencies;
    - duplicated symbols, notebook functions duplicating src/ and files with
      identical content;
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


SCHEMA_VERSION = 7
OUTPUT_DIR = Path("docs")
OUTPUT_MD_NAME = "PROJECT_COMPLETE_REFERENCE.md"
OUTPUT_JSON_NAME = "PROJECT_COMPLETE_REFERENCE.json"
PARTS_DIR_NAME = "project_reference_parts"
INDEX_NAME = "00_INDEX.md"
GENERATOR_PATH = "tools/update_project_reference.py"

DEFAULT_MAX_INLINE_BYTES = 4_000_000
DEFAULT_MAX_OUTPUT_CHARS = 6_000
DEFAULT_MAX_ARTIFACT_BYTES = 300_000
DEFAULT_MAX_CSV_ROWS = 60
DEFAULT_MAX_DIFF_CHARS = 400_000
DEFAULT_GIT_LOG = 10
DEFAULT_SPLIT_MB = 1.0
MAX_INVENTORY_ENTRIES = 30_000
MAX_DOCSTRING_CHARS = 4_000
MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL = 200
BINARY_PROBE_BYTES = 8192

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
# Files whose existence and keys are reported, but whose values are hidden.
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

QUOTE = "(?:'|\")"
ENV_RE = re.compile(
    r"(?:os\.getenv|os\.environ\.get|os\.environ\[|get_env|get_secret|getenv)"
    r"\(?\s*" + QUOTE + r"([A-Za-z_][A-Za-z0-9_]*)" + QUOTE
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
WINDOWS_USER_RE = re.compile(r"(?i)\b[A-Z]\:[\\/]+Users[\\/]+[^\\/\s\"'<>|]+")
POSIX_HOME_RE = re.compile(r"(?<![A-Za-z0-9_])/(?:home|Users)/[^/\s\"'<>|]+")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
BACKTICK_RUN_RE = re.compile(r"`+")
FENCE_RE = re.compile(r"^(`{3,})")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
FILE_LITERAL_RE = re.compile(
    QUOTE
    + r"([^'\"\n]+\.(?:parquet|csv|json|yaml|yml|joblib|pkl|png|jpg|md|html|txt))"
    + QUOTE,
    re.IGNORECASE,
)
GATE_RE = re.compile(r"\bG\d+_[A-Za-z0-9_]+\b")
TODO_RE = re.compile(r"(?i)\b(TODO|FIXME|XXX|HACK|PENDENTE)\b[:\s-]*(.{0,140})")
MOJIBAKE_RE = re.compile(r"(?:├|┤|Ã[\u0080-\u00BF¡-¿]|Â[\u00A0-\u00BF ]|â€|\uFFFD)")
DOC_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])((?:src|tests|notebooks|configs|tools|docs|data|outputs)/"
    r"[A-Za-z0-9_./-]+\.(?:py|ipynb|yaml|yml|md|csv|json|parquet|toml))"
)

CONTEXT = """# Project Complete Reference

> **Generated file. Do not edit manually.**
> Generated by `tools/update_project_reference.py` (schema v{schema}).
> Static snapshot of the repository and of the local working folder.

## 1. Purpose

This reference lets a person or an AI continue the SRAG project without prior
conversation context and without access to the machine. It prioritizes the full,
untruncated source of Python files, notebooks, tests, configuration and project
documentation, plus fast structural diagnostics that prevent duplicated functions,
conflicting pipelines and patchwork implementations.

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

0. When the reference is split, start with `docs/project_reference_parts/00_INDEX.md`:
   it lists the part where each section and each file is.
1. Read Sections 6 (executive map) and 7 (attention report).
2. Check Section 8 (configuration and gates) and Section 9 (environment).
3. Search Section 12 (API catalog) before proposing any new function. If an
   equivalent function exists, reuse or extend it; never create a parallel one.
4. Check Sections 13 to 15 for imports, tests and notebook orchestration.
5. Read the exact implementation in Section 17 (full source). Lines are
   numbered: cite files as `path:line` and notebook cells as
   `path#cell-N:line` (line counted inside the cell). The numbers are not
   part of the files.
6. Use Section 18 (artifacts) and notebook outputs as evidence of what was
   actually executed; use Section 10 (inventory) to know what exists locally.
7. If code, configuration, tests, notebooks and plans disagree, report the
   conflict explicitly; never choose silently.
8. "Consumed by" and "Tested by" are resolved statically through imports,
   aliases, relative imports and package re-exports. Dynamic access
   (getattr, importlib, strings) is not detected.

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
    keywords: list
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
    end_lineno: Any
    docstring: str
    decorators: list = field(default_factory=list)
    calls: list = field(default_factory=list)
    env_vars: list = field(default_factory=list)
    file_literals: list = field(default_factory=list)
    is_private: bool = False
    params: list = field(default_factory=list)
    n_positional_params: int = 0
    has_varargs: bool = False
    has_varkw: bool = False
    defaults: dict = field(default_factory=dict)


@dataclass
class PythonFileAnalysis:
    path: str
    module: str
    docstring: str
    parse_error: Any
    imports: list
    internal_imports: list
    external_imports: list
    import_from: list
    calls: list
    call_sites: list
    symbols: list
    top_level_names: list
    constants: dict
    env_vars: list
    file_literals: list
    has_star_import: bool = False
    lines: int = 0
    module_aliases: dict = field(default_factory=dict)
    references: list = field(default_factory=list)


@dataclass
class NotebookAnalysis:
    path: str
    cells: int
    code_cells: int
    markdown_cells: int
    kernel: dict
    language_version: str
    headings: list
    imports: list
    internal_imports: list
    import_from: list
    functions: list
    classes: list
    assignments: list
    file_literals: list
    env_vars: list
    parse_errors: list
    call_sites: list
    code_lines: int
    executed_cells: int
    execution_counts: list
    out_of_order: bool
    error_outputs: list
    outputs_included: bool
    module_aliases: dict = field(default_factory=dict)
    references: list = field(default_factory=list)


@dataclass
class Attention:
    severity: str
    category: str
    message: str
    evidence: list = field(default_factory=list)
    recommendation: str = ""


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def run_command(args, *, cwd, check=True, timeout=None):
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
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(message or "Command failed: " + " ".join(args))
    return result


def git(root, *args, check=True):
    command = ["git", "-c", "core.quotepath=false"] + list(args)
    return run_command(command, cwd=root, check=check).stdout


def root_dir():
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode:
        raise RuntimeError("Run inside the Git repository.")
    return Path(result.stdout.strip()).resolve()


def module_name(path):
    parts = list(path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def human_bytes(value):
    size = float(value)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            if unit == "B":
                return f"{size:.0f} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"


def looks_binary(data):
    head = data[:BINARY_PROBE_BYTES]
    return b"\x00" in head


class Redactor:
    """Removes secrets and replaces absolute local paths."""

    def __init__(self, root):
        variants = {str(root), root.as_posix(), str(root).replace("\\", "\\\\")}
        self.root_variants = sorted((v for v in variants if v), key=len, reverse=True)
        home = Path.home()
        home_variants = {str(home), home.as_posix(), str(home).replace("\\", "\\\\")}
        self.home_variants = sorted(home_variants, key=len, reverse=True)

    def replace_paths(self, text):
        for value in self.root_variants:
            text = text.replace(value, "<REPO>")
        for value in self.home_variants:
            text = text.replace(value, "<HOME>")
        text = WINDOWS_USER_RE.sub("<HOME>", text)
        return POSIX_HOME_RE.sub("<HOME>", text)

    def __call__(self, text):
        warnings = []
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
        return self.replace_paths(text), warnings


def fence_for(text):
    longest = max((len(m.group(0)) for m in BACKTICK_RUN_RE.finditer(text)), default=0)
    return "`" * max(3, longest + 1)


def code_block(text, lexer="text"):
    fence = fence_for(text)
    return f"{fence}{lexer}\n{text}\n{fence}"


def number_lines(text):
    """Prefix each line with its 1-based number, for path:line citations."""
    lines = text.splitlines()
    if not lines:
        return text
    width = len(str(len(lines)))
    numbered = (f"{index:>{width}} | {line}" for index, line in enumerate(lines, 1))
    return "\n".join(numbered)


def truncate(text, limit, label="characters"):
    if limit <= 0 or len(text) <= limit:
        return text
    head = text[: int(limit * 0.7)]
    tail = text[-int(limit * 0.3):]
    omitted = len(text) - len(head) - len(tail)
    return f"{head}\n... [{omitted} {label} omitted] ...\n{tail}"


def safe_unparse(node, default=""):
    if node is None:
        return default
    try:
        return ast.unparse(node)
    except Exception:
        return default or "..."


def literal_preview(node, max_chars=300):
    try:
        text = repr(ast.literal_eval(node))
    except Exception:
        text = safe_unparse(node, "<dynamic>")
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def dotted_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return dotted_name(node.func)
    return None


def env_names(text):
    return sorted(set(ENV_RE.findall(text)))


def file_literals(text):
    return sorted({m.group(1) for m in FILE_LITERAL_RE.finditer(text)})


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    if path.exists() and path.read_bytes() == data:
        return
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=path.parent) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    temporary.replace(path)


def iter_lines_with_fence_state(text):
    """Yield (line, inside_fence) for every line, keeping line endings."""
    in_fence = None
    for line in text.splitlines(keepends=True):
        fence = FENCE_RE.match(line)
        if fence:
            if in_fence is None:
                in_fence = fence.group(1)
                yield line, True
                continue
            if line.strip() == in_fence:
                in_fence = None
                yield line, True
                continue
        yield line, in_fence is not None


# ---------------------------------------------------------------------------
# Git and filesystem inventory
# ---------------------------------------------------------------------------

def parse_porcelain_status(root):
    raw = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    items = raw.split("\0")
    status = {}
    i = 0
    while i < len(items):
        item = items[i]
        if not item:
            i += 1
            continue
        code = item[:2]
        path_text = item[3:]
        status[path_text] = code
        if code[0] in {"R", "C"} and i + 1 < len(items):
            i += 2
        else:
            i += 1
    return status


def collect_git_entries(root):
    status_map = parse_porcelain_status(root)
    tracked = {line.strip() for line in git(root, "ls-files").splitlines() if line.strip()}
    others = git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    untracked = {line.strip() for line in others if line.strip()}
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


def walk_inventory(root, tracked, untracked):
    """All files in the working folder, except tooling/caches/venvs."""
    rows = []
    for current, dirs, files in os.walk(root):
        kept = sorted(d for d in dirs if d not in EXCLUDED_DIRS_ANYWHERE)
        dirs.clear()
        dirs.extend(kept)
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
            modified = datetime.fromtimestamp(stat.st_mtime, timezone.utc)
            rows.append(
                {
                    "path": rel,
                    "git": state,
                    "bytes": stat.st_size,
                    "modified_utc": modified.strftime("%Y-%m-%d %H:%M"),
                }
            )
            if len(rows) >= MAX_INVENTORY_ENTRIES:
                return rows, True
    return rows, False


def is_artifact_path(path):
    return bool(path.parts) and path.parts[0] in ARTIFACT_DIRS_AT_ROOT


def include_source(path, *, tracked):
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


def include_artifact(path, size, max_bytes):
    if not is_artifact_path(path):
        return False
    if any(part.lower() in ARTIFACT_EXCLUDED_DIR_NAMES for part in path.parts):
        return False
    if path.name.startswith(".env"):
        return False
    suffix = path.suffix.lower()
    if suffix not in ARTIFACT_TEXT_SUFFIXES:
        return False
    # Raw/large CSVs are only previewed (head), so allow them up to 50x.
    limit = max_bytes * 50 if suffix in {".csv", ".tsv"} else max_bytes
    return size <= limit


# ---------------------------------------------------------------------------
# Python AST analysis
# ---------------------------------------------------------------------------

def imported_names(tree):
    imports = set()
    froms = []
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
                {
                    "module": prefix,
                    "names": names,
                    "asnames": [alias.asname or alias.name for alias in node.names],
                    "lineno": getattr(node, "lineno", 0),
                }
            )
            for name in names:
                imports.add(f"{prefix}.{name}".strip("."))
    return sorted(imports), froms, star


def module_aliases(tree):
    """Local name -> module for `import a.b` and `import a.b as c`."""
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    aliases[alias.asname] = alias.name
                else:
                    top = alias.name.split(".")[0]
                    aliases.setdefault(top, top)
    return aliases


def referenced_names(tree):
    """Every name and dotted attribute read in the code."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            value = dotted_name(node)
            if value:
                names.add(value)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            names.add(node.id)
    return sorted(names)


def call_names(tree):
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = dotted_name(node.func)
            if name:
                found.add(name)
    return sorted(found)


def call_sites(tree, label):
    sites = []
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


def top_level_names(tree):
    names = set()
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


def assigned_constants(tree):
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id.isupper():
                constants[target.id] = literal_preview(node.value)
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id.isupper() and node.value:
                constants[target.id] = literal_preview(node.value)
    return constants


def function_signature(node):
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    returns = f" -> {safe_unparse(node.returns)}" if node.returns else ""
    return f"{prefix} {node.name}({safe_unparse(node.args, '...')}){returns}"


def extract_symbol(node, *, path, module, text, parent=""):
    qualname = f"{parent}.{node.name}" if parent else node.name
    params = []
    n_pos = 0
    has_varargs = has_varkw = False
    defaults = {}
    if isinstance(node, ast.ClassDef):
        bases = ", ".join(safe_unparse(b) for b in node.bases)
        signature = f"class {node.name}({bases})"
        kind = "class"
        # A class call uses __init__ (or dataclass fields): handled loosely.
        init = None
        for child in node.body:
            if isinstance(child, ast.FunctionDef) and child.name == "__init__":
                init = child
                break
        if init is not None:
            args = init.args
            positional = [a.arg for a in args.posonlyargs + args.args]
            positional = positional[1:]
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
        all_positional = args.posonlyargs + args.args
        with_default = all_positional[len(all_positional) - len(pos_defaults):]
        for arg, default in zip(with_default, pos_defaults):
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


def analyze_python(path, text, internal_roots):
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
    internal = sorted(
        v for v in imports if v.split(".")[0] in internal_roots or v.startswith(".")
    )
    external = sorted(set(imports) - set(internal))
    symbols = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(extract_symbol(node, path=path, module=module, text=text))
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        symbols.append(
                            extract_symbol(
                                child, path=path, module=module, text=text, parent=node.name
                            )
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
        module_aliases=module_aliases(tree),
        references=referenced_names(tree),
    )


# ---------------------------------------------------------------------------
# Notebooks
# ---------------------------------------------------------------------------

def strip_magics(source):
    """Comment out IPython magics/shell lines so the cell can be parsed."""
    lines = []
    for line in source.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("%", "!", "?")) or stripped.endswith("?"):
            lines.append("# " + line)
        else:
            lines.append(line)
    return "\n".join(lines)


def cell_source(cell):
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return str(source)


def render_output(output, max_chars, redactor):
    """Return (kind, text) for one notebook output."""
    kind = output.get("output_type", "unknown")
    if kind == "stream":
        text = "".join(output.get("text", ()))
        label = "stream:" + str(output.get("name", "stdout"))
    elif kind in {"execute_result", "display_data"}:
        data = output.get("data", {})
        omitted = sorted(mime for mime in data if mime != "text/plain")
        text = "".join(data.get("text/plain", ()))
        if omitted:
            note = "[non-text output omitted: " + ", ".join(omitted) + "]"
            text = text + "\n" + note if text else note
        label = kind
    elif kind == "error":
        trace = "\n".join(output.get("traceback", ()))
        text = f"{output.get('ename', '')}: {output.get('evalue', '')}\n{trace}"
        label = "error"
    else:
        text = json.dumps(output)
        text = text[:500]
        label = kind
    text = ANSI_RE.sub("", text)
    text, _ = redactor(text)
    return label, truncate(text.rstrip(), max_chars)


def analyze_notebook(path, data, internal_roots):
    nb = json.loads(data.decode("utf-8-sig"))
    headings = []
    imports = set()
    internal_imports = set()
    froms = []
    functions = []
    classes = []
    assignments = set()
    literals = set()
    envs = set()
    parse_errors = []
    sites = []
    errors = []
    counts = []
    aliases = {}
    references = set()
    code_lines = code_cells = markdown_cells = executed = 0
    for number, cell in enumerate(nb.get("cells", ()), 1):
        kind = cell.get("cell_type", "unknown")
        source = cell_source(cell)
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
        for output in cell.get("outputs", ()):
            if output.get("output_type") == "error":
                evalue = str(output.get("evalue", ""))
                errors.append(f"cell {number}: {output.get('ename', '')}: {evalue[:200]}")
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
            entry = dict(item)
            entry["cell"] = number
            froms.append(entry)
        aliases.update(module_aliases(tree))
        references.update(referenced_names(tree))
        sites.extend(call_sites(tree, label))
        nb_module = f"notebook:{path.as_posix()}"
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(extract_symbol(node, path=Path(label), module=nb_module, text=source))
            elif isinstance(node, ast.ClassDef):
                classes.append(extract_symbol(node, path=Path(label), module=nb_module, text=source))
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if not isinstance(target, ast.Name):
                        continue
                    lowered = target.id.lower()
                    if target.id.isupper() or lowered.endswith(("_dir", "_path", "_file")):
                        assignments.add(target.id)
        literals.update(file_literals(source))
        envs.update(env_names(source))
    numeric = [c for c in counts if c is not None]
    out_of_order = any(b < a for a, b in zip(numeric, numeric[1:]))
    meta = nb.get("metadata", {})
    analysis = NotebookAnalysis(
        path=path.as_posix(),
        cells=len(nb.get("cells", ())),
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
        module_aliases=aliases,
        references=sorted(references),
    )
    return analysis, nb


def notebook_source_markdown(nb, analysis, *, include_outputs, max_output_chars,
                             reduced, redactor, numbered):
    order_note = " — **executed out of order**" if analysis.out_of_order else ""
    outputs_note = "text outputs included" if include_outputs else "omitted"
    reduced_note = "; **reduced view** (notebook above size limit)" if reduced else ""
    parts = [
        f"- Cells: `{analysis.cells}` (`{analysis.code_cells}` code, `{analysis.markdown_cells}` markdown)",
        f"- Code cells executed: `{analysis.executed_cells}` of `{analysis.code_cells}`{order_note}",
        f"- Kernel: `{analysis.kernel.get('display_name', '')}`; Python `{analysis.language_version}`",
        f"- Outputs: `{outputs_note}`{reduced_note}",
        f"- Cite cells as `{analysis.path}#cell-N:line` (line counted inside the cell)",
        "",
    ]
    for number, cell in enumerate(nb.get("cells", ()), 1):
        kind = cell.get("cell_type", "unknown")
        source, _ = redactor(cell_source(cell).rstrip())
        if kind == "code" and reduced:
            lines = source.splitlines()
            if len(lines) > MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL:
                kept = lines[:MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL]
                hidden = len(lines) - MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL
                source = "\n".join(kept) + f"\n# ... {hidden} lines omitted ..."
        if numbered:
            source = number_lines(source)
        if kind == "code":
            count = cell.get("execution_count")
            shown_count = count if count is not None else " "
            parts.append(f"### Cell {number} [code] · In [{shown_count}]")
            parts.append("")
            parts.append(code_block(source, "python"))
            if include_outputs:
                for out_index, output in enumerate(cell.get("outputs", ()), 1):
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

def office_text(data, suffix):
    """Plain text of .docx/.pptx using only the standard library."""
    import io
    from xml.etree import ElementTree as ET

    texts = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        available = set(archive.namelist())
        if suffix == ".docx":
            names = ["word/document.xml"]
        else:
            slides = [n for n in available if re.match(r"ppt/slides/slide\d+\.xml$", n)]
            names = sorted(slides, key=lambda n: int(re.findall(r"\d+", n)[-1]))
        for index, name in enumerate(names, 1):
            if name not in available:
                continue
            root = ET.fromstring(archive.read(name))
            if suffix == ".pptx":
                texts.append(f"--- slide {index} ---")
            for paragraph in root.iter():
                if paragraph.tag.rsplit("}", 1)[-1] != "p":
                    continue
                pieces = []
                for node in paragraph.iter():
                    if node.tag.rsplit("}", 1)[-1] in {"t", "tab"}:
                        pieces.append(node.text or "")
                line = "".join(pieces).strip()
                if line:
                    texts.append(line)
    return "\n".join(texts)


def csv_preview(text, max_rows):
    lines = text.splitlines()
    total = max(0, len(lines) - 1)
    if len(lines) <= max_rows + 1:
        return text, total
    head = "\n".join(lines[: max_rows + 1])
    return head + f"\n... [{total - max_rows} more rows omitted]", total


def keys_only_json(text):
    try:
        data = json.loads(text)
    except Exception:
        return "[could not parse; values hidden]"

    def mask(value):
        if isinstance(value, dict):
            return {k: mask(v) for k, v in value.items()}
        if isinstance(value, list):
            return [mask(v) for v in value[:5]]
        return "<" + type(value).__name__ + ">"

    return json.dumps(mask(data), ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Configuration, environment and dependency files
# ---------------------------------------------------------------------------

def flatten_mapping(value, prefix=""):
    result = {}
    if isinstance(value, dict) and value:
        for key, child in value.items():
            new_prefix = f"{prefix}.{key}" if prefix else str(key)
            result.update(flatten_mapping(child, new_prefix))
    else:
        result[prefix] = value
    return result


def nested_get(mapping, *keys, default=None):
    current = mapping
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def load_yaml_strict(text):
    """Parse YAML; also report duplicated keys (safe_load silently keeps the last)."""
    if yaml is None:
        return None, "PyYAML not available", []
    duplicates = []

    class DupLoader(yaml.SafeLoader):  # type: ignore
        pass

    def construct_mapping(loader, node, deep=False):
        seen = set()
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


def parse_dependency_line(text):
    match = re.match(r"([A-Za-z0-9_.\-\[\]]+)\s*(.*)", text)
    if not match:
        return None, None
    name = re.sub(r"\[.*\]", "", match.group(1)).lower().replace("_", "-")
    return name, match.group(2).strip()


def parse_requirements(text):
    deps = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith(("-", "git+", "http")):
            continue
        name, spec = parse_dependency_line(line)
        if name:
            deps[name] = spec
    return deps


def parse_pyproject(text):
    if tomllib is None:
        return None, "tomllib unavailable (Python < 3.11)"
    try:
        return tomllib.loads(text), None
    except Exception as exc:
        return None, repr(exc)


def pyproject_dependencies(data):
    deps = {}
    values = list(nested_get(data, "project", "dependencies", default=()) or ())
    optional = nested_get(data, "project", "optional-dependencies", default={}) or {}
    for group in optional.values():
        values.extend(group or ())
    for item in values:
        name, spec = parse_dependency_line(str(item))
        if name:
            deps[name] = spec
    return deps


def installed_packages():
    packages = {}
    for dist in importlib_metadata.distributions():
        try:
            name = (dist.metadata["Name"] or "").lower().replace("_", "-")
        except Exception:
            continue
        if name:
            packages[name] = dist.version
    return dict(sorted(packages.items()))


def top_level_import_map():
    """Import name -> distribution, from installed metadata when available."""
    mapping = dict(IMPORT_TO_DIST)
    try:
        for top, dists in importlib_metadata.packages_distributions().items():
            if dists:
                mapping.setdefault(top, dists[0].lower().replace("_", "-"))
    except Exception:
        pass
    return mapping


def run_tests(root, extra, timeout):
    args = [sys.executable, "-m", "pytest", "-q", "-rfEs", "--no-header", "-p", "no:cacheprovider"]
    if extra:
        import shlex
        args += shlex.split(extra, posix=(os.name != "nt"))
    command = " ".join(args[1:])
    try:
        result = run_command(args, cwd=root, check=False, timeout=timeout)
        output = (result.stdout + "\n" + result.stderr).strip()
        return {"command": command, "returncode": result.returncode, "output": output}
    except subprocess.TimeoutExpired:
        return {"command": command, "returncode": None, "output": f"Timeout after {timeout}s"}
    except Exception as exc:
        return {"command": command, "returncode": None, "output": repr(exc)}


# ---------------------------------------------------------------------------
# Usage index (consumers and tests resolved through imports)
# ---------------------------------------------------------------------------

def resolve_relative(module, current, is_package):
    if not module.startswith("."):
        return module
    level = len(module) - len(module.lstrip("."))
    base = current.split(".")
    if not is_package:
        base = base[:-1]
    if level > 1:
        base = base[: len(base) - (level - 1)]
    rest = module.lstrip(".")
    return ".".join(base + [rest] if rest else base)


def is_test_path(path):
    return path.startswith("tests/") or Path(path).name.startswith("test_")


def index_usage(symbols, python_files, notebooks):
    """Map `module.qualname` to consuming files and to test files.

    A file uses `module.name` when it imports it (directly, with an alias, or
    through a package that re-exports it), or when it reads `alias.name` after
    `import module as alias`. Methods inherit the usage of their class.
    """
    modules = {f.module for f in python_files if f.module}
    known = set(modules)
    for name in modules:
        pieces = name.split(".")
        for size in range(1, len(pieces)):
            known.add(".".join(pieces[:size]))

    reexports = {}
    for f in python_files:
        is_pkg = f.path.endswith("__init__.py")
        for item in f.import_from:
            source = resolve_relative(item.get("module", ""), f.module, is_pkg)
            names = item.get("names", ())
            locals_ = item.get("asnames", names)
            for name, local in zip(names, locals_):
                if name != "*":
                    reexports[(f.module, local)] = (source, name)

    def origin(module, name):
        seen = set()
        current = (module, name)
        while current in reexports and current not in seen:
            seen.add(current)
            current = reexports[current]
        return current

    def used_by(froms, aliases, refs, current, is_pkg):
        used = set()
        local_modules = dict(aliases)
        for item in froms:
            raw = item.get("module", "")
            source = resolve_relative(raw, current, is_pkg) if current else raw
            names = item.get("names", ())
            locals_ = item.get("asnames", names)
            for name, local in zip(names, locals_):
                if name == "*":
                    continue
                full = f"{source}.{name}"
                if full in known:
                    local_modules[local] = full
                else:
                    used.add(origin(source, name))
        for ref in refs:
            pieces = ref.split(".")
            if len(pieces) < 2 or pieces[0] not in local_modules:
                continue
            module = local_modules.get(pieces[0])
            rest = pieces[1:]
            while len(rest) > 1 and f"{module}.{rest[0]}" in known:
                module = f"{module}.{rest[0]}"
                rest = rest[1:]
            used.add(origin(module, rest[0]))
        return used

    users = defaultdict(set)
    for f in python_files:
        if f.parse_error:
            continue
        is_pkg = f.path.endswith("__init__.py")
        for key in used_by(f.import_from, f.module_aliases, f.references, f.module, is_pkg):
            users[key].add(f.path)
    for nb in notebooks:
        for key in used_by(nb.import_from, nb.module_aliases, nb.references, "", False):
            users[key].add(nb.path)

    consumers = {}
    tests = {}
    for symbol in symbols:
        top = symbol.qualname.split(".")[0]
        paths = users.get((symbol.module, top), set()) - {symbol.path}
        key = f"{symbol.module}.{symbol.qualname}"
        consuming = sorted(p for p in paths if not is_test_path(p))
        testing = sorted(p for p in paths if is_test_path(p))
        if consuming:
            consumers[key] = consuming
        if testing:
            tests[key] = testing
    return dict(sorted(consumers.items())), dict(sorted(tests.items()))


# ---------------------------------------------------------------------------
# Static diagnostics
# ---------------------------------------------------------------------------

def import_integrity_attention(python_files, notebooks, internal_roots):
    modules = {f.module: f for f in python_files}
    packages = {m.rsplit(".", 1)[0] for m in modules if "." in m}
    missing_modules = defaultdict(set)
    missing_names = defaultdict(set)

    def check(module, names, where):
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
            full = f"{module}.{name}"
            if full in modules or full in packages:
                continue
            missing_names[full].add(where)

    for f in python_files:
        is_pkg = f.path.endswith("__init__.py")
        for item in f.import_from:
            module = resolve_relative(item.get("module", ""), f.module, is_pkg)
            check(module, item.get("names", ()), f"{f.path}:{item.get('lineno')}")
    for nb in notebooks:
        for item in nb.import_from:
            check(item.get("module", ""), item.get("names", ()), f"{nb.path}#cell-{item.get('cell')}")

    attention = [
        Attention(
            "high", "internal-import-missing-module",
            f"Import of internal module `{name}`, which does not exist in the snapshot.",
            sorted(paths),
            "Check branch completeness, renamed modules or stale imports before recreating code.",
        )
        for name, paths in sorted(missing_modules.items())
    ]
    for name, paths in sorted(missing_names.items()):
        module, short = name.rsplit(".", 1)
        attention.append(
            Attention(
                "high", "internal-import-missing-name",
                f"`{short}` is imported from `{module}`, but that module does not define or re-export it.",
                sorted(paths),
                "Export the name in the module (or its __init__) or fix the import.",
            )
        )
    return attention


def call_signature_attention(symbols, python_files, notebooks):
    """Calls to project functions with keywords they do not accept."""
    candidates = defaultdict(list)
    for symbol in symbols:
        if symbol.kind in {"function", "class"} and symbol.path.startswith("src/"):
            candidates[symbol.name].append(symbol)
    unique = {name: items[0] for name, items in candidates.items() if len(items) == 1}
    local_defs = defaultdict(set)
    for f in python_files:
        local_defs[f.path].update(s.name for s in f.symbols if s.kind in {"function", "class"})
    for nb in notebooks:
        local_defs[nb.path].update(s.name for s in nb.functions + nb.classes)

    problems = []
    sources = [(f.path, f.call_sites) for f in python_files]
    sources += [(n.path, n.call_sites) for n in notebooks]
    for path, sites in sources:
        defined_here = local_defs.get(path, set())
        for site in sites:
            tail = site.name.rsplit(".", 1)[-1]
            target = unique.get(tail)
            if target is None or path == target.path or tail in defined_here:
                continue
            if "." in site.name and site.name.split(".")[0] in {"self", "cls"}:
                continue
            issues = []
            if not target.has_varkw:
                bad = [k for k in site.keywords if k not in target.params]
                if bad:
                    issues.append(f"unknown keyword(s) {bad}")
            too_many = site.n_positional > target.n_positional_params
            if not target.has_varargs and not site.has_star_args and too_many:
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


def gate_attention(gate_names, files_text, notebook_sources):
    if not gate_names:
        return []
    found = defaultdict(set)
    merged = dict(files_text)
    merged.update(notebook_sources)
    for path, text in merged.items():
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


def config_contract_attention(config, python_files):
    if not isinstance(config, dict):
        return []
    attention = []

    def as_list(*keys):
        value = nested_get(config, *keys, default=())
        return [str(v) for v in value] if isinstance(value, list) else []

    final = as_list("features", "final")
    numeric_features = set(as_list("features", "numericas"))
    categorical_features = set(as_list("features", "categoricas"))
    active = set(final) or (numeric_features | categorical_features)
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
    model_features = numeric_features | categorical_features
    unused_derived = sorted(derived - model_features - set(final))
    if unused_derived:
        attention.append(Attention(
            "low", "derived-not-used-as-feature",
            "Derived columns produced by feature engineering but absent from the model feature lists.",
            unused_derived, "Confirm whether they are intentionally descriptive-only or missing from the model."))
    pieces = []
    for f in python_files:
        if f.path.startswith(("src/features/", "src/data/")):
            pieces.extend(f.calls)
            pieces.extend(f.constants)
            pieces.extend(f.constants.values())
            pieces.extend(f.file_literals)
            pieces.extend(f.top_level_names)
    source_text = " ".join(pieces)
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
    numbers = []
    for key in gates:
        match = re.match(r"G(\d+)_", str(key))
        if match:
            numbers.append(int(match.group(1)))
    numbers.sort()
    if numbers:
        gaps = [f"G{n}" for n in range(numbers[0], numbers[-1] + 1) if n not in numbers]
        if gaps:
            attention.append(Attention(
                "low", "gate-numbering", "Gate numbering has gaps.", gaps,
                "Document why the gate does not exist or renumber."))
    return attention


def unused_config_keys_attention(config, code_text):
    if not isinstance(config, dict):
        return []
    unused = []
    for key in flatten_mapping(config):
        parts = key.split(".")
        if parts[0] in {"gates", "selecao_modelos"}:
            continue
        leaf = next((p for p in reversed(parts) if not p.isdigit()), parts[-1])
        pattern = QUOTE + re.escape(leaf) + QUOTE
        if not re.search(pattern, code_text):
            unused.append(key)
    if not unused:
        return []
    return [Attention(
        "low", "config-key-not-referenced",
        f"{len(unused)} YAML keys whose name never appears as a string literal in code or notebooks "
        "(possible dead configuration, or keys read dynamically).",
        unused[:80], "Remove dead keys or make the code read them; keep documentation keys commented.")]


def dependency_attention(python_files, notebooks, requirements, pyproject_deps, import_map, internal_roots):
    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    used = defaultdict(set)
    for f in python_files:
        for value in f.external_imports:
            used[value.split(".")[0]].add(f.path)
    for nb in notebooks:
        for value in nb.imports:
            used[value.split(".")[0]].add(nb.path)
    third_party = {
        top: paths for top, paths in used.items()
        if top and top not in stdlib and top not in internal_roots and not top.startswith("_")
    }
    attention = []
    for label, deps in (("requirements.txt", requirements), ("pyproject.toml", pyproject_deps)):
        if deps is None:
            continue
        missing = []
        for top, paths in sorted(third_party.items()):
            dist = import_map.get(top, top).lower().replace("_", "-")
            if dist not in deps and top.lower() not in deps:
                first = sorted(paths)[0]
                missing.append(f"{top} (distribution `{dist}`) used in {first}")
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


def duplicate_symbol_attention(symbols):
    grouped = defaultdict(set)
    for symbol in symbols:
        if symbol.kind not in {"function", "class"}:
            continue
        if symbol.path.startswith("tests/") or symbol.name == "main":
            continue
        grouped[symbol.name].add(symbol.path)
    return [
        Attention(
            "medium", "duplicate-symbol-name", f"`{name}` is defined in multiple files.",
            sorted(paths), "Confirm distinct responsibilities or consolidate competing implementations.")
        for name, paths in sorted(grouped.items()) if len(paths) > 1
    ]


def duplicate_content_attention(file_records):
    groups = defaultdict(list)
    for record in file_records:
        if record.get("bytes", 0) > 0:
            groups[record.get("sha256")].append(record.get("path"))
    return [
        Attention(
            "low", "duplicate-file-content", "Files with identical content.", sorted(paths),
            "Keep a single copy, or confirm that the duplication is intentional.")
        for paths in groups.values() if len(paths) > 1
    ]


def notebook_attention(notebooks, python_files):
    canonical = defaultdict(list)
    for f in python_files:
        if f.path.startswith("src/"):
            for s in f.symbols:
                if s.kind in {"function", "class"}:
                    canonical[s.name].append(s.path)
    attention = []
    for nb in notebooks:
        local_symbols = nb.functions + nb.classes
        for s in local_symbols:
            if s.name in canonical:
                evidence = [s.path] + sorted(set(canonical.get(s.name, ())))
                attention.append(Attention(
                    "medium", "notebook-duplicates-src",
                    f"Notebook defines `{s.name}`, already present in src.",
                    evidence,
                    "Use the src implementation, or extend it if behaviour differs."))
        local = [s.name for s in local_symbols if s.name not in canonical]
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
            missing = nb.code_cells - nb.executed_cells
            attention.append(Attention(
                "low", "notebook-not-fully-executed",
                f"`{nb.path}`: {missing} of {nb.code_cells} code cells have no saved execution.",
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


def stale_document_attention(files_text, existing_paths):
    existing_dirs = {Path(p).parent.as_posix() for p in existing_paths}
    attention = []
    for path, text in files_text.items():
        if not path.lower().endswith((".md", ".rst", ".txt", ".py", ".yaml", ".yml")):
            continue
        refs = sorted({m.group(1) for m in DOC_PATH_RE.finditer(text)})
        missing = [
            r for r in refs
            if r not in existing_paths and "{" not in r and "*" not in r and r not in existing_dirs
        ]
        if missing:
            severity = "low" if path.endswith(".py") else "medium"
            attention.append(Attention(
                severity, "reference-to-missing-path",
                f"`{path}` references paths absent from the working folder.", missing[:40],
                "Confirm whether the reference is historical, generated at runtime, or stale."))
    return attention


def text_quality_attention(files_text, notebook_sources):
    mojibake = []
    todos = []
    merged = dict(files_text)
    merged.update(notebook_sources)
    for path, text in merged.items():
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


def working_tree_attention(entries):
    relevant = [
        e.path for e in entries
        if not e.tracked and e.exists and e.path.startswith(IMPORTANT_UNTRACKED_PREFIXES)
    ]
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


def symbol_quality_attention(symbols, consumers, tests):
    public = [
        s for s in symbols
        if s.path.startswith("src/") and not s.is_private and s.kind in {"function", "class"}
    ]
    orphan = []
    untested = []
    nodoc = []
    for s in public:
        key = f"{s.module}.{s.qualname}"
        label = f"{s.module}.{s.name}"
        if not consumers.get(key) and not tests.get(key):
            orphan.append(label)
        if not tests.get(key):
            untested.append(label)
        if not s.docstring:
            nodoc.append(label)
    out = []
    if orphan:
        out.append(Attention(
            "low", "public-symbol-unused",
            "Public src symbols with no detected consumer and no test (possibly dead code).",
            orphan, "Remove, test, or document why they exist."))
    if untested:
        out.append(Attention(
            "low", "public-symbol-untested",
            f"{len(untested)} public src symbols without a detected test.", untested,
            "Prioritise tests for functions consumed by notebooks and other modules."))
    if nodoc:
        out.append(Attention(
            "low", "missing-docstring", "Public src symbols without docstring.", nodoc,
            "Add a short docstring with purpose, parameters and returned value."))
    return out


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def render_attention(attention):
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
        message = a.message.replace("|", "/")
        lines.append(f"| A{i} | {a.severity.upper()} | {a.category} | {message} |")
    lines.append("")
    for i, a in enumerate(ordered, 1):
        lines.extend([f"### A{i}. {a.severity.upper()} — {a.category}", "", a.message, ""])
        if a.evidence:
            lines.append("**Evidence**")
            lines.append("")
            lines.extend(f"- `{v}`" for v in a.evidence)
            lines.append("")
        if a.recommendation:
            lines.extend([f"**Recommended action:** {a.recommendation}", ""])
    return "\n".join(lines).rstrip()


def render_symbol(symbol, consumers, tests):
    key = f"{symbol.module}.{symbol.qualname}"
    tested = ", ".join(f"`{p}`" for p in tests.get(key, ())) or "not found statically"
    consumed = ", ".join(f"`{p}`" for p in consumers.get(key, ())) or "not found statically"
    visibility = "private" if symbol.is_private else "public"
    lines = [
        f"#### `{symbol.qualname}`",
        "",
        code_block(symbol.signature, "python"),
        "",
        f"- Location: `{symbol.path}:{symbol.lineno}-{symbol.end_lineno}`",
        f"- Visibility: `{visibility}`",
        "- Tested by: " + tested,
        "- Consumed by: " + consumed,
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
    lines.extend(["", symbol.docstring or "_Missing docstring._", ""])
    return "\n".join(lines)


def render_python_api(python_files, consumers, tests):
    parts = []
    for f in sorted(python_files, key=lambda x: x.path.lower()):
        parts.extend([f"### `{f.path}`", ""])
        if f.parse_error:
            parts.extend([f"- **Parse error:** `{f.parse_error}`", ""])
            continue
        internal = ", ".join(f"`{v}`" for v in f.internal_imports) or "none"
        external = ", ".join(f"`{v}`" for v in f.external_imports) or "none"
        parts.extend([
            f"- Module: `{f.module}` · {f.lines} lines",
            "- Internal imports: " + internal,
            "- External imports: " + external,
        ])
        if f.constants:
            parts.append("- Module constants: " + ", ".join(f"`{k} = {v}`" for k, v in f.constants.items()))
        if f.env_vars:
            parts.append("- Environment variables: " + ", ".join(f"`{e}`" for e in f.env_vars))
        parts.append("")
        if f.docstring:
            parts.extend([f.docstring, ""])
        for symbol in f.symbols:
            parts.append(render_symbol(symbol, consumers, tests))
    return "\n".join(parts).rstrip()


def render_table(headers, rows):
    if not rows:
        return "- None."
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for row in rows:
        cells = [str(c).replace("|", "/").replace("\n", " ") for c in row]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def render_tree(inventory):
    """Directory tree with file counts and sizes."""
    dirs = defaultdict(lambda: [0, 0])
    for row in inventory:
        parent = Path(row.get("path")).parent.as_posix()
        while True:
            totals = dirs[parent]
            totals[0] += 1
            totals[1] += row.get("bytes", 0)
            if parent in {".", ""}:
                break
            parent = Path(parent).parent.as_posix()
    lines = []
    for d in sorted(dirs):
        depth = 0 if d == "." else d.count("/") + 1
        name = "./" if d == "." else Path(d).name + "/"
        files_count, size = dirs.get(d)
        lines.append(f"{'  ' * depth}{name}  ({files_count} files, {human_bytes(size)})")
    return code_block("\n".join(lines), "text")


def split_document(document, max_bytes):
    """Split on level-2 headings, keeping parts under max_bytes when possible.

    Sizes are tracked incrementally, so the cost stays linear even for very
    large documents.
    """
    chunks = []
    current = []
    for line, inside in iter_lines_with_fence_state(document):
        if not inside and line.startswith("## ") and current:
            chunks.append("".join(current))
            current = []
        current.append(line)
    if current:
        chunks.append("".join(current))

    parts = []
    buffer = []
    buffer_size = 0
    note = "\n\n_(section continues in the next part)_\n"
    for chunk in chunks:
        chunk_size = len(chunk.encode("utf-8"))
        if buffer and buffer_size + chunk_size > max_bytes:
            parts.append("".join(buffer))
            buffer = []
            buffer_size = 0
        if chunk_size <= max_bytes:
            buffer.append(chunk)
            buffer_size += chunk_size
            continue
        for line in chunk.splitlines(keepends=True):
            line_size = len(line.encode("utf-8"))
            if buffer and buffer_size + line_size > max_bytes:
                parts.append("".join(buffer) + note)
                buffer = []
                buffer_size = 0
            buffer.append(line)
            buffer_size += line_size
    if buffer:
        parts.append("".join(buffer))
    return parts


def map_sections_to_parts(parts):
    """Level-2 heading -> numbers of the parts where it appears.

    The fence state is carried from one part to the next, because a long
    section can be split in the middle of a code block.
    """
    mapping = defaultdict(list)
    current = None
    in_fence = None
    for number, part in enumerate(parts, 1):
        lines = part.splitlines()
        first = ""
        for line in lines:
            if line.strip():
                first = line
                break
        starts_new = in_fence is None and first.startswith("## ")
        if current is not None and not starts_new:
            mapping[current].append(number)
        for line in lines:
            fence = FENCE_RE.match(line)
            if fence:
                if in_fence is None:
                    in_fence = fence.group(1)
                elif line.strip() == in_fence:
                    in_fence = None
                continue
            if in_fence is None and line.startswith("## "):
                current = line[3:].strip()
                numbers = mapping[current]
                if number not in numbers:
                    numbers.append(number)
    return dict(mapping)


def render_index(part_names, section_map, file_records, machine):
    def where(heading):
        numbers = section_map.get(heading, ())
        return ", ".join(f"`{part_names[n - 1]}`" for n in numbers) or "-"

    repo = machine.get("repository", {})
    counts = Counter(a.get("severity") for a in machine.get("attention", ()))
    sections = [h for h in section_map if not (h.startswith("`") and h.endswith("`"))]
    file_rows = []
    for r in sorted(file_records, key=lambda x: x.get("path", "").lower()):
        status = r.get("status", "").strip()
        git_state = "tracked" if r.get("tracked") else "untracked"
        if status:
            git_state += f" ({status})"
        lines = r.get("lines")
        file_rows.append([
            f"`{r.get('path')}`",
            r.get("type", ""),
            git_state,
            "-" if lines is None else str(lines),
            human_bytes(r.get("bytes", 0)),
            where(f"`{r.get('path')}`"),
        ])
    commit = str(repo.get("commit", ""))
    lines_out = [
        "# Project reference index",
        "",
        "> **Generated file. Do not edit manually.**",
        f"> Generated by `{GENERATOR_PATH}` (schema v{SCHEMA_VERSION}).",
        "",
        f"- Generated (UTC): `{machine.get('generated_utc')}` · branch `{repo.get('branch')}` · commit `{commit[:12]}`",
        f"- Parts: `{len(part_names)}` · files with full content: `{len(file_records)}`",
        f"- Attention items: **{counts.get('high', 0)} high**, {counts.get('medium', 0)} medium, {counts.get('low', 0)} low",
        "",
        "## How to use",
        "",
        "1. Read this index first, then the parts holding Sections 1 to 7.",
        "2. Before proposing any function, class or module, search Section 12 (API catalog).",
        "   If an equivalent exists, reuse or extend it; never create a parallel implementation.",
        "3. To read a file, open the part listed for it below. A file may span several parts.",
        "4. Cite code as `path:line` and notebook cells as `path#cell-N:line`.",
        "   Line numbers are added by the generator and are not part of the files.",
        "5. Files marked `untracked` or with a status may differ in other copies of the repository.",
        "",
        "## Sections",
        "",
        render_table(["Section", "Parts"], [[s, where(s)] for s in sections]),
        "",
        "## Files",
        "",
        render_table(["File", "Type", "Git", "Lines", "Size", "Parts"], file_rows),
    ]
    return "\n".join(lines_out).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build_reference(root, args):
    print("[reference] 1/7 Coletando estado Git básico...", flush=True)
    redactor = Redactor(root)
    entries, tracked, untracked = collect_git_entries(root)
    print("[reference] 2/7 Inventariando arquivos locais...", flush=True)
    inventory, inventory_truncated = walk_inventory(root, tracked, untracked)
    inv_by_path = dict((row.get("path"), row) for row in inventory)
    existing_paths = set(inv_by_path)
    internal_roots = {"src", "tests", "tools"}
    for e in entries:
        p = Path(e.path)
        if e.exists and p.suffix.lower() in {".py", ".pyi"} and len(p.parts) > 1:
            internal_roots.add(p.parts[0])

    selected = []
    seen = set()
    for e in entries:
        if e.exists and include_source(Path(e.path), tracked=e.tracked):
            selected.append((Path(e.path), e.tracked, e.status))
            seen.add(e.path)
    ignored_sources = []
    for row in inventory:
        rel_text = row.get("path")
        rel_path = Path(rel_text)
        if (
            row.get("git") == "ignored"
            and rel_text not in seen
            and rel_text.startswith(IMPORTANT_UNTRACKED_PREFIXES)
            and include_source(rel_path, tracked=True)
        ):
            selected.append((rel_path, False, "!! ignored by .gitignore"))
            ignored_sources.append(rel_text)

    python_files = []
    notebooks = []
    files_text = {}
    notebook_text = {}
    file_records = []
    source_sections = []
    skipped = []
    yaml_docs = {}
    config = None
    config_error = None
    yaml_duplicates = {}
    pyproject_data = None
    pyproject_error = None
    requirements = None
    numbered = args.line_numbers

    print(
        f"[reference] 3/7 Lendo {len(selected)} arquivos de código, notebooks e documentação em integridade...",
        flush=True,
    )
    for file_index, (rel, is_tracked, status) in enumerate(selected, 1):
        rel_text = rel.as_posix()
        if file_index == 1 or file_index % 10 == 0 or file_index == len(selected):
            print(f"[reference] Arquivo {file_index}/{len(selected)}: {rel_text}", flush=True)
        data = (root / rel).read_bytes()
        digest = sha256_bytes(data)
        suffix = rel.suffix.lower()
        git_label = "tracked" if is_tracked else "untracked (working tree)"
        modified = inv_by_path.get(rel_text, {}).get("modified_utc", "?")
        header = [
            f"## `{rel_text}`",
            "",
            f"- Git: `{git_label}` · status `{status.strip() or 'clean'}`",
            f"- Size: `{human_bytes(len(data))}` · modified `{modified} UTC`",
            f"- SHA-256: `{digest}`",
        ]
        record = {
            "path": rel_text, "tracked": is_tracked, "status": status, "sha256": digest,
            "bytes": len(data), "type": suffix.lstrip(".") or rel.name, "lines": None,
        }
        if suffix in LIKELY_BINARY_SUFFIXES:
            skipped.append(f"{rel_text} (binary)")
            continue

        if suffix == ".ipynb":
            try:
                analysis, nb = analyze_notebook(rel, data, internal_roots)
            except Exception as exc:
                skipped.append(f"{rel_text} (notebook parse error: {exc!r})")
                continue
            reduced = len(data) > args.max_inline_bytes
            analysis.outputs_included = args.notebook_outputs
            notebooks.append(analysis)
            notebook_text[rel_text] = "\n".join(cell_source(c) for c in nb.get("cells", ()))
            record["lines"] = analysis.code_lines
            body = notebook_source_markdown(
                nb, analysis, include_outputs=args.notebook_outputs,
                max_output_chars=args.max_output_chars, reduced=reduced,
                redactor=redactor, numbered=numbered,
            )
            source_sections.append("\n".join(header) + "\n\n" + body + "\n")
            file_records.append(record)
            continue

        if suffix in OFFICE_SUFFIXES:
            try:
                text = office_text(data, suffix)
            except Exception as exc:
                skipped.append(f"{rel_text} (office parse error: {exc!r})")
                continue
            text, _ = redactor(text)
            files_text[rel_text] = text
            record["lines"] = len(text.splitlines())
            header.append("- Content: plain text extracted (formatting, tables layout and images not preserved)")
            shown = number_lines(text.rstrip()) if numbered else text.rstrip()
            source_sections.append("\n".join(header) + "\n\n" + code_block(shown, "text") + "\n")
            file_records.append(record)
            continue

        if looks_binary(data):
            skipped.append(f"{rel_text} (binary content)")
            continue
        decoded = data.decode("utf-8-sig", errors="replace")
        if rel.name in KEYS_ONLY_FILES:
            text = keys_only_json(decoded)
            warnings = ["values hidden (keys only)"]
        elif rel_text == GENERATOR_PATH:
            # The generator's own regular expressions look like secrets.
            text = redactor.replace_paths(decoded)
            warnings = []
        else:
            text, warnings = redactor(decoded)
        files_text[rel_text] = text
        record["lines"] = len(text.splitlines())
        if warnings:
            header.append("- Security: " + "; ".join(warnings))
        if suffix in {".py", ".pyi"}:
            analysis_py = analyze_python(rel, text, internal_roots)
            python_files.append(analysis_py)
            header.append(f"- Module: `{analysis_py.module}`")
        elif suffix in {".yaml", ".yml"}:
            parsed, error, dups = load_yaml_strict(decoded)
            yaml_docs[rel_text] = {"error": error, "duplicates": dups}
            if dups:
                yaml_duplicates[rel_text] = dups
            if rel_text == args.config:
                config, config_error = parsed, error
        elif rel.name == "pyproject.toml":
            pyproject_data, pyproject_error = parse_pyproject(decoded)
        elif rel.name == "requirements.txt" and len(rel.parts) == 1:
            requirements = parse_requirements(decoded)
        header.append(f"- Lines: `{record.get('lines')}` · cite as `{rel_text}:line`")
        # Source and documentation are included in full. Limits apply only to
        # notebook outputs and generated artifacts, never to code or project docs.
        shown = number_lines(text.rstrip()) if numbered else text.rstrip()
        body = code_block(shown, LANG.get(suffix, "text"))
        source_sections.append("\n".join(header) + "\n\n" + body + "\n")
        file_records.append(record)

    # Small text artifacts (outputs/, data/ manifests, reports/)
    artifact_sections = []
    artifact_records = []
    if args.artifacts:
        for row in inventory:
            rel = Path(row.get("path"))
            if not include_artifact(rel, row.get("bytes", 0), args.max_artifact_bytes):
                continue
            try:
                raw = (root / rel).read_bytes()
            except OSError:
                continue
            if looks_binary(raw):
                continue
            text, _ = redactor(raw.decode("utf-8-sig", errors="replace"))
            suffix = rel.suffix.lower()
            note = ""
            if suffix in {".csv", ".tsv"}:
                text, total = csv_preview(text, args.max_csv_rows)
                note = f" · {total} rows"
                if total > args.max_csv_rows:
                    note += f" (first {args.max_csv_rows} shown)"
            else:
                text = truncate(text, args.max_artifact_bytes)
            artifact_sections.append(
                f"### `{rel.as_posix()}`\n\n- Git: `{row.get('git')}` · `{human_bytes(row.get('bytes', 0))}` · "
                f"modified `{row.get('modified_utc')} UTC`{note}\n\n"
                + code_block(text.rstrip(), LANG.get(suffix, "text")) + "\n"
            )
            artifact_records.append(row)
            if suffix in {".yaml", ".yml"}:
                files_text[rel.as_posix()] = text

    # Indexes and diagnostics
    symbols = [s for f in python_files for s in f.symbols]
    print("[reference] 4/7 Construindo catálogo de APIs, consumidores e testes...", flush=True)
    consumers, tests = index_usage(symbols, python_files, notebooks)
    import_map = top_level_import_map()
    packages = installed_packages()
    pyproject_deps = pyproject_dependencies(pyproject_data) if pyproject_data else None
    gates = nested_get(config, "gates", default={}) if isinstance(config, dict) else {}
    gate_names = set(gates) if isinstance(gates, dict) else set()
    code_pieces = [t for p, t in files_text.items() if p.endswith(".py")]
    code_pieces.extend(notebook_text.values())
    code_text = "\n".join(code_pieces)

    attention = []
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
    attention += duplicate_content_attention(file_records)
    attention += notebook_attention(notebooks, python_files)
    attention += stale_document_attention(files_text, existing_paths)
    quality, todos = text_quality_attention(files_text, notebook_text)
    attention += quality
    attention += symbol_quality_attention(symbols, consumers, tests)
    for f in python_files:
        if f.parse_error:
            attention.append(Attention(
                "high", "python-parse-error", f"`{f.path}` could not be parsed.",
                [f.parse_error], "Fix syntax or check interpreter compatibility."))
    if config_error:
        attention.append(Attention(
            "high", "yaml-error", f"`{args.config}` could not be analysed.",
            [config_error], "Fix the YAML (or install PyYAML) and regenerate."))
    for path, dups in yaml_duplicates.items():
        attention.append(Attention(
            "high", "yaml-duplicate-keys",
            f"`{path}` has duplicated keys; yaml.safe_load silently keeps the last value.",
            dups, "Remove the duplicates."))
    if pyproject_error:
        attention.append(Attention(
            "high", "pyproject-invalid", "`pyproject.toml` is not valid TOML.",
            [pyproject_error], "Fix it; `pip install -e .` fails with an invalid pyproject."))
    if inventory_truncated:
        attention.append(Attention(
            "low", "inventory-truncated",
            f"Path inventory stopped at {MAX_INVENTORY_ENTRIES} files.", [],
            "Exclude large generated folders or raise MAX_INVENTORY_ENTRIES."))

    if args.run_tests:
        print("[reference] 5/7 Executando pytest...", flush=True)
        tests_result = run_tests(root, args.pytest_args, args.test_timeout)
    else:
        print("[reference] 5/7 Pytest não solicitado; seguindo sem executar código...", flush=True)
        tests_result = None
    if tests_result and tests_result.get("returncode") not in (0, None):
        output_lines = (tests_result.get("output") or "").splitlines()
        last_line = output_lines[-1] if output_lines else ""
        attention.append(Attention(
            "high", "tests-failing", "pytest returned a non-zero exit code.",
            [last_line], "See Section 11."))

    print("[reference] 6/7 Coletando contexto Git rápido e montando documentos...", flush=True)
    branch = git(root, "branch", "--show-current").strip() or "detached"
    commit = git(root, "rev-parse", "HEAD", check=False).strip() or "no commits"
    remote, _ = redactor(git(root, "remote", "get-url", "origin", check=False).strip())
    status_text = git(root, "status", "--short", "--branch").rstrip() or "clean"
    log_text = git(
        root, "log", f"-{args.git_log}", "--date=iso", "--pretty=format:%h %ad %an%n    %s", check=False
    ).rstrip()
    branches = git(root, "branch", "-a", "-vv", check=False).rstrip()
    ahead_behind = git(root, "rev-list", "--left-right", "--count", "HEAD...@{upstream}", check=False).strip()
    diff_stat = git(root, "diff", "HEAD", "--stat", check=False).rstrip()
    diff_text = ""
    if args.include_diff:
        raw_diff = git(
            root, "diff", "HEAD", "--", ".",
            ":(exclude)docs/" + OUTPUT_MD_NAME, ":(exclude)docs/" + OUTPUT_JSON_NAME,
            check=False,
        )
        diff_text = truncate(redactor(raw_diff)[0], args.max_diff_chars)
    candidates = ("data/", "outputs/", "models/", ".env", "configs/paths.local.json")
    local_paths = [p for p in candidates if (root / p).exists()]
    gitignore_check = ""
    if local_paths:
        gitignore_check = git(root, "check-ignore", "-v", "--no-index", *local_paths, check=False).strip()
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    counts = Counter(a.severity for a in attention)
    public = [
        s for s in symbols
        if s.path.startswith("src/") and not s.is_private and s.kind in {"function", "class"}
    ]
    with_tests = sum(bool(tests.get(f"{s.module}.{s.qualname}")) for s in public)
    with_consumers = sum(bool(consumers.get(f"{s.module}.{s.qualname}")) for s in public)
    git_state = "clean" if status_text.count("\n") == 0 else "has changes"
    tests_label = f"yes, exit {tests_result.get('returncode')}" if tests_result else "no (use --run-tests)"
    inv_tracked = sum(r.get("git") == "tracked" for r in inventory)
    inv_untracked = sum(r.get("git") == "untracked" for r in inventory)
    inv_ignored = sum(r.get("git") == "ignored" for r in inventory)

    # ---- Section 6
    sec6 = [
        "## 6. Executive continuation map", "",
        f"- Generated (UTC): `{generated}` · branch `{branch}` · commit `{commit[:12]}`",
        f"- Git status: `{git_state}`; upstream ahead/behind: `{ahead_behind or 'n/a'}`",
        f"- Files in working folder (inventory): `{len(inventory)}` "
        f"(tracked `{inv_tracked}`, untracked `{inv_untracked}`, ignored/local `{inv_ignored}`)",
        f"- Source files with full content: `{len(file_records)}`; artifacts included: `{len(artifact_records)}`",
        f"- Python modules: `{len(python_files)}` · notebooks: `{len(notebooks)}` · public src symbols: `{len(public)}`",
        f"- Public src symbols with tests: `{with_tests}` · with consumers: `{with_consumers}`",
        f"- Attention items: **{counts.get('high', 0)} high**, {counts.get('medium', 0)} medium, {counts.get('low', 0)} low",
        f"- Tests executed: `{tests_label}`",
        f"- Line numbers in Section 17: `{'yes' if numbered else 'no'}`",
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
            gate_rows = []
            for k in gates:
                description = str(nested_get(gates, k, "descricao") or "").strip()
                gate_rows.append([
                    f"`{k}`",
                    str(nested_get(gates, k, "status")),
                    str(nested_get(gates, k, "aprovado_por")),
                    str(nested_get(gates, k, "data")),
                    description[:160],
                ])
            sec8.extend([
                "### Gates", "",
                render_table(["Gate", "Status", "Approved by", "Date", "Description"], gate_rows), "",
            ])
        sec8.extend(["### Flattened active configuration", "", f"Source: `{args.config}`", ""])
        for k, v in flatten_mapping(config).items():
            sec8.append(f"- `{k}`: `{repr(v)[:400]}`")
    else:
        sec8.append(f"- Configuration unavailable: `{config_error}`")
    yaml_rows = []
    for p, d in sorted(yaml_docs.items()):
        error = d.get("error")
        yaml_rows.append([f"`{p}`", "ok" if not error else error[:80], ", ".join(d.get("duplicates", ())) or "none"])
    sec8.extend(["", "### YAML files", "", render_table(["File", "Parse", "Duplicated keys"], yaml_rows)])
    sec8.extend(["", "### pyproject.toml", ""])
    if pyproject_data is not None:
        deps_text = ", ".join(f"`{k}{v}`" for k, v in (pyproject_deps or {}).items()) or "none"
        sec8.extend([
            f"- Valid TOML: yes · name `{nested_get(pyproject_data, 'project', 'name')}` · "
            f"requires-python `{nested_get(pyproject_data, 'project', 'requires-python')}`",
            "- Dependencies: " + deps_text,
        ])
    else:
        sec8.append(f"- {pyproject_error or 'not found'}")
    req_text = ", ".join(f"`{k}{v}`" for k, v in requirements.items()) if requirements else "not found"
    sec8.extend(["", "### requirements.txt", "", "- " + req_text])

    # ---- Section 9: environment
    key_rows = []
    declared = dict(requirements or {})
    declared.update(pyproject_deps or {})
    for name in KEY_PACKAGES:
        if name in packages or name in declared:
            req_value = (requirements or {}).get(name, "—") if requirements is not None else "n/a"
            pyp_value = (pyproject_deps or {}).get(name, "—") if pyproject_deps is not None else "n/a"
            key_rows.append([f"`{name}`", packages.get(name, "**not installed**"), req_value, pyp_value])
    in_venv = "yes" if str(root).lower() in sys.executable.lower() else "no (results reflect another interpreter)"
    python_version = sys.version.split()[0]
    sec9 = [
        "## 9. Python environment", "",
        f"- Interpreter: `{python_version}` · implementation `{platform.python_implementation()}`",
        f"- Executable inside repo venv: `{in_venv}`",
        f"- Platform: `{platform.platform()}`",
        f"- PyYAML available: `{yaml is not None}` · tomllib available: `{tomllib is not None}`",
        "", "### Key packages: installed vs declared", "",
        render_table(["Package", "Installed", "requirements.txt", "pyproject.toml"], key_rows),
        "", "### All installed distributions", "",
        code_block("\n".join(f"{k}=={v}" for k, v in packages.items()), "text"),
    ]

    # ---- Section 10: inventory
    inventory_rows = [
        [f"`{r.get('path')}`", r.get("git"), human_bytes(r.get("bytes", 0)), r.get("modified_utc")]
        for r in inventory
    ]
    sec10 = [
        "## 10. Path inventory of the working folder", "",
        "Contents of data/models are never copied. `ignored` = exists locally but is ignored by Git.", "",
        "### Directory tree", "", render_tree(inventory), "",
        "### All files", "",
        render_table(["Path", "Git", "Size", "Modified (UTC)"], inventory_rows),
        "", "### Skipped files", "",
    ]
    sec10.extend(f"- `{s}`" for s in skipped)
    if not skipped:
        sec10.append("- None.")
    sec10.extend(["", "### .gitignore check for local folders", "", code_block(gitignore_check or "n/a", "text")])

    # ---- Section 11: tests
    test_rows = []
    for f in python_files:
        if is_test_path(f.path):
            names = [s.qualname for s in f.symbols if s.name.startswith("test_")]
            internal = ", ".join(f"`{v}`" for v in f.internal_imports) or "none"
            test_rows.append([f"`{f.path}`", str(len(names)), internal])
    sec11 = ["## 11. Tests", "", render_table(["Test file", "Tests", "Internal imports"], test_rows), ""]
    if tests_result:
        sec11.extend([
            f"### pytest result (exit `{tests_result.get('returncode')}`)", "",
            f"Command: `{tests_result.get('command')}`", "",
            code_block(truncate(redactor(tests_result.get("output", ""))[0], 60_000), "text"),
        ])
    else:
        sec11.append("pytest was not executed. Use `--run-tests` (optionally `--pytest-args \"-m 'not slow'\"`).")

    # ---- Sections 13 to 16
    dep_rows = [
        [f"`{f.module}`", ", ".join(f"`{v}`" for v in f.internal_imports) or "none"]
        for f in sorted(python_files, key=lambda x: x.module)
    ]
    sec13 = ["## 13. Internal dependency map", "", render_table(["Module", "Internal imports"], dep_rows)]
    nb_rows = []
    for n in sorted(notebooks, key=lambda x: x.path):
        nb_rows.append([
            f"`{n.path}`",
            f"{n.code_cells}/{n.markdown_cells}",
            f"{n.executed_cells}/{n.code_cells}",
            "yes" if n.out_of_order else "no",
            str(len(n.error_outputs)),
            ", ".join(f"`{v}`" for v in n.internal_imports) or "none",
            ", ".join(f"`{s.name}`" for s in n.functions + n.classes) or "none",
        ])
    sec14 = [
        "## 14. Notebook orchestration inventory", "",
        render_table(
            ["Notebook", "Code/MD cells", "Executed", "Out of order", "Errors", "Internal imports", "Local functions"],
            nb_rows,
        ),
        "",
    ]
    for n in sorted(notebooks, key=lambda x: x.path):
        sec14.extend([f"### `{n.path}` headings", ""])
        sec14.extend(f"- {h}" for h in n.headings)
        sec14.append("")
        if n.file_literals:
            sec14.extend(["Referenced files: " + ", ".join(f"`{v}`" for v in n.file_literals), ""])
    env_index = defaultdict(set)
    lit_index = defaultdict(set)
    for item in list(python_files) + list(notebooks):
        for e in item.env_vars:
            env_index[e].add(item.path)
        for lit in item.file_literals:
            lit_index[lit].add(item.path)
    env_lines = [
        f"- `{k}`: " + ", ".join(f"`{p}`" for p in sorted(v)) for k, v in sorted(env_index.items())
    ] or ["- None."]
    lit_lines = [
        f"- `{k}` ← " + ", ".join(f"`{p}`" for p in sorted(v)) for k, v in sorted(lit_index.items())
    ] or ["- None."]
    todo_lines = [f"- `{t}`" for t in todos] or ["- None."]
    sec15 = ["## 15. Environment variables, file literals and TODOs", "",
             "### Environment variables (names only)", ""]
    sec15.extend(env_lines)
    sec15.extend(["", "### File names referenced in code", ""])
    sec15.extend(lit_lines)
    sec15.extend(["", "### TODO / FIXME / PENDENTE markers", ""])
    sec15.extend(todo_lines)
    sec16 = [
        "## 16. Git history and uncommitted changes", "",
        "### Status", "", code_block(status_text, "text"), "",
        "### Branches", "", code_block(redactor(branches)[0] or "n/a", "text"), "",
        f"### Last {args.git_log} commits", "", code_block(redactor(log_text)[0] or "no commits", "text"), "",
        "### Diff stat (working tree vs HEAD)", "", code_block(diff_stat or "no changes", "text"),
    ]
    if args.include_diff:
        sec16.extend(["", "### Full diff (working tree vs HEAD)", "", code_block(diff_text or "no changes", "diff")])

    numbering_note = ""
    if numbered:
        numbering_note = (
            "Lines are numbered for citation (`path:line`, `path#cell-N:line`); "
            "the numbers are not part of the files."
        )
    options = {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()}
    artifacts_text = "\n".join(artifact_sections).rstrip() if artifact_sections else "- None included (use --artifacts)."
    document_parts = [CONTEXT.format(schema=SCHEMA_VERSION).rstrip(), ""]
    document_parts.extend(sec6)
    document_parts.extend(["", "## 7. Static attention report", "", render_attention(attention), ""])
    document_parts.extend(sec8)
    document_parts.append("")
    document_parts.extend(sec9)
    document_parts.append("")
    document_parts.extend(sec10)
    document_parts.append("")
    document_parts.extend(sec11)
    document_parts.extend([
        "",
        "## 12. Python API and reuse catalog", "",
        "Generated with Python AST; project modules are not imported. Consumers and tests are "
        "resolved through imports, aliases and package re-exports.", "",
        render_python_api(python_files, consumers, tests), "",
    ])
    document_parts.extend(sec13)
    document_parts.append("")
    document_parts.extend(sec14)
    document_parts.append("")
    document_parts.extend(sec15)
    document_parts.append("")
    document_parts.extend(sec16)
    document_parts.extend([
        "",
        "## 17. Full source by file", "",
        "Every relevant file of the repository, including untracked files in source folders. "
        "Notebooks include cell sources and, unless disabled, text outputs. " + numbering_note, "",
        "\n".join(source_sections).rstrip(), "",
        "## 18. Local artifacts (small text files from data/, outputs/, reports/, models/)", "",
        artifacts_text,
        "",
        "## 19. Snapshot provenance", "",
        f"- Generated UTC: `{generated}`",
        f"- Branch / commit: `{branch}` / `{commit}`",
        f"- Origin: `{remote or 'not configured'}`",
        f"- Generator options: `{options}`",
    ])
    document = "\n".join(document_parts).rstrip() + "\n"

    machine = {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "repository": {
            "branch": branch, "commit": commit, "origin": remote or None,
            "status": status_text, "ahead_behind": ahead_behind,
        },
        "environment": {"python": python_version, "platform": platform.platform(), "packages": packages},
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


def parse_args():
    # argparse rejects values that start with "-" (e.g. --pytest-args "-m 'not slow'").
    argv = list(sys.argv[1:])
    for index in range(len(argv) - 1):
        if argv[index] == "--pytest-args" and argv[index + 1].startswith("-"):
            merged = "--pytest-args=" + argv[index + 1]
            argv = argv[:index] + [merged] + argv[index + 2 :]
            break
    parser = argparse.ArgumentParser(
        description="Generate a complete diagnostic snapshot of the repository for review by a person or an AI.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Destination folder (default: docs).")
    parser.add_argument("--config", default="configs/supervised.yaml", help="Main YAML configuration (relative path).")
    parser.add_argument("--split-mb", type=float, default=DEFAULT_SPLIT_MB,
                        help=f"Size of each part in docs/{PARTS_DIR_NAME}/ (default: {DEFAULT_SPLIT_MB} MB).")
    parser.add_argument("--no-split", dest="split", action="store_false",
                        help="Do not write the part files (the index is still written).")
    parser.add_argument("--no-line-numbers", dest="line_numbers", action="store_false",
                        help="Do not number source lines in Section 17.")
    parser.add_argument("--no-notebook-outputs", dest="notebook_outputs", action="store_false",
                        help="Omit notebook outputs (sources only).")
    parser.add_argument("--max-output-chars", type=int, default=DEFAULT_MAX_OUTPUT_CHARS,
                        help="Maximum characters per notebook output.")
    parser.add_argument("--artifacts", dest="artifacts", action="store_true",
                        help="Also include small generated text artifacts. Disabled by default for speed.")
    parser.add_argument("--max-artifact-bytes", type=int, default=DEFAULT_MAX_ARTIFACT_BYTES)
    parser.add_argument("--max-csv-rows", type=int, default=DEFAULT_MAX_CSV_ROWS)
    parser.add_argument("--max-inline-bytes", type=int, default=DEFAULT_MAX_INLINE_BYTES,
                        help=f"Notebooks above this size show at most {MAX_SOURCE_LINES_PER_LARGE_NOTEBOOK_CELL} "
                             "lines per code cell.")
    parser.add_argument("--git-log", type=int, default=DEFAULT_GIT_LOG, help="Number of recent commits to list.")
    parser.add_argument("--include-diff", dest="include_diff", action="store_true",
                        help="Include the full uncommitted diff. Disabled by default for speed.")
    parser.add_argument("--max-diff-chars", type=int, default=DEFAULT_MAX_DIFF_CHARS)
    parser.add_argument("--run-tests", action="store_true",
                        help="Run pytest and include the result (executes project code).")
    parser.add_argument("--pytest-args", default="", help="Extra pytest arguments, e.g. \"-m 'not slow'\".")
    parser.add_argument("--test-timeout", type=int, default=1800)
    parser.add_argument("--fail-on-high", action="store_true", help="Exit with code 2 if HIGH attention items exist.")
    return parser.parse_args(argv)


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles
        except Exception:
            pass
    args = parse_args()
    root = root_dir()
    document, machine = build_reference(root, args)
    print("[reference] 7/7 Gravando Markdown, índice, partes e JSON...", flush=True)
    out_dir = root / args.output_dir
    output_md = out_dir / OUTPUT_MD_NAME
    output_json = out_dir / OUTPUT_JSON_NAME
    atomic_write(output_md, document)

    parts_dir = out_dir / PARTS_DIR_NAME
    if parts_dir.exists():
        for old in parts_dir.glob("part_*.md"):
            old.unlink()
    written_parts = []
    if args.split and args.split_mb > 0:
        parts = split_document(document, int(args.split_mb * 1024 * 1024))
        total = len(parts)
        part_names = [f"part_{i:02d}_of_{total:02d}.md" for i in range(1, total + 1)]
        for index, part in enumerate(parts, 1):
            target = parts_dir / part_names[index - 1]
            header = f"<!-- PROJECT_COMPLETE_REFERENCE part {index}/{total} -->\n"
            atomic_write(target, header + part)
            written_parts.append(target)
    else:
        parts = [document]
        part_names = ["../" + OUTPUT_MD_NAME]
    section_map = map_sections_to_parts(parts)
    index_path = parts_dir / INDEX_NAME
    atomic_write(index_path, render_index(part_names, section_map, machine.get("files", ()), machine))

    sections_json = {}
    for heading, numbers in section_map.items():
        sections_json[heading] = [part_names[n - 1] for n in numbers]
    machine["reference_parts"] = {
        "index": f"{args.output_dir.as_posix()}/{PARTS_DIR_NAME}/{INDEX_NAME}",
        "parts": part_names,
        "sections": sections_json,
    }
    atomic_write(output_json, json.dumps(machine, ensure_ascii=False, indent=2, default=str) + "\n")

    attention = machine.get("attention", ())
    high = sum(a.get("severity") == "high" for a in attention)
    print(f"update_project_reference.py schema v{SCHEMA_VERSION}")
    print(f"Updated: {output_md} ({human_bytes(output_md.stat().st_size)})")
    print(f"Updated: {output_json} ({human_bytes(output_json.stat().st_size)})")
    print(f"Index:   {index_path}")
    if written_parts:
        print(f"Parts:   {len(written_parts)} file(s) in {parts_dir}")
        for part in written_parts:
            print(f"         {part.name} ({human_bytes(part.stat().st_size)})")
    else:
        print("Parts:   not written (--no-split)")
    print(
        f"Inventory: {len(machine.get('inventory', ()))} files, full source: {len(machine.get('files', ()))}, "
        f"artifacts: {len(machine.get('artifacts', ()))}"
    )
    print(f"Python modules: {len(machine.get('python_files', ()))}, notebooks: {len(machine.get('notebooks', ()))}")
    print(f"Attention items: {len(attention)} ({high} high)")
    tests_result = machine.get("tests_result")
    if tests_result:
        print(f"pytest exit code: {tests_result.get('returncode')}")
    if args.fail_on_high and high:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())