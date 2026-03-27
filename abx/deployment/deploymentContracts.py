from __future__ import annotations

from abx.deployment.deploymentInventory import build_deployment_contract_inventory



def build_environment_deployment_contracts() -> dict[str, list[dict[str, object]]]:
    by_environment: dict[str, list[dict[str, object]]] = {}
    for x in build_deployment_contract_inventory():
        by_environment.setdefault(x.environment, []).append(
            {
                "deployment_id": x.deployment_id,
                "entrypoint": x.entrypoint,
                "preconditions": sorted(x.expected_inputs),
                "topology": x.expected_topology,
                "postconditions": sorted(x.postconditions),
                "classification": x.classification,
            }
        )
    return {k: sorted(v, key=lambda it: it["deployment_id"]) for k, v in by_environment.items()}
