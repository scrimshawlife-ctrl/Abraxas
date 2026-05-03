from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _hash(obj: Any) -> str:
    return hashlib.sha256(_canonical(obj).encode()).hexdigest()


def build_readiness_policy_trends() -> dict[str, Any]:
    ledger_path = Path("out/registry/readiness_policy_ledger.latest.json")
    if not ledger_path.exists():
        payload = {
            "schema_version": "ReadinessPolicyTrends.v1",
            "status": "NOT_COMPUTABLE",
            "reason": "MISSING_POLICY_LEDGER",
            "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
        }
        payload["canonical_hash"] = _hash(payload)
        return payload

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    entries = ledger.get("entries", []) if isinstance(ledger, dict) else []
    if not isinstance(entries, list):
        entries = []

    policy_hashes = [e.get("policy_hash") for e in entries if isinstance(e, dict) and e.get("policy_hash")]
    hash_changes = 0
    for i in range(1, len(policy_hashes)):
        if policy_hashes[i] != policy_hashes[i - 1]:
            hash_changes += 1

    status_by_policy: dict[str, set[str]] = {}
    blocker_count: dict[str, int] = {}
    for e in entries:
        if not isinstance(e, dict):
            continue
        ph = str(e.get("policy_hash", ""))
        rs = str(e.get("readiness_status", "UNKNOWN"))
        if ph:
            status_by_policy.setdefault(ph, set()).add(rs)
        for b in e.get("blockers", []) if isinstance(e.get("blockers"), list) else []:
            blocker_count[str(b)] = blocker_count.get(str(b), 0) + 1

    persistent_blockers = sorted([k for k, v in blocker_count.items() if v >= 3])
    top_blockers = sorted(blocker_count.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    drift_under_same_policy = sorted([p for p, statuses in status_by_policy.items() if len(statuses) > 1])

    payload = {
        "schema_version": "ReadinessPolicyTrends.v1",
        "status": "TRENDS_READY",
        "entry_count": len(entries),
        "policy_hash_changes": hash_changes,
        "readiness_status_drift_under_same_policy": drift_under_same_policy,
        "persistent_blockers": persistent_blockers,
        "blocker_frequency_patterns": [{"blocker": b, "count": c} for b, c in top_blockers],
        "policy_vs_state_causality": {
            "policy_change_events": hash_changes,
            "status_variants_by_policy": {k: sorted(v) for k, v in status_by_policy.items()},
        },
        "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
    }
    payload["canonical_hash"] = _hash(payload)
    return payload
