from __future__ import annotations


def build_contract_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("ct.001", "api.billing->ledger", "CONTRACT_VALID", "STRUCTURAL_VALID"),
        ("ct.002", "pipeline.orders->fulfillment", "CONTRACT_VALID", "SEMANTIC_VALID"),
        ("ct.003", "adapter.crm->identity", "CONTRACT_VALID", "IDENTITY_PRESERVING"),
        ("ct.004", "cache.sync->search", "CONTRACT_VALID", "FRESHNESS_VALID"),
        ("ct.005", "ops.override->runtime", "CONTRACT_VALID", "AUTHORITY_VALID"),
        ("ct.006", "webhook.partner->ingest", "CONTRACT_DRIFT_SUSPECTED", "SEMANTIC_VALID"),
        ("ct.007", "legacy.feed->normalizer", "CONTRACT_BROKEN", "STRUCTURAL_VALID"),
        ("ct.008", "mirror.edge->core", "NOT_COMPUTABLE", "UNKNOWN"),
    )
