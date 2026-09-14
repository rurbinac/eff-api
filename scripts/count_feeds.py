"""Recursively count XML files in each subfolder of the feeds directory.

Usage:
    python scripts/count_feeds.py [--feeds-dir PATH]
"""

import argparse
from pathlib import Path


def count_feeds(feeds_dir: Path) -> None:
    # Collect (folder, count) for every directory that contains files
    rows: list[tuple[Path, int]] = []

    for folder in sorted(feeds_dir.rglob("*")):
        if not folder.is_dir():
            continue
        count = sum(1 for f in folder.iterdir() if f.is_file())
        if count:
            rows.append((folder, count))

    # Also count files directly in feeds_dir (not in subfolders)
    root_count = sum(1 for f in feeds_dir.iterdir() if f.is_file())
    if root_count:
        rows.insert(0, (feeds_dir, root_count))

    if not rows:
        print("No files found under", feeds_dir)
        return

    # Format: align counts right, show relative path
    max_count_width = max(len(str(count)) for _, count in rows)
    total = sum(count for _, count in rows)

    print(f"{'Count':>{max_count_width}}  Path")
    print("-" * (max_count_width + 2 + 60))
    for folder, count in rows:
        rel = folder.relative_to(feeds_dir.parent)
        print(f"{count:>{max_count_width}}  {rel}")
    print("-" * (max_count_width + 2 + 60))
    print(f"{total:>{max_count_width}}  TOTAL")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Count feed files per subfolder.")
    parser.add_argument(
        "--feeds-dir",
        default=str(Path(__file__).resolve().parents[1] / "feeds"),
        help="Path to the feeds directory (default: ../feeds relative to this script)",
    )
    args = parser.parse_args()

    feeds_path = Path(args.feeds_dir)
    if not feeds_path.is_dir():
        print(f"Error: directory not found: {feeds_path}")
        raise SystemExit(1)

    count_feeds(feeds_path)
