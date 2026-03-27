from __future__ import annotations

from abx.continuity.continuityClassification import classify_mission_continuity_state
from abx.continuity.continuityReports import build_mission_continuity_report
from abx.continuity.continuityScorecard import build_mission_continuity_scorecard
from abx.continuity.persistenceClassification import classify_persistence_state
from abx.continuity.persistenceReports import build_intent_persistence_report
from abx.continuity.planClassification import PLAN_STATES
from abx.continuity.planReports import build_long_horizon_plan_report
from abx.continuity.transitionReports import build_continuity_transition_report


def test_long_horizon_plan_state_and_horizon_reporting_determinism() -> None:
    report_a = build_long_horizon_plan_report()
    report_b = build_long_horizon_plan_report()
    assert report_a == report_b
    assert set(report_a["planStates"].values()).issubset(PLAN_STATES | {"NOT_COMPUTABLE"})


def test_intent_persistence_state_and_freshness_determinism() -> None:
    report_a = build_intent_persistence_report()
    report_b = build_intent_persistence_report()
    assert report_a == report_b
    assert set(report_a["intentStates"].values()).issubset(
        {"ACTIVE_INTENT", "LATENT_INTENT", "RESUMABLE_INTENT", "STALE_INTENT", "SUPERSEDED_INTENT", "RETIRED_INTENT", "NOT_COMPUTABLE"}
    )
    assert classify_persistence_state(persistence_state="ACTIVE_INTENT", freshness_state="FRESH", revalidation_required=False) == "ACTIVE_INTENT"


def test_mission_continuity_lifecycle_and_lineage_determinism() -> None:
    report_a = build_mission_continuity_report()
    report_b = build_mission_continuity_report()
    assert report_a == report_b
    assert all(k.startswith("mission.") for k in report_a["missionStates"])
    assert classify_mission_continuity_state("PAUSED", ["x"]) == "PAUSED_CONTINUITY"


def test_transition_pause_resume_branch_supersede_retire_visibility_determinism() -> None:
    report_a = build_continuity_transition_report()
    report_b = build_continuity_transition_report()
    assert report_a == report_b
    assert report_a["transitions"]
    assert set(x["to_state"] for x in report_a["transitions"]).issubset({"ACTIVE", "PAUSED", "INITIATED", "SUPERSEDED", "RETIRED"})


def test_continuity_scorecard_determinism_and_blocker_surfacing() -> None:
    score_a = build_mission_continuity_scorecard()
    score_b = build_mission_continuity_scorecard()
    assert score_a == score_b
    assert score_a.category in {"CONTINUITY_READY", "RESUME_READY", "STALE_BURDENED", "BLOCKED"}
    assert "stale_objective_burden" in score_a.dimensions


def test_elegance_regressions_and_invariance_guards() -> None:
    plans = build_long_horizon_plan_report()
    persistence = build_intent_persistence_report()
    continuity = build_mission_continuity_report()

    # Duplicate continuity vocabulary detection.
    assert set(plans["planStates"].values()).issubset(PLAN_STATES | {"NOT_COMPUTABLE"})

    # Redundant lifecycle grammar detection.
    assert set(continuity["missionStates"].values()).issubset(
        {
            "ACTIVE_MISSION",
            "STAGED_PLAN",
            "PAUSED_CONTINUITY",
            "RESUMABLE_CONTINUITY",
            "BRANCHED_CONTINUITY",
            "SUPERSEDED_CONTINUITY",
            "RETIRED_MISSION",
            "DEGRADED",
            "NOT_COMPUTABLE",
        }
    )

    # Stale-intent masking detection.
    if persistence["staleIntents"]:
        assert any(v == "STALE_INTENT" for v in persistence["intentStates"].values())

    # Silent-reactivation drift detection.
    assert not (
        any(v == "ACTIVE_INTENT" for v in persistence["intentStates"].values())
        and any(v == "RETIRED_MISSION" for v in continuity["missionStates"].values())
        and all(v != "RETIRED_INTENT" for v in persistence["intentStates"].values())
    )
