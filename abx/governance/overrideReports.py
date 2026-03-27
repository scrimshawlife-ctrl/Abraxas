from __future__ import annotations

from abx.governance.overrideClassification import classify_overrides, detect_stale_overrides
from abx.governance.overrideInventory import build_override_inventory
from abx.governance.overridePrecedence import build_override_precedence
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_override_audit_report() -> dict[str, object]:
    precedence = build_override_precedence()
    report = {
        "artifactType": "OverrideAudit.v1",
        "artifactId": "override-audit",
        "overrides": [x.__dict__ for x in build_override_inventory()],
        "classification": classify_overrides(),
        "stale": detect_stale_overrides(),
        "precedence": precedence.__dict__,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
