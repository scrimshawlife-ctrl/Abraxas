from __future__ import annotations

from abx.federation.handoffEnvelopes import build_handoff_envelopes
from abx.federation.interopClassification import classify_interop_paths, detect_redundant_interop_patterns
from abx.federation.interopInventory import build_interop_inventory
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_interop_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "InteropAudit.v1",
        "artifactId": "interop-audit",
        "inventory": [x.__dict__ for x in build_interop_inventory()],
        "classification": classify_interop_paths(),
        "handoffEnvelopes": [x.__dict__ for x in build_handoff_envelopes()],
        "redundantPatterns": detect_redundant_interop_patterns(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
