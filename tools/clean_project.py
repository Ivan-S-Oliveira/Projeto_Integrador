from __future__ import annotations

import argparse
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES_TO_CLEAN = [
    "outputs",
    "reports",
    "models",
    ".pytest_cache",
    ".ipynb_checkpoints",
]

FILE_PATTERNS = [
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.svg",
    "*.log",
    "*.tmp",
    "*.joblib",
    "*.pkl",
]

PROTECTED_FOLDERS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "notebooks",
    "src",
    "tests",
    "configs",
    "data/raw",
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


def clean_directories(dry_run: bool) -> None:
    for directory in DIRECTORIES_TO_CLEAN:
        path = PROJECT_ROOT / directory

        if path.exists():
            remove_directory(path, dry_run)


def clean_pycache(dry_run: bool) -> None:
    for cache_dir in PROJECT_ROOT.rglob("__pycache__"):
        remove_directory(cache_dir, dry_run)


def clean_generated_files(dry_run: bool) -> None:
    for pattern in FILE_PATTERNS:
        for file_path in PROJECT_ROOT.rglob(pattern):

            skip = any(
                protected in str(file_path)
                for protected in PROTECTED_FOLDERS
            )

            if skip:
                continue

            remove_file(file_path, dry_run)


def clean_processed_data(dry_run: bool) -> None:
    processed_folder = PROJECT_ROOT / "data" / "processed"

    if processed_folder.exists():
        remove_directory(processed_folder, dry_run)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra o que será removido sem apagar arquivos.",
    )

    parser.add_argument(
        "--keep-processed",
        action="store_true",
        help="Mantém data/processed.",
    )

    args = parser.parse_args()

    clean_directories(args.dry_run)
    clean_pycache(args.dry_run)
    clean_generated_files(args.dry_run)

    if not args.keep_processed:
        clean_processed_data(args.dry_run)

    print("\nLimpeza concluída.")


if __name__ == "__main__":
    main()