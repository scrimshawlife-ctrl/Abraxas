from __future__ import annotations

from abx.federation.types import CapabilityRegistryRecord


def build_capability_inventory() -> list[CapabilityRegistryRecord]:
    rows = [
        CapabilityRegistryRecord("capability.boundary.validate", "boundary", "contract.input.envelope.v1", "handoff.interop.boundary.runtime"),
        CapabilityRegistryRecord("capability.runtime.dispatch", "runtime", "contract.runtime.events.v1", "handoff.interop.runtime.observability"),
        CapabilityRegistryRecord("capability.resilience.recover", "resilience", "contract.recovery.status.v1", "handoff.interop.resilience.operator"),
        CapabilityRegistryRecord("capability.knowledge.continuity", "knowledge", "contract.continuity.snapshot.v1", "handoff.interop.knowledge.governance"),
    ]
    return sorted(rows, key=lambda x: x.capability_id)
