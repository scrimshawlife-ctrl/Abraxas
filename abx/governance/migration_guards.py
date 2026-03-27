from __future__ import annotations

from abx.governance.canonical_manifest import BASELINE_ID, manifest_diff_against_frozen
from abx.governance.schema_inventory import build_schema_mappings
from abx.governance.types import MigrationGuardResult
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _classify_manifest_diff(diff: dict[str, object]) -> tuple[list[str], list[str], list[str], list[str]]:
    compatible_additive: list[str] = []
    migration_required: list[str] = []
    breaking: list[str] = []
    not_computable: list[str] = []

    if diff.get("status") == "NOT_COMPUTABLE":
        not_computable.append("frozen-manifest-missing")
        return compatible_additive, migration_required, breaking, not_computable

    for item in diff.get("added", []):
        compatible_additive.append(f"added:{item}")
    for item in diff.get("changed", []):
        migration_required.append(f"changed:{item}")
    for item in diff.get("removed", []):
        breaking.append(f"removed:{item}")

    return compatible_additive, migration_required, breaking, not_computable


def run_migration_guards() -> MigrationGuardResult:
    diff = manifest_diff_against_frozen()
    compatible_additive, migration_required, breaking, not_computable = _classify_manifest_diff(diff)

    mapping_statuses = {x.mapping_id: x.status for x in build_schema_mappings()}
    if any(status == "DEPRECATED_CANDIDATE" for status in mapping_statuses.values()):
        migration_required.append("deprecated-schema-mappings-present")

    if not_computable:
        status = "NOT_COMPUTABLE"
    elif breaking:
        status = "BREAKING"
    elif migration_required:
        status = "MIGRATION_REQUIRED"
    elif compatible_additive:
        status = "COMPATIBLE_ADDITIVE"
    else:
        status = "COMPATIBLE_INTERNAL"

    payload = {
        "baseline_id": BASELINE_ID,
        "status": status,
        "compatible_additive": sorted(set(compatible_additive)),
        "migration_required": sorted(set(migration_required)),
        "breaking": sorted(set(breaking)),
        "not_computable": sorted(set(not_computable)),
    }
    guard_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))

    return MigrationGuardResult(
        artifact_type="MigrationGuardResult.v1",
        artifact_id="migration-guards-abx",
        baseline_id=BASELINE_ID,
        status=status,
        compatible_additive=payload["compatible_additive"],
        migration_required=payload["migration_required"],
        breaking=payload["breaking"],
        not_computable=payload["not_computable"],
        guard_hash=guard_hash,
    )
