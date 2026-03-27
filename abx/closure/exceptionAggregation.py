from __future__ import annotations

from abx.closure.gapInventory import build_residual_gap_inventory
from abx.closure.types import ExceptionAggregationRecord


def build_exception_aggregation_record() -> ExceptionAggregationRecord:
    gaps = build_residual_gap_inventory()
    totals: dict[str, int] = {}
    blocking_domains: list[str] = []
    stale_exceptions: list[str] = []

    for row in gaps:
        totals[row.classification] = totals.get(row.classification, 0) + 1
        if row.classification == "blocking":
            blocking_domains.append(row.domain_id)
        if row.classification == "stale_exception":
            stale_exceptions.append(row.gap_id)

    return ExceptionAggregationRecord(
        aggregation_id="exception-aggregation",
        totals_by_classification={k: totals[k] for k in sorted(totals)},
        blocking_domains=sorted(set(blocking_domains)),
        stale_exceptions=sorted(stale_exceptions),
    )
