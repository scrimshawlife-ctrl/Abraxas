import json
from pathlib import Path

import jsonschema
import pytest


def _load_schema(name: str) -> dict:
    path = Path("schemas") / name
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def test_input_envelope_v2_schema_valid():
    schema = _load_schema("input_envelope.v2.json")
    sample = {
        "signal_sources": ["mda", "telemetry"],
        "payload": {"alpha": {"beta": 1}},
        "metadata": {
            "tier": "psychonaut",
            "lane": "canon",
            "provenance_status": "complete",
            "invariance_status": "pass",
            "drift_flags": [],
        },
        "context": {"unknowns": [{"region_id": "r1", "reason_code": "missing"}]},
    }
    jsonschema.validate(instance=sample, schema=schema)


def test_input_envelope_v2_rejects_extra_metadata():
    schema = _load_schema("input_envelope.v2.json")
    sample = {
        "signal_sources": ["mda"],
        "payload": {"alpha": 1},
        "metadata": {
            "tier": "psychonaut",
            "lane": "canon",
            "provenance_status": "complete",
            "invariance_status": "pass",
            "drift_flags": [],
            "extra": "nope",
        },
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=sample, schema=schema)


def test_oracle_output_v2_schema_valid():
    schema = _load_schema("oracle_output.v2.json")
    sample = {
        "signal_id": "sig-001",
        "tier": "psychonaut",
        "lane": "canon",
        "indicators": {"pressure": {"score": 0.5}},
        "evidence": [],
        "flags": {"suppressed": False},
        "provenance": {
            "input_hash": "hash_in",
            "policy_hash": "hash_policy",
            "operator_versions": {"extract_structure_v0": "v0"},
            "stability_status": {"passed": True, "drift_class": "none"},
        },
    }
    jsonschema.validate(instance=sample, schema=schema)
