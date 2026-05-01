from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

from abraxas.viz.interaction_policy_ledger_models import AUTHORITY, sha256_json


def evaluate_promotion(policy: Dict[str, Any], manifest: Dict[str, Any]) -> Dict[str, str]:
    try:
        if policy.get("authority", {}).get("interaction_runtime") is not False:
            return {"status": "blocked", "reason": "runtime_enabled"}
        allowed = set(policy.get("allowed_future_interactions", []))
        forbidden = set(policy.get("forbidden_interactions", []))
        if allowed.intersection(forbidden):
            return {"status": "blocked", "reason": "overlap_detected"}
        if "package-lock.json" not in (manifest.get("files") or {}):
            return {"status": "blocked", "reason": "missing_lockfile"}
        return {"status": "review_ready", "reason": "policy_and_harness_verified"}
    except Exception:
        return {"status": "not_computable", "reason": "policy_evaluation_error"}


def build_drift_hooks(policy: Dict[str, Any]) -> List[str]:
    _ = policy
    return [
        "forbidden_runtime_api_scan",
        "policy_overlap_scan",
        "authority_regression_scan",
        "frontend_lockfile_presence_scan",
        "component_source_hash_change_scan",
    ]


def compute_entry(policy: Dict[str, Any], harness_manifest: Dict[str, Any]) -> Dict[str, Any]:
    base = {
        "policy_id": policy["policy_id"],
        "policy_hash": policy["policy_hash"],
        "harness_manifest_hash": harness_manifest["manifest_hash"],
    }
    entry_id = sha256_json(base)
    promotion_status = evaluate_promotion(policy, harness_manifest)
    drift_hooks = build_drift_hooks(policy)
    entry = {
        "entry_id": entry_id,
        "policy": deepcopy(policy),
        "harness_manifest_hash": harness_manifest["manifest_hash"],
        "promotion_status": promotion_status,
        "drift_hooks": drift_hooks,
        "authority": dict(AUTHORITY),
    }
    entry["entry_hash"] = sha256_json(entry)
    return entry


def build_ledger(policy: Dict[str, Any], manifest: Dict[str, Any], prior: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    new_entry = compute_entry(policy, manifest)
    entries: List[Dict[str, Any]] = []
    if prior:
        entries.extend(deepcopy(prior.get("entries", [])))
    if not any(e.get("entry_id") == new_entry["entry_id"] for e in entries):
        entries.append(new_entry)
    entries = sorted(entries, key=lambda x: str(x.get("entry_id", "")))
    run = {
        "type": "AALVizInteractionPolicyLedgerRun.v1",
        "entries": entries,
        "count": len(entries),
        "authority": dict(AUTHORITY),
    }
    run["run_hash"] = sha256_json(run)
    return run
