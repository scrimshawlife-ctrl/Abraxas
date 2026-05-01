from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.viz.svg_ledger_models import AUTHORITY, ENTRY_VERSION, ledger_run_payload
from abraxas.viz.svg_ledger_validator import validate_authority, validate_manifest


def _entry_id(manifest: Dict[str, Any]) -> str:
    material = {
        "render_id": manifest["render_id"],
        "svg_hash": manifest["svg_hash"],
        "view_packet_hash": manifest["view_packet_hash"],
    }
    return sha256_hex(canonical_json(material))


def _lineage_hash(manifest: Dict[str, Any]) -> str:
    material = {
        "render_id": manifest["render_id"],
        "view_id": manifest["view_id"],
        "svg_hash": manifest["svg_hash"],
        "view_packet_hash": manifest["view_packet_hash"],
    }
    return sha256_hex(canonical_json(material))


def build_entry(manifest: Dict[str, Any]) -> Dict[str, Any]:
    validate_manifest(manifest)
    manifest_hash = sha256_hex(canonical_json(manifest))
    return {
        "entry_version": ENTRY_VERSION,
        "entry_id": _entry_id(manifest),
        "render_id": manifest["render_id"],
        "view_id": manifest["view_id"],
        "svg_hash": manifest["svg_hash"],
        "view_packet_hash": manifest["view_packet_hash"],
        "svg_path": str(manifest.get("files", {}).get("svg_path", "")),
        "render_snapshot": deepcopy(manifest),
        "audit": {
            "render_manifest_hash": manifest_hash,
            "lineage_hash": _lineage_hash(manifest),
        },
        "review": {
            "ledger_status": "recorded",
            "review_notes": [],
            "decision_reason": None,
        },
        "authority": dict(AUTHORITY),
    }


def build_ledger_run(manifest: Dict[str, Any], previous: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    validate_authority()
    manifest_copy = deepcopy(manifest)
    prior_entries = list((previous or {}).get("entries") or [])
    indexed = {str(e.get("entry_id")): e for e in prior_entries}

    candidate = build_entry(manifest_copy)
    existing = candidate["entry_id"] in indexed
    if not existing:
        indexed[candidate["entry_id"]] = candidate

    entries = list(indexed.values())
    entries.sort(key=lambda e: (str(e.get("render_id", "")), str(e.get("entry_id", ""))))
    return ledger_run_payload(
        entries=entries,
        manifests_total=1,
        entries_created=0 if existing else 1,
        entries_existing=1 if existing else 0,
    )
