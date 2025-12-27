# Deployment policy loader (v0.1)

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[1] / ".aal" / "policy.json"


def load_policy(path: str | None = None) -> Dict[str, Any]:
    policy_path = Path(path) if path else DEFAULT_POLICY_PATH
    if not policy_path.exists():
        return {
            "profile": "default",
            "allow_runes": [
                "compression.detect",
                "weather.generate",
                "ser.run",
                "abx.doctor",
                "infra.self_heal",
            ],
            "deny_runes": ["actuator.apply"],
            "stabilization": {"required_advisory_cycles": 3},
        }
    return json.loads(policy_path.read_text(encoding="utf-8"))


def is_allowed(policy: Dict[str, Any], rune_id: str) -> bool:
    deny = set(policy.get("deny_runes", []) or [])
    if rune_id in deny:
        return False
    allow = policy.get("allow_runes")
    if allow is None:
        return True
    return rune_id in set(allow)
