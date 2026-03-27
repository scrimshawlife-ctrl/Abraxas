from __future__ import annotations

from pathlib import Path

from abx.governance.breaking_change_detection import scan_breaking_changes
from abx.governance.canonical_manifest import BASELINE_ID, manifest_diff_against_frozen
from abx.governance.health_scorecard import build_repo_health_scorecard
from abx.governance.migration_guards import run_migration_guards
from abx.governance.types import BaselineEnforcementResult
from abx.governance.waivers import build_waiver_audit
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def run_baseline_enforcement(*, repo_root: Path) -> BaselineEnforcementResult:
    manifest_diff = manifest_diff_against_frozen()
    guards = run_migration_guards()
    breaks = scan_breaking_changes()
    health = build_repo_health_scorecard(repo_root=repo_root)
    waivers = build_waiver_audit()

    blocking_checks: list[str] = []
    warning_checks: list[str] = []
    informational_checks: list[str] = []

    if manifest_diff.get("status") == "DRIFT":
        blocking_checks.append("manifest-drift-detected")
    elif manifest_diff.get("status") == "NOT_COMPUTABLE":
        warning_checks.append("manifest-state-not-computable")

    if guards.status == "BREAKING":
        blocking_checks.append("migration-guard-breaking")
    elif guards.status == "MIGRATION_REQUIRED":
        warning_checks.append("migration-guard-required")

    if breaks.status == "BREAKING":
        blocking_checks.append("breaking-change-detected")
    elif breaks.status == "MIGRATION_REQUIRED":
        warning_checks.append("breaking-scan-migration-required")

    if health.overall_status == "BLOCKED":
        warning_checks.append("health-blocked")
    informational_checks.extend(sorted(health.weak_zones))

    active_waived = {
        c
        for row in waivers.active_waivers
        for c in row.get("related_checks", [])
    }
    waived_checks = sorted(x for x in warning_checks if x in active_waived)
    warning_checks = sorted(x for x in warning_checks if x not in active_waived)

    if blocking_checks:
        status = "FAIL"
    elif warning_checks:
        status = "WARN"
    else:
        status = "PASS"

    payload = {
        "baseline_id": BASELINE_ID,
        "status": status,
        "blocking_checks": sorted(set(blocking_checks)),
        "warning_checks": sorted(set(warning_checks)),
        "informational_checks": sorted(set(informational_checks)),
        "waived_checks": waived_checks,
    }
    enforcement_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))

    return BaselineEnforcementResult(
        artifact_type="BaselineEnforcementResult.v1",
        artifact_id="baseline-enforcement-abx",
        baseline_id=BASELINE_ID,
        status=status,
        blocking_checks=payload["blocking_checks"],
        warning_checks=payload["warning_checks"],
        informational_checks=payload["informational_checks"],
        waived_checks=payload["waived_checks"],
        enforcement_hash=enforcement_hash,
    )


def run_ci_enforcement_gate(*, repo_root: Path) -> int:
    result = run_baseline_enforcement(repo_root=repo_root)
    return 1 if result.status == "FAIL" else 0
