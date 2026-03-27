from __future__ import annotations

from dataclasses import asdict

from abx.operations.types import RunbookArtifact, RunbookExecutionSummary, WorkflowStep
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _runbook_templates() -> dict[str, dict[str, object]]:
    return {
        "governance-check": {
            "category": "governance",
            "preflight": ["python scripts/run_baseline_enforcement.py"],
            "steps": [
                WorkflowStep("step.baseline", "python scripts/run_baseline_enforcement.py", "BaselineEnforcementResult.v1", "halt"),
                WorkflowStep("step.migration", "python scripts/run_migration_guards.py", "MigrationGuardResult.v1", "halt"),
                WorkflowStep("step.breaking", "python scripts/run_breaking_change_scan.py", "BreakingChangeReport.v1", "halt"),
            ],
            "completion_checks": ["no-blocking-checks", "deterministic-artifacts"],
        },
        "simulation-proof-closure": {
            "category": "runtime",
            "preflight": ["python scripts/run_operator_workflow.py --help"],
            "steps": [
                WorkflowStep("step.simulation", "python scripts/run_operator_console_check.py /tmp/scenario.json", "SimulationArtifact.v1", "contain"),
                WorkflowStep("step.proof", "python scripts/run_proof_chain_validation.py /tmp/scenario.json", "ProofChainArtifact.v1", "contain"),
                WorkflowStep("step.closure", "python scripts/run_closure_summary.py /tmp/scenario.json", "ClosureSummaryArtifact.v1", "contain"),
            ],
            "completion_checks": ["proof-chain-valid-or-explained", "closure-summary-emitted"],
        },
        "maintenance-cycle": {
            "category": "maintenance",
            "preflight": ["python scripts/run_waiver_audit.py"],
            "steps": [
                WorkflowStep("step.waivers", "python scripts/run_waiver_audit.py", "WaiverAuditArtifact.v1", "review"),
                WorkflowStep("step.maintenance", "python scripts/run_maintenance_cycle.py", "MaintenanceCycleArtifact.v1", "review"),
            ],
            "completion_checks": ["cycle-state-recorded", "summary-artifact-updated"],
        },
        "incident-triage": {
            "category": "incident",
            "preflight": ["python scripts/run_failure_domain_audit.py"],
            "steps": [
                WorkflowStep("step.incident", "python scripts/run_incident_report.py", "IncidentSummaryArtifact.v1", "escalate"),
                WorkflowStep("step.rollback-plan", "python scripts/run_rollback_plan.py", "RollbackPlanArtifact.v1", "escalate"),
            ],
            "completion_checks": ["incident-categorized", "rollback-path-determined"],
        },
    }


def build_runbooks() -> list[RunbookArtifact]:
    rows: list[RunbookArtifact] = []
    for runbook_id, spec in sorted(_runbook_templates().items()):
        payload = {
            "runbook_id": runbook_id,
            "category": spec["category"],
            "preflight": spec["preflight"],
            "steps": [asdict(s) for s in spec["steps"]],
            "completion_checks": spec["completion_checks"],
        }
        runbook_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))
        rows.append(
            RunbookArtifact(
                artifact_type="RunbookArtifact.v1",
                artifact_id=f"runbook-{runbook_id}",
                runbook_id=runbook_id,
                category=str(spec["category"]),
                preflight=list(spec["preflight"]),
                steps=list(spec["steps"]),
                completion_checks=list(spec["completion_checks"]),
                runbook_hash=runbook_hash,
            )
        )
    return rows


def validate_runbooks() -> dict[str, object]:
    runbooks = build_runbooks()
    issues: list[str] = []
    for row in runbooks:
        if not row.steps:
            issues.append(f"{row.runbook_id}:no-steps")
        if len(row.steps) > 6:
            issues.append(f"{row.runbook_id}:too-many-steps")
        seen = set()
        for step in row.steps:
            if step.step_id in seen:
                issues.append(f"{row.runbook_id}:duplicate-step:{step.step_id}")
            seen.add(step.step_id)

    return {
        "artifactType": "RunbookValidationArtifact.v1",
        "artifactId": "runbook-validation-abx",
        "status": "VALID" if not issues else "BROKEN",
        "issues": sorted(issues),
        "runbooks": [
            row.__dict__ | {"steps": [asdict(x) for x in row.steps]}
            for row in runbooks
        ],
    }


def summarize_runbook_execution(runbook_id: str) -> RunbookExecutionSummary:
    runbook = {x.runbook_id: x for x in build_runbooks()}[runbook_id]
    expected_outputs = [step.expected_artifact for step in runbook.steps]
    payload = {
        "runbook_id": runbook.runbook_id,
        "status": "PLANNED",
        "executed_steps": [step.step_id for step in runbook.steps],
        "expected_outputs": expected_outputs,
    }
    summary_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return RunbookExecutionSummary(
        artifact_type="RunbookExecutionSummary.v1",
        artifact_id=f"runbook-summary-{runbook_id}",
        runbook_id=runbook.runbook_id,
        status="PLANNED",
        executed_steps=payload["executed_steps"],
        expected_outputs=expected_outputs,
        summary_hash=summary_hash,
    )
