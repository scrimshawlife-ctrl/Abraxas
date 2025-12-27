# AUTO-GENERATED. DO NOT EDIT.
# meta: {"count":8,"generated_at_utc":"2025-12-27T23:00:34.946924+00:00","registry_sha256":"1f626e140a3017e0cef62dd92d54cdaa88bad30408548623c8be764a4d9069f8"}

PAYLOAD_SCHEMAS = {
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

RESULT_SCHEMAS = {
  "compression.detect": {
    "required": {
      "compression_event": dict,
      "provenance_bundle": dict,
    },
    "optional": {
      "metrics": dict,
      "labels": list,
      "confidence": float,
    },
    "allow_extra": True,
  },
  "weather.generate": {
    "required": {
    },
    "optional": {
      "weather_report": dict,
      "drift_vectors": dict,
      "provenance_bundle": dict,
    },
    "allow_extra": True,
  },
  "ser.run": {
    "required": {
    },
    "optional": {
      "envelope": dict,
      "cascade_sheet": dict,
      "contamination_advisory": dict,
      "provenance_bundle": dict,
    },
    "allow_extra": True,
  },
  "daemon.ingest": {
    "required": {
    },
    "optional": {
      "raw_events": dict,
      "ingest_log": dict,
      "provenance_bundle": dict,
    },
    "allow_extra": True,
  },
  "infra.self_heal": {
    "required": {
      "issues": list,
      "action_plan": list,
      "evidence": dict,
      "provenance_bundle": dict,
    },
    "optional": {
      "audit_log": dict,
    },
    "allow_extra": True,
  },
  "actuator.apply": {
    "required": {
      "apply_receipt": dict,
      "verification": dict,
      "audit_log": list,
      "provenance_bundle": dict,
    },
    "optional": {
    },
    "allow_extra": True,
  },
  "edge.deploy_orin": {
    "required": {
    },
    "optional": {
      "deploy_receipt": dict,
      "rollback_point": dict,
      "provenance_bundle": dict,
    },
    "allow_extra": True,
  },
  "abx.doctor": {
    "required": {
    },
    "optional": {
      "diagnostic_report": dict,
      "provenance_bundle": dict,
    },
    "allow_extra": True,
  },
}

# Backwards compatibility
SCHEMAS = PAYLOAD_SCHEMAS

def payload_schema_for(rune_id: str):
    return PAYLOAD_SCHEMAS.get(rune_id)

def result_schema_for(rune_id: str):
    return RESULT_SCHEMAS.get(rune_id)

def schema_for(rune_id: str):
    """Backwards compatibility - returns payload schema."""
    return PAYLOAD_SCHEMAS.get(rune_id)
