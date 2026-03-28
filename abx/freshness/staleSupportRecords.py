from __future__ import annotations

from abx.freshness.types import StaleSupportRecord


def build_stale_support_records() -> tuple[StaleSupportRecord, ...]:
    return (
        StaleSupportRecord("sup.dash", "dashboard.rollup", "STALE_SUPPORT_ACTIVE", "decision-card"),
        StaleSupportRecord("sup.summary", "summary.blurb", "STALE_SUPPORT_ACTIVE", "explanation"),
        StaleSupportRecord("sup.evidence", "evidence.packet", "FRESH_SUPPORT", "decision-path"),
    )
