from __future__ import annotations

from abx.security.abuseInventory import build_abuse_containment_inventory, build_abuse_path_inventory


def classify_abuse_containment() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"contained": [], "monitored": [], "partial": [], "not_computable": []}
    for record in build_abuse_containment_inventory():
        bucket = record.status if record.status in out else "not_computable"
        out[bucket].append(record.containment_id)
    return {k: sorted(v) for k, v in out.items()}


def validate_containment_linkage() -> list[str]:
    known = {x.abuse_id for x in build_abuse_path_inventory()}
    missing = [x.containment_id for x in build_abuse_containment_inventory() if x.abuse_id not in known]
    return sorted(missing)
