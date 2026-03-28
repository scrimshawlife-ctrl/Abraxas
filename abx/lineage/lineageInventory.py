from __future__ import annotations

from abx.lineage.types import LineageRecord


def build_lineage_inventory() -> tuple[LineageRecord, ...]:
    return (
        LineageRecord("lin.raw.orders", "state.orders.raw", "PRIMARY", "ingest/orders.csv", "SOURCE_TRACEABLE_STATE", "CONTINUOUS"),
        LineageRecord("lin.norm.orders", "state.orders.norm", "DERIVED", "state.orders.raw", "DERIVED_WITH_VALID_LINEAGE", "CONTINUOUS"),
        LineageRecord("lin.rollup.rev", "state.rev.rollup", "MATERIALIZED", "state.orders.norm", "MATERIALIZED_LINEAGE_STATE", "CONTINUOUS"),
        LineageRecord("lin.cache.rev", "state.rev.cache", "CACHED", "state.rev.rollup", "CACHED_LINEAGE_STATE", "CONTINUOUS"),
        LineageRecord("lin.copy.rev", "state.rev.copy", "COPIED", "state.rev.rollup", "COPIED_LINEAGE_STATE", "CONTINUOUS"),
        LineageRecord("lin.merge.partner", "state.partner.merged", "MERGED", "federation/partner-feed", "MERGED_LINEAGE_STATE", "PARTIAL"),
        LineageRecord("lin.unknown", "state.partner.shadow", "UNKNOWN", "", "LINEAGE_UNKNOWN", "BROKEN"),
    )
