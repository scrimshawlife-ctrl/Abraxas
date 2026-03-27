from __future__ import annotations

from abx.productization.audienceInventory import build_audience_entrypoints, build_audience_inventory


def detect_audience_terminology_drift() -> list[str]:
    known = {x.audience_name for x in build_audience_inventory()}
    drift = [x.audience_name for x in build_audience_entrypoints() if x.audience_name not in known]
    return sorted(drift)
