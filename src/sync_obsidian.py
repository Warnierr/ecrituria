"""
Synchronisation des fichiers Obsidian vers data/<projet>

Usage:
    python -m src.sync_obsidian --vault "C:/Users/User/Documents/Ecrituria" --project anomalie2084
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Iterable

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_VAULT = Path.home() / "Documents" / "Ecrituria"
VALID_EXTENSIONS = {".md", ".txt"}


def iter_files(source_root: Path) -> Iterable[Path]:
    for path in source_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS:
            yield path


def sync_obsidian(vault_root: Path, project: str, mode: str = "merge", dry_run: bool = False) -> None:
    source_dir = vault_root / project
    target_dir = DATA_DIR / project

    if not source_dir.exists():
        raise FileNotFoundError(
            f"Le dossier source Obsidian n'existe pas: {source_dir}\n"
            "Vérifiez le chemin du vault (--vault) et le nom du projet (--project)."
        )

    print("=" * 70)
    print(f"🔄 Synchronisation Obsidian → data/{project}")
    print("=" * 70)
    print(f"📁 Source : {source_dir}")
    print(f"📁 Cible  : {target_dir}")
    print(f"⚙️  Mode   : {mode}  |  Dry-run: {dry_run}")
    print()

    if mode == "replace" and target_dir.exists() and not dry_run:
        print("🧹 Suppression de l'ancien contenu cible...")
        shutil.rmtree(target_dir)

    copied = 0
    skipped = 0

    for file_path in iter_files(source_dir):
        rel_path = file_path.relative_to(source_dir)
        dest_path = target_dir / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if dry_run:
            print(f"[DRY-RUN] Copier {rel_path}")
            copied += 1
            continue

        shutil.copy2(file_path, dest_path)
        copied += 1

    if copied == 0:
        print("⚠️  Aucun fichier .md ou .txt trouvé à copier.")
    else:
        print(f"✅ {copied} fichiers copiés depuis Obsidian.")

    if skipped:
        print(f"ℹ️  Fichiers ignorés (extension non supportée) : {skipped}")

    print("\n📌 Étape suivante : reconstruisez l'index vectoriel :")
    print(f"    python -m src.indexer {project}")
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synchronise un vault Obsidian vers data/<projet>.")
    parser.add_argument(
        "--vault",
        type=Path,
        default=DEFAULT_VAULT,
        help=f"Chemin du vault Obsidian (défaut: {DEFAULT_VAULT})",
    )
    parser.add_argument(
        "--project",
        type=str,
        default="anomalie2084",
        help="Nom du projet (dossier dans data/ et dans le vault)",
    )
    parser.add_argument(
        "--mode",
        choices=("merge", "replace"),
        default="merge",
        help="merge: remplace fichier par fichier (défaut) | replace: supprime le dossier cible avant copie",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simule la synchronisation sans copier de fichiers",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sync_obsidian(
        vault_root=args.vault,
        project=args.project,
        mode=args.mode,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()

