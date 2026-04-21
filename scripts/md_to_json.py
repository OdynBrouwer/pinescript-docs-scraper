#!/usr/bin/env python3
"""Convert processed Markdown files into mcp-server JSON structure.

Creates `index.json` and `language-reference.json` under the target output
directory (defaults to ../mcp-server-pinescript/docs/processed).

Usage:
  python scripts/md_to_json.py --src pinescript_docs/processed --out ../mcp-server-pinescript/docs/processed
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict


def slug_from_filename(p: Path) -> str:
    name = p.stem
    parts = name.split("_")
    if parts and parts[0] == "processed":
        parts = parts[1:]
    # drop trailing timestamp-like tokens
    cleaned = [t for t in parts if not (t.isdigit() or (len(t) >= 8 and t.isdigit()))]
    if not cleaned:
        return name
    return "_".join(cleaned)


def make_id(slug: str) -> str:
    return hashlib.md5(slug.encode("utf-8")).hexdigest()[:8]


def parse_markdown(p: Path) -> Dict[str, str]:
    text = p.read_text(encoding="utf-8")
    title = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# "):
            title = s[2:].strip()
            break
    if not title:
        title = slug_from_filename(p).replace("_", " ")
    return {"title": title, "content": text}


def build_index(src_dir: Path) -> Dict[str, Dict]:
    index = {}
    md_files = sorted(src_dir.glob("processed_*.md"))
    if not md_files:
        # fallback: include any .md in directory
        md_files = sorted(src_dir.glob("*.md"))
    for p in md_files:
        slug = slug_from_filename(p)
        pid = make_id(slug)
        parsed = parse_markdown(p)
        index[pid] = {
            "title": parsed["title"],
            "type": "reference",
            "slug": slug,
            "content": parsed["content"],
            "examples": [],
        }
    return index


def build_language_reference(index: Dict[str, Dict]) -> Dict:
    # Minimal skeleton that matches the mcp-server shape. Fill functions/variables
    # as empty maps for later enrichment.
    return {
        "functions": {},
        "variables": {},
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source": "pinescript-docs-scraper",
            "entries_count": len(index),
        },
    }


def write_json(obj: Dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert processed Markdown → mcp-server JSON")
    ap.add_argument("--src", default="pinescript_docs/processed", help="Source processed markdown dir")
    ap.add_argument("--out", default="../mcp-server-pinescript/docs/processed", help="Output mcp-server docs dir")
    args = ap.parse_args()

    src = Path(args.src).resolve()
    out = Path(args.out).resolve()

    if not src.exists():
        print(f"Source directory not found: {src}")
        return 2

    print(f"Reading Markdown from: {src}")
    index = build_index(src)
    langref = build_language_reference(index)

    print(f"Writing JSON to: {out}")
    write_json(index, out / "index.json")
    write_json(langref, out / "language-reference.json")

    # small defaults to help mcp-server pick these files up
    write_json({"version": "1.0.0", "execution_model": {"bar_processing": "sequential", "script_execution": "per_bar"}}, out / "execution-model.json")
    write_json({"version": "1.0.0", "style_rules": [{"rule": "line_length", "max_length": 120}]}, out / "style-guide.json")

    print(f"Generated {len(index)} index entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
