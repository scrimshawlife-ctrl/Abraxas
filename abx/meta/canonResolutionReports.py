from __future__ import annotations

from abx.meta.canonCompression import build_canon_compression_records
from abx.meta.canonConflicts import build_canon_conflict_records
from abx.meta.supersessionRecords import build_supersession_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def classify_conflict_and_supersession() -> dict[str, list[str]]:
    buckets = {
        "active": [],
        "superseded": [],
        "conflicting": [],
        "merged_compressed": [],
        "shadow_candidate": [],
        "unresolved": [],
        "not_computable": [],
    }
    for conf in build_canon_conflict_records():
        buckets.setdefault(conf.conflict_state.replace("-", "_"), []).append(conf.conflict_id)
        if conf.conflict_state == "unresolved":
            buckets["conflicting"].append(conf.conflict_id)
    for cmp in build_canon_compression_records():
        buckets.setdefault(cmp.compression_state.replace("-", "_"), []).append(cmp.compression_id)
    for sup in build_supersession_records():
        buckets["superseded"].append(sup.supersession_id)
    for ids in buckets.values():
        ids.sort()
    return buckets


def detect_unresolved_supersession_drift() -> list[dict[str, str]]:
    return [
        {"conflictId": x.conflict_id, "reason": "unresolved_conflict"}
        for x in build_canon_conflict_records()
        if x.conflict_state == "unresolved"
    ]


def build_canon_conflict_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "CanonConflictAudit.v1",
        "artifactId": "canon-conflict-audit",
        "supersession": [x.__dict__ for x in build_supersession_records()],
        "conflicts": [x.__dict__ for x in build_canon_conflict_records()],
        "compression": [x.__dict__ for x in build_canon_compression_records()],
        "classification": classify_conflict_and_supersession(),
        "unresolvedDrift": detect_unresolved_supersession_drift(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
