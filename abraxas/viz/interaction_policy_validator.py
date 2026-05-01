from __future__ import annotations

from typing import Any, Dict


def validate_policy(policy: Dict[str, Any]) -> None:
    if policy["event_policy"]["event_binding_allowed"] is not False:
        raise ValueError("event_binding_allowed must be false")
    if policy["mutation_policy"]["runtime_mutation_allowed"] is not False:
        raise ValueError("runtime_mutation_allowed must be false")

    overlap = set(policy["allowed_future_interactions"]).intersection(set(policy["forbidden_interactions"]))
    if overlap:
        raise ValueError("allowed and forbidden interactions overlap")

    authority = policy["authority"]
    must_false = [
        "interaction_runtime", "event_listener_binding", "animation_runtime", "request_animation_frame",
        "physics_simulation", "browser_runtime_mutation", "inference", "production_activation", "baseline_mutation",
        "runtime_config_write", "promotion", "execution", "scheduler",
    ]
    if authority.get("interaction_policy_generation") is not True:
        raise ValueError("interaction_policy_generation must be true")
    for key in must_false:
        if authority.get(key) is not False:
            raise ValueError(f"{key} must be false")
