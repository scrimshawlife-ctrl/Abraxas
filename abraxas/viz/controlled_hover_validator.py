from __future__ import annotations

from typing import Any, Dict

from abraxas.viz.controlled_hover_models import AUTHORITY


def validate(packet: Dict[str, Any]) -> None:
    if packet["authority"] != AUTHORITY:
        raise ValueError("authority mismatch")
    if packet["interaction"]["runtime_enabled"] is not False:
        raise ValueError("runtime_enabled must be false")
    if packet["interaction"]["event_binding_enabled"] is not False:
        raise ValueError("event_binding_enabled must be false")
    if packet["interaction"]["component_mutation_required"] is not False:
        raise ValueError("component_mutation_required must be false")
    if packet["status"]["value"] not in {"blocked", "review_ready", "not_computable"}:
        raise ValueError("invalid status")
    if packet["status"]["value"] == "review_ready" and packet["status"]["blockers"]:
        raise ValueError("review_ready must have no blockers")
    if packet["status"]["value"] == "blocked" and not packet["status"]["blockers"]:
        raise ValueError("blocked must have blockers")
    if "requestAnimationFrame" not in packet["hover_contract"]["forbidden_runtime_apis"]:
        raise ValueError("missing forbidden api")
    if "pointermove" not in packet["hover_contract"]["forbidden_runtime_bindings"]:
        raise ValueError("missing forbidden binding")
