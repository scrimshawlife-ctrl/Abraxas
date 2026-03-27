from __future__ import annotations

from abx.approval.approvalInventory import build_approval_inventory


def build_human_approval_records() -> tuple:
    return build_approval_inventory()
