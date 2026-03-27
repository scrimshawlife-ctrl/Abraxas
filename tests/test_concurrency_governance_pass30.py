from __future__ import annotations

from abx.concurrency.arbitrationRecords import build_arbitration_decisions
from abx.concurrency.arbitrationReports import build_arbitration_report
from abx.concurrency.concurrentClassification import classify_concurrency_posture
from abx.concurrency.concurrentReports import build_concurrent_operation_report
from abx.concurrency.conflictClassification import classify_conflict_posture
from abx.concurrency.conflictInventory import build_conflict_inventory
from abx.concurrency.conflictReports import build_conflict_report
from abx.concurrency.concurrencyScorecard import build_concurrency_scorecard
from abx.concurrency.mergeabilityRules import build_mergeability_records
from abx.concurrency.overlapReports import build_overlap_resolution_report
from abx.concurrency.overlapResolution import build_compensation_records, build_overlap_resolution_records


EXPECTED_OVERLAP_STATES = {
    "INDEPENDENT_CONCURRENT",
    "SHARED_DOMAIN_CONCURRENT",
    "NON_CONFLICTING_OVERLAP",
    "MERGEABLE_OVERLAP",
    "SERIALIZE_REQUIRED",
    "NOT_COMPUTABLE",
}

EXPECTED_CONFLICT_CLASSES = {
    "NO_CONFLICT",
    "DUPLICATE_CONFLICT",
    "TARGET_CONFLICT",
    "AUTHORITY_CONFLICT",
    "POLICY_CONFLICT",
    "TEMPORAL_CONFLICT",
    "SIDE_EFFECT_CONFLICT",
    "MERGEABLE_CONFLICT",
}


def test_concurrent_operation_report_and_domain_classification_determinism() -> None:
    report_a = build_concurrent_operation_report()
    report_b = build_concurrent_operation_report()
    assert report_a == report_b
    assert set(x["state"] for x in report_a["overlaps"]).issubset(EXPECTED_OVERLAP_STATES)
    assert classify_concurrency_posture([x["state"] for x in report_a["overlaps"]]) == report_a["posture"]


def test_conflict_detection_preflight_inflight_and_determinism() -> None:
    conflicts_a = build_conflict_inventory()
    conflicts_b = build_conflict_inventory()
    assert conflicts_a == conflicts_b
    assert set(x.conflict_class for x in conflicts_a).issubset(EXPECTED_CONFLICT_CLASSES)
    assert set(x.phase for x in conflicts_a).issubset({"PREFLIGHT", "IN_FLIGHT"})

    report = build_conflict_report()
    assert report == build_conflict_report()
    assert classify_conflict_posture([x["conflict_class"] for x in report["conflicts"]]) == report["posture"]


def test_arbitration_decisions_and_outcome_grammar_determinism() -> None:
    decisions = build_arbitration_decisions()
    assert decisions == build_arbitration_decisions()
    assert set(x.outcome for x in decisions).issubset(
        {"MERGED", "SERIALIZED", "DELAYED", "ESCALATED", "DENIED", "BLOCKED", "NOT_COMPUTABLE"}
    )

    report = build_arbitration_report()
    assert report == build_arbitration_report()
    assert set(report["outcomes"].keys()).issubset(
        {"MERGED", "SERIALIZED", "DELAYED", "ESCALATED", "DENIED", "BLOCKED", "NOT_COMPUTABLE"}
    )


def test_overlap_resolution_mergeability_serialization_compensation_determinism() -> None:
    merge = build_mergeability_records()
    assert merge == build_mergeability_records()
    assert set(x.merge_state for x in merge).issubset({"MERGEABLE", "SERIALIZE_INSTEAD", "NOT_MERGEABLE"})

    resolutions = build_overlap_resolution_records()
    assert resolutions == build_overlap_resolution_records()
    assert set(x.outcome_class for x in resolutions).issubset({"MERGED", "SERIALIZED", "DELAYED", "YIELDED", "ABORTED", "NOT_COMPUTABLE"})

    compensation = build_compensation_records()
    assert compensation == build_compensation_records()
    assert set(x.compensation_class for x in compensation).issubset({"COMPENSATED", "NONE"})

    overlap_report = build_overlap_resolution_report()
    assert overlap_report == build_overlap_resolution_report()


def test_concurrency_scorecard_determinism_blockers_and_category_stability() -> None:
    score_a = build_concurrency_scorecard()
    score_b = build_concurrency_scorecard()
    assert score_a == score_b
    assert score_a.category in {"CONCURRENCY_READY", "MERGE_READY", "ARBITRATION_READY", "PARTIAL", "BLOCKED", "HIDDEN_WINNER_RISK", "NOT_COMPUTABLE"}
    assert "hidden_winner_selection_burden" in score_a.dimensions


def test_elegance_regressions_and_invariance_guards() -> None:
    concurrent = build_concurrent_operation_report()
    conflict = build_conflict_report()
    arbitration = build_arbitration_report()

    # Duplicate concurrency vocabulary detection.
    assert set(x["state"] for x in concurrent["overlaps"]).issubset(EXPECTED_OVERLAP_STATES)

    # Redundant arbitration grammar detection.
    assert set(arbitration["outcomes"]).issubset({"MERGED", "SERIALIZED", "DELAYED", "ESCALATED", "DENIED", "BLOCKED", "NOT_COMPUTABLE"})

    # Hidden winner-selection drift detection.
    for row in arbitration["decisions"]:
        assert row["outcome"] != "MERGED" or row["winner_operation_id"] != "none"

    # Over-blocking regression detection.
    assert conflict["posture"] != "BLOCKED_BY_CONFLICT" or conflict["byType"].get("SIDE_EFFECT_CONFLICT")
