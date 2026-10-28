#!/usr/bin/env python3
"""PROJECT_STATUS_TEXT.md: fonte única do conteúdo textual do Painel de Pendências SRAG.

Fluxo:  PROJECT_STATUS_TEXT.md (Git, editável no VS Code e pelo painel)
          -> parse()  -> modelo (dicionários simples, serializáveis em JSON)
          -> build_view() -> dados do painel (HTML de cada seção já renderizado)
          -> update_html() -> região delimitada dentro do painel.html (só reescreve se o hash mudou)

O modelo também volta para texto com serialize(); o painel edita o arquivo campo a campo
(título, metadados, seções), por isso duas pessoas editando campos diferentes nunca conflitam.

Formato (resumo; a gramática completa está no topo do próprio PROJECT_STATUS_TEXT.md):
    ## Painel · textos gerais          -> textos globais (### Título, ### Cronograma, ### Ajuda · ...)
    ## #120 · Título da pendência        -> um item
    - prioridade: P1                     -> metadados (uma linha cada)
    ### ① Para entender                  -> seções (Markdown simples; HTML também é aceito)
"""
from __future__ import annotations

import copy
import hashlib
import html as _html
import json
import os
import re
import tempfile
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

FORMAT_VERSION = 1
CONTENT_FILE = "PROJECT_STATUS_TEXT.md"
LEGACY_CONTENT_FILES = ("PENDENCIAS.md",)
MARK_BEGIN = "/*@@CONTEUDO_PENDENCIAS:INICIO@@*/"
MARK_END = "/*@@CONTEUDO_PENDENCIAS:FIM@@*/"

# --------------------------------------------------------------------------- vocabulário
PRIORITIES = ("P1", "P2", "P3", "P4")
EDITORIAL = ("aberta", "parcial", "resolvida")
STRATEGIES = ("desenvolver", "explorar", "documentar", "despriorizar", "resolvida")
MILESTONE_ORDER = ["M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "Contínuo", "Plano B", "Pós-entrega", "—"]

# (chave canônica escrita no arquivo, chave no painel, tipo)
META = [
    ("prioridade", "p", "enum"),
    ("situação", "st", "enum"),
    ("estratégia", "est", "enum"),
    ("marco", "m", "text"),
    ("data ideal", "due", "text"),
    ("responsável", "own", "text"),
    ("pessoas", "ow", "list"),
    ("fonte", "src", "text"),
    ("depende de", "dep", "ids"),
    ("tags", "tags", "list"),
    ("pilar", "pillar", "text"),
    ("carga", "load", "int"),
    ("novo", "new", "bool"),
    ("professores", "prof", "bool"),
    ("arquivos", "files", "list"),
    ("removido", "rm", "text"),
]
META_KEYS = [m[0] for m in META]
OPTIONAL_META = {"arquivos", "removido"}  # só aparecem no arquivo quando preenchidos
SECTIONS = [("u", "① Para entender"), ("pb", "② Problema"), ("fz", "③ O que fazer"), ("pq", "④ Pronto quando")]
SECTION_DEFAULT = dict(SECTIONS)
BOX_NAMES = {"dec": "decisão", "at": "atenção", "ex": "exemplo", "go": "ok", "pil": "pilar"}
BOX_ALIASES = {
    "decisao": "dec", "dec": "dec", "important": "dec", "importante": "dec",
    "atencao": "at", "at": "at", "warning": "at", "caution": "at", "cuidado": "at",
    "exemplo": "ex", "ex": "ex", "note": "ex", "nota": "ex", "info": "ex",
    "ok": "go", "go": "go", "tip": "go", "dica": "go", "situacao": "go",
    "pilar": "pil", "pil": "pil",
}
EMPTY = ("", "—", "-", "–", "nenhum", "nenhuma")


def fold(text: str) -> str:
    """minúsculas, sem acentos, sem símbolos de numeração (①②③), espaços simples."""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[\u2460-\u24ff\u2776-\u2793]", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


META_ALIASES = {fold(k): k for k in META_KEYS}
META_ALIASES.update({
    "prioridade": "prioridade", "p": "prioridade", "situacao editorial": "situação", "status editorial": "situação",
    "estrategia": "estratégia", "categoria": "estratégia", "marco logico": "marco", "data": "data ideal",
    "prazo": "data ideal", "dono": "responsável", "responsaveis": "responsável", "pessoa": "pessoas",
    "fontes": "fonte", "depende": "depende de", "dependencias": "depende de", "dependências": "depende de",
    "tag": "tags", "pilares": "pilar", "peso": "carga", "item novo": "novo", "para professores": "professores",
    "arquivo": "arquivos", "files": "arquivos", "removida": "removido",
})


def section_code(heading: str) -> str:
    f = fold(heading)
    f = re.sub(r"^[\d\.\)\s]+", "", f)
    if f.startswith("para entender") or f == "entender":
        return "u"
    if f.startswith("problema"):
        return "pb"
    if f.startswith("o que fazer") or f.startswith("que fazer") or f.startswith("acoes"):
        return "fz"
    if f.startswith("pronto quando"):
        return "pq"
    return ""


# --------------------------------------------------------------------------- utilidades
def sha(text: str, n: int = 16) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:n]


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    os.replace(tmp, path)


def split_list(value: str, sep: str = ",") -> list[str]:
    if fold(value) in EMPTY:
        return []
    return [x.strip() for x in re.split(r"\s*[,;]\s*" if sep == "," else r"\s*;\s*", value) if x.strip() and fold(x) not in EMPTY]


def parse_ids(value: str) -> list[str]:
    return [str(int(x)) for x in re.findall(r"#?\s*(\d{1,5})", value or "")]


def parse_bool(value: str) -> bool:
    return fold(value) in ("sim", "s", "yes", "y", "true", "1", "x", "verdadeiro")


# =========================================================================== PARSE / SERIALIZE
H2 = re.compile(r"^##(?!#) (.*?)\s*$")
H3 = re.compile(r"^###(?!#) (.*?)\s*$")
ITEM_HEAD = re.compile(r"^#\s*(\d{1,5})\s*(?:[·\-–—:|]\s*)?(.*)$")
META_LINE = re.compile(r"^\s*[-*+]\s+([^:\n]{1,40}?)\s*:\s?(.*)$")
FENCE = re.compile(r"^\s*(```|~~~)")


def _blocks(lines: list[str], head: re.Pattern) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """Divide em blocos pelos cabeçalhos `head`, ignorando o que está dentro de blocos de código."""
    pre: list[str] = []
    out: list[tuple[str, list[str]]] = []
    fence = None
    for line in lines:
        m = FENCE.match(line)
        if m:
            fence = None if fence == m.group(1) else (fence or m.group(1))
        hm = head.match(line) if fence is None and not m else None
        if hm:
            out.append((hm.group(1), []))
        elif out:
            out[-1][1].append(line)
        else:
            pre.append(line)
    return pre, out


def _trim(lines: list[str]) -> str:
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return "\n".join(l.rstrip() for l in lines)


