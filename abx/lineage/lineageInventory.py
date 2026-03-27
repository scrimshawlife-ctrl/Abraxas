from __future__ import annotations

from abx.lineage.types import LineageRecord


def build_lineage_inventory() -> tuple[LineageRecord, ...]:
    return (
        LineageRecord("lin.raw.orders", "state.orders.raw", "PRIMARY", "ingest/orders.csv"),
        LineageRecord("lin.norm.orders", "state.orders.norm", "DERIVED", "state.orders.raw"),
        LineageRecord("lin.rollup.rev", "state.rev.rollup", "MATERIALIZED", "state.orders.norm"),
        LineageRecord("lin.cache.rev", "state.rev.cache", "CACHED", "state.rev.rollup"),
        LineageRecord("lin.merge.partner", "state.partner.merged", "MERGED", "federation/partner-feed"),
    )
