from __future__ import annotations

from abx.meta.types import CanonConflictRecord


def build_canon_conflict_records() -> list[CanonConflictRecord]:
    return [
        CanonConflictRecord(
            conflict_id="conf-shadow-steering",
            left_ref="governance_notes_shadow.md",
            right_ref="canonical_manifest.py",
            conflict_state="unresolved",
            resolution_ref="pending:supersession",
        ),
        CanonConflictRecord(
            conflict_id="conf-priority-v2-v3",
            left_ref="canon_priority.v2",
            right_ref="canon_priority.v3",
            conflict_state="superseded",
            resolution_ref="sup-canon-priority-v3",
        ),
    ]