def parse(text: str) -> dict[str, Any]:
    """Texto -> modelo. Nunca levanta exceção por conteúdo: problemas viram `issues`."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    pre, blocks = _blocks(text.split("\n"), H2)
    doc: dict[str, Any] = {"preamble": _trim(pre), "panel": None, "items": {}, "layout": [], "issues": []}
    for heading, body in blocks:
        m = ITEM_HEAD.match(heading)
        raw = ("## " + heading + "\n" + "\n".join(body)).rstrip("\n") + "\n"
        if m:
            iid = str(int(m.group(1)))
            item = _parse_item(iid, m.group(2).strip(), body, doc["issues"])
            item["_raw"], item["_sig"] = raw, signature(item)
            if iid in doc["items"]:
                doc["issues"].append({"level": "erro", "item": iid, "msg": f"Número #{iid} repetido; a segunda ocorrência foi ignorada."})
                continue
            doc["items"][iid] = item
            doc["layout"].append(["item", iid])
        elif fold(heading).startswith("painel") and doc["panel"] is None:
            ipre, secs = _blocks(body, H3)
            doc["panel"] = {"heading": heading, "intro": _trim(ipre), "sections": [[h, _trim(b)] for h, b in secs]}
            doc["panel"]["_raw"], doc["panel"]["_sig"] = raw, signature(doc["panel"])
            doc["layout"].append(["panel", ""])
        else:
            doc["layout"].append(["raw", "## " + heading + "\n" + "\n".join(body).rstrip()])
    _validate(doc)
    return doc


def _parse_item(iid: str, title: str, body: list[str], issues: list[dict[str, Any]]) -> dict[str, Any]:
    head, secs = _blocks(body, H3)
    meta: dict[str, str] = {}
    extra: list[list[str]] = []
    intro: list[str] = []
    for line in head:
        m = META_LINE.match(line)
        if m and not intro:
            key = META_ALIASES.get(fold(m.group(1)))
            if key:
                if key in meta:
                    issues.append({"level": "aviso", "item": iid, "msg": f"Campo '{key}' repetido no #{iid}; vale o último."})
                meta[key] = m.group(2).strip()
            else:
                extra.append([m.group(1).strip(), m.group(2).strip()])
        elif line.strip() or intro:
            intro.append(line)
    sections = [[h, _trim(b)] for h, b in secs]
    if not title:
        issues.append({"level": "aviso", "item": iid, "msg": f"#{iid} sem título."})
    return {"id": iid, "title": title, "meta": meta, "extra_meta": extra, "intro": _trim(intro), "sections": sections}


def _validate(doc: dict[str, Any]) -> None:
    issues = doc["issues"]
    items = doc["items"]
    for iid, it in items.items():
        m = it["meta"]
        if m.get("prioridade") and m["prioridade"].upper() not in PRIORITIES:
            issues.append({"level": "aviso", "item": iid, "msg": f"#{iid}: prioridade '{m['prioridade']}' desconhecida (use P1–P4)."})
        if m.get("situação") and fold(m["situação"]) not in EDITORIAL:
            issues.append({"level": "aviso", "item": iid, "msg": f"#{iid}: situação '{m['situação']}' desconhecida (aberta, parcial, resolvida)."})
        if m.get("estratégia") and fold(m["estratégia"]) not in STRATEGIES:
            issues.append({"level": "aviso", "item": iid, "msg": f"#{iid}: estratégia '{m['estratégia']}' desconhecida."})
        for dep in parse_ids(m.get("depende de", "")):
            if dep not in items:
                issues.append({"level": "aviso", "item": iid, "msg": f"#{iid} depende de #{dep}, que não existe."})
            elif dep == iid:
                issues.append({"level": "aviso", "item": iid, "msg": f"#{iid} depende de si mesmo."})
        due = m.get("data ideal", "")
        if due and not re.match(r"^\d{2}/\d{2}$", due) and fold(due) not in ("concluido", "apos 03/11") and fold(due) not in EMPTY \
                and not fold(due).startswith(("apos", "concl", "continuo")):
            issues.append({"level": "info", "item": iid, "msg": f"#{iid}: data ideal '{due}' fora do formato DD/MM (aceita, mas não entra nos filtros de vencimento)."})
    # ciclo de dependências (simples, DFS)
    graph = {i: [d for d in parse_ids(it["meta"].get("depende de", "")) if d in items] for i, it in items.items()}
    state: dict[str, int] = {}

    def dfs(n: str, path: list[str]) -> None:
        state[n] = 1
        for d in graph.get(n, []):
            if state.get(d) == 1:
                cyc = path[path.index(d):] + [d] if d in path else [n, d]
                issues.append({"level": "aviso", "item": n, "msg": "Ciclo de dependências: " + " → ".join("#" + x for x in cyc)})
            elif not state.get(d):
                dfs(d, path + [d])
        state[n] = 2

    for n in graph:
        if not state.get(n):
            dfs(n, [n])


def signature(obj: dict[str, Any]) -> str:
    """Assinatura do conteúdo (sem campos internos): se não mudou, o serializador reaproveita o texto original."""
    return sha(json.dumps({k: v for k, v in obj.items() if not k.startswith("_")}, ensure_ascii=False, sort_keys=True), 20)


def _escape_heading_lines(body: str) -> str:
    """Linhas de conteúdo que começam com '## ' ou '### ' quebrariam a estrutura: viram texto literal."""
    out, fence = [], None
    for line in body.split("\n"):
        m = FENCE.match(line)
        if m:
            fence = None if fence == m.group(1) else (fence or m.group(1))
        if fence is None and not m and re.match(r"^#{2,3} ", line):
            line = "\\" + line
        out.append(line)
    return "\n".join(out)


def one_line(value: Any) -> str:
    return re.sub(r"\s*\n\s*", " ", str(value if value is not None else "")).strip()


def serialize_item(item: dict[str, Any]) -> str:
    if item.get("_raw") and item.get("_sig") == signature(item):
        return item["_raw"]
    lines = [f"## #{item['id']} · {one_line(item.get('title', ''))}", ""]
    meta = item.get("meta", {})
    for key in META_KEYS:
        if key in meta and (key not in OPTIONAL_META or fold(meta[key]) not in EMPTY):
            lines.append(f"- {key}: {one_line(meta[key])}")
    for k, v in item.get("extra_meta", []):
        lines.append(f"- {one_line(k)}: {one_line(v)}")
    lines.append("")
    if item.get("intro"):
        lines += [_escape_heading_lines(item["intro"]), ""]
    for heading, body in item.get("sections", []):
        lines += [f"### {one_line(heading)}", ""]
        if body.strip():
            lines += [_escape_heading_lines(body.strip("\n")), ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def serialize(doc: dict[str, Any]) -> str:
    parts = []
    if doc.get("preamble"):
        parts.append(doc["preamble"].rstrip("\n") + "\n")
    layout = doc.get("layout") or ([["panel", ""]] if doc.get("panel") else []) + [["item", i] for i in doc["items"]]
    seen = set()
    for kind, ref in layout:
        if kind == "panel" and doc.get("panel"):
            p = doc["panel"]
            if p.get("_raw") and p.get("_sig") == signature(p):
                parts.append(p["_raw"])
                continue
            chunk = [f"## {p.get('heading') or 'Painel · textos gerais'}", ""]
            if p.get("intro"):
                chunk += [p["intro"], ""]
            for h, b in p.get("sections", []):
                chunk += [f"### {one_line(h)}", ""]
                if b.strip():
                    chunk += [_escape_heading_lines(b), ""]
            parts.append("\n".join(chunk).rstrip("\n") + "\n")
        elif kind == "item" and ref in doc["items"] and ref not in seen:
            seen.add(ref)
            parts.append(serialize_item(doc["items"][ref]))
        elif kind == "raw":
            parts.append(ref.rstrip("\n") + "\n")
    for iid, item in doc["items"].items():  # itens novos ainda fora do layout
        if iid not in seen:
            parts.append(serialize_item(item))
    return "\n".join(parts).rstrip("\n") + "\n"


# =========================================================================== EDIÇÃO CAMPO A CAMPO
def field_names(item: dict[str, Any]) -> list[str]:
    names = ["title", "intro"] + [f"meta:{k}" for k in META_KEYS]
    names += [f"meta+:{k}" for k, _ in item.get("extra_meta", [])]
    for h, _ in item.get("sections", []):
        code = section_code(h)
        names.append(f"sec:{code}" if code else f"sec+:{h}")
    return names


def get_field(item: dict[str, Any], field: str) -> str | None:
    if field == "title":
        return item.get("title", "")
    if field == "intro":
        return item.get("intro", "")
    kind, _, name = field.partition(":")
    if kind == "meta":
        return item.get("meta", {}).get(name)
    if kind == "meta+":
        return next((v for k, v in item.get("extra_meta", []) if k == name), None)
    if kind == "sec":
        return next((b for h, b in item.get("sections", []) if section_code(h) == name), None)
    if kind == "sec+":
        return next((b for h, b in item.get("sections", []) if h == name and not section_code(h)), None)
    raise KeyError(field)


def set_field(item: dict[str, Any], field: str, value: str | None) -> None:
    if field == "title":
        item["title"] = one_line(value or "")
        return
    if field == "intro":
        item["intro"] = (value or "").strip("\n")
        return
    kind, _, name = field.partition(":")
    if kind == "meta":
        if name not in META_KEYS:
            raise KeyError(field)
        if value is None:
            item.setdefault("meta", {}).pop(name, None)
        else:
            item.setdefault("meta", {})[name] = one_line(value)
        # mantém a ordem canônica
        item["meta"] = {k: item["meta"][k] for k in META_KEYS if k in item["meta"]}
        return
    if kind == "meta+":
        rows = [r for r in item.get("extra_meta", []) if r[0] != name]
        if value is not None:
            rows.append([name, one_line(value)])
        item["extra_meta"] = rows
        return
    if kind in ("sec", "sec+"):
        secs = item.setdefault("sections", [])
        idx = next((i for i, (h, _) in enumerate(secs) if (section_code(h) == name if kind == "sec" else (h == name and not section_code(h)))), None)
        if value is None:
            if idx is not None:
                secs.pop(idx)
            return
        body = value.replace("\r\n", "\n").strip("\n")
        if idx is not None:
            secs[idx][1] = body
            return
        heading = SECTION_DEFAULT.get(name, name) if kind == "sec" else name
        if kind == "sec":  # u, pb, fz entram na ordem canônica
            order = [c for c, _ in SECTIONS]
            pos = len([1 for h, _ in secs if section_code(h) in order[:order.index(name)]])
            secs.insert(pos, [heading, body])
        else:
            secs.append([heading, body])
        return
    raise KeyError(field)


def diff_items(old: dict[str, Any] | None, new: dict[str, Any]) -> dict[str, tuple[str | None, str | None]]:
    """{campo: (antes, depois)} para os campos que mudaram."""
    out = {}
    names = list(dict.fromkeys(field_names(new) + (field_names(old) if old else [])))
    for f in names:
        a = get_field(old, f) if old else None
        b = get_field(new, f)
        if (a or None) != (b or None) and not (a in (None, "") and b in (None, "")):
            out[f] = (a, b)
    return out


def diff_docs(base: dict[str, Any] | None, new: dict[str, Any]) -> dict[str, Any]:
    """Diferenças de `new` em relação a `base`: itens novos, campos alterados e textos do painel."""
    base_items = (base or {}).get("items", {})
    res: dict[str, Any] = {"created": {}, "fields": {}, "panel": {}}
    for iid, item in new["items"].items():
        if iid not in base_items:
            res["created"][iid] = item
        else:
            d = diff_items(base_items[iid], item)
            if d:
                res["fields"][iid] = d
    bp = {h: b for h, b in ((base or {}).get("panel") or {}).get("sections", [])}
    for h, b in (new.get("panel") or {}).get("sections", []):
        if bp.get(h) != b:
            res["panel"][h] = (bp.get(h), b)
    return res


def set_panel_section(doc: dict[str, Any], heading: str, body: str | None) -> None:
    p = doc.setdefault("panel", None) or {"heading": "Painel · textos gerais", "intro": "", "sections": []}
    doc["panel"] = p
    if not any(k == "panel" for k, _ in doc.get("layout", [])):
        doc.setdefault("layout", []).insert(0, ["panel", ""])
    secs = p["sections"]
    idx = next((i for i, (h, _) in enumerate(secs) if h == heading), None)
    if body is None:
        if idx is not None:
            secs.pop(idx)
    elif idx is None:
        secs.append([heading, body.strip("\n")])
    else:
        secs[idx][1] = body.strip("\n")


def panel_section(doc: dict[str, Any], heading: str) -> str | None:
    return next((b for h, b in (doc.get("panel") or {}).get("sections", []) if h == heading), None)


def next_id(doc: dict[str, Any]) -> str:
    nums = [int(i) for i in doc["items"] if str(i).isdigit()]
    return str(max(nums + [0]) + 1)


def new_item(iid: str, title: str) -> dict[str, Any]:
    return {"id": iid, "title": one_line(title), "intro": "", "extra_meta": [],
            "meta": {"prioridade": "P3", "situação": "aberta", "estratégia": "desenvolver", "marco": "—", "data ideal": "—",
                     "responsável": "—", "pessoas": "—", "fonte": "—", "depende de": "—", "tags": "—", "pilar": "—",
                     "carga": "—", "novo": "sim", "professores": "não"},
            "sections": [[SECTION_DEFAULT["u"], ""], [SECTION_DEFAULT["pb"], ""], [SECTION_DEFAULT["fz"], ""],
                         [SECTION_DEFAULT["pq"], ""]]}


def definitions(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Formato usado pelo serviço e pela auditoria (title, owner, priority, due, source, files)."""
    out = {}
    for iid, it in doc["items"].items():
        m = it["meta"]
        if fold(m.get("removido", "")) not in EMPTY:
            continue
        out[iid] = {"title": it["title"], "owner": m.get("responsável", "—"), "priority": (m.get("prioridade") or "P3").upper(),
                    "due": m.get("data ideal", "—"), "source": m.get("fonte", ""), "files": split_list(m.get("arquivos", ""))}
    return out


