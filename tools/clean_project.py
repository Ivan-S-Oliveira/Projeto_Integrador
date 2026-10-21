from __future__ import annotations

import argparse
import gc
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES_TO_CLEAN = [
    "outputs",
    "reports",
    "models",
    "logs",
    ".pytest_cache",
    ".ipynb_checkpoints",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
]

FILE_PATTERNS = [
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg",
    "*.log", "*.tmp",
    "*.joblib", "*.pkl", "*.pickle",
    "*.h5", "*.hdf5",
    "*.pt", "*.pth", "*.onnx",
    "*.npy", "*.npz",
]

# Pastas e caminhos (relativos a PROJECT_ROOT) que NUNCA devem ser limpos.
PROTECTED_FOLDERS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "notebooks",
    "src",
    "tests",
    "tools",
    "configs",
    "docs",
    "data/raw",
    "data/analytical",
    "data/external",
}

# Caches seguros de remover. NÃO incluímos ~/.local/share/jupyter porque lá ficam
# os ficheiros de conexão dos kernels ativos (mexer nisso derruba o JupyterLab).
JUPYTER_CACHE_DIRS = [
    Path.home() / ".cache" / "jupyter",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_protected(path: Path) -> bool:
    """Devolve True se `path` estiver dentro de algo em PROTECTED_FOLDERS.

    Usa comparação por componentes de caminho (não substring), para evitar
    falsos positivos como `source_output.png` casar com `src`, ou `.venv`
    ser apagado por engano.
    """
    try:
        rel = path.resolve().relative_to(PROJECT_ROOT)
    except ValueError:
        # Fora do projeto — não tocar.
        return True

    parts = set(rel.parts)
    for protected in PROTECTED_FOLDERS:
        if "/" in protected:
            protected_path = Path(protected)
            if rel == protected_path or protected_path in rel.parents:
                return True
        else:
            if protected in parts:
                return True
    return False


def remove_file(path: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"[DRY RUN] FILE  {path}")
        return
    path.unlink(missing_ok=True)
    print(f"[REMOVED] FILE  {path}")


def remove_directory(path: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"[DRY RUN] DIR   {path}")
        return
    shutil.rmtree(path, ignore_errors=True)
    print(f"[REMOVED] DIR   {path}")


def clean_directory_contents(path: Path, dry_run: bool) -> None:
    """Remove conteúdo mas preserva o diretório e os .gitkeep."""
    if not path.exists():
        return
    for child in path.iterdir():
        if child.name == ".gitkeep":
            continue
        if child.is_dir():
            remove_directory(child, dry_run)
        else:
            remove_file(child, dry_run)


# ---------------------------------------------------------------------------
# Limpeza de artefactos
# ---------------------------------------------------------------------------

def clean_directories(dry_run: bool) -> None:
    for directory in DIRECTORIES_TO_CLEAN:
        path = PROJECT_ROOT / directory
        if path.exists():
            clean_directory_contents(path, dry_run)


def clean_pycache(dry_run: bool) -> None:
    """Remove __pycache__ do projeto, exceto dentro de pastas protegidas (.venv etc.)."""
    for cache_dir in PROJECT_ROOT.rglob("__pycache__"):
        if _is_protected(cache_dir):
            continue
        remove_directory(cache_dir, dry_run)


def clean_generated_files(dry_run: bool) -> None:
    for pattern in FILE_PATTERNS:
        for file_path in PROJECT_ROOT.rglob(pattern):
            if _is_protected(file_path):
                continue
            remove_file(file_path, dry_run)


def clean_processed_data(dry_run: bool) -> None:
    processed_folder = PROJECT_ROOT / "data" / "processed"
    if processed_folder.exists():
        clean_directory_contents(processed_folder, dry_run)


def clean_reference(dry_run: bool) -> None:
    for name in ("PROJECT_COMPLETE_REFERENCE.md", "PROJECT_COMPLETE_REFERENCE.json"):
        path = PROJECT_ROOT / "docs" / name
        if path.exists():
            remove_file(path, dry_run)


def clean_jupyter_cache(dry_run: bool) -> None:
    """Limpa caches do Jupyter (só ~/.cache/jupyter; não afeta kernels ativos)."""
    for cache_dir in JUPYTER_CACHE_DIRS:
        if cache_dir.exists():
            clean_directory_contents(cache_dir, dry_run)


# ---------------------------------------------------------------------------
# Memória
# ---------------------------------------------------------------------------

def clean_memory(dry_run: bool) -> None:
    """Força gc.collect() e, em Linux/glibc, devolve páginas livres ao SO.

    Nota: só afeta o processo atual. Para libertar RAM de um script pesado,
    importe esta função no final do script:
        from tools.clean_project import clean_memory
        clean_memory(dry_run=False)
    """
    if dry_run:
        print("[DRY RUN] MEMORY  (gc.collect + malloc_trim)")
        return

    collected = gc.collect()
    trimmed = "n/a"
    if sys.platform.startswith("linux"):
        try:
            import ctypes

            libc = ctypes.CDLL("libc.so.6")
            trimmed = "ok" if libc.malloc_trim(0) else "noop"
        except Exception:
            trimmed = "n/a"

    print(f"[CLEANED] MEMORY  (gc objetos={collected}, malloc_trim={trimmed})")


def diagnose_memory() -> None:
    """Lista processos Python/Jupyter em execução e o RSS de cada um (Linux)."""
    proc_root = Path("/proc")
    if not proc_root.exists():
        print("[DIAGNOSE] /proc não disponível (este relatório é Linux-only).")
        return

    rows: list[tuple[int, int, str]] = []
    for pid_dir in proc_root.iterdir():
        if not pid_dir.name.isdigit():
            continue
        try:
            cmdline_raw = (pid_dir / "cmdline").read_bytes()
            cmdline = cmdline_raw.replace(b"\0", b" ").decode("utf-8", "ignore").strip()
            if not cmdline:
                continue

            low = cmdline.lower()
            if "python" not in low and "jupyter" not in low:
                continue

            status = (pid_dir / "status").read_text(errors="ignore")
            rss_kb = 0
            for line in status.splitlines():
                if line.startswith("VmRSS:"):
                    rss_kb = int(line.split()[1])
                    break

            rows.append((rss_kb, int(pid_dir.name), cmdline[:140]))
        except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
            continue

    if not rows:
        print("[DIAGNOSE] Nenhum processo Python/Jupyter encontrado.")
        return

    rows.sort(reverse=True)
    total = sum(r[0] for r in rows)
    print(f"[DIAGNOSE] Top processos Python/Jupyter (RSS total ≈ {total / 1024:.1f} MiB):")
    for rss_kb, pid, cmdline in rows[:15]:
        print(f"  {rss_kb / 1024:8.1f} MiB  pid={pid:<7}  {cmdline}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Limpa artefactos gerados sem tocar em código, configs ou dados originais."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostra o que seria removido sem apagar.")
    parser.add_argument("--clean-processed", action="store_true",
                        help="Remove data/processed (obriga a re-download do Parquet).")
    parser.add_argument("--clean-reference", action="store_true",
                        help="Remove docs/PROJECT_COMPLETE_REFERENCE.{md,json}.")
    parser.add_argument("--clean-jupyter-cache", action="store_true",
                        help="Remove ~/.cache/jupyter (não afeta kernels ativos).")
    parser.add_argument("--clean-memory", action="store_true",
                        help="Força gc.collect() + malloc_trim() no processo atual.")
    parser.add_argument("--diagnose-memory", action="store_true",
                        help="Lista processos Python/Jupyter e o RSS de cada um.")
    args = parser.parse_args()

    if args.diagnose_memory:
        diagnose_memory()
        return

    clean_directories(args.dry_run)
    clean_pycache(args.dry_run)
    clean_generated_files(args.dry_run)

    if args.clean_processed:
        clean_processed_data(args.dry_run)

    if args.clean_reference:
        clean_reference(args.dry_run)

    if args.clean_jupyter_cache:
        clean_jupyter_cache(args.dry_run)

    if args.clean_memory:
        clean_memory(args.dry_run)

    print("\nLimpeza concluída.")


if __name__ == "__main__":
    main()