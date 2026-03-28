from __future__ import annotations

from abx.freshness.types import ArchivalValidityRecord


def build_archival_validity_records() -> tuple[ArchivalValidityRecord, ...]:
    return (
        ArchivalValidityRecord("arc.report", "report.archive", "ARCHIVAL_VALID", "read-only"),
        ArchivalValidityRecord("arc.dashboard", "dashboard.rollup", "ARCHIVAL_DOWNGRADE_ACTIVE", "visible-not-authoritative"),
        ArchivalValidityRecord("arc.legacy", "legacy.signal", "NOT_COMPUTABLE", "unknown"),
    )
