from __future__ import annotations

from pathlib import Path
from typing import Any

from abx.governance.breaking_change_detection import scan_breaking_changes
from abx.governance.canonical_manifest import BASELINE_ID, BASELINE_VERSION, build_canonical_manifest
from abx.governance.migration_guards import run_migration_guards
from abx.governance.types import GovernedUpgradePlan
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_governed_upgrade_plan(payload: dict[str, Any]) -> GovernedUpgradePlan:
    baseline_to = str(payload.get("baseline_to") or "ABX-GOV-BASELINE-002")
    target_version = str(payload.get("target_version") or "v1.1.0-rc0")

    manifest = build_canonical_manifest()
    guards = run_migration_guards()
    breaks = scan_breaking_changes()

    affected_surfaces = sorted(m["member_id"] for m in manifest.members if m["classification"] == "AUTHORITATIVE")

    if breaks.status == "BREAKING":
        compatibility_status = "BREAKING_MAJOR"
        readiness_state = "BLOCKED"
    elif guards.status == "MIGRATION_REQUIRED":
        compatibility_status = "MIGRATION_BACKED"
        readiness_state = "NEEDS_MIGRATION_BUNDLE"
    elif guards.status in {"COMPATIBLE_ADDITIVE", "COMPATIBLE_INTERNAL"}:
        compatibility_status = "ADDITIVE_UPGRADE"
        readiness_state = "READY_FOR_REVIEW"
    else:
        compatibility_status = "DEFERRED"
        readiness_state = "NOT_COMPUTABLE"

    migration_bundle_refs = []
    if compatibility_status == "MIGRATION_BACKED":
        migration_bundle_refs.append(f"migration-bundle:{BASELINE_VERSION}->{target_version}")

    blockers = []
    if breaks.status == "BREAKING":
        blockers.append("breaking-change-detected")
    if guards.status == "MIGRATION_REQUIRED":
        blockers.append("migration-bundle-required")

    plan_payload = {
        "baseline_from": BASELINE_ID,
        "baseline_to": baseline_to,
        "affected_surfaces": affected_surfaces,
        "compatibility_status": compatibility_status,
        "migration_bundle_refs": migration_bundle_refs,
        "blockers": blockers,
        "readiness_state": readiness_state,
    }
    plan_hash = sha256_bytes(dumps_stable(plan_payload).encode("utf-8"))

    return GovernedUpgradePlan(
        artifact_type="GovernedUpgradePlan.v1",
        artifact_id=f"upgrade-plan-{BASELINE_ID.lower()}-to-{baseline_to.lower()}",
        baseline_from=BASELINE_ID,
        baseline_to=baseline_to,
        affected_surfaces=affected_surfaces,
        compatibility_status=compatibility_status,
        migration_bundle_refs=migration_bundle_refs,
        blockers=blockers,
        readiness_state=readiness_state,
        plan_hash=plan_hash,
    )
