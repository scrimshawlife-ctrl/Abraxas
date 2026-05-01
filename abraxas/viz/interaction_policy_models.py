from __future__ import annotations

ARTIFACT = "AAL-VIZ-WEBGL-INTERACTION-POLICY-001"
SCHEMA_VERSION = "AALVizWebGLInteractionPolicy.v1"

ALLOWED_FUTURE_INTERACTIONS = [
    "node_hover",
    "node_select",
    "edge_highlight",
    "camera_pan",
    "camera_zoom",
]

FORBIDDEN_INTERACTIONS = [
    "animation_loop",
    "physics_simulation",
    "auto_layout_runtime",
    "mutation_of_render_bundle",
    "mutation_of_viewer_spec",
]

STATE_MODEL = {
    "states": ["idle", "hover_candidate", "selected"],
    "transitions": [
        {"from": "idle", "to": "hover_candidate"},
        {"from": "hover_candidate", "to": "selected"},
    ],
}

AUTHORITY = {
    "interaction_policy_generation": True,
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
