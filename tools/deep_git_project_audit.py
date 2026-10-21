#!/usr/bin/env python3
from __future__ import annotations

r"""
Auditoria profunda do Git e atualização conservadora do PROJECT_STATUS.md.

Objetivos:
- percorrer todo o histórico alcançável do Git, em todas as refs;
- reconhecer marcadores explícitos e referências textuais a tarefas;
- relacionar commits/arquivos às fontes declaradas no baseline do painel;
- analisar sintaxe, notebooks, conflitos, riscos de segredo, performance e vazamento;
- executar testes rápidos, locais e sem rede, salvo --no-tests;
- atualizar tarefas somente de forma conservadora:
    * [done...] -> CONCLUÍDA;
    * evidência provável + auditoria sem bloqueio -> RESOLVIDA — PENDENTE DE VALIDAÇÃO;
    * evidência provável + problema impeditivo -> PRECISA REVISÃO;
- nunca reabrir automaticamente uma tarefa concluída;
- nunca acessar Parquet, modelos, predições, dados brutos ou o holdout;
- compartilhar apenas PROJECT_STATUS.md. O relatório detalhado fica local.

Uso, na raiz do projeto:
    .\.venv\Scripts\python.exe tools\deep_git_project_audit.py
    .\.venv\Scripts\python.exe tools\deep_git_project_audit.py --dry-run
    .\.venv\Scripts\python.exe tools\deep_git_project_audit.py --no-tests
    .\.venv\Scripts\python.exe tools\deep_git_project_audit.py --since-commit SHA
"""

import argparse
import ast
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

SCHEMA_VERSION = 1
STATUS_BLOCK = re.compile(
    r"<!--\s*PROJECT_STATUS_DATA\s*\r?\n(.*?)\r?\nPROJECT_STATUS_DATA\s*-->",
    re.S,
)
EXPLICIT_MARKER = re.compile(
    r"\[(done|progress|reopen):(?:(?:id)?#?)?(\d+)\]",
    re.I,
)
TASK_REFERENCE = re.compile(
    r"(?<![\wÀ-ÿ])tarefa\s+#?0*(\d+)(?!\d)",
    re.I,
)
COMPLETION_LANGUAGE = re.compile(
    r"(?i)\b(corrig(?:e|ido|ida|ir)|implement(?:a|ado|ada|ar)|resolv(?:e|ido|ida|er)|"
    r"conclu(?:i|ído|ída|ir)|finaliz(?:a|ado|ada|ar)|fecha(?:do|da|r)|entreg(?:a|ue|ado|ada))\b"
)
MERGE_CONFLICT = re.compile(r"^(<{7}|={7}|>{7})", re.M)
TODO = re.compile(r"(?i)\b(TODO|FIXME|XXX|HACK|PENDENTE)\b[:\s-]*(.{0,160})")
SECRET = re.compile(
    r"(?i)(password|passwd|pwd|secret|token|api[_-]?key|private[_-]?key)"
    r"\s*[:=]\s*['\"]([^'\"\n]{8,})['\"]"
)
PRIVATE_KEY = re.compile(r"-----BEGIN [^-]+ PRIVATE KEY-----", re.I)
ABSOLUTE_PATH = re.compile(r"(?i)\b[A-Z]:[\\/]Users[\\/][^\\/\s]+|/(?:home|Users)/[^/\s]+")

TEXT_SUFFIXES = {
    ".py", ".pyi", ".ipynb", ".md", ".rst", ".txt", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".json", ".sql", ".ps1", ".psm1", ".sh",
    ".bat", ".cmd", ".csv", ".tsv", ".html", ".css", ".js", ".r",
}
BINARY_OR_DATA_SUFFIXES = {
    ".parquet", ".feather", ".arrow", ".pkl", ".pickle", ".joblib", ".onnx",
    ".pt", ".pth", ".h5", ".hdf5", ".npy", ".npz", ".pdf", ".doc", ".docx",
    ".ppt", ".pptx", ".xls", ".xlsx", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".zip", ".7z", ".gz", ".tar", ".db", ".sqlite",
}
EXCLUDED_PARTS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".tox", ".nox", "node_modules", "site-packages", "dist", "build",
    ".ipynb_checkpoints",
}
DATA_ROOTS = {"data", "outputs", "models", "artifacts", "mlruns", "predictions", "predicoes"}
STATUS_LABELS = {
    "open": "ABERTA",
    "in_progress": "EM ANDAMENTO",
    "resolved_pending_validation": "RESOLVIDA — PENDENTE DE VALIDAÇÃO",
    "implemented_unconfirmed": "RESOLVIDA — PENDENTE DE VALIDAÇÃO",
    "needs_review": "PRECISA REVISÃO",
    "done": "CONCLUÍDA",
}
STATUS_ICONS = {
    "open": "⬜",
    "in_progress": "🟦",
    "resolved_pending_validation": "🟪",
    "implemented_unconfirmed": "🟪",
    "needs_review": "🟨",
    "done": "✅",
}