# =========================================================================== MARKDOWN -> HTML
_PH = "\x00{}\x00"
CODE_SPAN = re.compile(r"(`+)(.+?)(?<!`)\1(?!`)", re.S)
ESCAPE = re.compile(r"\\([\\`*_\[\]{}()#+\-.!|<>~])")
RAW_TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*)?/?>|<!--.*?-->", re.S)
BOLD = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", re.S)
ITAL = re.compile(r"(?<![\*\w\\])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![\*\w])", re.S)
LINK = re.compile(r"\[([^\[\]]+)\]\(([^()\s]+)\)")


def inline(md: str) -> str:
    """Markdown inline -> HTML. Texto e tags HTML passam sem alteração; código é escapado."""
    store: list[str] = []

    def keep(s: str) -> str:
        store.append(s)
        return _PH.format(len(store) - 1)

    s = CODE_SPAN.sub(lambda m: keep("<code>" + _html.escape(m.group(2).strip(" ") if m.group(2).strip(" ") else m.group(2), quote=False) + "</code>"), md)
    s = ESCAPE.sub(lambda m: keep(_html.escape(m.group(1), quote=False)), s)
    s = RAW_TAG.sub(lambda m: keep(m.group(0)), s)
    s = LINK.sub(lambda m: keep(f'<a href="{_html.escape(m.group(2))}" target="_blank" rel="noopener">') + m.group(1) + keep("</a>"), s)
    for _ in range(3):
        s2 = BOLD.sub(lambda m: "<b>" + m.group(1) + "</b>", s)
        s2 = ITAL.sub(lambda m: "<i>" + m.group(1) + "</i>", s2)
        if s2 == s:
            break
        s = s2
    for _ in range(4):
        if "\x00" not in s:
            break
        s = re.sub(r"\x00(\d+)\x00", lambda m: store[int(m.group(1))], s)
    return s


LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d{1,3}[.)])\s+(.*)$")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
HR = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")


def _starts_block(line: str) -> bool:
    s = line.lstrip()
    return bool(FENCE.match(line) or s.startswith(("<", ">", "|")) or LIST_ITEM.match(line) or HEADING.match(line) or HR.match(line))


def _cells(row: str) -> list[str]:
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", row)]


