from __future__ import annotations

from abx.deployment.environmentInventory import build_environment_inventory



def classify_environment_taxonomy() -> dict[str, list[str]]:
    classes: dict[str, list[str]] = {}
    for env in build_environment_inventory():
        classes.setdefault(env["class"], []).append(env["environment"])
    return {k: sorted(v) for k, v in classes.items()}



def detect_redundant_environment_taxonomy() -> list[str]:
    taxonomy = classify_environment_taxonomy()
    return sorted([k for k, v in taxonomy.items() if len(v) > 2 and k in {"dev", "test", "staging-like"}])
