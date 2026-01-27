"""
InvarianceGate.v0 (v0.1.3)

Optional 12-run invariance harness.
Defaults to stub behavior unless explicitly enabled.
"""

from __future__ import annotations

from typing import Optional, Dict, Any


def invariance_gate(
    outputs: Optional[Dict[str, Any]] = None,
    *,
    enabled: bool = False,
    runtime: Any = None,
    context: Optional[Dict[str, Any]] = None,
    runs_required: int = 12,
) -> Dict[str, Any]:
    """
    If enabled=True and runtime+context are supplied, run the invariance harness.
    Otherwise return structured stub response.
    """
    if not enabled:
        return {
            "passed": False,
            "reason": "stub_not_implemented",
            "runs_required": 12,
        }

    if runtime is None or context is None:
        return {
            "passed": False,
            "reason": "missing_runtime_or_context",
            "runs_required": runs_required,
        }

    from abx_familiar.governance.invariance_harness import run_invariance_harness

    report = run_invariance_harness(
        runtime=runtime,
        context=context,
        runs_required=runs_required,
        artifact_keys=["task_graph", "delivery_pack", "ledger_entry"],
    )

    return {
        "passed": report.passed,
        "reason": report.reason,
        "runs_required": report.runs_required,
        "reference_hashes": report.reference_hashes,
        "mismatches": report.mismatches,
    }
