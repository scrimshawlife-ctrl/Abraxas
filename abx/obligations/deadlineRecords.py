from __future__ import annotations

from abx.obligations.deadlineInventory import build_deadline_inventory
from abx.obligations.types import DeadlineRecord


def build_deadline_records() -> list[DeadlineRecord]:
    return build_deadline_inventory()
