#!/usr/bin/env python3
r"""
Verificador do Painel de Pendências SRAG ("Pronto quando") e auditoria do repositório.

O que faz
---------
1. Lê, em cada pendência do PROJECT_STATUS_TEXT.md, a seção "④ Pronto quando" e confere
   cada critério contra o repositório (arquivo existe, função definida, chave do YAML,
   teste passa, notebook executado, saída de notebook...). Cada critério recebe um
   resultado: atendido, não atendido, indisponível nesta máquina, confirmação manual,
   ou critério inválido.
2. Roda o pytest rápido numa cópia limpa do commit verificado (git worktree), lê o
   resultado teste a teste e liga cada teste que falhou às pendências cujos arquivos
   ele importa. Para cada ligação, propõe um critério novo "teste: ... passa".
3. Lista, por pendência, os commits que a citam (marcadores e menções) e os commits
   que só mexeram nos arquivos dela. NUNCA muda status: só informa.
4. Detecta mudanças em chaves críticas da configuração (anos dos blocos, features,
   alvo, gates, finalista...) e diz se o commit que mudou citou alguma pendência.
5. Faz uma varredura estática enxuta (sintaxe, notebooks com erro salvo, segredos,
   conflitos de merge reais, padrões de performance em código Python).
6. Confere a higiene do .gitignore DESTA máquina: código, configuração, testes, notebooks
   e o código do painel que o .gitignore esconde (nunca chegam ao Git) e arquivos novos
   ainda não adicionados ao Git. Sai só no terminal e em "git_hygiene" do relatório local;
   nunca entra no PROJECT_STATUS.md compartilhado.

O verificador NUNCA grava o PROJECT_STATUS.md. Só produz um relatório
(.srag-status-local/deep_git_audit_report.json) que o painel lê. A única escrita
opcional é --aplicar-sugestoes, que acrescenta critérios "teste:" ao
PROJECT_STATUS_TEXT.md local (o painel publica a edição como qualquer outra).

Formato de um critério (uma linha por critério, dentro de "### ④ Pronto quando")
---------------------------------------------------------------------------------
    - <verbo>: <argumentos> | <descrição detalhada em português>

    verbo                argumentos                                 atendido quando
    existe               caminho                                    o arquivo existe
    nao-existe           caminho                                    o arquivo não existe
    nao-vazio            caminho                                    existe e tem conteúdo (Python: ao menos 1 instrução além da docstring)
    define               caminho :: Nome (ou Classe.metodo)         função, classe ou variável com esse nome existe (AST; comentários não contam)
    nao-define           caminho :: Nome                            o nome não está definido
    contem               caminho :: texto                           o texto aparece (Python: fora de comentários; notebook: código sem comentários + Markdown)
    nao-contem           caminho :: texto                           o texto não aparece (mesma regra de busca de contem)
    yaml                 caminho :: chave.pontilhada OP valor       OP: = | != | contem | nao-contem | existe | nao-existe
    json                 caminho :: chave.pontilhada OP valor       idem, para arquivos JSON
    teste                tests/arquivo.py[::teste]                  o(s) teste(s) passam no pytest rápido (pelo menos 1 coletado)
    notebook-executado   caminho.ipynb                              todas as células de código executadas e nenhuma saída de erro salva
    notebook-saida       caminho.ipynb :: texto                     alguma saída salva contém o texto
    manual               (nenhum)                                   só uma pessoa confirma: exige comentário ao concluir

    Argumentos podem vir entre crases. Use " :: " (com espaços) e " | " (com espaços)
    como separadores; textos que contenham esses separadores devem vir entre crases.
    Exemplo:
    - define: `src/data/split.py` :: `criar_group_id` | A função criar_group_id existe em src/data/split.py ...
    - yaml: `configs/supervised.yaml` :: `gates.G6_finalistas_tuning.status` = `aprovado` | O gate G6 está aprovado ...

De onde vem a verdade
---------------------
- Arquivos rastreados pelo Git: lidos do commit verificado (padrão: origin/<branch
  principal>), igual para todo o time. Mudanças locais não commitadas NÃO contam.
- Arquivos novos que ainda não foram commitados (nem ignorados) NÃO contam: o resultado
  é "não atendido", com o aviso de que falta git add/commit/push.
- Arquivos ignorados pelo Git (outputs/, data/...): só existem em cada máquina.
  Se existirem, o resultado é "atendido (local)"; se não existirem, o resultado é
  "indisponível nesta máquina" (nunca "não atendido"), porque a ausência local não
  prova que a tarefa não foi feita por outra pessoa.
- Exceção: código e configuração (.py, .ipynb, .yaml, .toml...) e o código do painel que o
  .gitignore esconde NUNCA contam como "atendido (local)": o resultado é "não atendido", porque esses
  arquivos precisam estar no Git para valer para o time.

Uso (na raiz do repositório, com o venv do projeto)
---------------------------------------------------
    .\.venv\Scripts\python.exe .srag-status-local\deep_git_project_audit.py
    .\.venv\Scripts\python.exe .srag-status-local\deep_git_project_audit.py --item 142
    .\.venv\Scripts\python.exe .srag-status-local\deep_git_project_audit.py --sem-testes
    .\.venv\Scripts\python.exe .srag-status-local\deep_git_project_audit.py --aplicar-sugestoes
    .\.venv\Scripts\python.exe .srag-status-local\deep_git_project_audit.py --self-test

Código de saída: 0 ok · 1 erro de execução · 2 critérios inválidos no PROJECT_STATUS_TEXT.md.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - o projeto exige pyyaml; o verificador avisa se faltar
    yaml = None

SCHEMA_VERSION = 2
REPORT_NAME = "deep_git_audit_report.json"
PANEL_COMMIT_PREFIXES = ("(#status)", "chore(status)")   # commits do próprio painel: nunca são evidência
CONTENT_NAME = "PROJECT_STATUS_TEXT.md"
STATUS_NAME = "PROJECT_STATUS.md"
CRITERIA_HEADING = "④ Pronto quando"

# ------------------------------------------------------------------ marcadores em mensagens de commit
EXPLICIT_MARKER = re.compile(
    r"\[(done|progress|reopen|feito|conclu[ií]d[oa]|andamento|reabr[ei]r?)\s*[:#]\s*(?:id)?#?\s*0*(\d+)\]", re.I)
TASK_REFERENCE = re.compile(
    r"(?<![\wÀ-ÿ])(?:tarefas?|tasks?|itens?|item|pend[eê]ncias?|cards?)\s*(?:n[ºo°.]\s*)?#?\s*0*(\d{1,4})(?!\d)", re.I)
HASH_REFERENCE = re.compile(r"(?<![\w/&])#(\d{1,4})\b")
PULL_REQUEST = re.compile(r"(?i)pull\s+request\s+#\d+")
MARKER_ACTION = {"done": "done", "feito": "done", "concluido": "done", "concluído": "done", "concluida": "done",
                 "concluída": "done", "progress": "progress", "andamento": "progress", "reopen": "reopen",
                 "reabrir": "reopen", "reabre": "reopen", "reabri": "reopen"}

# ------------------------------------------------------------------ varredura estática
MERGE_CONFLICT = re.compile(r"^(<{7} |={7}$|>{7} )", re.M)   # só marcadores reais do Git
SECRET = re.compile(r"(?i)(password|passwd|pwd|secret|token|api[_-]?key|private[_-]?key)"
                    r"\s*[:=]\s*['\"]([^'\"\n]{8,})['\"]")
PRIVATE_KEY = re.compile(r"-----BEGIN [^-]+ PRIVATE KEY-----", re.I)
PERFORMANCE_RULES: list[tuple[str, re.Pattern[str], str, str]] = [
    ("dense-one-hot", re.compile(r"sparse_output\s*=\s*False"), "medium",
     "OneHotEncoder denso: em milhões de linhas pode estourar a memória (aceitável em amostras pequenas)."),
    ("toarray", re.compile(r"\.toarray\s*\("), "medium", "Conversão de matriz esparsa para densa."),
    ("iterrows", re.compile(r"\.iterrows\s*\("), "low", "iterrows tende a ser lento em tabelas grandes."),
    ("apply-axis-1", re.compile(r"\.apply\s*\([^\n]*axis\s*=\s*1"), "low", "apply(axis=1) tende a ser lento."),
    ("read-parquet-wide", re.compile(r"read_parquet\s*\((?![^\)]*columns\s*=)"), "low",
     "Leitura de Parquet sem escolher colunas."),
]
CODE_SUFFIXES = {".py", ".pyi"}
SCAN_SUFFIXES = {".py", ".pyi", ".ipynb", ".json", ".yaml", ".yml", ".toml"}
NEVER_SCAN = {STATUS_NAME, CONTENT_NAME, "docs/PROJECT_COMPLETE_REFERENCE.txt"}
EXCLUDED_PARTS = {".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".ipynb_checkpoints",
                  "node_modules", ".srag-status-local"}

# ------------------------------------------------------------------ higiene do .gitignore
# Pastas cujo código/configuração precisa estar no Git. Só extensões de código e configuração contam,
# para que saídas locais (CSV, PNG, TXT, MD gerados) dentro dessas pastas nunca virem falso alarme.
SHARED_DIRS = ("src/", "tests/", "configs/", "notebooks/", "tools/")
SHARED_SUFFIXES = {".py", ".pyi", ".ipynb", ".yaml", ".yml", ".toml", ".cfg", ".ini"}
# Pasta do painel: o .gitignore interno dela decide o que é local; aqui só os arquivos de código do painel.
PANEL_DIR = ".srag-status-local/"
PANEL_CODE = {"server.py", "project_status_text.py", "deep_git_project_audit.py", "painel.html", "LEIA-ME.md",
              ".gitignore", "PROJECT_STATUS_TEXT.inicial.md"}
NEVER_SHARED_PARTS = {"__pycache__", ".ipynb_checkpoints", ".pytest_cache"}

# ------------------------------------------------------------------ configuração crítica
CRITICAL_CONFIG_KEYS = {
    "configs/supervised.yaml": ("periodo", "temporal.blocos", "target", "features.final", "features.proibidas",
                                "gates", "selecao_modelos", "calibracao.metodo", "limiar"),
    "configs/decisoes.yaml": ("dev_years", "pandemic_test_years", "experimentos_split.blocos", "status_decisoes"),
    "configs/final_cohort_v1.yaml": ("",),
}

# ------------------------------------------------------------------ critérios
VERBS = {
    "existe": "file", "nao-existe": "file", "nao-vazio": "file",
    "define": "file_name", "nao-define": "file_name",
    "contem": "file_text", "nao-contem": "file_text",
    "yaml": "file_query", "json": "file_query",
    "teste": "test", "notebook-executado": "file", "notebook-saida": "file_text",
    "manual": "none",
}
VERB_ALIASES = {"existir": "existe", "não-existe": "nao-existe", "nao existe": "nao-existe",
                "não-vazio": "nao-vazio", "contém": "contem", "não-contém": "nao-contem", "nao-contém": "nao-contem",
                "não-contem": "nao-contem", "não-define": "nao-define", "teste-passa": "teste",
                "notebook-saída": "notebook-saida"}
QUERY_OPS = ("nao-contem", "nao-existe", "contem", "existe", "!=", "=")
CRITERION_LINE = re.compile(r"^\s*[-*+]\s+(?:\[[ xX✓✗]\]\s*)?([A-Za-zçãõéêíóúÀ-ÿ\- ]{3,24}?)\s*:\s*(.*)$")

PASS, FAIL, LOCAL_MISSING, MANUAL, INVALID, ERROR = (
    "atendido", "nao_atendido", "indisponivel_nesta_maquina", "manual", "criterio_invalido", "erro")
STATUS_TEXT = {
    PASS: "✓ atendido", FAIL: "✗ não atendido", LOCAL_MISSING: "… indisponível nesta máquina",
    MANUAL: "✋ confirmação manual", INVALID: "⚠ critério inválido", ERROR: "⚠ erro ao verificar",
}
# veredito da pendência (ordem = gravidade)
V_INVALID, V_TEST, V_FAIL, V_LOCAL, V_MANUAL, V_PASS, V_NONE = (
    "criterio_invalido", "revisar_por_teste", "nao_atendida", "indisponivel_nesta_maquina",
    "depende_de_confirmacao_manual", "atendida", "sem_criterios")
VERDICT_TEXT = {
    V_INVALID: "Há critério escrito em formato inválido: corrija o texto do card.",
    V_TEST: "Um teste que importa arquivos desta pendência falhou: revisar.",
    V_FAIL: "Pelo menos um critério não está atendido.",
    V_LOCAL: "Critérios de arquivos locais não puderam ser conferidos nesta máquina.",
    V_MANUAL: "Critérios automáticos atendidos; falta a confirmação manual (exige comentário ao concluir).",
    V_PASS: "Todos os critérios estão atendidos.",
    V_NONE: "A pendência não tem critérios de pronto.",
}


# =========================================================================== modelos
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
class Criterion:
    index: int
    raw: str
    verb: str = ""
    path: str = ""
    arg: str = ""
    op: str = ""
    value: str = ""
    description: str = ""
    problem: str = ""


@dataclass
class Commit:
    sha: str
    when: str
    author: str
    subject: str
    body: str
    files: list[str]

    @property
    def message(self) -> str:
        return f"{self.subject}\n{self.body}"


class AuditError(RuntimeError):
    pass


# =========================================================================== utilidades
def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def to_instant(text: str | None) -> dt.datetime | None:
    if not text:
        return None
    try:
        value = dt.datetime.fromisoformat(str(text).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)


def run(args: list[str], cwd: Path, timeout: int = 120, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(args, cwd=cwd, text=True, capture_output=True, encoding="utf-8", errors="replace",
                              timeout=timeout, stdin=subprocess.DEVNULL, env=env)
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(args, 124, str(exc.stdout or ""), f"timeout após {timeout}s")
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(args, 127, "", str(exc))


def git(root: Path, *args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return run(["git", "-c", "core.quotepath=false", *args], root, timeout)


def git_bytes(root: Path, *args: str, timeout: int = 120) -> bytes | None:
    try:
        p = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=root, capture_output=True,
                           timeout=timeout, stdin=subprocess.DEVNULL)
    except Exception:
        return None
    return p.stdout if p.returncode == 0 else None


def repo_root(start: Path | None = None) -> Path:
    p = git(start or Path.cwd(), "rev-parse", "--show-toplevel")
    if p.returncode:
        raise AuditError("Execute dentro do repositório Git do projeto.")
    return Path(p.stdout.strip()).resolve()


def fold(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).strip().lower()


def strip_ticks(text: str) -> str:
    text = text.strip()
    m = re.fullmatch(r"(`+)(.*?)\1", text, re.S)
    return m.group(2) if m else text


def decode(data: bytes | None) -> str | None:
    if data is None:
        return None
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    try:
        return data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError:
        return data.decode("latin-1").replace("\r\n", "\n").replace("\r", "\n")


def norm_path(text: str) -> str:
    """Caminho no formato do Git. Remove só o prefixo "./" (nunca o ponto de nomes como .gitignore)."""
    text = strip_ticks(text).replace("\\", "/").strip()
    while text.startswith("./"):
        text = text[2:]
    text = text.lstrip("/")
    return str(PurePosixPath(text)) if text else ""


def is_shared_path(path: str) -> bool:
    """Caminho que precisa estar no Git: código e configuração (src/, tests/, configs/, notebooks/, tools/,
    raiz) e o código do painel. Diretórios vêm com "/" no final (saída de git ls-files --directory)."""
    clean = path.rstrip("/")
    parts = PurePosixPath(clean).parts
    if not parts or any(p in NEVER_SHARED_PARTS for p in parts):
        return False
    if path.endswith("/"):
        # Só a própria pasta compartilhada (ou a do painel) ignorada inteira é alarme; subpastas (ex.: saídas
        # locais dentro de notebooks/) não.
        return clean + "/" in SHARED_DIRS or clean + "/" == PANEL_DIR
    if clean.startswith(PANEL_DIR):
        rest = clean[len(PANEL_DIR):]
        return "/" not in rest and (rest in PANEL_CODE or rest.endswith(".cmd"))
    if PurePosixPath(clean).suffix.lower() not in SHARED_SUFFIXES:
        return False
    return len(parts) == 1 or any(clean.startswith(s) for s in SHARED_DIRS)


def git_hygiene(root: Path) -> tuple[list[str], list[str]]:
    """(arquivos de código escondidos pelo .gitignore, arquivos de código novos ainda fora do Git)."""
    ignored = git(root, "ls-files", "--others", "--ignored", "--exclude-standard", "--directory", timeout=180)
    untracked = git(root, "ls-files", "--others", "--exclude-standard", timeout=180)
    hidden = sorted(x for x in ignored.stdout.splitlines() if x and is_shared_path(x))
    pending = sorted(x for x in untracked.stdout.splitlines() if x and is_shared_path(x))
    return hidden, pending


def hygiene_report(hidden: list[str], pending: list[str]) -> dict[str, Any]:
    """Resultado da higiene do .gitignore DESTA máquina. Fica fora de "findings" de propósito: o painel copia os
    achados graves para o PROJECT_STATUS.md compartilhado, e arquivos locais diferem de máquina para máquina
    (entrariam e sairiam do estado a cada verificação, gerando commits sem motivo)."""
    return {
        "ignored_code": hidden[:50], "ignored_code_total": len(hidden),
        "not_added": pending[:50], "not_added_total": len(pending),
        "how_to_check": "git check-ignore -v <caminho> mostra o arquivo .gitignore e a linha que ignora o caminho.",
    }


# =========================================================================== leitura do repositório
class RepoView:
    """Leitura de arquivos: rastreados vêm do commit verificado; ignorados vêm da máquina local.

    Arquivos novos não commitados (e não ignorados) NÃO são lidos: não contam como evidência.
    """

    def __init__(self, root: Path, rev: str):
        self.root = root
        self.rev = rev
        self.sha = git(root, "rev-parse", rev).stdout.strip()
        listing = git(root, "ls-tree", "-r", "--name-only", rev, timeout=120)
        if listing.returncode:
            raise AuditError(f"Não foi possível listar o commit {rev}: {listing.stderr.strip()}")
        self.tracked = set(listing.stdout.splitlines())
        self._cache: dict[str, bytes | None] = {}
        self._ignored: dict[str, bool] = {}

    def is_tracked(self, path: str) -> bool:
        return path in self.tracked

    def is_ignored(self, path: str) -> bool:
        if path not in self._ignored:
            p = git(self.root, "check-ignore", "-q", "--no-index", path)
            self._ignored[path] = p.returncode == 0
        return self._ignored[path]

    def source(self, path: str) -> str:
        """'commit' (compartilhado), 'local' (ignorado pelo Git, existe aqui), 'nao_commitado' ou 'ausente'."""
        if self.is_tracked(path):
            return "commit"
        if (self.root / path).exists():
            return "local" if self.is_ignored(path) else "nao_commitado"
        return "ausente"

    def read(self, path: str) -> bytes | None:
        if path not in self._cache:
            if self.is_tracked(path):
                self._cache[path] = git_bytes(self.root, "show", f"{self.rev}:{path}")
            elif (self.root / path).is_file() and self.is_ignored(path):
                try:
                    self._cache[path] = (self.root / path).read_bytes()
                except OSError:
                    self._cache[path] = None
            else:
                self._cache[path] = None
        return self._cache[path]

    def text(self, path: str) -> str | None:
        return decode(self.read(path))

    def dir_has_files(self, path: str) -> bool:
        prefix = path.rstrip("/") + "/"
        if any(t.startswith(prefix) for t in self.tracked):
            return True
        return (self.root / path).is_dir() and self.is_ignored(path)

    def absent_means_unknown(self, path: str) -> bool:
        """Ausente num caminho que o Git ignora (outputs/, data/...): não dá para concluir nada nesta máquina."""
        return not self.is_tracked(path) and self.is_ignored(path)


# =========================================================================== Python e notebooks
def python_without_comments(text: str) -> str:
    """Código Python sem comentários, com espaçamento e quebras de linha originais (strings continuam).

    Cada comentário é trocado por espaços na mesma posição, para que trechos com vários tokens
    (ex.: `early_stopping: bool = True`) continuem encontráveis exatamente como estão no arquivo.
    Em caso de erro de tokenização, devolve o texto.
    """
    lines = text.splitlines(keepends=True)
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                row, start = tok.start
                _, end = tok.end
                line = lines[row - 1]
                lines[row - 1] = line[:start] + " " * (end - start) + line[end:]
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text
    return "".join(lines)


def neutralize_magics(source: str) -> str:
    return "\n".join("# " + l if l.lstrip().startswith(("%", "!", "?")) else l for l in source.splitlines())


def defined_names(tree: ast.AST) -> dict[str, int]:
    """Nome e nome qualificado (Classe.metodo) -> linha. Inclui funções, classes e variáveis atribuídas."""
    found: dict[str, int] = {}

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qual = f"{prefix}{child.name}"
                found.setdefault(qual, child.lineno)
                found.setdefault(child.name, child.lineno)
                visit(child, qual + "." if isinstance(child, ast.ClassDef) else prefix)
            elif isinstance(child, (ast.Assign, ast.AnnAssign)) and not prefix:
                targets = child.targets if isinstance(child, ast.Assign) else [child.target]
                for target in targets:
                    for name in ast.walk(target):
                        if isinstance(name, ast.Name):
                            found.setdefault(name.id, child.lineno)
            elif isinstance(child, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
                visit(child, prefix)

    visit(tree, "")
    return found


def notebook_cells(text: str) -> list[dict[str, Any]] | None:
    try:
        nb = json.loads(text)
    except Exception:
        return None
    cells = []
    for index, cell in enumerate(nb.get("cells", []), 1):
        source = cell.get("source", "")
        source = "".join(source) if isinstance(source, list) else str(source)
        cells.append({"index": index, "type": cell.get("cell_type"), "source": source,
                      "count": cell.get("execution_count"), "outputs": cell.get("outputs", []) or []})
    return cells


def output_text(output: dict[str, Any]) -> str:
    parts: list[str] = []
    if output.get("output_type") == "stream":
        text = output.get("text", "")
        parts.append("".join(text) if isinstance(text, list) else str(text))
    elif output.get("output_type") == "error":
        parts.append(f"{output.get('ename')}: {output.get('evalue')}")
    for mime, value in (output.get("data") or {}).items():
        if mime.startswith("text/") or mime.endswith("json"):
            parts.append("".join(value) if isinstance(value, list) else str(value))
    return "\n".join(parts)


def code_text_of(path: str, text: str) -> str:
    """Texto pesquisável por 'contem': Python sem comentários; notebook = código sem comentários + células Markdown."""
    suffix = PurePosixPath(path).suffix.lower()
    if suffix in CODE_SUFFIXES:
        return python_without_comments(text)
    if suffix == ".ipynb":
        cells = notebook_cells(text) or []
        # Código sem comentários + texto das células Markdown (instruções escritas no notebook também contam).
        return "\n".join(python_without_comments(neutralize_magics(c["source"])) if c["type"] == "code" else c["source"]
                         for c in cells if c["type"] in ("code", "markdown"))
    return text


def names_in(path: str, text: str) -> tuple[dict[str, str], str]:
    """Nome -> onde foi definido. Segundo valor: erro de análise (vazio se ok)."""
    suffix = PurePosixPath(path).suffix.lower()
    if suffix in CODE_SUFFIXES:
        try:
            return {k: f"linha {v}" for k, v in defined_names(ast.parse(text)).items()}, ""
        except SyntaxError as exc:
            return {}, f"erro de sintaxe na linha {exc.lineno}: {exc.msg}"
    if suffix == ".ipynb":
        cells = notebook_cells(text)
        if cells is None:
            return {}, "notebook com JSON inválido"
        out: dict[str, str] = {}
        errors = []
        for c in cells:
            if c["type"] != "code" or not c["source"].strip():
                continue
            try:
                for k, v in defined_names(ast.parse(neutralize_magics(c["source"]))).items():
                    out.setdefault(k, f"célula {c['index']}, linha {v}")
            except SyntaxError:
                errors.append(str(c["index"]))
        return out, (f"células sem análise: {', '.join(errors)}" if errors else "")
    return {}, "verbo 'define' só vale para .py e .ipynb"


# =========================================================================== critérios: leitura
def criteria_section(item: dict[str, Any]) -> tuple[int, str] | None:
    for index, (heading, body) in enumerate(item.get("sections", [])):
        if re.sub(r"^[^a-z]+", "", fold(heading)).startswith("pronto quando"):
            return index, body
    return None


def _split_unquoted(text: str, sep: str) -> tuple[str, str] | None:
    """Divide no primeiro `sep` que não esteja dentro de crases."""
    depth = None
    i = 0
    while i < len(text):
        if text[i] == "`":
            run_len = len(text[i:]) - len(text[i:].lstrip("`"))
            ticks = "`" * run_len
            depth = None if depth == ticks else (ticks if depth is None else depth)
            i += run_len
            continue
        if depth is None and text.startswith(sep, i):
            return text[:i], text[i + len(sep):]
        i += 1
    return None


def parse_criterion(index: int, line: str) -> Criterion | None:
    m = CRITERION_LINE.match(line)
    if not m:
        return None
    verb = VERB_ALIASES.get(fold(m.group(1)), fold(m.group(1)).replace(" ", "-"))
    if verb not in VERBS:
        return None
    c = Criterion(index=index, raw=line.strip(), verb=verb)
    rest = m.group(2).strip()
    if rest.startswith("|"):
        # Critério sem argumentos (ex.: "- manual: | descrição"): tudo depois da barra é a descrição.
        machine, c.description = "", rest[1:].strip()
    else:
        split = _split_unquoted(rest, " | ")
        machine, c.description = (split[0].strip(), split[1].strip()) if split else (rest, "")
    if not c.description:
        c.problem = "falta a descrição depois de ' | ' (cada critério precisa explicar o que está sendo conferido)"
    kind = VERBS[verb]
    if kind == "none":
        if not c.description:
            c.description = strip_ticks(machine)
            c.problem = "" if c.description else c.problem
        return c
    if kind == "test":
        c.path = norm_path(machine)
        if not c.path.startswith("tests/") and "/test" not in c.path:
            c.problem = c.problem or "o argumento de 'teste' deve ser tests/arquivo.py ou tests/arquivo.py::nome_do_teste"
        return c
    if kind == "file":
        c.path = norm_path(machine)
        if not c.path:
            c.problem = "falta o caminho do arquivo"
        return c
    split = _split_unquoted(machine, " :: ")
    if not split:
        c.problem = c.problem or "falta ' :: ' separando o caminho do restante"
        c.path = norm_path(machine)
        return c
    c.path = norm_path(split[0])
    remainder = split[1].strip()
    if kind in ("file_name", "file_text"):
        c.arg = strip_ticks(remainder)
        if not c.arg:
            c.problem = c.problem or "falta o nome ou texto depois de ' :: '"
        return c
    # file_query: chave OP valor
    tokens = re.match(r"^(`[^`]+`|\S+)\s*(.*)$", remainder)
    if not tokens:
        c.problem = c.problem or "falta a chave"
        return c
    c.arg = strip_ticks(tokens.group(1))
    tail = tokens.group(2).strip()
    for op in QUERY_OPS:
        if fold(tail).startswith(op):
            c.op = op
            c.value = strip_ticks(tail[len(op):].strip())
            break
    if not c.op:
        c.problem = c.problem or f"operador ausente ou desconhecido (use um de: {', '.join(QUERY_OPS)})"
    elif c.op not in ("existe", "nao-existe") and c.value == "":
        c.problem = c.problem or "falta o valor depois do operador"
    return c


def parse_criteria(body: str) -> tuple[list[Criterion], list[str]]:
    """Critérios da seção. Linhas de lista que não começam com um verbo conhecido viram aviso."""
    criteria: list[Criterion] = []
    warnings: list[str] = []
    in_fence = False
    for line in body.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            continue
        if in_fence or not re.match(r"^\s*[-*+]\s+", line):
            continue
        c = parse_criterion(len(criteria) + 1, line)
        if c is None:
            warnings.append(f"linha ignorada (não começa com um verbo conhecido): {line.strip()[:120]}")
            continue
        criteria.append(c)
    return criteria, warnings


# =========================================================================== critérios: avaliação
def _query(data: Any, dotted: str) -> tuple[bool, Any]:
    current = data
    for part in [p for p in dotted.split(".") if p != ""]:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, dict) and part.isdigit() and int(part) in current:
            current = current[int(part)]
        elif isinstance(current, list) and part.lstrip("-").isdigit() and -len(current) <= int(part) < len(current):
            current = current[int(part)]
        else:
            return False, None
    return True, current


def _literal(text: str) -> Any:
    if yaml is not None:
        try:
            return yaml.safe_load(text)
        except Exception:
            return text
    try:
        return json.loads(text)
    except Exception:
        return text


def _same(a: Any, b: Any) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        return float(a) == float(b)
    if isinstance(a, str) or isinstance(b, str):
        return str(a).strip() == str(b).strip()
    return a == b


def _short(value: Any, limit: int = 160) -> str:
    text = json.dumps(value, ensure_ascii=False, default=str) if not isinstance(value, str) else value
    return text if len(text) <= limit else text[:limit - 1] + "…"


def evaluate(c: Criterion, repo: RepoView, tests: dict[str, Any] | None) -> dict[str, Any]:
    result: dict[str, Any] = {"index": c.index, "verb": c.verb, "path": c.path, "arg": c.arg, "op": c.op,
                              "value": c.value, "description": c.description, "raw": c.raw}

    def done(status: str, detail: str, source: str = "") -> dict[str, Any]:
        result.update(status=status, status_text=STATUS_TEXT[status], detail=detail,
                      source=source or (repo.source(c.path) if c.path else ""))
        return result

    if c.problem:
        return done(INVALID, c.problem)
    try:
        if c.verb == "manual":
            return done(MANUAL, "Só uma pessoa pode confirmar este critério; ao concluir, o painel exige um comentário.")
        if c.verb == "teste":
            return _evaluate_test(c, tests, done)
        source = repo.source(c.path)
        where = f"commit {repo.sha[:7]}" if source == "commit" else "arquivo local desta máquina"
        data = repo.read(c.path)
        exists = data is not None or (c.verb in ("existe", "nao-existe") and repo.dir_has_files(c.path))
        if c.verb == "nao-existe":
            if exists:
                return done(FAIL, f"O arquivo existe ({where}).", source)
            if repo.absent_means_unknown(c.path):
                return done(PASS, "Não existe nesta máquina (caminho ignorado pelo Git: confira também nas outras máquinas).", "local")
            return done(PASS, f"Não existe no commit {repo.sha[:7]}.", "commit")
        if source == "local" and is_shared_path(c.path):
            # Código/configuração/teste/notebook escondido pelo .gitignore: só existe aqui, não vale para o time.
            return done(FAIL, "O arquivo só existe nesta máquina porque o .gitignore o ignora; ele precisa ir para o "
                              f"Git. Veja a regra com: git check-ignore -v {c.path}", source)
        if not exists:
            if source == "nao_commitado":
                return done(FAIL, f"O arquivo existe na sua máquina, mas não está no commit {repo.sha[:7]}: "
                                  "falta git add/commit/push.", source)
            if repo.absent_means_unknown(c.path):
                return done(LOCAL_MISSING, "O caminho é ignorado pelo Git e o arquivo não existe nesta máquina; "
                                          "quem gerou o arquivo precisa rodar a verificação.", "local")
            return done(FAIL, f"O arquivo não existe no commit {repo.sha[:7]} (nem localmente).", "ausente")
        if c.verb == "existe":
            return done(PASS, f"Existe ({where}).", source)
        text = decode(data) if data is not None else None
        if text is None:
            return done(ERROR, "Não foi possível ler o arquivo como texto.", source)
        if c.verb == "nao-vazio":
            return _evaluate_not_empty(c, text, where, source, done)
        if c.verb in ("define", "nao-define"):
            names, problem = names_in(c.path, text)
            if problem and not names:
                return done(ERROR, problem, source)
            hit = names.get(c.arg)
            if c.verb == "define":
                return done(PASS, f"`{c.arg}` definido em {hit} ({where}).", source) if hit else \
                    done(FAIL, f"`{c.arg}` não está definido ({where}).", source)
            return done(FAIL, f"`{c.arg}` ainda está definido em {hit} ({where}).", source) if hit else \
                done(PASS, f"`{c.arg}` não está definido ({where}).", source)
        if c.verb in ("contem", "nao-contem"):
            haystack = code_text_of(c.path, text)
            found = c.arg in haystack
            scope = " fora de comentários" if PurePosixPath(c.path).suffix.lower() in CODE_SUFFIXES | {".ipynb"} else ""
            if c.verb == "contem":
                return done(PASS if found else FAIL, f"Texto {'encontrado' if found else 'não encontrado'}{scope} ({where}).", source)
            return done(FAIL if found else PASS, f"Texto {'ainda presente' if found else 'ausente'}{scope} ({where}).", source)
        if c.verb in ("yaml", "json"):
            return _evaluate_query(c, text, where, source, done)
        if c.verb == "notebook-executado":
            cells = notebook_cells(text)
            if cells is None:
                return done(ERROR, "Notebook com JSON inválido.", source)
            code = [x for x in cells if x["type"] == "code" and x["source"].strip()]
            missing = [str(x["index"]) for x in code if not isinstance(x["count"], int)]
            errors = [f"célula {x['index']}" for x in code for o in x["outputs"] if o.get("output_type") == "error"]
            if not code:
                return done(FAIL, "O notebook não tem células de código.", source)
            if missing or errors:
                parts = []
                if missing:
                    parts.append(f"{len(missing)} de {len(code)} células sem execução (ex.: {', '.join(missing[:6])})")
                if errors:
                    parts.append(f"saída de erro salva em {', '.join(errors[:6])}")
                return done(FAIL, "; ".join(parts) + f" ({where}).", source)
            return done(PASS, f"{len(code)} de {len(code)} células executadas, sem erro salvo ({where}).", source)
        if c.verb == "notebook-saida":
            cells = notebook_cells(text)
            if cells is None:
                return done(ERROR, "Notebook com JSON inválido.", source)
            for x in cells:
                for o in x["outputs"]:
                    if c.arg in output_text(o):
                        return done(PASS, f"Texto encontrado na saída da célula {x['index']} ({where}).", source)
            return done(FAIL, f"Nenhuma saída salva contém o texto ({where}).", source)
    except Exception as exc:  # o verificador nunca derruba o painel por um critério
        return done(ERROR, f"{type(exc).__name__}: {exc}")
    return done(INVALID, f"verbo sem avaliação: {c.verb}")


def _evaluate_not_empty(c, text, where, source, done):
    if PurePosixPath(c.path).suffix.lower() in CODE_SUFFIXES:
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            return done(FAIL, f"Erro de sintaxe na linha {exc.lineno} ({where}).", source)
        body = [n for n in tree.body if not (isinstance(n, ast.Expr) and isinstance(getattr(n, "value", None), ast.Constant)
                                              and isinstance(n.value.value, str)) and not isinstance(n, ast.Pass)]
        return done(PASS, f"{len(body)} instrução(ões) de nível de módulo ({where}).", source) if body else \
            done(FAIL, f"O arquivo existe mas não tem código (vazio, só docstring ou 'pass') ({where}).", source)
    return done(PASS, f"{len(text.strip())} caracteres ({where}).", source) if text.strip() else \
        done(FAIL, f"O arquivo existe mas está vazio ({where}).", source)


def _evaluate_query(c, text, where, source, done):
    try:
        if c.verb == "yaml":
            if yaml is None:
                return done(ERROR, "pyyaml não está instalado no Python que rodou o verificador.", source)
            data = yaml.safe_load(text)
        else:
            data = json.loads(text)
    except Exception as exc:
        return done(FAIL, f"O arquivo não pôde ser lido como {c.verb.upper()}: {exc} ({where}).", source)
    found, current = _query(data, c.arg)
    if c.op == "existe":
        return done(PASS if found else FAIL, f"Chave `{c.arg}` {'presente' if found else 'ausente'} ({where}).", source)
    if c.op == "nao-existe":
        return done(FAIL if found else PASS, f"Chave `{c.arg}` {'presente' if found else 'ausente'} ({where}).", source)
    if not found:
        return done(FAIL, f"Chave `{c.arg}` ausente ({where}).", source)
    expected = _literal(c.value)
    if c.op == "=":
        ok = _same(current, expected)
    elif c.op == "!=":
        ok = not _same(current, expected)
    else:
        if isinstance(current, (list, tuple, set)):
            inside = any(_same(v, expected) for v in current) if not isinstance(expected, list) else \
                all(any(_same(v, e) for v in current) for e in expected)
        elif isinstance(current, dict):
            inside = str(expected) in current
        else:
            inside = str(expected) in str(current)
        ok = inside if c.op == "contem" else not inside
    return done(PASS if ok else FAIL, f"Valor atual de `{c.arg}`: {_short(current)} ({where}).", source)


def _evaluate_test(c, tests, done):
    if not tests or not tests.get("executed"):
        reason = (tests or {}).get("detail") or "pytest não foi executado nesta verificação"
        return done(LOCAL_MISSING, f"Sem resultado de testes: {reason}.", "pytest")
    cases = tests.get("cases", {})
    wanted = c.path
    if "::" in wanted:
        selected = {k: v for k, v in cases.items() if k == wanted or k.startswith(wanted + "[") or k.startswith(wanted + "::")}
    else:
        selected = {k: v for k, v in cases.items() if k.split("::", 1)[0] == wanted}
    if not selected:
        return done(FAIL, f"Nenhum teste coletado para `{wanted}` (nome errado, arquivo ausente ou teste marcado como slow/net).", "pytest")
    bad = {k: v for k, v in selected.items() if v["outcome"] in ("failed", "error")}
    skipped = [k for k, v in selected.items() if v["outcome"] == "skipped"]
    if bad and all(failure_kind(v["message"]) == "ambiente" for v in bad.values()):
        first = next(iter(bad.items()))
        return done(LOCAL_MISSING, f"{len(bad)} teste(s) não puderam rodar por causa da instalação desta máquina "
                                   f"(ex.: {first[1]['message']}). Rode `pip install -r requirements.txt` e verifique de novo.", "pytest")
    if bad:
        first = next(iter(bad.items()))
        return done(FAIL, f"{len(bad)} de {len(selected)} teste(s) falharam; ex.: {first[0]} — {first[1]['message']}", "pytest")
    if len(skipped) == len(selected):
        return done(FAIL, f"Os {len(selected)} teste(s) foram pulados (skip): não contam como aprovados.", "pytest")
    return done(PASS, f"{len(selected) - len(skipped)} teste(s) passaram" + (f", {len(skipped)} pulado(s)" if skipped else "")
                + f" no {tests.get('where')}.", "pytest")


def verdict_of(results: list[dict[str, Any]], affected: bool) -> str:
    statuses = {r["status"] for r in results}
    if not results:
        return V_TEST if affected else V_NONE
    if INVALID in statuses or ERROR in statuses:
        return V_INVALID
    if affected:
        return V_TEST
    if FAIL in statuses:
        return V_FAIL
    if LOCAL_MISSING in statuses:
        return V_LOCAL
    if MANUAL in statuses:
        return V_MANUAL
    return V_PASS


# =========================================================================== pytest numa cópia limpa
def _nodeid(case: ET.Element, root: Path) -> str:
    file = (case.get("file") or "").replace("\\", "/")
    classname = case.get("classname") or ""
    name = case.get("name") or ""
    if not classname and name and "." in name:  # erro de coleta: o "nome" é o módulo (tests.test_x)
        candidate = name.replace(".", "/") + ".py"
        if candidate == file or (root / candidate).is_file():
            return candidate
    if not file:
        parts = classname.split(".")
        for cut in range(len(parts), 0, -1):
            candidate = "/".join(parts[:cut]) + ".py"
            if (root / candidate).is_file():
                file, classname = candidate, ".".join(parts[cut:])
                break
        else:
            return f"{classname}::{name}"
    module = file[:-3].replace("/", ".") if file.endswith(".py") else file
    rest = classname[len(module):].lstrip(".") if classname.startswith(module) else ""
    return "::".join([file] + ([*rest.split(".")] if rest else []) + [name])


def parse_junit(path: Path, root: Path) -> dict[str, dict[str, str]]:
    cases: dict[str, dict[str, str]] = {}
    tree = ET.parse(path)
    for case in tree.iter("testcase"):
        outcome, message = "passed", ""
        for tag in ("failure", "error", "skipped"):
            node = case.find(tag)
            if node is not None:
                outcome = {"failure": "failed", "error": "error", "skipped": "skipped"}[tag]
                message = (node.get("message") or "").strip()
                e_lines = [l[1:].strip() for l in (node.text or "").splitlines() if l.startswith("E ")]
                if (not message or message in ("collection failure", "failed on setup")) and e_lines:
                    message = e_lines[-1]
                message = (message.splitlines() or [""])[0][:240]
                break
        cases[_nodeid(case, root)] = {"outcome": outcome, "message": message}
    return cases


ENVIRONMENT_FAILURE = re.compile(
    r"ModuleNotFoundError: No module named '(?!src\b|tests\b)|ImportError(?!.*\bsrc\.)|requires NumPy|"
    r"usable engine|necess[áa]rio[^.]{0,30}instalad|DLL load failed|No such file or directory: '.*python",
    re.I)


def failure_kind(message: str) -> str:
    """'ambiente' quando a falha vem da instalação desta máquina (biblioteca ausente ou em versão errada)."""
    return "ambiente" if ENVIRONMENT_FAILURE.search(message or "") else "codigo"


def same_code(root: Path, a: str | None, b: str) -> bool:
    """Dois commits têm o mesmo código? (diferem no máximo nos arquivos do painel de pendências)."""
    if not a:
        return False
    if a == b:
        return True
    p = git(root, "diff", "--name-only", a, b)
    return p.returncode == 0 and set(filter(None, p.stdout.splitlines())) <= {STATUS_NAME, CONTENT_NAME}


def run_pytest(root: Path, rev: str, timeout: int = 600, python: str | None = None) -> dict[str, Any]:
    """Roda o pytest rápido numa cópia limpa do commit `rev` (git worktree).

    Se a cópia não puder ser criada, roda na pasta de trabalho e avisa (pode incluir mudanças locais).
    """
    python = python or sys.executable
    started = dt.datetime.now(dt.timezone.utc)
    temp = Path(tempfile.mkdtemp(prefix="srag_verificador_"))
    worktree = temp / "repo"
    junit = temp / "junit.xml"
    created = git(root, "worktree", "add", "--detach", str(worktree), rev, timeout=300)
    where_dir = worktree if created.returncode == 0 else root
    where = f"commit {rev} (cópia limpa)" if created.returncode == 0 else "pasta de trabalho (cópia limpa falhou)"
    try:
        args = [python, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-m", "not slow and not net",
                "--continue-on-collection-errors",
                "-o", "junit_family=xunit1", f"--junitxml={junit}"]
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(where_dir))
        p = run(args, where_dir, timeout=timeout, env=env)
        tail = (p.stdout + "\n" + p.stderr).strip()[-4000:]
        if not junit.exists():
            return {"executed": False, "where": where, "returncode": p.returncode,
                    "detail": "pytest não produziu resultado (veja a saída)", "output_tail": tail,
                    "cases": {}, "summary": {}}
        cases = parse_junit(junit, where_dir)
        for case in cases.values():  # o caminho da cópia temporária não significa nada para quem lê
            case["message"] = case["message"].replace(str(where_dir) + os.sep, "").replace(str(where_dir), "<repositório>")
        summary = Counter(v["outcome"] for v in cases.values())
        failed = [{"nodeid": k, "outcome": v["outcome"], "message": v["message"], "kind": failure_kind(v["message"])}
                  for k, v in cases.items() if v["outcome"] in ("failed", "error")]
        collect_errors = re.findall(r"^ERROR (\S+)", p.stdout, re.M)
        for path in collect_errors:
            if not any(f["nodeid"].startswith(path) for f in failed):
                failed.append({"nodeid": path, "outcome": "error", "message": "erro ao coletar (import falhou)",
                               "kind": "codigo"})
        return {"executed": True, "where": where, "returncode": p.returncode, "cases": cases,
                "summary": {"passed": summary.get("passed", 0), "failed": summary.get("failed", 0),
                            "errors": sum(1 for f in failed if f["outcome"] == "error"), "skipped": summary.get("skipped", 0)},
                "failed": failed, "output_tail": tail,
                "seconds": round((dt.datetime.now(dt.timezone.utc) - started).total_seconds(), 1)}
    finally:
        if created.returncode == 0:
            git(root, "worktree", "remove", "--force", str(worktree), timeout=120)
            git(root, "worktree", "prune", timeout=60)
        shutil.rmtree(temp, ignore_errors=True)


def project_imports(text: str, tracked: set[str]) -> set[str]:
    """Arquivos do projeto importados por um arquivo Python (imports absolutos)."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            modules.add(node.module)
            modules.update(f"{node.module}.{a.name}" for a in node.names)
    files = set()
    for module in modules:
        base = module.replace(".", "/")
        for candidate in (f"{base}.py", f"{base}/__init__.py"):
            if candidate in tracked:
                files.add(candidate)
    return files


