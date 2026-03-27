from __future__ import annotations

from abx.knowledge.continuityInventory import build_continuity_inventory
from abx.knowledge.types import ContinuityCoverageRecord


def build_continuity_coverage(run_id: str = "RUN-CONTINUITY") -> ContinuityCoverageRecord:
    rows = build_continuity_inventory(run_id=run_id)
    missing: list[str] = []
    if not any(x.previous_ref for x in rows):
        missing.append("previous_ref")
    if not any(x.baseline_ref for x in rows):
        missing.append("baseline_ref")
    return ContinuityCoverageRecord(run_id=run_id, complete=not missing, missing_links=sorted(missing))
