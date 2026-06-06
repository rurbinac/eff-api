#!/usr/bin/env python3
"""Local script to load F42 OPTA feeds from a folder into the database."""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.database import engine
from app.services.f42_loader import F42Loader


def load_f42_folder(folder_path: str, pattern: str = "f42-*.xml") -> None:
    """Load all F42 files from a folder.

    Args:
        folder_path: Path to folder containing F42 XML files
        pattern: File pattern to match (default: f42-*.xml)
    """
    folder = Path(folder_path)
    if not folder.exists():
        print(f"[ERROR] Folder not found: {folder_path}")
        return

    # Find matching files
    files = sorted(folder.glob(pattern))
    if not files:
        print(f"[WARN] No files matching pattern '{pattern}' in {folder_path}")
        return

    print(f"[INFO] Found {len(files)} F42 files to process\n")

    with Session(engine) as db:
        for file_path in files:
            print(f"Processing: {file_path.name}")
            print("=" * 60)

            try:
                stats = F42Loader.load_file(db, str(file_path))

                print(f"  Competitions: {stats['competitions_inserted']} inserted, {stats['competitions_updated']} updated")
                print(f"  Teams:        {stats['teams_inserted']} inserted, {stats['teams_updated']} updated")
                print(f"  Players:      {stats['players_inserted']} inserted, {stats['players_updated']} updated")
                print(f"  Matches:      {stats['matches_inserted']} inserted, {stats['matches_updated']} updated")

                if stats['errors']:
                    print(f"\n  Errors:")
                    for error in stats['errors']:
                        print(f"    - {error}")

                print()

            except Exception as e:
                print(f"  [ERROR] Failed to load file: {str(e)}\n")
                import traceback
                traceback.print_exc()

    print("Done!")


if __name__ == "__main__":
    # Default to the feeds folder
    feeds_folder = project_root / "feeds" / "opta"

    if len(sys.argv) > 1:
        feeds_folder = sys.argv[1]

    print(f"Loading F42 feeds from: {feeds_folder}\n")
    load_f42_folder(str(feeds_folder))
