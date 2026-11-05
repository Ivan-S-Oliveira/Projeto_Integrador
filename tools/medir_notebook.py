"""Executa um notebook em processo isolado e mede tempo e pico de memória."""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

RAIZ = Path(__file__).resolve().parents[1]
TABELA = RAIZ / "outputs" / "final" / "performance_notebooks.csv"
CAMPOS = ["quando", "notebook", "duracao_s", "pico_rss_mb", "codigo_saida", "python", "limite_mb", "limite_s"]


def _rss_arvore_mb(proc: psutil.Process) -> float:
    """Soma o RSS do processo e de todos os filhos (o kernel do Jupyter é um filho)."""
    total = 0
    try:
        for p in [proc, *proc.children(recursive=True)]:
            try:
                total += p.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return total / 1_048_576


def medir_comando(comando: list[str], intervalo: float = 0.25) -> dict:
    """Roda `comando` e devolve duração, pico de RSS (MB, árvore de processos) e código de saída."""
    t0 = time.perf_counter()
    filho = subprocess.Popen(comando, cwd=RAIZ)
    proc, pico = psutil.Process(filho.pid), 0.0
    while filho.poll() is None:
        pico = max(pico, _rss_arvore_mb(proc))
        time.sleep(intervalo)
    return {
        "duracao_s": round(time.perf_counter() - t0, 1),
        "pico_rss_mb": round(pico),
        "codigo_saida": filho.returncode,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("notebook", type=Path)
    ap.add_argument("--salvar-no-lugar", action="store_true")
    ap.add_argument("--limite-mb", type=int, default=6144, help="pico aceitável de memória (padrão 6 GB)")
    ap.add_argument("--limite-s", type=int, default=1200, help="duração aceitável (padrão 20 min)")
    args = ap.parse_args()

    nb = args.notebook if args.notebook.is_absolute() else (RAIZ / args.notebook).resolve()
    if not nb.is_file():
        print(f"Notebook não encontrado: {nb}")
        return 1

    cmd = [sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute",
           "--ExecutePreprocessor.timeout=-1", str(nb)]
    if args.salvar_no_lugar:
        cmd.append("--inplace")
    else:
        saida = RAIZ / "outputs" / "notebooks"
        saida.mkdir(parents=True, exist_ok=True)
        cmd += ["--output", f"{nb.stem}_executado", "--output-dir", str(saida)]

    r = medir_comando(cmd)
    linha = {"quando": datetime.now().isoformat(timespec="seconds"), "notebook": nb.name, **r,
             "python": sys.version.split()[0], "limite_mb": args.limite_mb, "limite_s": args.limite_s}

    TABELA.parent.mkdir(parents=True, exist_ok=True)
    novo = not TABELA.exists()
    with TABELA.open("a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if novo:
            w.writeheader()
        w.writerow(linha)

    ok_mem, ok_t = r["pico_rss_mb"] <= args.limite_mb, r["duracao_s"] <= args.limite_s
    print(f"{nb.name}: {r['duracao_s']:.0f} s · pico {r['pico_rss_mb']:,} MB · saída {r['codigo_saida']} "
          f"· memória {'OK' if ok_mem else 'ACIMA DO LIMITE'} · tempo {'OK' if ok_t else 'ACIMA DO LIMITE'}")
    return 0 if r["codigo_saida"] == 0 and ok_mem else 2


if __name__ == "__main__":
    sys.exit(main())
