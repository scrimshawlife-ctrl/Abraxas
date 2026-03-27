from __future__ import annotations

from abx.approval.consentInventory import build_consent_inventory


def build_consent_state_records() -> tuple:
    return build_consent_inventory()
