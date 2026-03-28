from __future__ import annotations

from abx.lineage.types import ProvenanceRecord


def build_provenance_inventory() -> tuple[ProvenanceRecord, ...]:
    return (
        ProvenanceRecord("prov.raw", "lin.raw.orders", "ingest->validate", "PROVENANCE_COMPLETE", "INGEST_VALIDATION", "v5"),
        ProvenanceRecord("prov.norm", "lin.norm.orders", "normalize->enrich", "PROVENANCE_COMPLETE", "NORMALIZATION_ENRICHMENT", "v5"),
        ProvenanceRecord("prov.rollup", "lin.rollup.rev", "aggregate->materialize", "PROVENANCE_STALE", "AGGREGATION_MATERIALIZATION", "v4"),
        ProvenanceRecord("prov.cache", "lin.cache.rev", "cache_refresh", "PROVENANCE_PARTIAL", "CACHE_REFRESH", "v4"),
        ProvenanceRecord("prov.copy", "lin.copy.rev", "copy_snapshot", "PROVENANCE_COMPLETE", "COPY_SNAPSHOT", "v4"),
        ProvenanceRecord("prov.partner", "lin.merge.partner", "merge_external", "PROVENANCE_BROKEN", "FEDERATED_MERGE", "unknown"),
        ProvenanceRecord("prov.shadow", "lin.unknown", "", "NOT_COMPUTABLE", "UNKNOWN", "unknown"),
    )
