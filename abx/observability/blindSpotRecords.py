from __future__ import annotations

from abx.observability.blindSpotInventory import build_blind_spot_inventory
from abx.observability.types import BlindSpotRecord


def build_blind_spot_records() -> list[BlindSpotRecord]:
    return [
        BlindSpotRecord(blind_spot_id=bid, surface_ref=surface_ref, blind_spot_state=state, risk_level=risk)
        for bid, surface_ref, state, risk in build_blind_spot_inventory()
    ]
