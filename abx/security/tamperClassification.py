from __future__ import annotations

from abx.security.integrityInventory import build_tamper_resistance_inventory


def classify_tamper_resistance() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"governed": [], "partial": [], "legacy_exposure": []}
    for record in build_tamper_resistance_inventory():
        out[record.resistance_level if record.resistance_level in out else "legacy_exposure"].append(record.tamper_id)
    return {k: sorted(v) for k, v in out.items()}
