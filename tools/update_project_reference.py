#!/usr/bin/env python3
r"""One-command project reference generator.

Run from repository root:
    .\.venv\Scripts\python.exe tools\update_project_reference.py

Creates:
    docs/PROJECT_COMPLETE_REFERENCE.md
"""
from __future__ import annotations
import ast, hashlib, json, re, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path("docs/PROJECT_COMPLETE_REFERENCE.md")
MAX_BYTES = 4_000_000

# Diretórios ignorados em QUALQUER nível da árvore (não fazem parte do produto).
EXCLUDED_DIRS_ANYWHERE = {
    ".git", ".venv", "venv", "__pycache__",
    ".pytest_cache", ".ipynb_checkpoints", "node_modules",
}

# Diretórios ignorados APENAS na raiz (conteúdo local, gerado ou sensível).
EXCLUDED_DIRS_AT_ROOT = {"data", "outputs", "models", "logs"}

EXCLUDED_FILES = {".env", "paths.local.json", "pip_inspect-venv.json", OUTPUT.name}

TEXT_SUFFIXES = {".py", ".pyi", ".md", ".rst", ".txt", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".json", ".json5", ".sql", ".ps1", ".sh", ".bat", ".gitignore", ".gitattributes"}
SPECIAL_NAMES = {"README", "README.md", "LICENSE", "Makefile", "Dockerfile", "requirements.txt", "pyproject.toml", "pytest.ini", ".env.example"}
LANG = {".py":"python", ".pyi":"python", ".md":"markdown", ".rst":"rst", ".yaml":"yaml", ".yml":"yaml", ".toml":"toml", ".json":"json", ".json5":"json5", ".ini":"ini", ".cfg":"ini", ".sql":"sql", ".ps1":"powershell", ".sh":"bash", ".bat":"bat"}
ENV_RE = re.compile(r"(?:os\.getenv|os\.environ\.get|get_env|get_secret)\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]")
SECRET_RE = re.compile(r"(?im)^(\s*[A-Za-z_][A-Za-z0-9_.-]*?(?:token|secret|password|passwd|pwd|api[_-]?key|private[_-]?key|credential)[A-Za-z0-9_.-]*\s*[:=]\s*)([^\n#]+)")
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [^-]+ PRIVATE KEY-----.*?-----END [^-]+ PRIVATE KEY-----", re.DOTALL)

CONTEXT = '''# Project Complete Reference

> **Generated file. Do not edit manually.**  
> Update with `tools/update_project_reference.py`.

## 1. Project context

This is an academic retrospective machine-learning project using SRAG/SIVEP-Gripe data. The operational objective is to estimate risk of death from SRAG using only information plausibly available by hospital admission. The unit of analysis is an eligible notification used as a proxy for a hospital episode, not automatically a unique person.

This section states **intent and rules**, not a verified inventory of what is implemented. The authoritative views of the current codebase are:

- **Section 9 — Python API catalog**: public functions and classes actually present in tracked Python modules (generated statically via AST; project code is not imported or executed).
- **Section 11 — Complete tracked source**: literal contents of every included file, including notebooks without outputs.
- **`configs/supervised.yaml`**: approved or pending decisions and gates.

If a capability is mentioned in this section (or in any older plan) but does not appear in section 9 or section 11, treat it as **planned**, not implemented. Absence from the catalog is meaningful evidence, not an omission of the generator.

## 2. Non-negotiable methodological rules

- Academic retrospective analysis, not a clinically validated decision tool.
- Do not make causal claims from predictive associations.
- Prediction time is hospital admission. Later information cannot be a feature.
- Current target contract in `configs/supervised.yaml`: `evolucao == 2.0` is positive; `evolucao == 1.0` is negative; other values stay outside the primary binary target unless the config is formally changed and a gate is approved.
- Never use the final holdout to choose model, hyperparameters, calibration or threshold. Access is mediated by `TemporalSplit` and gated by `gates.G7_limiar`.
- Preserve temporal ordering. Do not silently replace temporal validation with random splitting.
- Data, trained models, outputs, local paths, `.env` and secrets do not belong in Git.
- Changes to cohort, target, features, split, seed, calibration, threshold or gates must update configuration, tests and documentation together.

## 3. Ways of working

1. Read this document before proposing code.
2. Search the API catalog and complete source sections before creating a function.
3. Notebooks orchestrate, explain and visualize. Reusable logic belongs in `src/`.
4. Experimental decisions belong in `configs/`.
5. Use `src/utils/storage.py` for the official Parquet contract.
6. Use `src/evaluation/temporal.py::TemporalSplit` for the final three-way workflow.
7. Reuse metrics and error analysis from `src/evaluation/`.
8. Use `src/utils/reproducibility.py::Run` instead of creating another logger.
9. A new public function requires an uncovered gap, typing, docstring and tests.
10. Review `git diff` and run relevant tests before integration.

## 4. Source precedence

1. Executable code and tests describe actual behavior.
2. `configs/supervised.yaml` describes approved or pending decisions and gates.
3. This generated reference combines the current codebase.
4. Older plans describe intent, not necessarily implementation.

## 5. Status labels

- **Implemented:** executable code exists.
- **Configured:** a value or rule exists in configuration.
- **Planned:** described but not confirmed in executable code.
- **Placeholder:** intentionally empty file reserved for later work.
- **Attention:** overlap, pending decision or technical risk.
'''

