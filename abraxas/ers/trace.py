from __future__ import annotations

import json
import hashlib
from dataclasses import asdict
from typing import Any, Dict, List, Tuple

from .types import TraceEvent


def _to_primitive(x: Any) -> Any:
    """
    Convert to JSON-safe primitives deterministically.
    - Dict keys sorted.
    - Tuples -> lists.
    - Unknown objects -> repr(x) (deterministic within run; avoid if possible).
    """
    if x is None:
        return None
    if isinstance(x, (bool, int, float, str)):
        return x
    if isinstance(x, (list, tuple)):
        return [_to_primitive(v) for v in x]
    if isinstance(x, dict):
        return {str(k): _to_primitive(x[k]) for k in sorted(x.keys(), key=lambda z: str(z))}
    return repr(x)


def canonicalize_trace(trace: List[TraceEvent]) -> Dict[str, Any]:
    """
    Produce a deterministic, JSON-safe trace payload.
    """
    events: List[Dict[str, Any]] = []
    for e in trace:
        d = asdict(e)
        d = _to_primitive(d)
        events.append(d)
    # events are already in execution order; preserve as-is.
    return {"events": events}


def trace_json_bytes(trace: List[TraceEvent]) -> bytes:
    payload = canonicalize_trace(trace)
    # separators to ensure stable JSON bytes, sort_keys for deterministic dict ordering
    s = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def trace_hash_sha256(trace: List[TraceEvent]) -> str:
    b = trace_json_bytes(trace)
    return hashlib.sha256(b).hexdigest()