# =========================================================================== commits
def main_ref(root: Path) -> str:
    head = git(root, "symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD").stdout.strip()
    if head and git(root, "rev-parse", "--verify", "-q", head).returncode == 0:
        return head
    for candidate in ("origin/main", "origin/master", "@{upstream}"):
        if git(root, "rev-parse", "--verify", "-q", candidate).returncode == 0:
            return candidate
    return "HEAD"


def read_commits(root: Path, rev: str, limit: int = 500) -> list[Commit]:
    """Uma única chamada: mensagem e arquivos dos últimos `limit` commits do histórico de `rev` (sem --all)."""
    fmt = "%x1e%H%x1f%aI%x1f%an%x1f%s%x1f%b%x1d"
    p = git(root, "log", rev, f"-n{limit}", f"--format={fmt}", "--name-only", "--no-renames", timeout=300)
    commits: list[Commit] = []
    for chunk in p.stdout.split("\x1e"):
        if not chunk.strip():
            continue
        head, _, files = chunk.partition("\x1d")
        parts = head.split("\x1f", 4)
        if len(parts) != 5:
            continue
        commits.append(Commit(sha=parts[0].strip(), when=parts[1], author=parts[2], subject=parts[3].strip(),
                              body=parts[4].strip(), files=[f.strip() for f in files.splitlines() if f.strip()]))
    return commits


