from __future__ import annotations

from datetime import date
from pathlib import Path

from abx.governance.baseline_enforcement import run_baseline_enforcement
from abx.governance.health_scorecard import build_repo_health_scorecard
from abx.governance.types import MaintenanceCycleArtifact, MaintenanceSummaryArtifact
from abx.governance.upgrade_plan import build_governed_upgrade_plan
from abx.governance.waivers import build_waiver_audit
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def run_maintenance_cycle(*, repo_root: Path, cycle_id: str | None = None) -> tuple[MaintenanceCycleArtifact, MaintenanceSummaryArtifact]:
    cycle_key = cycle_id or f"cycle-{date.today()}"
    enforcement = run_baseline_enforcement(repo_root=repo_root)
    waivers = build_waiver_audit()
    health = build_repo_health_scorecard(repo_root=repo_root)
    upgrade = build_governed_upgrade_plan({})

    checks_run = [
        enforcement.artifact_type,
        waivers.artifact_type,
        health.artifact_type,
        upgrade.artifact_type,
    ]

    blockers = sorted(set(enforcement.blocking_checks) | set(health.blockers) | set(upgrade.blockers))
    stale_waivers = sorted(row["waiver_id"] for row in waivers.expired_waivers)

    if stale_waivers:
        cycle_state = "WAIVER_STALE"
    elif blockers:
        cycle_state = "BASELINE_DRIFT_RISK"
    elif upgrade.readiness_state == "NEEDS_MIGRATION_BUNDLE":
        cycle_state = "UPGRADE_BACKLOG"
    elif enforcement.status == "PASS":
        cycle_state = "HEALTHY"
    else:
        cycle_state = "NEEDS_REVIEW"

    cycle_payload = {
        "cycle_id": cycle_key,
        "cycle_state": cycle_state,
        "checks_run": checks_run,
        "blockers": blockers,
    }
    cycle_hash = sha256_bytes(dumps_stable(cycle_payload).encode("utf-8"))

    cycle_artifact = MaintenanceCycleArtifact(
        artifact_type="MaintenanceCycleArtifact.v1",
        artifact_id=f"maintenance-cycle-{cycle_key}",
        cycle_id=cycle_key,
        cadence="weekly",
        cycle_state=cycle_state,
        checks_run=checks_run,
        blockers=blockers,
        cycle_hash=cycle_hash,
    )

    summary_payload = {
        "latest_cycle_id": cycle_key,
        "summary_state": cycle_state,
        "stale_waivers": stale_waivers,
        "drift_risks": blockers,
        "upgrade_backlog": upgrade.migration_bundle_refs,
    }
    summary_hash = sha256_bytes(dumps_stable(summary_payload).encode("utf-8"))

    summary_artifact = MaintenanceSummaryArtifact(
        artifact_type="MaintenanceSummaryArtifact.v1",
        artifact_id="maintenance-summary-abx",
        latest_cycle_id=cycle_key,
        summary_state=cycle_state,
        stale_waivers=stale_waivers,
        drift_risks=blockers,
        upgrade_backlog=upgrade.migration_bundle_refs,
        summary_hash=summary_hash,
    )

    return cycle_artifact, summary_artifact
