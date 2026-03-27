from __future__ import annotations

from abx.concurrency.conflictClassification import classify_conflict_posture
from abx.concurrency.conflictInventory import build_conflict_inventory
from abx.concurrency.conflictRecords import build_conflict_classification_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_conflict_report() -> dict[str, object]:
    conflicts = build_conflict_inventory()
    classes = build_conflict_classification_records()
    posture = classify_conflict_posture([x.conflict_class for x in conflicts])
    report = {
        "artifactType": "ConflictAudit.v1",
        "artifactId": "conflict-audit",
        "conflicts": [x.__dict__ for x in conflicts],
        "classifications": [x.__dict__ for x in classes],
        "posture": posture,
        "byType": {
            k: sorted(x.conflict_id for x in conflicts if x.conflict_class == k)
            for k in sorted({x.conflict_class for x in conflicts})
        },
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