PERFORMANCE_RULES: list[tuple[str, re.Pattern[str], str, str]] = [
    ("dense-one-hot", re.compile(r"sparse_output\s*=\s*False"), "high", "OneHotEncoder denso pode causar explosão de memória."),
    ("toarray", re.compile(r"\.toarray\s*\("), "high", "Conversão explícita de matriz esparsa para densa."),
    ("iterrows", re.compile(r"\.iterrows\s*\("), "medium", "iterrows em dados tabulares grandes tende a ser lento."),
    ("apply-axis-1", re.compile(r"\.apply\s*\([^\n]*axis\s*=\s*1"), "medium", "apply(axis=1) tende a ser lento em milhões de linhas."),
    ("deep-copy", re.compile(r"\.copy\s*\(\s*(?:deep\s*=\s*True)?\s*\)"), "low", "Cópia potencialmente profunda; revisar impacto de memória."),
    ("read-parquet-wide", re.compile(r"read_parquet\s*\((?![^\)]*columns\s*=)"), "medium", "Leitura Parquet sem projeção explícita de colunas."),
    ("groupby-observed", re.compile(r"\.groupby\s*\((?![^\)]*observed\s*=)"), "low", "groupby sem observed explícito pode gerar combinações categóricas vazias."),
    ("unbounded-concat-loop", re.compile(r"for\s+.+:\s*(?:\n[^\n]*){0,5}\n[^\n]*pd\.concat\s*\("), "medium", "pd.concat dentro de loop pode ter custo quadrático."),
]

LEAKAGE_NAME_HINTS = {
    "evolucao", "evolucao_categoria", "alvo_obito_srag", "obito", "dt_evoluca",
    "uti", "suport_ven", "hospitaliz", "dt_saida", "encerramento", "classi_fin",
}


@dataclass
class Finding:
    severity: str
    category: str
    message: str
    evidence: list[str] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)
    commits: list[str] = field(default_factory=list)
    task_ids: list[str] = field(default_factory=list)


@dataclass
class CommitRecord:
    sha: str
    when: str
    author: str
    subject: str
    body: str
    parents: list[str]
    files: list[str] = field(default_factory=list)
    explicit: list[tuple[str, str]] = field(default_factory=list)
    task_mentions: list[str] = field(default_factory=list)


class AuditError(RuntimeError):
    pass


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_id(value: str) -> str:
    stripped = value.lstrip("0")
    return stripped or "0"


def run(args: list[str], root: Path, timeout: int = 120, check: bool = False) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            args,
            cwd=root,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        return subprocess.CompletedProcess(args, 124, stdout, "timeout")
    if check and result.returncode:
        raise AuditError(result.stderr.strip() or result.stdout.strip() or "Command failed")
    return result


def git(root: Path, *args: str, timeout: int = 120, check: bool = False) -> subprocess.CompletedProcess[str]:
    return run(["git", "-c", "core.quotepath=false", *args], root, timeout, check)


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise AuditError("Execute dentro do repositório Git.")
    return Path(result.stdout.strip()).resolve()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="strict")


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=path.parent) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def load_status(path: Path) -> tuple[str, dict[str, Any]]:
    if not path.exists():
        raise AuditError(f"Arquivo obrigatório ausente: {path}")
    text = read_text(path)
    match = STATUS_BLOCK.search(text)
    if not match:
        raise AuditError("PROJECT_STATUS.md não contém um bloco PROJECT_STATUS_DATA válido.")
    try:
        state = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise AuditError(f"JSON oculto inválido em PROJECT_STATUS.md: {exc}") from exc
    if not isinstance(state.get("items"), dict):
        raise AuditError("O estado oculto não contém o dicionário items.")
    return text, state


