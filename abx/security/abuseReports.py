from __future__ import annotations

from abx.security.abuseClassification import classify_abuse_paths, detect_inconsistent_abuse_taxonomy
from abx.security.abuseContainment import classify_abuse_containment, validate_containment_linkage
from abx.security.abuseInventory import build_abuse_containment_inventory, build_abuse_path_inventory
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_abuse_path_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "AbusePathAudit.v1",
        "artifactId": "abuse-path-audit",
        "paths": [x.__dict__ for x in build_abuse_path_inventory()],
        "containment": [x.__dict__ for x in build_abuse_containment_inventory()],
        "classification": classify_abuse_paths(),
        "containmentClassification": classify_abuse_containment(),
        "inconsistentTaxonomy": detect_inconsistent_abuse_taxonomy(),
        "missingContainmentLinks": validate_containment_linkage(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
