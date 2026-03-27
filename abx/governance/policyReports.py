from __future__ import annotations

from abx.governance.policyClassification import classify_policy_surfaces, detect_duplicate_policy_surfaces
from abx.governance.policyInventory import build_policy_inventory
from abx.governance.policyOwnership import policy_ownership_report
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_policy_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "PolicySurfaceAudit.v1",
        "artifactId": "policy-surface-audit",
        "policies": [x.__dict__ for x in build_policy_inventory()],
        "classification": classify_policy_surfaces(),
        "ownership": policy_ownership_report(),
        "duplicates": detect_duplicate_policy_surfaces(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
