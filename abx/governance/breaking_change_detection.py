from __future__ import annotations

from abx.governance.canonical_manifest import BASELINE_ID
from abx.governance.migration_guards import run_migration_guards
from abx.governance.types import BreakingChangeReport
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def scan_breaking_changes() -> BreakingChangeReport:
    guard = run_migration_guards()

    additive_changes = list(guard.compatible_additive)
    breaking_changes = list(guard.breaking)
    migration_required_changes = list(guard.migration_required)
    heuristic_warnings: list[str] = []

    if guard.status in {"MIGRATION_REQUIRED", "BREAKING"}:
        heuristic_warnings.append("classification-is-rule-based-not-full-ast-schema-semantic")

    if guard.status == "NOT_COMPUTABLE":
        status = "NOT_COMPUTABLE"
    elif breaking_changes:
        status = "BREAKING"
    elif migration_required_changes:
        status = "MIGRATION_REQUIRED"
    else:
        status = "NON_BREAKING"

    payload = {
        "baseline_id": BASELINE_ID,
        "status": status,
        "additive_changes": additive_changes,
        "breaking_changes": breaking_changes,
        "migration_required_changes": migration_required_changes,
        "heuristic_warnings": heuristic_warnings,
    }
    report_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))

    return BreakingChangeReport(
        artifact_type="BreakingChangeReport.v1",
        artifact_id="breaking-change-scan-abx",
        baseline_id=BASELINE_ID,
        status=status,
        additive_changes=additive_changes,
        breaking_changes=breaking_changes,
        migration_required_changes=migration_required_changes,
        heuristic_warnings=heuristic_warnings,
        report_hash=report_hash,
    )
