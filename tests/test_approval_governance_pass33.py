from __future__ import annotations

from abx.approval.approvalClassification import classify_approval_state
from abx.approval.approvalReports import build_human_approval_report
from abx.approval.authorityClassification import classify_authority
from abx.approval.authorityReports import build_authority_report
from abx.approval.authorityToProceed import build_authority_to_proceed_records
from abx.approval.consentClassification import classify_consent_state
from abx.approval.consentReports import build_consent_state_report
from abx.approval.transitionReports import build_approval_transition_report
from abx.approval.approvalScorecard import build_approval_governance_scorecard


def test_human_approval_classification_and_reporting_determinism() -> None:
    report_a = build_human_approval_report()
    report_b = build_human_approval_report()
    assert report_a == report_b
    assert set(report_a["approvalStates"].values()).issubset(
        {
            "APPROVAL_REQUIRED",
            "APPROVAL_REQUESTED",
            "APPROVAL_GRANTED",
            "APPROVAL_CONDITIONAL",
            "APPROVAL_DENIED",
            "APPROVAL_WITHDRAWN",
            "APPROVAL_EXPIRED",
            "INVALID_APPROVAL",
            "BLOCKED_PENDING_APPROVAL",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_approval_state(approval_required="REQUIRED", approver_id="lead", raw_signal="approved", valid_until="2026-04-01T00:00:00Z") == "APPROVAL_GRANTED"


def test_consent_semantics_distinctions_and_determinism() -> None:
    report_a = build_consent_state_report()
    report_b = build_consent_state_report()
    assert report_a == report_b
    assert set(report_a["consentClassification"].values()).issubset(
        {
            "EXPLICIT_APPROVAL",
            "CONDITIONAL_APPROVAL",
            "ACKNOWLEDGMENT_ONLY",
            "PREFERENCE_ONLY",
            "AMBIGUOUS_CONSENT",
            "DENIED_CONSENT",
            "WITHDRAWN_CONSENT",
            "EXPIRED_CONSENT",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_consent_state("ACKNOWLEDGMENT_ONLY") == "ACKNOWLEDGMENT_ONLY"


def test_authority_validity_scope_and_determinism() -> None:
    report_a = build_authority_report()
    report_b = build_authority_report()
    assert report_a == report_b
    states = {row["validity_state"] for row in report_a["validityRecords"]}
    assert states.issubset(
        {
            "VALID_AUTHORITY",
            "DELEGATED_AUTHORITY",
            "SCOPE_INVALID_AUTHORITY",
            "EXPIRED_AUTHORITY",
            "INVALID_AUTHORITY",
        }
    )
    assert classify_authority(build_authority_to_proceed_records()[0]) == "VALID_AUTHORITY"


def test_transition_distinctions_and_determinism() -> None:
    report_a = build_approval_transition_report()
    report_b = build_approval_transition_report()
    assert report_a == report_b
    assert {x["to_state"] for x in report_a["transitions"]}.issuperset(
        {
            "APPROVAL_GRANTED",
            "APPROVAL_EXPIRED",
            "APPROVAL_DENIED",
            "APPROVAL_WITHDRAWN",
            "DELEGATED",
            "BLOCKED_PENDING_APPROVAL",
        }
    )


def test_approval_scorecard_determinism_and_blockers() -> None:
    score_a = build_approval_governance_scorecard()
    score_b = build_approval_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {
        "APPROVAL_READY",
        "AMBIGUITY_BURDENED",
        "STALE_APPROVAL_BURDENED",
        "BLOCKED",
    }
    assert "authority_validity_quality" in score_a.dimensions


def test_elegance_regressions_and_invariance_guards() -> None:
    approval = build_human_approval_report()
    consent = build_consent_state_report()
    authority = build_authority_report()
    transitions = build_approval_transition_report()

    assert len(set(approval["approvalStates"].values())) <= 10
    assert len(set(consent["consentClassification"].values())) <= 9
    assert not any(v == "APPROVAL_GRANTED" for k, v in approval["approvalStates"].items() if k == "apr.publish.001")
    if any(x["validity_state"] == "EXPIRED_AUTHORITY" for x in authority["validityRecords"]):
        assert any(x["to_state"] == "APPROVAL_EXPIRED" for x in transitions["transitions"])
