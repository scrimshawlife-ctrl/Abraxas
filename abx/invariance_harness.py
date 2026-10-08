from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable

#: A per-call identifier such as `runtime_corridor.20261008t072642z` or
#: `pipeline_envelope.20261008t072642z`: a lower-case name, a dot, then a UTC stamp at
#: SECOND resolution. Operator console builds mint values like this from the clock on every
#: call (`webpanel/operator_console.py`), so the value can never be equal across two runs --
#: keeping it in an invariance comparison guarantees a spurious mismatch whenever a second
#: boundary is crossed. Measured 2026-10-08: CI failed on
#: `runtime_corridor.20261008t072642z` vs `runtime_corridor.20261008t072643z`, one second
#: apart, with nothing else different. Volatile KEYS are dropped by name above; this drops
#: the same volatility when it is embedded in a VALUE.
_LIVE_STAMP = re.compile(r"^[a-z_]+\.\d{8}t\d{6}z$")


@dataclass(frozen=True)
class InvarianceResultArtifact:
    artifact_type: str
    artifact_id: str
    target: str
    runs: int
    status: str
    baseline_hash: str
    mismatches: list[dict[str, Any]] = field(default_factory=list)
    normalization_rules: list[str] = field(default_factory=list)


def normalize_for_invariance(payload: Any) -> Any:
    """Canonical normalization rules for invariance checks.

    Rules:
    - sort dict keys recursively
    - remove volatile timestamp-ish keys
    - replace per-call clock-stamped identifiers embedded in values
    """

    volatile = {"timestamp", "ts", "checked_at", "generated_at_utc"}

    def _norm(value: Any) -> Any:
        if isinstance(value, dict):
            out = {}
            for key in sorted(value.keys()):
                if key in volatile:
                    continue
                out[key] = _norm(value[key])
            return out
        if isinstance(value, list):
            return [_norm(v) for v in value]
        if isinstance(value, str) and _LIVE_STAMP.match(value):
            return "<live-stamp>"
        return value

    return _norm(payload)


def run_invariance_harness(
    *,
    target: str,
    producer: Callable[[], Any],
    runs: int = 12,
) -> InvarianceResultArtifact:
    if runs <= 0:
        raise ValueError("runs must be > 0")

    normalized_outputs = [normalize_for_invariance(producer()) for _ in range(runs)]
    hashes = [sha256_bytes(dumps_stable(out).encode("utf-8")) for out in normalized_outputs]
    baseline = hashes[0]

    mismatches: list[dict[str, Any]] = []
    for idx, h in enumerate(hashes[1:], start=1):
        if h != baseline:
            mismatches.append(
                {
                    "run_index": idx,
                    "baseline_hash": baseline,
                    "observed_hash": h,
                    "classification": "logic_nondeterminism_or_ordering_drift",
                }
            )

    status = "VALID" if not mismatches else "BROKEN"
    return InvarianceResultArtifact(
        artifact_type="InvarianceResultArtifact.v1",
        artifact_id=f"invariance-{target}",
        target=target,
        runs=runs,
        status=status,
        baseline_hash=baseline,
        mismatches=mismatches,
        normalization_rules=[
            "drop volatile keys: timestamp, ts, checked_at, generated_at_utc",
            "replace per-call clock-stamped identifiers (name.<utc-stamp>) with <live-stamp>",
            "recursive deterministic key ordering",
        ],
    )
