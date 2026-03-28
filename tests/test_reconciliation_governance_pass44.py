from __future__ import annotations

from abx.reconcile.conflictClassification import classify_conflict
from abx.reconcile.conflictReports import build_state_conflict_report
from abx.reconcile.reconciliationReports import build_reconciliation_report
from abx.reconcile.reconciliationScorecard import build_reconciliation_governance_scorecard
from abx.reconcile.reconciliationScorecardSerialization import serialize_reconciliation_scorecard
from abx.reconcile.repairClassification import classify_repair
from abx.reconcile.restorationClassification import classify_restoration
from abx.reconcile.restorationReports import build_restoration_status_report
from abx.reconcile.transitionReports import build_reconciliation_transition_report


def test_state_conflict_determinism_and_classes() -> None:
    report_a = build_state_conflict_report()
    report_b = build_state_conflict_report()
    assert report_a == report_b
    assert set(report_a["conflictStates"].values()).issuperset(
        {
            "TEMPORAL_CONFLICT",
            "FRESHNESS_CONFLICT",
            "IDENTITY_CONFLICT",
            "SEMANTIC_CONFLICT",
            "LINEAGE_CONFLICT",
            "AUTHORITY_CONFLICT",
            "COSMETIC_MISMATCH",
            "CONFLICT_UNKNOWN",
            "NOT_COMPUTABLE",
            "BLOCKING_CONFLICT",
        }
    )
    assert classify_conflict(conflict_state="SEMANTIC_CONFLICT", severity="BLOCKING") == "SEMANTIC_CONFLICT"


def test_reconciliation_determinism_and_repair_modes() -> None:
    report_a = build_reconciliation_report()
    report_b = build_reconciliation_report()
    assert report_a == report_b
    assert set(report_a["reconciliationStates"].values()).issuperset(
        {
            "AUTHORITATIVE_OVERWRITE",
            "LAWFUL_MERGE",
            "REFRESH_REPAIR",
            "ROLLBACK_REPAIR",
            "REBUILD_REPAIR",
            "QUARANTINE_REPAIR",
            "REPAIR_FORBIDDEN",
            "REPAIR_LEGITIMACY_UNKNOWN",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_repair(
        repair_mode="REPAIR_FORBIDDEN",
        reconciliation_state="RECONCILIATION_BLOCKED",
        legitimacy_state="FORBIDDEN",
    ) == "REPAIR_FORBIDDEN"


def test_restoration_determinism_and_posture() -> None:
    report_a = build_restoration_status_report()
    report_b = build_restoration_status_report()
    assert report_a == report_b
    assert set(report_a["restorationStates"].values()).issuperset(
        {
            "CONSISTENCY_RESTORED_DURABLE",
            "PROVISIONAL_OR_PENDING",
            "CONSISTENCY_PARTIALLY_RESTORED",
            "COSMETIC_ALIGNMENT_ONLY",
            "BLOCKED",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_restoration(
        restoration_state="CONSISTENCY_RESTORED_PROVISIONAL",
        validation_state="PENDING_VALIDATION",
    ) == "PROVISIONAL_OR_PENDING"


def test_transition_determinism_and_risk_visibility() -> None:
    report_a = build_reconciliation_transition_report()
    report_b = build_reconciliation_transition_report()
    assert report_a == report_b
    assert {x["to_state"] for x in report_a["transitions"]}.issuperset(
        {
            "UNRESOLVED_CONFLICT_ACTIVE",
            "COSMETIC_ALIGNMENT_ACTIVE",
            "VALIDATION_REQUIRED",
            "PROVISIONAL_RESTORED",
            "DURABLE_RESTORED",
            "NOT_COMPUTABLE",
        }
    )


def test_reconciliation_scorecard_determinism_and_blockers() -> None:
    score_a = build_reconciliation_governance_scorecard()
    score_b = build_reconciliation_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {
        "RECONCILIATION_GOVERNED",
        "PROVISIONAL_BURDENED",
        "UNRESOLVED_CONFLICT_BURDENED",
        "COSMETIC_ALIGNMENT_BURDENED",
        "PARTIAL",
        "BLOCKED",
        "NOT_COMPUTABLE",
    }
    assert "unresolved_conflict_visibility" in score_a.blockers
    assert serialize_reconciliation_scorecard(score_a) == serialize_reconciliation_scorecard(score_b)


def test_elegance_regression_guards() -> None:
    conflict = build_state_conflict_report()
    restoration = build_restoration_status_report()
    transitions = build_reconciliation_transition_report()

    assert len(set(conflict["conflictStates"].values())) <= 10
    assert len(set(restoration["restorationStates"].values())) <= 6
    assert any(x["loss_state"] == "LOSSY_REPAIR_ACTIVE" for x in transitions["lossyRepair"])
    assert any(x["to_state"] == "COSMETIC_ALIGNMENT_ACTIVE" for x in transitions["transitions"])
