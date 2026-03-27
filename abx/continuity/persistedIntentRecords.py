from __future__ import annotations

from abx.continuity.intentInventory import build_intent_inventory
from abx.continuity.types import PersistedIntentRecord


def build_persisted_intent_records() -> list[PersistedIntentRecord]:
    return build_intent_inventory()