def load_definitions(root: Path) -> dict[str, dict[str, Any]]:
    baseline = root / ".srag-status-local" / "baseline.json"
    if not baseline.exists():
        return {}
    raw = json.loads(read_text(baseline))
    definitions = {}
    for key, value in raw.get("items", {}).items():
        definitions[str(key)] = value.get("definition", {})
    return definitions


def parse_commit_history(root: Path, since_commit: str | None) -> list[CommitRecord]:
    fmt = "%H%x1f%aI%x1f%an%x1f%P%x1f%s%x1f%b%x1e"
    args = ["log", "--all", "--reverse", f"--format={fmt}"]
    if since_commit:
        args.extend(["--not", since_commit])
    result = git(root, *args, timeout=300, check=True)
    records: list[CommitRecord] = []
    for raw in result.stdout.split("\x1e"):
        raw = raw.strip("\r\n")
        if not raw:
            continue
        parts = raw.split("\x1f", 5)
        if len(parts) != 6:
            continue
        sha, when, author, parents_raw, subject, body = parts
        message = f"{subject}\n{body}"
        explicit = [(action.lower(), normalize_id(item)) for action, item in EXPLICIT_MARKER.findall(message)]
        mentions = sorted({normalize_id(value) for value in TASK_REFERENCE.findall(message)}, key=int)
        files_result = git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "-m", sha, timeout=60)
        files = sorted({line.strip() for line in files_result.stdout.splitlines() if line.strip()})
        records.append(
            CommitRecord(
                sha=sha,
                when=when,
                author=author,
                subject=subject.strip(),
                body=body.strip(),
                parents=parents_raw.split(),
                files=files,
                explicit=explicit,
                task_mentions=mentions,
            )
        )
    return records


def source_tokens(definition: dict[str, Any]) -> list[str]:
    source = str(definition.get("source", "")).replace("\\", "/")
    tokens = []
    for part in source.split(";"):
        cleaned = re.sub(r"\s*\([^)]*\).*", "", part).strip(" .")
        name = Path(cleaned).name.lower()
        if len(name) > 3 and not any(word in name for word in ("projeto", "reunião", "orientação", "plano")):
            tokens.append(name)
    return sorted(set(tokens))


def task_files(definition: dict[str, Any], paths: Iterable[str]) -> list[str]:
    tokens = source_tokens(definition)
    return sorted({path for path in paths if any(token in Path(path).name.lower() or token in path.lower() for token in tokens)})


def tracked_text_files(root: Path) -> list[Path]:
    result = git(root, "ls-files", "-co", "--exclude-standard", check=True)
    output = []
    for rel in result.stdout.splitlines():
        path = Path(rel)
        if not rel or any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if path.parts and path.parts[0] in DATA_ROOTS:
            continue
        if path.suffix.lower() in BINARY_OR_DATA_SUFFIXES:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"README", "LICENSE", "Makefile", "Dockerfile"}:
            continue
        absolute = root / path
        if absolute.is_file():
            output.append(path)
    return sorted(set(output), key=lambda value: value.as_posix().lower())


