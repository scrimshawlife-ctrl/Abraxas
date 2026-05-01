from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.viz.controlled_hover_models import ARTIFACT, AUTHORITY, DRIFT_HOOKS, SCHEMA_VERSION
from abraxas.viz.controlled_hover_validator import validate


def _hash(x: Dict[str, Any]) -> str:
    return sha256_hex(canonical_json(x))


def _policy_ledger_review_ready(ledger: Dict[str, Any]) -> bool:
    entries = list(ledger.get("entries") or [])
    if not entries:
        return False
    latest = sorted(entries, key=lambda e: str(e.get("entry_id", "")))[-1]
    return str((latest.get("promotion_status") or {}).get("status")) == "review_ready"


def _component_manifest_present(cm: Dict[str, Any]) -> bool:
    return bool(cm.get("artifact") and cm.get("schema_version"))


def _runtime_authority_locked() -> bool:
    keys = ["hover_runtime", "interaction_runtime", "event_listener_binding", "component_source_mutation", "animation_runtime", "request_animation_frame", "physics_simulation", "browser_runtime_mutation", "execution", "scheduler"]
    return all(AUTHORITY[k] is False for k in keys)


def build_packet(interaction_policy: Dict[str, Any], policy_ledger: Dict[str, Any], provisioning_manifest: Dict[str, Any], ci_proof: Dict[str, Any], component_manifest: Dict[str, Any]) -> Dict[str, Any]:
    try:
        ih = _hash(interaction_policy)
        lh = _hash(policy_ledger)
        ph = _hash(provisioning_manifest)
        ch = _hash(ci_proof)
        cmh = _hash(component_manifest)
    except Exception:
        return _not_computable_packet()

    required = [interaction_policy.get("policy_hash"), ci_proof.get("proof_hash"), component_manifest.get("manifest_hash")]
    if any(x is None for x in required):
        return _not_computable_packet()

    readiness = {
        "frontend_execution_verified": ci_proof.get("frontend_execution") == "verified",
        "policy_ledger_review_ready": _policy_ledger_review_ready(policy_ledger),
        "component_manifest_present": _component_manifest_present(component_manifest),
        "interaction_policy_allows_node_hover": "node_hover" in list(interaction_policy.get("allowed_future_interactions") or []),
        "runtime_authority_locked": _runtime_authority_locked(),
    }

    status, reason, blockers = _status_from_readiness(readiness)

    packet = _base_packet()
    packet["status"] = {"value": status, "reason": reason, "blockers": blockers}
    packet["readiness"] = readiness
    packet["lineage"] = {
        "interaction_policy_hash": ih,
        "policy_ledger_hash": lh,
        "provisioning_manifest_hash": ph,
        "ci_proof_hash": ch,
        "component_manifest_hash": cmh,
    }
    packet_id_payload = {k: packet[k] for k in ["artifact", "schema_version", "interaction", "status", "readiness", "hover_contract", "drift_hooks", "lineage", "authority"]}
    packet["packet_id"] = sha256_hex(canonical_json(packet_id_payload))
    packet["packet_hash"] = sha256_hex(canonical_json(packet))
    validate(packet)
    return packet


def _status_from_readiness(r: Dict[str, bool]) -> tuple[str, str, List[str]]:
    blockers: List[str] = []
    if not r["frontend_execution_verified"]:
        blockers.append("frontend_execution_not_verified")
        return "blocked", "frontend_execution_not_verified", blockers
    if not r["policy_ledger_review_ready"]:
        blockers.append("policy_ledger_not_review_ready")
        return "blocked", "policy_ledger_not_review_ready", blockers
    if not r["interaction_policy_allows_node_hover"]:
        blockers.append("node_hover_not_allowed_by_policy")
        return "blocked", "node_hover_not_allowed_by_policy", blockers
    if not r["runtime_authority_locked"]:
        blockers.append("runtime_authority_not_locked")
        return "blocked", "runtime_authority_not_locked", blockers
    return "review_ready", "controlled_hover_policy_packet_ready", []


def _base_packet() -> Dict[str, Any]:
    return {
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "packet_id": "",
        "packet_hash": "",
        "interaction": {"name": "node_hover", "category": "controlled_interaction_candidate", "runtime_enabled": False, "event_binding_enabled": False, "component_mutation_required": False},
        "hover_contract": {
            "target_type": "node",
            "input_event_family": "pointer",
            "conceptual_events": ["pointer_move"],
            "forbidden_runtime_bindings": ["pointermove", "mousemove", "mouseover"],
            "forbidden_runtime_apis": ["requestAnimationFrame", "setInterval", "setTimeout", "Math.random", "Date.now"],
        },
        "drift_hooks": list(DRIFT_HOOKS),
        "authority": dict(AUTHORITY),
    }


def _not_computable_packet() -> Dict[str, Any]:
    p = _base_packet()
    p["status"] = {"value": "not_computable", "reason": "missing_or_invalid_input", "blockers": ["missing_or_invalid_input"]}
    p["readiness"] = {"frontend_execution_verified": False, "policy_ledger_review_ready": False, "component_manifest_present": False, "interaction_policy_allows_node_hover": False, "runtime_authority_locked": _runtime_authority_locked()}
    p["lineage"] = {"interaction_policy_hash": "", "policy_ledger_hash": "", "provisioning_manifest_hash": "", "ci_proof_hash": "", "component_manifest_hash": ""}
    pid_payload = {k: p[k] for k in ["artifact", "schema_version", "interaction", "status", "readiness", "hover_contract", "drift_hooks", "lineage", "authority"]}
    p["packet_id"] = sha256_hex(canonical_json(pid_payload))
    p["packet_hash"] = sha256_hex(canonical_json(p))
    return p
