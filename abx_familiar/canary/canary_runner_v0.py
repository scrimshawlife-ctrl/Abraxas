"""
CANARY runner (v0.1.x)

Runs the invariance harness in a "pure mode" configuration:
- ledger disabled (avoid time-dependent hashes)
- stabilization disabled
- fixed context
"""

from __future__ import annotations

from typing import Dict, Any

from abx_familiar.runtime.familiar_runtime import FamiliarRuntime
from abx_familiar.governance.invariance_harness import run_invariance_harness


def run_canary(runs_required: int = 12) -> Dict[str, Any]:
    rt = FamiliarRuntime()  # no ledger store for pure invariance

    ctx = {
        "run_id": "canary",
        "summoner": {
            "task_id": "t_canary",
            "tier_scope": "Academic",
            "mode": "Analyst",
            "requested_ops": [],
            "constraints": {"canary": True},
        },
        # Explicitly do NOT enable stabilization here.
        "stabilization_enabled": False,
        "stabilization_window_size": 0,
    }

    report = run_invariance_harness(runtime=rt, context=ctx, runs_required=runs_required)
    return {
        "passed": report.passed,
        "reason": report.reason,
        "runs_required": report.runs_required,
        "reference_hashes": report.reference_hashes,
        "mismatches": report.mismatches,
    }
