from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from abx.governance.baseline_enforcement import run_baseline_enforcement
from abx.governance.breaking_change_detection import scan_breaking_changes
from abx.governance.canonical_manifest import BASELINE_ID
from abx.governance.migration_guards import run_migration_guards
from abx.operations.types import (
    IncidentRecord,
    IncidentSummaryArtifact,
    RollbackExecutionSummary,
    RollbackPlanArtifact,
    WorkflowStep,
)
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def classify_incidents() -> list[IncidentRecord]:
    incidents: list[IncidentRecord] = []
    enforcement = run_baseline_enforcement(repo_root=Path("."))
    guards = run_migration_guards()
    breaks = scan_breaking_changes()

    if enforcement.status == "FAIL":
        incidents.append(
            IncidentRecord(
                incident_id="inc.baseline-enforcement",
                category="baseline_enforcement_failure",
                severity="HIGH",
                affected_surfaces=["governance/baseline"],
                evidence_refs=[enforcement.artifact_id],
                rollback_possible=True,
            )
        )
    if guards.status == "BREAKING":
        incidents.append(
            IncidentRecord(
                incident_id="inc.migration-breach",
                category="migration_guard_breach",
                severity="HIGH",
                affected_surfaces=["schema/canonical"],
                evidence_refs=[guards.artifact_id],
                rollback_possible=True,
            )
        )
    if breaks.status == "BREAKING":
        incidents.append(
            IncidentRecord(
                incident_id="inc.breaking-regression",
                category="breaking_change_regression",
                severity="CRITICAL",
                affected_surfaces=["runtime/frame", "proof/closure", "governance"],
                evidence_refs=[breaks.artifact_id],
                rollback_possible=True,
            )
        )

    if not incidents:
        incidents.append(
            IncidentRecord(
                incident_id="inc.none",
                category="no_active_incident",
                severity="LOW",
                affected_surfaces=[],
                evidence_refs=[],
                rollback_possible=False,
            )
        )

    return incidents


def build_incident_summary() -> IncidentSummaryArtifact:
    incidents = [asdict(x) for x in classify_incidents()]
    payload = {"incidents": incidents}
    summary_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return IncidentSummaryArtifact(
        artifact_type="IncidentSummaryArtifact.v1",
        artifact_id=f"incident-summary-{BASELINE_ID.lower()}",
        incidents=incidents,
        summary_hash=summary_hash,
    )


def build_rollback_plan(incident_id: str) -> RollbackPlanArtifact:
    incidents = {x.incident_id: x for x in classify_incidents()}
    target = incidents.get(incident_id) or IncidentRecord(
        incident_id=incident_id,
        category="unknown",
        severity="MEDIUM",
        affected_surfaces=[],
        evidence_refs=[],
        rollback_possible=False,
    )

    strategy = "rollback-to-frozen-baseline" if target.rollback_possible else "patch-forward-only"
    rollback_steps = [
        WorkflowStep("rollback.preflight", "python scripts/run_baseline_enforcement.py", "BaselineEnforcementResult.v1", "abort"),
        WorkflowStep("rollback.apply", "git checkout abx/governance/frozen/canonical_manifest_v1.json", "rollback-marker", "abort"),
    ] if target.rollback_possible else []

    payload = {
        "incident_id": incident_id,
        "strategy": strategy,
        "pre_validation": ["confirm-incident-evidence"],
        "rollback_steps": [asdict(x) for x in rollback_steps],
        "post_validation": ["python scripts/run_baseline_enforcement.py"],
    }
    rollback_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))

    return RollbackPlanArtifact(
        artifact_type="RollbackPlanArtifact.v1",
        artifact_id=f"rollback-plan-{incident_id}",
        incident_id=incident_id,
        strategy=strategy,
        pre_validation=payload["pre_validation"],
        rollback_steps=rollback_steps,
        post_validation=payload["post_validation"],
        rollback_hash=rollback_hash,
    )


def summarize_rollback_execution(incident_id: str) -> RollbackExecutionSummary:
    plan = build_rollback_plan(incident_id)
    status = "UNSUPPORTED" if not plan.rollback_steps else "PLANNED"
    payload = {
        "incident_id": incident_id,
        "status": status,
        "executed_steps": [x.step_id for x in plan.rollback_steps],
    }
    summary_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return RollbackExecutionSummary(
        artifact_type="RollbackExecutionSummary.v1",
        artifact_id=f"rollback-summary-{incident_id}",
        incident_id=incident_id,
        status=status,
        executed_steps=payload["executed_steps"],
        summary_hash=summary_hash,
    )