def git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode:
        raise RuntimeError(p.stderr.strip() or "Git command failed")
    return p.stdout

def root_dir() -> Path:
    p = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode:
        raise RuntimeError("Run inside the Git repository.")
    return Path(p.stdout.strip()).resolve()

def tracked(root: Path) -> list[Path]:
    return sorted((Path(x) for x in git(root, "ls-files").splitlines() if x.strip()), key=lambda p: p.as_posix().lower())

def include(path: Path) -> bool:
    parts = path.parts
    # Diretórios ignorados em qualquer nível.
    if any(part in EXCLUDED_DIRS_ANYWHERE for part in parts):
        return False
    # Diretórios locais ignorados apenas quando estão na raiz do repositório.
    if parts and parts[0] in EXCLUDED_DIRS_AT_ROOT:
        return False
    # Arquivos explicitamente excluídos.
    if path.name in EXCLUDED_FILES:
        return False
    # `.env` e variantes (.env.local, .env.production, ...) são sensíveis,
    # mas `.env.example` é seguro e deve ser versionado e incluído.
    if path.name.startswith(".env") and path.name != ".env.example":
        return False
    return path.suffix.lower() in TEXT_SUFFIXES or path.suffix.lower() == ".ipynb" or path.name in SPECIAL_NAMES

def redact(text: str) -> tuple[str, list[str]]:
    warnings = []
    if PRIVATE_KEY_RE.search(text):
        text = PRIVATE_KEY_RE.sub("[REDACTED_PRIVATE_KEY]", text); warnings.append("private key redacted")
    if SECRET_RE.search(text):
        text = SECRET_RE.sub(r"\1[REDACTED]", text); warnings.append("possible secret assignment redacted")
    return text, warnings

def function_signature(node) -> str:
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    try: args = ast.unparse(node.args)
    except Exception: args = "..."
    try: returns = " -> " + ast.unparse(node.returns) if node.returns else ""
    except Exception: returns = ""
    return f"{prefix} {node.name}({args}){returns}"

