"""
Load and query the user's uploaded .pptx template library (catalog.json).
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional


def _backend_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def catalog_path() -> str:
    return os.path.join(_backend_root(), "data", "templates", "catalog.json")


def templates_library_dir() -> str:
    return os.path.join(_backend_root(), "data", "templates", "library")


def load_catalog_raw() -> Dict[str, Any]:
    path = catalog_path()
    if not os.path.isfile(path):
        return {"version": 1, "templates": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def clear_catalog_cache() -> None:
    """No-op placeholder (catalog is read from disk each call)."""


def list_templates() -> List[Dict[str, Any]]:
    return list(load_catalog_raw().get("templates", []))


def resolve_pptx_path(entry: Dict[str, Any]) -> Optional[str]:
    rel = entry.get("pptx_relative") or entry.get("pptx_path")
    if not rel:
        return None
    # Allow paths relative to data/templates/
    if os.path.isabs(rel) and os.path.isfile(rel):
        return rel
    base = os.path.join(_backend_root(), "data", "templates")
    full = os.path.normpath(os.path.join(base, rel))
    if os.path.isfile(full):
        return full
    return None


def filter_by_structure_hint(structure_hint: str) -> List[Dict[str, Any]]:
    hint = (structure_hint or "").strip().lower()
    if not hint:
        return list_templates()
    out: List[Dict[str, Any]] = []
    for t in list_templates():
        hints = [str(h).strip().lower() for h in t.get("structure_hints", [])]
        if hint in hints or any(hint in h or h in hint for h in hints):
            out.append(t)
    return out


def format_catalog_for_llm(entries: List[Dict[str, Any]]) -> str:
    """Compact JSON for prompt context."""
    slim = []
    for e in entries:
        slim.append(
            {
                "id": e.get("id"),
                "name": e.get("name"),
                "description": e.get("description", ""),
                "structure_hints": e.get("structure_hints", []),
            }
        )
    return json.dumps(slim, ensure_ascii=False, indent=2)
