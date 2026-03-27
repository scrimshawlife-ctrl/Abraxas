from __future__ import annotations

from abx.security.authorityInventory import build_action_permissions


def build_authority_precedence() -> list[str]:
    return [x.permission_id for x in sorted(build_action_permissions(), key=lambda r: (r.precedence, r.permission_id))]


def detect_hidden_privilege_drift() -> list[str]:
    drift: list[str] = []
    for row in build_action_permissions():
        if row.authorization == "authorized" and "override" in row.action_class:
            drift.append(row.permission_id)
    return sorted(drift)
