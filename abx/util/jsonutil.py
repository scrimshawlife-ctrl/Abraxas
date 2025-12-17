"""Deterministic JSON utilities for provenance and hashing."""

from __future__ import annotations
import json
from typing import Any

def dumps_stable(obj: Any) -> str:
    """Stable JSON for hashing / provenance."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def loads(s: str) -> Any:
    """Load JSON from string."""
    return json.loads(s)

def dump_file(path: str, obj: Any) -> None:
    """Write JSON to file with stable formatting."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(dumps_stable(obj) + "\n")

def load_file(path: str) -> Any:
    """Load JSON from file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.loads(f.read())
