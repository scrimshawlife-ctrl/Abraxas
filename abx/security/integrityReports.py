from __future__ import annotations

from abx.security.integrityInventory import build_integrity_inventory, build_tamper_resistance_inventory
from abx.security.integrityVerification import classify_integrity_verification, detect_integrity_mismatches
from abx.security.tamperClassification import classify_tamper_resistance
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_integrity_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "IntegrityAudit.v1",
        "artifactId": "integrity-audit",
        "integrityVerification": [x.__dict__ for x in build_integrity_inventory()],
        "tamperResistance": [x.__dict__ for x in build_tamper_resistance_inventory()],
        "verificationClassification": classify_integrity_verification(),
        "tamperClassification": classify_tamper_resistance(),
        "mismatches": detect_integrity_mismatches(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
