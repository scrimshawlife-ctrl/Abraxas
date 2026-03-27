from __future__ import annotations

from abx.federation.interopInventory import build_interop_inventory
from abx.federation.types import CapabilityHandoffRecord


def build_handoff_envelopes() -> list[CapabilityHandoffRecord]:
    rows = []
    for item in build_interop_inventory():
        rows.append(
            CapabilityHandoffRecord(
                handoff_id=f"handoff.{item.interop_id}",
                expected_inputs=["run_id", "artifact_id", "trust_state"],
                expected_outputs=["artifact_id", "status", "lineage_ref"],
                trust_propagation="explicit",
                lifecycle_propagation="explicit",
            )
        )
    return sorted(rows, key=lambda x: x.handoff_id)
