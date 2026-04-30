from __future__ import annotations

from abraxas.pse.calibration_application import build_calibration_application_proposal


def test_deterministic_output_and_global_multiplier() -> None:
    feedback = {
        "status": "ADVISORY_ONLY",
        "global_reliability": 0.8025,
        "domain_reliability": {"unknown": 0.8025},
        "source_reliability": {"unknown": 0.8025},
    }
    readiness = {"status": "READY"}
    first = build_calibration_application_proposal(feedback, readiness)
    second = build_calibration_application_proposal(feedback, readiness)
    assert first == second
    assert first["status"] == "PROPOSAL_ONLY"
    assert first["proposed_changes"]["global_confidence_multiplier"] == 0.8025


def test_readiness_and_feedback_enforced() -> None:
    feedback = {"status": "ADVISORY_ONLY", "global_reliability": 0.9}
    assert build_calibration_application_proposal(feedback, {"status": "NOT_READY"})["status"] == "NOT_COMPUTABLE"
    assert build_calibration_application_proposal({"status": "NOT_COMPUTABLE"}, {"status": "READY"})["status"] == "NOT_COMPUTABLE"


def test_clamping_approval_and_no_mutation_flags() -> None:
    feedback = {
        "status": "ADVISORY_ONLY",
        "global_reliability": 0.1,
        "domain_reliability": {"d1": 1.2},
        "source_reliability": {"s1": 0.0},
    }
    report = build_calibration_application_proposal(feedback, {"status": "READY"})
    assert report["proposed_changes"]["global_confidence_multiplier"] == 0.25
    assert report["proposed_changes"]["domain_weights"]["d1"] == 1.0
    assert report["proposed_changes"]["source_weights"]["s1"] == 0.25
    assert report["approval"] == {"requires_approval": True, "approved": False, "applied": False}
