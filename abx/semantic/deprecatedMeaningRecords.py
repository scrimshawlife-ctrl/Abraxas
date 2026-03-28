from __future__ import annotations

from abx.semantic.types import DeprecatedMeaningRecord


def build_deprecated_meaning_records() -> tuple[DeprecatedMeaningRecord, ...]:
    return (
        DeprecatedMeaningRecord("dep.confidence", "packet.confidence", "SEMANTIC_DEPRECATION_ACTIVE", "MEDIUM"),
        DeprecatedMeaningRecord("dep.legacy", "packet.legacy_signal", "SEMANTIC_BREAK", "CRITICAL"),
    )
