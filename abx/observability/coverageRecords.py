from __future__ import annotations

from abx.observability.coverageInventory import build_coverage_inventory
from abx.observability.types import ObservabilityCoverageRecord


def build_coverage_records() -> list[ObservabilityCoverageRecord]:
    return [
        ObservabilityCoverageRecord(coverage_id=cid, surface_ref=surface_ref, coverage_state=state, measurement_mode=mode)
        for cid, surface_ref, state, mode in build_coverage_inventory()
    ]
