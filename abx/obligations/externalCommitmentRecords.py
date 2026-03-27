from __future__ import annotations

from abx.obligations.commitmentInventory import build_commitment_inventory
from abx.obligations.types import ExternalCommitmentRecord


def build_external_commitment_records() -> list[ExternalCommitmentRecord]:
    return build_commitment_inventory()
