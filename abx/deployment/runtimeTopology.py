from __future__ import annotations

from abx.deployment.topologyInventory import build_runtime_topology_inventory



def classify_runtime_topologies() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for x in build_runtime_topology_inventory():
        out.setdefault(x.topology_class, []).append(x.topology_id)
    return {k: sorted(v) for k, v in out.items()}



def environment_topology_mapping() -> dict[str, str]:
    return {x.environment: x.topology_id for x in build_runtime_topology_inventory()}



def detect_conflicting_topology_grammars() -> list[str]:
    invalid = []
    for x in build_runtime_topology_inventory():
        if not all("->" in e for e in x.edges):
            invalid.append(x.topology_id)
    return sorted(invalid)