def scan_file(root: Path, relative: Path) -> list[Finding]:
    path = root / relative
    rel = relative.as_posix()
    findings: list[Finding] = []
    try:
        text = read_text(path)
    except Exception as exc:
        return [Finding("high", "encoding", f"Falha ao ler {rel} como UTF-8: {exc}", paths=[rel])]
    if MERGE_CONFLICT.search(text):
        findings.append(Finding("high", "merge-conflict", "Marcadores de conflito Git encontrados.", paths=[rel]))
    if PRIVATE_KEY.search(text):
        findings.append(Finding("critical", "secret", "Possível chave privada no repositório.", paths=[rel]))
    for match in SECRET.finditer(text):
        findings.append(Finding("critical", "secret", f"Possível segredo atribuído à chave {match.group(1)}.", paths=[rel]))
    for match in ABSOLUTE_PATH.finditer(text):
        findings.append(Finding("medium", "absolute-path", "Caminho local absoluto encontrado.", evidence=[match.group(0)[:180]], paths=[rel]))
    todo_matches = TODO.findall(text)
    if todo_matches:
        findings.append(Finding("low", "todo", f"Arquivo contém {len(todo_matches)} marcador(es) TODO/FIXME/PENDENTE.", evidence=[f"{a}: {b}" for a, b in todo_matches[:10]], paths=[rel]))
    for category, pattern, severity, message in PERFORMANCE_RULES:
        matches = list(pattern.finditer(text))
        if matches:
            lines = [str(text.count("\n", 0, match.start()) + 1) for match in matches[:20]]
            findings.append(Finding(severity, f"performance-{category}", message, evidence=[f"linhas: {', '.join(lines)}"], paths=[rel]))

    suffix = relative.suffix.lower()
    if suffix in {".py", ".pyi"}:
        try:
            ast.parse(text, filename=rel)
        except SyntaxError as exc:
            findings.append(Finding("high", "python-syntax", f"Erro de sintaxe Python: {exc}", paths=[rel]))
    elif suffix == ".ipynb":
        try:
            notebook = json.loads(text)
            counts: list[int] = []
            saved_errors = []
            parse_errors = []
            for index, cell in enumerate(notebook.get("cells", []), 1):
                if cell.get("cell_type") != "code":
                    continue
                count = cell.get("execution_count")
                if isinstance(count, int):
                    counts.append(count)
                source = "".join(cell.get("source", []))
                source = "\n".join("# " + line if line.lstrip().startswith(("%", "!", "?")) else line for line in source.splitlines())
                if source.strip():
                    try:
                        ast.parse(source, filename=f"{rel}:cell-{index}")
                    except SyntaxError as exc:
                        parse_errors.append(f"célula {index}: {exc}")
                for output in cell.get("outputs", []):
                    if output.get("output_type") == "error":
                        saved_errors.append(f"célula {index}: {output.get('ename')}: {output.get('evalue')}")
            if any(next_count < count for count, next_count in zip(counts, counts[1:])):
                findings.append(Finding("medium", "notebook-order", "Notebook salvo com contagens de execução fora de ordem.", paths=[rel]))
            if saved_errors:
                findings.append(Finding("high", "notebook-saved-error", "Notebook contém saídas de erro salvas.", evidence=saved_errors[:20], paths=[rel]))
            if parse_errors:
                findings.append(Finding("high", "notebook-syntax", "Células do notebook não puderam ser analisadas.", evidence=parse_errors[:20], paths=[rel]))
        except Exception as exc:
            findings.append(Finding("high", "notebook-json", f"Notebook inválido: {exc}", paths=[rel]))
    elif suffix == ".json":
        try:
            json.loads(text)
        except Exception as exc:
            findings.append(Finding("high", "json-invalid", f"JSON inválido: {exc}", paths=[rel]))
    elif suffix in {".yaml", ".yml"} and yaml is not None:
        try:
            yaml.safe_load(text)
        except Exception as exc:
            findings.append(Finding("high", "yaml-invalid", f"YAML inválido: {exc}", paths=[rel]))
    return findings


def scan_config_leakage(root: Path) -> list[Finding]:
    config_path = root / "configs" / "supervised.yaml"
    if not config_path.exists() or yaml is None:
        return []
    try:
        config = yaml.safe_load(read_text(config_path)) or {}
    except Exception:
        return []
    features = config.get("features", {}) if isinstance(config, dict) else {}
    configured: list[str] = []
    for key in ("final", "numericas", "categoricas"):
        value = features.get(key, []) if isinstance(features, dict) else []
        if isinstance(value, list):
            configured.extend(str(item) for item in value)
    suspects = sorted({name for name in configured if any(hint in name.lower() for hint in LEAKAGE_NAME_HINTS)})
    if not suspects:
        return []
    return [
        Finding(
            "critical",
            "possible-temporal-leakage",
            "Features configuradas têm nomes associados a desfecho ou informação potencialmente posterior à internação. Exige revisão humana; o scanner não conclui temporalidade apenas pelo nome.",
            evidence=suspects,
            paths=["configs/supervised.yaml"],
        )
    ]


