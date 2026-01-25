from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

REQUIRED_KEYS = ("id", "source", "url", "published_at", "title", "text")


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for ln, line in enumerate(f, start=1):
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {ln} in {path}: {e}") from e
            items.append(obj)
    return items


def validate_items(items: List[Dict[str, Any]]) -> None:
    for i, it in enumerate(items):
        for k in REQUIRED_KEYS:
            if k not in it:
                raise ValueError(f"Item[{i}] missing required key '{k}'")
        # deterministic type checks (no coercion)
        for k in REQUIRED_KEYS:
            if not isinstance(it[k], str):
                raise ValueError(
                    f"Item[{i}] key '{k}' must be string, got {type(it[k]).__name__}"
                )


def sort_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # deterministic order
    return sorted(items, key=lambda x: (x.get("published_at", ""), x.get("source", ""), x.get("id", "")))
