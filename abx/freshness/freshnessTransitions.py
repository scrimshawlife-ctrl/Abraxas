from __future__ import annotations

from abx.freshness.types import FreshnessTransitionRecord


def build_freshness_transition_records() -> tuple[FreshnessTransitionRecord, ...]:
    return (
        FreshnessTransitionRecord("trn.cache", "cache.snapshot", "FRESH_WITH_WARNING", "REFRESH_REQUIRED", "source_window_elapsed"),
        FreshnessTransitionRecord("trn.dash", "dashboard.rollup", "AGING", "STALE_SUPPORT_ACTIVE", "upstream_delay"),
        FreshnessTransitionRecord("trn.expiry", "config.snapshot", "STALE", "REFRESH_OVERDUE", "refresh_missed"),
        FreshnessTransitionRecord("trn.archive", "report.archive", "STALE", "ARCHIVAL_DOWNGRADE_ACTIVE", "operational_window_closed"),
        FreshnessTransitionRecord("trn.block", "legacy.signal", "DECAY_UNKNOWN", "REUSE_BLOCKED", "decay_unknown"),
        FreshnessTransitionRecord("trn.restore", "evidence.packet", "AGING", "FRESHNESS_RESTORED", "new_ingest"),
    )
