from __future__ import annotations

from abx.docs_governance.freshnessClassification import classify_freshness_states
from abx.docs_governance.freshnessInventory import build_freshness_inventory
from abx.docs_governance.refreshDependencies import build_refresh_dependencies
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def detect_stale_generated_manual_mismatch() -> list[str]:
    stale_docs = {x.doc_id for x in build_freshness_inventory() if x.freshness_state == "stale_candidate"}
    generated_docs = {x.doc_id for x in build_freshness_inventory() if x.refresh_mode == "generated_on_refresh"}
    return sorted(stale_docs & generated_docs)


def build_doc_freshness_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "DocumentationFreshnessAudit.v1",
        "artifactId": "doc-freshness-audit",
        "freshness": [x.__dict__ for x in build_freshness_inventory()],
        "dependencies": [x.__dict__ for x in build_refresh_dependencies()],
        "classification": classify_freshness_states(),
        "staleGeneratedMismatch": detect_stale_generated_manual_mismatch(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
