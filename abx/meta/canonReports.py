from __future__ import annotations

from abx.meta.canonClassification import classify_canon_surfaces, detect_canon_taxonomy_drift, detect_duplicate_canon_home
from abx.meta.canonInventory import build_canon_surface_inventory
from abx.meta.canonOwnership import build_canon_ownership_map, detect_unowned_canon_surfaces
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_canon_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "CanonSurfaceAudit.v1",
        "artifactId": "canon-surface-audit",
        "canon": [x.__dict__ for x in build_canon_surface_inventory()],
        "classification": classify_canon_surfaces(),
        "ownership": build_canon_ownership_map(),
        "unowned": detect_unowned_canon_surfaces(),
        "taxonomyDrift": detect_canon_taxonomy_drift(),
        "duplicateHome": detect_duplicate_canon_home(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
