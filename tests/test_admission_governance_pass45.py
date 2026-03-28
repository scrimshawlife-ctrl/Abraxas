from __future__ import annotations

from abx.admission.admissionClassification import classify_admission
from abx.admission.admissionReports import build_change_admission_report
from abx.admission.admissionScorecard import build_admission_governance_scorecard
from abx.admission.admissionScorecardSerialization import serialize_admission_scorecard
from abx.admission.promotionClassification import classify_promotion
from abx.admission.promotionReports import build_promotion_gate_report
from abx.admission.readinessClassification import classify_release_readiness
from abx.admission.releaseReports import build_release_readiness_report
from abx.admission.rollbackReports import build_rejection_rollback_report


def test_admission_determinism_and_states() -> None:
    report_a = build_change_admission_report()
    report_b = build_change_admission_report()
    assert report_a == report_b
    assert set(report_a["admissionStates"].values()).issuperset(
        {
            "CHANGE_PROPOSED",
            "ADMISSION_PENDING",
            "ADMISSION_APPROVED",
            "ADMISSION_REJECTED",
            "ADMISSION_BLOCKED",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_admission(admission_state="ADMISSION_PENDING", evidence_state="EVIDENCE_PENDING") == "ADMISSION_PENDING"


def test_promotion_determinism_and_states() -> None:
    report_a = build_promotion_gate_report()
    report_b = build_promotion_gate_report()
    assert report_a == report_b
    assert set(report_a["promotionStates"].values()).issuperset(
        {
            "PROMOTION_CANDIDATE",
            "PROMOTION_GATED",
            "PROMOTION_APPROVED",
            "PROMOTION_FAILED_GATE",
            "PROMOTION_DEFERRED",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_promotion(promotion_state="PROMOTION_APPROVED") == "PROMOTION_APPROVED"


def test_release_readiness_determinism_and_states() -> None:
    report_a = build_release_readiness_report()
    report_b = build_release_readiness_report()
    assert report_a == report_b
    assert set(report_a["readinessStates"].values()).issuperset(
        {
            "EXPERIMENTAL",
            "RELEASE_PROVISIONAL",
            "RELEASE_READY",
            "RELEASE_BLOCKED",
            "ROLLBACK_REQUIRED",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_release_readiness(readiness_state="RELEASE_READY") == "RELEASE_READY"


def test_rejection_rollback_determinism() -> None:
    report_a = build_rejection_rollback_report()
    report_b = build_rejection_rollback_report()
    assert report_a == report_b
    assert {x["rejection_state"] for x in report_a["rejection"]}.issuperset({"REJECTED", "DEFERRED", "RE_ADMISSION_REQUIRED"})
    assert {x["rollback_state"] for x in report_a["rollback"]}.issuperset({"ROLLBACK_TRIGGERED", "ROLLBACK_COMPLETE", "RE_ADMISSION_REQUIRED"})


def test_admission_scorecard_determinism_and_blockers() -> None:
    score_a = build_admission_governance_scorecard()
    score_b = build_admission_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {
        "ADMISSION_GOVERNED",
        "PROVISIONAL_BURDENED",
        "ROLLBACK_BURDENED",
        "PARTIAL",
        "BLOCKED",
        "NOT_COMPUTABLE",
    }
    assert "promotion_legitimacy" in score_a.blockers
    assert serialize_admission_scorecard(score_a) == serialize_admission_scorecard(score_b)


def test_elegance_regression_guards() -> None:
    admission = build_change_admission_report()
    promotion = build_promotion_gate_report()
    release = build_release_readiness_report()

    assert len(set(admission["admissionStates"].values())) <= 6
    assert len(set(promotion["promotionStates"].values())) <= 6
    assert len(set(release["readinessStates"].values())) <= 6
    assert any(x["code"] == "PROMOTION_BLOCKING" for x in promotion["governanceErrors"])
