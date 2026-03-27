from __future__ import annotations

from abx.docs_governance.docClassification import classify_doc_surfaces, detect_duplicate_doc_surfaces
from abx.docs_governance.docInventory import build_doc_inventory
from abx.docs_governance.docOwnership import build_doc_ownership
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_doc_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "DocumentationAudit.v1",
        "artifactId": "documentation-audit",
        "surfaces": [x.__dict__ for x in build_doc_inventory()],
        "classification": classify_doc_surfaces(),
        "ownership": build_doc_ownership(),
        "duplicates": detect_duplicate_doc_surfaces(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
