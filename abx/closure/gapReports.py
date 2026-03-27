from __future__ import annotations

from abx.closure.exceptionAggregation import build_exception_aggregation_record
from abx.closure.gapInventory import build_residual_gap_inventory
from abx.closure.nonClosureRecords import build_non_closure_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_residual_gap_report() -> dict[str, object]:
    gaps = build_residual_gap_inventory()
    non_closure = build_non_closure_records()
    aggregation = build_exception_aggregation_record()
    report = {
        "artifactType": "ResidualGapReport.v1",
        "artifactId": "residual-gap-report",
        "gaps": [x.__dict__ for x in gaps],
        "nonClosure": [x.__dict__ for x in non_closure],
        "aggregation": aggregation.__dict__,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
