"""Doctrine validator with rune-layer gates.

Extends baseline governance validation with four new gates for the
v2.0.1-rune-layer:
  - execution_plan_gate
  - execution_receipt_gate
  - replayability_gate
  - rollback_gate

A pipeline cannot be fully compliant if any of these gates fail.
All execution remains shadow-only, replayable, receipt-backed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from typing import Any, Dict, List, Optional
import json


class GateStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NOT_COMPUTABLE = "not_computable"


@dataclass
class GateResult:
    gate_id: str
    status: GateStatus
    reason: str
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DoctrineValidationResult:
    schema_version: str = "DoctrineValidationResult.v1"
    pipeline_id: str = ""
    fully_compliant: bool = False
    gates: List[GateResult] = field(default_factory=list)
    blocking_gates: List[str] = field(default_factory=list)
    result_hash: str = ""

    def compute_hash(self) -> str:
        canonical = json.dumps(
            {
                "pipeline_id": self.pipeline_id,
                "fully_compliant": self.fully_compliant,
                "gates": [
                    {"gate_id": g.gate_id, "status": g.status.value, "reason": g.reason}
                    for g in self.gates
                ],
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def _execution_plan_gate(evidence: Dict[str, Any]) -> GateResult:
    """Gate: pipeline must have a valid invocation plan."""
    invocation_plan = evidence.get("invocation_plan")
    if invocation_plan is None:
        return GateResult(
            gate_id="execution_plan_gate",
            status=GateStatus.FAIL,
            reason="No invocation plan present. Pipeline cannot be compliant.",
        )
    steps = invocation_plan.get("steps", [])
    if not steps:
        return GateResult(
            gate_id="execution_plan_gate",
            status=GateStatus.FAIL,
            reason="Invocation plan has no steps.",
        )
    orders = [s.get("deterministic_order", -1) for s in steps]
    if len(set(orders)) != len(orders):
        return GateResult(
            gate_id="execution_plan_gate",
            status=GateStatus.FAIL,
            reason="Invocation plan has duplicate deterministic_order values.",
        )
    return GateResult(
        gate_id="execution_plan_gate",
        status=GateStatus.PASS,
        reason=f"Invocation plan valid with {len(steps)} step(s).",
        evidence={"step_count": len(steps)},
    )


def _execution_receipt_gate(evidence: Dict[str, Any]) -> GateResult:
    """Gate: pipeline must have a valid receipt chain."""
    receipt_chain = evidence.get("receipt_chain")
    if receipt_chain is None:
        return GateResult(
            gate_id="execution_receipt_gate",
            status=GateStatus.FAIL,
            reason="No receipt chain present. Pipeline cannot be compliant.",
        )
    chain_hash = receipt_chain.get("chain_hash", "")
    receipt_count = receipt_chain.get("receipt_count", 0)
    if not chain_hash or len(chain_hash) != 64:
        return GateResult(
            gate_id="execution_receipt_gate",
            status=GateStatus.FAIL,
            reason=f"Receipt chain hash invalid: '{chain_hash}'",
        )
    if receipt_count == 0:
        return GateResult(
            gate_id="execution_receipt_gate",
            status=GateStatus.FAIL,
            reason="Receipt chain is empty.",
        )
    return GateResult(
        gate_id="execution_receipt_gate",
        status=GateStatus.PASS,
        reason=f"Receipt chain valid. {receipt_count} receipt(s), hash={chain_hash[:8]}...",
        evidence={"receipt_count": receipt_count, "chain_hash": chain_hash},
    )


def _replayability_gate(evidence: Dict[str, Any]) -> GateResult:
    """Gate: pipeline must have a replay packet showing deterministic match."""
    replay_packet = evidence.get("replay_packet")
    if replay_packet is None:
        return GateResult(
            gate_id="replayability_gate",
            status=GateStatus.FAIL,
            reason="No replay packet present. Pipeline cannot be fully compliant.",
        )
    deterministic_match = replay_packet.get("deterministic_match", False)
    if not deterministic_match:
        mismatched = replay_packet.get("mismatched_receipts", [])
        return GateResult(
            gate_id="replayability_gate",
            status=GateStatus.FAIL,
            reason=f"Replay did not produce deterministic match. Mismatched: {mismatched}",
            evidence={"mismatched_receipts": mismatched},
        )
    return GateResult(
        gate_id="replayability_gate",
        status=GateStatus.PASS,
        reason="Replay packet confirms deterministic match.",
        evidence={"deterministic_match": True},
    )


def _rollback_gate(evidence: Dict[str, Any]) -> GateResult:
    """Gate: pipeline must have a valid rollback packet."""
    rollback_packet = evidence.get("rollback_packet")
    if rollback_packet is None:
        return GateResult(
            gate_id="rollback_gate",
            status=GateStatus.FAIL,
            reason="No rollback packet present. Pipeline cannot be fully compliant.",
        )
    # Check that rollback_id is present
    rollback_id = rollback_packet.get("rollback_id", "")
    if not rollback_id:
        return GateResult(
            gate_id="rollback_gate",
            status=GateStatus.FAIL,
            reason="Rollback packet missing rollback_id.",
        )
    return GateResult(
        gate_id="rollback_gate",
        status=GateStatus.PASS,
        reason="Rollback packet valid.",
        evidence={
            "rollback_possible": rollback_packet.get("rollback_possible", False),
            "rollback_id": rollback_id[:8] + "...",
        },
    )


# ── v2.0.6 Oracle Intake Gate Functions ──────────────────────────────────

def _intake_envelope_gate(evidence: Dict[str, Any]) -> GateResult:
    """Gate: intake run must have at least one intake envelope."""
    intake_run = evidence.get("intake_run")
    if intake_run is None:
        return GateResult(
            gate_id="intake_envelope_gate",
            status=GateStatus.PASS,
            reason="No intake_run present (oracle intake not required for this pipeline).",
        )
    envelopes = intake_run.get("intake_envelopes", [])
    if not envelopes:
        return GateResult(
            gate_id="intake_envelope_gate",
            status=GateStatus.FAIL,
            reason="intake_run present but has no intake_envelopes.",
        )
    blocked = [e for e in envelopes if e.get("intake_status") in {"conflict_detected", "rejected"}]
    if blocked:
        return GateResult(
            gate_id="intake_envelope_gate",
            status=GateStatus.FAIL,
            reason=f"{len(blocked)} envelope(s) in blocked status.",
            evidence={"blocked_count": len(blocked)},
        )
    return GateResult(
        gate_id="intake_envelope_gate",
        status=GateStatus.PASS,
        reason=f"Intake envelopes valid: {len(envelopes)} envelope(s).",
        evidence={"envelope_count": len(envelopes)},
    )


def _intake_replay_gate(evidence: Dict[str, Any]) -> GateResult:
    """Gate: all replay packets must show deterministic match."""
    intake_run = evidence.get("intake_run")
    if intake_run is None:
        return GateResult(
            gate_id="intake_replay_gate",
            status=GateStatus.PASS,
            reason="No intake_run present (oracle intake not required).",
        )
    replay_pkts = intake_run.get("replay_packets", [])
    if not replay_pkts:
        return GateResult(
            gate_id="intake_replay_gate",
            status=GateStatus.FAIL,
            reason="intake_run present but has no replay packets.",
        )
    mismatched = [p for p in replay_pkts if not p.get("deterministic_match", False)]
    if mismatched:
        return GateResult(
            gate_id="intake_replay_gate",
            status=GateStatus.FAIL,
            reason=f"Replay mismatch: {len(mismatched)} packet(s) failed deterministic match.",
            evidence={"mismatched_count": len(mismatched)},
        )
    return GateResult(
        gate_id="intake_replay_gate",
        status=GateStatus.PASS,
        reason=f"All {len(replay_pkts)} replay packet(s) matched deterministically.",
        evidence={"replay_count": len(replay_pkts)},
    )


def _intake_conflict_gate(evidence: Dict[str, Any]) -> GateResult:
    """Gate: no unresolved conflicts may remain."""
    intake_run = evidence.get("intake_run")
    if intake_run is None:
        return GateResult(
            gate_id="intake_conflict_gate",
            status=GateStatus.PASS,
            reason="No intake_run present (oracle intake not required).",
        )
    conflict_pkts = intake_run.get("conflict_packets", [])
    unresolved = [c for c in conflict_pkts if c.get("status") == "unresolved"]
    if unresolved:
        return GateResult(
            gate_id="intake_conflict_gate",
            status=GateStatus.FAIL,
            reason=f"Unresolved conflicts: {len(unresolved)} conflict(s) block compliance.",
            evidence={"unresolved_count": len(unresolved)},
        )
    return GateResult(
        gate_id="intake_conflict_gate",
        status=GateStatus.PASS,
        reason=f"No unresolved conflicts. Total: {len(conflict_pkts)}.",
        evidence={"conflict_count": len(conflict_pkts)},
    )


def _intake_lineage_gate(evidence: Dict[str, Any]) -> GateResult:
    """Gate: intake lineage must not be cyclic."""
    intake_lineage = evidence.get("intake_lineage")
    if intake_lineage is None:
        return GateResult(
            gate_id="intake_lineage_gate",
            status=GateStatus.PASS,
            reason="No intake_lineage present (not required for compliance).",
        )
    status = intake_lineage.get("status", "")
    if status == "cyclic":
        return GateResult(
            gate_id="intake_lineage_gate",
            status=GateStatus.FAIL,
            reason="Cyclic lineage detected. Intake lineage gate fails closed.",
        )
    if status == "invalid":
        return GateResult(
            gate_id="intake_lineage_gate",
            status=GateStatus.FAIL,
            reason="Invalid parent references in intake lineage.",
        )
    return GateResult(
        gate_id="intake_lineage_gate",
        status=GateStatus.PASS,
        reason=f"Intake lineage valid: status={status}.",
        evidence={"lineage_status": status},
    )


def _intake_stabilization_gate(evidence: Dict[str, Any]) -> GateResult:
    """Gate: stabilization packets must not all be failed/conflicted."""
    intake_run = evidence.get("intake_run")
    if intake_run is None:
        return GateResult(
            gate_id="intake_stabilization_gate",
            status=GateStatus.PASS,
            reason="No intake_run present (oracle intake not required).",
        )
    stab_pkts = intake_run.get("stabilization_packets", [])
    if not stab_pkts:
        return GateResult(
            gate_id="intake_stabilization_gate",
            status=GateStatus.FAIL,
            reason="intake_run present but has no stabilization packets.",
        )
    failed_or_conflicted = [
        p for p in stab_pkts if p.get("stabilization_state") in {"failed", "conflicted"}
    ]
    if len(failed_or_conflicted) == len(stab_pkts):
        return GateResult(
            gate_id="intake_stabilization_gate",
            status=GateStatus.FAIL,
            reason="All stabilization packets are failed or conflicted.",
            evidence={"failed_count": len(failed_or_conflicted)},
        )
    return GateResult(
        gate_id="intake_stabilization_gate",
        status=GateStatus.PASS,
        reason=f"Stabilization packets present: {len(stab_pkts)}.",
        evidence={"stabilization_count": len(stab_pkts)},
    )


def _intake_approval_gate(evidence: Dict[str, Any]) -> GateResult:
    """Gate: no approval bypass attempted."""
    intake_run = evidence.get("intake_run")
    if intake_run is None:
        return GateResult(
            gate_id="intake_approval_gate",
            status=GateStatus.PASS,
            reason="No intake_run present (oracle intake not required).",
        )
    approval_pkts = intake_run.get("approval_packets", [])
    if not approval_pkts:
        return GateResult(
            gate_id="intake_approval_gate",
            status=GateStatus.FAIL,
            reason="intake_run present but has no approval packets.",
        )
    bypassed = [
        a for a in approval_pkts
        if a.get("approved", False) and a.get("conflict_hashes")
    ]
    if bypassed:
        return GateResult(
            gate_id="intake_approval_gate",
            status=GateStatus.FAIL,
            reason=f"Approval bypass detected: {len(bypassed)} packet(s) approved with conflicts.",
            evidence={"bypass_count": len(bypassed)},
        )
    return GateResult(
        gate_id="intake_approval_gate",
        status=GateStatus.PASS,
        reason=f"Approval gate satisfied: {len(approval_pkts)} packet(s).",
        evidence={"approval_count": len(approval_pkts)},
    )


# Registry of all gates for this layer
_GATE_FUNCTIONS = [
    _execution_plan_gate,
    _execution_receipt_gate,
    _replayability_gate,
    _rollback_gate,
    # v2.0.6 intake gates
    _intake_envelope_gate,
    _intake_replay_gate,
    _intake_conflict_gate,
    _intake_lineage_gate,
    _intake_stabilization_gate,
    _intake_approval_gate,
]


def validate_pipeline_doctrine(pipeline_id: str, evidence: Dict[str, Any]) -> DoctrineValidationResult:
    """Run all doctrine gates for a pipeline and return the validation result.

    Args:
        pipeline_id: Identifier for the pipeline under validation.
        evidence: Dict containing:
            - invocation_plan: RuneInvocationPlan dict (or None)
            - receipt_chain: build_receipt_chain output dict (or None)
            - replay_packet: RuneReplayPacket dict (or None)
            - rollback_packet: ExecutionRollbackPacket dict (or None)

    Returns:
        DoctrineValidationResult with per-gate status and overall compliance.
    """
    gates: List[GateResult] = []
    blocking: List[str] = []

    for gate_fn in _GATE_FUNCTIONS:
        result = gate_fn(evidence)
        gates.append(result)
        if result.status != GateStatus.PASS:
            blocking.append(result.gate_id)

    fully_compliant = len(blocking) == 0

    validation = DoctrineValidationResult(
        pipeline_id=pipeline_id,
        fully_compliant=fully_compliant,
        gates=gates,
        blocking_gates=blocking,
    )
    validation.result_hash = validation.compute_hash()
    return validation


def doctrine_result_to_dict(result: DoctrineValidationResult) -> Dict[str, Any]:
    """Serialize a DoctrineValidationResult to a plain dict."""
    return {
        "schema_version": result.schema_version,
        "pipeline_id": result.pipeline_id,
        "fully_compliant": result.fully_compliant,
        "blocking_gates": result.blocking_gates,
        "result_hash": result.result_hash,
        "gates": [
            {
                "gate_id": g.gate_id,
                "status": g.status.value,
                "reason": g.reason,
                "evidence": g.evidence,
            }
            for g in result.gates
        ],
    }
