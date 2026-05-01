from __future__ import annotations

ARTIFACT = "AAL-VIZ-CONTROLLED-HOVER-RUNTIME-SCAFFOLD-001"
SCHEMA_VERSION = "AALVizControlledHoverRuntimeScaffold.v1"

DRIFT_HOOKS = [
    "event_binding_scan",
    "raf_usage_scan",
    "async_loop_scan",
    "component_mutation_scan",
    "hover_state_leak_scan",
]

AUTHORITY = {
    "scaffold_generation": True,
    "runtime_enabled": False,
    "event_binding": False,
    "component_mutation": False,
    "animation": False,
    "execution": False,
}
