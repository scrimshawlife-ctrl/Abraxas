"""Log retention and compaction policies.

Defines stable defaults for:
- Raw event retention
- Compaction triggers
- Dictionary sizing
"""

from __future__ import annotations
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass


# Stable policy defaults
RAW_RETENTION_DAYS = 14
COMPACT_INTERVAL_EVENTS = 2000
COMPACT_INTERVAL_SECONDS = 900  # 15 minutes
DICT_TOPK = 256


@dataclass
class CompactionPolicy:
    """Compaction policy configuration."""
    interval_events: int = COMPACT_INTERVAL_EVENTS
    interval_seconds: int = COMPACT_INTERVAL_SECONDS
    dict_topk: int = DICT_TOPK
    use_gzip: bool = True


@dataclass
class RetentionPolicy:
    """Retention policy configuration."""
    raw_retention_days: int = RAW_RETENTION_DAYS
    keep_compressed: bool = True


def should_compact(
    stats: Dict[str, Any],
    last_compaction_ts: Optional[int] = None,
    policy: Optional[CompactionPolicy] = None
) -> bool:
    """Determine if compaction should run.

    Args:
        stats: Ledger statistics (from ledger.get_stats)
        last_compaction_ts: Timestamp of last compaction
        policy: Compaction policy (uses defaults if None)

    Returns:
        True if compaction should be triggered
    """
    if policy is None:
        policy = CompactionPolicy()

    total_events = stats.get("total_events", 0)
    if total_events == 0:
        return False

    # Check event count threshold
    if total_events >= policy.interval_events:
        return True

    # Check time threshold
    if last_compaction_ts is not None:
        elapsed = int(time.time()) - last_compaction_ts
        if elapsed >= policy.interval_seconds:
            return True

    return False


def should_vacuum(
    event_ts: int,
    policy: Optional[RetentionPolicy] = None
) -> bool:
    """Determine if an event is old enough to vacuum.

    Args:
        event_ts: Event timestamp
        policy: Retention policy (uses defaults if None)

    Returns:
        True if event should be vacuumed
    """
    if policy is None:
        policy = RetentionPolicy()

    retention_seconds = policy.raw_retention_days * 86400
    age_seconds = int(time.time()) - event_ts

    return age_seconds > retention_seconds


def get_vacuum_cutoff_ts(policy: Optional[RetentionPolicy] = None) -> int:
    """Get the cutoff timestamp for vacuuming.

    Events older than this timestamp should be removed.

    Args:
        policy: Retention policy (uses defaults if None)

    Returns:
        Cutoff timestamp
    """
    if policy is None:
        policy = RetentionPolicy()

    retention_seconds = policy.raw_retention_days * 86400
    return int(time.time()) - retention_seconds


def calculate_compaction_range(
    stats: Dict[str, Any],
    policy: Optional[CompactionPolicy] = None
) -> Optional[tuple[int, int]]:
    """Calculate the next range to compact.

    Args:
        stats: Ledger statistics
        policy: Compaction policy

    Returns:
        Tuple of (start_id, end_id) or None if nothing to compact
    """
    if policy is None:
        policy = CompactionPolicy()

    total_events = stats.get("total_events", 0)
    if total_events < policy.interval_events:
        return None

    min_id = stats.get("min_id")
    max_id = stats.get("max_id")

    if min_id is None or max_id is None:
        return None

    # Compact in chunks of interval_events
    start_id = min_id
    end_id = min(min_id + policy.interval_events - 1, max_id)

    return (start_id, end_id)


def get_default_compaction_policy() -> CompactionPolicy:
    """Get default compaction policy."""
    return CompactionPolicy()


def get_default_retention_policy() -> RetentionPolicy:
    """Get default retention policy."""
    return RetentionPolicy()
