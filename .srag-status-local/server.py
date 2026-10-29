#!/usr/bin/env python3
"""Painel de Pendências SRAG — serviço local (v6).

Commits: só concluir, reabrir, comentar, confirmar/rejeitar sugestão, escolher em conflito, editar conteúdo pelo
painel e mudanças de pendência achadas pela auditoria. Buscar nunca gera commit. Mensagem: "(#status) #10 concluída · Mateus".

Novidade da v5 — conteúdo em texto:
- Todo o texto do painel (itens, seções, metadados, cronograma, ajuda…) vive em PROJECT_STATUS_TEXT.md, na raiz do repositório.
  É Markdown legível e editável no VS Code ou pelo editor do painel (campo a campo, com o mesmo merge da situação).
- O serviço converte o PROJECT_STATUS_TEXT.md em HTML e grava o resultado DENTRO do painel.html (região delimitada por
  marcadores). Só regrava quando o hash do conteúdo muda; o navegador aberto recebe apenas os itens alterados.
- Edições salvas no PROJECT_STATUS_TEXT.md da pasta aparecem em ~2 s como prévia local (merge de 3 vias com o remoto).

Novidades da v6:
- "④ Pronto quando" em cada pendência, conferido pelo verificador (deep_git_project_audit.py). Marcar como concluída
  uma pendência que o verificador não confirma exige um comentário.
- Seção REVISÕES no painel: detectadas como concluídas, ainda pendentes, reconfirmações, testes que falharam,
  mudanças na configuração crítica e referência para IAs desatualizada.
- Só menção explícita em commit muda situação; commit que só mexe nos arquivos de uma tarefa é informação no card.
- Proteção contra regressão: o painel se recusa a publicar um estado que perca itens, comentários, rejeições,
  histórico ou que mude situações sem motivo. Nunca republica do zero.
- Commits agrupados por tipo, cada #ID uma vez: "(#status) conteúdo: #1, #31; comentário: #5 +12 · Mateus".
- Publicação ~12 s depois do último clique. O painel se recusa a rodar fora da pasta .srag-status-local do repositório.

Princípios:
- O que é compartilhado: PROJECT_STATUS.md (situação) e PROJECT_STATUS_TEXT.md (conteúdo), publicados na branch de status
  (padrão: a branch principal do origin).
- O painel NUNCA escreve PROJECT_STATUS.md no seu working tree. Ele lê o arquivo direto de origin/<branch>
  e publica criando o commit "por fora" (plumbing do Git com índice temporário). Por isso o VS Code nunca vê o
  arquivo como modificado e o pull nunca reclama.
- Alterações humanas viram eventos (fila local outbox.json). Na publicação, os eventos são reaplicados sobre a
  versão MAIS RECENTE do remoto, campo a campo. Duas pessoas editando itens/campos diferentes nunca conflitam.
  Mesmo campo alterado por duas pessoas: vale o que chegou primeiro e o segundo recebe um aviso para decidir.
- Push rejeitado (alguém publicou antes) => busca de novo, reaplica e tenta outra vez. Nunca usa --force.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import http.server
import importlib.util
import json
import os
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid
import webbrowser
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

VERSION = "6.2.0"
LOCAL = Path(__file__).resolve().parent
MD_NAME = "PROJECT_STATUS.md"
BASE = LOCAL / "baseline.json"
LEGACY_CACHE = LOCAL / "cache.json"
STATE_CACHE = LOCAL / "estado_remoto.json"
OUTBOX = LOCAL / "outbox.json"
CONFLICTS = LOCAL / "conflitos.json"
CONFIG = LOCAL / "config.json"
REPORT = LOCAL / "deep_git_audit_report.json"
REPORT_QUICK = LOCAL / "verificacao_rapida.json"
AUDIT_SCRIPT = LOCAL / "deep_git_project_audit.py"
BACKUPS = LOCAL / "backups"
LOGS = LOCAL / "logs"
HTML = "painel.html"                 # modelo versionado no Git (nunca é regravado pelo serviço)
GENERATED = LOCAL / "painel_gerado.html"  # cópia local com o conteúdo embutido (ignorada pelo Git); é o que o navegador recebe
CONTENT_CACHE = LOCAL / "conteudo_remoto.md"
sys.path.insert(0, str(LOCAL))
import project_status_text as pm  # noqa: E402  (módulo ao lado do server.py)

DEFAULT_CONFIG = {
    "remote": "origin",
    "branch": "",                 # vazio = detecta a branch principal do remoto (origin/HEAD)
    "port": 8765,
    "fetch_interval_minutes": 60,
    "publish_delay_seconds": 12,  # agrupa cliques próximos em um único commit
    "commit_scan_limit": 500,
    "auto_ff_status_only": True,  # avança sua branch local quando o ÚNICO arquivo novo no remoto é o PROJECT_STATUS.md
    "pytest_timeout_seconds": 900,
    "content_file": "PROJECT_STATUS_TEXT.md",  # fonte do conteúdo do painel, na raiz do repositório
    "watch_seconds": 2,               # intervalo da checagem (só stat) do PROJECT_STATUS_TEXT.md e do índice do Git
}
STATUSES = ("open", "in_progress", "resolved_pending_validation", "needs_review", "done")
STATUS_LABELS = {
    "open": "ABERTA",
    "in_progress": "EM ANDAMENTO",
    "resolved_pending_validation": "RESOLVIDA — PENDENTE DE VALIDAÇÃO",
    "needs_review": "PRECISA REVISÃO",
    "done": "CONCLUÍDA",
}
STATUS_ICONS = {"open": "⬜", "in_progress": "🟦", "resolved_pending_validation": "🟪", "needs_review": "🟨", "done": "✅"}
SHORT = {"open": "reaberta", "in_progress": "em andamento", "resolved_pending_validation": "a confirmar",
         "needs_review": "revisar", "done": "concluída"}
CATEGORY_PT = {"notebook-saved-error": "notebook com erro salvo", "notebook-syntax": "sintaxe no notebook",
               "notebook-json": "notebook inválido", "python-syntax": "sintaxe Python", "json-invalid": "JSON inválido",
               "yaml-invalid": "YAML inválido", "merge-conflict": "marcas de conflito", "pytest": "teste falhando",
               "secret": "possível segredo", "possible-temporal-leakage": "possível vazamento", "encoding": "codificação",
               "performance-dense-one-hot": "one-hot denso", "performance-toarray": "conversão densa"}
COMMIT_PREFIX = "(#status)"
SCAN_SINCE_DEFAULT = "2026-10-28T00:00:00Z"   # commits mais antigos que isto nunca mudam situação (já foram avaliados)
VERDICT_PT = {"atendida": "atendidas", "nao_atendida": "não atendidas", "revisar_por_teste": "revisar por teste",
              "indisponivel_nesta_maquina": "indisponíveis nesta máquina", "depende_de_confirmacao_manual": "dependem de confirmação manual",
              "criterio_invalido": "com critério inválido", "sem_criterios": "sem critérios"}
AUTO_ACTORS = ("verificação automática", "auditoria profunda automática", "auditoria", "varredura de commits", "baseline",
               "verificador automático")

# ---- reconhecimento de tarefas nos commits ----
TAG = re.compile(r"\[(done|progress|reopen|feito|conclu[ií]d[oa]|andamento|reabr[ei]r?)\s*[:#]\s*(?:id)?#?\s*0*(\d+)\]", re.I)
REF_WORD = re.compile(
    r"(?<![\wÀ-ÿ])(?:tarefas?|tasks?|itens?|item|pend[eê]ncias?|cards?|issues?)\s*(?:n[ºo°.]\s*)?#?\s*"
    r"(\d{1,4}(?:\s*(?:,|e|and|&|/|\+)\s*#?\s*\d{1,4})*)",
    re.I,
)
REF_HASH = re.compile(r"(?<![\w/&])#(\d{1,4})\b")
PULL_REQUEST = re.compile(r"(?i)pull\s+request\s+#\d+")
COMPLETION = re.compile(
    r"(?i)\b(corrig\w*|implement\w*|resolv\w*|conclu\w*|finaliz\w*|fecha\w*|fech[ao]u?|entreg\w*|feit[oa]|pront[oa]|"
    r"done|fix(?:ed|es)?|close[sd]?|complet\w*|ok)\b"
)
STATUS_FROM_TAG = {"done": "done", "feito": "done", "concluido": "done", "concluída": "done", "concluído": "done", "concluida": "done",
                   "progress": "in_progress", "andamento": "in_progress", "reopen": "open", "reabrir": "open", "reabre": "open"}

LOCK = threading.RLock()
JOB_LOCK = threading.Lock()
PUBLISH_TIMER: threading.Timer | None = None
META: dict[str, Any] = {"last_fetch": None, "last_fetch_ok": None, "last_publish": None, "last_error": None,
                        "last_message": "Iniciando…", "mode": "normal", "root": None, "branch": None, "tip": None}
JOB: dict[str, Any] = {"id": None, "running": False, "kind": None, "log": [], "result": None, "error": None,
                       "started": None, "finished": None}
SHUTDOWN = threading.Event()


# =============================================================== utilitários
def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def log(msg: str) -> None:
    line = f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    try:
        print(line, flush=True)
    except Exception:
        pass
    try:
        LOGS.mkdir(exist_ok=True)
        path = LOGS / "painel.log"
        if path.exists() and path.stat().st_size > 2_000_000:
            os.replace(path, LOGS / "painel.old.log")
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def load_config() -> dict[str, Any]:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG.exists():
        try:
            cfg.update(json.loads(CONFIG.read_text(encoding="utf-8-sig")))
        except Exception as exc:
            log(f"config.json inválido, usando padrões: {exc}")
    return cfg


CFG = load_config()
CFG["publish_delay_seconds"] = max(12, float(CFG.get("publish_delay_seconds") or 12))
CONTENT_NAME = str(CFG.get("content_file") or "PROJECT_STATUS_TEXT.md")
if CONTENT_NAME in pm.LEGACY_CONTENT_FILES:  # config.json da v5.0 ainda aponta para o nome antigo
    CONTENT_NAME = pm.CONTENT_FILE
LEGACY_CONTENT = tuple(n for n in pm.LEGACY_CONTENT_FILES if n != CONTENT_NAME)
PANEL_FILES = {MD_NAME, CONTENT_NAME, *LEGACY_CONTENT}
SEED = LOCAL / "PROJECT_STATUS_TEXT.inicial.md"  # conteúdo inicial distribuído no zip (publicado se o GitHub ainda não tiver)


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return default
    except Exception as exc:
        log(f"Falha ao ler {path.name}: {exc}; preservando cópia.")
        try:
            BACKUPS.mkdir(exist_ok=True)
            shutil.copy2(path, BACKUPS / f"{path.stem}_ilegivel_{int(time.time())}{path.suffix}")
        except Exception:
            pass
        return default


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    os.replace(tmp, path)


def write_json(path: Path, value: Any) -> None:
    atomic_write(path, json.dumps(value, ensure_ascii=False, indent=1, default=str))


def git_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    # credenciais vêm do Git Credential Manager, exatamente como no VS Code
    if extra:
        env.update(extra)
    return env


def git(*args: str, input_text: str | None = None, env: dict[str, str] | None = None, timeout: int = 90,
        cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(["git", *args], cwd=cwd or ROOT, input=input_text, text=True, capture_output=True,
                              encoding="utf-8", errors="replace", timeout=timeout, env=git_env(env))
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(["git", *args], 124, str(exc.stdout or ""), "timeout")
    except FileNotFoundError:
        return subprocess.CompletedProcess(["git", *args], 127, "", "git não encontrado no PATH")


def detail(p: subprocess.CompletedProcess[str], limit: int = 1500) -> str:
    return ((p.stdout or "") + "\n" + (p.stderr or "")).strip()[-limit:]


def find_root() -> Path:
    p = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=LOCAL, text=True, capture_output=True,
                       encoding="utf-8", errors="replace") \
        if shutil.which("git") else None
    if p is not None and p.returncode == 0 and p.stdout.strip():
        return Path(p.stdout.strip()).resolve()
    return LOCAL.parent


ROOT = find_root()
META["root"] = str(ROOT)


def repo_guard() -> str:
    """Vazio = ok. O painel só roda em <repositório>/.srag-status-local (uma cópia solta, ex. em Downloads,
    publicaria um estado sem histórico e zeraria o painel da equipe)."""
    if not shutil.which("git"):
        return "Git não encontrado no PATH."
    p = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=LOCAL, text=True, capture_output=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        return (f"Esta pasta ({LOCAL}) não está dentro de um repositório Git. Use a pasta .srag-status-local que fica "
                "dentro do repositório do projeto (não uma cópia em Downloads ou na área de trabalho).")
    if LOCAL.parent.resolve() != Path(p.stdout.strip()).resolve():
        return (f"A pasta do painel precisa estar na raiz do repositório ({Path(p.stdout.strip()) / '.srag-status-local'}), "
                f"mas está em {LOCAL}.")
    return ""


def has_remote() -> bool:
    return CFG["remote"] in git("remote").stdout.split()


def status_branch() -> str:
    if CFG.get("branch"):
        return CFG["branch"]
    remote = CFG["remote"]
    p = git("symbolic-ref", "--short", f"refs/remotes/{remote}/HEAD")
    if p.returncode == 0 and "/" in p.stdout.strip():
        return p.stdout.strip().split("/", 1)[1]
    for cand in ("main", "master"):
        if git("rev-parse", "--verify", "-q", f"refs/remotes/{remote}/{cand}").returncode == 0:
            return cand
    p = git("ls-remote", "--symref", remote, "HEAD", timeout=30)
    m = re.search(r"ref:\s+refs/heads/(\S+)\s+HEAD", p.stdout)
    if m:
        return m.group(1)
    cur = git("branch", "--show-current").stdout.strip()
    return cur or "main"


def remote_ref() -> str:
    return f"refs/remotes/{CFG['remote']}/{META['branch'] or status_branch()}"


def default_actor() -> str:
    return git("config", "user.name").stdout.strip() or os.environ.get("USERNAME") or os.environ.get("USER") or "anônimo"


# =============================================================== estado
BLOCK = re.compile(r"<!--\s*PROJECT_STATUS_DATA\s*\r?\n(.*?)\r?\nPROJECT_STATUS_DATA\s*-->", re.S)


class StateError(RuntimeError):
    pass


def extract_state(text: str, source: str) -> dict[str, Any]:
    found = list(BLOCK.finditer(text))
    if len(found) != 1:
        raise StateError(f"Esperado 1 bloco PROJECT_STATUS_DATA em {source}; encontrados {len(found)}.")
    try:
        value = json.loads(found[0].group(1).strip())
    except json.JSONDecodeError as exc:
        raise StateError(f"JSON do bloco inválido em {source}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("items"), dict):
        raise StateError(f"Estado sem 'items' em {source}.")
    return value


def baseline() -> dict[str, Any]:
    raw = read_json(BASE, {"items": {}})
    return raw


DEFINITIONS: dict[str, dict[str, Any]] = {str(k): v.get("definition", {}) for k, v in baseline().get("items", {}).items()}


def default_item(item_id: str) -> dict[str, Any]:
    return {"id": item_id, "status": "open", "done": False, "note": "", "comments": [], "updated_at": None,
            "updated_by": "baseline", "origin": "baseline", "evidence": [], "history": [], "dismissed": [], "flags": {}}


def normalize(state: dict[str, Any] | None) -> dict[str, Any]:
    state = copy.deepcopy(state) if state else {}
    state.setdefault("schema_version", 3)
    state["schema_version"] = max(int(state.get("schema_version") or 1), 3)
    state.setdefault("generated_at", now())
    state.setdefault("items", {})
    scan = state.setdefault("scan", {})
    scan.setdefault("seen", [])
    scan.setdefault("deep_seen", [])
    scan.setdefault("since", SCAN_SINCE_DEFAULT)
    if state.get("last_scanned_commit") and not scan.get("migrated_from"):
        scan["migrated_from"] = state["last_scanned_commit"]
    state.setdefault("audit", {})
    for key in DEFINITIONS:
        state["items"].setdefault(key, default_item(key))
    for key, item in state["items"].items():
        base = default_item(str(key))
        for f, v in base.items():
            item.setdefault(f, v)
        if item.get("status") == "implemented_unconfirmed":
            item["status"] = "resolved_pending_validation"
        if item.get("status") not in STATUSES:
            item["status"] = "open"
        item["done"] = item["status"] == "done"
        if not item.get("origin") or item["origin"] == "baseline":
            ub = str(item.get("updated_by") or "")
            item["origin"] = "baseline" if ub in ("baseline", "") else ("auto" if ub in AUTO_ACTORS or ub.startswith("auditoria") else "human")
    return state


def initial_state() -> dict[str, Any]:
    legacy = read_json(LEGACY_CACHE, None)
    if isinstance(legacy, dict) and isinstance(legacy.get("items"), dict):
        for item in legacy["items"].values():
            item.pop("definition", None)
        return normalize(legacy)
    return normalize({"items": {}})


def canonical(state: dict[str, Any]) -> str:
    """Representação usada para decidir se há mudança real (ignora carimbos de horário)."""
    s = copy.deepcopy(state)
    s.pop("generated_at", None)
    s.pop("published_by", None)
    for k in ("generated_at", "by", "head"):
        (s.get("audit") or {}).pop(k, None)
    return json.dumps(s, ensure_ascii=False, sort_keys=True, default=str)


def render_markdown(state: dict[str, Any]) -> str:
    items = state["items"]
    counts = Counter(i.get("status", "open") for i in items.values())

    def line(item: dict[str, Any]) -> str:
        d = DEFINITIONS.get(item["id"], {})
        extra = ""
        if item.get("flags", {}).get("reconfirm"):
            extra = " · ⚠ reconfirmar"
        elif item.get("status") == "needs_review" and (item.get("flags", {}).get("review_reason") or {}).get("kind") == "tests":
            extra = " · teste falhou"
        return (f"- {STATUS_ICONS.get(item['status'], '⬜')} **#{item['id']}** {d.get('title', '')} — "
                f"{STATUS_LABELS.get(item['status'], item['status'])} · {d.get('owner', '—')} · {d.get('due', '—')}{extra}")

    def key(item: dict[str, Any]):
        d = DEFINITIONS.get(item["id"], {})
        due = str(d.get("due", "99/99"))
        try:
            dd, mm = due.split("/")[:2]
            dk = int(mm) * 100 + int(dd)
        except Exception:
            dk = 9999
        return (str(d.get("priority", "P9")), dk, int(item["id"]) if str(item["id"]).isdigit() else 0)

    lines = [
        "# Status do projeto SRAG",
        "",
        "> Arquivo mantido automaticamente pelo **Painel de Pendências** (pasta local `.srag-status-local`).",
        "> Não edite à mão: use o painel, ou escreva `[done:#ID]`, `[progress:#ID]`, `[reopen:#ID]` ou `tarefa ID` nas mensagens de commit.",
        f"> O texto das pendências (títulos, seções, responsáveis, datas) fica em `{CONTENT_NAME}` — esse sim pode ser editado à mão.",
        "",
        f"> Atualizado em {state['generated_at']}.",
        "",
        f"- Concluídas: **{counts['done']}**",
        f"- Resolvidas pendentes de validação: **{counts['resolved_pending_validation']}**",
        f"- Precisam revisão: **{counts['needs_review']}**",
        f"- Em andamento: **{counts['in_progress']}**",
        f"- Abertas: **{counts['open']}**",
        "",
    ]
    sections = [("needs_review", "Precisam revisão (teste falhou ou problema no código)"),
                ("resolved_pending_validation", "Detectadas como resolvidas — confirmar no painel"),
                ("in_progress", "Em andamento"), ("open", "Abertas"), ("done", "Concluídas")]
    for status, title in sections:
        group = sorted((i for i in items.values() if i.get("status") == status), key=key)
        lines.append(f"## {title} ({len(group)})")
        lines.append("")
        lines.extend(line(i) for i in group)
        if not group:
            lines.append("_Nenhum item._")
        lines.append("")
    audit = state.get("audit") or {}
    if audit.get("generated_at") and audit.get("kind") == "verificador":
        t = audit.get("tests_summary") or {}
        v = audit.get("verdicts") or {}
        lines += ["## Última verificação do “Pronto quando”", "",
                  f"- Executada em {audit.get('generated_at')} por {audit.get('by', '—')} sobre `{str(audit.get('head', ''))[:12]}`.",
                  "- Pendências: " + (", ".join(f"{VERDICT_PT.get(k, k)} {n}" for k, n in sorted(v.items())) or "—") + ".",
                  (f"- pytest: {t.get('passed', 0)} passaram, {t.get('failed', 0)} falharam, {t.get('errors', 0)} erro(s), "
                   f"{t.get('skipped', 0)} pulados." if audit.get("tests_executed") else "- pytest: não executado."), ""]
        for f in (audit.get("tests_failed") or [])[:15]:
            lines.append(f"- ✗ `{f.get('nodeid')}` — {f.get('message', '')}" + (f" (afeta {', '.join('#' + x for x in f.get('tasks', []))})" if f.get("tasks") else ""))
        for c in (audit.get("config_changes") or [])[:5]:
            cited = ", ".join("#" + x for x in c.get("cites_tasks", [])) or "nenhuma pendência citada"
            lines.append(f"- Configuração crítica `{c.get('file')}` mudou em `{c.get('commit', '')[:7]}` por {c.get('author')} ({cited}).")
        lines.append("")
    elif audit.get("generated_at"):
        c = audit.get("counts", {})
        lines += ["## Última auditoria", "",
                  f"- Executada em {audit.get('generated_at')} por {audit.get('by', '—')} sobre `{str(audit.get('head', ''))[:12]}`.",
                  f"- Achados: crítico={c.get('critical', 0)}, alto={c.get('high', 0)}, médio={c.get('medium', 0)}, baixo={c.get('low', 0)}.", ""]
    # Bloco de dados: um item por linha => diffs pequenos e legíveis no GitHub.
    meta = {k: v for k, v in state.items() if k != "items"}
    body = ",\n".join(json.dumps(str(k), ensure_ascii=False) + ":" + json.dumps(v, ensure_ascii=False, separators=(",", ":"), default=str)
                      for k, v in sorted(state["items"].items(), key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else 10**9))
    meta_json = json.dumps(meta, ensure_ascii=False, separators=(",", ":"), default=str)
    payload = meta_json[:-1] + (',"items":{\n' if len(meta) else '{"items":{\n') + body + "\n}}"
    if not meta:
        payload = '{"items":{\n' + body + "\n}}"
    json.loads(payload)  # validação
    lines += ["<!-- PROJECT_STATUS_DATA", payload, "PROJECT_STATUS_DATA -->", ""]
    text = "\n".join(lines)
    extract_state(text, "render")  # validação final
    return text


# =============================================================== remoto
def fetch() -> dict[str, Any]:
    if not has_remote():
        META["mode"] = "local"
        return {"ok": False, "detail": f"Remoto '{CFG['remote']}' não configurado: modo somente local."}
    p = git("fetch", CFG["remote"], "--prune", "--quiet", timeout=120)
    META["last_fetch"] = now()
    META["last_fetch_ok"] = p.returncode == 0
    if p.returncode != 0:
        META["mode"] = "offline"
        META["fetch_error"] = {**classify_fetch_error(detail(p)), "detail": detail(p, 600), "at": now()}
        log(f"Busca falhou ({META['fetch_error']['kind']}): {detail(p, 400)}")
        return {"ok": False, "detail": detail(p)}
    META["mode"] = "normal"
    META.pop("fetch_error", None)
    if not META.get("branch"):
        META["branch"] = status_branch()
    return {"ok": True, "detail": f"Atualizado de {CFG['remote']}/{META['branch']}."}


def remote_tip() -> str | None:
    p = git("rev-parse", "--verify", "-q", remote_ref())
    return p.stdout.strip() if p.returncode == 0 else None


def read_remote_state(tip: str | None) -> dict[str, Any] | None:
    if not tip:
        return None
    p = git("show", f"{tip}:{MD_NAME}")
    if p.returncode != 0 or not p.stdout.strip():
        return None
    try:
        return extract_state(p.stdout, f"{CFG['remote']}/{META['branch']}:{MD_NAME}")
    except StateError as exc:
        META["last_error"] = f"{exc} — publicação suspensa até o arquivo ser restaurado (nada é republicado do zero)."
        log(META["last_error"])
        return None


def commit_on_tip(tip: str | None, files: dict[str, str | None], message: str) -> str:
    """Cria o commit 'por fora' (índice temporário): a pasta de trabalho não é tocada.
    Valor None remove o arquivo do commit (usado para aposentar o nome antigo PENDENCIAS.md)."""
    blobs: dict[str, str | None] = {}
    for name, content in files.items():
        if content is None:
            blobs[name] = None
            continue
        # bytes (não texto): evita que o Windows converta \n em \r\n na entrada do git
        raw = subprocess.run(["git", "hash-object", "-w", "--stdin", "--path", name], cwd=ROOT, input=content.encode("utf-8"),
                             capture_output=True, timeout=60, env=git_env())
        if raw.returncode != 0:
            raise RuntimeError("git hash-object falhou: " + raw.stderr.decode("utf-8", "replace")[-800:])
        blobs[name] = raw.stdout.decode().strip()
    with tempfile.TemporaryDirectory(prefix="painel-idx-") as tmp:
        env = {"GIT_INDEX_FILE": str(Path(tmp) / "index")}
        if tip:
            r = git("read-tree", tip, env=env)
        else:
            r = git("read-tree", "--empty", env=env)
        if r.returncode != 0:
            raise RuntimeError("git read-tree falhou: " + detail(r))
        for name, blob_sha in blobs.items():
            if blob_sha is None:
                u = git("update-index", "--force-remove", "--", name, env=env)
            else:
                u = git("update-index", "--add", "--cacheinfo", f"100644,{blob_sha},{name}", env=env)
            if u.returncode != 0:
                raise RuntimeError("git update-index falhou: " + detail(u))
        tree = git("write-tree", env=env)
        if tree.returncode != 0:
            raise RuntimeError("git write-tree falhou: " + detail(tree))
    ident_env = {}
    if not git("config", "user.email").stdout.strip():
        ident_env.update(GIT_AUTHOR_EMAIL="painel@local", GIT_COMMITTER_EMAIL="painel@local")
    if not git("config", "user.name").stdout.strip():
        ident_env.update(GIT_AUTHOR_NAME="Painel de Pendências", GIT_COMMITTER_NAME="Painel de Pendências")
    args = ["commit-tree", tree.stdout.strip(), "-m", message]
    if tip:
        args[2:2] = ["-p", tip]
    c = git(*args, env=ident_env)
    if c.returncode != 0:
        raise RuntimeError("git commit-tree falhou: " + detail(c))
    return c.stdout.strip()


def push(sha: str) -> tuple[bool, bool, str]:
    """Retorna (ok, rejeitado_por_concorrência, detalhe)."""
    p = git("push", "--porcelain", CFG["remote"], f"{sha}:refs/heads/{META['branch']}", timeout=180)
    out = detail(p, 3000)
    if p.returncode == 0:
        return True, False, out
    rejected = any(s in out.lower() for s in ("non-fast-forward", "fetch first", "rejected", "stale info", "[rejected]"))
    auth = any(s in out.lower() for s in ("authentication", "permission", "403", "could not read username", "denied"))
    return False, rejected and not auth, out


def auto_fast_forward(tip: str | None) -> str:
    """Avança a branch local SOMENTE se o que chegou do remoto forem apenas os arquivos do painel."""
    if not CFG.get("auto_ff_status_only") or not tip:
        return ""
    cur = git("branch", "--show-current").stdout.strip()
    if cur != META.get("branch"):
        return ""
    head = git("rev-parse", "HEAD").stdout.strip()
    if not head or head == tip:
        return ""
    if git("merge-base", "--is-ancestor", head, tip).returncode != 0:
        return ""  # você tem commits locais; o VS Code fará o pull normal
    changed = [x for x in git("diff", "--name-only", head, tip).stdout.splitlines() if x.strip()]
    if not changed or not set(changed) <= PANEL_FILES:
        return ""
    if git("status", "--porcelain", "--", *sorted(PANEL_FILES)).stdout.strip():
        return ""  # você tem edições locais nesses arquivos: o pull fica com o VS Code
    m = git("merge", "--ff-only", "--quiet", tip, timeout=60)
    if m.returncode == 0:
        return "Branch local avançada automaticamente (só os arquivos do painel mudaram)."
    return ""


# =============================================================== absorção do arquivo local (corrige o problema do VS Code)
def absorb_worktree_markdown() -> str:
    """Se PROJECT_STATUS.md estiver modificado no working tree (versão antiga do painel, auditoria avulsa ou edição
    manual), converte as diferenças em eventos, guarda backup e devolve o arquivo ao estado do commit.
    Resultado: o VS Code deixa de enxergar o arquivo como alterado e o pull volta a funcionar."""
    st = git("status", "--porcelain", "--", MD_NAME).stdout
    if not st.strip():
        return ""
    code = st[:2]
    if code in ("UU", "AA", "DU", "UD", "AU", "UA", "DD"):
        # conflito de merge em andamento: aceita a versão remota para o arquivo de status (os eventos ficam preservados)
        path = ROOT / MD_NAME
        if path.exists():
            BACKUPS.mkdir(exist_ok=True)
            shutil.copy2(path, BACKUPS / f"PROJECT_STATUS_conflito_{int(time.time())}.md")
            absorb_text(path.read_text(encoding="utf-8", errors="replace"), "conflito de merge")
        git("checkout", "--theirs", "--", MD_NAME)
        git("add", "--", MD_NAME)
        return "Conflito no PROJECT_STATUS.md resolvido automaticamente (suas marcações foram preservadas como eventos). Conclua o merge no VS Code."
    path = ROOT / MD_NAME
    msg = ""
    if path.exists():
        BACKUPS.mkdir(exist_ok=True)
        shutil.copy2(path, BACKUPS / f"PROJECT_STATUS_local_{dt.datetime.now().strftime('%Y%m%dT%H%M%S')}.md")
        msg = absorb_text(path.read_text(encoding="utf-8", errors="replace"), "arquivo local")
    in_head = git("cat-file", "-e", f"HEAD:{MD_NAME}").returncode == 0
    if in_head:
        git("reset", "-q", "--", MD_NAME)
        git("checkout", "HEAD", "--", MD_NAME)
    else:
        git("rm", "-q", "--cached", "--ignore-unmatch", "--", MD_NAME)
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    return msg or "PROJECT_STATUS.md local restaurado (cópia em backups/)."


def absorb_text(text: str, origem: str) -> str:
    try:
        local = normalize(extract_state(text, origem))
    except StateError as exc:
        return f"Arquivo local ilegível ({exc}); cópia guardada em backups/."
    head_text = git("show", f"HEAD:{MD_NAME}").stdout
    try:
        head = normalize(extract_state(head_text, "HEAD")) if head_text.strip() else normalize(None)
    except StateError:
        head = normalize(None)
    events = []
    for iid, item in local["items"].items():
        old = head["items"].get(iid, default_item(iid))
        if item.get("status") != old.get("status") and item.get("origin") != "auto":
            events.append(make_event(iid, "status", item["status"], old.get("status"), item.get("updated_by") or "migração",
                                     ts=item.get("updated_at")))
        known = {c.get("event_id") for c in old.get("comments", [])}
        for c in item.get("comments", []):
            if c.get("event_id") and c["event_id"] not in known:
                events.append({"event_id": c["event_id"], "ts": c.get("timestamp") or now(), "actor": c.get("actor") or "migração",
                               "item_id": iid, "kind": "comment", "value": c.get("text", ""), "base": None})
    if events:
        with LOCK:
            box = read_json(OUTBOX, [])
            have = {e["event_id"] for e in box}
            box.extend(e for e in events if e["event_id"] not in have)
            write_json(OUTBOX, box)
    return f"{len(events)} alteração(ões) do {origem} preservada(s) e enviada(s) para publicação."


# =============================================================== eventos e merge campo a campo
def make_event(item_id: str, kind: str, value: Any, base: Any, actor: str, ts: str | None = None,
               event_id: str | None = None) -> dict[str, Any]:
    return {"event_id": event_id or str(uuid.uuid4()), "ts": ts or now(), "actor": actor, "item_id": str(item_id),
            "kind": kind, "value": value, "base": base}


def push_history(item: dict[str, Any], entry: dict[str, Any]) -> None:
    item.setdefault("history", []).append(entry)
    item["history"] = item["history"][-40:]


def set_status(item: dict[str, Any], status: str, actor: str, origin: str, ts: str, note: str = "", ref: str = "") -> bool:
    if item.get("status") == status:
        return False
    push_history(item, {"at": ts, "by": actor, "from": item.get("status"), "to": status, "origin": origin, **({"ref": ref} if ref else {})})
    if origin == "auto" and item.get("origin") != "auto":
        item["auto_prev"] = item.get("status")
    item["status"] = status
    item["done"] = status == "done"
    item["updated_at"] = ts
    item["updated_by"] = actor
    item["origin"] = origin
    if note:
        item["note"] = note
    if status == "done" or origin == "human":
        item.get("flags", {}).pop("reconfirm", None)
    return True


def apply_events(state: dict[str, Any], events: list[dict[str, Any]], conflicts: list[dict[str, Any]]) -> list[str]:
    changes = []
    for ev in sorted(events, key=lambda e: (e.get("ts") or "", e.get("event_id"))):
        if ev.get("kind") in CONTENT_KINDS:
            continue  # conteúdo é aplicado sobre o PROJECT_STATUS_TEXT.md (apply_content_events)
        item = state["items"].get(str(ev.get("item_id")))
        if item is None:
            continue
        applied = set(item.setdefault("applied_events", []))
        if ev["event_id"] in applied:
            continue
        kind = ev.get("kind")
        if kind == "comment":
            ids = {c.get("event_id") for c in item["comments"]}
            if ev["event_id"] not in ids and str(ev.get("value") or "").strip():
                item["comments"].append({"event_id": ev["event_id"], "timestamp": ev["ts"], "actor": ev["actor"], "text": str(ev["value"])[:5000]})
                item["note"] = str(ev["value"])[:500]
                changes.append(f"#{item['id']} comentário")
        elif kind == "status":
            cur, want, base = item.get("status"), ev.get("value"), ev.get("base")
            if want not in STATUSES:
                continue
            if cur == want:
                pass
            elif cur == base or item.get("origin") in ("auto", "baseline", "commit") or ev.get("force"):
                set_status(item, want, ev["actor"], "human", ev["ts"], ref=ev["event_id"])
                changes.append(f"#{item['id']} {SHORT[want]}")
            else:
                conflicts.append({"id": ev["event_id"], "item_id": item["id"], "mine": want, "theirs": cur,
                                  "theirs_by": item.get("updated_by"), "theirs_at": item.get("updated_at"),
                                  "actor": ev["actor"], "at": now(), "base": base})
        elif kind == "ack":
            item.setdefault("flags", {})["tests_ack"] = sorted(set(ev.get("value") or []))[:60]
            item["flags"].pop("review_reason", None)
            changes.append(f"#{item['id']} testes reconhecidos")
        elif kind == "dismiss":
            shas = [s for s in (ev.get("value") or []) if s]
            item["dismissed"] = sorted(set(item.get("dismissed", [])) | set(shas))[-200:]
            if item.get("origin") == "auto" and item.get("status") in ("resolved_pending_validation", "needs_review", "in_progress"):
                set_status(item, item.get("auto_prev") or "open", ev["actor"], "human", ev["ts"],
                           note="Sugestão automática rejeitada.", ref=ev["event_id"])
            changes.append(f"#{item['id']} sugestão rejeitada")
        item["applied_events"] = (list(applied) + [ev["event_id"]])[-60:]
    return changes


# =============================================================== varredura leve de commits (todo fetch)
def parse_ids(fragment: str) -> list[str]:
    return [str(int(x)) for x in re.findall(r"\d+", fragment)]


def commit_mentions(message: str) -> tuple[list[tuple[str, str]], list[str]]:
    msg = PULL_REQUEST.sub(" ", message)
    explicit = []
    for action, iid in TAG.findall(msg):
        a = action.lower()
        a = "done" if a.startswith(("conclu", "feito", "done")) else ("open" if a.startswith(("reop", "reab")) else ("in_progress" if a.startswith(("prog", "anda")) else a))
        explicit.append((a if a in STATUSES else STATUS_FROM_TAG.get(a, "in_progress"), str(int(iid))))
    clean = TAG.sub(" ", msg)
    mentions = set()
    for frag in REF_WORD.findall(clean):
        mentions.update(parse_ids(frag))
    for iid in REF_HASH.findall(clean):
        mentions.add(str(int(iid)))
    exp_ids = {i for _, i in explicit}
    return explicit, sorted(mentions - exp_ids, key=int)


def list_commits(limit: int) -> list[dict[str, Any]]:
    fmt = "%x1e%H%x1f%aI%x1f%an%x1f%B%x1d"
    scope = [f"--remotes={CFG['remote']}"] if has_remote() else ["HEAD"]
    p = git("log", *scope, f"-n{limit}", "--name-only", f"--format={fmt}", timeout=120)
    out = []
    for chunk in p.stdout.split("\x1e"):
        if not chunk.strip():
            continue
        head, _, files = chunk.partition("\x1d")
        parts = head.split("\x1f", 3)
        if len(parts) != 4:
            continue
        sha, when, who, body = parts
        out.append({"sha": sha.strip(), "when": when, "who": who, "message": body.strip(),
                    "subject": (body.strip().splitlines() or [""])[0], "files": [f.strip() for f in files.splitlines() if f.strip()]})
    return list(reversed(out))


def item_has_sha(item: dict[str, Any], sha: str) -> bool:
    s12 = sha[:12]
    if s12 in {str(x)[:12] for x in item.get("dismissed", [])}:
        return True
    for e in item.get("evidence", []):
        if str(e.get("sha") or e.get("commit") or "")[:12] == s12:
            return True
    return False


def add_evidence(item: dict[str, Any], ev: dict[str, Any]) -> None:
    item.setdefault("evidence", []).append(ev)
    item["evidence"] = item["evidence"][-25:]


def _instant(text: Any) -> dt.datetime | None:
    """'2026-10-19T10:27:11-03:00' ou '...Z' -> datetime com fuso (None se inválido)."""
    if not text:
        return None
    try:
        value = dt.datetime.fromisoformat(str(text).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)


def scan_cutoff(state: dict[str, Any], item: dict[str, Any]) -> dt.datetime | None:
    """Commit só muda a situação se for MAIS NOVO que (a) o início desta versão do painel e (b) a última decisão
    humana sobre o item. Isso impede que commits antigos reabram sugestões já decididas a cada busca."""
    marks = [_instant((state.get("scan") or {}).get("since") or SCAN_SINCE_DEFAULT)]
    if item.get("origin") == "human":
        marks.append(_instant(item.get("updated_at")))
    marks = [m for m in marks if m]
    return max(marks) if marks else None


def light_scan(state: dict[str, Any]) -> list[str]:
    """Lê os commits novos. Só MENÇÃO EXPLÍCITA muda a situação ([done:#N], 'tarefa N', '#N');
    commits que apenas mexem nos arquivos de uma tarefa nunca mudam nada (aparecem como informação no card)."""
    if git("rev-parse", "--verify", "-q", "HEAD").returncode != 0:
        return []
    commits = list_commits(int(CFG["commit_scan_limit"]))
    changes = []
    for c in commits:
        s12 = c["sha"][:12]
        if (c["files"] and set(c["files"]) <= PANEL_FILES) or c["subject"].startswith(("chore(status)", COMMIT_PREFIX)):
            continue
        explicit, mentions = commit_mentions(c["message"])
        when = _instant(c["when"])
        evid = {"type": "commit", "sha": s12, "subject": c["subject"][:160], "author": c["who"], "when": c["when"]}
        for status, iid in explicit:
            item = state["items"].get(iid)
            if not item or item_has_sha(item, c["sha"]):
                continue
            cutoff = scan_cutoff(state, item)
            if cutoff and when and when <= cutoff:
                continue
            add_evidence(item, {**evid, "marker": status})
            if status == "in_progress" and item["status"] == "done":
                continue
            if set_status(item, status, c["who"], "commit", c["when"], note=f"Commit {s12}: {c['subject'][:140]}", ref=s12):
                changes.append(f"#{iid} {SHORT[status]} (commit {s12[:7]} de {c['who']})")
        done_lang = bool(COMPLETION.search(c["message"]))
        for iid in mentions:
            item = state["items"].get(iid)
            if not item or item_has_sha(item, c["sha"]):
                continue
            cutoff = scan_cutoff(state, item)
            if cutoff and when and when <= cutoff:
                continue
            if item["status"] in ("done", "needs_review"):
                continue
            add_evidence(item, {**evid, "type": "commit_task_reference", "completion_language": done_lang})
            if done_lang and item["status"] in ("open", "in_progress"):
                if set_status(item, "resolved_pending_validation", "varredura de commits", "auto", c["when"],
                              note=f"Commit {s12} de {c['who']} cita a tarefa com linguagem de conclusão: “{c['subject'][:120]}”. Confirme no painel.", ref=s12):
                    changes.append(f"#{iid} a confirmar (commit {s12[:7]} de {c['who']})")
            elif item["status"] == "open":
                if set_status(item, "in_progress", "varredura de commits", "auto", c["when"],
                              note=f"Commit {s12} de {c['who']} cita a tarefa: “{c['subject'][:120]}”.", ref=s12):
                    changes.append(f"#{iid} em andamento (commit {s12[:7]})")
    return changes


# =============================================================== verificação do "Pronto quando" (botão 2)
def load_audit_module():
    if not AUDIT_SCRIPT.exists():
        raise RuntimeError(f"Verificador não encontrado em {AUDIT_SCRIPT}.")
    spec = importlib.util.spec_from_file_location("deep_git_project_audit", AUDIT_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    sys.modules["deep_git_project_audit"] = mod
    spec.loader.exec_module(mod)
    if not hasattr(mod, "audit"):
        raise RuntimeError("deep_git_project_audit.py é de uma versão antiga: atualize a pasta .srag-status-local.")
    return mod


def verification_ref() -> str:
    """A verificação usa o commit publicado (igual para todos); sem remoto, o HEAD local."""
    if has_remote() and remote_tip():
        return remote_ref()
    return "HEAD"


def full_tests() -> dict[str, Any] | None:
    rep = read_json(REPORT, None)
    if isinstance(rep, dict) and isinstance(rep.get("tests"), dict) and rep["tests"].get("executed"):
        return {**rep["tests"], "cases": rep.get("test_cases") or {}, "sha": rep.get("sha")}
    return None


def run_verification(progress, *, quick: bool = False, only: set[str] | None = None) -> dict[str, Any]:
    mod = load_audit_module()
    doc = CONTENT.get("doc") or (compute_content("verificação") and CONTENT["doc"])
    items = view_state()["items"]
    if not quick:
        progress("Verificação 1/3 · conferindo o “Pronto quando” de cada pendência e rodando o pytest rápido numa cópia limpa do commit publicado…")
    report = mod.audit(ROOT, ref=verification_ref(), only=only, quick=quick, previous_tests=full_tests(),
                       doc=doc, status_items=items, test_timeout=int(CFG["pytest_timeout_seconds"]))
    report["by"] = default_actor()
    if only is None:
        write_json(REPORT_QUICK if quick else REPORT, report)
    if not quick:
        t = report.get("tests") or {}
        s = t.get("summary") or {}
        progress(f"Verificação 2/3 · pytest: {s.get('passed', 0)} passaram, {s.get('failed', 0)} falharam, "
                 f"{s.get('errors', 0)} erro(s), {s.get('skipped', 0)} pulados." if t.get("executed") else
                 f"Verificação 2/3 · pytest não executado: {t.get('detail', '')}")
        v = report["summary"]["verdicts"]
        progress("Verificação 3/3 · pendências: " + ", ".join(f"{VERDICT_PT.get(k, k)} {n}" for k, n in sorted(v.items())))
    return report


def queue_suggested_criteria(report: dict[str, Any]) -> int:
    """Testes que falharam e importam arquivos de uma pendência JÁ INICIADA (em andamento, a confirmar, concluída)
    entram no "④ Pronto quando" dela (edição de conteúdo, publicada no mesmo commit da verificação)."""
    doc = CONTENT.get("doc") or {}
    states = view_state()["items"]
    events = []
    for iid, task in report.get("tasks", {}).items():
        if (states.get(iid) or {}).get("status", "open") == "open":
            continue
        lines = task.get("suggested_criteria") or []
        item = (doc.get("items") or {}).get(iid)
        if not lines or item is None:
            continue
        cur = pm.get_field(item, "sec:pq")
        new = [l for l in lines if l.split(" | ", 1)[0] not in (cur or "")]
        if not new:
            continue
        value = ((cur or "").rstrip() + "\n" + "\n".join(new)).strip()
        events.append(make_event(iid, "content", {"sec:pq": value}, {"sec:pq": cur}, "verificador automático"))
    if events:
        with LOCK:
            box = read_json(OUTBOX, [])
            box.extend(events)
            write_json(OUTBOX, box)
    return len(events)


def _criteria_text(task: dict[str, Any], status: str, limit: int = 3) -> str:
    rows = [r for r in task.get("criteria", []) if r.get("status") == status][:limit]
    return "; ".join(f"{r.get('description') or r.get('raw')} ({r.get('detail')})"[:220] for r in rows)


def apply_verification(state: dict[str, Any], report: dict[str, Any], actor: str) -> list[str]:
    """Resultado do verificador -> situações compartilhadas. Nunca conclui sozinho.

    - teste que importa arquivos de uma pendência já iniciada falhou -> PRECISA REVISÃO (inclusive se estava concluída);
      pendência ainda aberta só aparece como informação em REVISÕES;
    - todos os critérios atendidos e item aberto/em andamento -> A CONFIRMAR;
    - item concluído com critério não atendido -> alerta "reconfirmar";
    - sugestões automáticas que deixaram de valer voltam ao estado anterior.
    """
    changes: list[str] = []
    stamp = now()
    sha7 = str(report.get("sha", ""))[:7]
    for iid, task in report.get("tasks", {}).items():
        item = state["items"].get(iid)
        if item is None:
            continue
        verdict = task.get("verdict")
        affected = task.get("affected_by_tests") or []
        failing = sorted({a["nodeid"] for a in affected})
        flags = item.setdefault("flags", {})
        status = item.get("status")
        reason = flags.get("review_reason") or {}
        if failing and status != "open" and not set(failing) <= set(flags.get("tests_ack") or []):
            if status != "needs_review":
                note = (f"Verificação de {sha7}: {len(failing)} teste(s) que importam arquivos desta pendência falharam "
                        f"(ex.: {failing[0]} — {affected[0].get('message', '')[:160]}). Revise antes de seguir.")
                if set_status(item, "needs_review", "verificador automático", "auto", stamp, note=note):
                    changes.append(f"#{iid} revisar (teste falhou)")
            flags["review_reason"] = {"kind": "tests", "tests": failing[:20], "at": stamp, "sha": sha7}
            continue
        if status == "needs_review" and item.get("origin") == "auto" and reason.get("kind") == "tests":
            back = item.get("auto_prev") or "open"
            if back == "needs_review":
                back = "open"
            if set_status(item, back, "verificador automático", "auto", stamp,
                          note=f"Os testes ligados a esta pendência voltaram a passar (verificação de {sha7})."):
                changes.append(f"#{iid} {SHORT[back]} (testes voltaram a passar)")
            flags.pop("review_reason", None)
            status = item["status"]
        if verdict == "atendida":
            if status in ("open", "in_progress"):
                if set_status(item, "resolved_pending_validation", "verificador automático", "auto", stamp,
                              note=f"Todos os critérios do “Pronto quando” estão atendidos na verificação de {sha7}. Confirme no painel."):
                    changes.append(f"#{iid} a confirmar (critérios atendidos)")
            if flags.pop("reconfirm", None):
                changes.append(f"#{iid} reconfirmação ok")
        elif verdict == "nao_atendida":
            if status == "done":
                text = _criteria_text(task, "nao_atendido")
                if (flags.get("reconfirm") or {}).get("reason") != text:
                    flags["reconfirm"] = {"at": stamp, "reason": f"Critério(s) não atendido(s) em {sha7}: {text}"[:600], "sha": sha7}
                    changes.append(f"#{iid} reconfirmar (critério não atendido)")
            elif status == "resolved_pending_validation" and item.get("origin") == "auto":
                back = item.get("auto_prev") or "open"
                back = back if back in ("open", "in_progress") else "open"
                if set_status(item, back, "verificador automático", "auto", stamp,
                              note=f"Sugestão desfeita: critério(s) não atendido(s) em {sha7}: {_criteria_text(task, 'nao_atendido', 2)}"[:500]):
                    changes.append(f"#{iid} {SHORT[back]} (critério não atendido)")
    tests = report.get("tests") or {}
    failed = tests.get("failed") or []
    code_failed = [f for f in failed if f.get("kind") != "ambiente"]
    env_failed = [f for f in failed if f.get("kind") == "ambiente"]
    linked: dict[str, list[str]] = {}
    for iid, task in report.get("tasks", {}).items():
        for a in task.get("affected_by_tests") or []:
            linked.setdefault(a["nodeid"], []).append(iid)
    state["audit"] = {
        "kind": "verificador", "generated_at": report.get("generated_at") or stamp, "by": actor,
        "head": report.get("sha"), "ref": report.get("ref"),
        "tests_executed": bool(tests.get("executed")), "tests_ok": bool(tests.get("executed")) and not code_failed,
        "tests_summary": tests.get("summary") or {}, "tests_where": tests.get("where", ""),
        "tests_failed": [{"nodeid": f["nodeid"], "message": str(f.get("message", ""))[:220],
                          "tasks": sorted(set(linked.get(f["nodeid"], [])), key=int)} for f in code_failed[:60]],
        "tests_env": {"count": len(env_failed), "example": str(env_failed[0].get("message", ""))[:220] if env_failed else ""},
        "verdicts": report.get("summary", {}).get("verdicts", {}),
        "invalid": sorted((i for i, t in report.get("tasks", {}).items() if t.get("verdict") == "criterio_invalido"), key=int),
        "config_changes": (report.get("config_changes") or [])[:12],
        "counts": dict(Counter(f.get("severity") for f in report.get("findings", []))),
        "top": [{"severity": f["severity"], "category": f["category"], "message": f["message"][:220], "paths": f["paths"][:3]}
                for f in report.get("findings", []) if f.get("severity") in ("critical", "high")][:20],
    }
    return changes


def audit_signature(state: dict[str, Any]) -> str:
    a = {k: v for k, v in (state.get("audit") or {}).items() if k not in ("generated_at", "by")}
    return json.dumps(a, sort_keys=True, ensure_ascii=False, default=str)


def quick_check(iid: str) -> dict[str, Any]:
    """Verificação rápida de uma pendência (sem pytest; testes vêm da última verificação completa do mesmo commit)."""
    report = run_verification(lambda _m: None, quick=True, only={str(iid)})
    task = report["tasks"].get(str(iid))
    if task is None:
        return {"ok": True, "verdict": "sem_criterios", "verdict_text": "Pendência sem critérios.", "criteria": [], "sha": report["sha"]}
    return {"ok": True, "sha": report["sha"], "ref": report["ref"], **task}


LOCAL_CHECK_LOCK = threading.Lock()


def local_check(iid: str) -> dict[str, Any]:
    """Botão "Conferir na minha pasta" do card: confere UMA pendência na pasta de trabalho, antes ou depois do
    commit, rodando só os testes dela. Não grava relatório, não gera commit e não muda a situação compartilhada."""
    mod = load_audit_module()
    if not hasattr(mod, "check_task_local"):
        raise RuntimeError("deep_git_project_audit.py é de uma versão antiga: atualize a pasta .srag-status-local.")
    doc = CONTENT.get("doc") or (compute_content("conferência local") and CONTENT["doc"])
    if not LOCAL_CHECK_LOCK.acquire(timeout=1):
        raise RuntimeError("Já existe uma conferência em andamento nesta máquina. Aguarde ela terminar.")
    try:
        return mod.check_task_local(ROOT, str(iid), doc=doc, test_timeout=int(CFG["pytest_timeout_seconds"]))
    finally:
        LOCAL_CHECK_LOCK.release()


def regression_problems(remote: dict[str, Any] | None, new: dict[str, Any], explained: set[str]) -> list[str]:
    """Proteção contra regressão: nunca publicar um estado que perde informação do remoto.

    Bloqueia se o novo estado (a) perde itens, (b) perde comentários, rejeições ou histórico de algum item ou
    (c) muda a situação de um item sem que nenhuma alteração desta publicação explique a mudança."""
    if not remote:
        return []
    problems = []
    for iid, r in remote.get("items", {}).items():
        n = new["items"].get(iid)
        if n is None:
            problems.append(f"#{iid} sumiria do arquivo")
            continue
        lost = {c.get("event_id") for c in r.get("comments", [])} - {c.get("event_id") for c in n.get("comments", [])}
        if lost:
            problems.append(f"#{iid} perderia {len(lost)} comentário(s)")
        if set(r.get("dismissed", [])) - set(n.get("dismissed", [])):
            problems.append(f"#{iid} perderia sugestões já rejeitadas")
        rh, nh = r.get("history", []), n.get("history", [])
        if rh and rh[-1] not in nh:
            problems.append(f"#{iid} perderia o histórico")
        if r.get("status") != n.get("status") and iid not in explained:
            problems.append(f"#{iid} mudaria de {SHORT.get(r.get('status'), r.get('status'))} para "
                            f"{SHORT.get(n.get('status'), n.get('status'))} sem nenhuma alteração que explique")
    return problems


def explained_ids(changes: list[str], detected: list[str], box: list[dict[str, Any]]) -> set[str]:
    ids = {str(e.get("item_id")) for e in box}
    for c in list(changes) + list(detected):
        m = re.match(r"^#(\d+)", c)
        if m:
            ids.add(m.group(1))
    return ids


def classify_fetch_error(text: str) -> dict[str, str]:
    low = (text or "").lower()
    if any(s in low for s in ("authentication", "could not read username", "403", "permission", "denied", "logon failed", "credential")):
        return {"kind": "credencial", "hint": "O GitHub recusou a credencial. Faça um pull pelo VS Code (ele pede o login) e depois clique em Buscar."}
    if any(s in low for s in ("could not resolve", "failed to connect", "timed out", "timeout", "proxy", "ssl", "unable to access",
                              "network", "connection reset", "connection refused")):
        return {"kind": "rede", "hint": "Sem acesso ao GitHub por esta rede (internet, VPN ou proxy da empresa). Tente outra rede ou ligue/desligue a VPN; a fila sai sozinha quando a conexão voltar."}
    if any(s in low for s in ("does not appear to be a git repository", "repository not found", "no such remote")):
        return {"kind": "remoto", "hint": "O endereço do repositório remoto não foi encontrado. Rode DIAGNOSTICO.cmd e confira `git remote -v`."}
    return {"kind": "outro", "hint": "O Git não conseguiu buscar o GitHub. Rode DIAGNOSTICO.cmd e veja .srag-status-local/logs/painel.log."}


def reference_status() -> dict[str, Any]:
    """Referência para IAs (docs/PROJECT_COMPLETE_REFERENCE.txt) está atualizada em relação ao commit publicado?"""
    path = ROOT / "docs" / "PROJECT_COMPLETE_REFERENCE.txt"
    if not path.exists():
        return {"exists": False}
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            head = "".join(fh.readline() for _ in range(5))
    except OSError:
        return {"exists": False}
    m = re.search(r"SNAPSHOT ID:\s*([0-9a-f]{7,40})@(\S+)", head)
    if not m:
        return {"exists": True, "sha": None}
    sha, at = m.group(1), m.group(2)
    tip = (META.get("tip") or remote_tip() or git("rev-parse", "HEAD").stdout.strip()) if has_remote() else git("rev-parse", "HEAD").stdout.strip()
    behind = None
    if tip and git("cat-file", "-e", sha).returncode == 0:
        p = git("rev-list", "--count", f"{sha}..{tip}")
        behind = int(p.stdout.strip()) if p.returncode == 0 and p.stdout.strip().isdigit() else None
    return {"exists": True, "sha": sha, "at": at, "behind": behind}


# =============================================================== conteúdo (PROJECT_STATUS_TEXT.md -> painel.html)
CONTENT_KINDS = ("content", "create", "panel", "bootstrap")
CONTENT_LOCK = threading.RLock()
CONTENT: dict[str, Any] = {"doc": None, "published": None, "view": None, "hash": None, "meta": {}, "provisional": {},
                           "written_hash": None, "blob_cache": {}, "watch_sig": None}


def read_blob(rev: str | None, path: str) -> str | None:
    """Texto de <rev>:<path> com cache pelo id do blob (evita reler quando nada mudou)."""
    if not rev:
        return None
    p = git("rev-parse", "--verify", "-q", f"{rev}:{path}")
    blob = p.stdout.strip() if p.returncode == 0 else ""
    if not blob:
        return None
    cache = CONTENT["blob_cache"]
    if blob not in cache:
        raw = subprocess.run(["git", "cat-file", "blob", blob], cwd=ROOT, capture_output=True, timeout=60, env=git_env())
        if raw.returncode != 0:
            return None
        if len(cache) > 12:
            cache.clear()
        cache[blob] = raw.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    return cache[blob]


def worktree_content() -> str | None:
    try:
        return (ROOT / CONTENT_NAME).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    except FileNotFoundError:
        return None
    except Exception as exc:
        log(f"Não consegui ler {CONTENT_NAME} da pasta: {exc}")
        return None


def base_rev(tip: str | None) -> str | None:
    """Versão de referência das suas edições locais: ponto em comum entre sua branch e o remoto."""
    if git("rev-parse", "--verify", "-q", "HEAD").returncode != 0:
        return None
    if tip:
        mb = git("merge-base", "HEAD", tip)
        if mb.returncode == 0 and mb.stdout.strip():
            return mb.stdout.strip()
    return "HEAD"


def fallback_content_doc() -> dict[str, Any]:
    """Último recurso quando não há PROJECT_STATUS_TEXT.md em lugar nenhum: cache, painel.html embutido, painel v4 ou baseline."""
    for candidate in (CONTENT_CACHE, SEED):
        if candidate.exists():
            try:
                return pm.parse(candidate.read_text(encoding="utf-8"))
            except Exception:
                pass
    html_path = GENERATED if GENERATED.exists() else LOCAL / HTML
    try:
        text = html_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        text = ""
    legacy = pm.items_from_legacy_html(text)
    if legacy:
        return pm.bootstrap_doc(legacy)[0]
    embedded = pm.view_from_html(html_path)
    if embedded and embedded.get("D"):
        return pm.bootstrap_doc(embedded["D"])[0]
    items = [{"id": k, "t": v.get("definition", {}).get("title", ""), "p": v.get("definition", {}).get("priority", "P3"),
              "own": v.get("definition", {}).get("owner", "—"), "due": v.get("definition", {}).get("due", "—"),
              "src": v.get("definition", {}).get("source", "—"), "u": "", "pb": "", "fz": ""}
             for k, v in baseline().get("items", {}).items()]
    return pm.bootstrap_doc(items, convert=False)[0]


def refresh_definitions(doc: dict[str, Any]) -> None:
    defs = pm.definitions(doc)
    if defs:
        DEFINITIONS.clear()
        DEFINITIONS.update(defs)


def _norm(v: Any) -> str:
    return re.sub(r"[ \t]+\n", "\n", str(v or "")).strip()


def apply_content_events(doc: dict[str, Any], events: list[dict[str, Any]], conflicts: list[dict[str, Any]] | None,
                         provisional: dict[str, str] | None = None) -> list[str]:
    """Reaplica edições de conteúdo campo a campo sobre a versão mais nova (mesma lógica da situação)."""
    changes: list[str] = []
    for ev in sorted(events, key=lambda e: (e.get("ts") or "", e.get("event_id") or "")):
        kind = ev.get("kind")
        if kind == "bootstrap":
            continue
        if kind == "create":
            value = copy.deepcopy(ev.get("value") or {})
            title = pm.one_line(value.get("title", ""))
            dup = next((i for i, it in doc["items"].items() if it.get("title") == title and
                        [s[1] for s in it.get("sections", [])] == [s[1] for s in value.get("sections", [])]), None)
            if dup:  # publicação repetida (ex.: push que pareceu falhar): não duplica
                if provisional is not None:
                    provisional[dup] = ev["item_id"]
                continue
            want = str(value.get("want_id") or "")
            iid = want if want.isdigit() and want not in doc["items"] else pm.next_id(doc)
            item = pm.new_item(iid, title)
            for k, v in (value.get("meta") or {}).items():
                if k in pm.META_KEYS:
                    pm.set_field(item, f"meta:{k}", v)
            item["extra_meta"] = [list(x) for x in value.get("extra_meta", [])]
            item["intro"] = value.get("intro", "")
            if value.get("sections") is not None:
                item["sections"] = [[h, b] for h, b in value["sections"]]
            item["meta"]["novo"] = item["meta"].get("novo", "sim")
            doc["items"][iid] = item
            doc.setdefault("layout", []).append(["item", iid])
            if provisional is not None:
                provisional[iid] = ev["item_id"]
            changes.append(f"#{iid} nova" + (f" (pedida como #{want})" if want and want != iid else ""))
        elif kind == "content":
            iid = str(ev.get("item_id"))
            item = doc["items"].get(iid)
            if item is None:
                if conflicts is not None:
                    conflicts.append({"id": ev["event_id"], "kind": "content", "item_id": iid, "field": "*", "mine": "", "theirs": "",
                                      "actor": ev.get("actor"), "at": now(), "note": "O item não existe mais no PROJECT_STATUS_TEXT.md remoto."})
                continue
            touched = False
            base = ev.get("base") or {}
            for field, new in (ev.get("value") or {}).items():
                try:
                    cur = pm.get_field(item, field)
                except KeyError:
                    continue
                if _norm(cur) == _norm(new):
                    continue
                if _norm(cur) == _norm(base.get(field)) or ev.get("force"):
                    pm.set_field(item, field, new)
                    touched = True
                elif conflicts is not None:
                    conflicts.append({"id": f"{ev['event_id']}::{field}", "kind": "content", "item_id": iid, "field": field,
                                      "mine": new, "theirs": cur, "base": base.get(field), "actor": ev.get("actor"), "at": now(),
                                      "theirs_by": "", "theirs_at": ""})
            if touched:
                changes.append(f"#{iid} conteúdo")
        elif kind == "panel":
            touched = False
            base = ev.get("base") or {}
            for heading, new in (ev.get("value") or {}).items():
                cur = pm.panel_section(doc, heading)
                if _norm(cur) == _norm(new):
                    continue
                if _norm(cur) == _norm(base.get(heading)) or ev.get("force"):
                    pm.set_panel_section(doc, heading, new)
                    touched = True
                elif conflicts is not None:
                    conflicts.append({"id": f"{ev['event_id']}::{heading}", "kind": "panel", "item_id": "", "field": heading,
                                      "mine": new, "theirs": cur, "base": base.get(heading), "actor": ev.get("actor"), "at": now()})
            if touched:
                changes.append("textos do painel")
    return changes


def local_edit_events(base_doc: dict[str, Any] | None, work_doc: dict[str, Any], actor: str) -> list[dict[str, Any]]:
    """Diferenças do PROJECT_STATUS_TEXT.md da pasta em relação à base -> eventos (os mesmos do editor do painel)."""
    diff = pm.diff_docs(base_doc, work_doc)
    events = []
    for iid, item in diff["created"].items():
        clean = {k: v for k, v in item.items() if not k.startswith("_")}
        clean["want_id"] = iid
        events.append(make_event(f"novo-{uuid.uuid4().hex[:8]}", "create", clean, None, actor))
    for iid, fields in diff["fields"].items():
        events.append(make_event(iid, "content", {f: b for f, (a, b) in fields.items()}, {f: a for f, (a, b) in fields.items()}, actor))
    if diff["panel"]:
        events.append(make_event("", "panel", {h: b for h, (a, b) in diff["panel"].items()}, {h: a for h, (a, b) in diff["panel"].items()}, actor))
    return events


def compute_content(reason: str = "") -> dict[str, Any]:
    """Conteúdo efetivo = remoto + suas edições locais no PROJECT_STATUS_TEXT.md (prévia) + edições do painel na fila.
    Regrava a região de dados do painel.html somente se o hash mudou."""
    with CONTENT_LOCK:
        tip = remote_tip() if has_remote() else None
        r_text = read_blob(tip, CONTENT_NAME)
        b_rev = base_rev(tip)
        b_text = read_blob(b_rev, CONTENT_NAME) if b_rev else None
        w_text = worktree_content()
        source = {"file": CONTENT_NAME, "origin": "remoto" if r_text is not None else ("commit local" if b_text is not None else
                  ("pasta (não publicado)" if w_text is not None else "reserva local")),
                  "commit": (tip or "")[:10], "remote_missing": bool(has_remote() and tip and r_text is None)}
        if r_text is not None:
            try:
                if not CONTENT_CACHE.exists() or CONTENT_CACHE.read_text(encoding="utf-8") != r_text:
                    atomic_write(CONTENT_CACHE, r_text)
            except Exception:
                pass
            if tip:
                d = git("log", "-1", "--format=%cI%x1f%an", tip, "--", CONTENT_NAME)
                if d.returncode == 0 and "\x1f" in d.stdout:
                    source["changed_at"], source["changed_by"] = d.stdout.strip().split("\x1f", 1)
        start_text = r_text if r_text is not None else (b_text if b_text is not None else None)
        published = pm.parse(start_text) if start_text is not None else None
        doc = copy.deepcopy(published) if published else (pm.parse(w_text) if w_text is not None else fallback_content_doc())
        if published is None and w_text is None:
            source["origin"] = "reserva local"
        flags: dict[str, dict[str, Any]] = {}
        preview: dict[str, Any] = {"items": [], "created": [], "panel": [], "untracked": False}
        # 1) edições locais no arquivo da pasta (prévia)
        ref_text = b_text if b_text is not None else r_text
        if w_text is not None and published is not None and w_text != ref_text and w_text != r_text:
            work = pm.parse(w_text)
            base_doc = pm.parse(ref_text) if ref_text is not None else published
            diff = pm.diff_docs(base_doc, work)
            for iid, item in diff["created"].items():
                if iid not in doc["items"]:
                    doc["items"][iid] = copy.deepcopy(item)
                    doc["layout"].append(["item", iid])
                    flags.setdefault(iid, {})["lp"] = ["novo"]
                    preview["created"].append(iid)
            for iid, fields in diff["fields"].items():
                if iid in doc["items"]:
                    for f, (_, b) in fields.items():
                        pm.set_field(doc["items"][iid], f, b)
                    flags.setdefault(iid, {})["lp"] = sorted(fields)
                    preview["items"].append(iid)
            for h, (_, b) in diff["panel"].items():
                pm.set_panel_section(doc, h, b)
                preview["panel"].append(h)
            doc["issues"] = work.get("issues", [])
        elif w_text is not None and published is None:
            preview["untracked"] = True
        # 2) edições feitas no painel e ainda na fila de publicação
        box = [e for e in read_json(OUTBOX, []) if e.get("kind") in CONTENT_KINDS]
        provisional: dict[str, str] = {}
        if box:
            before = {i: pm.signature(it) for i, it in doc["items"].items()}
            apply_content_events(doc, box, None, provisional)
            for i, it in doc["items"].items():
                if before.get(i) != pm.signature(it):
                    flags.setdefault(i, {})["pp"] = True
            if any(e.get("kind") == "panel" for e in box):
                source["panel_pending"] = True
        if published is not None:
            refresh_definitions(published)
        elif DEFINITIONS == {} or reason == "inicio":
            refresh_definitions(doc)
        view = pm.build_view(doc, source={"source": source, "generated_at": now()}, flags=flags)
        # o hash ignora o carimbo de horário
        view["meta"]["hash"] = pm.sha(json.dumps([view["G"], [d["h"] for d in view["D"]]], ensure_ascii=False, sort_keys=True), 16)
        CONTENT.update(doc=doc, published=published, view=view, hash=view["meta"]["hash"], provisional=provisional,
                       meta={"hash": view["meta"]["hash"], "source": source, "preview": preview,
                             "issues": doc.get("issues", [])[:60], "pending": len(box)})
        if CONTENT.get("written_hash") != view["meta"]["hash"]:
            try:
                if pm.fill_html(LOCAL / HTML, GENERATED, view):
                    log(f"painel.html atualizado a partir do {CONTENT_NAME} ({len(view['D'])} itens; {reason or 'mudança'}).")
                CONTENT["written_hash"] = view["meta"]["hash"]
            except FileNotFoundError:
                log("painel.html não encontrado ao lado do server.py.")
            except ValueError as exc:
                log(f"painel.html sem região de dados ({exc}); substitua pelo painel.html da v6.")
        return CONTENT["meta"]


def ensure_content_published() -> str:
    """Primeira abertura sem atrito: se o GitHub ainda não tem o arquivo de conteúdo, publica a semente do zip.
    Quem abrir primeiro publica; os demais encontram o arquivo pronto. Nunca sobrescreve conteúdo existente."""
    if not has_remote() or not SEED.exists():
        return ""
    tip = remote_tip()
    if not tip or read_blob(tip, CONTENT_NAME) is not None:
        return ""
    with LOCK:
        box = read_json(OUTBOX, [])
        if any(e.get("kind") == "bootstrap" for e in box):
            return ""
        box.append(make_event("", "bootstrap", SEED.read_text(encoding="utf-8").replace("\r\n", "\n"), None, default_actor()))
        write_json(OUTBOX, box)
    schedule_publish(2)
    return f"{CONTENT_NAME} ainda não está no GitHub: o painel vai publicá-lo agora (uma única vez, para toda a equipe)."


def tidy_legacy_worktree() -> None:
    """Arquivo de conteúdo com o nome antigo, não rastreado, sobrando na pasta (zip da v5.0): vai para backups."""
    for legacy in LEGACY_CONTENT:
        path = ROOT / legacy
        if path.exists() and git("ls-files", "--error-unmatch", "--", legacy).returncode != 0:
            BACKUPS.mkdir(exist_ok=True)
            target = BACKUPS / f"{Path(legacy).stem}_v5.0_{dt.datetime.now().strftime('%Y%m%dT%H%M%S')}.md"
            shutil.move(str(path), str(target))
            log(f"{legacy} (nome antigo, não rastreado) movido para {target.name}.")


def watch_loop() -> None:
    """Detecta (a) PROJECT_STATUS_TEXT.md salvo na pasta e (b) commit, pull, checkout ou fetch (refs do Git) — só stat(), sem custo.
    O índice do Git fica de fora de propósito: o VS Code roda `git status` o tempo todo e isso não muda conteúdo."""
    gd = git("rev-parse", "--git-dir").stdout.strip()
    git_dir = (ROOT / gd) if gd and not Path(gd).is_absolute() else Path(gd or ROOT / ".git")
    step = max(1.0, float(CFG.get("watch_seconds") or 2))
    while not SHUTDOWN.is_set():
        targets = [ROOT / CONTENT_NAME, git_dir / "HEAD", git_dir / "FETCH_HEAD", git_dir / "ORIG_HEAD", git_dir / "packed-refs"]
        try:
            head_ref = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
            if head_ref.startswith("ref:"):
                targets.append(git_dir / head_ref[4:].strip())
            targets.append(git_dir / "refs" / "remotes" / CFG["remote"] / (META.get("branch") or "main"))
        except OSError:
            pass
        sig = []
        for t in targets:
            try:
                s = t.stat()
                sig.append((s.st_mtime_ns, s.st_size))
            except OSError:
                sig.append(None)
        if sig != CONTENT.get("watch_sig"):
            first = CONTENT.get("watch_sig") is None
            CONTENT["watch_sig"] = sig
            if not first:
                try:
                    compute_content("arquivo alterado na pasta")
                except Exception:
                    log(traceback.format_exc())
        SHUTDOWN.wait(step)


def content_item_source(iid: str) -> dict[str, Any] | None:
    with CONTENT_LOCK:
        doc = CONTENT.get("doc") or compute_content() and CONTENT["doc"]
        item = doc["items"].get(str(iid))
        if not item:
            return None
        clean = {k: v for k, v in item.items() if not k.startswith("_")}
        fields = {f: pm.get_field(item, f) for f in pm.field_names(item)}
        return {"item": clean, "fields": fields, "markdown": pm.serialize_item(item),
                "pending_create": str(iid) in CONTENT.get("provisional", {})}


def add_content_event(payload: dict[str, Any]) -> dict[str, Any]:
    actor = str(payload.get("actor") or default_actor())[:80]
    action = payload.get("action")
    eid = str(payload.get("event_id") or uuid.uuid4())
    with LOCK:
        box = read_json(OUTBOX, [])
        if action == "create":
            value = payload.get("value") or {}
            if not pm.one_line(value.get("title", "")):
                raise ValueError("A pendência nova precisa de um título.")
            meta = {k: str(v) for k, v in (value.get("meta") or {}).items() if k in pm.META_KEYS}
            secs = [[str(h), str(b)] for h, b in (value.get("sections") or []) if str(h).strip()]
            ev = make_event(f"novo-{uuid.uuid4().hex[:8]}", "create",
                            {"title": pm.one_line(value["title"]), "meta": meta, "sections": secs, "intro": "", "extra_meta": []}, None, actor, event_id=eid)
            box.append(ev)
        elif action == "edit":
            iid = str(payload.get("item_id") or "").lstrip("#")
            fields = payload.get("fields") or {}
            base = payload.get("base") or {}
            if not fields:
                return {"ok": True, "queued": 0, "detail": "Nada mudou."}
            prov = CONTENT.get("provisional", {}).get(iid)
            for f in fields:
                if not (f in ("title", "intro") or f.startswith(("meta:", "meta+:", "sec:", "sec+:"))):
                    raise ValueError(f"Campo inválido: {f}")
                if f.startswith("meta:") and f[5:] not in pm.META_KEYS:
                    raise ValueError(f"Campo inválido: {f}")
            if "title" in fields and not pm.one_line(fields["title"] or ""):
                raise ValueError("O título não pode ficar vazio.")
            if prov:  # item ainda não publicado: edita o próprio pedido de criação
                ev = next((e for e in box if e.get("item_id") == prov and e.get("kind") == "create"), None)
                if ev is None:
                    raise ValueError("Item novo não encontrado na fila.")
                tmp = pm.new_item("0", ev["value"].get("title", ""))
                tmp["meta"] = dict(ev["value"].get("meta") or tmp["meta"])
                tmp["sections"] = ev["value"].get("sections") or tmp["sections"]
                for f, v in fields.items():
                    pm.set_field(tmp, f, v)
                ev["value"].update(title=tmp["title"], meta=tmp["meta"], sections=tmp["sections"])
            else:
                if CONTENT.get("doc") is not None and iid not in CONTENT["doc"]["items"]:
                    raise ValueError(f"Item inexistente: {iid}")
                cur_item = (CONTENT.get("doc") or {}).get("items", {}).get(iid) or {}
                def current(f: str) -> Any:
                    try:
                        return pm.get_field(cur_item, f) if cur_item else None
                    except KeyError:
                        return None
                # base = o que a pessoa viu ao abrir o editor; se não veio, o valor atual (nunca vira conflito falso)
                box.append(make_event(iid, "content", fields, {f: (base[f] if f in base else current(f)) for f in fields}, actor, event_id=eid))
        elif action == "panel":
            sections = payload.get("sections") or {}
            if not sections:
                return {"ok": True, "queued": 0}
            pbase = payload.get("base") or {}
            doc = CONTENT.get("doc") or {}
            box.append(make_event("", "panel", sections, {h: (pbase[h] if h in pbase else pm.panel_section(doc, h)) for h in sections},
                                  actor, event_id=eid))
        else:
            raise ValueError(f"Ação inválida: {action}")
        write_json(OUTBOX, box)
    compute_content("edição no painel")
    schedule_publish()
    return {"ok": True, "queued": 1, "content": CONTENT["meta"]}


def publish_local_edits(actor: str, progress) -> dict[str, Any]:
    """Botão 'Publicar edições locais': transforma as diferenças do PROJECT_STATUS_TEXT.md da pasta em eventos,
    publica pelo mesmo caminho do painel e devolve o arquivo da pasta ao estado do Git (com backup)."""
    progress("Buscando a versão mais nova no GitHub…")
    fetch()
    tip = remote_tip() if has_remote() else None
    snapshot = worktree_content()
    if snapshot is None:
        return {"ok": False, "detail": f"Não há {CONTENT_NAME} na pasta do projeto."}
    r_text = read_blob(tip, CONTENT_NAME)
    b_rev = base_rev(tip)
    b_text = read_blob(b_rev, CONTENT_NAME) if b_rev else None
    with LOCK:
        box = read_json(OUTBOX, [])
        if r_text is None:
            box.append(make_event("", "bootstrap", snapshot, None, actor))
            progress(f"{CONTENT_NAME} ainda não existe no GitHub: será publicado inteiro.")
        else:
            ref = pm.parse(b_text if b_text is not None else r_text)
            events = local_edit_events(ref, pm.parse(snapshot), actor)
            if not events:
                return {"ok": True, "detail": "Nenhuma diferença em relação ao Git para publicar."}
            box.extend(events)
            progress(f"{len(events)} alteração(ões) do arquivo local enfileirada(s).")
        write_json(OUTBOX, box)
    res = sync("publicar edições locais", actor)
    if res.get("ok") and res.get("published"):
        path = ROOT / CONTENT_NAME
        if worktree_content() == snapshot:
            BACKUPS.mkdir(exist_ok=True)
            shutil.copy2(path, BACKUPS / f"PENDENCIAS_local_{dt.datetime.now().strftime('%Y%m%dT%H%M%S')}.md")
            if git("cat-file", "-e", f"HEAD:{CONTENT_NAME}").returncode == 0:
                git("checkout", "HEAD", "--", CONTENT_NAME)
            else:
                path.unlink(missing_ok=True)
            msg = auto_fast_forward(remote_tip())
            progress(msg or "Arquivo da pasta devolvido ao estado do Git (backup em backups/). Faça pull no VS Code para receber a versão publicada.")
        else:
            progress("O arquivo mudou durante a publicação; ele foi mantido como está (nada se perde).")
    compute_content("publicação de edições locais")
    return res


# =============================================================== ciclo de sincronização/publicação
def view_state() -> dict[str, Any]:
    with LOCK:
        cached = read_json(STATE_CACHE, None)
        state = normalize(cached.get("state") if isinstance(cached, dict) and cached.get("state") else initial_state())
        box = read_json(OUTBOX, [])
        apply_events(state, box, [])
        pending_items = {str(e.get("item_id")) for e in box}
        for iid in pending_items:
            if iid in state["items"]:
                state["items"][iid]["pending_publish"] = True
        return state


def decision_key(state: dict[str, Any]) -> str:
    """O que JUSTIFICA um commit: situação, comentários, rejeições e alertas de reconfirmação dos itens.
    Ficam de fora: resumo da auditoria, achados por item, evidências e varredura de commits
    (cada painel recalcula sozinho a partir do mesmo histórico do Git, então não precisam de commit)."""
    out = {}
    for iid, item in state.get("items", {}).items():
        flags = item.get("flags") or {}
        out[iid] = [item.get("status"), sorted(c.get("event_id") or "" for c in item.get("comments", [])),
                    sorted(item.get("dismissed", [])), (flags.get("reconfirm") or {}).get("reason") if flags.get("reconfirm") else None,
                    sorted(flags.get("tests_ack") or [])]
    return json.dumps(out, sort_keys=True, ensure_ascii=False)


COMMIT_KIND_ORDER = ["concluída", "reaberta", "revisar", "a confirmar", "reconfirmar", "reconfirmação ok", "em andamento",
                     "nova", "conteúdo", "comentário", "sugestão rejeitada", "testes reconhecidos"]


def commit_message(kind: str, changes: list[str], people: list[str]) -> str:
    """Mensagem agrupada por tipo; cada #ID aparece UMA vez no commit inteiro (no assunto ou no corpo).
    Ex.: (#status) conteúdo: #1, #31, #46; comentário: #5 +59 · Mateus"""
    groups: dict[str, list[int]] = {}
    other: list[str] = []
    seen: set[int] = set()
    parsed = []
    for c in changes:
        m = re.match(r"^#(\d+)\s+(.+?)(?:\s*\(.*\))?$", c.strip())
        if m:
            parsed.append((int(m.group(1)), m.group(2).strip()))
        elif c.startswith(("textos do painel", "cria ", "remove ")):
            if c not in other:
                other.append(re.sub(r"\s*\(.*\)$", "", c))
    rank = {k: i for i, k in enumerate(COMMIT_KIND_ORDER)}
    for iid, label in sorted(parsed, key=lambda x: (rank.get(x[1], len(rank)), x[0])):
        if iid in seen:
            continue
        seen.add(iid)
        groups.setdefault(label, []).append(iid)
    ordered = sorted(groups.items(), key=lambda kv: rank.get(kv[0], len(rank)))
    for _, ids in ordered:
        ids.sort()
    shown: list[str] = []
    rest: list[tuple[str, list[int]]] = []
    budget = 6
    for label, ids in ordered:
        take, left = ids[:budget], ids[budget:]
        budget -= len(take)
        if take:
            shown.append(f"{label}: " + ", ".join(f"#{i}" for i in take))
        if left:
            rest.append((label, left))
    hidden = sum(len(ids) for _, ids in rest)
    head = "; ".join(shown + other[:1]) or "sem mudanças de pendência"
    if hidden:
        head += f" +{hidden}"
    if kind == "audit":
        head = "verificação: " + head
    elif kind == "init":
        head = "inicializa painel"
    subject = f"{COMMIT_PREFIX} {head}".strip() + (f" · {', '.join(people)}" if people else "")
    body = [f"{label}: " + ", ".join(f"#{i}" for i in ids) for label, ids in rest] + other[1:]
    return subject + ("\n\n" + "\n".join(body) if body else "")


def sync(reason: str, actor: str = "", deep: dict[str, Any] | None = None, do_fetch: bool = True) -> dict[str, Any]:
    """Busca → reaplica a fila sobre a versão remota mais nova → decide se há motivo para commit.

    Reconciliação item a item e campo a campo: cada marcação ou edição é um evento com o valor que a pessoa viu
    (base). Na publicação, os eventos são reaplicados sobre a versão MAIS NOVA do GitHub; campos diferentes do
    mesmo item somam, comentários sempre somam, e só o MESMO campo mudado por outra pessoa vira conflito (o resto
    sai normalmente no commit). Sem conexão, a fila fica guardada e sai sozinha quando a conexão voltar.
    Antes de publicar, a proteção contra regressão confere que nada do remoto se perde.
    """
    actor = actor or default_actor()
    with LOCK:
        messages = []
        try:
            absorbed = absorb_worktree_markdown()
            if absorbed:
                messages.append(absorbed)
        except Exception as exc:
            messages.append(f"Não foi possível limpar o PROJECT_STATUS.md local: {exc}")
        result: dict[str, Any] = {"ok": True, "published": False, "commit": None, "changes": [], "detected": [], "conflicts": []}
        for attempt in range(1, 7):
            f = fetch() if do_fetch or attempt > 1 else {"ok": True}
            online = f.get("ok", False)
            if not online:
                messages.append(f.get("detail", ""))
            if not META.get("branch"):
                META["branch"] = status_branch() if has_remote() else (git("branch", "--show-current").stdout.strip() or "main")
            tip = remote_tip() if has_remote() else None
            remote_state = read_remote_state(tip)
            remote_file = bool(tip) and git("cat-file", "-e", f"{tip}:{MD_NAME}").returncode == 0
            if remote_file and remote_state is None:
                # arquivo existe no GitHub mas está ilegível: NUNCA republicar do zero (foi o que zerou o painel em 25/10)
                META["blocked"] = {"at": now(), "reason": "unreadable", "problems": [META.get("last_error") or "PROJECT_STATUS.md ilegível no GitHub."]}
                result.update(ok=False, detail="O PROJECT_STATUS.md do GitHub está ilegível. Nada foi publicado e sua fila está guardada. "
                                               "Restaure o arquivo pelo histórico do Git (git log -- PROJECT_STATUS.md) e clique em Buscar.")
                break
            cached = read_json(STATE_CACHE, None)
            if remote_state:
                start = normalize(remote_state)
            elif isinstance(cached, dict) and cached.get("state"):
                start = normalize(cached["state"])   # sem arquivo no remoto: parte do último estado conhecido, nunca do zero
            else:
                start = initial_state()
            state = copy.deepcopy(start)
            box = read_json(OUTBOX, [])
            conflicts: list[dict[str, Any]] = []
            c_events = [e for e in box if e.get("kind") in CONTENT_KINDS]
            r_text = read_blob(tip, CONTENT_NAME) if tip else None
            new_content: str | None = None
            c_changes: list[str] = []
            if c_events:
                boot = next((e for e in c_events if e.get("kind") == "bootstrap"), None)
                if r_text is not None:
                    cdoc = pm.parse(r_text)
                    if boot:
                        messages.append(f"{CONTENT_NAME} já existe no GitHub; as diferenças do seu arquivo continuam como prévia local.")
                elif boot:
                    cdoc = pm.parse(str(boot.get("value") or ""))
                    c_changes.append(f"cria {CONTENT_NAME}")
                else:
                    cdoc = copy.deepcopy(CONTENT.get("doc") or fallback_content_doc())
                    c_changes.append(f"cria {CONTENT_NAME}")
                c_changes += apply_content_events(cdoc, c_events, conflicts)
                if c_changes:
                    new_content = (str(boot.get("value")) if boot and r_text is None and len(c_changes) == 1 else pm.serialize(cdoc))
                    if new_content == r_text:
                        new_content = None
                if r_text is None and cdoc is not None and new_content is not None:
                    refresh_definitions(cdoc)
            for c in conflicts:  # quem mudou o arquivo de conteúdo por último (para o aviso de conflito)
                if c.get("kind") in ("content", "panel") and tip and not c.get("theirs_by"):
                    d = git("log", "-1", "--format=%an%x1f%cI", tip, "--", CONTENT_NAME)
                    if d.returncode == 0 and "\x1f" in d.stdout:
                        c["theirs_by"], c["theirs_at"] = d.stdout.strip().split("\x1f", 1)
            changes = apply_events(state, box, conflicts)
            changes = c_changes + changes if new_content is not None else changes
            if deep is not None:
                changes += apply_verification(state, deep, actor)
            # decisão de commit ANTES de ler os commits: a leitura entra no arquivo se houver commit, mas sozinha não gera
            # commit (todos os painéis leem o mesmo histórico e chegam ao mesmo resultado)
            must_publish = (remote_state is None or decision_key(state) != decision_key(start) or new_content is not None
                            or (deep is not None and audit_signature(state) != audit_signature(start)))
            try:
                detected = light_scan(state)
            except Exception as exc:
                detected = []
                messages.append(f"Leitura dos commits falhou: {exc}")
            result.update(changes=changes, detected=detected, conflicts=conflicts)
            if conflicts:
                old = read_json(CONFLICTS, [])
                have = {c["id"] for c in old}
                write_json(CONFLICTS, old + [c for c in conflicts if c["id"] not in have])
            if not must_publish:
                write_json(STATE_CACHE, {"tip": tip, "fetched_at": now(), "state": state})
                done_ids = {x["event_id"] for x in box}
                write_json(OUTBOX, [e for e in read_json(OUTBOX, []) if e["event_id"] not in done_ids])
                META["tip"] = tip
                META.pop("blocked", None)
                messages.append(auto_fast_forward(tip))
                result["detail"] = ("Atualizado. Nada para commitar." if not detected else
                                    f"Atualizado. {len(detected)} novidade(s) lida(s) dos commits — sem commit (todos os painéis leem o mesmo).")
                break
            if not online or not has_remote():
                write_json(STATE_CACHE, {"tip": tip, "fetched_at": now(), "state": copy.deepcopy(start)})
                result["ok"] = False
                err = META.get("fetch_error") or {}
                result["detail"] = ("Sem conexão com o GitHub: suas marcações ficaram guardadas e saem sozinhas quando a conexão voltar."
                                    + (f" Causa provável: {err.get('hint')}" if err.get("hint") else ""))
                break
            problems = regression_problems(remote_state, state, explained_ids(changes, detected, box))
            if problems:
                META["blocked"] = {"at": now(), "reason": "regression", "problems": problems[:20]}
                write_json(STATE_CACHE, {"tip": tip, "fetched_at": now(), "state": copy.deepcopy(start)})
                result["ok"] = False
                result["detail"] = ("Publicação bloqueada pela proteção contra regressão (nada foi enviado; sua fila está guardada): "
                                    + "; ".join(problems[:5]))
                log(result["detail"])
                break
            META.pop("blocked", None)
            state["generated_at"] = now()
            state["published_by"] = actor
            content = render_markdown(state)
            people = sorted({e.get("actor", "") for e in box if e.get("actor") and e.get("actor") not in AUTO_ACTORS
                             and e.get("actor") != "verificador automático"}) or [actor]
            kind = "init" if remote_state is None and not remote_file and not changes else ("audit" if deep is not None and not box else "human")
            msg = commit_message(kind, changes + detected, people)
            files: dict[str, str | None] = {MD_NAME: content}
            if new_content is not None:
                files[CONTENT_NAME] = new_content
                for legacy in LEGACY_CONTENT:  # aposenta o nome antigo do arquivo de conteúdo
                    if tip and git("cat-file", "-e", f"{tip}:{legacy}").returncode == 0:
                        files[legacy] = None
                        changes.append(f"remove {legacy} (renomeado para {CONTENT_NAME})")
            sha = commit_on_tip(tip, files, msg)
            ok, retry, out = push(sha)
            if ok:
                ids = {x["event_id"] for x in box}
                write_json(OUTBOX, [e for e in read_json(OUTBOX, []) if e["event_id"] not in ids])
                git("update-ref", remote_ref(), sha)
                write_json(STATE_CACHE, {"tip": sha, "fetched_at": now(), "state": state})
                META["tip"] = sha
                META["last_publish"] = now()
                result.update(published=True, commit=sha, detail=f"Commit {sha[:7]} publicado: {msg.splitlines()[0]}")
                log(f"Publicado {sha[:7]}: {msg.splitlines()[0]}")
                messages.append(auto_fast_forward(sha))
                break
            if not retry:
                write_json(STATE_CACHE, {"tip": tip, "fetched_at": now(), "state": start})
                META["fetch_error"] = classify_fetch_error(out)
                result["ok"] = False
                result["detail"] = ("O GitHub recusou a publicação. Suas marcações ficaram guardadas. "
                                    + META["fetch_error"]["hint"] + " Detalhe: " + out[-400:])
                META["last_error"] = result["detail"]
                break
            log(f"Alguém publicou antes (tentativa {attempt}); buscando de novo e reaplicando…")
            time.sleep(min(2 * attempt, 6))
        else:
            result["ok"] = False
            result["detail"] = "Muitas publicações simultâneas; tento de novo em instantes. Nada foi perdido."
            schedule_publish(30)
        result["messages"] = [m for m in messages if m]
        META["last_message"] = result.get("detail", "")
        try:
            compute_content(reason)
        except Exception:
            log(traceback.format_exc())
        if result["ok"]:
            META["last_error"] = None
        return result


def schedule_publish(delay: float | None = None) -> None:
    global PUBLISH_TIMER
    if PUBLISH_TIMER is not None:
        PUBLISH_TIMER.cancel()

    def run() -> None:
        try:
            if read_json(OUTBOX, []):
                r = sync("alterações feitas no painel")
                log(r.get("detail", ""))
        except Exception:
            log(traceback.format_exc())

    PUBLISH_TIMER = threading.Timer(delay if delay is not None else float(CFG["publish_delay_seconds"]), run)
    PUBLISH_TIMER.daemon = True
    PUBLISH_TIMER.start()


def add_event(payload: dict[str, Any]) -> dict[str, Any]:
    iid = str(payload.get("item_id") or "").lstrip("#")
    iid = str(int(iid)) if iid.isdigit() else iid
    if iid not in DEFINITIONS:
        if iid in CONTENT.get("provisional", {}):
            raise ValueError(f"O #{iid} ainda está aguardando publicação; marque a situação depois que ele for publicado.")
        raise ValueError(f"Item inexistente: {iid}")
    actor = str(payload.get("actor") or default_actor())[:80]
    action = payload.get("action")
    current = view_state()["items"][iid]
    events = []
    note = str(payload.get("note") or "").strip()[:5000]
    eid = str(payload.get("event_id") or uuid.uuid4())
    if action == "progress":
        raise ValueError("'Estou fazendo' é uma marcação só sua, guardada no navegador; não vai para o GitHub.")
    target = {"confirm_done": "done", "reopen": "open", "set_status": payload.get("status")}.get(action)
    if action in ("confirm_done", "reopen", "set_status"):
        if target not in STATUSES:
            raise ValueError("Situação inválida.")
        if target == "done" and current.get("status") != "done":
            check = quick_check(iid)
            if check.get("verdict") != "atendida" and len(note) < 15:
                raise ValueError("O verificador não confirma esta conclusão ("
                                 + str(check.get("verdict_text") or check.get("verdict")) + "). Escreva um comentário "
                                 "de pelo menos 15 caracteres explicando por que ela está concluída.")
            failing = sorted({a["nodeid"] for a in check.get("affected_by_tests") or []}
                             | set(((current.get("flags") or {}).get("review_reason") or {}).get("tests") or []))
            if failing:
                events.append(make_event(iid, "ack", failing, None, actor, event_id=eid + "-a"))
            if check.get("verdict") != "atendida":
                note = (f"[Concluída sem confirmação do verificador: {check.get('verdict_text') or check.get('verdict')}] " + note)[:5000]
        events.append(make_event(iid, "status", target, current.get("status"), actor, event_id=eid))
        if note:
            events.append(make_event(iid, "comment", note, None, actor, event_id=eid + "-c"))
    elif action == "comment":
        if not note:
            raise ValueError("Comentário vazio.")
        events.append(make_event(iid, "comment", note, None, actor, event_id=eid))
    elif action == "dismiss":
        shas = [str(e.get("sha") or e.get("commit") or "")[:12] for e in current.get("evidence", [])
                if e.get("type") in ("commit_task_reference", "commit_source_match", "commit")]
        events.append(make_event(iid, "dismiss", shas, current.get("status"), actor, event_id=eid))
    else:
        raise ValueError(f"Ação inválida: {action}")
    with LOCK:
        box = read_json(OUTBOX, [])
        have = {e["event_id"] for e in box}
        box.extend(e for e in events if e["event_id"] not in have)
        write_json(OUTBOX, box)
    schedule_publish()
    return {"ok": True, "queued": len(events)}


def resolve_conflict(payload: dict[str, Any]) -> dict[str, Any]:
    cid = payload.get("id")
    choice = payload.get("choice")
    actor = str(payload.get("actor") or default_actor())
    with LOCK:
        items = read_json(CONFLICTS, [])
        found = next((c for c in items if c["id"] == cid), None)
        if not found:
            return {"ok": True}
        write_json(CONFLICTS, [c for c in items if c["id"] != cid])
        if choice in ("mine", "edit") and found.get("kind") in ("content", "panel"):
            if found.get("field") == "*":
                return {"ok": True}
            value = str(payload.get("value") if choice == "edit" else found["mine"])
            ev = make_event(found["item_id"], found["kind"], {found["field"]: value}, {found["field"]: found.get("theirs")}, actor)
            ev["force"] = True
            box = read_json(OUTBOX, [])
            box.append(ev)
            write_json(OUTBOX, box)
            compute_content("conflito resolvido")
            schedule_publish(1)
            return {"ok": True}
        if choice == "mine":
            ev = make_event(found["item_id"], "status", found["mine"], view_state()["items"][found["item_id"]]["status"], actor)
            ev["force"] = True
            box = read_json(OUTBOX, [])
            box.append(ev)
            write_json(OUTBOX, box)
            schedule_publish(1)
    return {"ok": True}


# =============================================================== jobs em segundo plano
def start_job(kind: str, actor: str) -> dict[str, Any]:
    if not JOB_LOCK.acquire(blocking=False):
        if JOB["running"]:  # um trabalho visível (clique) já está rodando: o painel acompanha esse
            return {"ok": True, "job": job_public(), "detail": "Já existe um trabalho em andamento."}
        # trava ocupada por trabalho em segundo plano (busca automática): espera ela terminar
        if not JOB_LOCK.acquire(timeout=180):
            return {"ok": False, "busy": True, "job": None,
                    "error": "A busca automática ainda está rodando. Tente de novo em instantes."}
    JOB.update(id=str(uuid.uuid4()), running=True, kind=kind, log=[], result=None, error=None, started=now(), finished=None)

    def progress(msg: str) -> None:
        JOB["log"].append(f"{dt.datetime.now().strftime('%H:%M:%S')} {msg}")
        JOB["log"] = JOB["log"][-80:]
        log(msg)

    def work() -> None:
        try:
            if kind == "publish_local":
                res = publish_local_edits(actor, progress)
            elif kind == "audit":
                progress("Buscando o mais recente no GitHub…")
                pre = sync("busca antes da verificação", actor)
                for m in pre.get("messages", []):
                    progress(m)
                report = run_verification(progress)
                added = queue_suggested_criteria(report)
                if added:
                    progress(f"{added} pendência(s) ganharam um critério de teste no “④ Pronto quando”.")
                progress("Aplicando o resultado e publicando se alguma pendência mudar…")
                res = sync("verificação do pronto quando", actor, deep=report)
            else:
                progress("Buscando o mais recente no GitHub…")
                res = sync("busca", actor)
                schedule_quick_verification()
            for m in res.get("messages", []):
                progress(m)
            progress(res.get("detail", ""))
            for c in res.get("changes", [])[:80]:
                progress("• " + c)
            for c in res.get("detected", [])[:80]:
                progress("· lido dos commits: " + c)
            JOB["result"] = res
        except Exception as exc:
            JOB["error"] = f"{exc}"
            progress("ERRO: " + str(exc))
            log(traceback.format_exc())
        finally:
            JOB["running"] = False
            JOB["finished"] = now()
            JOB_LOCK.release()

    threading.Thread(target=work, daemon=True).start()
    return {"ok": True, "job": job_public()}


QUICK = {"running": False, "sha": None}


def schedule_quick_verification() -> None:
    """Depois de cada busca, confere o “Pronto quando” de todas as pendências sem pytest (não publica nada)."""
    tip = remote_tip() if has_remote() else git("rev-parse", "HEAD").stdout.strip()
    quick = read_json(REPORT_QUICK, None)
    content_hash = CONTENT.get("hash")
    if QUICK["running"] or (isinstance(quick, dict) and quick.get("sha") == tip and quick.get("content_hash") == content_hash):
        return

    def work() -> None:
        QUICK["running"] = True
        try:
            rep = run_verification(lambda _m: None, quick=True)
            rep["content_hash"] = content_hash
            write_json(REPORT_QUICK, rep)
        except Exception:
            log(traceback.format_exc())
        finally:
            QUICK["running"] = False

    threading.Thread(target=work, daemon=True).start()


def current_report() -> dict[str, Any] | None:
    """Relatório mais recente: completo ou rápido (o rápido reaproveita os testes do completo do mesmo commit)."""
    full, quick = read_json(REPORT, None), read_json(REPORT_QUICK, None)
    cands = [r for r in (full, quick) if isinstance(r, dict) and r.get("schema_version", 0) >= 2 and isinstance(r.get("tasks"), dict)]
    if not cands:
        return None
    best = max(cands, key=lambda r: str(r.get("generated_at", "")))
    out = {k: v for k, v in best.items() if k not in ("test_cases", "findings")}
    out["full_at"] = (full or {}).get("generated_at") if isinstance(full, dict) else None
    return out


def job_public() -> dict[str, Any]:
    r = JOB.get("result") or {}
    return {"id": JOB["id"], "running": JOB["running"], "kind": JOB["kind"], "log": JOB["log"][-40:], "error": JOB["error"],
            "started": JOB["started"], "finished": JOB["finished"],
            "result": {k: r.get(k) for k in ("ok", "published", "commit", "detail", "changes", "detected", "conflicts")} if r else None}


def periodic_loop() -> None:
    interval = max(5, int(CFG["fetch_interval_minutes"])) * 60
    time.sleep(3)
    while not SHUTDOWN.is_set():
        try:
            if JOB_LOCK.acquire(blocking=False):
                try:
                    r = sync("busca automática")
                    log("Busca automática: " + r.get("detail", ""))
                    schedule_quick_verification()
                finally:
                    JOB_LOCK.release()  # sem mexer em JOB: o último trabalho clicado continua sendo o exibido
        except Exception:
            log(traceback.format_exc())
        # se houver fila pendente (ex.: sem internet), tenta de novo em 5 min
        wait = 300 if read_json(OUTBOX, []) else interval
        SHUTDOWN.wait(wait)


def api_state() -> dict[str, Any]:
    state = view_state()
    report = current_report()
    cached = read_json(STATE_CACHE, {})
    box = read_json(OUTBOX, [])
    return {"ok": True, "version": VERSION, "state": state,
            "meta": {**META, "remote": CFG["remote"], "outbox": len(box), "conflicts": read_json(CONFLICTS, []),
                     "outbox_since": min((e.get("ts") or "" for e in box), default=None), "version": VERSION,
                     "reference": reference_status(), "quick_running": QUICK["running"],
                     "actor_default": default_actor(), "tip": cached.get("tip") if isinstance(cached, dict) else None,
                     "fetch_interval_minutes": CFG["fetch_interval_minutes"],
                     "report_at": (report or {}).get("generated_at") if isinstance(report, dict) else None,
                     "report_sha": (report or {}).get("sha") if isinstance(report, dict) else None,
                     "version_key": hashlib.md5(canonical(state).encode("utf-8")).hexdigest(),
                     "publish_delay_seconds": CFG["publish_delay_seconds"],
                     "content": CONTENT.get("meta") or compute_content()},
            "job": job_public()}


# =============================================================== HTTP
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(LOCAL), **kw)

    def log_message(self, fmt: str, *args: Any) -> None:
        pass

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ("127.0.0.1", "localhost")

    def do_GET(self) -> None:
        if not self.host_ok():
            self.send_error(403)
            return
        path = urlparse(self.path).path
        if path in ("/", ""):
            self.send_response(302)
            self.send_header("Location", "/" + HTML)
            self.end_headers()
            return
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if path == "/api/ping":
            return self.send_json({"ok": True, "app": "painel-srag", "version": VERSION})
        if path == "/api/state":
            try:
                return self.send_json(api_state())
            except Exception as exc:
                log(traceback.format_exc())
                return self.send_json({"ok": False, "error": str(exc)}, 500)
        if path == "/api/job":
            return self.send_json({"ok": True, "job": job_public()})
        if path == "/api/report":
            return self.send_json({"ok": True, "report": current_report()})
        if path == "/api/check":
            iid = parse_qs(urlparse(self.path).query).get("id", [""])[0].lstrip("#")
            try:
                return self.send_json(quick_check(iid))
            except Exception as exc:
                log(traceback.format_exc())
                return self.send_json({"ok": False, "error": str(exc)}, 500)
        if path == "/api/check-local":
            iid = parse_qs(urlparse(self.path).query).get("id", [""])[0].lstrip("#")
            try:
                return self.send_json(local_check(iid))
            except Exception as exc:
                log(traceback.format_exc())
                return self.send_json({"ok": False, "error": str(exc)}, 500)
        if path == "/api/content/hash":
            return self.send_json({"ok": True, "hash": CONTENT.get("hash")})
        if path == "/api/content/index":
            view = CONTENT.get("view") or (compute_content() and CONTENT["view"])
            return self.send_json({"ok": True, "hash": view["meta"]["hash"], "meta": view["meta"], "G": view["G"],
                                   "order": [d["id"] for d in view["D"]], "items": {d["id"]: d["h"] for d in view["D"]},
                                   "content": CONTENT.get("meta")})
        if path == "/api/content/items":
            view = CONTENT.get("view") or (compute_content() and CONTENT["view"])
            q = parse_qs(urlparse(self.path).query).get("ids", [""])[0]
            wanted = None if q in ("", "all") else set(q.split(","))
            return self.send_json({"ok": True, "hash": view["meta"]["hash"], "items": [d for d in view["D"] if wanted is None or d["id"] in wanted]})
        if path == "/api/item":
            iid = parse_qs(urlparse(self.path).query).get("id", [""])[0].lstrip("#")
            src = content_item_source(iid)
            return self.send_json({"ok": bool(src), **(src or {"error": f"Item #{iid} não encontrado."})}, 200 if src else 404)
        if path == "/api/panel-texts":
            doc = CONTENT.get("doc") or (compute_content() and CONTENT["doc"])
            return self.send_json({"ok": True, "sections": (doc.get("panel") or {}).get("sections", [])})
        if path != "/" + HTML:
            self.send_error(404)
            return
        if not GENERATED.exists():
            try:
                compute_content("primeira abertura")
                pm.fill_html(LOCAL / HTML, GENERATED, CONTENT["view"], force=True)
            except Exception:
                log(traceback.format_exc())
        body = (GENERATED if GENERATED.exists() else LOCAL / HTML).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if not self.host_ok() or self.headers.get("X-Painel") != "1":
            self.send_json({"ok": False, "error": "Origem não autorizada."}, 403)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 3_000_000:
                raise ValueError("Requisição grande demais.")
            payload = json.loads(self.rfile.read(length) or b"{}")
            path = urlparse(self.path).path
            actor = str(payload.get("actor") or "")[:80]
            if path == "/api/event":
                res = add_event(payload)
            elif path == "/api/fetch":
                res = start_job("fetch", actor)
            elif path in ("/api/audit", "/api/verify"):
                res = start_job("audit", actor)
            elif path == "/api/conflict":
                res = resolve_conflict(payload)
            elif path == "/api/content":
                res = add_content_event(payload)
            elif path == "/api/preview":
                res = {"ok": True, "html": pm.render(str(payload.get("markdown") or "")[:200_000])}
            elif path == "/api/publish-local":
                res = start_job("publish_local", actor)
            elif path == "/api/shutdown":
                self.send_json({"ok": True})
                threading.Thread(target=shutdown_soon, daemon=True).start()
                return
            else:
                return self.send_json({"ok": False, "error": "Endpoint inexistente."}, 404)
            self.send_json(res)
        except Exception as exc:
            log(traceback.format_exc())
            self.send_json({"ok": False, "error": str(exc)}, 400)


HTTPD: socketserver.ThreadingTCPServer | None = None


def shutdown_soon() -> None:
    time.sleep(0.4)
    try:
        if read_json(OUTBOX, []):
            sync("publicação ao encerrar")
    except Exception:
        pass
    SHUTDOWN.set()
    if HTTPD:
        HTTPD.shutdown()


def running_version(port: int) -> str | None:
    """Versão do painel aberto nesta porta (None = nada aberto ou outro programa)."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=1.5) as r:
            data = json.loads(r.read().decode())
            return str(data.get("version") or "antiga") if data.get("app") == "painel-srag" else None
    except Exception:
        return None


def already_running(port: int) -> bool:
    return running_version(port) is not None


def replace_old_instance(port: int) -> bool:
    """Painel de versão anterior aberto: pede para ele encerrar (ele publica a fila antes) e espera a porta liberar."""
    found = running_version(port)
    if found is None or found == VERSION:
        return False
    log(f"Painel {found} aberto na porta {port}: encerrando para abrir a versão {VERSION}.")
    stop(port, quiet=True)
    for _ in range(60):
        if running_version(port) is None:
            time.sleep(0.5)
            return True
        time.sleep(0.5)
    return False


def serve(port: int, open_browser: bool) -> None:
    global HTTPD
    problem = repo_guard()
    if problem:
        log("O painel NÃO foi aberto: " + problem)
        raise SystemExit("O painel NÃO foi aberto: " + problem)
    url = f"http://127.0.0.1:{port}/{HTML}"
    socketserver.ThreadingTCPServer.allow_reuse_address = os.name != "nt"
    socketserver.ThreadingTCPServer.daemon_threads = True
    for candidate in range(port, port + 6):
        replace_old_instance(candidate)
    for candidate in range(port, port + 6):
        url = f"http://127.0.0.1:{candidate}/{HTML}"
        if already_running(candidate):
            log(f"Painel já estava aberto em {url}; abrindo a aba.")
            if open_browser:
                webbrowser.open(url)
            return
        try:
            HTTPD = socketserver.ThreadingTCPServer(("127.0.0.1", candidate), Handler)
            break
        except OSError:
            continue
    else:
        raise SystemExit(f"Portas {port}-{port + 5} ocupadas. Ajuste 'port' em config.json.")
    log(f"Painel {VERSION} ativo em {url} · repositório {ROOT}")
    if has_remote():
        META["branch"] = status_branch()
    try:
        tidy_legacy_worktree()
    except Exception:
        log(traceback.format_exc())
    try:
        compute_content("inicio")
    except Exception:
        log(traceback.format_exc())
    threading.Thread(target=watch_loop, daemon=True).start()
    def first_run() -> None:
        try:
            fetch()
            schedule_quick_verification()
            msg = ensure_content_published()
            if msg:
                log(msg)
                META["last_message"] = msg
        except Exception:
            log(traceback.format_exc())
    threading.Thread(target=first_run, daemon=True).start()
    threading.Thread(target=periodic_loop, daemon=True).start()
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        HTTPD.serve_forever()
    finally:
        HTTPD.server_close()


def stop(port: int, quiet: bool = False) -> None:
    import urllib.request
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/shutdown", data=b"{}", method="POST",
                                     headers={"X-Painel": "1", "Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=60)
        if not quiet:
            print("Painel encerrado.")
    except Exception:
        if not quiet:
            print("O painel não estava aberto.")


def main() -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    parser = argparse.ArgumentParser(description="Painel de Pendências SRAG")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("start", "serve", "stop"):
        p = sub.add_parser(name)
        p.add_argument("--port", type=int, default=int(CFG["port"]))
    sub.add_parser("sync")
    sub.add_parser("audit")
    sub.add_parser("diagnostico")
    sub.add_parser("gerar", help="Regenera o painel.html a partir do PROJECT_STATUS_TEXT.md (sem servidor)")
    sub.add_parser("validar", help="Lista problemas de formato do PROJECT_STATUS_TEXT.md")
    mg = sub.add_parser("migrar", help="Cria o PROJECT_STATUS_TEXT.md a partir do painel atual (se ainda não existir)")
    mg.add_argument("--forcar", action="store_true", help="Sobrescreve o PROJECT_STATUS_TEXT.md da pasta (com backup)")
    a = parser.parse_args()
    if a.cmd == "gerar":
        meta = compute_content("linha de comando")
        CONTENT["written_hash"] = None
        changed = pm.fill_html(LOCAL / HTML, GENERATED, CONTENT["view"], force=True)
        print(json.dumps({"painel_html": str(GENERATED), "regravado": changed, "itens": len(CONTENT["view"]["D"]), **meta},
                         ensure_ascii=False, indent=1, default=str))
        return
    if a.cmd == "validar":
        text = worktree_content() or read_blob(remote_tip() if has_remote() else None, CONTENT_NAME)
        if text is None:
            print(f"{CONTENT_NAME} não encontrado (pasta nem remoto).")
            raise SystemExit(1)
        doc = pm.parse(text)
        issues = doc["issues"]
        print(f"{CONTENT_NAME}: {len(doc['items'])} itens, {len(issues)} aviso(s); ida-e-volta {'ok' if pm.serialize(pm.parse(pm.serialize(doc))) == pm.serialize(doc) else 'DIFERENTE'}.")
        for i in issues:
            print(f"- [{i['level']}] {i['msg']}")
        raise SystemExit(1 if any(i["level"] == "erro" for i in issues) else 0)
    if a.cmd == "migrar":
        target = ROOT / CONTENT_NAME
        if target.exists() and not a.forcar:
            print(f"{target} já existe. Use --forcar para recriar (o atual vai para backups/).")
            raise SystemExit(1)
        if target.exists():
            BACKUPS.mkdir(exist_ok=True)
            shutil.copy2(target, BACKUPS / f"PENDENCIAS_antes_migrar_{int(time.time())}.md")
        doc = fallback_content_doc() if not CONTENT_CACHE.exists() else pm.parse(CONTENT_CACHE.read_text(encoding="utf-8"))
        atomic_write(target, pm.serialize(doc))
        print(f"{target} criado com {len(doc['items'])} itens. Revise, faça commit e push pelo VS Code.")
        return
    if a.cmd in ("start", "serve"):
        serve(a.port, a.cmd == "start")
        return
    if a.cmd == "stop":
        stop(a.port)
        return
    if a.cmd in ("sync", "audit"):
        problem = repo_guard()
        if problem:
            raise SystemExit(problem)
        try:
            compute_content("linha de comando")
        except Exception as exc:
            print(f"Aviso: conteúdo não carregado ({exc}); usando definições locais.")
    if a.cmd == "sync":
        print(json.dumps(sync("linha de comando"), ensure_ascii=False, indent=1, default=str))
    elif a.cmd == "audit":
        report = run_verification(print)
        queue_suggested_criteria(report)
        print(json.dumps(sync("verificação (linha de comando)", deep=report), ensure_ascii=False, indent=1, default=str))
    else:
        print(json.dumps({"versao": VERSION, "python": sys.version, "repositorio": str(ROOT), "git": shutil.which("git"),
                          "remoto": has_remote(), "branch_status": status_branch() if has_remote() else None,
                          "pasta_ok": repo_guard() or "ok", "busca": fetch(),
                          "erro_de_busca": META.get("fetch_error"),
                          "usuario_git": default_actor(), "itens_definidos": len(DEFINITIONS),
                          "fila_pendente": len(read_json(OUTBOX, [])), "auditoria": AUDIT_SCRIPT.exists(),
                          "conteudo": compute_content("diagnostico")},
                         ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