def _render_list(lines: list[str]) -> str:
    base = len(LIST_ITEM.match(lines[0]).group(1))
    ordered = LIST_ITEM.match(lines[0]).group(2)[0].isdigit()
    items: list[list[str]] = []
    for line in lines:
        m = LIST_ITEM.match(line)
        if m and len(m.group(1)) <= base + 1:
            items.append([m.group(3)])
        elif items:
            items[-1].append(line)
    out = []
    for it in items:
        text, sub = [it[0]], []
        for l in it[1:]:
            if sub or (LIST_ITEM.match(l) and len(LIST_ITEM.match(l).group(1)) > base + 1):
                sub.append(l)
            else:
                text.append(l.strip())
        body = inline("\n".join(text))
        if sub:
            body += _render_list(sub)
        out.append(f"<li>{body}</li>")
    start = ""
    if ordered:
        n = int(re.match(r"\d+", LIST_ITEM.match(lines[0]).group(2)).group(0))
        start = f' start="{n}"' if n != 1 else ""
    tag = "ol" if ordered else "ul"
    return f"<{tag}{start}>" + "".join(out) + f"</{tag}>"


def render(md: str) -> str:
    """Markdown do painel -> HTML (subconjunto previsível; HTML cru é preservado)."""
    lines = (md or "").replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        fm = FENCE.match(line)
        if fm:
            j = i + 1
            while j < n and not lines[j].lstrip().startswith(fm.group(1)):
                j += 1
            out.append("<pre><code>" + _html.escape("\n".join(lines[i + 1:j]), quote=False) + "</code></pre>")
            i = j + 1
            continue
        if line.lstrip().startswith("<"):
            j = i
            while j < n and lines[j].strip():
                j += 1
            out.append("\n".join(lines[i:j]))
            i = j
            continue
        if line.lstrip().startswith(">"):
            j = i
            while j < n and lines[j].lstrip().startswith(">"):
                j += 1
            out.append(_render_quote([re.sub(r"^\s*> ?", "", l) for l in lines[i:j]]))
            i = j
            continue
        if line.lstrip().startswith("|") and i + 1 < n and TABLE_SEP.match(lines[i + 1]):
            j = i + 2
            while j < n and lines[j].lstrip().startswith("|"):
                j += 1
            head = "<tr>" + "".join(f"<th>{inline(c)}</th>" for c in _cells(line)) + "</tr>"
            rows = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in _cells(r)) + "</tr>" for r in lines[i + 2:j])
            out.append(f'<div class="tbl"><table>{head}{rows}</table></div>')
            i = j
            continue
        if LIST_ITEM.match(line):
            j = i + 1
            while j < n and lines[j].strip() and (LIST_ITEM.match(lines[j]) or lines[j].startswith((" ", "\t"))):
                j += 1
            out.append(_render_list(lines[i:j]))
            i = j
            continue
        hm = HEADING.match(line)
        if hm:
            lvl = {1: 4, 2: 4, 3: 4, 4: 5}.get(len(hm.group(1)), 6)
            out.append(f'<h{lvl} class="mdh">{inline(hm.group(2))}</h{lvl}>')
            i += 1
            continue
        if HR.match(line):
            out.append("<hr>")
            i += 1
            continue
        j = i + 1
        while j < n and lines[j].strip() and not _starts_block(lines[j]):
            j += 1
        out.append("<p>" + inline("\n".join(l.strip() for l in lines[i:j])) + "</p>")
        i = j
    return "".join(out)


def _render_quote(lines: list[str]) -> str:
    m = re.match(r"^\s*\[!([^\]]+)\]\s*(.*)$", lines[0]) if lines else None
    if m:
        cls = BOX_ALIASES.get(fold(m.group(1)), "ex")
        body = lines[1:]
        paras, cur = [], []
        for l in body:
            if l.strip():
                cur.append(l.strip())
            elif cur:
                paras.append(cur)
                cur = []
        if cur:
            paras.append(cur)
        if len(paras) <= 1:
            inner = inline("\n".join(paras[0])) if paras else ""
        else:
            inner = "".join("<p>" + inline("\n".join(p)) + "</p>" for p in paras)
        return f'<div class="box {cls}"><b class="l">{inline(m.group(2))}</b>{inner}</div>'
    return "<blockquote>" + render("\n".join(lines)) + "</blockquote>"


# =========================================================================== HTML -> MARKDOWN (migração, com verificação)
BLOCK_TAGS = {"p", "div", "ol", "ul", "li", "table", "tr", "td", "th", "pre", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "hr", "tbody", "thead"}
VOID = {"br", "hr", "img", "input", "meta", "link", "wbr", "col", "source"}
TAG = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9]*)\b([^<>]*?)(/?)>")


