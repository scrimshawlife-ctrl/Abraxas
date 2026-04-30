from __future__ import annotations


def _clamp_weight(value: float) -> float:
    return max(0.25, min(1.0, float(value)))


def build_calibration_application_proposal(feedback: dict, readiness: dict) -> dict:
    base = {
        "schema_version": "CalibrationApplicationProposal.v1",
        "status": "NOT_COMPUTABLE",
        "authority": "PROPOSAL_ONLY",
        "proposed_changes": {
            "global_confidence_multiplier": 0.0,
            "domain_weights": {},
            "source_weights": {},
        },
        "approval": {
            "requires_approval": True,
            "approved": False,
            "applied": False,
        },
    }

    if readiness.get("status") != "READY":
        return base
    if feedback.get("status") != "ADVISORY_ONLY":
        return base

    global_rel = feedback.get("global_reliability", 0.0)
    proposal = {
        "schema_version": "CalibrationApplicationProposal.v1",
        "status": "PROPOSAL_ONLY",
        "authority": "PROPOSAL_ONLY",
        "proposed_changes": {
            "global_confidence_multiplier": round(_clamp_weight(global_rel), 6),
            "domain_weights": {
                key: round(_clamp_weight(val), 6)
                for key, val in sorted(feedback.get("domain_reliability", {}).items())
            },
            "source_weights": {
                key: round(_clamp_weight(val), 6)
                for key, val in sorted(feedback.get("source_reliability", {}).items())
            },
        },
        "approval": {
            "requires_approval": True,
            "approved": False,
            "applied": False,
        },
    }
    return proposal
