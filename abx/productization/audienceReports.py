from __future__ import annotations

from abx.productization.audienceCoverage import classify_audience_legibility
from abx.productization.audienceEntrypoints import detect_audience_terminology_drift
from abx.productization.audienceInventory import build_audience_entrypoints, build_audience_inventory
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_audience_legibility_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "AudienceLegibilityAudit.v1",
        "artifactId": "audience-legibility-audit",
        "audiences": [x.__dict__ for x in build_audience_inventory()],
        "entrypoints": [x.__dict__ for x in build_audience_entrypoints()],
        "coverage": classify_audience_legibility(),
        "terminologyDrift": detect_audience_terminology_drift(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
