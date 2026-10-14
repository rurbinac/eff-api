#!/usr/bin/env python3
"""Local script to load F42 OPTA feeds from a folder into the database."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.database import create_db_and_tables, engine
from app.services.f_loader import FLoader


def load_f42_folder(folder_path: str, pattern: str = "f42-*.xml") -> None:
    folder = Path(folder_path)
    if not folder.exists():
        print(f"[ERROR] Folder not found: {folder_path}")
        return

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
                content = file_path.read_bytes()
                process = FLoader.log_feed_start(db, file_path.name, content, force=True)
                if process is None:
                    print("  Skipped (identical content)\n")
                    continue

                process = FLoader.load_file(db, process, str(file_path))

                print(f"  Process ID: {process.process_id}")
                print(f"  Duration:   {process.duration:.3f}s" if process.duration else "  Duration:   —")
                if process.tasks:
                    for task in process.tasks:
                        t = task if isinstance(task, dict) else task.to_dict()
                        status = t.get("status", "?")
                        name = t.get("name", "?")
                        info = t.get("info", {})
                        errors = t.get("errors", [])
                        info_str = ", ".join(f"{k}={v}" for k, v in info.items() if v is not None)
                        print(f"  [{status}] {name}" + (f" — {info_str}" if info_str else ""))
                        for err in errors:
                            print(f"    ERROR: {err}")
                print()

            except Exception as e:
                print(f"  [ERROR] Failed to load file: {e}\n")
                import traceback
                traceback.print_exc()

    print("Done!")


if __name__ == "__main__":
    feeds_folder = project_root / "feeds" / "opta"

    if len(sys.argv) > 1:
        feeds_folder = sys.argv[1]

    print("Ensuring all tables exist...")
    create_db_and_tables()

    print(f"Loading F42 feeds from: {feeds_folder}\n")
    load_f42_folder(str(feeds_folder))
