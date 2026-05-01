from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.viz.interaction_policy_models import ALLOWED_FUTURE_INTERACTIONS, ARTIFACT, AUTHORITY, FORBIDDEN_INTERACTIONS, SCHEMA_VERSION, STATE_MODEL
from abraxas.viz.interaction_policy_validator import validate_policy


def build_interaction_policy(viewer_spec: Dict[str, Any], component_manifest: Dict[str, Any]) -> Dict[str, Any]:
    viewer_hash = sha256_hex(canonical_json(deepcopy(viewer_spec)))
    component_hash = sha256_hex(canonical_json(deepcopy(component_manifest)))

    policy = {
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "allowed_future_interactions": list(ALLOWED_FUTURE_INTERACTIONS),
        "forbidden_interactions": list(FORBIDDEN_INTERACTIONS),
        "interaction_state_model": deepcopy(STATE_MODEL),
        "event_policy": {"event_binding_allowed": False, "event_types_defined": ["pointer_move", "pointer_down"]},
        "mutation_policy": {
            "runtime_mutation_allowed": False,
            "allowed_targets": [],
            "forbidden_targets": ["render_bundle", "viewer_spec", "component_source"],
        },
        "authority": dict(AUTHORITY),
        "lineage": {"viewer_spec_hash": viewer_hash, "component_manifest_hash": component_hash},
        "policy_id": "",
        "policy_hash": "",
    }

    policy_id_payload = {
        "artifact": policy["artifact"],
        "schema_version": policy["schema_version"],
        "allowed_future_interactions": policy["allowed_future_interactions"],
        "forbidden_interactions": policy["forbidden_interactions"],
        "interaction_state_model": policy["interaction_state_model"],
        "event_policy": policy["event_policy"],
        "mutation_policy": policy["mutation_policy"],
        "authority": policy["authority"],
        "lineage": policy["lineage"],
    }
    policy["policy_id"] = sha256_hex(canonical_json(policy_id_payload))
    policy["policy_hash"] = sha256_hex(canonical_json(policy))
    validate_policy(policy)
    return policy
