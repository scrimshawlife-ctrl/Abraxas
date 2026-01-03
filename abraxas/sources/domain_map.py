"""Deterministic mapping from source_id -> domain."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

_DEFAULT_DOMAIN_MAP: Dict[str, str] = {}
_LOADED = False


def _load_default() -> None:
    global _DEFAULT_DOMAIN_MAP, _LOADED
    if _LOADED:
        return
    try:
        here = Path(__file__).resolve().parent
        path = here / "domain_map.json"
        if path.exists():
            _DEFAULT_DOMAIN_MAP = json.loads(path.read_text(encoding="utf-8"))
    finally:
        _LOADED = True


def domain_for_source_id(source_id: str) -> str:
    """Return a stable domain label for a source_id."""
    _load_default()
    sid = str(source_id or "unknown")
    if sid in _DEFAULT_DOMAIN_MAP:
        return str(_DEFAULT_DOMAIN_MAP[sid])
    if sid.startswith("LINGUISTIC_"):
        return "culture_memes"
    if sid.startswith("GOV_"):
        return "geopolitics"
    if sid.startswith("ECON_"):
        return "finance"
    if sid.startswith("NOAA_"):
        return "climate_energy"
    if sid.startswith("NASA_"):
        return "wildcards"
    return "unknown"
