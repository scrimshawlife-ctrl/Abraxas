from __future__ import annotations

from dataclasses import asdict

from abx.operations.incidents import build_rollback_plan, summarize_rollback_execution
from abx.operations.runbooks import build_runbooks, summarize_runbook_execution
from abx.resilience.faultInjection import plan_fault_injection
from abx.resilience.types import RecoveryDrillArtifact
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _pick_runbook(mode: str) -> str:
    runbook_ids = {x.runbook_id for x in build_runbooks()}
    preferred = {
        "rollback": "incident-triage",
        "patch-forward": "governance-check",
        "containment": "simulation-proof-closure",
    }[mode]
    return preferred if preferred in runbook_ids else sorted(runbook_ids)[0]


def run_recovery_drill(scenario_id: str, mode: str, incident_id: str = "inc.none") -> RecoveryDrillArtifact:
    if mode not in {"rollback", "patch-forward", "containment"}:
        raise ValueError(f"unsupported recovery mode: {mode}")

    fault = plan_fault_injection(scenario_id=scenario_id)
    runbook_id = _pick_runbook(mode)
    runbook_summary = summarize_runbook_execution(runbook_id)
    rollback_plan = build_rollback_plan(incident_id)
    rollback_summary = summarize_rollback_execution(incident_id)

    expected = {
        "rollback": ["rollback-plan-emitted", "rollback-status-planned-or-unsupported"],
        "patch-forward": ["runbook-summary-emitted", "governance-path-selected"],
        "containment": ["fault-plan-emitted", "containment-runbook-selected"],
    }[mode]

    actual = [
        "fault-plan-emitted" if fault.injection_plan else "fault-plan-empty",
        "runbook-summary-emitted" if runbook_summary.status == "PLANNED" else "runbook-summary-missing",
        "rollback-plan-emitted" if rollback_plan.artifact_id else "rollback-plan-missing",
        f"rollback-status-{rollback_summary.status.lower()}",
    ]

    comparison = {item: ("MATCH" if item in actual else "MISSING") for item in expected}
    status = "PASS" if all(v == "MATCH" for v in comparison.values()) else "FAIL"

    payload = {
        "drill_id": f"drill.{mode}.{scenario_id}",
        "scenario_id": scenario_id,
        "mode": mode,
        "runbook_id": runbook_id,
        "expected": expected,
        "actual": actual,
        "comparison": comparison,
        "status": status,
        "linked_artifacts": [
            runbook_summary.artifact_id,
            rollback_plan.artifact_id,
            rollback_summary.artifact_id,
            fault.artifact_id,
        ],
    }
    drill_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return RecoveryDrillArtifact(
        artifact_type="RecoveryDrillArtifact.v1",
        artifact_id=f"recovery-drill-{mode}-{scenario_id}",
        drill_id=payload["drill_id"],
        scenario_id=scenario_id,
        mode=mode,
        runbook_id=runbook_id,
        expected_outcomes=expected,
        actual_outcomes=actual,
        comparison=comparison,
        status=status,
        drill_hash=drill_hash,
    )


def render_recovery_drill_report(scenario_id: str, mode: str, incident_id: str = "inc.none") -> dict[str, object]:
    artifact = run_recovery_drill(scenario_id=scenario_id, mode=mode, incident_id=incident_id)
    return {
        "artifactType": artifact.artifact_type,
        "artifactId": artifact.artifact_id,
        "drillId": artifact.drill_id,
        "scenarioId": artifact.scenario_id,
        "mode": artifact.mode,
        "runbookId": artifact.runbook_id,
        "expectedOutcomes": artifact.expected_outcomes,
        "actualOutcomes": artifact.actual_outcomes,
        "comparison": artifact.comparison,
        "status": artifact.status,
        "drillHash": artifact.drill_hash,
    }
