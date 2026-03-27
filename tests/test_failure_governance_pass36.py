from __future__ import annotations

from abx.failure.errorClassification import classify_error
from abx.failure.errorReports import build_error_taxonomy_report
from abx.failure.failureClassification import classify_failure_semantics
from abx.failure.failureReports import build_failure_semantics_report
from abx.failure.recoveryClassification import classify_recovery
from abx.failure.recoveryReports import build_recovery_eligibility_report
from abx.failure.transitionReports import build_failure_transition_report
from abx.failure.failureScorecard import build_failure_governance_scorecard


def test_error_taxonomy_determinism() -> None:
    report_a = build_error_taxonomy_report()
    report_b = build_error_taxonomy_report()
    assert report_a == report_b
    assert set(report_a["errorStates"].values()).issubset(
        {
            "TRANSIENT_ERROR",
            "PERSISTENT_ERROR",
            "EXTERNAL_DEPENDENCY_FAILURE",
            "INTERNAL_LOGIC_FAILURE",
            "STATE_INVALIDITY",
            "INTEGRITY_RISK_FAILURE",
            "SAFETY_BLOCKING_FAILURE",
            "UNKNOWN_FAILURE",
            "BLOCKED",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_error(failure_class="TRANSIENT_ERROR", severity="MEDIUM") == "TRANSIENT_ERROR"


def test_failure_semantics_determinism() -> None:
    report_a = build_failure_semantics_report()
    report_b = build_failure_semantics_report()
    assert report_a == report_b
    assert set(report_a["semanticStates"].values()).issubset(
        {
            "RETRYABLE_FAILURE",
            "NON_RETRYABLE_FAILURE",
            "INTEGRITY_COMPROMISED_FAILURE",
            "HUMAN_INTERVENTION_REQUIRED",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_failure_semantics(recoverability="NON_RETRYABLE_FAILURE", degraded_state="DEGRADED_AND_UNSAFE", integrity_impact="MEDIUM") == "NON_RETRYABLE_FAILURE"


def test_recovery_eligibility_determinism() -> None:
    report_a = build_recovery_eligibility_report()
    report_b = build_recovery_eligibility_report()
    assert report_a == report_b
    assert set(report_a["recoveryStates"].values()).issubset({"RECOVERY_ELIGIBLE", "RECOVERY_FORBIDDEN", "PARTIAL", "BLOCKED"})
    assert classify_recovery(retry_allowed="YES", restore_allowed="YES", clearance_required="NO") == "RECOVERY_ELIGIBLE"


def test_failure_transition_determinism() -> None:
    report_a = build_failure_transition_report()
    report_b = build_failure_transition_report()
    assert report_a == report_b
    assert {x["to_state"] for x in report_a["transitions"]}.issuperset(
        {"RECOVERY_ELIGIBLE", "RETRY_FORBIDDEN", "QUARANTINE_REQUIRED", "REBUILD_REQUIRED", "ROLLBACK_REQUIRED"}
    )


def test_failure_scorecard_determinism_and_blockers() -> None:
    score_a = build_failure_governance_scorecard()
    score_b = build_failure_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {"FAILURE_GOVERNED", "UNSAFE_RESTORATION_BURDENED", "REPEAT_FAILURE_BURDENED", "PARTIAL", "BLOCKED"}
    assert "error_taxonomy_clarity" in score_a.dimensions


def test_elegance_regressions_and_invariance_guards() -> None:
    errors = build_error_taxonomy_report()
    recovery = build_recovery_eligibility_report()
    transitions = build_failure_transition_report()

    assert len(set(errors["errorStates"].values())) <= 10
    assert not any(v == "RECOVERY_ELIGIBLE" for k, v in recovery["recoveryStates"].items() if "cache.corrupt" in k)
    if any(x["unsafe_state"] == "UNSAFE_RESTORATION" for x in transitions["unsafeRestoration"]):
        assert any(x["to_state"] in {"QUARANTINE_REQUIRED", "REBUILD_REQUIRED"} for x in transitions["transitions"])
