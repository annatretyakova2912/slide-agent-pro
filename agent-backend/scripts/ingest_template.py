#!/usr/bin/env python3
"""
Register a user .pptx template in data/templates/library/ and catalog.json.

Usage (from agent-backend/):
  python3 scripts/ingest_template.py --file ./mydeck.pptx --id timeline_01 \\
    --name "Timeline" --hints timeline,process_steps --description "4-step timeline"
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BACKEND_ROOT)

from src.services import template_catalog as tc  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a .pptx slide template into the library.")
    parser.add_argument("--file", required=True, help="Path to source .pptx (ideally one master slide).")
    parser.add_argument("--id", required=True, help="Unique template id (e.g. timeline_brand_a).")
    parser.add_argument("--name", required=True, help="Human-readable name.")
    parser.add_argument("--hints", required=True, help="Comma-separated structure_hints matching Content Architect.")
    parser.add_argument("--description", default="", help="Optional description for the selector LLM.")
    parser.add_argument("--slide-index", type=int, default=0, help="Which slide in the file is the master (0-based).")
    args = parser.parse_args()

    src = os.path.abspath(args.file)
    if not os.path.isfile(src):
        raise SystemExit(f"File not found: {src}")

    os.makedirs(tc.templates_library_dir(), exist_ok=True)
    dest_name = f"{args.id}.pptx"
    dest_rel = os.path.join("library", dest_name)
    dest_abs = os.path.join(tc.templates_library_dir(), dest_name)
    shutil.copy2(src, dest_abs)

    catalog_file = tc.catalog_path()
    os.makedirs(os.path.dirname(catalog_file), exist_ok=True)
    if os.path.isfile(catalog_file):
        with open(catalog_file, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"version": 1, "templates": []}

    hints = [h.strip().lower() for h in args.hints.split(",") if h.strip()]
    entry = {
        "id": args.id,
        "name": args.name,
        "description": args.description,
        "structure_hints": hints,
        "pptx_relative": dest_rel.replace("\\", "/"),
        "slide_index": args.slide_index,
    }

    templates = data.setdefault("templates", [])
    templates = [t for t in templates if t.get("id") != args.id]
    templates.append(entry)
    data["templates"] = templates

    with open(catalog_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    tc.clear_catalog_cache()
    print(f"Registered template '{args.id}' -> {dest_abs}")
    print(f"Updated catalog: {catalog_file}")


if __name__ == "__main__":
    main()
