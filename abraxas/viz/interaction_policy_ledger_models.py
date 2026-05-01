from __future__ import annotations

import hashlib
from typing import Any, Dict

from abraxas.core.canonical import canonical_json


def sha256_json(data: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


AUTHORITY = {
    "interaction_policy_ledger_write": True,
    "promotion_gate_evaluation": True,
    "drift_hook_generation": True,
    "interaction_runtime": False,
    "event_listener_binding": False,
    "animation_runtime": False,
    "request_animation_frame": False,
    "physics_simulation": False,
    "browser_runtime_mutation": False,
    "inference": False,
    "production_activation": False,
    "baseline_mutation": False,
    "runtime_config_write": False,
    "promotion": False,
    "execution": False,
    "scheduler": False,
}
