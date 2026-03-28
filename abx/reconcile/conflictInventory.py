from __future__ import annotations


def build_conflict_inventory() -> tuple[tuple[str, str, str, str, str], ...]:
    return (
        ("conf.001", "ledger", "derived_view", "TEMPORAL_CONFLICT", "DEGRADED"),
        ("conf.002", "cache", "canonical_store", "FRESHNESS_CONFLICT", "DEGRADED"),
        ("conf.003", "entity_map", "external_reference", "IDENTITY_CONFLICT", "BLOCKING"),
        ("conf.004", "schema_projection", "runtime_payload", "SEMANTIC_CONFLICT", "BLOCKING"),
        ("conf.005", "replay_lineage", "materialized_index", "LINEAGE_CONFLICT", "BLOCKING"),
        ("conf.006", "policy_snapshot", "runtime_override", "BLOCKING_CONFLICT", "BLOCKING"),
        ("conf.007", "ui_projection", "backend_truth", "COSMETIC_MISMATCH", "DEGRADED"),
        ("conf.008", "replica", "source_of_truth", "CONFLICT_UNKNOWN", "DEGRADED"),
        ("conf.009", "import_mirror", "canonical_store", "NOT_COMPUTABLE", "BLOCKING"),
        ("conf.010", "approval_state", "obligation_ledger", "AUTHORITY_CONFLICT", "DEGRADED"),
    )
