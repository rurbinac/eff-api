"""Sort XML feed files in the feeds/ directory into per-type subdirectories.

Usage:
    python scripts/sort_feeds.py [--dry-run]

Moves files from:
    feeds/<filename>.xml
To:
    feeds/<type>/<filename>.xml   e.g. feeds/f7/srml-8-2026-f2645232-matchresults.xml

ZIP files are extracted to feeds/ first, then the zip is moved to feeds/zip/.
Unknown XML files go to feeds/unknown/.
Non-XML files are left in place.
"""

import argparse
import hashlib
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

# Matches the OPTA production-header comment block at the top of every feed file.
_PROD_TIME_RE = re.compile(r"production time:\s*(\d{8}T\d{6}[,\.]\d+Z?)", re.IGNORECASE)


def parse_production_time(path: Path) -> datetime | None:
    """Read the OPTA production-time stamp from the XML comment header.

    Format in file:  20260318T135549,844Z
    Returned as:     datetime(2026, 3, 18, 13, 55, 49, 844000)  (naive UTC)
    Returns None if the header is absent or unparseable.
    """
    try:
        # The header is always in the first few lines — read only 512 bytes
        with path.open("r", encoding="utf-8", errors="replace") as f:
            head = f.read(512)
        m = _PROD_TIME_RE.search(head)
        if not m:
            return None
        raw = m.group(1).rstrip("Z").replace(",", ".").replace("T", "")
        # raw is now e.g. "202603181355549.844" → split into date+time+frac
        dt_part, _, frac = raw.partition(".")
        # dt_part: "20260318135549"
        return datetime(
            int(dt_part[0:4]),   # year
            int(dt_part[4:6]),   # month
            int(dt_part[6:8]),   # day
            int(dt_part[8:10]),  # hour
            int(dt_part[10:12]), # minute
            int(dt_part[12:14]), # second
            int(frac.ljust(6, "0")[:6]) if frac else 0,  # microseconds
        )
    except Exception:
        return None


