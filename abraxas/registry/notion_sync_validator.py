from __future__ import annotations

from typing import Any
import hashlib
import json

from .notion_repo_map import load_notion_repo_map
from .subsystem_registry import load_subsystem_registry


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_notion_sync_validator() -> dict[str, Any]:
    registry = load_subsystem_registry()
    notion_map = load_notion_repo_map()

    registry_ids = set(registry.subsystem_ids)
    mapped_ids = set(binding["subsystem_id"] for binding in notion_map.bindings)

    missing_in_map = sorted(list(registry_ids - mapped_ids))
    extra_in_map = sorted(list(mapped_ids - registry_ids))
    status = "PASS" if not missing_in_map and not extra_in_map else "FAIL"

    payload = {
        "schema_version": "NotionSyncValidatorRun.v1",
        "status": status,
        "missing_in_map": missing_in_map,
        "extra_in_map": extra_in_map,
        "registry_hash": registry.canonical_hash,
        "map_hash": notion_map.canonical_hash,
    }
    payload_hash = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return {
        **payload,
        "canonical_hash": payload_hash,
        "authority": {
            "mutation": False,
            "promotion": False,
            "execution": False,
            "observe_only": True,
        },
    }
