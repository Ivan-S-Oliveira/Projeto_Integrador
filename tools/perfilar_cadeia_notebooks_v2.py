#!/usr/bin/env python3
"""Executa uma cadeia de notebooks sequencialmente e perfila tempo e RAM por célula."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import queue
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

import psutil
from jupyter_client import KernelManager

MB = 1024 * 1024
GB = 1024 * 1024 * 1024
DEFAULT_NOTEBOOKS = [
    "notebooks/00_acesso_dados_parquet.ipynb",
    "notebooks/01_extracao.ipynb",
    "notebooks/A/A_03_coorte_protocolo.ipynb",
    "notebooks/B/B_02_eda_primeira_passagem.ipynb",
    "notebooks/B/B_04_eda_temporal_clustering.ipynb",
    "notebooks/B/B_05_supervisionado_pilotos.ipynb",
    "notebooks/C/C_11_pipeline_supervisionado.ipynb",
    "notebooks/C/C_12_baseline_logistica.ipynb",
    "notebooks/C/C_14_ablacoes_variaveis.ipynb",
    "notebooks/C/C_13_boosting.ipynb",
    "notebooks/C/C_15_calibracao_limiar.ipynb",
]


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def process_tree_rss_mb(pid: int) -> float:
    total = 0
    try:
        root = psutil.Process(pid)
        processes = [root, *root.children(recursive=True)]
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0.0
    for proc in processes:
        try:
            total += proc.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return total / MB


def system_used_mb() -> float:
    vm = psutil.virtual_memory()
    return (vm.total - vm.available) / MB


def reserve_gb(peak_mb: float, headroom: float, quantum_gb: float) -> float:
    raw = peak_mb / 1024 * (1 + headroom)
    return math.ceil(raw / quantum_gb) * quantum_gb


def cell_summary(source: str, limit: int = 110) -> str:
    for line in source.splitlines():
        text = line.strip()
        if text and not text.startswith("#"):
            return text[:limit]
    return ""


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class Sampler(threading.Thread):
    def __init__(self, pid: int, interval: float, chain_samples: list[dict], notebook: str):
        super().__init__(daemon=True)
        self.pid = pid
        self.interval = interval
        self.chain_samples = chain_samples
        self.notebook = notebook
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.cell_peak_mb = 0.0
        self.notebook_peak_mb = 0.0
        self.current_mb = 0.0

    def reset_cell(self):
        value = process_tree_rss_mb(self.pid)
        with self.lock:
            self.current_mb = value
            self.cell_peak_mb = value
        return value

    def snapshot(self):
        with self.lock:
            return self.current_mb, self.cell_peak_mb, self.notebook_peak_mb

    def run(self):
        while not self.stop_event.is_set():
            value = process_tree_rss_mb(self.pid)
            used = system_used_mb()
            stamp = time.time()
            with self.lock:
                self.current_mb = value
                self.cell_peak_mb = max(self.cell_peak_mb, value)
                self.notebook_peak_mb = max(self.notebook_peak_mb, value)
            self.chain_samples.append({
                "timestamp_epoch": round(stamp, 3), "quando": now_iso(),
                "notebook": self.notebook, "rss_arvore_mb": round(value, 1),
                "ram_sistema_usada_mb": round(used, 1),
            })
            self.stop_event.wait(self.interval)


def execute_cell(km, kc, code: str, timeout_s: int | None):
    msg_id = kc.execute(code, store_history=True, allow_stdin=False, stop_on_error=True)
    error = None
    deadline = None if timeout_s is None else time.monotonic() + timeout_s
    while True:
        if deadline is not None and time.monotonic() > deadline:
            km.interrupt_kernel()
            return "TimeoutError: célula excedeu o limite"
        try:
            msg = kc.get_iopub_msg(timeout=2)
        except queue.Empty:
            if not km.is_alive():
                return "KernelDied: kernel encerrou, possível falta de memória"
            continue
        if msg.get("parent_header", {}).get("msg_id") != msg_id:
            continue
        msg_type = msg.get("msg_type")
        if msg_type == "error":
            content = msg.get("content", {})
            error = f"{content.get('ename')}: {content.get('evalue')}"
        if msg_type == "status" and msg.get("content", {}).get("execution_state") == "idle":
            break
    return error


def profile_notebook(path: Path, root: Path, interval: float, timeout_s: int | None,
                     headroom: float, quantum_gb: float, chain_samples: list[dict]):
    notebook = json.loads(path.read_text(encoding="utf-8"))
    cells = notebook.get("cells", [])
    kernel_name = notebook.get("metadata", {}).get("kernelspec", {}).get("name", "python3")
    km = KernelManager(kernel_name=kernel_name)
    notebook_started = time.perf_counter()
    rows = []
    status = "ok"
    error_text = ""
    km.start_kernel(cwd=str(root))
    kc = km.client()
    kc.start_channels()
    try:
        kc.wait_for_ready(timeout=120)
        pid = km.provisioner.pid
        sampler = Sampler(pid, interval, chain_samples, path.as_posix())
        sampler.start()
        try:
            for number, cell in enumerate(cells, start=1):
                if cell.get("cell_type") != "code":
                    continue
                source = cell.get("source", "")
                code = "".join(source) if isinstance(source, list) else source
                if not code.strip():
                    continue
                before = sampler.reset_cell()
                sys_before = system_used_mb()
                started = time.perf_counter()
                error = execute_cell(km, kc, code, timeout_s)
                duration = time.perf_counter() - started
                time.sleep(interval * 1.2)
                after, peak, _ = sampler.snapshot()
                sys_after = system_used_mb()
                row = {
                    "notebook": path.as_posix(), "celula": number,
                    "resumo": cell_summary(code), "status": "erro" if error else "ok",
                    "erro": error or "", "duracao_s": round(duration, 3),
                    "rss_antes_mb": round(before, 1), "rss_depois_mb": round(after, 1),
                    "rss_pico_mb": round(peak, 1), "subida_pico_mb": round(peak - before, 1),
                    "delta_retido_mb": round(after - before, 1),
                    "ram_sistema_antes_mb": round(sys_before, 1),
                    "ram_sistema_depois_mb": round(sys_after, 1),
                }
                rows.append(row)
                print(f"  célula {number:>3}: {duration:8.1f}s | pico {peak:9.1f} MB | {row['status']}", flush=True)
                if error:
                    status, error_text = "erro", error
                    break
        finally:
            sampler.stop_event.set()
            sampler.join(timeout=5)
            _, _, notebook_peak = sampler.snapshot()
    except BaseException as exc:
        status = "erro"
        error_text = f"{type(exc).__name__}: {exc}"
        notebook_peak = max((r["rss_pico_mb"] for r in rows), default=0.0)
        traceback.print_exc()
    finally:
        try:
            kc.stop_channels()
        except Exception:
            pass
        try:
            km.shutdown_kernel(now=True)
        except Exception:
            pass
    duration = time.perf_counter() - notebook_started
    summary = {
        "notebook": path.as_posix(), "status": status, "erro": error_text,
        "duracao_s": round(duration, 3), "celulas_executadas": len(rows),
        "pico_rss_mb": round(notebook_peak, 1),
        "reserva_recomendada_gb": reserve_gb(notebook_peak, headroom, quantum_gb),
        "maior_subida_celula_mb": round(max((r["subida_pico_mb"] for r in rows), default=0), 1),
    }
    return rows, summary


def markdown_report(summaries, cells, chain, args, machine):
    ok = [s for s in summaries if s["status"] == "ok"]
    peak = max((s["pico_rss_mb"] for s in summaries), default=0)
    chain_reserve = reserve_gb(peak, args.headroom, args.quantum_gb)
    top_cells = sorted(cells, key=lambda r: r["rss_pico_mb"], reverse=True)[:20]
    lines = [
        "# Perfil de tempo e memória da cadeia de notebooks", "",
        f"Gerado em: {now_iso()}", "",
        "## Critério de reserva", "",
        f"Reserva = pico RSS medido × (1 + {args.headroom:.0%} de folga), arredondada para {args.quantum_gb:g} GB.",
        "Como a execução é sequencial e cada kernel é encerrado, a reserva da cadeia é baseada no maior pico, não na soma dos picos.", "",
        f"- RAM física: {machine['ram_total_gb']:.1f} GB",
        f"- Maior pico da cadeia: {peak/1024:.2f} GB",
        f"- Reserva recomendada da cadeia: {chain_reserve:.1f} GB",
        f"- Notebooks concluídos: {len(ok)}/{len(summaries)}", "",
        "## Por notebook", "",
        "| Notebook | Status | Tempo (min) | Pico (GB) | Reserva (GB) |",
        "|---|---:|---:|---:|---:|",
    ]
    for s in summaries:
        lines.append(f"| {s['notebook']} | {s['status']} | {s['duracao_s']/60:.2f} | {s['pico_rss_mb']/1024:.2f} | {s['reserva_recomendada_gb']:.1f} |")
    lines += ["", "## Células com maior pico absoluto", "", "| Notebook | Célula | Pico (GB) | Subida (GB) | Tempo (s) | Resumo |", "|---|---:|---:|---:|---:|---|"]
    for r in top_cells:
        safe = r["resumo"].replace("|", "\\|")
        lines.append(f"| {r['notebook']} | {r['celula']} | {r['rss_pico_mb']/1024:.2f} | {r['subida_pico_mb']/1024:.2f} | {r['duracao_s']:.1f} | {safe} |")
    lines += ["", "## Interpretação", "",
              "- `subida_pico_mb` identifica a célula que aloca memória adicional.",
              "- `delta_retido_mb` positivo indica memória que permaneceu no kernel após a célula.",
              "- Pico alto com subida baixa costuma indicar acúmulo de objetos de células anteriores.",
              "- Compare as células líderes com leituras de Parquet sem projeção, cópias de DataFrame, one-hot denso, conversões para NumPy e buscas paralelas."]
    return "\n".join(lines) + "\n", chain_reserve


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebooks", nargs="*", help="ordem explícita; usa a cadeia padrão se omitido")
    parser.add_argument("--saida", type=Path, default=Path("outputs/final/perfil_cadeia"))
    parser.add_argument("--intervalo", type=float, default=0.2)
    parser.add_argument("--timeout-celula-s", type=int, default=0, help="0 = sem limite")
    parser.add_argument("--headroom", type=float, default=0.25, help="folga da reserva; padrão 25%%")
    parser.add_argument("--quantum-gb", type=float, default=0.5)
    parser.add_argument("--continuar-em-erro", action="store_true")
    args = parser.parse_args()
    if not 0 <= args.headroom <= 2:
        parser.error("--headroom deve ficar entre 0 e 2")
    if args.intervalo <= 0 or args.quantum_gb <= 0:
        parser.error("intervalo e quantum devem ser positivos")
    root = Path.cwd().resolve()
    requested = args.notebooks or DEFAULT_NOTEBOOKS
    paths = [(root / item).resolve() for item in requested]
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        parser.error("notebooks não encontrados:\n" + "\n".join(missing))
    args.saida = (root / args.saida).resolve()
    args.saida.mkdir(parents=True, exist_ok=True)
    machine = {"ram_total_gb": psutil.virtual_memory().total / GB, "cpu_logicos": psutil.cpu_count()}
    all_cells, summaries, chain_samples = [], [], []
    started = time.perf_counter()
    for index, path in enumerate(paths, start=1):
        rel = path.relative_to(root)
        print(f"[{index}/{len(paths)}] {rel}", flush=True)
        rows, summary = profile_notebook(path, root, args.intervalo,
                                         None if args.timeout_celula_s == 0 else args.timeout_celula_s,
                                         args.headroom, args.quantum_gb, chain_samples)
        all_cells.extend(rows)
        summaries.append(summary)
        write_csv(args.saida / f"celulas_{path.stem}.csv", rows)
        if summary["status"] != "ok" and not args.continuar_em_erro:
            break
    write_csv(args.saida / "notebooks.csv", summaries)
    write_csv(args.saida / "celulas_todas.csv", all_cells)
    write_csv(args.saida / "amostras_cadeia.csv", chain_samples)
    report, chain_reserve = markdown_report(summaries, all_cells, chain_samples, args, machine)
    (args.saida / "relatorio_memoria.md").write_text(report, encoding="utf-8")
    payload = {
        "quando": now_iso(), "maquina": machine, "duracao_total_s": round(time.perf_counter()-started, 3),
        "headroom": args.headroom, "reserva_cadeia_gb": chain_reserve,
        "notebooks": summaries,
    }
    (args.saida / "resumo.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRelatório: {args.saida / 'relatorio_memoria.md'}")
    print(f"Reserva recomendada para a cadeia sequencial: {chain_reserve:.1f} GB")
    return 0 if summaries and all(s["status"] == "ok" for s in summaries) and len(summaries) == len(paths) else 2


if __name__ == "__main__":
    raise SystemExit(main())