def sha1(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

# ── Feed-type patterns (mirrors app/services/f_loader.py) ──────────────────
PATTERNS = [
    ("f7",      re.compile(r"^srml-([18])-(\d+)-f\d+-matchresults\.xml$")),
    ("f42",     re.compile(r"^f42-([18])-(\d{4})-results\.xml$")),
    ("f1",      re.compile(r"^srml-([18])-(\d{4})-results\.xml$")),
    ("f2",      re.compile(r"^opta-(\d+)-matchpreview\.xml$")),
    ("f3",      re.compile(r"^srml-([18])-(\d{4})-standings\.xml$")),
    ("f26",     re.compile(r"^football_results\.([18])\.(\d{8})\.(\d{6})\.xml$")),
    ("f40",     re.compile(r"^srml-([18])-(\d{4})-squads\.xml$")),
    ("f45",     re.compile(r"^f45-([18])-(\d{4})-venues\.xml$")),
]


def get_feed_type(filename: str) -> str:
    for feed_type, pattern in PATTERNS:
        if pattern.match(filename):
            return feed_type
    return "unknown"


_F7_SEASON_RE = re.compile(r"^srml-[18]-(\w+)-f\d+-matchresults\.xml$")


def get_dest_dir(feeds_dir: Path, filename: str, feed_type: str) -> Path:
    """Return the destination directory for a file, applying per-type sub-grouping.

    F26: year < 2025  → f26/{yyyy}/
         year >= 2025 → f26/{yyyymm}/
    F7:  season ID from filename → f7/{season_id}/   (e.g. f7/2026/ or f7/7/)

    If feeds_dir is already the type folder (e.g. feeds/f26), the type prefix
    is not added again — sub-grouping goes directly under feeds_dir.
    """
    # If we're already inside the type folder, don't add it again
    base = feeds_dir if feeds_dir.name == feed_type else feeds_dir / feed_type

    if feed_type == "f26":
        # football_results.8.20250815.205249.xml → date segment = parts[2]
        parts = filename.split(".")
        if len(parts) >= 3 and len(parts[2]) >= 6:
            return base / parts[2][:6]   # yyyymm  e.g. "202508", "200609"

    elif feed_type == "f2":
        # opta-2210471-matchpreview.xml → first 4 digits of the match ID
        m = re.match(r"^opta-(\d{4})", filename)
        if m:
            return base / m.group(1)   # e.g. "2210"

    elif feed_type == "f7":
        # srml-8-2026-f2645226-matchresults.xml  → season "2026"
        # srml-8-7-f44373-matchresults.xml        → season "7"
        m = _F7_SEASON_RE.match(filename)
        if m:
            return base / m.group(1)

    return base


def extract_zips(feeds_dir: Path, dry_run: bool = False) -> int:
    """Extract any zip files in feeds_dir to feeds_dir, then move the zip to feeds/zip/.

    Returns the number of zips processed.
    """
    zip_files = [f for f in feeds_dir.iterdir() if f.is_file() and f.suffix.lower() == ".zip"]
    if not zip_files:
        return 0

    zip_dir = feeds_dir / "zip"
    processed = 0

    for zf_path in sorted(zip_files):
        print(f"\n  ZIP  {zf_path.name}")
        try:
            with zipfile.ZipFile(zf_path, "r") as zf:
                members = zf.namelist()
                for member in members:
                    dest = feeds_dir / Path(member).name  # flatten — no subdirs from zip
                    if dest.exists():
                        print(f"       skip {member}  (already exists in feeds/)")
                    else:
                        print(f"       {'DRY ' if dry_run else ''}extract  {member}")
                        if not dry_run:
                            zf.extract(member, feeds_dir)
                            # If the zip stored it in a subdir, move it up to feeds_dir
                            extracted = feeds_dir / member
                            if extracted != dest:
                                shutil.move(str(extracted), str(dest))

            # Move the zip itself to feeds/zip/
            zip_dest = zip_dir / zf_path.name
            print(f"       {'DRY ' if dry_run else ''}move zip → zip/{zf_path.name}")
            if not dry_run:
                zip_dir.mkdir(exist_ok=True)
                shutil.move(str(zf_path), str(zip_dest))
            processed += 1

        except (zipfile.BadZipFile, PermissionError) as e:
            print(f"       ERROR: {e} — skipped")

    return processed


def sort_feeds(feeds_dir: Path, dry_run: bool = False) -> None:
    # Step 1 — unpack any zips first so their contents get sorted below
    n_zips = extract_zips(feeds_dir, dry_run=dry_run)
    if n_zips:
        print()

    xml_files = [f for f in feeds_dir.iterdir() if f.is_file() and f.suffix.lower() == ".xml"]

    if not xml_files:
        if not n_zips:
            print("No XML or ZIP files found directly in", feeds_dir)
        return

    moved = 0
    deleted = 0
    replaced = 0
    skipped = 0
    locked: list[str] = []

    for src in sorted(xml_files):
        # Empty file — delete immediately, nothing to sort
        if src.stat().st_size == 0:
            print(f"  {'DRY ' if dry_run else ''}DEL   {src.name}  (empty file, deleted)")
            if not dry_run:
                src.unlink()
            deleted += 1
            continue

        feed_type = get_feed_type(src.name)
        dest_dir = get_dest_dir(feeds_dir, src.name, feed_type)
        dest = dest_dir / src.name

        rel = dest_dir.relative_to(feeds_dir)
        if dest.exists():
            if sha1(src) == sha1(dest):
                # Identical content — source is redundant, remove it
                if not dry_run:
                    src.unlink()
                print(f"  {'DRY ' if dry_run else ''}DEL   {src.name}  (identical, source removed)")
                deleted += 1
            else:
                # Different content — compare production times
                src_time = parse_production_time(src)
                dest_time = parse_production_time(dest)

                if src_time is None or dest_time is None:
                    # Can't determine which is newer — leave both alone
                    print(f"  SKIP  {src.name}  (differs, no production time, kept both)")
                    skipped += 1
                elif src_time > dest_time:
                    # Source is newer — replace dest with source
                    if not dry_run:
                        dest.unlink()
                        dest_dir.mkdir(exist_ok=True)
                        shutil.move(str(src), str(dest))
                    print(f"  {'DRY ' if dry_run else ''}REPL  {src.name}  →  {rel}/  (source newer: {src_time} > {dest_time})")
                    replaced += 1
                else:
                    # Dest is newer or equal — source is outdated, remove it
                    if not dry_run:
                        src.unlink()
                    print(f"  {'DRY ' if dry_run else ''}DEL   {src.name}  (dest newer: {dest_time} >= {src_time}, source removed)")
                    deleted += 1
            continue

        print(f"  {'DRY ' if dry_run else ''}MOVE  {src.name}  →  {rel}/")

        if not dry_run:
            dest_dir.mkdir(exist_ok=True)
            try:
                shutil.move(str(src), str(dest))
                moved += 1
            except PermissionError:
                print(f"  LOCK  {src.name}  (in use, skipped)")
                locked.append(src.name)
        else:
            moved += 1

    parts = [f"{moved} moved", f"{replaced} replaced", f"{deleted} removed", f"{skipped} skipped"]
    if locked:
        parts.append(f"{len(locked)} locked (still downloading)")
    print(f"\nDone — {', '.join(parts)}.")
    if locked:
        for name in locked:
            print(f"    {name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sort feed XML files into per-type subdirectories.")
    parser.add_argument(
        "--feeds-dir",
        default=str(Path(__file__).resolve().parents[1] / "feeds"),
        help="Path to the feeds directory (default: ../feeds relative to this script)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be moved without actually moving anything.",
    )
    args = parser.parse_args()

    feeds_path = Path(args.feeds_dir)
    if not feeds_path.is_dir():
        print(f"Error: directory not found: {feeds_path}")
        raise SystemExit(1)

    print(f"Feeds dir : {feeds_path}")
    print(f"Dry run   : {args.dry_run}\n")
    sort_feeds(feeds_path, dry_run=args.dry_run)
