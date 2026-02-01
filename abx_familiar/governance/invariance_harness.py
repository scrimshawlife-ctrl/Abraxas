"""
Invariance Harness (v0.1).

Runs the runtime N times on identical inputs and checks that selected artifact
hashes remain invariant.

No external IO.
No adapters.
Deterministic given deterministic runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass(frozen=True)
class InvarianceRunResult:
    run_index: int
    hashes: Dict[str, Optional[str]]  # e.g., {"task_graph": "...", "delivery_pack": "..."}


@dataclass(frozen=True)
class InvarianceReport:
    passed: bool
    runs_required: int
    reason: str
    reference_hashes: Dict[str, Optional[str]] = field(default_factory=dict)
    mismatches: List[Dict[str, Any]] = field(default_factory=list)
    runs: List[InvarianceRunResult] = field(default_factory=list)


def _extract_hashes(artifacts: Dict[str, Any], keys: List[str]) -> Dict[str, Optional[str]]:
    out: Dict[str, Optional[str]] = {}
    for k in keys:
        obj = artifacts.get(k)
        if obj is None:
            out[k] = None
            continue
        # If hash() exists, use it; else None
        h = getattr(obj, "hash", None)
        out[k] = h() if callable(h) else None
    return out


def run_invariance_harness(
    *,
    runtime: Any,
    context: Dict[str, Any],
    runs_required: int = 12,
    artifact_keys: Optional[List[str]] = None,
) -> InvarianceReport:
    """
    Execute `runtime.execute(context)` runs_required times and check invariance.
    """
    if runs_required <= 0:
        return InvarianceReport(
            passed=False,
            runs_required=runs_required,
            reason="invalid_runs_required",
        )

    keys = artifact_keys or ["task_graph", "delivery_pack", "ledger_entry"]

    reference_hashes: Optional[Dict[str, Optional[str]]] = None
    results: List[InvarianceRunResult] = []
    mismatches: List[Dict[str, Any]] = []

    for i in range(runs_required):
        # IMPORTANT: context is treated as immutable by policy; if callers mutate it,
        # invariance failure is correct.
        artifacts = runtime.execute(context)
        hashes = _extract_hashes(artifacts, keys)
        results.append(InvarianceRunResult(run_index=i, hashes=hashes))

        if reference_hashes is None:
            reference_hashes = hashes
            continue

        # Compare strictly
        for k in keys:
            if reference_hashes.get(k) != hashes.get(k):
                mismatches.append(
                    {
                        "run_index": i,
                        "key": k,
                        "expected": reference_hashes.get(k),
                        "got": hashes.get(k),
                    }
                )

    if reference_hashes is None:
        return InvarianceReport(
            passed=False,
            runs_required=runs_required,
            reason="no_runs_executed",
        )

    if mismatches:
        return InvarianceReport(
            passed=False,
            runs_required=runs_required,
            reason="hash_mismatch",
            reference_hashes=reference_hashes,
            mismatches=mismatches,
            runs=results,
        )

    return InvarianceReport(
        passed=True,
        runs_required=runs_required,
        reason="hash_equal",
        reference_hashes=reference_hashes,
        mismatches=[],
        runs=results,
    )
