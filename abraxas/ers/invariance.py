from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from .trace import canonicalize_trace, trace_hash_sha256
from .types import TraceEvent


@dataclass(frozen=True)
class InvarianceResult:
    ok: bool
    expected_hash: str
    hashes: List[str]
    first_mismatch_index: Optional[int] = None
    divergence: Optional[Dict[str, Any]] = None


def _first_divergence(a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i, {"a": a[i], "b": b[i]}
    if len(a) != len(b):
        return n, {"a": {"_len": len(a)}, "b": {"_len": len(b)}}
    return None, None


def dozen_run_invariance_gate(
    *,
    make_trace: Callable[[int], List[TraceEvent]],
    runs: int = 12,
) -> InvarianceResult:
    """
    Canonical invariance gate:
      - Run make_trace(i) for i in [0..runs-1]
      - Hash each canonicalized trace
      - PASS iff all hashes match

    make_trace must be deterministic given identical ambient state.
    """
    hashes: List[str] = []
    payloads: List[Dict[str, Any]] = []

    for i in range(runs):
        tr = make_trace(i)
        hashes.append(trace_hash_sha256(tr))
        payloads.append(canonicalize_trace(tr))

    expected = hashes[0]
    for idx, h in enumerate(hashes):
        if h != expected:
            # compute drift report vs baseline
            base_events = payloads[0]["events"]
            cur_events = payloads[idx]["events"]
            div_i, div = _first_divergence(base_events, cur_events)
            return InvarianceResult(
                ok=False,
                expected_hash=expected,
                hashes=hashes,
                first_mismatch_index=idx,
                divergence={"event_index": div_i, "diff": div},
            )

    return InvarianceResult(ok=True, expected_hash=expected, hashes=hashes)
