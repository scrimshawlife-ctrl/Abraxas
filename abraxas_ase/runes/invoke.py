"""
ABX-Runes Invocation System for ASE.

Provides deterministic rune lookup and invocation with schema validation.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from ..provenance import sha256_hex, stable_json_dumps


class RuneNotFoundError(Exception):
    """Raised when a rune_id is not found in the catalog."""

    def __init__(self, rune_id: str):
        self.rune_id = rune_id
        super().__init__(f"Rune not found: {rune_id}")


class RuneValidationError(Exception):
    """Raised when rune input/output validation fails."""

    def __init__(self, rune_id: str, message: str):
        self.rune_id = rune_id
        super().__init__(f"Rune validation error [{rune_id}]: {message}")


# -----------------------------------------------------------------------------
# Catalog Loading
# -----------------------------------------------------------------------------

_CATALOG_PATH = Path(__file__).parent / "catalog.v0.yaml"
_catalog_cache: Optional[Dict[str, Any]] = None


def _load_catalog() -> Dict[str, Any]:
    """Load the rune catalog (cached)."""
    global _catalog_cache
    if _catalog_cache is not None:
        return _catalog_cache

    if not _CATALOG_PATH.exists():
        raise FileNotFoundError(f"Rune catalog not found: {_CATALOG_PATH}")

    with open(_CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = yaml.safe_load(f)

    # Build lookup dict by rune_id
    _catalog_cache = {}
    for entry in catalog.get("runes", []):
        rune_id = entry.get("rune_id")
        if rune_id:
            _catalog_cache[rune_id] = entry

    return _catalog_cache


def _get_catalog_entry(rune_id: str) -> Dict[str, Any]:
    """Get catalog entry for a rune_id."""
    catalog = _load_catalog()
    if rune_id not in catalog:
        raise RuneNotFoundError(rune_id)
    return catalog[rune_id]


# -----------------------------------------------------------------------------
# Rune Module Loading
# -----------------------------------------------------------------------------

_module_cache: Dict[str, Any] = {}


def _load_rune_module(module_path: str) -> Any:
    """Load and cache a rune module."""
    if module_path not in _module_cache:
        _module_cache[module_path] = importlib.import_module(module_path)
    return _module_cache[module_path]


def _get_rune_handler(entry: Dict[str, Any]) -> Callable:
    """Get the handler function from a rune module."""
    module = _load_rune_module(entry["module"])
    handler_name = entry.get("handler", "invoke")
    if not hasattr(module, handler_name):
        raise AttributeError(
            f"Rune module {entry['module']} has no handler '{handler_name}'"
        )
    return getattr(module, handler_name)


# -----------------------------------------------------------------------------
# Schema Loading
# -----------------------------------------------------------------------------

_schema_cache: Dict[str, Dict[str, Any]] = {}


def _load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a JSON schema by relative path."""
    if schema_path in _schema_cache:
        return _schema_cache[schema_path]

    # Resolve relative to package root
    base = Path(__file__).parent.parent
    full_path = base / schema_path

    if not full_path.exists():
        raise FileNotFoundError(f"Schema not found: {full_path}")

    with open(full_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    _schema_cache[schema_path] = schema
    return schema


def get_rune_schema(rune_id: str, schema_type: str = "input") -> Dict[str, Any]:
    """
    Get the input or output schema for a rune.

    Args:
        rune_id: The rune identifier
        schema_type: "input" or "output"

    Returns:
        JSON schema dict
    """
    entry = _get_catalog_entry(rune_id)
    schema_key = f"{schema_type}_schema"

    if schema_key not in entry:
        raise ValueError(f"Rune {rune_id} has no {schema_type} schema defined")

    return _load_schema(entry[schema_key])


# -----------------------------------------------------------------------------
# Invocation
# -----------------------------------------------------------------------------


def _compute_input_hash(payload: Dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash of input payload."""
    return sha256_hex(stable_json_dumps(payload).encode("utf-8"))


def invoke_rune(
    rune_id: str,
    payload: Dict[str, Any],
    ctx: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Invoke a rune by ID with payload and context.

    Args:
        rune_id: The rune identifier (e.g., "sdct.text_subword.v1")
        payload: Input payload (items, params, etc.)
        ctx: Invocation context (run_id, date, key, tier, etc.)

    Returns:
        Rune output dict with evidence_rows, provenance, etc.

    Raises:
        RuneNotFoundError: If rune_id is not in catalog
        RuneValidationError: If input/output validation fails
    """
    # Lookup rune in catalog
    entry = _get_catalog_entry(rune_id)

    # Compute input hash for provenance
    input_hash = _compute_input_hash(payload)

    # Build invocation context
    invoke_ctx = {
        "rune_id": rune_id,
        "rune_version": entry.get("version", "0.0.0"),
        "input_hash": input_hash,
        **(ctx or {}),
    }

    # Get and call handler
    handler = _get_rune_handler(entry)

    try:
        result = handler(payload, invoke_ctx)
    except Exception as e:
        # Wrap handler exceptions
        if isinstance(e, (RuneNotFoundError, RuneValidationError)):
            raise
        raise RuneValidationError(rune_id, str(e)) from e

    # Ensure result is a dict
    if not isinstance(result, dict):
        raise RuneValidationError(rune_id, "Handler must return a dict")

    # Attach provenance if not already present
    if "provenance" not in result:
        result["provenance"] = {}
    result["provenance"]["rune_id"] = rune_id
    result["provenance"]["rune_version"] = entry.get("version", "0.0.0")
    result["provenance"]["input_hash"] = input_hash
    result["provenance"]["schema_versions"] = {
        "input": entry.get("input_schema", "unknown"),
        "output": entry.get("output_schema", "unknown"),
    }

    return result


def list_runes() -> List[str]:
    """List all available rune IDs in deterministic order."""
    catalog = _load_catalog()
    return sorted(catalog.keys())


def get_rune_entry(rune_id: str) -> Dict[str, Any]:
    """Get full catalog entry for a rune."""
    return _get_catalog_entry(rune_id)


# -----------------------------------------------------------------------------
# Cache Management (for testing)
# -----------------------------------------------------------------------------


def clear_caches() -> None:
    """Clear all caches (for testing)."""
    global _catalog_cache
    _catalog_cache = None
    _module_cache.clear()
    _schema_cache.clear()
