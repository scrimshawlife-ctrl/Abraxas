from __future__ import annotations

from abx.deployment.types import TopologyCapabilityRecord



def build_topology_capabilities() -> list[TopologyCapabilityRecord]:
    return [
        TopologyCapabilityRecord("topology.single-process", "capability.runtime.dispatch", "enabled"),
        TopologyCapabilityRecord("topology.validation-runner", "capability.trace.causal", "enabled"),
        TopologyCapabilityRecord("topology.distributed-core", "capability.resilience.recover", "enabled"),
        TopologyCapabilityRecord("topology.distributed-core", "capability.federation.interop", "enabled"),
        TopologyCapabilityRecord("topology.drill-fault-path", "capability.fault.injection", "enabled"),
        TopologyCapabilityRecord("topology.legacy-bridge", "capability.federation.interop", "adapted"),
    ]
