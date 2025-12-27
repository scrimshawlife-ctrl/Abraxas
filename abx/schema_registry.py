"""
abx/schema_registry.py
Thin wrapper around generated schemas + strict overrides.
"""

from abx.schema_registry_gen import SCHEMAS as GEN_SCHEMAS

OVERRIDES = {
    "actuator.apply": {
        "required": {"action_plan": list, "governance_receipt_id": str},
        "optional": {"dry_run": bool, "seed": int},
        "allow_extra": False,
    },
    "compression.detect": {
        "required": {"text_event": str, "config": dict},
        "optional": {"seed": int},
        "allow_extra": True,
    },
    "infra.self_heal": {
        "required": {"health_state": dict, "policy": dict},
        "optional": {"audit_report_sha256": str, "seed": int},
        "allow_extra": True,
    },
}


def schema_for(rune_id: str):
    return OVERRIDES.get(rune_id) or GEN_SCHEMAS.get(rune_id)
