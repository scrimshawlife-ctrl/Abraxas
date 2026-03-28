from __future__ import annotations


def build_handoff_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("hf.001", "api.billing->ledger", "HANDOFF_PREPARED", "QUEUED"),
        ("hf.002", "pipeline.orders->fulfillment", "HANDOFF_SENT", "IN_FLIGHT"),
        ("hf.003", "adapter.crm->identity", "HANDOFF_DELIVERED", "ACKED"),
        ("hf.004", "cache.sync->search", "HANDOFF_RECEIVED", "RECEIPT_CONFIRMED"),
        ("hf.005", "ops.override->runtime", "HANDOFF_PENDING", "RETRYING"),
        ("hf.006", "webhook.partner->ingest", "HANDOFF_FAILED", "NACKED"),
        ("hf.007", "legacy.feed->normalizer", "HANDOFF_UNKNOWN", "UNKNOWN"),
        ("hf.008", "mirror.edge->core", "NOT_COMPUTABLE", "UNKNOWN"),
    )
