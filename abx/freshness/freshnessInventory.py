from __future__ import annotations

from abx.freshness.types import DecaySemanticRecord, FreshnessRecord


def build_freshness_inventory() -> tuple[FreshnessRecord, ...]:
    return (
        FreshnessRecord("frs.evidence", "evidence.packet", "FRESH", "REUSE_ALLOWED"),
        FreshnessRecord("frs.cache", "cache.snapshot", "FRESH_WITH_WARNING", "REUSE_WARN"),
        FreshnessRecord("frs.forecast", "forecast.model", "AGING", "REUSE_DOWNGRADE"),
        FreshnessRecord("frs.dashboard", "dashboard.rollup", "STALE", "REFRESH_REQUIRED"),
        FreshnessRecord("frs.legacy", "legacy.signal", "DECAY_UNKNOWN", "REUSE_BLOCKED"),
        FreshnessRecord("frs.archive", "report.archive", "ARCHIVAL_ONLY", "REUSE_BLOCKED"),
        FreshnessRecord("frs.expired", "config.snapshot", "EXPIRED", "REUSE_BLOCKED"),
        FreshnessRecord("frs.blocked", "live.feed", "AGING", "REUSE_BLOCKED"),
    )


def build_decay_inventory() -> tuple[DecaySemanticRecord, ...]:
    return (
        DecaySemanticRecord("dcy.evidence", "evidence.packet", "DECAY_GRADUAL", "halflife/2h"),
        DecaySemanticRecord("dcy.cache", "cache.snapshot", "DECAY_THRESHOLD", "ttl/30m"),
        DecaySemanticRecord("dcy.forecast", "forecast.model", "DECAY_GRADUAL", "halflife/24h"),
        DecaySemanticRecord("dcy.legacy", "legacy.signal", "DECAY_UNKNOWN", "unknown"),
        DecaySemanticRecord("dcy.blocked", "live.feed", "DECAY_THRESHOLD", "ttl/5m"),
    )