def run_tests(root: Path, timeout: int) -> tuple[Finding | None, dict[str, Any]]:
    args = [sys.executable, "-m", "pytest", "-q", "-m", "not slow and not net", "--maxfail=1"]
    result = run(args, root, timeout=timeout)
    detail = (result.stdout + "\n" + result.stderr).strip()[-6000:]
    record = {"command": args[1:], "returncode": result.returncode, "detail": detail}
    if result.returncode == 0:
        return None, record
    severity = "medium" if result.returncode == 5 else "high"
    return Finding(severity, "pytest", f"pytest rápido retornou código {result.returncode}.", evidence=[detail[-1800:]]), record


def severity_rank(value: str) -> int:
    return {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(value, 0)


def relate_findings_to_tasks(findings: list[Finding], definitions: dict[str, dict[str, Any]]) -> None:
    for finding in findings:
        for task_id, definition in definitions.items():
            if task_files(definition, finding.paths):
                finding.task_ids.append(task_id)
        finding.task_ids = sorted(set(finding.task_ids), key=int)


def summarize_task_evidence(
    commits: list[CommitRecord],
    definitions: dict[str, dict[str, Any]],
    existing_items: dict[str, Any],
    findings: list[Finding],
) -> dict[str, dict[str, Any]]:
    evidence: dict[str, dict[str, Any]] = {
        task_id: {"explicit": [], "mentions": [], "source_commits": [], "findings": []}
        for task_id in existing_items
    }
    for commit in commits:
        explicit_ids = set()
        for action, task_id in commit.explicit:
            if task_id in evidence:
                evidence[task_id]["explicit"].append({"action": action, "commit": commit.sha, "when": commit.when, "author": commit.author, "subject": commit.subject})
                explicit_ids.add(task_id)
        for task_id in commit.task_mentions:
            if task_id in evidence and task_id not in explicit_ids:
                evidence[task_id]["mentions"].append({"commit": commit.sha, "when": commit.when, "author": commit.author, "subject": commit.subject})
        for task_id, definition in definitions.items():
            if task_id in evidence:
                hits = task_files(definition, commit.files)
                if hits and COMPLETION_LANGUAGE.search(f"{commit.subject}\n{commit.body}"):
                    evidence[task_id]["source_commits"].append({"commit": commit.sha, "when": commit.when, "author": commit.author, "subject": commit.subject, "files": hits})
    for index, finding in enumerate(findings):
        for task_id in finding.task_ids:
            if task_id in evidence:
                evidence[task_id]["findings"].append(index)
    return evidence


def update_state(
    state: dict[str, Any],
    evidence: dict[str, dict[str, Any]],
    findings: list[Finding],
    tests_ok: bool,
    head: str,
) -> list[str]:
    changes: list[str] = []
    for task_id, item in state["items"].items():
        item.setdefault("id", task_id)
        item.setdefault("evidence", [])
        item.setdefault("comments", [])
        ev = evidence.get(task_id, {})
        explicit = ev.get("explicit", [])
        mentions = ev.get("mentions", [])
        sources = ev.get("source_commits", [])
        related_findings = [findings[index] for index in ev.get("findings", [])]

        for marker in explicit:
            if marker["action"] == "done":
                if item.get("status") != "done" or not item.get("done"):
                    changes.append(f"#{task_id}: marcador explícito de conclusão encontrado")
                item["status"] = "done"
                item["done"] = True
                item["updated_at"] = marker["when"]
                item["updated_by"] = marker["author"]
                item["note"] = f"Commit {marker['commit'][:12]}: {marker['subject']}"
            elif marker["action"] == "reopen":
                item["status"] = "open"
                item["done"] = False
                item["updated_at"] = marker["when"]
                item["updated_by"] = marker["author"]
                item["note"] = f"Commit {marker['commit'][:12]}: {marker['subject']}"
                changes.append(f"#{task_id}: reabertura explícita encontrada")
            elif marker["action"] == "progress" and not item.get("done"):
                item["status"] = "in_progress"
                item["updated_at"] = marker["when"]
                item["updated_by"] = marker["author"]
                item["note"] = f"Commit {marker['commit'][:12]}: {marker['subject']}"
                changes.append(f"#{task_id}: progresso explícito encontrado")
            item["evidence"].append({"type": "commit_marker", **marker})

        if item.get("done"):
            item["evidence"] = item["evidence"][-40:]
            continue

        candidate = bool(mentions or sources)
        if not candidate:
            continue
        blocking = any(severity_rank(finding.severity) >= 3 for finding in related_findings)
        if blocking or not tests_ok:
            new_status = "needs_review"
            message = "Evidência de implementação encontrada, mas há problema impeditivo ou teste rápido não aprovado."
        else:
            new_status = "resolved_pending_validation"
            message = "Evidência de implementação encontrada e verificações automáticas sem bloqueio. Confirmar manualmente."
        if item.get("status") != new_status:
            changes.append(f"#{task_id}: {STATUS_LABELS.get(new_status, new_status)}")
        item["status"] = new_status
        item["done"] = False
        latest = (mentions + sources)[-1]
        item["updated_at"] = latest["when"]
        item["updated_by"] = "auditoria profunda automática"
        item["note"] = message
        for record in mentions[-8:]:
            item["evidence"].append({"type": "commit_task_reference", **record})
        for record in sources[-8:]:
            item["evidence"].append({"type": "commit_source_match", **record})
        for finding in related_findings[-12:]:
            item["evidence"].append({"type": "audit_finding", "severity": finding.severity, "category": finding.category, "message": finding.message, "paths": finding.paths})
        item["evidence"] = item["evidence"][-40:]

    state["schema_version"] = max(int(state.get("schema_version", 1)), 2)
    state["generated_at"] = utc_now()
    state["last_scanned_commit"] = head
    state["deep_audit"] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": state["generated_at"],
        "head": head,
        "findings": Counter(finding.severity for finding in findings),
        "tests_ok": tests_ok,
    }
    return changes


