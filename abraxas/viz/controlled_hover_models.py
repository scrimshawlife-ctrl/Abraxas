from __future__ import annotations

ARTIFACT = "AAL-VIZ-CONTROLLED-HOVER-POLICY-PACKET-001"
SCHEMA_VERSION = "AALVizControlledHoverPolicyPacket.v1"

DRIFT_HOOKS = [
    "hover_runtime_api_scan",
    "event_listener_binding_scan",
    "component_source_mutation_scan",
    "authority_regression_scan",
    "frontend_execution_regression_scan",
]

AUTHORITY = {
    "hover_policy_packet_generation": True,
    "hover_runtime": False,
    "interaction_runtime": False,
    "event_listener_binding": False,
    "component_source_mutation": False,
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
