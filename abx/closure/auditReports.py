from __future__ import annotations

from abx.closure.evidenceBundles import build_evidence_bundles
from abx.closure.evidenceClassification import classify_audit_readiness, classify_bundle_state
from abx.closure.types import AuditReadinessRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_audit_readiness_record() -> AuditReadinessRecord:
    bundles = build_evidence_bundles()
    bundle_states = {
        b.bundle_id: classify_bundle_state(
            missing_required_domains=b.missing_required_domains,
            stale_evidence_refs=b.stale_evidence_refs,
            blocked_domains=b.blocked_domains,
        )
        for b in bundles
    }
    readiness = classify_audit_readiness(bundle_states)
    blocked = sorted(bundle_id for bundle_id, state in bundle_states.items() if state == "BLOCKED")
    stale = sorted(bundle_id for bundle_id, state in bundle_states.items() if state == "STALE_EVIDENCE")
    incomplete = sorted(bundle_id for bundle_id, state in bundle_states.items() if state == "EVIDENCE_INCOMPLETE")
    evidence_refs = sorted({ref for b in bundles for ref in b.included_evidence})
    return AuditReadinessRecord(
        record_id="audit-readiness-record",
        readiness_state=readiness,
        bundle_states=bundle_states,
        blocked_bundles=blocked,
        stale_bundles=stale,
        incomplete_bundles=incomplete,
        evidence_refs=evidence_refs,
    )


def build_audit_readiness_report() -> dict[str, object]:
    bundles = build_evidence_bundles()
    record = build_audit_readiness_record()
    report = {
        "artifactType": "AuditReadinessReport.v1",
        "artifactId": "audit-readiness-report",
        "record": record.__dict__,
        "bundles": [x.__dict__ for x in bundles],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
