from __future__ import annotations

from typing import Any, Dict


def validate_manifest(manifest: Dict[str, Any]) -> None:
    authority = manifest["authority"]
    required_false = [
        "animation_runtime", "request_animation_frame", "physics_simulation", "browser_runtime_mutation", "inference",
        "production_activation", "baseline_mutation", "runtime_config_write", "promotion", "execution", "scheduler",
    ]
    for key in required_false:
        if authority.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if authority.get("react_component_scaffold_generation") is not True:
        raise ValueError("react_component_scaffold_generation must be true")
    if authority.get("static_single_frame_render") is not True:
        raise ValueError("static_single_frame_render must be true")
