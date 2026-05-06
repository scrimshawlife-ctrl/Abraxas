"""Adaptive sandbox validators.

Implements:
- validate_adaptive_replay()
- Doctrine validator extension gates:
    - sandbox_branch_gate
    - adaptive_replay_gate
    - adaptive_stabilization_gate
    - promotion_candidate_gate
    - mutation_receipt_gate

Rules:
- replay mismatch invalidates promotion
- unstable stabilization blocks promotion
- cyclic lineage fail closed
- operator review required for all promotion candidates
- authority leak detected
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, Dict

from core.sandbox.models import AdaptiveSandboxBranch
from core.sandbox.replay import SandboxReplayPacket
from core.validators.doctrine import GateResult, GateStatus


def validate_adaptive_replay(
    branch: AdaptiveSandboxBranch,
    replay_packet: SandboxReplayPacket,
) -> Dict[str, Any]:
    """Validate adaptive replay for a sandbox branch.

    Rules:
    - replay mismatch invalidates promotion
    - unstable stabilization blocks promotion

    Returns a validation dict with 'valid', 'reason', and 'blocks_promotion' fields.
    """
    if not replay_packet.deterministic_match:
        return {
            "valid": False,
            "reason": f"Replay mismatch: mismatched_mutations={replay_packet.mismatched_mutations}",
            "blocks_promotion": True,
        }
    if branch.stabilization_state in {"unstable", "failed"}:
        return {
            "valid": False,
            "reason": f"Branch stabilization_state={branch.stabilization_state!r} blocks promotion",
            "blocks_promotion": True,
        }
    return {
        "valid": True,
        "reason": "Replay deterministic match confirmed and branch not unstable",
        "blocks_promotion": False,
    }


# ── Doctrine validator extension gates ─────────────────────────────────────

def sandbox_branch_gate(evidence: Dict[str, Any]) -> GateResult:
    """Gate: sandbox branch must be isolated and have locked authority."""
    sandbox_branch = evidence.get("sandbox_branch")
    if sandbox_branch is None:
        return GateResult(
            gate_id="sandbox_branch_gate",
            status=GateStatus.FAIL,
            reason="No sandbox branch present. Pipeline cannot be compliant.",
        )
    authority = sandbox_branch.get("authority", {})
    if not authority.get("locked", False):
        return GateResult(
            gate_id="sandbox_branch_gate",
            status=GateStatus.FAIL,
            reason="Sandbox branch authority is not locked. Authority leak detected.",
        )
    branch_hash = sandbox_branch.get("deterministic_branch_hash", "")
    if not branch_hash or len(branch_hash) != 64:
        return GateResult(
            gate_id="sandbox_branch_gate",
            status=GateStatus.FAIL,
            reason=f"Sandbox branch has invalid deterministic_branch_hash: '{branch_hash}'",
        )
    source_hash = sandbox_branch.get("source_state_hash", "")
    sandbox_hash = sandbox_branch.get("sandbox_state_hash", "")
    if source_hash and sandbox_hash and source_hash == sandbox_hash:
        return GateResult(
            gate_id="sandbox_branch_gate",
            status=GateStatus.FAIL,
            reason="Sandbox state hash equals source state hash - sandbox not isolated.",
        )
    return GateResult(
        gate_id="sandbox_branch_gate",
        status=GateStatus.PASS,
        reason="Sandbox branch isolated with locked authority.",
        evidence={"branch_hash": branch_hash[:8] + "..."},
    )


def adaptive_replay_gate(evidence: Dict[str, Any]) -> GateResult:
    """Gate: adaptive replay must produce deterministic match."""
    replay_packet = evidence.get("sandbox_replay_packet")
    if replay_packet is None:
        return GateResult(
            gate_id="adaptive_replay_gate",
            status=GateStatus.FAIL,
            reason="No sandbox replay packet present. Replay unverified.",
        )
    deterministic_match = replay_packet.get("deterministic_match", False)
    if not deterministic_match:
        mismatched = replay_packet.get("mismatched_mutations", [])
        return GateResult(
            gate_id="adaptive_replay_gate",
            status=GateStatus.FAIL,
            reason=f"Sandbox replay mismatch. Invalidates promotion. Mismatched: {mismatched}",
            evidence={"mismatched_mutations": mismatched},
        )
    return GateResult(
        gate_id="adaptive_replay_gate",
        status=GateStatus.PASS,
        reason="Sandbox replay deterministic match confirmed.",
        evidence={"deterministic_match": True},
    )


def adaptive_stabilization_gate(evidence: Dict[str, Any]) -> GateResult:
    """Gate: sandbox stabilization must not be unstable or failed."""
    stab_packet = evidence.get("sandbox_stabilization_packet")
    if stab_packet is None:
        return GateResult(
            gate_id="adaptive_stabilization_gate",
            status=GateStatus.FAIL,
            reason="No sandbox stabilization packet present.",
        )
    stab_state = stab_packet.get("stabilization_state", "")
    if stab_state in {"unstable", "failed", ""}:
        return GateResult(
            gate_id="adaptive_stabilization_gate",
            status=GateStatus.FAIL,
            reason=f"Sandbox stabilization state is '{stab_state}'. Blocks promotion.",
            evidence={"stabilization_state": stab_state},
        )
    # Check lineage for cycles
    lineage = evidence.get("sandbox_lineage")
    if lineage is not None and lineage.get("status") == "cyclic":
        return GateResult(
            gate_id="adaptive_stabilization_gate",
            status=GateStatus.FAIL,
            reason="Cyclic lineage detected. Fail-closed.",
            evidence={"lineage_status": "cyclic"},
        )
    return GateResult(
        gate_id="adaptive_stabilization_gate",
        status=GateStatus.PASS,
        reason=f"Sandbox stabilization state is '{stab_state}'.",
        evidence={"stabilization_state": stab_state},
    )


def promotion_candidate_gate(evidence: Dict[str, Any]) -> GateResult:
    """Gate: promotion candidate must require operator review and default false."""
    candidate = evidence.get("promotion_candidate")
    if candidate is None:
        return GateResult(
            gate_id="promotion_candidate_gate",
            status=GateStatus.FAIL,
            reason="No promotion candidate present.",
        )
    operator_review_required = candidate.get("operator_review_required", False)
    if not operator_review_required:
        return GateResult(
            gate_id="promotion_candidate_gate",
            status=GateStatus.FAIL,
            reason="Promotion candidate does not require operator review. Bypass attempted.",
        )
    promotion_allowed = candidate.get("promotion_allowed", True)
    if promotion_allowed:
        return GateResult(
            gate_id="promotion_candidate_gate",
            status=GateStatus.FAIL,
            reason="Promotion is allowed without operator sign-off. Authority bypass detected.",
        )
    return GateResult(
        gate_id="promotion_candidate_gate",
        status=GateStatus.PASS,
        reason="Promotion candidate gated with operator review required and promotion_allowed=False.",
        evidence={
            "operator_review_required": True,
            "promotion_allowed": False,
        },
    )


def mutation_receipt_gate(evidence: Dict[str, Any]) -> GateResult:
    """Gate: all mutation receipts must be present and have locked authority."""
    receipts = evidence.get("mutation_receipts")
    if receipts is None:
        return GateResult(
            gate_id="mutation_receipt_gate",
            status=GateStatus.FAIL,
            reason="No mutation receipts present.",
        )
    if not isinstance(receipts, list):
        return GateResult(
            gate_id="mutation_receipt_gate",
            status=GateStatus.FAIL,
            reason="mutation_receipts must be a list.",
        )
    # Empty receipts list is allowed (no mutations proposed)
    for r in receipts:
        authority = r.get("authority", {}) if isinstance(r, dict) else {}
        if not authority.get("locked", False):
            return GateResult(
                gate_id="mutation_receipt_gate",
                status=GateStatus.FAIL,
                reason="A mutation receipt has unlocked authority. Authority leak detected.",
            )
    return GateResult(
        gate_id="mutation_receipt_gate",
        status=GateStatus.PASS,
        reason=f"All {len(receipts)} mutation receipt(s) validated.",
        evidence={"receipt_count": len(receipts)},
    )


# Registry of sandbox extension gates
SANDBOX_GATE_FUNCTIONS = [
    sandbox_branch_gate,
    adaptive_replay_gate,
    adaptive_stabilization_gate,
    promotion_candidate_gate,
    mutation_receipt_gate,
]


def validate_sandbox_doctrine(
    pipeline_id: str,
    evidence: Dict[str, Any],
) -> Dict[str, Any]:
    """Run all sandbox doctrine gates and return a validation result dict.

    Extends the base doctrine validator with sandbox-specific gates.
    Pipeline fails compliance if any sandbox gate fails.
    """
    gates = []
    blocking = []
    for gate_fn in SANDBOX_GATE_FUNCTIONS:
        result = gate_fn(evidence)
        gate_dict = {
            "gate_id": result.gate_id,
            "status": result.status.value,
            "reason": result.reason,
            "evidence": result.evidence,
        }
        gates.append(gate_dict)
        if result.status != GateStatus.PASS:
            blocking.append(result.gate_id)

    fully_compliant = len(blocking) == 0

    import json
    canonical = json.dumps(
        {
            "pipeline_id": pipeline_id,
            "fully_compliant": fully_compliant,
            "gates": [
                {"gate_id": g["gate_id"], "status": g["status"], "reason": g["reason"]}
                for g in gates
            ],
        },
        sort_keys=True,
    ).encode("utf-8")
    result_hash = sha256(canonical).hexdigest()

    return {
        "schema_version": "SandboxDoctrineValidationResult.v1",
        "pipeline_id": pipeline_id,
        "fully_compliant": fully_compliant,
        "blocking_gates": blocking,
        "result_hash": result_hash,
        "gates": gates,
    }
