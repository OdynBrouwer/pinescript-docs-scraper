#!/usr/bin/env python3
"""Cleanup script: keep only the latest timestamped processed file per base name.

Files are expected to end with _YYYYMMDD_HHMMSS.md. For each base (everything
before the timestamp), we keep the file with the highest timestamp and remove
older files.
"""
import os
import re
from collections import defaultdict

ROOT = os.path.join(os.getcwd(), "pinescript_docs", "processed")
PAT = re.compile(r"(?P<base>.+)_(?P<ts>\d{8}_\d{6})\.md$")

if not os.path.isdir(ROOT):
    print(f"No processed folder found at {ROOT}, nothing to do.")
    exit(0)

files = os.listdir(ROOT)
by_base = defaultdict(list)

for fn in files:
    m = PAT.match(fn)
    if not m:
        # skip files that don't match the timestamp pattern
        continue
    base = m.group("base")
    ts = m.group("ts")
    by_base[base].append((ts, fn))

removed = []
for base, ts_files in by_base.items():
    if len(ts_files) <= 1:
        continue
    ts_files.sort(reverse=True)  # highest timestamp first
    to_keep = ts_files[0][1]
    to_remove = [fn for ts, fn in ts_files[1:]]
    for fn in to_remove:
        path = os.path.join(ROOT, fn)
        try:
            os.remove(path)
            removed.append(fn)
            print(f"Removed: {fn}")
        except Exception as e:
            print(f"Failed to remove {fn}: {e}")

if removed:
    print(f"Total removed: {len(removed)}")
else:
    print("No old files to remove.")

exit(0)
