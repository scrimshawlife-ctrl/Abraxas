from __future__ import annotations

from abx.human_factors.interactionClassification import classify_interaction_surfaces, detect_duplicate_interaction_surfaces
from abx.human_factors.interactionInventory import build_interaction_inventory
from abx.human_factors.interactionOwnership import build_interaction_ownership
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_interaction_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "InteractionAudit.v1",
        "artifactId": "interaction-audit",
        "surfaces": [x.__dict__ for x in build_interaction_inventory()],
        "classification": classify_interaction_surfaces(),
        "ownership": build_interaction_ownership(),
        "duplicates": detect_duplicate_interaction_surfaces(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
