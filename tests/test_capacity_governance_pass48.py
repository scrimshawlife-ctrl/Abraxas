from __future__ import annotations

from abx.capacity.allocationClassification import classify_commitment
from abx.capacity.capacityScorecard import build_capacity_governance_scorecard
from abx.capacity.capacityScorecardSerialization import serialize_capacity_scorecard
from abx.capacity.commitmentReports import build_capacity_commitment_report
from abx.capacity.contentionClassification import classify_contention
from abx.capacity.contentionReports import build_contention_budget_report
from abx.capacity.reservationClassification import classify_reservation
from abx.capacity.reservationReports import build_resource_reservation_report
from abx.capacity.transitionReports import build_capacity_transition_report


def test_reservation_determinism_and_states() -> None:
    report_a = build_resource_reservation_report()
    report_b = build_resource_reservation_report()
    assert report_a == report_b
    assert set(report_a["reservationStates"].values()).issuperset(
        {
            "RESOURCE_AVAILABLE",
            "RESOURCE_RESERVED",
            "PROVISIONAL_HOLD_ACTIVE",
            "RESERVATION_EXPIRED",
            "RESERVATION_DENIED",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_reservation(reservation_state="RESOURCE_RESERVED") == "RESOURCE_RESERVED"


def test_commitment_determinism_and_states() -> None:
    report_a = build_capacity_commitment_report()
    report_b = build_capacity_commitment_report()
    assert report_a == report_b
    assert set(report_a["commitmentStates"].values()).issuperset(
        {
            "HARD_CAPACITY_COMMITTED",
            "SOFT_CAPACITY_COMMITTED",
            "BEST_EFFORT_CLAIM",
            "COMMITMENT_UNKNOWN",
            "BLOCKED",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_commitment(commitment_state="BLOCKED", allocation_state="UNALLOCATED") == "BLOCKED"


def test_contention_determinism_and_states() -> None:
    report_a = build_contention_budget_report()
    report_b = build_contention_budget_report()
    assert report_a == report_b
    assert set(report_a["contentionStates"].values()).issuperset(
        {
            "CONTENTION_TOLERABLE",
            "CONTENTION_ACTIVE",
            "CONTENTION_BLOCKING",
            "OVERCOMMITTED",
            "STARVATION_RISK",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_contention(contention_state="OVERCOMMITTED") == "OVERCOMMITTED"


def test_capacity_transition_determinism_and_states() -> None:
    report_a = build_capacity_transition_report()
    report_b = build_capacity_transition_report()
    assert report_a == report_b
    assert {x["to_state"] for x in report_a["transitions"]}.issuperset(
        {
            "RESOURCE_RESERVED",
            "RESOURCE_ALLOCATED",
            "BUDGET_EXHAUSTED",
            "GUARANTEE_DOWNGRADED",
            "RELEASE_REQUIRED",
            "ADMISSION_BLOCKED",
        }
    )


def test_capacity_scorecard_determinism_and_blockers() -> None:
    score_a = build_capacity_governance_scorecard()
    score_b = build_capacity_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {
        "CAPACITY_GOVERNED",
        "EXHAUSTION_BURDENED",
        "OVERCOMMITTED_BURDENED",
        "STARVATION_BURDENED",
        "PARTIAL",
        "BLOCKED",
        "NOT_COMPUTABLE",
    }
    assert "commitment_legitimacy" in score_a.blockers
    assert serialize_capacity_scorecard(score_a) == serialize_capacity_scorecard(score_b)


def test_elegance_regression_guards() -> None:
    reservation = build_resource_reservation_report()
    commitment = build_capacity_commitment_report()
    contention = build_contention_budget_report()

    assert len(set(reservation["reservationStates"].values())) <= 6
    assert len(set(commitment["commitmentStates"].values())) <= 6
    assert len(set(contention["contentionStates"].values())) <= 6
    assert any(x["code"] == "CONTENTION_BLOCKING" for x in contention["governanceErrors"])
