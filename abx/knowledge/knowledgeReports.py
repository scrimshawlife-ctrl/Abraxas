from __future__ import annotations

from abx.knowledge.knowledgeClassification import classify_knowledge_surfaces
from abx.knowledge.knowledgeInventory import build_knowledge_inventory, classify_active_vs_historical
from abx.knowledge.knowledgeOwnership import knowledge_ownership_report
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_knowledge_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "KnowledgeAudit.v1",
        "artifactId": "knowledge-audit",
        "surfaces": [x.__dict__ for x in build_knowledge_inventory()],
        "classification": classify_knowledge_surfaces(),
        "ownership": knowledge_ownership_report(),
        "activeVsHistorical": [x.__dict__ for x in classify_active_vs_historical()],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
