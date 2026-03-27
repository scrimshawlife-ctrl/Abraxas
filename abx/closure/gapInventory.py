from __future__ import annotations

from abx.closure.nonClosureRecords import build_non_closure_records
from abx.closure.types import ResidualGapRecord


SEVERITY_BY_CLASSIFICATION = {
    "blocking": "HIGH",
    "unresolved": "HIGH",
    "stale_exception": "MEDIUM",
    "waived": "MEDIUM",
    "tolerated": "LOW",
    "informational_only": "LOW",
}


def build_residual_gap_inventory() -> list[ResidualGapRecord]:
    rows = [
        ResidualGapRecord(
            gap_id=record.non_closure_id.replace("non-closure", "gap"),
            domain_id=record.domain_id,
            classification=record.classification,
            severity=SEVERITY_BY_CLASSIFICATION.get(record.classification, "LOW"),
            evidence_ref=record.evidence_ref,
        )
        for record in build_non_closure_records()
    ]
    return sorted(rows, key=lambda x: x.gap_id)
