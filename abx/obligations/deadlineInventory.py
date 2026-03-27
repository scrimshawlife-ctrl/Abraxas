from __future__ import annotations

from abx.obligations.types import DeadlineRecord


def build_deadline_inventory() -> list[DeadlineRecord]:
    rows = [
        DeadlineRecord("deadline.release-v1-6", "commitment.release-v1-6", "HARD_DEADLINE", "2026-06-30", ""),
        DeadlineRecord("deadline.incident-followup", "commitment.incident-followup", "DUE_WINDOW", "2026-05-20", "2026-05-15/2026-05-20"),
        DeadlineRecord("deadline.docs-refresh", "commitment.docs-refresh", "SOFT_TARGET", "2026-07-15", ""),
        DeadlineRecord("deadline.legacy-api-window", "commitment.legacy-api-window", "HARD_DEADLINE", "2026-04-15", ""),
        DeadlineRecord("deadline.deprecated-export", "commitment.deprecated-export", "SOFT_TARGET", "2026-03-15", ""),
    ]
    return sorted(rows, key=lambda x: x.deadline_id)
