"""
abx/schema_registry.py
Thin wrapper around generated schemas + strict overrides.
"""

from abx.schema_registry_gen import PAYLOAD_SCHEMAS as GEN_PAYLOAD
from abx.schema_registry_gen import RESULT_SCHEMAS as GEN_RESULT

# Strict overrides (hand-authored, minimal surface area)
OVERRIDES = {
    "actuator.apply": {
        "payload": {
            "required": {"action_plan": list, "governance_receipt_id": str},
            "optional": {"dry_run": bool, "seed": int, "config": dict},
            "allow_extra": False,
        },
        "result": {
            "required": {"apply_receipt": dict, "verification": dict, "audit_log": list, "provenance_bundle": dict},
            "optional": {},
            "allow_extra": False,
        },
    },
    "compression.detect": {
        "payload": {
            "required": {"text_event": str, "config": dict},
            "optional": {"lexicon_ref": dict, "seed": int},
            "allow_extra": True,
        },
        "result": {
            "required": {"compression_event": dict, "provenance_bundle": dict},
            "optional": {"metrics": dict, "labels": list, "confidence": float},
            "allow_extra": True,
        },
    },
    "infra.self_heal": {
        "payload": {
            "required": {"health_state": dict, "policy": dict},
            "optional": {"audit_report_sha256": str, "config": dict, "seed": int},
            "allow_extra": True,
        },
        "result": {
            "required": {"issues": list, "action_plan": list, "evidence": dict, "provenance_bundle": dict},
            "optional": {"audit_log": dict},
            "allow_extra": True,
        },
    },
}


def payload_schema_for(rune_id: str):
    """Get payload (input) schema for a rune."""
    o = OVERRIDES.get(rune_id)
    return (o.get("payload") if o else None) or GEN_PAYLOAD.get(rune_id)


def result_schema_for(rune_id: str):
    """Get result (output) schema for a rune."""
    o = OVERRIDES.get(rune_id)
    return (o.get("result") if o else None) or GEN_RESULT.get(rune_id)


def schema_for(rune_id: str):
    """Backwards compatibility - returns payload schema."""
    return payload_schema_for(rune_id)