def is_panel_commit(commit: Commit) -> bool:
    """Commits publicados pelo painel (só PROJECT_STATUS*.md): não são evidência de trabalho."""
    if commit.subject.startswith(PANEL_COMMIT_PREFIXES):
        return True
    return bool(commit.files) and set(commit.files) <= {STATUS_NAME, CONTENT_NAME, "PENDENCIAS.md"}


def commit_claims(message: str) -> tuple[list[tuple[str, str]], set[str]]:
    """(marcadores explícitos [(ação, id)], ids citados por 'tarefa N' ou '#N')."""
    clean = PULL_REQUEST.sub(" ", message)
    explicit = [(MARKER_ACTION.get(a.lower(), "done"), str(int(i))) for a, i in EXPLICIT_MARKER.findall(clean)]
    mentions = {str(int(i)) for i in TASK_REFERENCE.findall(clean)} | {str(int(i)) for i in HASH_REFERENCE.findall(clean)}
    return explicit, mentions


# =========================================================================== configuração crítica
def flatten(data: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(data, dict):
        out: dict[str, Any] = {}
        for k, v in data.items():
            out.update(flatten(v, f"{prefix}{k}."))
        return out or {prefix.rstrip("."): {}}
    return {prefix.rstrip("."): data}


def config_changes(root: Path, commits: list[Commit], max_per_file: int = 30) -> list[dict[str, Any]]:
    """Mudanças de valor em chaves críticas, commit a commit, com quem mudou e se citou pendência."""
    if yaml is None:
        return []
    changes: list[dict[str, Any]] = []
    for path, prefixes in CRITICAL_CONFIG_KEYS.items():
        touching = [c for c in commits if path in c.files and not is_panel_commit(c)][:max_per_file]
        for commit in touching:
            after = decode(git_bytes(root, "show", f"{commit.sha}:{path}"))
            before = decode(git_bytes(root, "show", f"{commit.sha}^:{path}"))
            if before is None or after is None:
                continue  # criação ou remoção do arquivo: não é mudança de valor
            try:
                a = flatten(yaml.safe_load(after) or {}) if after is not None else {}
                b = flatten(yaml.safe_load(before) or {}) if before is not None else {}
            except Exception:
                continue
            keys = sorted(k for k in set(a) | set(b)
                          if any(p == "" or k == p or k.startswith(p + ".") for p in prefixes) and a.get(k) != b.get(k))
            if not keys:
                continue
            explicit, mentions = commit_claims(commit.message)
            changes.append({
                "file": path, "commit": commit.sha[:12], "when": commit.when, "author": commit.author,
                "subject": commit.subject, "cites_tasks": sorted({i for _, i in explicit} | mentions, key=int),
                "keys": [{"key": k, "before": _short(b.get(k, "(ausente)"), 200), "after": _short(a.get(k, "(ausente)"), 200)}
                         for k in keys[:40]],
                "more_keys": max(0, len(keys) - 40),
            })
    return sorted(changes, key=lambda x: x["when"], reverse=True)


# =========================================================================== varredura estática
def scan_text(path: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    suffix = PurePosixPath(path).suffix.lower()
    if MERGE_CONFLICT.search(text):
        findings.append(Finding("high", "merge-conflict", "Marcadores de conflito do Git encontrados.", paths=[path]))
    if PRIVATE_KEY.search(text):
        findings.append(Finding("critical", "secret", "Possível chave privada no repositório.", paths=[path]))
    for match in SECRET.finditer(text):
        findings.append(Finding("high", "secret", f"Possível segredo atribuído à chave {match.group(1)}.", paths=[path]))
    code = ""
    if suffix in CODE_SUFFIXES:
        try:
            ast.parse(text)
        except SyntaxError as exc:
            findings.append(Finding("high", "python-syntax", f"Erro de sintaxe na linha {exc.lineno}: {exc.msg}", paths=[path]))
        code = python_without_comments(text)
    elif suffix == ".ipynb":
        cells = notebook_cells(text)
        if cells is None:
            return findings + [Finding("high", "notebook-json", "Notebook com JSON inválido.", paths=[path])]
        errors = [f"célula {c['index']}: {o.get('ename')}: {str(o.get('evalue'))[:120]}"
                  for c in cells if c["type"] == "code" for o in c["outputs"] if o.get("output_type") == "error"]
        if errors:
            findings.append(Finding("high", "notebook-saved-error", "Notebook salvo com saída de erro.", evidence=errors[:10], paths=[path]))
        counts = [c["count"] for c in cells if c["type"] == "code" and isinstance(c["count"], int)]
        if any(b < a for a, b in zip(counts, counts[1:])):
            findings.append(Finding("low", "notebook-order", "Células executadas fora de ordem.", paths=[path]))
        code = "\n".join(python_without_comments(neutralize_magics(c["source"])) for c in cells if c["type"] == "code")
    elif suffix == ".json":
        try:
            json.loads(text)
        except Exception as exc:
            findings.append(Finding("high", "json-invalid", f"JSON inválido: {exc}", paths=[path]))
    elif suffix in (".yaml", ".yml") and yaml is not None:
        try:
            yaml.safe_load(text)
        except Exception as exc:
            findings.append(Finding("high", "yaml-invalid", f"YAML inválido: {str(exc)[:200]}", paths=[path]))
    if code:
        for category, pattern, severity, message in PERFORMANCE_RULES:
            hits = len(pattern.findall(code))
            if hits:
                findings.append(Finding(severity, f"performance-{category}", message, evidence=[f"{hits} ocorrência(s)"], paths=[path]))
    return findings


def scan_repository(repo: RepoView) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(repo.tracked):
        parts = PurePosixPath(path).parts
        if path in NEVER_SCAN or any(p in EXCLUDED_PARTS for p in parts) or PurePosixPath(path).suffix.lower() not in SCAN_SUFFIXES:
            continue
        text = repo.text(path)
        if text is not None:
            findings.extend(scan_text(path, text))
    return findings


# =========================================================================== pendências
def load_content(root: Path) -> tuple[dict[str, Any], Any]:
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    import project_status_text as pm  # type: ignore
    path = root / CONTENT_NAME
    if not path.exists():
        raise AuditError(f"{CONTENT_NAME} não encontrado na raiz do repositório.")
    return pm.parse(path.read_text(encoding="utf-8-sig")), pm


def load_status_items(root: Path) -> dict[str, Any]:
    path = root / STATUS_NAME
    if not path.exists():
        return {}
    match = re.search(r"<!--\s*PROJECT_STATUS_DATA\s*\r?\n(.*?)\r?\nPROJECT_STATUS_DATA\s*-->",
                      path.read_text(encoding="utf-8-sig"), re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group(1)).get("items", {})
    except json.JSONDecodeError:
        return {}


EMPTY_PATHS = {"", "—", "-", "nenhum"}


def task_files_of(item: dict[str, Any], criteria: list[Criterion]) -> set[str]:
    files = {norm_path(f) for f in re.split(r"[,;]", item.get("meta", {}).get("arquivos", "") or "") if f.strip()}
    files |= {c.path for c in criteria if c.path and c.verb != "teste"}
    return {f for f in files if f and f not in EMPTY_PATHS}


def suggestion_for(nodeid: str, message: str, files: Iterable[str], when: str) -> str:
    joined = ", ".join(f"`{f}`" for f in sorted(files)[:4])
    return (f"- teste: `{nodeid}` | O teste `{nodeid}` precisa passar no pytest rápido. Ele importa {joined}, que "
            f"pertence(m) a esta pendência, e falhou na verificação de {when[:10]} ({message[:160] or 'sem mensagem'}). "
            f"Acrescentado automaticamente pelo verificador.")


def audit(root: Path, *, ref: str | None = None, only: set[str] | None = None, with_tests: bool = True,
          test_timeout: int = 600, scan: bool = True, commit_limit: int = 500, quick: bool = False,
          previous_tests: dict[str, Any] | None = None, doc: dict[str, Any] | None = None,
          status_items: dict[str, Any] | None = None) -> dict[str, Any]:
    """Verificação completa ou rápida (quick=True: sem pytest, sem varredura, sem histórico da configuração).

    Na rápida, critérios 'teste:' usam o resultado da última verificação completa (previous_tests) se ela foi
    feita sobre o mesmo commit; senão, ficam "indisponível nesta máquina".
    A higiene do .gitignore roda nas duas (é barata).
    """
    root = root.resolve()
    ref = ref or main_ref(root)
    repo = RepoView(root, ref)
    if doc is None:
        doc, _pm = load_content(root)
    if status_items is None:
        status_items = load_status_items(root)
    local_head = git(root, "rev-parse", "HEAD").stdout.strip()
    dirty = [l[3:] for l in git(root, "status", "--porcelain", "--untracked-files=no").stdout.splitlines() if len(l) > 3]
    warnings: list[str] = []
    if local_head and local_head != repo.sha:
        warnings.append(f"Sua pasta local está no commit {local_head[:7]}, mas a verificação usa {ref} ({repo.sha[:7]}). "
                        "Mudanças ainda não publicadas não contam.")
    if yaml is None:
        warnings.append("pyyaml não está instalado no Python que rodou o verificador: critérios 'yaml' dão erro.")
    hidden, pending = git_hygiene(root)
    if hidden:
        warnings.append(f"{len(hidden)} arquivo(s)/pasta(s) de código estão ignorados pelo .gitignore e nunca chegam ao "
                        f"Git (ex.: {', '.join(hidden[:3])}). Veja a regra com git check-ignore -v <caminho>.")
    if pending:
        warnings.append(f"{len(pending)} arquivo(s) de código novos ainda não foram adicionados ao Git "
                        f"(ex.: {', '.join(pending[:3])}).")
    if quick:
        with_tests, scan = False, False
    if quick and previous_tests and previous_tests.get("executed") and same_code(root, previous_tests.get("sha"), repo.sha):
        tests = dict(previous_tests)
    elif with_tests:
        tests = run_pytest(root, repo.sha, timeout=test_timeout)
    else:
        tests = {"executed": False, "detail": "verificação rápida (sem pytest; rode a verificação completa)" if quick
                 else "execução sem testes (--sem-testes)", "cases": {}, "summary": {}}
    tests["sha"] = repo.sha
    failed_tests = tests.get("failed", []) if tests.get("executed") else []
    test_imports: dict[str, set[str]] = {}
    for failure in failed_tests:
        file = failure["nodeid"].split("::", 1)[0]
        if file not in test_imports:
            test_imports[file] = project_imports(repo.text(file) or "", repo.tracked)
    for failure in failed_tests:
        failure["imports"] = sorted(test_imports.get(failure["nodeid"].split("::", 1)[0], set()))
    commits = read_commits(root, repo.sha, commit_limit)

    tasks: dict[str, Any] = {}
    invalid_total = 0
    for iid, item in doc["items"].items():
        if only and iid not in only:
            continue
        if fold(item["meta"].get("removido", "")) not in ("", "—", "-", "nenhum", "nenhuma"):
            continue
        section = criteria_section(item)
        criteria, parse_warnings = parse_criteria(section[1]) if section else ([], [])
        files = task_files_of(item, criteria)
        existing_tests = {c.path for c in criteria if c.verb == "teste"}
        existing_tests |= {p.split("::", 1)[0] for p in existing_tests}
        affected = []
        by_file: dict[str, list[dict[str, Any]]] = {}
        for failure in failed_tests:
            if failure.get("kind") == "ambiente":
                continue
            hit = files & set(failure["imports"])
            if not hit:
                continue
            affected.append({"nodeid": failure["nodeid"], "message": failure["message"], "files": sorted(hit)})
            by_file.setdefault(failure["nodeid"].split("::", 1)[0], []).append({**failure, "hit": hit})
        suggestions = []
        for node_file, group in sorted(by_file.items()):
            if node_file in existing_tests or any(g["nodeid"] in existing_tests for g in group):
                continue
            target = group[0]["nodeid"] if len(group) == 1 else node_file
            hit = set().union(*(g["hit"] for g in group))
            note = group[0]["message"] if len(group) == 1 else f"{len(group)} testes falharam; ex.: {group[0]['message']}"
            suggestions.append(suggestion_for(target, note, hit, utc_now()))
        results = [evaluate(c, repo, tests) for c in criteria]
        invalid_total += sum(r["status"] == INVALID for r in results)
        verdict = verdict_of(results, bool(affected))
        state = status_items.get(iid, {})
        decided = to_instant(state.get("updated_at")) if state.get("origin") == "human" else None
        claims, touching = [], []
        for commit in commits:
            if is_panel_commit(commit):
                continue
            explicit, mentions = commit_claims(commit.message)
            actions = [a for a, i in explicit if i == iid]
            record = {"commit": commit.sha[:12], "when": commit.when, "author": commit.author, "subject": commit.subject[:160]}
            if actions or iid in mentions:
                claims.append({**record, "actions": actions, "kind": "marcador" if actions else "menção"})
                continue
            hits = sorted(files & set(commit.files))
            if hits:
                instant = to_instant(commit.when)
                if decided and instant and instant <= decided:
                    continue
                touching.append({**record, "files": hits[:8]})
        counts = Counter(r["status"] for r in results)
        tasks[iid] = {
            "title": item["title"], "verdict": verdict, "verdict_text": VERDICT_TEXT[verdict],
            "criteria": results, "counts": dict(counts), "warnings": parse_warnings,
            "has_section": bool(section), "files": sorted(files),
            "affected_by_tests": affected, "suggested_criteria": suggestions,
            "claims": claims[:10], "touching_commits": touching[:10],
            "status": state.get("status"),
        }

    findings = scan_repository(repo) if scan else []
    report = {
        "schema_version": SCHEMA_VERSION, "generated_at": utc_now(),
        "machine": os.environ.get("USERNAME") or os.environ.get("USER") or "",
        "ref": ref, "sha": repo.sha, "local_head": local_head, "local_dirty_files": dirty[:50],
        "warnings": warnings, "tests": {k: v for k, v in tests.items() if k != "cases"},
        "test_cases": tests.get("cases", {}) if not quick else {},
        "quick": quick,
        "tasks": tasks, "config_changes": [] if quick else config_changes(root, commits),
        "findings": [asdict(f) for f in findings],
        "git_hygiene": hygiene_report(hidden, pending),
        "summary": {
            "tasks": len(tasks),
            "verdicts": dict(Counter(t["verdict"] for t in tasks.values())),
            "invalid_criteria": invalid_total,
            "without_criteria": sum(1 for t in tasks.values() if not t["criteria"]),
            "affected_by_tests": sorted((i for i, t in tasks.items() if t["affected_by_tests"]), key=int),
            "gitignore_hidden_code": len(hidden),
            "code_not_added": len(pending),
        },
    }
    return report


def apply_suggestions(root: Path, report: dict[str, Any]) -> list[str]:
    """Acrescenta ao PROJECT_STATUS_TEXT.md local os critérios 'teste:' sugeridos. Devolve os itens alterados."""
    doc, pm = load_content(root)
    changed = []
    for iid, task in report["tasks"].items():
        lines = task.get("suggested_criteria") or []
        item = doc["items"].get(iid)
        if not lines or item is None:
            continue
        section = criteria_section(item)
        if section is None:
            item["sections"].append([CRITERIA_HEADING, "\n".join(lines)])
        else:
            index, body = section
            new = [l for l in lines if l.split(" | ", 1)[0] not in body]
            if not new:
                continue
            item["sections"][index][1] = (body.rstrip() + "\n" + "\n".join(new)).strip()
        changed.append(iid)
    if changed:
        path = root / CONTENT_NAME
        text = pm.serialize(doc)
        # Arquivo temporário dentro da pasta do painel (coberta por *.tmp no .gitignore dela), nunca na raiz.
        tmp = Path(__file__).resolve().parent / (CONTENT_NAME + ".tmp")
        tmp.write_text(text, encoding="utf-8", newline="\n")
        os.replace(tmp, path)
    return changed


# =========================================================================== compatibilidade (painel 5.1)
def tracked_text_files(root: Path) -> list[Path]:
    p = git(root, "ls-files")
    return [Path(x) for x in p.stdout.splitlines()
            if x not in NEVER_SCAN and PurePosixPath(x).suffix.lower() in SCAN_SUFFIXES
            and not any(part in EXCLUDED_PARTS for part in PurePosixPath(x).parts) and (root / x).is_file()]


def scan_file(root: Path, relative: Path) -> list[Finding]:
    try:
        text = decode((root / relative).read_bytes()) or ""
    except OSError as exc:
        return [Finding("medium", "encoding", f"Falha ao ler: {exc}", paths=[relative.as_posix()])]
    return scan_text(relative.as_posix(), text)


def scan_config_leakage(root: Path) -> list[Finding]:
    return []


def task_files(definition: dict[str, Any], paths: Iterable[str]) -> list[str]:
    explicit = [norm_path(f).lower() for f in definition.get("files", []) or [] if str(f).strip()]
    return sorted({p for p in paths if any(p.lower() == f or p.lower().startswith(f.rstrip("/") + "/") for f in explicit)})


def relate_findings_to_tasks(findings: list[Finding], definitions: dict[str, dict[str, Any]]) -> None:
    for finding in findings:
        for task_id, definition in definitions.items():
            if task_files(definition, finding.paths):
                finding.task_ids.append(task_id)
        finding.task_ids = sorted(set(finding.task_ids), key=int)


def run_tests(root: Path, timeout: int) -> tuple[Finding | None, dict[str, Any]]:
    result = run_pytest(root, git(root, "rev-parse", "HEAD").stdout.strip() or "HEAD", timeout=timeout)
    record = {k: v for k, v in result.items() if k != "cases"}
    if not result.get("executed"):
        return None, record
    if result.get("failed"):
        names = [f["nodeid"] for f in result["failed"][:10]]
        return Finding("medium", "pytest", f"{len(result['failed'])} teste(s) falharam.", evidence=names), record
    return None, record


# =========================================================================== saída de terminal
def print_report(report: dict[str, Any], verbose: bool = False) -> None:
    print(f"Verificação de {report['ref']} ({report['sha'][:7]}) em {report['generated_at']}")
    for w in report["warnings"]:
        print(f"  ! {w}")
    t = report["tests"]
    if t.get("executed"):
        s = t["summary"]
        print(f"pytest ({t['where']}): {s['passed']} passaram · {s['failed']} falharam · {s['errors']} erro(s) · {s['skipped']} pulados")
        env = [f for f in t.get("failed", []) if f.get("kind") == "ambiente"]
        code = [f for f in t.get("failed", []) if f.get("kind") != "ambiente"]
        for f in code[:20]:
            print(f"  ✗ {f['nodeid']} — {f['message'][:140]}")
        if env:
            print(f"  ! {len(env)} falha(s) por causa da instalação desta máquina (não ligadas a pendências); ex.: {env[0]['message'][:120]}")
    else:
        print(f"pytest: não executado ({t.get('detail')})")
    hyg = report.get("git_hygiene") or {}
    if hyg.get("ignored_code"):
        print(f"  ! Código ignorado pelo .gitignore ({hyg['ignored_code_total']}); confira com git check-ignore -v <caminho>:")
        for path in hyg["ignored_code"][:15]:
            print(f"      {path}")
    if hyg.get("not_added"):
        print(f"  ! Código novo ainda fora do Git ({hyg['not_added_total']}; falta git add/commit/push):")
        for path in hyg["not_added"][:15]:
            print(f"      {path}")
    print("Pendências:", ", ".join(f"{k} {v}" for k, v in sorted(report["summary"]["verdicts"].items())))
    for iid in sorted(report["tasks"], key=int):
        task = report["tasks"][iid]
        if not verbose and task["verdict"] in (V_PASS, V_NONE):
            continue
        print(f"#{iid} [{task['verdict']}] {task['title'][:90]}")
        for r in task["criteria"]:
            if verbose or r["status"] != PASS:
                print(f"    {r['status_text']}: {r['verb']} {r['path']} {r['arg']} {r['op']} {r['value']}".rstrip()
                      + f" — {r['detail']}")
        for s in task["suggested_criteria"]:
            print(f"    + sugestão: {s[:160]}")
    for change in report["config_changes"][:10]:
        cited = ", ".join("#" + i for i in change["cites_tasks"]) or "NENHUMA pendência citada"
        print(f"Configuração crítica: {change['file']} em {change['commit'][:7]} ({change['author']}, {change['when'][:10]}) — {cited}")
        for k in change["keys"][:6]:
            print(f"    {k['key']}: {k['before']} → {k['after']}")


# =========================================================================== self-test
def self_test() -> int:
    checks: list[str] = []

    def check(cond: bool, label: str) -> None:
        if not cond:
            raise AssertionError(label)
        checks.append(label)

    c = parse_criterion(1, "- define: `src/a.py` :: `soma` | A função soma existe.")
    check(c and c.verb == "define" and c.path == "src/a.py" and c.arg == "soma" and not c.problem, "parse define")
    limpo = python_without_comments("def f(\n    x: bool = True,  # comentário\n):\n    return g(saida=\"ordinal\")\n")
    check("x: bool = True," in limpo and "saida=\"ordinal\"" in limpo and "comentário" not in limpo,
          "contem acha trechos com vários tokens e ignora comentários")
    c = parse_criterion(1, "- yaml: configs/s.yaml :: gates.G6.status = aprovado | G6 aprovado.")
    check(c and c.op == "=" and c.value == "aprovado" and c.arg == "gates.G6.status", "parse yaml")
    c = parse_criterion(1, "- contem: `a.md` :: `x | y :: z` | texto com separadores entre crases")
    check(c and c.arg == "x | y :: z" and c.description.startswith("texto"), "separadores entre crases")
    c = parse_criterion(1, "- existe: outputs/final/x.csv")
    check(c and c.problem.startswith("falta a descrição"), "descrição obrigatória")
    c = parse_criterion(1, "- manual: | Relatório revisado por duas pessoas.")
    check(c and c.description == "Relatório revisado por duas pessoas." and not c.problem, "manual sem argumentos")
    check(parse_criterion(1, "- Observação: texto livre") is None, "linha sem verbo é ignorada")
    check(norm_path("`.srag-status-local\\server.py`") == ".srag-status-local/server.py"
          and norm_path(".gitignore") == ".gitignore" and norm_path("./src/a.py") == "src/a.py",
          "norm_path preserva nomes que começam com ponto")
    check(is_shared_path("src/x.py") and is_shared_path(".srag-status-local/") and is_shared_path(".srag-status-local/server.py")
          and is_shared_path(".srag-status-local/ABRIR_PAINEL.cmd")
          and not is_shared_path(".srag-status-local/painel_gerado.html") and not is_shared_path(".srag-status-local/conteudo_remoto.md")
          and not is_shared_path(".srag-status-local/outbox.json") and not is_shared_path(".srag-status-local/logs/painel.log")
          and not is_shared_path("outputs/r.md") and not is_shared_path("notebooks/outputs/") and not is_shared_path("notebooks/x.txt")
          and not is_shared_path("data/") and not is_shared_path("src/__pycache__/"), "o que precisa ir para o Git")
    check(criteria_section({"sections": [["③ O que fazer", "x"], [CRITERIA_HEADING, "- existe: a | b"]]}) == (1, "- existe: a | b"),
          "seção ④ Pronto quando reconhecida")
    check(not MERGE_CONFLICT.search("x\n" + "=" * 58 + "\ny"), "linha decorativa não é conflito")
    check(MERGE_CONFLICT.search("<<<<<<< HEAD\na\n=======\nb\n>>>>>>> x\n") is not None, "conflito real")
    check("criar" not in code_text_of("a.py", "# def criar():\nx = 1\n"), "comentário não conta em 'contem'")
    explicit, mentions = commit_claims("feat: x [done:#10] e tarefa 5; ver #7. Pull request #99")
    check(explicit == [("done", "10")] and mentions == {"5", "7", "10"}, "marcadores e menções")
    check(failure_kind("ImportError: Unable to find a usable engine; tried using: 'pyarrow'") == "ambiente"
          and failure_kind("ModuleNotFoundError: No module named 'src.data.x'") == "codigo"
          and failure_kind("KeyError: 'sem_2020_2021'") == "codigo", "falha de ambiente × de código")

    if shutil.which("git") is None:
        print(f"[verificador] Self-test parcial (git ausente): {len(checks)} verificações.")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for args in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"], ["config", "user.name", "T"]):
            git(root, *args)
        (root / "src").mkdir()
        (root / "tests").mkdir()
        (root / "configs").mkdir()
        (root / "outputs").mkdir()
        (root / ".gitignore").write_text("outputs/*\nsrc/ignorado.py\n", encoding="utf-8")
        (root / "src" / "__init__.py").write_text("", encoding="utf-8")
        (root / "src" / "a.py").write_text('"""Mod."""\n\n# def fantasma(): pass\ndef soma(a, b):\n    return a + b\n', encoding="utf-8")
        (root / "src" / "vazio.py").write_text('"""Só docstring."""\n', encoding="utf-8")
        (root / "src" / "ignorado.py").write_text("x = 1\n", encoding="utf-8")
        (root / "tests" / "test_a.py").write_text(
            "from src.a import soma\n\ndef test_ok():\n    assert soma(1, 2) == 3\n\ndef test_quebra():\n    assert soma(1, 1) == 3\n",
            encoding="utf-8")
        (root / "configs" / "supervised.yaml").write_text("temporal:\n  blocos:\n    train_ref:\n      anos: [2019, 2023]\ngates:\n  G6:\n    status: pendente\n", encoding="utf-8")
        nb = {"cells": [{"cell_type": "code", "execution_count": 1, "metadata": {}, "source": ["print('Tipo: final')"],
                         "outputs": [{"output_type": "stream", "name": "stdout", "text": ["Tipo: final\n"]}]}],
              "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
        (root / "n.ipynb").write_text(json.dumps(nb), encoding="utf-8")
        git(root, "add", "-A")
        git(root, "commit", "-qm", "init")
        (root / "configs" / "supervised.yaml").write_text("temporal:\n  blocos:\n    train_ref:\n      anos: [2023]\ngates:\n  G6:\n    status: pendente\n", encoding="utf-8")
        git(root, "commit", "-qam", "muda anos sem citar")
        (root / "outputs" / "local.csv").write_text("a\n", encoding="utf-8")
        (root / "src" / "nao_commitado.py").write_text("y = 2\n", encoding="utf-8")
        here = Path(__file__).resolve().parent
        shutil.copy(here / "project_status_text.py", root / "project_status_text.py") if (here / "project_status_text.py").exists() else None
        repo = RepoView(root, "HEAD")

        def ev(line: str, tests: dict | None = None) -> str:
            return evaluate(parse_criterion(1, line), repo, tests)["status"]

        check(ev("- define: src/a.py :: soma | x") == PASS, "define encontra função")
        check(ev("- define: src/a.py :: fantasma | x") == FAIL, "define ignora comentário")
        check(ev("- nao-vazio: src/vazio.py | x") == FAIL, "só docstring é vazio")
        check(ev("- nao-vazio: src/a.py | x") == PASS, "arquivo com código não é vazio")
        check(ev("- yaml: configs/supervised.yaml :: temporal.blocos.train_ref.anos = [2023] | x") == PASS, "yaml lista igual")
        check(ev("- yaml: configs/supervised.yaml :: temporal.blocos.train_ref.anos contem 2019 | x") == FAIL, "yaml contem")
        check(ev("- yaml: configs/supervised.yaml :: gates.G6.status = aprovado | x") == FAIL, "yaml valor diferente")
        check(ev("- existe: outputs/final/x.csv | x") == LOCAL_MISSING, "ausente em pasta ignorada não reprova")
        check(ev("- existe: outputs/local.csv | x") == PASS, "arquivo local existente")
        check(ev("- existe: src/b.py | x") == FAIL, "rastreável ausente reprova")
        check(ev("- existe: .gitignore | x") == PASS, "caminho que começa com ponto")
        check(ev("- existe: src/nao_commitado.py | x") == FAIL, "arquivo novo não commitado não conta")
        check(ev("- existe: src/ignorado.py | x") == FAIL, "código escondido pelo .gitignore não conta")
        check(ev("- notebook-executado: n.ipynb | x") == PASS, "notebook executado")
        check(ev("- notebook-saida: n.ipynb :: Tipo: final | x") == PASS, "saída de notebook")
        check(ev("- manual: | Relatório revisado por duas pessoas.") == MANUAL, "critério manual")
        hidden, pending = git_hygiene(root)
        check(hidden == ["src/ignorado.py"] and "src/nao_commitado.py" in pending, "higiene do .gitignore")
        changes = config_changes(root, read_commits(root, "HEAD"))
        check(len(changes) == 1 and changes[0]["keys"][0]["key"] == "temporal.blocos.train_ref.anos" and not changes[0]["cites_tasks"],
              "mudança de configuração crítica sem pendência citada")
        try:
            import pytest  # noqa: F401
            has_pytest = True
        except Exception:
            has_pytest = False
        if has_pytest:
            tests = run_pytest(root, repo.sha, timeout=180)
            check(tests["executed"] and tests["summary"]["failed"] == 1, "pytest numa cópia limpa")
            check(ev("- teste: tests/test_a.py::test_ok | x", tests) == PASS, "teste que passa")
            check(ev("- teste: tests/test_a.py | x", tests) == FAIL, "arquivo de teste com falha")
            failed = tests["failed"][0]
            check(project_imports((root / "tests" / "test_a.py").read_text(), repo.tracked) == {"src/a.py"},
                  "imports do teste ligados aos arquivos")
            check(failed["nodeid"] == "tests/test_a.py::test_quebra", "nodeid do teste que falhou")
            check(git(root, "worktree", "list").stdout.count("\n") == 1, "cópia limpa removida")
    print(f"[verificador] Self-test passed: {len(checks)} checks.")
    return 0


# =========================================================================== CLI
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Verificador do 'Pronto quando' e auditoria do repositório (SRAG).")
    p.add_argument("--ref", help="Commit ou branch a verificar (padrão: origin/<branch principal>).")
    p.add_argument("--item", action="append", default=[], help="Verifica só esta pendência (repita para várias).")
    p.add_argument("--sem-testes", action="store_true", help="Não roda o pytest.")
    p.add_argument("--sem-varredura", action="store_true", help="Não faz a varredura estática.")
    p.add_argument("--timeout-testes", type=int, default=600)
    p.add_argument("--json", help="Grava o relatório também neste caminho.")
    p.add_argument("--aplicar-sugestoes", action="store_true",
                   help="Acrescenta ao PROJECT_STATUS_TEXT.md local os critérios 'teste:' sugeridos.")
    p.add_argument("--detalhado", action="store_true", help="Mostra também os critérios atendidos.")
    p.add_argument("--self-test", action="store_true")
    for legacy in ("--write", "--dry-run", "--no-tests", "--since-commit", "--fail-on-high", "--test-timeout"):
        p.add_argument(legacy, nargs="?", const=True, help=argparse.SUPPRESS)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    args = parse_args(argv)
    if args.self_test:
        return self_test()
    if args.write:
        print("O modo --write foi removido: o verificador nunca grava o PROJECT_STATUS.md (o painel publica).")
        return 1
    try:
        root = repo_root(Path(__file__).resolve().parent)
        report = audit(root, ref=args.ref, only=set(args.item) or None,
                       with_tests=not (args.sem_testes or args.no_tests), test_timeout=args.timeout_testes,
                       scan=not args.sem_varredura)
    except AuditError as exc:
        print(f"[verificador] {exc}")
        return 1
    local = Path(__file__).resolve().parent / REPORT_NAME
    text = json.dumps(report, ensure_ascii=False, indent=1, default=str)
    local.write_text(text, encoding="utf-8")
    if args.json:
        Path(args.json).write_text(text, encoding="utf-8")
    print_report(report, verbose=args.detalhado)
    if args.aplicar_sugestoes:
        changed = apply_suggestions(root, report)
        print("Critérios de teste acrescentados em: " + (", ".join("#" + i for i in changed) or "nenhuma pendência"))
    print(f"Relatório: {local}")
    return 2 if report["summary"]["invalid_criteria"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
