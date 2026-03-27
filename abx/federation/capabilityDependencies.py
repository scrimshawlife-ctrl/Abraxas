from __future__ import annotations

from abx.federation.types import CapabilityDependencyRecord


def build_capability_dependencies() -> list[CapabilityDependencyRecord]:
    rows = [
        CapabilityDependencyRecord("capability.runtime.dispatch", ["capability.boundary.validate"]),
        CapabilityDependencyRecord("capability.resilience.recover", ["capability.runtime.dispatch"]),
        CapabilityDependencyRecord("capability.knowledge.continuity", ["capability.runtime.dispatch", "capability.resilience.recover"]),
    ]
    return sorted(rows, key=lambda x: x.capability_id)
