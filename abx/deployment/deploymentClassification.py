from __future__ import annotations

from collections import Counter

from abx.deployment.deploymentInventory import build_deployment_contract_inventory



def classify_deployment_surfaces() -> dict[str, list[str]]:
    inventory = build_deployment_contract_inventory()
    out: dict[str, list[str]] = {
        "authoritative": [],
        "derived": [],
        "legacy": [],
        "redundant": [],
        "deprecated-candidate": [],
    }
    for x in inventory:
        out.setdefault(x.classification, []).append(x.deployment_id)
        if x.classification == "legacy":
            out["deprecated-candidate"].append(x.deployment_id)
    out["redundant"] = detect_duplicate_deployment_entrypoints()
    return {k: sorted(v) for k, v in out.items()}



def deployment_ownership_summary() -> dict[str, list[str]]:
    owners: dict[str, list[str]] = {}
    for x in build_deployment_contract_inventory():
        owners.setdefault(x.owner, []).append(x.deployment_id)
    return {k: sorted(v) for k, v in owners.items()}



def detect_duplicate_deployment_entrypoints() -> list[str]:
    counts = Counter(x.entrypoint for x in build_deployment_contract_inventory())
    return sorted([entrypoint for entrypoint, count in counts.items() if count > 1])
