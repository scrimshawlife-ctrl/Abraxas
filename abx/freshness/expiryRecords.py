from __future__ import annotations

from abx.freshness.types import ExpiryRecord


def build_expiry_records() -> tuple[ExpiryRecord, ...]:
    return (
        ExpiryRecord("exp.config", "config.snapshot", "EXPIRED", "HARD"),
        ExpiryRecord("exp.cache", "cache.snapshot", "NEAR_EXPIRY", "SOFT"),
        ExpiryRecord("exp.archive", "report.archive", "ARCHIVAL_ONLY", "ARCHIVAL"),
    )