def replace_visible_task_statuses(text: str, state: dict[str, Any]) -> str:
    for task_id, item in state["items"].items():
        label = STATUS_LABELS.get(item.get("status", "open"), item.get("status", "open"))
        icon = STATUS_ICONS.get(item.get("status", "open"), "⬜")
        pattern = re.compile(rf"(?m)^-\s+[⬜🟦🟪🟨✅]\s+\*\*#{re.escape(task_id)}\*\*(.*?)\s+—\s+[^·\n]+(\s+·.*)$")
        text = pattern.sub(lambda match: f"- {icon} **#{task_id}**{match.group(1)} — {label}{match.group(2)}", text)
    counts = Counter(item.get("status", "open") for item in state["items"].values())
    replacements = {
        r"(?m)^- Concluídas: \*\*\d+\*\*$": f"- Concluídas: **{counts['done']}**",
        r"(?m)^- Resolvidas pendentes de validação: \*\*\d+\*\*$": f"- Resolvidas pendentes de validação: **{counts['resolved_pending_validation'] + counts['implemented_unconfirmed']}**",
        r"(?m)^- Precisam revisão: \*\*\d+\*\*$": f"- Precisam revisão: **{counts['needs_review']}**",
        r"(?m)^- Em andamento: \*\*\d+\*\*$": f"- Em andamento: **{counts['in_progress']}**",
        r"(?m)^- Abertas: \*\*\d+\*\*$": f"- Abertas: **{counts['open']}**",
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"(?m)^> Atualizado em .*\.$", f"> Atualizado em {state['generated_at']}.", text)
    return text


def render_status(text: str, state: dict[str, Any]) -> str:
    visible = replace_visible_task_statuses(text, state)
    payload = json.dumps(state, ensure_ascii=False, separators=(",", ":"), default=str)
    replacement = f"<!-- PROJECT_STATUS_DATA\n{payload}\nPROJECT_STATUS_DATA -->"
    return STATUS_BLOCK.sub(replacement, visible, count=1)


