from __future__ import annotations

import argparse
import shutil
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


def clean_directories(dry_run: bool) -> None:
    for directory in DIRECTORIES_TO_CLEAN:
        path = PROJECT_ROOT / directory
        if path.exists():
            clean_directory_contents(path, dry_run)


def clean_pycache(dry_run: bool) -> None:
    for cache_dir in PROJECT_ROOT.rglob("__pycache__"):
        remove_directory(cache_dir, dry_run)


def clean_generated_files(dry_run: bool) -> None:
    for pattern in FILE_PATTERNS:
        for file_path in PROJECT_ROOT.rglob(pattern):
            if any(protected in str(file_path) for protected in PROTECTED_FOLDERS):
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
    args = parser.parse_args()

    clean_directories(args.dry_run)
    clean_pycache(args.dry_run)
    clean_generated_files(args.dry_run)

    if args.clean_processed:
        clean_processed_data(args.dry_run)

    if args.clean_reference:
        clean_reference(args.dry_run)

    print("\nLimpeza concluída.")


if __name__ == "__main__":
    main()