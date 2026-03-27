from __future__ import annotations

from abx.operations.runbooks import summarize_runbook_execution
from abx.resilience.degradation import evaluate_degradation
from abx.resilience.recoveryDrills import run_recovery_drill
from abx.resilience.types import TrainingScenarioArtifact
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def run_training_scenario(scenario_id: str, drill_mode: str = "containment") -> TrainingScenarioArtifact:
    drill = run_recovery_drill(scenario_id=scenario_id, mode=drill_mode)
    degradation = evaluate_degradation(scenario_id=scenario_id, subsystem="operator")
    runbook_exec = summarize_runbook_execution(drill.runbook_id)

    guided_steps = [
        f"open-runbook:{drill.runbook_id}",
        f"execute-drill:{drill.drill_id}",
        f"confirm-degradation-state:{degradation.state}",
        "validate-governance-artifacts",
    ]
    expected_outputs = [
        "RecoveryDrillArtifact.v1",
        "DegradationStateRecord.v1",
        "RunbookExecutionSummary.v1",
    ]
    observed_outputs = [
        drill.artifact_type,
        degradation.artifact_type,
        runbook_exec.artifact_type,
    ]
    checks = {
        "drill_passed": drill.status == "PASS",
        "degradation_explicit": degradation.state in {"FULL", "DEGRADED", "LIMITED", "BLOCKED"},
        "runbook_planned": runbook_exec.status == "PLANNED",
    }
    evaluation_summary = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "operator_readiness": "READY" if all(checks.values()) else "NEEDS_REVIEW",
    }

    payload = {
        "scenario_id": scenario_id,
        "drill_id": drill.drill_id,
        "guided_steps": guided_steps,
        "expected_outputs": expected_outputs,
        "observed_outputs": observed_outputs,
        "evaluation": evaluation_summary,
    }
    training_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))

    return TrainingScenarioArtifact(
        artifact_type="TrainingScenarioArtifact.v1",
        artifact_id=f"training-scenario-{scenario_id}",
        scenario_id=scenario_id,
        drill_id=drill.drill_id,
        guided_steps=guided_steps,
        expected_outputs=expected_outputs,
        observed_outputs=observed_outputs,
        evaluation_summary=evaluation_summary,
        training_hash=training_hash,
    )


def render_training_report(scenario_id: str, drill_mode: str = "containment") -> dict[str, object]:
    artifact = run_training_scenario(scenario_id=scenario_id, drill_mode=drill_mode)
    return {
        "artifactType": artifact.artifact_type,
        "artifactId": artifact.artifact_id,
        "scenarioId": artifact.scenario_id,
        "drillId": artifact.drill_id,
        "guidedSteps": artifact.guided_steps,
        "expectedOutputs": artifact.expected_outputs,
        "observedOutputs": artifact.observed_outputs,
        "evaluationSummary": artifact.evaluation_summary,
        "trainingHash": artifact.training_hash,
    }
