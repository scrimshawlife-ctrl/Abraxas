from __future__ import annotations

from abx.deployment.types import RuntimeTopologyRecord



def build_runtime_topology_inventory() -> list[RuntimeTopologyRecord]:
    return [
        RuntimeTopologyRecord(
            topology_id="topology.single-process",
            environment="local",
            topology_class="diagnostic",
            nodes=["boundary", "runtime", "observability"],
            edges=["boundary->runtime", "runtime->observability"],
        ),
        RuntimeTopologyRecord(
            topology_id="topology.validation-runner",
            environment="test",
            topology_class="canonical",
            nodes=["runtime", "scheduler", "trace"],
            edges=["scheduler->runtime", "runtime->trace"],
        ),
        RuntimeTopologyRecord(
            topology_id="topology.distributed-core",
            environment="prod",
            topology_class="canonical",
            nodes=["boundary", "runtime", "scheduler", "observability", "resilience"],
            edges=["boundary->runtime", "scheduler->runtime", "runtime->observability", "runtime->resilience"],
        ),
        RuntimeTopologyRecord(
            topology_id="topology.drill-fault-path",
            environment="drill",
            topology_class="adapted",
            nodes=["runtime", "resilience", "operator"],
            edges=["runtime->resilience", "resilience->operator"],
        ),
        RuntimeTopologyRecord(
            topology_id="topology.legacy-bridge",
            environment="dev",
            topology_class="legacy",
            nodes=["boundary", "runtime"],
            edges=["boundary->runtime"],
        ),
    ]
