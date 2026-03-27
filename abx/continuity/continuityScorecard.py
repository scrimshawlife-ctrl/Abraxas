from __future__ import annotations

from abx.continuity.continuityReports import build_mission_continuity_report
from abx.continuity.persistenceReports import build_intent_persistence_report
from abx.continuity.planReports import build_long_horizon_plan_report
from abx.continuity.transitionReports import build_continuity_transition_report
from abx.continuity.types import MissionContinuityScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, stale_burden: bool, blocked: bool, resume_ready: bool) -> str:
    if blocked:
        return "BLOCKED"
    if stale_burden:
        return "STALE_BURDENED"
    if resume_ready:
        return "RESUME_READY"
    return "CONTINUITY_READY"


def build_mission_continuity_scorecard() -> MissionContinuityScorecard:
    plans = build_long_horizon_plan_report()
    persistence = build_intent_persistence_report()
    continuity = build_mission_continuity_report()
    transitions = build_continuity_transition_report()

    stale_burden = bool(persistence["staleIntents"])
    blocked = any(v == "BLOCKED" for v in plans["planStates"].values())
    resume_ready = any(v == "RESUMABLE_INTENT" for v in persistence["intentStates"].values())

    dimensions = {
        "mission_state_clarity": "EXPLICIT",
        "persistence_liveness_quality": "STALE_BURDENED" if stale_burden else "HEALTHY",
        "continuity_lineage_integrity": "EXPLICIT",
        "pause_resume_validation_quality": "PARTIAL" if resume_ready else "GOVERNED",
        "branch_supersession_explicitness": "EXPLICIT" if transitions["supersessions"] else "PARTIAL",
        "stale_objective_burden": "ELEVATED" if stale_burden else "LOW",
        "retirement_hygiene": "GOVERNED" if transitions["retirements"] else "PARTIAL",
        "continuity_loss_burden": "LOW",
        "revalidation_discipline": "ENFORCED" if resume_ready else "OPTIONAL",
        "operator_long_horizon_clarity": "EXPLICIT",
    }
    blockers = sorted(
        key for key, value in dimensions.items() if value in {"STALE_BURDENED", "BLOCKED", "NOT_COMPUTABLE"}
    )
    evidence = {
        "plans": [plans["auditHash"]],
        "persistence": [persistence["auditHash"]],
        "continuity": [continuity["auditHash"]],
        "transitions": [transitions["auditHash"]],
        "staleIntents": persistence["staleIntents"],
    }
    category = _category(stale_burden=stale_burden, blocked=blocked, resume_ready=resume_ready)
    digest = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}).encode("utf-8"))
    return MissionContinuityScorecard(
        artifact_type="MissionContinuityScorecard.v1",
        artifact_id="mission-continuity-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=digest,
    )
