from __future__ import annotations

from abx.security.authorityInventory import build_action_permissions, build_authority_inventory


AUTHORIZED = (
    "authorized",
    "authorized_under_condition",
    "waiver_backed",
    "emergency_only",
    "prohibited",
    "unknown",
)


def classify_authority_boundaries() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in AUTHORIZED}
    for row in build_authority_inventory():
        key = row.authority_status if row.authority_status in out else "unknown"
        out[key].append(row.boundary_id)
    return {k: sorted(v) for k, v in out.items()}


def classify_action_permissions() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in AUTHORIZED}
    for row in build_action_permissions():
        key = row.authorization if row.authorization in out else "unknown"
        out[key].append(row.permission_id)
    return {k: sorted(v) for k, v in out.items()}


def detect_redundant_authority_models() -> list[str]:
    seen: set[tuple[str, str]] = set()
    redundant: list[str] = []
    for row in build_action_permissions():
        key = (row.action_surface, row.action_class)
        if key in seen:
            redundant.append(row.permission_id)
            continue
        seen.add(key)
    return sorted(redundant)
