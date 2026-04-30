from __future__ import annotations

from copy import deepcopy

from abraxas.pse.calibration_candidate_proposal import build_candidate_proposal


def _inputs() -> tuple[dict, dict]:
    cycle = {
        "status": "CANDIDATE_CYCLE_COMPLETE",
        "baseline": {"mean_brier": 0.1975},
        "best_candidate": {
            "multiplier": 0.9,
            "mean_brier": 0.196975,
            "delta_vs_baseline": -0.000525,
            "improvement": True,
        },
        "recommendation": "CREATE_NEW_PROPOSAL_CANDIDATE",
    }
    readiness = {"status": "READY"}
    return cycle, readiness


def test_deterministic_and_expected_values() -> None:
    cycle, readiness = _inputs()
    first = build_candidate_proposal(cycle, readiness)
    second = build_candidate_proposal(cycle, readiness)
    assert first == second
    assert first["status"] == "PROPOSAL_ONLY"
    assert first["proposed_changes"]["global_confidence_multiplier"] == 0.9
    assert first["evidence"]["baseline_mean_brier"] == 0.1975
    assert first["evidence"]["candidate_mean_brier"] == 0.196975
    assert first["evidence"]["mean_brier_delta"] == -0.000525
    assert first["approval"] == {"requires_approval": True, "approved": False, "applied": False}


def test_rejection_paths() -> None:
    cycle, readiness = _inputs()
    assert build_candidate_proposal(cycle, {"status": "NOT_READY"})["status"] == "NOT_COMPUTABLE"
    bad_cycle = deepcopy(cycle)
    bad_cycle["recommendation"] = "NO_IMPROVING_CANDIDATE"
    assert build_candidate_proposal(bad_cycle, readiness)["status"] == "NOT_COMPUTABLE"
    bad_candidate = deepcopy(cycle)
    bad_candidate["best_candidate"]["improvement"] = False
    assert build_candidate_proposal(bad_candidate, readiness)["status"] == "NOT_COMPUTABLE"


def test_runtime_stays_disabled() -> None:
    cycle, readiness = _inputs()
    report = build_candidate_proposal(cycle, readiness)
    assert report["runtime_wiring_enabled"] is False