def api_section(path: Path, text: str) -> tuple[str, list[str]]:
    try: tree = ast.parse(text)
    except SyntaxError as exc: return f"### `{path.as_posix()}`\n\n- Parse error: `{exc}`\n", []
    out = [f"### `{path.as_posix()}`", ""]
    module_doc = ast.get_docstring(tree)
    if module_doc: out += [module_doc.strip(), ""]
    found = False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found = True; out += [f"#### `{function_signature(node)}`", f"- Source line: `{node.lineno}`", ast.get_docstring(node) or "- **Missing docstring**", ""]
        elif isinstance(node, ast.ClassDef):
            found = True; out += [f"#### `class {node.name}`", f"- Source line: `{node.lineno}`", ast.get_docstring(node) or "- **Missing class docstring**", ""]
            for method in node.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out += [f"##### `{function_signature(method)}`", ast.get_docstring(method) or "- **Missing method docstring**", ""]
    if not found: out += ["- No top-level functions or classes detected.", ""]
    return "\n".join(out), sorted(set(ENV_RE.findall(text)))

def notebook(data: bytes) -> tuple[str, dict]:
    if not data: return "_Empty placeholder._\n", {"cells": 0, "placeholder": True}
    nb = json.loads(data.decode("utf-8-sig")); blocks = []
    for i, cell in enumerate(nb.get("cells", []), 1):
        kind = cell.get("cell_type", "unknown"); source = "".join(cell.get("source", [])).rstrip(); lexer = "python" if kind == "code" else "markdown"
        blocks.append(f"### Cell {i} [{kind}]\n\n```{lexer}\n{source}\n```")
    return "\n\n".join(blocks) + "\n", {"cells": len(nb.get("cells", [])), "kernel": nb.get("metadata", {}).get("kernelspec", {}), "outputs_omitted": True}

def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); data = text.encode("utf-8")
    if path.exists() and path.read_bytes() == data: return
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=path.parent) as f: f.write(data); temp = f.name
    Path(temp).replace(path)

def main() -> int:
    root = root_dir(); output = root / OUTPUT; paths = [p for p in tracked(root) if include(p)]
    branch = git(root, "branch", "--show-current").strip() or "detached"; commit = git(root, "rev-parse", "HEAD").strip(); status = git(root, "status", "--short").rstrip() or "clean working tree"
    api, sources, variables, skipped = [], [], {}, []
    for rel in paths:
        data = (root / rel).read_bytes()
        if len(data) > MAX_BYTES: skipped.append(f"{rel.as_posix()} ({len(data)} bytes)"); continue
        digest = hashlib.sha256(data).hexdigest()
        if rel.suffix.lower() == ".ipynb":
            try: text, meta = notebook(data)
            except Exception as exc: text, meta = f"_Notebook parse error: {exc!r}_\n", {"parse_error": repr(exc)}
            sources.append(f"## `{rel.as_posix()}`\n\n- SHA-256: `{digest}`\n- Bytes: `{len(data)}`\n- Notebook: `{json.dumps(meta, ensure_ascii=False)}`\n\n{text}")
            continue
        if b"\x00" in data[:8192]: skipped.append(f"{rel.as_posix()} (binary)"); continue
        text, warnings = redact(data.decode("utf-8-sig", errors="replace"))
        if rel.suffix.lower() == ".py":
            section, names = api_section(rel, text); api.append(section)
            for name in names: variables.setdefault(name, set()).add(rel.as_posix())
        security = "\n> Security: " + "; ".join(warnings) + "\n" if warnings else ""
        lexer = LANG.get(rel.suffix.lower(), "text")
        sources.append(f"## `{rel.as_posix()}`\n\n- SHA-256: `{digest}`\n- Bytes: `{len(data)}`\n{security}\n```{lexer}\n{text.rstrip()}\n```\n")
    env = "\n".join(f"- `{name}`: " + ", ".join(f"`{p}`" for p in sorted(files)) for name, files in sorted(variables.items())) or "- None detected."
    skipped_text = "\n".join(f"- `{x}`" for x in skipped) or "- None."
    document = f'''{CONTEXT}

## 6. Current snapshot

- Generated UTC: `{datetime.now(timezone.utc).isoformat()}`
- Branch: `{branch}`
- Commit: `{commit}`
- Included tracked files: `{len(paths) - len(skipped)}`

### Git status

```text
{status}