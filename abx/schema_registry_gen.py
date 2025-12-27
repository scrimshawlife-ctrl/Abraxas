# AUTO-GENERATED. DO NOT EDIT.
# meta: {"count":8,"generated_at_utc":"2025-12-27T22:54:50.274391+00:00","registry_sha256":"6718078bade65c242ae656820659620342d71b4bf64170eff6beb3be65f1cfdd"}

SCHEMAS = {
  "compression.detect": {
    "required": {
      "text_event": str,
      "config": dict,
    },
    "optional": {
      "lexicon_ref": dict,
      "seed": int,
    },
    "allow_extra": True,
  },
  "weather.generate": {
    "required": {
      "compression_event": dict,
      "time_window": dict,
      "config": dict,
    },
    "optional": {
    },
    "allow_extra": True,
  },
  "ser.run": {
    "required": {
      "priors": dict,
      "signals": dict,
      "seed": dict,
      "config": dict,
    },
    "optional": {
    },
    "allow_extra": True,
  },
  "daemon.ingest": {
    "required": {
      "source_config": dict,
      "poll_interval": dict,
      "config": dict,
    },
    "optional": {
    },
    "allow_extra": True,
  },
  "infra.self_heal": {
    "required": {
      "health_state": dict,
      "policy": dict,
    },
    "optional": {
      "audit_report_sha256": str,
      "config": dict,
      "seed": int,
    },
    "allow_extra": True,
  },
  "actuator.apply": {
    "required": {
      "action_plan": list,
      "governance_receipt_id": str,
    },
    "optional": {
      "dry_run": bool,
      "config": dict,
      "seed": int,
    },
    "allow_extra": True,
  },
  "edge.deploy_orin": {
    "required": {
      "target_profile": dict,
      "release_artifacts": dict,
      "config": dict,
    },
    "optional": {
    },
    "allow_extra": True,
  },
  "abx.doctor": {
    "required": {
      "diagnostic_level": dict,
      "config": dict,
    },
    "optional": {
    },
    "allow_extra": True,
  },
}

def schema_for(rune_id: str):
    return SCHEMAS.get(rune_id)
