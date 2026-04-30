from __future__ import annotations


def build_candidate_proposal(candidate_cycle: dict, readiness: dict) -> dict:
    base = {
        "schema_version": "CalibrationCandidateProposal.v1",
        "status": "NOT_COMPUTABLE",
        "authority": "PROPOSAL_ONLY",
        "source": "CANDIDATE_CYCLE",
        "proposed_changes": {"global_confidence_multiplier": 0.0},
        "evidence": {
            "baseline_mean_brier": None,
            "candidate_mean_brier": None,
            "mean_brier_delta": None,
            "improvement": False,
        },
        "approval": {"requires_approval": True, "approved": False, "applied": False},
        "runtime_wiring_enabled": False,
    }

    best = candidate_cycle.get("best_candidate")
    conditions = [
        readiness.get("status") == "READY",
        candidate_cycle.get("status") == "CANDIDATE_CYCLE_COMPLETE",
        candidate_cycle.get("recommendation") == "CREATE_NEW_PROPOSAL_CANDIDATE",
        isinstance(best, dict),
        bool(best and best.get("improvement") is True),
    ]
    if not all(conditions):
        return base

    return {
        "schema_version": "CalibrationCandidateProposal.v1",
        "status": "PROPOSAL_ONLY",
        "authority": "PROPOSAL_ONLY",
        "source": "CANDIDATE_CYCLE",
        "proposed_changes": {
            "global_confidence_multiplier": round(float(best.get("multiplier", 0.0)), 6)
        },
        "evidence": {
            "baseline_mean_brier": candidate_cycle.get("baseline", {}).get("mean_brier"),
            "candidate_mean_brier": best.get("mean_brier"),
            "mean_brier_delta": best.get("delta_vs_baseline"),
            "improvement": True,
        },
        "approval": {"requires_approval": True, "approved": False, "applied": False},
        "runtime_wiring_enabled": False,
    }
