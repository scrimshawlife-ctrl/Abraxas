"""
Policy loader (v0 stub).

Reads policy snapshot from an explicit dict (already loaded by caller),
or returns deterministic defaults.

No file IO here. No env reads. No hidden coupling.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from abx_familiar.policy.policy_snapshot_v0 import PolicySnapshot


def load_policy_snapshot_from_dict(data: Optional[Dict[str, Any]] = None) -> PolicySnapshot:
    if data is None:
        snap = PolicySnapshot(snapshot_id="default.v0")
        snap.validate()
        return snap

    # Strict: only known keys are used; unknown keys are retained in meta for audit.
    known = {
        "snapshot_id",
        "invariance_enabled",
        "invariance_runs_required",
        "stabilization_enabled_default",
        "stabilization_window_size_default",
        "allowed_tiers",
        "allowed_modes",
        "coupling_map_ref",
        "meta",
        "not_computable",
        "missing_fields",
    }

    meta = dict(data.get("meta") or {})
    for k in data.keys():
        if k not in known:
            meta[f"unknown:{k}"] = data[k]

    snap = PolicySnapshot(
        snapshot_id=str(data.get("snapshot_id", "dict.v0")),
        invariance_enabled=bool(data.get("invariance_enabled", False)),
        invariance_runs_required=int(data.get("invariance_runs_required", 12)),
        stabilization_enabled_default=bool(data.get("stabilization_enabled_default", False)),
        stabilization_window_size_default=int(data.get("stabilization_window_size_default", 0)),
        allowed_tiers=list(data.get("allowed_tiers") or ["Psychonaut", "Academic", "Enterprise"]),
        allowed_modes=list(data.get("allowed_modes") or ["Oracle", "Ritual", "Analyst"]),
        coupling_map_ref=data.get("coupling_map_ref"),
        meta=meta,
        not_computable=bool(data.get("not_computable", False)),
        missing_fields=list(data.get("missing_fields") or []),
    )
    snap.validate()
    return snap
