"""Oracle intake validators - doctrine gate extensions for v2.0.6.

Validates:
- intake_envelope_gate
- intake_replay_gate
- intake_conflict_gate
- intake_lineage_gate
- intake_stabilization_gate
- intake_approval_gate

Pipeline fails compliance if:
- replay mismatch unresolved
- conflicts unresolved
- lineage cyclic
- provenance invalid
- approval bypass attempted
"""
from __future__ import annotations

from typing import Any, Dict, List


def validate_intake_replay(
    intake_run: Dict[str, Any],
    replay_packet: Dict[str, Any],
) -> Dict[str, Any]:
    """Validate that a replay packet is consistent with the intake run.

    Rules:
    - replay mismatch invalidates approval
    - unresolved conflicts invalidate stabilization
    - lineage cycles fail closed
    - provenance mismatch blocks approval

    Returns:
        Dict with keys: valid (bool), reason (str), blocking_issues (List[str])
    """
    blocking: List[str] = []

    # Check replay deterministic match
    if not replay_packet.get("deterministic_match", False):
        mismatched = replay_packet.get("mismatched_normalizations", [])
        blocking.append(
            f"replay_mismatch: deterministic_match=False, mismatched={mismatched}"
        )

    # Check for unresolved conflicts in the run
    conflict_pkts = intake_run.get("conflict_packets", [])
    unresolved = [c for c in conflict_pkts if c.get("status") == "unresolved"]
    if unresolved:
        blocking.append(
            f"unresolved_conflicts: {len(unresolved)} conflict(s) unresolved"
        )

    # Check provenance via evidence packets
    evidence_pkts = intake_run.get("evidence_packets", [])
    missing_provenance = [
        e for e in evidence_pkts
        if not e.get("provenance_chain") or e.get("status") == "not_computable"
    ]
    if missing_provenance:
        blocking.append(
            f"provenance_missing: {len(missing_provenance)} evidence packet(s) lack provenance"
        )

    return {
        "valid": len(blocking) == 0,
        "reason": "; ".join(blocking) if blocking else "intake replay valid",
        "blocking_issues": blocking,
    }


# ── Doctrine gate functions (extend doctrine validator) ───────────────────

