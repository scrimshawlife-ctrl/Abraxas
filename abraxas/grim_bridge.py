"""GRIM overlay bridge for ABX rune discovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

_SCHEMA_VERSION = "grim.overlay_delta.v1"
_OVERLAY_NAME = "abraxas"

_RUNE_REGISTRY: dict[str, dict[str, Any]] = {}


def _get_value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _coerce_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple | set):
        return list(value)
    return [value]


def _normalize_str_list(values: Iterable[Any]) -> list[str]:
    normalized = [str(value) for value in values if value not in (None, "")]
    return sorted(set(normalized))


def _normalize_edges(edges: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:
    edges = list(edges or [])
    edges_sorted = sorted(
        edges,
        key=lambda edge: (
            str(edge.get("src_id", "")),
            str(edge.get("dst_id", "")),
            str(edge.get("kind", "")),
        ),
    )
    return edges_sorted


def register_rune(rune: Any, *, source: str | None = None, **metadata: Any) -> dict[str, Any] | None:
    """Register or update rune metadata for GRIM export."""
    rune_id = _get_value(rune, "rune_id", None) or _get_value(rune, "id", None)
    if not rune_id:
        return None

    name = _get_value(rune, "name", "")
    version = _get_value(rune, "version", None) or _get_value(rune, "introduced_version", None) or ""
    description = (
        _get_value(rune, "description", None)
        or _get_value(rune, "function", None)
        or _get_value(rune, "motto", None)
        or ""
    )

    capabilities = _coerce_list(_get_value(rune, "capabilities", None))
    capability = _get_value(rune, "capability", None)
    if capability:
        capabilities.append(capability)
    tags = _coerce_list(_get_value(rune, "tags", None))
    status = _get_value(rune, "status", None) or "active"
    replaced_by = _get_value(rune, "replaced_by", None)
    edges_out = _coerce_list(_get_value(rune, "edges_out", None) or _get_value(rune, "edges", None))

    existing = _RUNE_REGISTRY.get(str(rune_id), {})
    merged_capabilities = _normalize_str_list(existing.get("capabilities", []) + capabilities)
    merged_tags = _normalize_str_list(existing.get("tags", []) + tags)
    preserved_status = existing.get("status") or status

    record = {
        "rune_id": str(rune_id),
        "name": str(name),
        "version": str(version),
        "description": str(description),
        "capabilities": merged_capabilities,
        "tags": merged_tags,
        "status": preserved_status,
        "replaced_by": replaced_by,
        "edges_out": _normalize_edges(edges_out),
        "source": source or existing.get("source") or "",
    }
    if metadata:
        record.update(metadata)
    _RUNE_REGISTRY[str(rune_id)] = record
    return record


def registry_size() -> int:
    return len(_RUNE_REGISTRY)


def export_overlay_delta() -> dict[str, Any]:
    records = {rune_id: _RUNE_REGISTRY[rune_id] for rune_id in sorted(_RUNE_REGISTRY)}
    return {
        "schema_version": _SCHEMA_VERSION,
        "overlay": _OVERLAY_NAME,
        "records": records,
    }


def write_overlay_delta(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = export_overlay_delta()
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return path
