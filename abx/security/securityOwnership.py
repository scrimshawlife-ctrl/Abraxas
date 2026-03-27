from __future__ import annotations

from abx.security.securityInventory import build_security_surface_inventory


def build_security_ownership() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for record in build_security_surface_inventory():
        out.setdefault(record.owner, []).append(record.surface_id)
    return {k: sorted(v) for k, v in sorted(out.items())}
