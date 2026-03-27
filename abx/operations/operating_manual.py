from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from abx.governance.canonical_manifest import BASELINE_ID, BASELINE_VERSION
from abx.governance.maintenance_cycle import run_maintenance_cycle
from abx.operations.failure_domains import failure_domain_audit_report
from abx.operations.incidents import build_incident_summary
from abx.operations.runbooks import build_runbooks, validate_runbooks
from abx.operations.service_expectations import expectation_report
from abx.operations.types import OperatingManualArtifact
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_operating_manual() -> OperatingManualArtifact:
    runbooks = build_runbooks()
    runbook_validation = validate_runbooks()
    incidents = build_incident_summary()
    failure_domains = failure_domain_audit_report()
    expectations = expectation_report()
    maintenance_cycle, maintenance_summary = run_maintenance_cycle(repo_root=Path("."), cycle_id="manual-cycle")

    sections = {
        "overview": {
            "baseline_id": BASELINE_ID,
            "baseline_version": BASELINE_VERSION,
            "operator_modes": ["governance-check", "simulation-proof-closure", "maintenance-cycle", "incident-triage"],
        },
        "runbooks": {
            "validation": runbook_validation,
            "items": [x.__dict__ | {"steps": [asdict(s) for s in x.steps]} for x in runbooks],
        },
        "incident_response": {
            "summary": incidents.__dict__,
            "rollback_note": "Rollback supported only for incidents marked rollback_possible.",
        },
        "failure_domains": failure_domains,
        "service_expectations": expectations,
        "maintenance": {
            "cycle": maintenance_cycle.__dict__,
            "summary": maintenance_summary.__dict__,
        },
        "entrypoints": {
            "scripts": [
                "scripts/run_runbook_check.py",
                "scripts/run_incident_report.py",
                "scripts/run_rollback_plan.py",
                "scripts/run_failure_domain_audit.py",
                "scripts/run_service_expectations.py",
                "scripts/run_operating_manual.py",
            ]
        },
    }

    payload = {
        "baseline_id": BASELINE_ID,
        "baseline_version": BASELINE_VERSION,
        "sections": sections,
    }
    manual_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))

    return OperatingManualArtifact(
        artifact_type="OperatingManualArtifact.v1",
        artifact_id="operating-manual-abx",
        baseline_id=BASELINE_ID,
        baseline_version=BASELINE_VERSION,
        sections=sections,
        manual_hash=manual_hash,
    )
