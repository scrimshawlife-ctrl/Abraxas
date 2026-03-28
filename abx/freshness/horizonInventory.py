from __future__ import annotations

from abx.freshness.types import TimeHorizonRecord


def build_horizon_inventory() -> tuple[TimeHorizonRecord, ...]:
    return (
        TimeHorizonRecord("hrz.rt.evidence", "evidence.packet", "REAL_TIME_HORIZON", "cadence/5m"),
        TimeHorizonRecord("hrz.short.cache", "cache.snapshot", "SHORT_HORIZON", "cadence/30m"),
        TimeHorizonRecord("hrz.med.forecast", "forecast.model", "MEDIUM_HORIZON", "cadence/24h"),
        TimeHorizonRecord("hrz.long.plan", "mission.plan", "LONG_HORIZON", "cadence/7d"),
        TimeHorizonRecord("hrz.arch.report", "report.archive", "ARCHIVAL_HORIZON", "cadence/none"),
        TimeHorizonRecord("hrz.unknown.legacy", "legacy.signal", "HORIZON_UNKNOWN", "missing-cadence"),
    )