class _Tokens(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.t: list[tuple] = []

    def handle_starttag(self, tag, attrs):
        attrs = [(k, (v or "")) for k, v in attrs if k not in ("target", "rel")]
        self.t.append(("s", tag, tuple(sorted(attrs))))

    def handle_endtag(self, tag):
        self.t.append(("e", tag))

    def handle_data(self, data):
        self.t.append(("t", data))


def dom_signature(html_text: str) -> list[tuple]:
    p = _Tokens()
    p.feed(html_text)
    p.close()
    toks: list[tuple] = []
    for tk in p.t:
        if tk[0] == "t" and toks and toks[-1][0] == "t":
            toks[-1] = ("t", toks[-1][1] + tk[1])
        else:
            toks.append(tk)
    out: list[tuple] = []
    for i, tk in enumerate(toks):
        if tk[0] != "t":
            out.append(tk)
            continue
        txt = re.sub(r"\s+", " ", tk[1])
        prev = toks[i - 1] if i else None
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        if prev is None or (prev[0] in "se" and prev[1] in BLOCK_TAGS):
            txt = txt.lstrip()
        if nxt is None or (nxt[0] in "se" and nxt[1] in BLOCK_TAGS):
            txt = txt.rstrip()
        if txt:
            out.append(("t", txt))
    return out


def same_html(a: str, b: str) -> bool:
    return dom_signature(a) == dom_signature(b)


def top_blocks(html_text: str) -> list[str]:
    """Divide em elementos de nível superior (texto solto vira bloco próprio)."""
    blocks, depth, start, pos = [], 0, None, 0
    for m in TAG.finditer(html_text):
        close, name, _, selfclose = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
        if depth == 0 and m.start() > pos and html_text[pos:m.start()].strip():
            blocks.append(html_text[pos:m.start()])
        if close:
            depth -= 1
            if depth == 0 and start is not None:
                blocks.append(html_text[start:m.end()])
                start = None
                pos = m.end()
            depth = max(depth, 0)
        elif name in VOID or selfclose:
            if depth == 0:
                blocks.append(m.group(0))
                pos = m.end()
        else:
            if depth == 0:
                start = m.start()
            depth += 1
    if depth == 0 and pos < len(html_text) and html_text[pos:].strip():
        blocks.append(html_text[pos:])
    elif start is not None:
        blocks.append(html_text[start:])
    return blocks


def _md_text(s: str, table: bool = False) -> str:
    s = s.replace("\\", "\\\\").replace("`", "\\`").replace("*", "\\*").replace("[", "\\[")
    if table:
        s = s.replace("|", "\\|")
    return s


def _inline_md(h: str, table: bool = False) -> str | None:
    """HTML inline -> Markdown inline. None se não der para converter com segurança."""
    if "\n" in h:
        return None
    out, pos = [], 0
    stack: list[tuple[str, int, str]] = []
    tokens = list(TAG.finditer(h))
    i = 0
    while i < len(tokens):
        m = tokens[i]
        out.append(_md_text(h[pos:m.start()], table))
        close, name, attrs = m.group(1), m.group(2).lower(), m.group(3).strip()
        if not close and name == "code" and not attrs:
            end = h.find("</code>", m.end())
            inner = h[m.end():end] if end >= 0 else None
            if inner is not None and "<" not in re.sub(r"<(?![A-Za-z/!])", "", inner) and "`" not in inner and inner.strip() == inner and inner:
                txt = _html.unescape(inner)
                if table and "|" in txt:
                    return None
                out.append("`" + txt + "`")
                pos = end + len("</code>")
                while i < len(tokens) and tokens[i].start() < pos:
                    i += 1
                continue
            out.append(m.group(0))
        elif name in ("b", "strong", "i", "em") and not attrs:
            mark = "**" if name in ("b", "strong") else "*"
            out.append(mark)
        else:
            out.append(m.group(0))
        pos = m.end()
        i += 1
    out.append(_md_text(h[pos:], table))
    return "".join(out)


_LINE_START = re.compile(r"^(\s*)([#>|+\-]|\d+[.)]\s|```|~~~)")


def _guard_start(line: str) -> str:
    m = _LINE_START.match(line)
    if m:
        return m.group(1) + "\\" + line[len(m.group(1)):]
    return line


def block_to_md(block: str) -> str:
    """Converte um bloco HTML; se a conversão não reproduzir exatamente o mesmo DOM, mantém o HTML."""
    cand = _convert_block(block)
    if cand is not None and same_html(render(cand), block):
        return cand
    raw = block.strip()
    if not raw.startswith("<"):
        raw = "<span>" + raw + "</span>"  # texto solto: precisa começar com '<' para ser HTML cru
    pretty = _pretty_container(raw)
    if pretty and same_html(render(pretty), block):
        return pretty
    return raw.replace("\n\n", "\n")


def _pretty_container(raw: str) -> str | None:
    """<div class="kpi"><div>…</div><div>…</div></div> -> um filho por linha (mais fácil de ler e editar)."""
    m = re.fullmatch(r"(<div\b[^<>]*>)(.*)(</div>)", raw, re.S)
    if not m or "\n" in raw:
        return None
    kids = top_blocks(m.group(2))
    if len(kids) < 2 or not all(re.match(r"<(div|span)\b", k.strip()) for k in kids):
        return None
    return m.group(1) + "\n" + "\n".join(k.strip() for k in kids) + "\n" + m.group(3)


def _convert_block(b: str) -> str | None:
    s = b.strip()
    m = re.fullmatch(r"<p>(.*)</p>", s, re.S)
    if m and "<p" not in m.group(1):
        t = _inline_md(m.group(1))
        return _guard_start(t) if t is not None and t.strip() else None
    m = re.fullmatch(r"<(ol|ul)>(.*)</\1>", s, re.S)
    if m:
        lis = re.findall(r"<li>(.*?)</li>", m.group(2), re.S)
        if re.sub(r"<li>.*?</li>", "", m.group(2), flags=re.S).strip():
            return None
        lines = []
        for k, li in enumerate(lis, 1):
            if re.search(r"<(ol|ul|li|p|div|table)\b", li):
                return None
            t = _inline_md(li)
            if t is None:
                return None
            lines.append((f"{k}. " if m.group(1) == "ol" else "- ") + t)
        return "\n".join(lines)
    m = re.fullmatch(r'<div class="box (\w+)"><b class="l">(.*?)</b>(.*)</div>', s, re.S)
    if m and m.group(1) in BOX_NAMES:
        title, body = _inline_md(m.group(2)), _inline_md(m.group(3))
        if title is None or body is None:
            return None
        return f"> [!{BOX_NAMES[m.group(1)]}] {title}" + (f"\n> {body}" if body.strip() else "")
    m = re.fullmatch(r'<div class="tbl"><table>(.*)</table></div>', s, re.S)
    if m:
        rows = re.findall(r"<tr>(.*?)</tr>", m.group(1), re.S)
        if not rows or re.sub(r"<tr>.*?</tr>", "", m.group(1), flags=re.S).strip():
            return None
        head = re.findall(r"<th>(.*?)</th>", rows[0], re.S)
        if not head or re.sub(r"<th>.*?</th>", "", rows[0], flags=re.S).strip():
            return None
        out = ["| " + " | ".join(_inline_md(c, True) or "\x01" for c in head) + " |", "|" + "|".join("---" for _ in head) + "|"]
        for r in rows[1:]:
            cells = re.findall(r"<td>(.*?)</td>", r, re.S)
            if re.sub(r"<td>.*?</td>", "", r, flags=re.S).strip():
                return None
            out.append("| " + " | ".join(_inline_md(c, True) or "\x01" for c in cells) + " |")
        txt = "\n".join(out)
        return None if "\x01" in txt else txt
    m = re.fullmatch(r"<pre><code>(.*)</code></pre>", s, re.S)
    if m and "<" not in re.sub(r"<(?![A-Za-z/!])", "", m.group(1)) and "```" not in m.group(1):
        return "```\n" + _html.unescape(m.group(1)) + "\n```"
    return None


def html_to_md(h: str) -> tuple[str, dict[str, int]]:
    blocks = top_blocks(h or "")
    md_blocks, stats = [], {"md": 0, "html": 0}
    for b in blocks:
        md = block_to_md(b)
        stats["md" if not md.startswith("<") else "html"] += 1
        md_blocks.append(md)
    return "\n\n".join(md_blocks), stats


# =========================================================================== VISÃO DO PAINEL
_RENDER_CACHE: dict[str, str] = {}


def render_cached(md: str) -> str:
    key = sha(md, 24)
    hit = _RENDER_CACHE.get(key)
    if hit is None:
        hit = render(md)
        if len(_RENDER_CACHE) > 4000:
            _RENDER_CACHE.clear()
        _RENDER_CACHE[key] = hit
    return hit


def _people_from_owner(own: str) -> list[str]:
    found = []
    for code in re.findall(r"\b(?:Pessoa\s+)?([A-Z])\b|\b(Equipe)\b", own or ""):
        c = code[0] or code[1]
        if c and c not in found:
            found.append(c)
    return found


def item_view(it: dict[str, Any], flags: dict[str, Any] | None = None) -> dict[str, Any]:
    m = it.get("meta", {})
    def g(k, default=""):
        v = m.get(k)
        return default if v is None else v
    ow = split_list(g("pessoas"))
    if not ow:
        ow = _people_from_owner(g("responsável"))
    load = g("carga")
    est = fold(g("estratégia", "desenvolver")) or "desenvolver"
    st = fold(g("situação", "aberta")) or "aberta"
    v = {
        "id": it["id"], "t": it.get("title", ""), "p": (g("prioridade", "P3") or "P3").upper(),
        "st": st if st in EDITORIAL else "aberta", "est": est if est in STRATEGIES else "desenvolver",
        "m": g("marco", "—") or "—", "due": g("data ideal", "—") or "—", "own": g("responsável", "—") or "—", "ow": ow,
        "src": g("fonte", "—") or "—", "dep": parse_ids(g("depende de")), "tags": split_list(g("tags")),
        "pillar": "" if fold(g("pilar")) in EMPTY else g("pilar"),
        "load": int(load) if re.fullmatch(r"\d+", str(load).strip()) else None,
        "new": parse_bool(g("novo", "não")), "prof": parse_bool(g("professores", "não")),
        "files": split_list(g("arquivos")), "rm": "" if fold(g("removido")) in EMPTY else g("removido"),
        "intro": render_cached(it["intro"]) if it.get("intro") else "",
        "u": "", "pb": "", "fz": "", "pq": "", "x": [],
        "xm": [[k, val] for k, val in it.get("extra_meta", [])],
    }
    for h, body in it.get("sections", []):
        code = section_code(h)
        html_body = render_cached(body)
        if code and not v[code]:
            v[code] = html_body
            v[code + "_h"] = h
        else:
            v["x"].append([h, html_body])
    if flags:
        v.update(flags)
    v["h"] = sha(json.dumps(v, ensure_ascii=False, sort_keys=True), 12)
    return v


def panel_view(doc: dict[str, Any]) -> dict[str, Any]:
    G: dict[str, Any] = {"help": [], "extra": []}
    p = doc.get("panel") or {}
    for h, body in p.get("sections", []):
        f = fold(h)
        if f.startswith("titulo"):
            G["title"] = inline(one_line(body))
        elif f.startswith("subtitulo"):
            G["subtitle"] = render_cached(body)
        elif f.startswith("entrega"):
            m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", body)
            G["deadline"] = f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}" if m else ""
            G["deadline_label"] = one_line(body)
        elif f.startswith("cronograma"):
            tl = []
            for line in body.split("\n"):
                mm = re.match(r"^\s*[-*+]\s+(?:\*\*(.+?)\*\*|([^—:]+?)\s*[—:])\s*[—:-]?\s*(.*)$", line)
                if mm:
                    tl.append({"when": (mm.group(1) or mm.group(2) or "").strip(), "text": inline(mm.group(3).strip())})
            G["timeline"] = tl
        elif f.startswith("caminho critico"):
            G["chain"] = parse_ids(body)
        elif f.startswith("pessoas"):
            ppl = []
            for line in body.split("\n"):
                mm = re.match(r"^\s*[-*+]\s+(?:\*\*(.+?)\*\*|(\S+))\s*[—:-]+\s*(.*)$", line)
                if mm:
                    ppl.append({"code": (mm.group(1) or mm.group(2)).strip(), "desc": inline(mm.group(3).strip())})
            G["people"] = ppl
        elif f.startswith("legenda das estrategias"):
            G["legend"] = render_cached(body)
        elif f.startswith("como ler"):
            G["howtoread"] = render_cached(body)
        elif f.startswith("aviso"):
            G["notice"] = render_cached(body)
        elif f.startswith("ajuda"):
            G["help"].append({"title": re.sub(r"^ajuda\s*[·:\-–—]\s*", "", h, flags=re.I).strip() or h, "html": render_cached(body)})
        elif f.startswith("rodape"):
            G["footer"] = render_cached(body)
        else:
            G["extra"].append({"title": h, "html": render_cached(body)})
    return G


