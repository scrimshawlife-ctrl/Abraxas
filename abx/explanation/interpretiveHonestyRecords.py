from __future__ import annotations

from abx.explanation.honestyInventory import build_causal_inventory, build_honesty_inventory, build_omission_inventory


def build_interpretive_honesty_records() -> tuple:
    return build_honesty_inventory()


def build_causal_language_records() -> tuple:
    return build_causal_inventory()


def build_omission_risk_records() -> tuple:
    return build_omission_inventory()
