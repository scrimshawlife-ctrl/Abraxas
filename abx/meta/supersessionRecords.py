from __future__ import annotations

from abx.meta.types import SupersessionRecord


def build_supersession_records() -> list[SupersessionRecord]:
    return [
        SupersessionRecord(
            supersession_id="sup-canon-priority-v3",
            superseded_ref="canon_priority.v2",
            active_ref="canon_priority.v3",
            reason="precedence_normalization",
            impacted_domains=["governance", "decision"],
        )
    ]
