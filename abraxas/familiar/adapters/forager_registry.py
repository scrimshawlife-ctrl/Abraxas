from __future__ import annotations

from typing import Any, Dict, Optional


class ForagerRegistry:
    """
    Minimal registry for loading policy snapshots deterministically.
    """

    def __init__(self, policy_snapshots: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        self._policy_snapshots: Dict[str, Dict[str, Any]] = dict(policy_snapshots or {})

    def register_policy_snapshot(self, snapshot: Dict[str, Any]) -> None:
        policy_id = snapshot.get("policy_id")
        if not isinstance(policy_id, str) or not policy_id:
            raise ValueError("policy_snapshot.policy_id must be a non-empty string")
        self._policy_snapshots[policy_id] = snapshot

    def get_policy_snapshot(self, policy_id: str) -> Optional[Dict[str, Any]]:
        return self._policy_snapshots.get(policy_id)
