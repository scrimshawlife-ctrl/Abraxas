from __future__ import annotations

from abx.explanation.types import NarrativeCompressionRecord


def build_compression_inventory() -> tuple[NarrativeCompressionRecord, ...]:
    return (
        NarrativeCompressionRecord(
            "cmp.exec.summary",
            "executive.summary",
            "ABSTRACTIVE",
            "COMPRESSED_WITH_PRESERVATION",
            "NONE",
        ),
        NarrativeCompressionRecord(
            "cmp.incident.brief",
            "incident.brief",
            "BULLET_DIGEST",
            "COMPRESSED_WITH_NOTED_LOSS",
            "low_priority_context",
        ),
        NarrativeCompressionRecord(
            "cmp.dashboard.card",
            "dashboard.card",
            "CARD_SNIPPET",
            "COMPRESSED_WITH_HIDDEN_LOSS_RISK",
            "uncertainty_bounds",
        ),
        NarrativeCompressionRecord(
            "cmp.replay.report",
            "replay.report",
            "NONE",
            "NO_COMPRESSION_NEEDED",
            "NONE",
        ),
        NarrativeCompressionRecord(
            "cmp.legacy.note",
            "legacy.note",
            "UNKNOWN",
            "NOT_COMPUTABLE",
            "missing_source_text",
        ),
    )
