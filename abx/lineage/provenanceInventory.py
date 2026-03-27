from __future__ import annotations

from abx.lineage.types import ProvenanceRecord


def build_provenance_inventory() -> tuple[ProvenanceRecord, ...]:
    return (
        ProvenanceRecord("prov.raw", "lin.raw.orders", "ingest->validate", "PROVENANCE_COMPLETE"),
        ProvenanceRecord("prov.norm", "lin.norm.orders", "normalize->enrich", "PROVENANCE_COMPLETE"),
        ProvenanceRecord("prov.rollup", "lin.rollup.rev", "aggregate->materialize", "PROVENANCE_STALE"),
        ProvenanceRecord("prov.cache", "lin.cache.rev", "cache_refresh", "PROVENANCE_PARTIAL"),
        ProvenanceRecord("prov.partner", "lin.merge.partner", "merge_external", "PROVENANCE_BROKEN"),
    )
