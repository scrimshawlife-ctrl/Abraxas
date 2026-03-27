from __future__ import annotations

from abx.uncertainty.calibrationInventory import build_calibration_inventory


def build_calibration_validity_records() -> tuple:
    return build_calibration_inventory()
