from __future__ import annotations

from typing import Any
import hashlib
import json

from abraxas.registry.binding_validator import run_binding_validator
from abraxas.registry.closure_bundle import run_closure_bundle
from abraxas.registry.invariance_harness import run_invariance_harness
from abraxas.registry.notion_sync_validator import run_notion_sync_validator
from abraxas.registry.subsystem_registry import load_subsystem_registry


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_operator_closure_card() -> dict[str, Any]:
    registry = load_subsystem_registry()
    validator = run_binding_validator()
    bundle = run_closure_bundle()
    invariance = run_invariance_harness(runs=3)
    notion_sync = run_notion_sync_validator()

    health = "GREEN"
    if validator["overall_status"] != "PASS":
        health = "YELLOW"
    if not (
        invariance["registry_invariant"]
        and invariance["validator_invariant"]
        and invariance["bundle_invariant"]
    ):
        health = "RED"

    payload = {
        "schema_version": "OperatorClosureCard.v1",
        "health": health,
        "registry": {
            "subsystem_count": registry.subsystem_count,
            "hash": registry.canonical_hash,
        },
        "validator": {
            "status": validator["overall_status"],
            "fail_count": validator["counts"]["fail"],
        },
        "invariance": {
            "all_invariant": (
                invariance["registry_invariant"]
                and invariance["validator_invariant"]
                and invariance["bundle_invariant"]
            )
        },
        "notion_sync": {"status": notion_sync["status"]},
        "bundle": {
            "artifact_count": len(bundle["artifacts"]),
            "hash": bundle["bundle_hash"],
        },
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
