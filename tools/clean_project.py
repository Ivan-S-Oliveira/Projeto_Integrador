from __future__ import annotations

import argparse
import gc
import os
import shutil
import subprocess
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
# O mesmo se aplica no Windows a %LOCALAPPDATA%\Jupyter\runtime — não tocar.
JUPYTER_CACHE_DIRS = [
    Path.home() / ".cache" / "jupyter",
]

IS_WINDOWS = sys.platform.startswith("win")


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
# Caches do sistema (Windows)
# ---------------------------------------------------------------------------

def _require_windows(feature: str) -> bool:
    if not IS_WINDOWS:
        print(f"[SKIP] {feature}: apenas disponível no Windows.")
        return False
    return True


def flush_dns(dry_run: bool) -> None:
    """Limpa o cache de DNS do Windows com `ipconfig /flushdns`.

    Útil quando há problemas de conectividade ou o browser resolve IPs antigos.
    """
    if not _require_windows("flush DNS"):
        return
    if dry_run:
        print("[DRY RUN] CMD   ipconfig /flushdns")
        return
    try:
        result = subprocess.run(
            ["ipconfig", "/flushdns"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("[WARN] DNS: ipconfig não encontrado.")
        return
    if result.returncode == 0:
        print("[CLEANED] DNS   cache de DNS limpo")
    else:
        print(f"[WARN] DNS: ipconfig devolveu código {result.returncode}")
        if result.stdout.strip():
            print(result.stdout.strip())


def clean_windows_temp(dry_run: bool) -> None:
    """Remove o conteúdo de %TEMP% do utilizador, ignorando ficheiros em uso.

    Substitui o `del /q /s %TEMP%\\*` do CMD por uma versão em Python que:
      * não segue symlinks (apaga só o link);
      * ignora silenciosamente ficheiros bloqueados por outros processos.
    """
    if not _require_windows("clean TEMP"):
        return

    temp_env = os.environ.get("TEMP") or os.environ.get("TMP")
    if not temp_env:
        print("[SKIP] TEMP: variável de ambiente TEMP/TMP não definida.")
        return

    temp_path = Path(temp_env)
    if not temp_path.exists():
        print(f"[SKIP] TEMP: {temp_path} não existe.")
        return

    removed = 0
    skipped = 0
    for child in temp_path.iterdir():
        if dry_run:
            print(f"[DRY RUN] TEMP  {child}")
            removed += 1
            continue

        try:
            if child.is_symlink():
                child.unlink(missing_ok=True)
            elif child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
            removed += 1
        except (PermissionError, OSError):
            # Ficheiro/diretório em uso — normal, ignorar.
            skipped += 1

    if not dry_run:
        msg = f"[CLEANED] TEMP  {temp_path} (removidos={removed}"
        if skipped:
            msg += f", em uso/ignorados={skipped}"
        msg += ")"
        print(msg)


def _pip_cache_dir() -> Path | None:
    """Descobre a pasta de cache do pip (via `pip cache dir` com fallback)."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "cache", "dir"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except FileNotFoundError:
        pass

    if sys.platform.startswith("win"):
        return Path.home() / "AppData" / "Local" / "pip" / "Cache"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "pip"
    return Path.home() / ".cache" / "pip"


def clean_pip_cache(dry_run: bool) -> None:
    """Limpa o cache de wheels/HTTP do pip.

    Usa o comando oficial `pip cache purge`; se falhar, apaga manualmente
    a pasta devolvida por `pip cache dir` (preservando o diretório em si).
    """
    if dry_run:
        print("[DRY RUN] CMD   pip cache purge")
        return

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "cache", "purge"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print("[CLEANED] PIP   cache do pip limpo (pip cache purge)")
            return
        print(f"[WARN] PIP: 'pip cache purge' falhou (código {result.returncode}); "
              "a tentar apagar a pasta manualmente.")
    except FileNotFoundError:
        print("[WARN] PIP: pip não encontrado; a tentar apagar a pasta manualmente.")

    cache_dir = _pip_cache_dir()
    if cache_dir is None or not cache_dir.exists():
        print("[SKIP] PIP: pasta de cache não encontrada.")
        return
    clean_directory_contents(cache_dir, dry_run=False)
    print(f"[CLEANED] PIP   {cache_dir}")


def clean_windows_caches(dry_run: bool) -> None:
    """Agrega os caches de sistema do Windows: DNS + TEMP + pip."""
    if not _require_windows("clean Windows caches"):
        # Ainda assim limpamos o cache do pip (é cross-platform).
        clean_pip_cache(dry_run)
        return
    flush_dns(dry_run)
    clean_windows_temp(dry_run)
    clean_pip_cache(dry_run)


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

    # --- Caches do sistema (Windows) ---
    parser.add_argument("--flush-dns", action="store_true",
                        help="[Windows] Executa `ipconfig /flushdns`.")
    parser.add_argument("--clean-temp", action="store_true",
                        help="[Windows] Remove o conteúdo de %%TEMP%% (ignora ficheiros em uso).")
    parser.add_argument("--clean-pip-cache", action="store_true",
                        help="Limpa o cache do pip (`pip cache purge`).")
    parser.add_argument("--clean-windows-caches", action="store_true",
                        help="Agrega --flush-dns, --clean-temp e --clean-pip-cache.")

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

    # --- Caches do sistema ---
    if args.clean_windows_caches:
        clean_windows_caches(args.dry_run)
    else:
        if args.flush_dns:
            flush_dns(args.dry_run)
        if args.clean_temp:
            clean_windows_temp(args.dry_run)
        if args.clean_pip_cache:
            clean_pip_cache(args.dry_run)

    if args.clean_memory:
        clean_memory(args.dry_run)

    print("\nLimpeza concluída.")


if __name__ == "__main__":
    main()