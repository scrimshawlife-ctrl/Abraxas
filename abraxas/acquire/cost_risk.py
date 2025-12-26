from __future__ import annotations

from typing import Any, Dict


def estimate_cost(
    action_kind: str,
    cadence_hint: str | None,
    base_event_budget: int = 500,
) -> Dict[str, Any]:
    cadence_mult = 1
    if cadence_hint == "weekly":
        cadence_mult = 2
    elif cadence_hint == "daily":
        cadence_mult = 1
    elif cadence_hint == "manual":
        cadence_mult = 0
    return {
        "event_budget": int(base_event_budget * cadence_mult),
        "cpu_ms_est": int(50 * cadence_mult),
    }


def estimate_risk(gap_kind: str, action_kind: str) -> Dict[str, Any]:
    ssi_exposure = 0.2
    quarantine_likelihood = 0.3 if action_kind == "ONLINE_FETCH" else 0.05

    if gap_kind == "INTEGRITY_GAP":
        ssi_exposure = 0.6
        quarantine_likelihood = 0.5 if action_kind == "ONLINE_FETCH" else 0.1

    return {
        "ssi_exposure_est": float(ssi_exposure),
        "quarantine_likelihood_est": float(quarantine_likelihood),
    }
