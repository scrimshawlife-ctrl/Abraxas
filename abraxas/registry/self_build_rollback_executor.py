from __future__ import annotations

from typing import Any
import hashlib
import json
from pathlib import Path
import subprocess
import time

from abraxas.operator.closure_card import run_operator_closure_card

from .binding_validator import run_binding_validator
from .invariance_harness import run_invariance_harness
from .self_build_rollback_ledger import append_rollback_entry


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_ledger() -> dict[str, Any]:
    path = Path("out/registry/self_build_mutation_ledger.latest.json")
    if not path.exists():
        raise FileNotFoundError("Mutation ledger not found")
    return json.loads(path.read_text(encoding="utf-8"))


def _get_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "UNKNOWN"


def _fail_result(mutation_id: str, reason: str, operator_approved: bool, target_path: str = "", current_hash: str = "") -> dict[str, Any]:
    entry = {
        "mutation_id": mutation_id,
        "target_path": target_path,
        "pre_rollback_hash": current_hash,
        "restored_hash": "",
        "approval": operator_approved,
        "status": "NOT_COMPUTABLE",
        "failure_reason": reason,
        "post_validation": {
            "validator": "NOT_RUN",
            "operator_health": "NOT_RUN",
            "invariance": False,
        },
        "timestamp": time.time(),
        "commit": _get_commit(),
    }
    append_rollback_entry(entry)
    payload = {
        "schema_version": "SelfBuildRollbackResult.v1",
        "status": "NOT_COMPUTABLE",
        "reason": reason,
        "mutation_id": mutation_id,
    }
    payload["canonical_hash"] = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    payload["authority"] = {"mutation": False, "execution": False, "fail_closed": True}
    return payload


def run_self_build_rollback_executor(mutation_id: str, operator_approved: bool) -> dict[str, Any]:
    if not operator_approved:
        return _fail_result(mutation_id, "OPERATOR_APPROVAL_REQUIRED", operator_approved)

    ledger = _load_ledger()
    entry = next((item for item in ledger.get("entries", []) if item.get("mutation_id") == mutation_id), None)
    if entry is None:
        return _fail_result(mutation_id, "MUTATION_ID_NOT_FOUND", operator_approved)

    target_path = Path(entry["target_path"])
    current_hash = _sha256_text(target_path.read_text(encoding="utf-8")) if target_path.exists() else "NOT_FOUND"
    after_hash = entry.get("after_hash")
    before_hash = entry.get("before_hash")
    snapshot_ref = entry.get("before_snapshot", {}).get("payload_or_ref")
    snapshot_path = Path(snapshot_ref) if snapshot_ref else None

    if current_hash != after_hash:
        return _fail_result(mutation_id, "HASH_MISMATCH", operator_approved, str(target_path), current_hash)

    if snapshot_path is None or not snapshot_path.exists():
        return _fail_result(mutation_id, "MISSING_SNAPSHOT", operator_approved, str(target_path), current_hash)

    snapshot_content = snapshot_path.read_text(encoding="utf-8")
    snapshot_hash = _sha256_text(snapshot_content)
    if snapshot_hash != before_hash:
        return _fail_result(mutation_id, "SNAPSHOT_HASH_MISMATCH", operator_approved, str(target_path), current_hash)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(snapshot_content, encoding="utf-8")
    restored_hash = _sha256_text(target_path.read_text(encoding="utf-8"))

    validator = run_binding_validator()
    operator = run_operator_closure_card()
    invariance = run_invariance_harness()

    validator_status = validator["overall_status"]
    operator_health = operator["health"]
    invariance_flag = invariance["registry_invariant"] and invariance["validator_invariant"] and invariance["bundle_invariant"]

    rollback_entry = {
        "mutation_id": mutation_id,
        "target_path": str(target_path),
        "pre_rollback_hash": current_hash,
        "restored_hash": restored_hash,
        "approval": True,
        "status": "ROLLED_BACK",
        "failure_reason": None,
        "post_validation": {
            "validator": validator_status,
            "operator_health": operator_health,
            "invariance": invariance_flag,
        },
        "timestamp": time.time(),
        "commit": _get_commit(),
    }
    append_rollback_entry(rollback_entry)

    payload = {
        "schema_version": "SelfBuildRollbackResult.v1",
        "status": "ROLLED_BACK",
        "mutation_id": mutation_id,
        "target": str(target_path),
        "post_validation": {
            "validator": validator_status,
            "operator_health": operator_health,
            "invariance": invariance_flag,
        },
    }
    payload["canonical_hash"] = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    payload["authority"] = {"mutation": False, "execution": False, "operator_approval_required": True, "fail_closed": True}
    return payload
