#!/usr/bin/env python3
"""Cleanup script: keep only the latest timestamped file per document slug.

For processed files we group by the document slug, not by the numeric page index.
This avoids keeping old files when page numbering changes between runs.
"""
import argparse
import re
from collections import defaultdict
from pathlib import Path


PROCESSED_PAT = re.compile(
    r"^processed_(?P<number>\d+)_(?P<slug>.+)_(?P<ts>\d{8}_\d{6})\.md$"
)
UNPROCESSED_PAT = re.compile(r"^(?P<number>\d+)_(?P<slug>.+)_(?P<ts>\d{8}_\d{6})\.md$")


def cleanup_dir(root: Path, dry_run: bool = False, processed: bool = False) -> int:
    if not root.is_dir():
        print(f"No folder found at {root}, skipping.")
        return 0

    files = sorted(root.iterdir())
    by_slug = defaultdict(list)
    pattern = PROCESSED_PAT if processed else UNPROCESSED_PAT

    for path in files:
        if not path.is_file():
            continue
        m = pattern.match(path.name)
        if not m:
            continue
        slug = m.group("slug")
        ts = m.group("ts")
        by_slug[slug].append((ts, path))

    removed = []
    for slug, ts_paths in by_slug.items():
        if len(ts_paths) <= 1:
            continue
        ts_paths.sort(key=lambda item: item[0], reverse=True)
        to_keep = ts_paths[0][1]
        to_remove = [path for ts, path in ts_paths[1:]]
        for path in to_remove:
            if dry_run:
                print(f"Would remove: {path}")
                removed.append(path.name)
                continue
            try:
                path.unlink()
                removed.append(path.name)
                print(f"Removed: {path.name}")
            except Exception as e:
                print(f"Failed to remove {path.name}: {e}")

    if removed:
        print(f"Total removed from {root}: {len(removed)}")
    else:
        print(f"No old files to remove in {root}.")
    return len(removed)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Cleanup timestamped files in processed/unprocessed dirs"
    )
    ap.add_argument(
        "--target",
        choices=["processed", "unprocessed", "both"],
        default="processed",
        help="Which folder(s) to clean",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting",
    )
    ap.add_argument(
        "--root",
        default=None,
        help="Project root (defaults to CWD)",
    )
    args = ap.parse_args()

    root = Path(args.root or Path.cwd())
    removed_total = 0

    if args.target in ("processed", "both"):
        processed_dir = root / "pinescript_docs" / "processed"
        removed_total += cleanup_dir(processed_dir, dry_run=args.dry_run, processed=True)

    if args.target in ("unprocessed", "both"):
        unprocessed_dir = root / "pinescript_docs" / "unprocessed"
        removed_total += cleanup_dir(unprocessed_dir, dry_run=args.dry_run, processed=False)

    print(f"Total files removed: {removed_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