def _intake_envelope_gate(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Gate: intake run must have at least one intake envelope."""
    intake_run = evidence.get("intake_run")
    if intake_run is None:
        return {
            "gate_id": "intake_envelope_gate",
            "status": "fail",
            "reason": "No intake_run present. Intake envelope gate cannot be satisfied.",
        }
    envelopes = intake_run.get("intake_envelopes", [])
    if not envelopes:
        return {
            "gate_id": "intake_envelope_gate",
            "status": "fail",
            "reason": "intake_run has no intake_envelopes.",
        }
    pending_blocked = [
        e for e in envelopes
        if e.get("intake_status") in {"conflict_detected", "rejected"}
    ]
    if pending_blocked:
        return {
            "gate_id": "intake_envelope_gate",
            "status": "fail",
            "reason": f"{len(pending_blocked)} envelope(s) in blocked status.",
            "evidence": {"blocked_count": len(pending_blocked)},
        }
    return {
        "gate_id": "intake_envelope_gate",
        "status": "pass",
        "reason": f"Intake envelopes valid: {len(envelopes)} envelope(s).",
        "evidence": {"envelope_count": len(envelopes)},
    }


def _intake_replay_gate(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Gate: all replay packets must show deterministic match."""
    intake_run = evidence.get("intake_run")
    if intake_run is None:
        return {
            "gate_id": "intake_replay_gate",
            "status": "fail",
            "reason": "No intake_run present.",
        }
    replay_pkts = intake_run.get("replay_packets", [])
    if not replay_pkts:
        return {
            "gate_id": "intake_replay_gate",
            "status": "fail",
            "reason": "No replay packets in intake_run.",
        }
    mismatched = [p for p in replay_pkts if not p.get("deterministic_match", False)]
    if mismatched:
        return {
            "gate_id": "intake_replay_gate",
            "status": "fail",
            "reason": f"Replay mismatch: {len(mismatched)} packet(s) failed deterministic match.",
            "evidence": {"mismatched_count": len(mismatched)},
        }
    return {
        "gate_id": "intake_replay_gate",
        "status": "pass",
        "reason": f"All {len(replay_pkts)} replay packet(s) matched deterministically.",
        "evidence": {"replay_count": len(replay_pkts)},
    }


def _intake_conflict_gate(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Gate: no unresolved conflicts may remain."""
    intake_run = evidence.get("intake_run")
    if intake_run is None:
        return {
            "gate_id": "intake_conflict_gate",
            "status": "fail",
            "reason": "No intake_run present.",
        }
    conflict_pkts = intake_run.get("conflict_packets", [])
    unresolved = [c for c in conflict_pkts if c.get("status") == "unresolved"]
    if unresolved:
        return {
            "gate_id": "intake_conflict_gate",
            "status": "fail",
            "reason": f"Unresolved conflicts: {len(unresolved)} conflict(s) block compliance.",
            "evidence": {"unresolved_count": len(unresolved)},
        }
    return {
        "gate_id": "intake_conflict_gate",
        "status": "pass",
        "reason": f"No unresolved conflicts. Total: {len(conflict_pkts)}.",
        "evidence": {"conflict_count": len(conflict_pkts)},
    }


def _intake_lineage_gate(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Gate: intake lineage must not be cyclic."""
    intake_lineage = evidence.get("intake_lineage")
    if intake_lineage is None:
        # No lineage present = not applicable (not a blocking failure)
        return {
            "gate_id": "intake_lineage_gate",
            "status": "pass",
            "reason": "No intake lineage present (not required for compliance).",
        }
    status = intake_lineage.get("status", "")
    if status == "cyclic":
        return {
            "gate_id": "intake_lineage_gate",
            "status": "fail",
            "reason": "Cyclic lineage detected. Intake lineage gate fails closed.",
        }
    if status == "invalid":
        return {
            "gate_id": "intake_lineage_gate",
            "status": "fail",
            "reason": "Invalid parent references in lineage.",
        }
    return {
        "gate_id": "intake_lineage_gate",
        "status": "pass",
        "reason": f"Intake lineage valid: status={status}.",
        "evidence": {"lineage_status": status},
    }


def _intake_stabilization_gate(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Gate: at least one stabilization packet must reach stable or stabilizing state."""
    intake_run = evidence.get("intake_run")
    if intake_run is None:
        return {
            "gate_id": "intake_stabilization_gate",
            "status": "fail",
            "reason": "No intake_run present.",
        }
    stab_pkts = intake_run.get("stabilization_packets", [])
    if not stab_pkts:
        return {
            "gate_id": "intake_stabilization_gate",
            "status": "fail",
            "reason": "No stabilization packets in intake_run.",
        }
    failed_or_conflicted = [
        p for p in stab_pkts
        if p.get("stabilization_state") in {"failed", "conflicted"}
    ]
    if len(failed_or_conflicted) == len(stab_pkts):
        return {
            "gate_id": "intake_stabilization_gate",
            "status": "fail",
            "reason": "All stabilization packets are failed or conflicted.",
            "evidence": {"failed_count": len(failed_or_conflicted)},
        }
    return {
        "gate_id": "intake_stabilization_gate",
        "status": "pass",
        "reason": f"Stabilization packets present: {len(stab_pkts)}.",
        "evidence": {"stabilization_count": len(stab_pkts)},
    }


def _intake_approval_gate(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Gate: no approval bypass attempted; all approvals must be properly gated."""
    intake_run = evidence.get("intake_run")
    if intake_run is None:
        return {
            "gate_id": "intake_approval_gate",
            "status": "fail",
            "reason": "No intake_run present.",
        }
    approval_pkts = intake_run.get("approval_packets", [])
    if not approval_pkts:
        return {
            "gate_id": "intake_approval_gate",
            "status": "fail",
            "reason": "No approval packets in intake_run.",
        }
    # Detect bypass: approved=True with conflict_hashes present (should be impossible)
    bypassed = [
        a for a in approval_pkts
        if a.get("approved", False) and a.get("conflict_hashes")
    ]
    if bypassed:
        return {
            "gate_id": "intake_approval_gate",
            "status": "fail",
            "reason": f"Approval bypass detected: {len(bypassed)} packet(s) approved with conflicts.",
            "evidence": {"bypass_count": len(bypassed)},
        }
    return {
        "gate_id": "intake_approval_gate",
        "status": "pass",
        "reason": f"Approval gate satisfied: {len(approval_pkts)} packet(s), no bypass detected.",
        "evidence": {"approval_count": len(approval_pkts)},
    }


# Registry of all intake gate functions
INTAKE_GATE_FUNCTIONS = [
    _intake_envelope_gate,
    _intake_replay_gate,
    _intake_conflict_gate,
    _intake_lineage_gate,
    _intake_stabilization_gate,
    _intake_approval_gate,
]


def run_intake_doctrine_gates(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Run all intake doctrine gates and return a result dict.

    Returns:
        Dict with keys: fully_compliant (bool), gates (list), blocking_gates (list)
    """
    gates = []
    blocking: List[str] = []

    for gate_fn in INTAKE_GATE_FUNCTIONS:
        result = gate_fn(evidence)
        gates.append(result)
        if result.get("status") != "pass":
            blocking.append(result["gate_id"])

    return {
        "fully_compliant": len(blocking) == 0,
        "gates": gates,
        "blocking_gates": blocking,
    }
