from __future__ import annotations

from typing import Any
import hashlib
import json

from .binding_validator import run_binding_validator
from .subsystem_registry import load_subsystem_registry


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_binding_gap_plan() -> dict[str, Any]:
    validator = run_binding_validator()
    registry = load_subsystem_registry()

    plan: list[dict[str, Any]] = []
    registry_map = {row["subsystem_id"]: row for row in registry.raw["subsystems"]}

    for result in validator["results"]:
        if result["status"] != "FAIL":
            continue

        subsystem_id = result["subsystem_id"]
        missing = result["missing"]
        registry_row = registry_map.get(subsystem_id, {})
        expected = registry_row.get("expected_paths", {})

        actions = []
        for category in missing:
            paths = expected.get(category, [])
            actions.append(
                {
                    "category": category,
                    "expected_paths": paths,
                    "action": "CREATE_OR_FIX",
                }
            )

        plan.append(
            {
                "subsystem_id": subsystem_id,
                "missing_categories": missing,
                "actions": actions,
            }
        )

    payload = {
        "schema_version": "BindingGapPlan.v1",
        "fail_count": validator["counts"]["fail"],
        "plan": sorted(plan, key=lambda item: item["subsystem_id"]),
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
