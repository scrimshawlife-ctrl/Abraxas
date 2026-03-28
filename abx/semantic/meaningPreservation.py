from __future__ import annotations

from abx.semantic.types import MeaningPreservationRecord


def build_meaning_preservation_records() -> tuple[MeaningPreservationRecord, ...]:
    return (
        MeaningPreservationRecord("mp.packet.latency", "packet.latency_ms", "MEANING_PRESERVED", "MIGRATION_NOT_REQUIRED", "NO"),
        MeaningPreservationRecord("mp.risk.score", "packet.risk_score", "MEANING_PRESERVED_VIA_MIGRATION", "MIGRATION_COMPLETE", "NO"),
        MeaningPreservationRecord("mp.severity", "packet.severity", "SEMANTIC_TRANSLATION_REQUIRED", "MIGRATION_INCOMPLETE", "YES"),
        MeaningPreservationRecord("mp.legacy", "packet.legacy_signal", "UNSAFE_REINTERPRETATION", "MIGRATION_ILLEGITIMATE", "YES"),
    )
