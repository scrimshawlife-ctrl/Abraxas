from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional


_CATALOG_PATH = Path(__file__).with_name("catalog.v0.yaml")
_RUNE_CACHE: Optional[Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]]] = None


@dataclass(frozen=True)
class RuneEntry:
    rune_id: str
    module: str
    domain_id: str
    version: str


def _load_catalog() -> Dict[str, RuneEntry]:
    lines = _CATALOG_PATH.read_text(encoding="utf-8").splitlines()
    entries: Dict[str, RuneEntry] = {}
    current: Dict[str, Any] | None = None
    in_runes = False

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "runes:":
            in_runes = True
            continue
        if not in_runes:
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        if line.startswith("- ") and indent == 2:
            if current:
                entry = RuneEntry(
                    rune_id=str(current.get("rune_id", "")),
                    module=str(current.get("module", "")),
                    domain_id=str(current.get("domain_id", "")),
                    version=str(current.get("version", "")),
                )
                entries[entry.rune_id] = entry
            current = {}
            line = line[2:].strip()
            if line:
                key, value = [part.strip() for part in line.split(":", 1)]
                current[key] = value
            continue

        if current is None:
            continue

        if ":" in line:
            key, value = [part.strip() for part in line.split(":", 1)]
            current[key] = value

    if current:
        entry = RuneEntry(
            rune_id=str(current.get("rune_id", "")),
            module=str(current.get("module", "")),
            domain_id=str(current.get("domain_id", "")),
            version=str(current.get("version", "")),
        )
        entries[entry.rune_id] = entry

    return entries


def _load_callable(module_path: str) -> Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]:
    if ":" not in module_path:
        raise ValueError(f"Invalid rune module path: {module_path}")
    mod_name, fn_name = module_path.split(":", 1)
    module = importlib.import_module(mod_name)
    fn = getattr(module, fn_name, None)
    if fn is None:
        raise ValueError(f"Rune callable not found: {module_path}")
    return fn


def _load_rune_map() -> Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]]:
    catalog = _load_catalog()
    mapping: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = {}
    for rune_id in sorted(catalog.keys()):
        mapping[rune_id] = _load_callable(catalog[rune_id].module)
    return mapping


def invoke_rune(rune_id: str, payload: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    global _RUNE_CACHE
    if _RUNE_CACHE is None:
        _RUNE_CACHE = _load_rune_map()
    fn = _RUNE_CACHE.get(rune_id)
    if fn is None:
        _RUNE_CACHE = _load_rune_map()
        fn = _RUNE_CACHE.get(rune_id)
        if fn is None:
            raise ValueError(f"Unknown rune_id: {rune_id}")
    result = fn(payload, ctx)
    return result
