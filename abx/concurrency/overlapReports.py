from __future__ import annotations

from abx.concurrency.mergeabilityRules import build_mergeability_records
from abx.concurrency.overlapResolution import build_compensation_records, build_overlap_resolution_records
from abx.concurrency.serializationPolicies import build_serialization_policies
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_overlap_resolution_report() -> dict[str, object]:
    mergeability = build_mergeability_records()
    resolutions = build_overlap_resolution_records()
    compensation = build_compensation_records()
    policies = build_serialization_policies()
    report = {
        "artifactType": "OverlapResolutionAudit.v1",
        "artifactId": "overlap-resolution-audit",
        "mergeability": [x.__dict__ for x in mergeability],
        "resolutions": [x.__dict__ for x in resolutions],
        "compensation": [x.__dict__ for x in compensation],
        "serializationPolicies": [x.__dict__ for x in policies],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
