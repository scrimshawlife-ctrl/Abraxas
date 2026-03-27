from __future__ import annotations

from abx.deployment.runtimeTopology import (
    classify_runtime_topologies,
    detect_conflicting_topology_grammars,
    environment_topology_mapping,
)
from abx.deployment.topologyCapabilities import build_topology_capabilities
from abx.deployment.topologyInventory import build_runtime_topology_inventory
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable



def build_topology_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "RuntimeTopologyAudit.v1",
        "artifactId": "topology-audit",
        "topologies": [x.__dict__ for x in build_runtime_topology_inventory()],
        "classification": classify_runtime_topologies(),
        "environmentMapping": environment_topology_mapping(),
        "capabilities": [x.__dict__ for x in build_topology_capabilities()],
        "conflictingGrammars": detect_conflicting_topology_grammars(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
