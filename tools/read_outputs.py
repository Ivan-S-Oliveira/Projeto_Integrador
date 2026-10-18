#!/usr/bin/env python3
"""Compila resultados locais do projeto em um pacote legível por humanos e IAs.

Uso recomendado, na raiz do repositório:
    python tools/read_outputs.py
    python tools/read_outputs.py --output-dir .local-analysis/results
    python tools/read_outputs.py --include-notebook-outputs

A ferramenta não recalcula análises nem altera artefatos originais. Ela varre resultados
textuais, tabulares, estruturados, modelos e imagens; gera um Markdown consolidado, um
JSON de inventário, um CSV de catálogo e uma pasta local de thumbnails.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import platform
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import pandas as pd
except Exception:
    pd = None

try:
    from PIL import Image, ImageStat
except Exception:
    Image = None
    ImageStat = None

TEXT_EXT = {".txt", ".md", ".log", ".rst"}
TABLE_EXT = {".csv", ".tsv"}
STRUCTURED_EXT = {".json", ".yaml", ".yml"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
MODEL_EXT = {".joblib", ".pkl", ".pickle", ".onnx", ".pt", ".pth", ".h5", ".hdf5"}
NOTEBOOK_EXT = {".ipynb"}
RESULT_DIR_NAMES = {
    "outputs", "output", "results", "resultados", "reports", "report", "figures",
    "figuras", "tables", "tabelas", "metrics", "metricas", "predictions", "predicoes",
    "runs", "models", "modelos", "artifacts", "artefatos", "logs", "evaluation",
    "avaliacao", "experiments", "experimentos",
}
RESULT_NAME_HINTS = {
    "result", "resultado", "metric", "metrica", "score", "prediction", "predicao",
    "evaluation", "avaliacao", "report", "relatorio", "manifest", "manifesto", "waterfall",
    "comparison", "comparacao", "calibration", "calibracao", "confusion", "confusao",
    "importance", "importancia", "bootstrap", "subgroup", "subgrupo", "error", "erro",
    "performance", "benchmark", "summary", "resumo", "feature", "cluster", "silhouette",
    "auc", "brier", "threshold", "limiar", "shap", "umap", "pca",
}
EXCLUDED_DIR_NAMES = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".tox", ".nox", ".ipynb_checkpoints", "node_modules", ".idea",
    ".vscode", "site-packages", "build", "dist", ".local-analysis",
    ".srag-status-local", ".project-status-local",
}
SECRET_RE = re.compile(r"(?im)^\s*([A-Za-z_][\w.-]*(?:token|secret|password|passwd|pwd|api[_-]?key|private[_-]?key|credential)[\w.-]*)\s*[:=]\s*(.+)$")
WINDOWS_USER_RE = re.compile(r"(?i)\b[A-Z]:[\\/]+Users[\\/]+[^\\/\s\"'<>|]+")
POSIX_HOME_RE = re.compile(r"(?<![A-Za-z0-9_])/(?:home|Users)/[^/\s\"'<>|]+")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def human_bytes(n: int) -> str:
    value = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return str(n)


def repo_root(start: Path) -> Path:
    p = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start, text=True, capture_output=True, encoding="utf-8", errors="replace")
    return Path(p.stdout.strip()).resolve() if p.returncode == 0 and p.stdout.strip() else start.resolve()


def redact(text: str, root: Path) -> str:
    text = SECRET_RE.sub(lambda m: f"{m.group(1)}=[REDACTED]", text)
    text = text.replace(str(root), "<REPO>").replace(root.as_posix(), "<REPO>")
    text = WINDOWS_USER_RE.sub("<HOME>", text)
    text = POSIX_HOME_RE.sub("<HOME>", text)
    return text


def is_candidate(path: Path, root: Path, include_notebooks: bool) -> bool:
    rel = path.relative_to(root)
    parts_lower = [p.lower() for p in rel.parts]
    if any(p in EXCLUDED_DIR_NAMES for p in parts_lower[:-1]):
        return False
    ext = path.suffix.lower()
    supported = ext in TEXT_EXT | TABLE_EXT | STRUCTURED_EXT | IMAGE_EXT | MODEL_EXT or (include_notebooks and ext in NOTEBOOK_EXT)
    if not supported:
        return False
    in_result_dir = any(p in RESULT_DIR_NAMES for p in parts_lower[:-1])
    name = path.stem.lower()
    hinted = any(h in name for h in RESULT_NAME_HINTS)
    return in_result_dir or hinted


def walk_candidates(root: Path, include_notebooks: bool) -> list[Path]:
    found: list[Path] = []
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d.lower() not in EXCLUDED_DIR_NAMES)
        for name in sorted(files):
            p = Path(current) / name
            try:
                if is_candidate(p, root, include_notebooks):
                    found.append(p)
            except (OSError, ValueError):
                pass
    return sorted(found, key=lambda p: p.relative_to(root).as_posix().lower())


def read_text(path: Path, max_chars: int, root: Path) -> tuple[str, dict[str, Any]]:
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig", errors="replace")
    meta = {"encoding": "utf-8-sig/errors=replace", "characters": len(text), "truncated": len(text) > max_chars}
    if len(text) > max_chars:
        head = int(max_chars * 0.75)
        tail = max_chars - head
        text = text[:head] + f"\n... [{len(text)-max_chars} caracteres omitidos] ...\n" + text[-tail:]
    return redact(text, root), meta


def numeric_summary(series: Any) -> dict[str, Any]:
    clean = series.dropna()
    if clean.empty:
        return {"count": 0}
    desc = clean.describe(percentiles=[0.25, 0.5, 0.75])
    result = {}
    for key in ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]:
        if key in desc:
            value = desc[key]
            result[key] = None if pd.isna(value) else float(value)
    return result


def analyse_table(path: Path, args: argparse.Namespace, root: Path) -> tuple[str, dict[str, Any]]:
    sep = "\t" if path.suffix.lower() == ".tsv" else ","
    if pd is None:
        text, meta = read_text(path, args.max_text_chars, root)
        return text, {"warning": "pandas indisponível", **meta}
    try:
        df = pd.read_csv(path, sep=sep, encoding="utf-8-sig", nrows=args.max_table_rows, low_memory=False)
        total_rows = None
        try:
            with path.open("rb") as fh:
                total_rows = max(0, sum(1 for _ in fh) - 1)
        except Exception:
            pass
        info: dict[str, Any] = {
            "rows_total_estimated": total_rows,
            "rows_loaded": len(df),
            "columns": [str(c) for c in df.columns],
            "dtypes": {str(c): str(t) for c, t in df.dtypes.items()},
            "missing": {str(c): int(df[c].isna().sum()) for c in df.columns},
            "numeric_summary": {},
            "categorical_top": {},
        }
        for c in df.columns[: args.max_columns]:
            if pd.api.types.is_numeric_dtype(df[c]):
                info["numeric_summary"][str(c)] = numeric_summary(df[c])
            else:
                counts = df[c].astype("string").fillna("<NA>").value_counts(dropna=False).head(args.top_values)
                info["categorical_top"][str(c)] = {str(k): int(v) for k, v in counts.items()}
        preview = df.head(args.preview_rows).to_csv(index=False)
        lines = [
            f"Linhas totais estimadas: {total_rows if total_rows is not None else 'não calculado'}",
            f"Linhas analisadas: {len(df)}",
            f"Colunas: {len(df.columns)}",
            "",
            "Prévia:",
            preview.rstrip(),
            "",
            "Resumo estruturado:",
            json.dumps(info, ensure_ascii=False, indent=2, default=str),
        ]
        return redact("\n".join(lines), root), info
    except Exception as exc:
        return f"Falha ao ler tabela: {exc!r}", {"error": repr(exc)}


def flatten_json(value: Any, prefix: str = "", limit: int = 5000) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    def rec(v: Any, p: str) -> None:
        if len(out) >= limit:
            return
        if isinstance(v, dict):
            for k, child in v.items():
                rec(child, f"{p}.{k}" if p else str(k))
        elif isinstance(v, list):
            if len(v) <= 12 and all(not isinstance(x, (dict, list)) for x in v):
                out.append((p, repr(v)))
            else:
                out.append((p, f"<lista com {len(v)} itens>"))
                for i, child in enumerate(v[:20]):
                    rec(child, f"{p}[{i}]")
        else:
            out.append((p, repr(v)))
    rec(value, prefix)
    return out


def analyse_structured(path: Path, args: argparse.Namespace, root: Path) -> tuple[str, dict[str, Any]]:
    text, meta = read_text(path, args.max_text_chars, root)
    data = None
    try:
        if path.suffix.lower() == ".json":
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        else:
            try:
                import yaml
                data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
            except Exception as exc:
                meta["yaml_error"] = repr(exc)
        if data is not None:
            flat = flatten_json(data)
            meta["flattened_entries"] = len(flat)
            text += "\n\nChaves/valores estruturados:\n" + "\n".join(f"- {k}: {v}" for k, v in flat[: args.max_structured_entries])
    except Exception as exc:
        meta["error"] = repr(exc)
    return redact(text, root), meta


def image_entropy(img: Any) -> float | None:
    try:
        hist = img.convert("L").histogram()
        total = sum(hist)
        import math
        return -sum((n / total) * math.log2(n / total) for n in hist if n)
    except Exception:
        return None


def analyse_image(path: Path, args: argparse.Namespace, root: Path, thumbs: Path) -> tuple[str, dict[str, Any]]:
    if Image is None:
        return "Imagem catalogada; Pillow não está disponível para inspecionar pixels.", {"warning": "Pillow indisponível"}
    try:
        with Image.open(path) as img:
            width, height = img.size
            frames = getattr(img, "n_frames", 1)
            base = img.convert("RGB")
            stat = ImageStat.Stat(base) if ImageStat else None
            mean = [round(x, 2) for x in stat.mean] if stat else None
            extrema = base.getextrema()
            entropy = image_entropy(base)
            thumb_rel = None
            if args.thumbnails:
                thumbs.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha1(path.relative_to(root).as_posix().encode()).hexdigest()[:10]
                thumb = base.copy(); thumb.thumbnail((args.thumbnail_size, args.thumbnail_size))
                out = thumbs / f"{digest}_{path.stem[:60]}.jpg"; thumb.save(out, quality=85)
                thumb_rel = out.relative_to(args.output_dir_resolved).as_posix()
            info = {
                "width": width, "height": height, "mode": img.mode, "format": img.format,
                "frames": frames, "mean_rgb": mean, "extrema_rgb": extrema,
                "entropy_luma": round(entropy, 4) if entropy is not None else None,
                "thumbnail": thumb_rel,
            }
            text = [f"Dimensões: {width} × {height}", f"Formato/modo: {img.format} / {img.mode}", f"Frames: {frames}", f"Média RGB: {mean}", f"Entropia de luminância: {info['entropy_luma']}"]
            if thumb_rel:
                text += ["", f"Thumbnail local: {thumb_rel}", f"![{path.name}]({thumb_rel})"]
            text += ["", "Observação: a análise local registra metadados, propriedades visuais e thumbnail; não interpreta semanticamente eixos, legendas ou conclusões do gráfico."]
            return "\n".join(text), info
    except Exception as exc:
        return f"Falha ao inspecionar imagem: {exc!r}", {"error": repr(exc)}


def analyse_model(path: Path) -> tuple[str, dict[str, Any]]:
    info = {"extension": path.suffix.lower(), "bytes": path.stat().st_size, "sha256": sha256(path)}
    return "\n".join([f"Artefato binário de modelo: {path.suffix.lower()}", f"Tamanho: {human_bytes(path.stat().st_size)}", f"SHA-256: {info['sha256']}", "Conteúdo não desserializado por segurança e compatibilidade."]), info


def analyse_notebook(path: Path, args: argparse.Namespace, root: Path) -> tuple[str, dict[str, Any]]:
    try:
        nb = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return f"Falha ao ler notebook: {exc!r}", {"error": repr(exc)}
    records = []
    for i, cell in enumerate(nb.get("cells", []), 1):
        if cell.get("cell_type") != "code":
            continue
        outputs = cell.get("outputs", [])
        rendered = []
        for out in outputs:
            kind = out.get("output_type")
            if kind == "stream":
                rendered.append("".join(out.get("text", [])))
            elif kind == "error":
                rendered.append(f"ERRO {out.get('ename')}: {out.get('evalue')}\n" + "\n".join(out.get("traceback", [])))
            elif kind in {"execute_result", "display_data"}:
                data = out.get("data", {})
                if "text/plain" in data:
                    value = data["text/plain"]
                    rendered.append("".join(value) if isinstance(value, list) else str(value))
                rendered.extend(f"[saída não textual: {mime}]" for mime in data if mime != "text/plain")
        if rendered:
            records.append({"cell": i, "execution_count": cell.get("execution_count"), "outputs": rendered})
    info = {"cells": len(nb.get("cells", [])), "code_cells_with_outputs": len(records)}
    text = json.dumps(records, ensure_ascii=False, indent=2)
    if len(text) > args.max_text_chars:
        text = text[:args.max_text_chars] + "\n... [outputs omitidos]"
    return redact(text, root), info


def classify(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in TABLE_EXT: return "table"
    if ext in TEXT_EXT: return "text"
    if ext in STRUCTURED_EXT: return "structured"
    if ext in IMAGE_EXT: return "image"
    if ext in MODEL_EXT: return "model"
    if ext in NOTEBOOK_EXT: return "notebook"
    return "other"


def analyse(path: Path, args: argparse.Namespace, root: Path, thumbs: Path) -> tuple[str, dict[str, Any]]:
    kind = classify(path)
    if kind == "table": return analyse_table(path, args, root)
    if kind == "text": return read_text(path, args.max_text_chars, root)
    if kind == "structured": return analyse_structured(path, args, root)
    if kind == "image": return analyse_image(path, args, root, thumbs)
    if kind == "model": return analyse_model(path)
    if kind == "notebook": return analyse_notebook(path, args, root)
    return "Tipo não suportado.", {}


def markdown_fence(text: str) -> str:
    n = max([len(x) for x in re.findall(r"`+", text)] or [2]) + 1
    f = "`" * max(3, n)
    return f"{f}text\n{text}\n{f}"


def write_catalog(rows: list[dict[str, Any]], path: Path) -> None:
    fields = ["path", "kind", "extension", "bytes", "modified_utc", "sha256", "status"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for row in rows: w.writerow({k: row.get(k, "") for k in fields})


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compila resultados locais do projeto para análise por IA.")
    p.add_argument("--root", type=Path, default=Path.cwd(), help="Raiz do projeto; padrão: repositório Git atual.")
    p.add_argument("--output-dir", type=Path, default=Path(".local-analysis/results"), help="Pasta local dos arquivos compilados.")
    p.add_argument("--max-file-mb", type=float, default=50.0, help="Limite por arquivo textual/tabular; binários só são catalogados.")
    p.add_argument("--max-text-chars", type=int, default=120000)
    p.add_argument("--max-table-rows", type=int, default=200000)
    p.add_argument("--preview-rows", type=int, default=20)
    p.add_argument("--max-columns", type=int, default=200)
    p.add_argument("--top-values", type=int, default=12)
    p.add_argument("--max-structured-entries", type=int, default=5000)
    p.add_argument("--include-notebook-outputs", action="store_true", help="Inclui outputs textuais salvos em notebooks.")
    p.add_argument("--no-thumbnails", dest="thumbnails", action="store_false", help="Não gera thumbnails das imagens.")
    p.add_argument("--thumbnail-size", type=int, default=1400)
    p.add_argument("--fail-on-error", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root(args.root)
    output = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    output = output.resolve(); output.mkdir(parents=True, exist_ok=True)
    args.output_dir_resolved = output
    thumbs = output / "images"
    candidates = walk_candidates(root, args.include_notebook_outputs)
    max_bytes = int(args.max_file_mb * 1024 * 1024)
    rows: list[dict[str, Any]] = []
    sections: list[str] = []
    errors = 0
    print(f"[read_outputs] Raiz: {root}")
    print(f"[read_outputs] Resultados candidatos: {len(candidates)}")
    for idx, path in enumerate(candidates, 1):
        rel = path.relative_to(root).as_posix()
        stat = path.stat(); kind = classify(path)
        print(f"[read_outputs] {idx}/{len(candidates)} {rel}")
        row = {"path": rel, "kind": kind, "extension": path.suffix.lower(), "bytes": stat.st_size, "modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(), "sha256": sha256(path), "status": "ok"}
        if stat.st_size > max_bytes and kind in {"text", "table", "structured", "notebook"}:
            body, meta = f"Arquivo acima do limite de {args.max_file_mb:g} MB; somente metadados registrados.", {"skipped_large": True}
            row["status"] = "large_metadata_only"
        else:
            try:
                body, meta = analyse(path, args, root, thumbs)
                if "error" in meta:
                    row["status"] = "error"; errors += 1
            except Exception as exc:
                body, meta = f"Erro inesperado: {exc!r}", {"error": repr(exc)}; row["status"] = "error"; errors += 1
        row["analysis"] = meta; rows.append(row)
        sections += [f"## `{rel}`", "", f"- Tipo: `{kind}` · tamanho `{human_bytes(stat.st_size)}` · modificado `{row['modified_utc']}`", f"- SHA-256: `{row['sha256']}` · status `{row['status']}`", "", body if kind == "image" else markdown_fence(body), ""]
    counts = Counter(r["kind"] for r in rows)
    generated = utc_now()
    header = [
        "# Resultados compilados do projeto", "",
        "> Arquivo gerado localmente por `tools/read_outputs.py`. Não editar manualmente.",
        f"> Gerado em `{generated}` a partir de `{root.name}`.", "",
        "## Como interpretar", "",
        "- Este documento reúne evidências já produzidas. A ferramenta não recalcula modelos nem valida conclusões científicas.",
        "- Cada item mantém caminho, tamanho, data e SHA-256 para rastreabilidade.",
        "- Tabelas incluem prévia, tipos, missingness, estatísticas numéricas e valores categóricos frequentes.",
        "- Imagens incluem metadados, propriedades visuais simples e thumbnails; não há interpretação semântica automática de eixos ou conclusões.",
        "- Modelos binários são catalogados, mas não desserializados.",
        "- Resultados antigos ou provisórios continuam possíveis; a IA deve cruzar commit, manifesto, janela temporal e configuração.", "",
        "## Resumo", "",
        f"- Arquivos analisados: **{len(rows)}**", f"- Erros de leitura: **{errors}**",
        *[f"- {k}: **{v}**" for k, v in sorted(counts.items())], "",
        "## Catálogo", "",
        "| Caminho | Tipo | Tamanho | Status |", "|---|---:|---:|---|",
        *[f"| `{r['path']}` | {r['kind']} | {human_bytes(r['bytes'])} | {r['status']} |" for r in rows], "",
    ]
    md = "\n".join(header + sections).rstrip() + "\n"
    (output / "RESULTADOS_COMPILADOS.md").write_text(md, encoding="utf-8")
    (output / "RESULTADOS_COMPILADOS.json").write_text(json.dumps({"schema_version": 1, "generated_utc": generated, "root": "<REPO>", "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "pandas": getattr(pd, "__version__", None), "pillow": getattr(Image, "__version__", None) if Image else None}, "files": rows}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    write_catalog(rows, output / "RESULTADOS_CATALOGO.csv")
    print(f"[read_outputs] Markdown: {output / 'RESULTADOS_COMPILADOS.md'}")
    print(f"[read_outputs] JSON: {output / 'RESULTADOS_COMPILADOS.json'}")
    print(f"[read_outputs] Catálogo: {output / 'RESULTADOS_CATALOGO.csv'}")
    return 2 if args.fail_on_error and errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
