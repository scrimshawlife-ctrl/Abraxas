from __future__ import annotations

from abx.meta.types import CanonCompressionRecord


def build_canon_compression_records() -> list[CanonCompressionRecord]:
    return [
        CanonCompressionRecord(
            compression_id="cmp-precedence-merged-v3",
            source_refs=["canon_priority.v2", "canon_priority.v3"],
            merged_ref="canon_priority.v3",
            compression_state="merged-compressed",
        ),
        CanonCompressionRecord(
            compression_id="cmp-shadow-notes",
            source_refs=["governance_notes_shadow.md"],
            merged_ref="pending",
            compression_state="shadow-candidate",
        ),
    ]
