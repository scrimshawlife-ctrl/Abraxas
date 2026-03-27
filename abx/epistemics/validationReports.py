from __future__ import annotations

from abx.epistemics.validationClassification import (
    classify_validation_kinds,
    classify_validation_surfaces,
    detect_duplicate_epistemic_vocabulary,
)
from abx.epistemics.validationInventory import build_validation_surface_inventory
from abx.epistemics.validationOwnership import build_validation_ownership
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_validation_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "ValidationAudit.v1",
        "artifactId": "validation-audit",
        "surfaces": [x.__dict__ for x in build_validation_surface_inventory()],
        "classification": classify_validation_surfaces(),
        "kindClassification": classify_validation_kinds(),
        "ownership": build_validation_ownership(),
        "vocabularyConflicts": detect_duplicate_epistemic_vocabulary(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
