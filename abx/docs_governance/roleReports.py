from __future__ import annotations

from abx.docs_governance.roleCoverage import classify_role_legibility
from abx.docs_governance.roleEntrypoints import detect_role_terminology_drift
from abx.docs_governance.roleInventory import build_onboarding_entries, build_role_entrypoints, build_role_inventory
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_role_legibility_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "RoleLegibilityAudit.v1",
        "artifactId": "role-legibility-audit",
        "roles": [x.__dict__ for x in build_role_inventory()],
        "onboardingEntries": [x.__dict__ for x in build_onboarding_entries()],
        "roleEntrypoints": [x.__dict__ for x in build_role_entrypoints()],
        "coverage": classify_role_legibility(),
        "terminologyDrift": detect_role_terminology_drift(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
