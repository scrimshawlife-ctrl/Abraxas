from __future__ import annotations

from abx.innovation.innovationLifecycle import build_innovation_lifecycle_records
from abx.innovation.lifecycleTransitions import classify_lifecycle_states, detect_redundant_lifecycle_grammar
from abx.innovation.promotionReadiness import build_promotion_readiness_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_innovation_lifecycle_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "InnovationLifecycleAudit.v1",
        "artifactId": "innovation-lifecycle-audit",
        "lifecycle": [x.__dict__ for x in build_innovation_lifecycle_records()],
        "states": classify_lifecycle_states(),
        "promotionReadiness": [x.__dict__ for x in build_promotion_readiness_records()],
        "redundantGrammar": detect_redundant_lifecycle_grammar(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
