from __future__ import annotations

from typing import Any
import hashlib
import json
import subprocess

from abraxas.operator.closure_card import run_operator_closure_card

from .binding_validator import run_binding_validator
from .closure_bundle import run_closure_bundle
from .invariance_harness import run_invariance_harness
from .notion_sync_validator import run_notion_sync_validator


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _get_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "UNKNOWN"


def run_green_state_attestation() -> dict[str, Any]:
    validator = run_binding_validator()
    bundle = run_closure_bundle()
    invariance = run_invariance_harness(runs=3)
    notion = run_notion_sync_validator()
    operator = run_operator_closure_card()

    payload = {
        "schema_version": "GreenStateReceipt.v1",
        "commit": _get_commit(),
        "validator": validator["overall_status"],
        "operator_health": operator["health"],
        "invariance": {
            "registry": invariance["registry_invariant"],
            "validator": invariance["validator_invariant"],
            "bundle": invariance["bundle_invariant"],
        },
        "notion_sync": notion["status"],
        "bundle_hash": bundle["bundle_hash"],
        "limitations": [
            "subsystems return NOT_COMPUTABLE",
            "no real signal ingestion",
            "no domain logic implemented",
        ],
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
