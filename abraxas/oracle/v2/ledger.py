from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict


def _iso_z_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def append_stabilization_row(
    *,
    path: str,
    v2_block: Dict[str, Any],
    day: int,
    date_iso: str | None = None,
) -> Dict[str, Any]:
    """
    Append-only JSONL ledger row for v2 stabilization.
    Deterministic: stable keys, ISO8601 Z timestamps.
    """
    md = v2_block.get("mode_decision") or {}
    compliance = v2_block.get("compliance") or {}
    checks = compliance.get("checks") or {}

    row: Dict[str, Any] = {
        "date_iso": date_iso or _iso_z_now(),
        "day": int(day),
        "mode": v2_block.get("mode"),
        "mode_decision_fingerprint": md.get("fingerprint"),
        "compliance_status": compliance.get("status"),
        "checks": {
            "v1_golden_pass_rate": checks.get("v1_golden_pass_rate"),
            "drift_budget_violations": checks.get("drift_budget_violations"),
            "evidence_bundle_overflow_rate": checks.get("evidence_bundle_overflow_rate"),
            "ci_volatility_correlation": checks.get("ci_volatility_correlation"),
            "interaction_noise_rate": checks.get("interaction_noise_rate"),
        },
        "provenance": {
            "config_hash": (compliance.get("provenance") or {}).get("config_hash")
        },
    }

    os.makedirs(os.path.dirname(path), exist_ok=True)
    line = json.dumps(row, sort_keys=True, separators=(",", ":"))
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    return row