def write_local_report(root: Path, commits: list[CommitRecord], findings: list[Finding], changes: list[str], tests: dict[str, Any]) -> Path:
    report_dir = root / ".srag-status-local"
    report_dir.mkdir(exist_ok=True)
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "commits_scanned": len(commits),
        "findings": [asdict(finding) for finding in findings],
        "status_changes": changes,
        "tests": tests,
    }
    path = report_dir / "deep_git_audit_report.json"
    atomic_write(path, json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n")
    return path


def backup_status(root: Path, status_path: Path) -> Path:
    backup_dir = root / ".srag-status-local" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    backup = backup_dir / f"PROJECT_STATUS_before_deep_audit_{stamp}.md"
    backup.write_bytes(status_path.read_bytes())
    return backup


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audita profundamente o Git e atualiza PROJECT_STATUS.md de forma conservadora.")
    parser.add_argument("--dry-run", action="store_true", help="Não altera PROJECT_STATUS.md.")
    parser.add_argument("--no-tests", action="store_true", help="Não executa pytest rápido.")
    parser.add_argument("--test-timeout", type=int, default=300, help="Timeout do pytest rápido em segundos.")
    parser.add_argument("--since-commit", help="Limita a análise histórica a commits posteriores a este SHA.")
    parser.add_argument("--fail-on-high", action="store_true", help="Retorna código 2 se houver achado HIGH ou CRITICAL.")
    return parser.parse_args()


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            reconfigure = getattr(stream, "reconfigure", None)
            if callable(reconfigure):
                reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    args = parse_args()
    root = repo_root()
    status_path = root / "PROJECT_STATUS.md"
    print("[auditoria] 1/7 Lendo estado compartilhado e definições...")
    original_text, state = load_status(status_path)
    definitions = load_definitions(root)

    print("[auditoria] 2/7 Percorrendo histórico Git em todas as refs...")
    commits = parse_commit_history(root, args.since_commit)
    print(f"[auditoria] {len(commits)} commit(s) analisado(s).")

    print("[auditoria] 3/7 Analisando arquivos textuais atuais...")
    files = tracked_text_files(root)
    findings: list[Finding] = []
    for index, relative in enumerate(files, 1):
        if index == 1 or index % 25 == 0 or index == len(files):
            print(f"[auditoria] arquivo {index}/{len(files)}: {relative.as_posix()}")
        findings.extend(scan_file(root, relative))
    findings.extend(scan_config_leakage(root))

    print("[auditoria] 4/7 Relacionando achados às tarefas...")
    relate_findings_to_tasks(findings, definitions)

    tests_record: dict[str, Any] = {"executed": False, "ok": True}
    if not args.no_tests:
        print("[auditoria] 5/7 Executando pytest rápido, sem slow e sem net...")
        test_finding, raw_test = run_tests(root, args.test_timeout)
        tests_record = {"executed": True, "ok": test_finding is None, **raw_test}
        if test_finding:
            findings.append(test_finding)
    else:
        print("[auditoria] 5/7 Testes desativados por --no-tests.")

    print("[auditoria] 6/7 Inferindo progresso conservador...")
    evidence = summarize_task_evidence(commits, definitions, state["items"], findings)
    head_result = git(root, "rev-parse", "HEAD", check=True)
    head = head_result.stdout.strip()
    changes = update_state(state, evidence, findings, bool(tests_record.get("ok")), head)
    report_path = write_local_report(root, commits, findings, changes, tests_record)

    if args.dry_run:
        print("[auditoria] 7/7 Dry-run: PROJECT_STATUS.md não foi alterado.")
    else:
        print("[auditoria] 7/7 Gravando PROJECT_STATUS.md com backup e escrita atômica...")
        backup = backup_status(root, status_path)
        atomic_write(status_path, render_status(original_text, state))
        print(f"Backup local: {backup.relative_to(root)}")

    counts = Counter(finding.severity for finding in findings)
    print(f"Relatório local: {report_path.relative_to(root)}")
    print(f"Achados: critical={counts['critical']}, high={counts['high']}, medium={counts['medium']}, low={counts['low']}")
    print(f"Mudanças de status propostas/aplicadas: {len(changes)}")
    for change in changes[:40]:
        print(f"- {change}")
    print("Arquivo compartilhado alterado: PROJECT_STATUS.md" if not args.dry_run else "Nenhum arquivo compartilhado alterado.")
    if args.fail_on_high and (counts["critical"] or counts["high"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
