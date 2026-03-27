from __future__ import annotations

from abx.deployment.configInventory import build_config_inventory
from abx.deployment.types import ConfigClassificationRecord



def build_config_classifications() -> list[ConfigClassificationRecord]:
    out = []
    for x in build_config_inventory():
        if x["secret"]:
            classification = "secret"
        elif x["config_key"].startswith("env.override"):
            classification = "semantic/runtime-affecting"
        elif x["config_key"].startswith("observability"):
            classification = "operational-only"
        else:
            classification = "semantic/runtime-affecting"
        out.append(
            ConfigClassificationRecord(
                config_key=x["config_key"],
                classification=classification,
                owner=str(x["owner"]),
                affects=list(x["affects"]),
            )
        )
    return out



def classify_config_surface() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for x in build_config_classifications():
        grouped.setdefault(x.classification, []).append(x.config_key)
    return {k: sorted(v) for k, v in grouped.items()}
