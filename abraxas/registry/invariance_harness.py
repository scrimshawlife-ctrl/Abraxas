from __future__ import annotations

from typing import Any
import hashlib
import json

from .binding_validator import run_binding_validator
from .closure_bundle import run_closure_bundle
from .subsystem_registry import load_subsystem_registry


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _check_invariance(values: list[str]) -> bool:
    return len(set(values)) == 1


def run_invariance_harness(runs: int = 5) -> dict[str, Any]:
    registry_hashes: list[str] = []
    validator_hashes: list[str] = []
    bundle_hashes: list[str] = []

    for _ in range(runs):
        registry = load_subsystem_registry()
        validator = run_binding_validator()
        bundle = run_closure_bundle()

        registry_hashes.append(registry.canonical_hash)
        validator_hashes.append(validator["canonical_hash"])
        bundle_hashes.append(bundle["bundle_hash"])

    payload = {
        "schema_version": "InvarianceHarnessRun.v1",
        "runs": runs,
        "registry_invariant": _check_invariance(registry_hashes),
        "validator_invariant": _check_invariance(validator_hashes),
        "bundle_invariant": _check_invariance(bundle_hashes),
        "registry_hashes": registry_hashes,
        "validator_hashes": validator_hashes,
        "bundle_hashes": bundle_hashes,
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
