from __future__ import annotations

from abx.observability.sufficiencyInventory import build_sufficiency_inventory
from abx.observability.types import MeasurementSufficiencyRecord


def build_measurement_sufficiency_records() -> list[MeasurementSufficiencyRecord]:
    return [
        MeasurementSufficiencyRecord(
            sufficiency_id=sid,
            surface_ref=surface_ref,
            sufficiency_state=state,
            consequence_class=consequence,
        )
        for sid, surface_ref, state, consequence in build_sufficiency_inventory()
    ]
