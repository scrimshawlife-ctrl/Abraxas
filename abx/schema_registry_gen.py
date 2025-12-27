# AUTO-GENERATED. DO NOT EDIT.
# meta: {"count":8,"generated_at_utc":"2025-12-27T22:48:20.487904+00:00","registry_sha256":"e88642bdc180c7aa821449c04d9e60c0c997e8cdc1a852db9fc2cdbe6d03ca88"}

SCHEMAS = {
  "compression.detect": {
    "required": {
      "text_event": str,
      "lexicon_ref": dict,
      "config": dict,
    },
    "optional": {
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
      "seed": int,
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
      "seed": int,
    },
    "allow_extra": True,
  },
  "infra.self_heal": {
    "required": {
      "health_state": dict,
      "policy": dict,
      "config": dict,
    },
    "optional": {
      "seed": int,
    },
    "allow_extra": True,
  },
  "actuator.apply": {
    "required": {
      "action_plan": list,
      "governance_receipt_id": dict,
      "config": dict,
    },
    "optional": {
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
      "seed": int,
    },
    "allow_extra": True,
  },
  "abx.doctor": {
    "required": {
      "diagnostic_level": dict,
      "config": dict,
    },
    "optional": {
      "seed": int,
    },
    "allow_extra": True,
  },
}

def schema_for(rune_id: str):
    return SCHEMAS.get(rune_id)
