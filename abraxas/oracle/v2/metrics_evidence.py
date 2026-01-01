from __future__ import annotations

import os
from typing import Any, Dict, Tuple


DEFAULT_EVIDENCE_BUDGET_BYTES = int(os.environ.get("ABX_EVIDENCE_BUDGET_BYTES", str(2_000_000)))  # 2MB default


def _safe_int(x: Any, default: int) -> int:
    try:
        v = int(x)
        return v if v >= 0 else default
    except Exception:
        return default


def evidence_total_bytes(envelope: Dict[str, Any]) -> int:
    """
    Sums sizes of evidence files referenced by envelope["oracle_signal"]["evidence"]["paths"].
    Only counts existing regular files.
    """
    sig = envelope.get("oracle_signal", {}) or {}
    ev = sig.get("evidence")
    if not isinstance(ev, dict):
        return 0
    paths = ev.get("paths")
    if not isinstance(paths, dict):
        return 0

    total = 0
    for _, p in paths.items():
        if isinstance(p, str) and p and os.path.exists(p) and os.path.isfile(p):
            try:
                total += int(os.path.getsize(p))
            except Exception:
                continue
    return total


def evidence_overflow_metrics(
    envelope: Dict[str, Any],
    *,
    budget_bytes: int | None = None,
) -> Dict[str, Any]:
    """
    Returns a deterministic metrics bundle:
      - total_evidence_bytes
      - budget_bytes
      - overflow_bytes
      - overflow_rate in [0..1] (overflow/budget) when budget>0 else 0.0
    """
    budget = _safe_int(budget_bytes if budget_bytes is not None else DEFAULT_EVIDENCE_BUDGET_BYTES, DEFAULT_EVIDENCE_BUDGET_BYTES)
    total = evidence_total_bytes(envelope)
    overflow = max(0, total - budget)
    if budget <= 0:
        rate = 0.0
    else:
        rate = float(overflow) / float(budget)
        # cap to 1.0 for compliance signal stability (overflow beyond 100% is still "maxed")
        rate = min(1.0, max(0.0, rate))
    return {
        "total_evidence_bytes": total,
        "budget_bytes": budget,
        "overflow_bytes": overflow,
        "overflow_rate": rate,
    }
