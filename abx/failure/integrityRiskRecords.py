from __future__ import annotations

from abx.failure.types import IntegrityRiskRecord


def build_integrity_risk_records() -> tuple[IntegrityRiskRecord, ...]:
    return (
        IntegrityRiskRecord("int.cache.corrupt", "err.cache.corrupt", "INTEGRITY_RISK_ACTIVE"),
        IntegrityRiskRecord("int.dep.auth", "err.dep.auth", "INTEGRITY_RISK_MONITORED"),
    )
