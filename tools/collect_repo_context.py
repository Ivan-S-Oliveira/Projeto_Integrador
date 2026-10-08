#!/usr/bin/env python
"""Gera um pacote seguro de contexto técnico do repositório para pessoas e IAs.

As pastas data/, models/, outputs/ e logs/ são excluídas
somente quando estão na raiz. Módulos como src/data e
src/models permanecem incluídos no inventário.

Uso, na raiz do Git:
    python tools/collect_repo_context.py

Saídas:
    docs/ai_context/repo_inventory.json
    docs/ai_context/repo_inventory.md
    docs/ai_context/pip_inspect.json
    docs/ai_context/pip_freeze.txt
    docs/ai_context/git_tracked_files.txt

O script não lê valores de .env, não inclui o conteúdo de dados/artefatos, e exclui
.venv, .git, caches, outputs e arquivos grandes.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
OUT = ROOT / "docs" / "ai_context"
OUT.mkdir(parents=True, exist_ok=True)

EXCLUDED_DIR_NAMES_ANYWHERE = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".ipynb_checkpoints",
    "node_modules",
    "dist",
    "build",
}

EXCLUDED_ROOT_DIRS = {
    "data",
    "outputs",
    "models",
    "logs",
}
TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".json", ".ipynb", ".ps1", ".bat", ".sh", ".sql",
}
CODE_SUFFIXES = {".py", ".ipynb"}
MAX_TEXT_BYTES = 1_000_000
SECRET_NAME = re.compile(r"(token|secret|password|passwd|api[_-]?key|credential)", re.I)


def run(cmd: list[str]) -> dict[str, Any]:
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, errors="replace")
        return {"command": cmd, "returncode": p.returncode,
                "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    except Exception as exc:
        return {"command": cmd, "returncode": None, "stdout": "", "stderr": repr(exc)}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def excluded(path: Path) -> bool:
    """
    Exclui caches em qualquer nível, mas exclui data, models,
    outputs e logs somente quando forem pastas da raiz.

    Assim:
        data/processed/...       → excluído
        models/modelo.pkl        → excluído
        src/data/extracao.py     → incluído
        src/models/pipeline.py   → incluído
    """
    relative = path.relative_to(ROOT)
    parts = relative.parts

    if not parts:
        return False

    if any(
        part in EXCLUDED_DIR_NAMES_ANYWHERE
        for part in parts
    ):
        return True

    if parts[0] in EXCLUDED_ROOT_DIRS:
        return True

    return False


def tracked_files() -> list[Path]:
    result = run(["git", "ls-files", "-z"])
    if result["returncode"] == 0:
        return [ROOT / p for p in result["stdout"].split("\x00") if p]
    return [p for p in ROOT.rglob("*") if p.is_file() and not excluded(p)]


def safe_text(path: Path) -> str | None:
    if path.stat().st_size > MAX_TEXT_BYTES or path.suffix.lower() not in TEXT_SUFFIXES:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1")
        except Exception:
            return None
    except Exception:
        return None


def docstring(node: ast.AST) -> str | None:
    value = ast.get_docstring(node, clean=True)
    return value[:1200] if value else None


def signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = []
    positional = list(node.args.posonlyargs) + list(node.args.args)
    defaults_offset = len(positional) - len(node.args.defaults)
    for i, arg in enumerate(positional):
        prefix = "/" if node.args.posonlyargs and i == len(node.args.posonlyargs) else ""
        annotation = ast.unparse(arg.annotation) if arg.annotation else None
        item = arg.arg + (f": {annotation}" if annotation else "")
        if i >= defaults_offset:
            item += "=" + ast.unparse(node.args.defaults[i - defaults_offset])
        args.append(item)
        if prefix:
            args.append(prefix)
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    elif node.args.kwonlyargs:
        args.append("*")
    for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
        item = arg.arg
        if arg.annotation:
            item += ": " + ast.unparse(arg.annotation)
        if default is not None:
            item += "=" + ast.unparse(default)
        args.append(item)
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"{node.name}({', '.join(args)}){ret}"


def analyze_python(path: Path) -> dict[str, Any]:
    text = safe_text(path)
    if text is None:
        return {"parse_error": "arquivo não textual ou muito grande"}
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        return {"parse_error": f"{exc.msg} linha {exc.lineno}"}

    imports, functions, classes, constants = [], [], [], []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(("." * node.level) + (node.module or ""))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({"name": node.name, "signature": signature(node),
                              "line": node.lineno, "docstring": docstring(node)})
        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append({"name": item.name, "signature": signature(item),
                                    "line": item.lineno, "docstring": docstring(item)})
            classes.append({"name": node.name, "line": node.lineno,
                            "docstring": docstring(node), "methods": methods})
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    constants.append(target.id)
    return {"module_docstring": docstring(tree), "imports": sorted(set(imports)),
            "functions": functions, "classes": classes, "constants": constants}


def analyze_notebook(path: Path) -> dict[str, Any]:
    if path.stat().st_size == 0:
        return {
            "status": "placeholder",
            "empty": True,
            "cell_count": 0,
            "code_cells": 0,
            "markdown_cells": 0,
        }
    try:
        nb = json.loads(path.read_text(encoding="utf-8"))
        cells = nb.get("cells", [])
        return {
            "nbformat": nb.get("nbformat"),
            "kernel": nb.get("metadata", {}).get("kernelspec", {}),
            "language": nb.get("metadata", {}).get("language_info", {}),
            "cell_count": len(cells),
            "code_cells": sum(c.get("cell_type") == "code" for c in cells),
            "markdown_cells": sum(c.get("cell_type") == "markdown" for c in cells),
            "execution_counts": [c.get("execution_count") for c in cells if c.get("cell_type") == "code"],
        }
    except Exception as exc:
        return {"parse_error": repr(exc)}


def env_names_from_text(text: str) -> list[str]:
    patterns = [
        r"os\.getenv\([\"']([A-Za-z_][A-Za-z0-9_]*)",
        r"os\.environ(?:\.get)?\([\"']([A-Za-z_][A-Za-z0-9_]*)",
        r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}",
    ]
    found = set()
    for pattern in patterns:
        found.update(re.findall(pattern, text))
    return sorted(found)


def redact_config_preview(path: Path, text: str) -> str:
    if path.name == ".env" or SECRET_NAME.search(path.name):
        return "[conteúdo omitido por segurança]"
    lines = []
    for line in text.splitlines()[:250]:
        if "=" in line:
            key = line.split("=", 1)[0].strip()
            if SECRET_NAME.search(key):
                line = f"{key}=<REDACTED>"
        lines.append(line)
    return "\n".join(lines)


files = []
python_analysis = {}
notebooks = {}
env_vars = set()

for path in tracked_files():
    if not path.exists() or excluded(path):
        continue
    record = {
        "path": rel(path), "suffix": path.suffix.lower(),
        "size_bytes": path.stat().st_size, "sha256": sha256(path),
    }
    text = safe_text(path)
    if text is not None:
        record["line_count"] = len(text.splitlines())
        env_vars.update(env_names_from_text(text))
        if path.suffix.lower() in {".yaml", ".yml", ".toml", ".ini", ".cfg"}:
            record["preview_redacted"] = redact_config_preview(path, text)
    files.append(record)
    if path.suffix.lower() == ".py":
        python_analysis[rel(path)] = analyze_python(path)
    elif path.suffix.lower() == ".ipynb":
        notebooks[rel(path)] = analyze_notebook(path)

commands = {
    "git_status": run(["git", "status", "--short", "--branch"]),
    "git_remote": run(["git", "remote", "-v"]),
    "git_branches": run(["git", "branch", "--all", "--verbose", "--no-abbrev"]),
    "git_log": run(["git", "log", "--date=iso-strict", "--pretty=format:%H%x09%ad%x09%an%x09%s", "-n", "100"]),
    "git_tags": run(["git", "tag", "--list", "--sort=-creatordate"]),
    "git_submodules": run(["git", "submodule", "status"]),
    "python_version": run([sys.executable, "--version"]),
    "pip_check": run([sys.executable, "-m", "pip", "check"]),
}

pip_inspect = run([sys.executable, "-m", "pip", "inspect", "--local"])
if pip_inspect["returncode"] == 0:
    (OUT / "pip_inspect.json").write_text(pip_inspect["stdout"] + "\n", encoding="utf-8")
pip_freeze = run([sys.executable, "-m", "pip", "freeze"])
(OUT / "pip_freeze.txt").write_text(pip_freeze["stdout"] + "\n", encoding="utf-8")
(OUT / "git_tracked_files.txt").write_text("\n".join(sorted(f["path"] for f in files)) + "\n", encoding="utf-8")

inventory = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "root_name": ROOT.name,
    "python_executable": sys.executable,
    "python_version": sys.version,
    "platform": platform.platform(),
    "file_count": len(files),
    "files": sorted(files, key=lambda x: x["path"]),
    "python_analysis": python_analysis,
    "notebooks": notebooks,
    "environment_variable_names_only": sorted(env_vars),
    "commands": commands,
    "notes": [
        "Valores de variáveis de ambiente não são coletados.",
        "data/, outputs/, models/, logs/, .git/ e .venv/ são excluídos.",
        "Conteúdo integral dos arquivos não é copiado; são coletados estrutura, hashes e símbolos.",
    ],
}
(OUT / "repo_inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")

md = []
md.append("# Inventário técnico do repositório\n")
md.append(f"Gerado em: `{inventory['generated_at_utc']}`  ")
md.append(f"Python: `{sys.version.split()[0]}`  ")
md.append(f"Executável: `{sys.executable}`  ")
md.append(f"Arquivos rastreados analisados: **{len(files)}**\n")
md.append("## Estado do Git\n```text\n" + commands["git_status"]["stdout"] + "\n```\n")
md.append("## Variáveis de ambiente referenciadas\n")
md.extend(f"- `{name}`" for name in sorted(env_vars))
md.append("\n## Arquivos Python e símbolos\n")
for path, info in sorted(python_analysis.items()):
    md.append(f"### `{path}`")
    if info.get("parse_error"):
        md.append(f"- Erro de parse: `{info['parse_error']}`")
        continue
    if info.get("module_docstring"):
        md.append(f"- Módulo: {info['module_docstring'].splitlines()[0]}")
    for item in info.get("functions", []):
        md.append(f"- Função L{item['line']}: `{item['signature']}`")
    for cls in info.get("classes", []):
        md.append(f"- Classe L{cls['line']}: `{cls['name']}`")
        for method in cls["methods"]:
            md.append(f"  - Método L{method['line']}: `{method['signature']}`")
md.append("\n## Notebooks\n")
for path, info in sorted(notebooks.items()):
    md.append(f"- `{path}`: {info}")
md.append("\n## Validação do ambiente\n")
md.append(f"- `pip check` return code: `{commands['pip_check']['returncode']}`")
if commands["pip_check"]["stdout"]:
    md.append("```text\n" + commands["pip_check"]["stdout"] + "\n```")
if commands["pip_check"]["stderr"]:
    md.append("```text\n" + commands["pip_check"]["stderr"] + "\n```")
(OUT / "repo_inventory.md").write_text("\n".join(md) + "\n", encoding="utf-8")

print(f"Inventário criado em: {OUT}")
for p in sorted(OUT.iterdir()):
    print(" -", p.relative_to(ROOT))
