from __future__ import annotations

ARTIFACT = "AAL-VIZ-WEBGL-STATIC-VIEWER-001"
SCHEMA_VERSION = "AALVizWebGLStaticViewerSpec.v1"

AUTHORITY = {
    "static_viewer_spec_generation": True,
    "webgl_rendering": False,
    "animation_runtime": False,
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

VIEWER = {
    "viewer_type": "static_webgl_contract",
    "renderer_target": "react_webgl_component",
    "runtime_mode": "static_no_loop",
    "supports_interaction": False,
    "supports_animation": False,
}

COMPONENT_CONTRACT = {
    "component_name": "AALVizCanaryWebGLStaticViewer",
    "required_props": ["renderBundle", "width", "height"],
    "optional_props": ["className", "debug"],
}

PROPS_SCHEMA = {
    "renderBundle": {"schema_ref": "AALVizWebGLRenderBundle.v1", "required": True},
    "width": {"type": "number", "required": True, "default": 1200},
    "height": {"type": "number", "required": True, "default": 800},
    "className": {"type": "string", "required": False, "default": None},
    "debug": {"type": "boolean", "required": False, "default": False},
}

ASSET_BINDINGS = {
    "positions_buffer": {"source": "buffers.positions", "item_size": 3},
    "colors_buffer": {"source": "buffers.colors", "item_size": 3},
    "indices_buffer": {"source": "buffers.indices", "item_size": 1},
}

INTERACTION_POLICY = {"pan": False, "zoom": False, "select": False, "hover": False}
