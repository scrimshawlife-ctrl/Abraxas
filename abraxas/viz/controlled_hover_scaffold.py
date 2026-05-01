from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.viz.controlled_hover_scaffold_models import ARTIFACT, AUTHORITY, DRIFT_HOOKS, SCHEMA_VERSION
from abraxas.viz.controlled_hover_scaffold_validator import validate


def _diff_preview() -> str:
    return "\n".join([
        "--- a/frontend/aal-viz/src/components/AALVizCanaryWebGLStaticViewer.tsx",
        "+++ b/frontend/aal-viz/src/components/AALVizCanaryWebGLStaticViewer.tsx",
        "@@ scaffold-only @@",
        "+ // add pointer_move handler (disabled by gate)",
        "+ // derive hovered node from pointer coordinates",
        "+ // keep no animation loop and no external mutation",
    ])


def build_scaffold(hover_packet: Dict[str, Any], ci_proof: Dict[str, Any], component_manifest: Dict[str, Any]) -> Dict[str, Any]:
    try:
        lineage = {
            "hover_packet_hash": sha256_hex(canonical_json(hover_packet)),
            "ci_proof_hash": sha256_hex(canonical_json(ci_proof)),
            "component_manifest_hash": sha256_hex(canonical_json(component_manifest)),
        }
    except Exception:
        return _not_computable()

    if not isinstance(hover_packet.get("status"), dict) or "frontend_execution" not in ci_proof:
        return _not_computable()

    frontend_execution_verified = ci_proof.get("frontend_execution") == "verified"
    hover_packet_review_ready = hover_packet.get("status", {}).get("value") == "review_ready"

    status, reason, blockers = _status(frontend_execution_verified, hover_packet_review_ready)

    scaffold = {
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "scaffold_id": "",
        "scaffold_hash": "",
        "status": {"value": status, "reason": reason, "blockers": blockers},
        "readiness": {
            "frontend_execution_verified": frontend_execution_verified,
            "hover_packet_review_ready": hover_packet_review_ready,
        },
        "scaffold_plan": {
            "description": "Review-only scaffold for controlled hover runtime integration planning.",
            "component_target": "AALVizCanaryWebGLStaticViewer.tsx",
            "proposed_changes": {
                "add_pointer_move_handler": True,
                "derive_hovered_node_from_coordinates": True,
                "no_animation_loop": True,
                "no_state_mutation_outside_react": True,
            },
        },
        "diff_preview": _diff_preview(),
        "forbidden_runtime": {
            "apis": ["requestAnimationFrame", "setInterval", "setTimeout"],
            "bindings": ["pointermove", "mousemove"],
        },
        "drift_hooks": list(DRIFT_HOOKS),
        "lineage": lineage,
        "authority": dict(AUTHORITY),
    }
    sid_payload = {k: scaffold[k] for k in ["artifact", "schema_version", "status", "readiness", "scaffold_plan", "diff_preview", "forbidden_runtime", "drift_hooks", "lineage", "authority"]}
    scaffold["scaffold_id"] = sha256_hex(canonical_json(sid_payload))
    scaffold["scaffold_hash"] = sha256_hex(canonical_json(scaffold))
    validate(scaffold)
    return scaffold


def _status(frontend_verified: bool, hover_ready: bool) -> tuple[str, str, List[str]]:
    if not hover_ready:
        return "blocked", "hover_packet_not_review_ready", ["hover_packet_not_review_ready"]
    if not frontend_verified:
        return "blocked", "frontend_execution_not_verified", ["frontend_execution_not_verified"]
    return "review_ready", "scaffold_ready_for_manual_review", []


def _not_computable() -> Dict[str, Any]:
    scaffold = {
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "scaffold_id": "",
        "scaffold_hash": "",
        "status": {"value": "not_computable", "reason": "missing_or_invalid_input", "blockers": ["missing_or_invalid_input"]},
        "readiness": {"frontend_execution_verified": False, "hover_packet_review_ready": False},
        "scaffold_plan": {
            "description": "Review-only scaffold for controlled hover runtime integration planning.",
            "component_target": "AALVizCanaryWebGLStaticViewer.tsx",
            "proposed_changes": {
                "add_pointer_move_handler": True,
                "derive_hovered_node_from_coordinates": True,
                "no_animation_loop": True,
                "no_state_mutation_outside_react": True,
            },
        },
        "diff_preview": _diff_preview(),
        "forbidden_runtime": {"apis": ["requestAnimationFrame", "setInterval", "setTimeout"], "bindings": ["pointermove", "mousemove"]},
        "drift_hooks": list(DRIFT_HOOKS),
        "lineage": {"hover_packet_hash": "", "ci_proof_hash": "", "component_manifest_hash": ""},
        "authority": dict(AUTHORITY),
    }
    sid_payload = {k: scaffold[k] for k in ["artifact", "schema_version", "status", "readiness", "scaffold_plan", "diff_preview", "forbidden_runtime", "drift_hooks", "lineage", "authority"]}
    scaffold["scaffold_id"] = sha256_hex(canonical_json(sid_payload))
    scaffold["scaffold_hash"] = sha256_hex(canonical_json(scaffold))
    return scaffold
