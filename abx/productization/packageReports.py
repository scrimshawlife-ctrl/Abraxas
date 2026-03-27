from __future__ import annotations

from abx.productization.packageClassification import classify_package_types
from abx.productization.packageCompatibility import classify_package_compatibility, detect_redundant_package_dialects
from abx.productization.packagingContracts import build_packaging_contracts
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_packaging_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "PackagingAudit.v1",
        "artifactId": "packaging-audit",
        "contracts": [x.__dict__ for x in build_packaging_contracts()],
        "classification": classify_package_types(),
        "compatibility": classify_package_compatibility(),
        "redundantDialects": detect_redundant_package_dialects(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
