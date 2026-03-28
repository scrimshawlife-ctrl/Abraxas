from __future__ import annotations

from abx.admission.releaseInventory import build_release_inventory
from abx.admission.types import ReleaseReadinessRecord


def build_release_readiness_records() -> list[ReleaseReadinessRecord]:
    return [
        ReleaseReadinessRecord(readiness_id=rid, change_ref=cref, readiness_state=state, readiness_reason=reason)
        for rid, cref, state, reason in build_release_inventory()
    ]
