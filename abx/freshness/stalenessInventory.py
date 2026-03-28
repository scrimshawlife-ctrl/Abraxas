from __future__ import annotations

from abx.freshness.types import StalenessRecord


def build_staleness_inventory() -> tuple[StalenessRecord, ...]:
    return (
        StalenessRecord("stl.evidence", "evidence.packet", "OPERATIONALLY_VALID", "VALID"),
        StalenessRecord("stl.cache", "cache.snapshot", "AGING_BUT_VALID", "VALID"),
        StalenessRecord("stl.dashboard", "dashboard.rollup", "STALE_BUT_VISIBLE", "DOWNGRADED"),
        StalenessRecord("stl.expired", "config.snapshot", "EXPIRED_FOR_OPERATIONAL_USE", "INVALID"),
        StalenessRecord("stl.archive", "report.archive", "ARCHIVAL_VALID_ONLY", "ARCHIVAL"),
        StalenessRecord("stl.support", "summary.blurb", "STALE_SUPPORT_ACTIVE", "DOWNGRADED"),
    )