def item_order(doc: dict[str, Any]) -> list[str]:
    laid = [r for k, r in doc.get("layout", []) if k == "item" and r in doc["items"]]
    seen = set(laid)
    return list(dict.fromkeys(laid + [i for i in doc["items"] if i not in seen]))


def build_view(doc: dict[str, Any], source: dict[str, Any] | None = None,
               flags: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    flags = flags or {}
    items = [item_view(doc["items"][i], flags.get(i)) for i in item_order(doc)]
    G = panel_view(doc)
    digest = sha(json.dumps([G, [it["h"] for it in items]], ensure_ascii=False, sort_keys=True), 16)
    meta = {"hash": digest, "format": FORMAT_VERSION, "items": len(items), "issues": doc.get("issues", [])[:60]}
    if source:
        meta.update(source)
    return {"meta": meta, "G": G, "D": items}


# =========================================================================== painel.html
def _js(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def data_block(view: dict[str, Any]) -> str:
    rows = ",\n".join(_js(d) for d in view["D"])
    return (f"{MARK_BEGIN}\n"
            "/* Gerado automaticamente a partir de PROJECT_STATUS_TEXT.md. Não edite aqui: edite o PROJECT_STATUS_TEXT.md ou use o editor do painel. */\n"
            f"let CONTENT_META={_js(view['meta'])};\n"
            f"let G={_js(view['G'])};\n"
            f"let D=[\n{rows}\n];\n"
            f"{MARK_END}")


EMBEDDED_HASH = re.compile(r'let CONTENT_META=\{[^\n]*?"hash":"([0-9a-f]+)"')


def embedded_hash(html_text: str) -> str | None:
    m = EMBEDDED_HASH.search(html_text)
    return m.group(1) if m else None


def update_html(path: Path, view: dict[str, Any], force: bool = False) -> bool:
    """Atualiza só a região de dados do painel.html. Retorna True se gravou."""
    text = path.read_text(encoding="utf-8")
    a, b = text.find(MARK_BEGIN), text.find(MARK_END)
    if a < 0 or b < 0 or b < a:
        raise ValueError(f"{path.name} não tem os marcadores {MARK_BEGIN} … {MARK_END}.")
    if not force and embedded_hash(text[a:b]) == view["meta"]["hash"]:
        return False
    new = text[:a] + data_block(view) + text[b + len(MARK_END):]
    if new != text:
        atomic_write(path, new)
        return True
    return False


def fill_html(template: Path, out: Path, view: dict[str, Any], force: bool = False) -> bool:
    """Gera `out` = modelo `template` + região de dados. O modelo nunca é alterado (pode ficar versionado no Git).
    Retorna True se gravou."""
    text = template.read_text(encoding="utf-8")
    a, b = text.find(MARK_BEGIN), text.find(MARK_END)
    if a < 0 or b < 0 or b < a:
        raise ValueError(f"{template.name} não tem os marcadores {MARK_BEGIN} … {MARK_END}.")
    new = text[:a] + data_block(view) + text[b + len(MARK_END):]
    try:
        old = out.read_text(encoding="utf-8")
    except FileNotFoundError:
        old = None
    if old == new and not force:
        return False
    if old != new:
        atomic_write(out, new)
        return True
    return False


def view_from_html(path: Path) -> dict[str, Any] | None:
    """Lê os dados embutidos (permite abrir o painel offline e serve de último recurso)."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    a, b = text.find(MARK_BEGIN), text.find(MARK_END)
    if a < 0 or b < 0:
        return None
    blk = text[a:b]
    try:
        meta = json.loads(re.search(r"let CONTENT_META=(.*?);\n", blk).group(1))
        G = json.loads(re.search(r"let G=(.*?);\n", blk).group(1))
        rows = re.search(r"let D=\[\n(.*)\n\];", blk, re.S)
        D = json.loads("[" + (rows.group(1) if rows else "") + "]")
        return {"meta": meta, "G": G, "D": D}
    except Exception:
        return None


# =========================================================================== MIGRAÇÃO (painel v4 -> PROJECT_STATUS_TEXT.md)
def items_from_legacy_html(text: str) -> list[dict[str, Any]] | None:
    """Painel v4 guardava os itens numa linha `const D=[...]`. Lê como JSON (o literal é JSON válido)."""
    m = re.search(r"^const D=(\[.*\]);\s*$", text, re.M)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def item_from_view(d: dict[str, Any], convert: bool = True) -> tuple[dict[str, Any], dict[str, int]]:
    """Item no formato do painel (v4 ou v5) -> item do modelo, convertendo HTML em Markdown verificado."""
    stats = {"md": 0, "html": 0}

    def md(h: str) -> str:
        if not convert:
            return h
        out, st = html_to_md(h)
        stats["md"] += st["md"]
        stats["html"] += st["html"]
        return out

    yes = lambda b: "sim" if b else "não"
    meta = {
        "prioridade": d.get("p", "P3"), "situação": d.get("st", "aberta"), "estratégia": d.get("est", "desenvolver"),
        "marco": d.get("m") or "—", "data ideal": d.get("due") or "—", "responsável": d.get("own") or "—",
        "pessoas": ", ".join(d.get("ow") or []) or "—", "fonte": d.get("src") or "—",
        "depende de": ", ".join("#" + x for x in d.get("dep") or []) or "—", "tags": ", ".join(d.get("tags") or []) or "—",
        "pilar": d.get("pillar") or "—", "carga": str(d["load"]) if d.get("load") not in (None, "") else "—",
        "novo": yes(d.get("new")), "professores": yes(d.get("prof")),
    }
    if d.get("files"):
        meta["arquivos"] = ", ".join(d["files"])
    if d.get("rm"):
        meta["removido"] = d["rm"]
    sections = [[SECTION_DEFAULT[c], md(d.get(c, ""))] for c, _ in SECTIONS]
    for h, body in d.get("x", []):
        sections.append([h, md(body)])
    return {"id": str(d["id"]), "title": d.get("t", ""), "meta": meta, "extra_meta": [], "intro": "", "sections": sections}, stats


PREAMBLE = """<!-- PROJECT_STATUS_TEXT.md · formato 1 · fonte do conteúdo do Painel de Pendências SRAG -->
# Status do projeto SRAG · conteúdo textual

Este arquivo é a **fonte única de todo o texto** do Painel de Pendências (`.srag-status-local/painel.html`). O painel lê este arquivo do GitHub, converte para HTML e grava o conteúdo **dentro** do `painel.html` sempre que algo muda (só a região de dados; nada é reescrito quando não há mudança). A situação compartilhada de cada item (concluída, a confirmar, precisa revisão…), os comentários e a auditoria continuam em `PROJECT_STATUS.md`, mantido só pelo painel.

**Pode editar à mão** no VS Code ou pelo botão ✎ do painel. Ao salvar aqui, o painel mostra a mudança em ~2 s como prévia local. Para a equipe receber: commit e push normais, ou o botão “Publicar edições locais” do painel.

Regras do formato:

- `## #N · Título` abre um item. O número é fixo e nunca é reutilizado; para tirar um item, use `- removido: motivo`.
- Logo abaixo do título, uma linha por campo: `prioridade` (P1–P4), `situação` (aberta, parcial, resolvida), `estratégia` (desenvolver, explorar, documentar, despriorizar, resolvida), `marco`, `data ideal` (DD/MM), `responsável`, `pessoas` (A, B, C, Equipe), `fonte`, `depende de` (#12, #30), `tags`, `pilar`, `carga` (número), `novo` (sim/não), `professores` (sim/não) e, opcionais, `arquivos` (caminhos que a auditoria deve ligar ao item) e `removido`. Use `—` para vazio. “Trava” é calculado sozinho a partir de “depende de”.
- Seções com `###`: `① Para entender`, `② Problema`, `③ O que fazer` e `④ Pronto quando`. Qualquer outro `### Título` vira uma seção extra no card.
- `④ Pronto quando`: um critério por linha, no formato `- verbo: argumentos | descrição detalhada`. O verificador (`.srag-status-local/deep_git_project_audit.py`) confere cada critério contra o repositório. Verbos: `existe`, `nao-existe`, `nao-vazio`, `define`, `nao-define`, `contem`, `nao-contem`, `yaml`, `json`, `teste`, `notebook-executado`, `notebook-saida` e `manual`. Exemplo: ``- define: `src/data/split.py` :: `criar_group_id` | A função criar_group_id existe em src/data/split.py``. A gramática completa está no topo do verificador.
- Texto em Markdown simples: parágrafos, `**negrito**`, `*itálico*`, `` `código` ``, listas com `-` ou `1.`, tabelas `| a | b |`, blocos de código com três crases, links `[texto](url)` e caixas `> [!decisão] Título` (também `atenção`, `exemplo`, `ok` e `pilar`). HTML também é aceito: um bloco que começa com `<` passa sem alteração (é assim que ficam os gráficos de barras e os quadros de números).
- Dentro das seções, não comece linhas com dois ou três `#` seguidos de espaço (subtítulo: use `####`). `#30` no meio do texto vira link para o item no painel.
- `## Painel · textos gerais` guarda os textos do topo, entrega, cronograma, pessoas, caminho crítico, aviso, ajuda e rodapé."""

DEFAULT_PANEL_SECTIONS = [
    ["Título", "Projeto SRAG · Pendências"],
    ["Subtítulo", "Carga equilibrada, exclusividade de notebooks e decisões já fechadas: coorte definitiva inicial baseada na seleção de features provisória; treino em 2019, 2023, 2024 e 2025; Teste A nesses mesmos anos; Teste B em 2019–2025; 2026 apenas como exploração opcional no fim. Entrega: **03/11/2026**."],
    ["Entrega", "03/11/2026"],
    ["Cronograma", "\n".join([
        "- **18/10** — Registrar decisões e alinhar YAMLs",
        "- **19–21/10** — Blindar artefatos, partição e teste",
        "- **22/10** — Gerar mapa com test_ref e test_pandemic",
        "- **23/10** — Concluir validações internas",
        "- **24/10** — Professor: validação acadêmica não bloqueante",
        "- **25–28/10** — Importância, geografia, tuning curto e UMAP exploratório",
        "- **29/10** — Congelar modelo",
        "- **30/10** — Abrir Testes A/B",
        "- **31/10–02/11** — Relatório e contingência; 2026 só se sobrar capacidade",
    ])],
    ["Legenda das estratégias", '<div class="legend"><span class="tag e-desenvolver">▶ Desenvolver</span>necessário <span class="tag e-explorar">\U0001F50D Explorar</span>opcional com prazo <span class="tag e-documentar">✎ Decidir/documentar</span>contrato e decisão <span class="tag e-despriorizar">⏸ Despriorizado</span>não entra antes da entrega</div>'],
    ["Como ler", "\n\n".join([
        "Cada card é uma pendência. Dentro dele: **① Para entender** (o tema em linguagem simples, com números do projeto), **② Problema** (o que está errado, com detalhes técnicos), **③ O que fazer** (passos), **④ Ligações** (de quem depende e o que trava) e **⑤ Evidências** (commits, auditoria e histórico). Os números dos itens são fixos e mantêm seus números históricos; o item #108 foi removido por impossibilidade material de recuperar a gravação. Cada card mostra a data ideal mesmo quando fechado.",
        '<div class="legend"><span class="tag" style="background:var(--p1);color:#fff">P1</span>bloqueia o próximo passo ou compromete resultados <span class="tag" style="background:var(--p2);color:#fff">P2</span>afeta a validade ou a defesa <span class="tag" style="background:var(--p3);color:#fff">P3</span>consistência e organização <span class="tag" style="background:var(--p4);color:#fff">P4</span>melhoria <span class="tag" style="background:var(--ok);color:#fff">✓</span>resolvida</div>',
        '<div class="legend"><span class="tag blk">travado</span>depende de item ainda aberto <span class="tag rdy">pronto</span>pode começar já <span class="tag trv">trava N</span>quantos itens esperam por ele <span class="tag new">novo</span>surgiu na revisão de 18/10 <span class="tag mk">M3</span>marco lógico <span class="tag due">24/10</span>data ideal visível no card fechado <span class="tag pil">pilar</span>pilar do plano</div>',
    ])],
    ["Pessoas", "\n".join([
        "- **A** — protocolo e auditoria",
        "- **B** — EDA, clustering, pilotos",
        "- **C** — pipeline e modelos",
        "- **Equipe** — itens conjuntos",
    ])],
    ["Caminho crítico", "#120 → #123 → #86 → #121 → #118 → #127 → #119 → #91 → #110 → #1 → #79 → #80 → #77 → #81 → #2"],
    ["Aviso da revisão", "> [!atenção] Mudança importante desta revisão\n> Período e coorte estão fechados. O caminho crítico agora é: registrar o contrato, blindar os blocos, treinar uma vez, congelar e executar duas janelas de teste. 2026 não bloqueia nada."],
    ["Ajuda · Como usar (30 segundos)", "\n\n".join([
        "\n".join([
            "- **Abrir:** dois cliques em `.srag-status-local\\ABRIR_PAINEL.cmd`. Abre uma janela do terminal que fica aberta rodando o servidor; não feche enquanto usa. Se já estiver aberto, só abre a aba.",
            "- **Marcar:** concluir, reabrir, comentar ou confirmar/rejeitar uma sugestão: em ~12 s sai um commit curto só com os arquivos do painel, ex.: `(#status) #10 concluída · Mateus`. “▶ Estou fazendo” é só seu e não gera commit.",
            "- **Editar o conteúdo:** botão ✎ no card (ou ➕ Nova pendência). A alteração vai para o `PROJECT_STATUS_TEXT.md` no mesmo tipo de commit curto, campo a campo. Também dá para editar o `PROJECT_STATUS_TEXT.md` direto no VS Code: o painel mostra a prévia em ~2 s.",
            "- **Atualizar:** automático a cada hora e ao voltar para a aba. **⟳ Buscar** força agora e **nunca gera commit**. **\U0001F50E Verificar pronto quando** confere os critérios de todas as pendências, roda os testes e só gera commit se alguma pendência mudar.",
            "- **Commits do dia a dia:** continue no VS Code. Escreva `tarefa 30`, `#30` ou `[done:#30]` na mensagem: o painel reconhece sozinho.",
        ]),
        "> [!ok] Por que o VS Code não reclama\n> O painel **nunca** grava o `PROJECT_STATUS.md` na sua pasta de trabalho. Ele lê o arquivo direto do GitHub e publica o commit “por fora”. Assim o arquivo nunca aparece como modificado e o *pull* não dá erro. Quando a única novidade remota são os arquivos do painel e sua branch não tem commits locais, o painel ainda avança sua branch sozinho. Se encontrar uma versão antiga modificada do `PROJECT_STATUS.md` na pasta (versões anteriores do painel), ele guarda backup, converte as marcações em alterações do painel e devolve o arquivo ao estado do commit. O `PROJECT_STATUS_TEXT.md` é diferente: é seu para editar, e o painel só mexe nele na pasta quando você clica em “Publicar edições locais”.",
        "> [!atenção] Quando sai commit\n> Só quando há decisão: concluir, reabrir, comentar, confirmar/rejeitar sugestão, escolher num conflito, editar conteúdo pelo painel, ou quando a auditoria muda uma pendência. Buscar, ler commits, “Estou fazendo”, prévia de edições locais e resumo da auditoria nunca geram commit: cada painel lê o mesmo histórico do Git e chega ao mesmo resultado sozinho.",
        "> [!atenção] Três pessoas ao mesmo tempo\n> Cada clique vira uma alteração pequena (item + campo). Na hora de publicar, o painel busca a versão mais nova do GitHub e reaplica as suas alterações por cima. Itens ou campos diferentes nunca conflitam; comentários sempre somam. Se duas pessoas mudarem o **mesmo** campo (situação, título, uma seção…) para valores diferentes, vale o que chegou primeiro e a outra recebe um aviso aqui em cima para decidir. Push rejeitado por concorrência é refeito automaticamente; nunca usa `--force`. Sem internet, a fila fica guardada e sai sozinha depois.",
    ])],
    ["Ajuda · Como interpretar os estados", "\n".join([
        "- **ABERTA:** sem evidência suficiente.",
        "- **EM ANDAMENTO:** commit com `[progress:#ID]` ou commit que só cita a tarefa (lido por cada painel, sem commit). O “▶ Estou fazendo” aparece só para você.",
        "- **RESOLVIDA — PENDENTE DE VALIDAÇÃO (a confirmar):** commit cita a tarefa com linguagem de conclusão (“tarefa 30 concluída”, “corrige #30”) ou a auditoria achou commit nos arquivos da tarefa, sem problema impeditivo. Um humano confirma com um clique.",
        "- **PRECISA REVISÃO:** há implementação relacionada, mas a auditoria achou problema grave (notebook com erro salvo, sintaxe, JSON/YAML inválido, conflito de merge, teste falhando, possível vazamento).",
        "- **CONCLUÍDA:** confirmação humana no painel ou marcador `[done:#ID]` no commit. Automação nunca conclui sozinha.",
        "- **⚠ Reconfirmar:** item concluído cujos arquivos voltaram a apresentar problema. A conclusão não é apagada.",
        "- **Situação editorial** (aberta, parcial, resolvida no `PROJECT_STATUS_TEXT.md`) é o que o texto do card descreve; a **situação compartilhada** acima é a que vale para o andamento. Um item concluído no painel aparece como resolvido mesmo que o texto ainda diga “aberta”.",
    ])],
    ["Ajuda · Marcadores reconhecidos nos commits", "\n".join([
        "- `[done:#30]`, `[feito:#30]` → concluída. `[progress:#30]` → em andamento. `[reopen:#30]` → reaberta.",
        "- `tarefa 30`, `tarefas 30, 31 e 32`, `item 30`, `pendência 30`, `task 30`, `#30` → com palavra de conclusão (corrige, implementa, resolve, conclui, finaliza, fecha, feito, pronto, fix, done…) vira “a confirmar”; sem ela, “em andamento”.",
        "- “Merge pull request #N” é ignorado. Commits do próprio painel e commits que só mexem no `PROJECT_STATUS_TEXT.md` também (editar texto não conta como progresso).",
    ])],
    ["Ajuda · Editar o conteúdo (PROJECT_STATUS_TEXT.md)", "\n".join([
        "- **Pelo painel:** ✎ Editar no card abre o editor com todos os campos e as seções em Markdown, com pré-visualização. Salvar enfileira só os campos que você mudou; o commit sai em ~12 s junto com outras marcações.",
        "- **Pelo VS Code:** edite `PROJECT_STATUS_TEXT.md` na raiz do repositório e salve. O painel detecta em ~2 s, mostra a prévia com o selo “prévia local” e lista os itens alterados no topo. Depois faça commit e push normais, ou clique em **Publicar edições locais** (o painel publica só as suas diferenças, campo a campo, e devolve o arquivo da pasta ao estado do Git).",
        "- **Item novo:** ➕ Nova pendência no painel (o número é definido na publicação, sem colisão) ou um novo `## #N · Título` no arquivo usando o próximo número livre.",
        "- **Remover:** nunca apague a seção; use `- removido: motivo`. O número fica reservado e o card some da lista (filtro “Removidos” mostra).",
        "- **Erros de formato** (número repetido, dependência inexistente, valor desconhecido) aparecem num aviso no topo; o painel continua funcionando com o resto.",
    ])],
    ["Ajuda · Se algo parecer errado", "\n".join([
        "- Clique em **⟳ Buscar atualizações**. Nada é perdido: há fila local, backups em `.srag-status-local/backups` e todo o histórico no Git.",
        "- Sugestão automática errada? Use **✗ Não é isso** no card: ela volta ao estado anterior e aquele commit não será usado de novo para o item.",
        "- Marcou errado? Desmarque “feito”: a reabertura fica no histórico do card.",
        "- Se o GitHub recusar (credencial), faça um *push* qualquer pelo VS Code uma vez para salvar a credencial e clique em Buscar.",
        "- Painel sem texto ou desatualizado? Rode `.\\.venv\\Scripts\\python.exe .srag-status-local\\server.py gerar` para regenerar o `painel.html` a partir do `PROJECT_STATUS_TEXT.md`, e `... server.py validar` para listar problemas de formato.",
        "- Diagnóstico: `DIAGNOSTICO.cmd` e o arquivo `.srag-status-local/logs/painel.log`.",
    ])],
    ["Rodapé", "Painel local de acompanhamento do projeto. O conteúdo vem de `PROJECT_STATUS_TEXT.md` e o estado compartilhado de `PROJECT_STATUS.md`, ambos publicados pelo painel direto no GitHub. Painel v6."],
]

REMOVED_STUBS = [
    {"id": "108", "title": "Item removido (número reservado)", "meta": {"prioridade": "P4", "situação": "resolvida", "estratégia": "despriorizar",
     "marco": "—", "data ideal": "—", "responsável": "—", "pessoas": "—", "fonte": "—", "depende de": "—", "tags": "—", "pilar": "—",
     "carga": "—", "novo": "não", "professores": "não", "removido": "impossibilidade material de recuperar a gravação"},
     "extra_meta": [], "intro": "", "sections": []},
]


def bootstrap_doc(legacy_items: list[dict[str, Any]], convert: bool = True) -> tuple[dict[str, Any], dict[str, int]]:
    """Monta o PROJECT_STATUS_TEXT.md inicial a partir dos itens do painel antigo + textos gerais padrão."""
    doc: dict[str, Any] = {"preamble": PREAMBLE, "panel": {"heading": "Painel · textos gerais", "intro": "",
                                                          "sections": copy.deepcopy(DEFAULT_PANEL_SECTIONS)},
                           "items": {}, "layout": [["panel", ""]], "issues": []}
    stats = {"md": 0, "html": 0}
    for d in legacy_items:
        it, st = item_from_view(d, convert)
        stats["md"] += st["md"]
        stats["html"] += st["html"]
        doc["items"][it["id"]] = it
        doc["layout"].append(["item", it["id"]])
    for stub in REMOVED_STUBS:
        if stub["id"] not in doc["items"]:
            doc["items"][stub["id"]] = copy.deepcopy(stub)
            doc["layout"].append(["item", stub["id"]])
    _validate(doc)
    return doc, stats
