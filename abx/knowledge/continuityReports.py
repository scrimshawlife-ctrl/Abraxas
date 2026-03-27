from __future__ import annotations

from abx.knowledge.continuityCoverage import build_continuity_coverage
from abx.knowledge.continuityNormalization import normalize_continuity_refs
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_continuity_audit_report(run_id: str = "RUN-CONTINUITY") -> dict[str, object]:
    normalized = normalize_continuity_refs(run_id=run_id)
    coverage = build_continuity_coverage(run_id=run_id)
    report = {
        "artifactType": "ContinuityAudit.v1",
        "artifactId": f"continuity-audit-{run_id}",
        "normalized": normalized,
        "coverage": coverage.__dict__,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
