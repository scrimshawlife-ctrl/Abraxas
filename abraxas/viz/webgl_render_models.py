from __future__ import annotations

ARTIFACT = "AAL-VIZ-WEBGL-RENDERER-SCAFFOLD-001"
SCHEMA_VERSION = "AALVizWebGLRenderBundle.v1"

AUTHORITY = {
    "webgl_render_bundle_generation": True,
    "webgl_rendering": False,
    "animation_runtime": False,
    "physics_simulation": False,
    "browser_runtime": False,
    "inference": False,
    "production_activation": False,
    "baseline_mutation": False,
    "runtime_config_write": False,
    "promotion": False,
    "execution": False,
    "scheduler": False,
}

COLOR_MAP = {
    "stable": [0.0, 1.0, 0.78],
    "warning": [1.0, 0.72, 0.0],
    "critical": [1.0, 0.23, 0.23],
}
