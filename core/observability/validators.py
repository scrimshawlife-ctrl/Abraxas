"""Lineage replay validator.

validate_lineage_replay: validates that a lineage trace is stable with
respect to a replay packet. Fail-closed on:
- cyclic lineage
- missing parent references
- replay mismatches
"""
from __future__ import annotations

from typing import Optional

from core.observability.lineage import LineageTracePacket, _detect_cycles, _validate_parents
from core.observability.replay_metrics import ReplayTelemetryPacket


GATE_PASS = "pass"
GATE_FAIL = "fail"


class ValidationResult:
    """Result of a validator gate."""

    def __init__(
        self,
        *,
        gate: str,
        result: str,
        reason: str,
        details: Optional[dict] = None,
    ) -> None:
        self.gate = gate
        self.result = result
        self.reason = reason
        self.details = details or {}

    @property
    def passed(self) -> bool:
        return self.result == GATE_PASS

    def to_dict(self) -> dict:
        return {
            "gate": self.gate,
            "result": self.result,
            "reason": self.reason,
            "details": self.details,
        }


def validate_lineage_replay(
    trace: LineageTracePacket,
    replay_packet: ReplayTelemetryPacket,
) -> ValidationResult:
    """Validate that a lineage trace is deterministic and replay-consistent.

    Rules (all fail-closed):
    1. Cyclic lineage => FAIL
    2. Missing parent references => FAIL
    3. Replay mismatch in replay_packet => FAIL (lineage stability invalidated)
    4. Trace execution_hash must match replay_packet replay_hash (same run)
    """
    gate = "lineage_replay_validator"

    # Rule 1: cyclic lineage
    if _detect_cycles(trace.nodes):
        return ValidationResult(
            gate=gate,
            result=GATE_FAIL,
            reason="cyclic lineage detected — lineage trace is invalid",
            details={"trace_id": trace.trace_id, "violation": "cyclic_lineage"},
        )

    # Rule 2: missing parents
    missing_msg = _validate_parents(trace.nodes)
    if missing_msg:
        return ValidationResult(
            gate=gate,
            result=GATE_FAIL,
            reason=f"missing parent reference: {missing_msg}",
            details={"trace_id": trace.trace_id, "violation": "missing_parent"},
        )

    # Rule 3: replay mismatch invalidates lineage stability
    if not replay_packet.deterministic_match:
        return ValidationResult(
            gate=gate,
            result=GATE_FAIL,
            reason=(
                "replay telemetry shows mismatch — lineage stability invalidated; "
                f"mismatched_receipts={replay_packet.mismatched_receipts}"
            ),
            details={
                "trace_id": trace.trace_id,
                "violation": "replay_mismatch",
                "mismatched_receipts": replay_packet.mismatched_receipts,
            },
        )

    # Rule 4: execution hash alignment
    if trace.execution_hash != replay_packet.replay_hash:
        return ValidationResult(
            gate=gate,
            result=GATE_FAIL,
            reason=(
                f"execution_hash mismatch: trace.execution_hash={trace.execution_hash!r} "
                f"vs replay_packet.replay_hash={replay_packet.replay_hash!r}"
            ),
            details={
                "trace_id": trace.trace_id,
                "violation": "execution_hash_mismatch",
                "trace_execution_hash": trace.execution_hash,
                "replay_hash": replay_packet.replay_hash,
            },
        )

    return ValidationResult(
        gate=gate,
        result=GATE_PASS,
        reason="lineage deterministic and replay consistent",
        details={
            "trace_id": trace.trace_id,
            "lineage_depth": trace.lineage_depth,
            "node_count": len(trace.nodes),
        },
    )


# ── Doctrine validator gate extensions ─────────────────────────────────────


def observability_gate(telemetry_packet) -> ValidationResult:
    """Gate: telemetry must be deterministic (deterministic_match=True)."""
    gate = "observability_gate"
    if not telemetry_packet.deterministic_match:
        return ValidationResult(
            gate=gate,
            result=GATE_FAIL,
            reason="telemetry is non-deterministic (deterministic_match=False)",
            details={"telemetry_id": telemetry_packet.telemetry_id},
        )
    return ValidationResult(
        gate=gate,
        result=GATE_PASS,
        reason="telemetry deterministic",
    )


def lineage_gate(trace: LineageTracePacket) -> ValidationResult:
    """Gate: lineage trace must be valid."""
    gate = "lineage_gate"
    if trace.status != "valid":
        return ValidationResult(
            gate=gate,
            result=GATE_FAIL,
            reason=f"lineage trace invalid: status={trace.status!r}",
            details={"trace_id": trace.trace_id, "status": trace.status},
        )
    return ValidationResult(gate=gate, result=GATE_PASS, reason="lineage valid")


def telemetry_gate(telemetry_packet) -> ValidationResult:
    """Gate: telemetry packet must have status 'valid'."""
    gate = "telemetry_gate"
    if telemetry_packet.status not in ("valid",):
        return ValidationResult(
            gate=gate,
            result=GATE_FAIL,
            reason=f"telemetry status not valid: {telemetry_packet.status!r}",
        )
    return ValidationResult(gate=gate, result=GATE_PASS, reason="telemetry valid")


def stabilization_gate(stab: "StabilizationTelemetry") -> ValidationResult:  # type: ignore[name-defined]
    """Gate: stabilization must not be 'unstable' or 'failed'."""
    gate = "stabilization_gate"
    if stab.stabilization_state in ("unstable", "failed"):
        return ValidationResult(
            gate=gate,
            result=GATE_FAIL,
            reason=f"stabilization is {stab.stabilization_state!r}",
            details={"stabilization_id": stab.stabilization_id},
        )
    return ValidationResult(
        gate=gate,
        result=GATE_PASS,
        reason=f"stabilization state acceptable: {stab.stabilization_state!r}",
    )


def projection_snapshot_gate(snapshot) -> ValidationResult:
    """Gate: projection snapshot must have projection_only=True and inference_authority=False."""
    gate = "projection_snapshot_gate"
    if not snapshot.projection_only:
        return ValidationResult(
            gate=gate,
            result=GATE_FAIL,
            reason="projection_only is False — authority leak detected",
            details={"snapshot_id": snapshot.snapshot_id},
        )
    if snapshot.inference_authority:
        return ValidationResult(
            gate=gate,
            result=GATE_FAIL,
            reason="inference_authority is True — authority leak detected",
            details={"snapshot_id": snapshot.snapshot_id},
        )
    return ValidationResult(
        gate=gate,
        result=GATE_PASS,
        reason="projection snapshot authority clean",
    )


def run_all_doctrine_gates(
    telemetry_packet,
    trace: LineageTracePacket,
    stab,
    snapshot,
) -> list:
    """Run all doctrine validator gates and return list of ValidationResult."""
    results = [
        observability_gate(telemetry_packet),
        lineage_gate(trace),
        telemetry_gate(telemetry_packet),
        stabilization_gate(stab),
        projection_snapshot_gate(snapshot),
    ]
    return results
