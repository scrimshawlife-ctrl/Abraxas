from __future__ import annotations

from abx.security.securityClassification import (
    classify_security_domains,
    classify_security_surfaces,
    detect_duplicate_security_vocabulary,
)
from abx.security.securityInventory import build_security_surface_inventory
from abx.security.securityOwnership import build_security_ownership
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_security_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "SecuritySurfaceAudit.v1",
        "artifactId": "security-surface-audit",
        "surfaces": [x.__dict__ for x in build_security_surface_inventory()],
        "classification": classify_security_surfaces(),
        "domains": classify_security_domains(),
        "ownership": build_security_ownership(),
        "vocabularyConflicts": detect_duplicate_security_vocabulary(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
