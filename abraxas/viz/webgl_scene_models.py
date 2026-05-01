from __future__ import annotations

from typing import Any, Dict, List

ARTIFACT = "AAL-VIZ-WEBGL-SCENE-SPEC-001"
SCHEMA_VERSION = "AALVizWebGLSceneSpec.v1"

AUTHORITY = {
    "webgl_scene_spec_generation": True,
    "webgl_rendering": False,
    "animation_runtime": False,
    "physics_simulation": False,
    "inference": False,
    "production_activation": False,
    "baseline_mutation": False,
    "runtime_config_write": False,
    "promotion": False,
    "execution": False,
    "scheduler": False,
}

MATERIALS = {
    "color_tokens": {
        "stable": "#00FFC6",
        "warning": "#FFB800",
        "critical": "#FF3B3B",
    }
}


def default_layout(node_count: int) -> Dict[str, Any]:
    grid_width = max(1, min(8, node_count if node_count > 0 else 1))
    grid_height = max(1, (node_count + grid_width - 1) // grid_width)
    return {"algorithm": "deterministic_grid_v1", "grid_width": grid_width, "grid_height": grid_height, "spacing": 10.0}
