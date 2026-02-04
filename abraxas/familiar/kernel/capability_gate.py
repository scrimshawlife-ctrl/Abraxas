from __future__ import annotations

from typing import Any, Dict, Iterable, List


def evaluate_capabilities(
    policy_snapshot: Dict[str, Any],
    requested_capabilities: Iterable[str],
) -> Dict[str, Any]:
    grants = policy_snapshot.get("capability_grants", [])
    allowed_set = {
        grant.get("capability_id")
        for grant in grants
        if grant.get("granted") is True
    }

    requested = sorted({cap for cap in requested_capabilities if isinstance(cap, str)})
    granted = sorted([cap for cap in requested if cap in allowed_set])
    denied = sorted([cap for cap in requested if cap not in allowed_set])

    allowed = len(denied) == 0
    reason_code = "ok" if allowed else "capability_denied"

    return {
        "schema_version": "v0",
        "policy_id": policy_snapshot.get("policy_id"),
        "allowed": allowed,
        "reason_code": reason_code,
        "granted_capabilities": granted,
        "denied_capabilities": denied,
        "details": None,
    }
