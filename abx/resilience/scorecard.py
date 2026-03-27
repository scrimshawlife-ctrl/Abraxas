from __future__ import annotations

from abx.resilience.degradation import evaluate_degradation
from abx.resilience.faultInjection import plan_fault_injection
from abx.resilience.recoveryDrills import run_recovery_drill
from abx.resilience.training import run_training_scenario
from abx.resilience.types import ResilienceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_resilience_scorecard(scenario_id: str) -> ResilienceScorecard:
    fault = plan_fault_injection(scenario_id=scenario_id)
    drill = run_recovery_drill(scenario_id=scenario_id, mode="containment")
    degradation = evaluate_degradation(scenario_id=scenario_id)
    training = run_training_scenario(scenario_id=scenario_id, drill_mode="containment")

    dimensions = {
        "failure_coverage": "COVERED" if bool(fault.injection_plan) else "GAP",
        "recovery_success": "PASS" if drill.status == "PASS" else "GAP",
        "degradation_clarity": "EXPLICIT" if degradation.state in {"FULL", "DEGRADED", "LIMITED", "BLOCKED"} else "GAP",
        "operator_readiness": str(training.evaluation_summary["operator_readiness"]),
        "invariance_under_stress": "PASS" if fault.injection_hash and drill.drill_hash else "NEEDS_EVIDENCE",
    }
    evidence = {
        "failure_coverage": [fault.artifact_id, fault.injection_hash],
        "recovery_success": [drill.artifact_id, drill.drill_hash],
        "degradation_clarity": [degradation.artifact_id, degradation.state_hash],
        "operator_readiness": [training.artifact_id, training.training_hash],
        "invariance_under_stress": [fault.injection_hash, drill.drill_hash],
    }
    blockers = sorted([k for k, v in dimensions.items() if v in {"GAP", "NEEDS_REVIEW", "NEEDS_EVIDENCE"}])

    payload = {
        "scenario_id": scenario_id,
        "dimensions": dimensions,
        "evidence": evidence,
        "blockers": blockers,
    }
    scorecard_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return ResilienceScorecard(
        artifact_type="ResilienceScorecard.v1",
        artifact_id=f"resilience-scorecard-{scenario_id}",
        scenario_id=scenario_id,
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=scorecard_hash,
    )


def render_resilience_scorecard(scenario_id: str) -> dict[str, object]:
    artifact = build_resilience_scorecard(scenario_id=scenario_id)
    return {
        "artifactType": artifact.artifact_type,
        "artifactId": artifact.artifact_id,
        "scenarioId": artifact.scenario_id,
        "dimensions": artifact.dimensions,
        "evidence": artifact.evidence,
        "blockers": artifact.blockers,
        "scorecardHash": artifact.scorecard_hash,
    }
