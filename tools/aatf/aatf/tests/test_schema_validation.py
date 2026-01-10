import importlib.util
import json
from pathlib import Path

import pytest

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"


def _load_schema(name: str):
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _validate_required(schema: dict, payload: dict):
    for key in schema.get("required", []):
        assert key in payload


def _validate_schema(schema_name: str, payload: dict):
    schema = _load_schema(schema_name)
    if importlib.util.find_spec("jsonschema"):
        import jsonschema  # type: ignore

        jsonschema.validate(instance=payload, schema=schema)
    else:
        _validate_required(schema, payload)


def test_aalmanac_schema():
    payload = {
        "entries": [
            {
                "id": "abc",
                "term_type": "single",
                "term": "signal",
                "context_shift": "context",
                "domain_tags": ["tag"],
                "signals": {"novelty_score": 0.5, "adoption_pressure": 0.5, "drift_charge": 0.2},
                "provenance": {"source_ids": ["src"], "created_at": "1970-01-01T00:00:00Z"},
            }
        ]
    }
    _validate_schema("aalmanac.v0.json", payload)


def test_memetic_weather_schema():
    payload = {
        "report_id": "r1",
        "date": "1970-01-01",
        "regions": ["los_angeles"],
        "motifs": [
            {
                "handle": "h",
                "description": "d",
                "velocity": 0.5,
                "volatility": 0.5,
                "polarity": 0.0,
            }
        ],
        "emergent_terms": ["e1"],
        "evidence": [{"source_id": "s", "title": "t", "url": None}],
    }
    _validate_schema("memetic_weather.v0.json", payload)


def test_neon_genie_schema():
    payload = {
        "run_id": "run",
        "date": "1970-01-01",
        "apps": [
            {
                "id": "a",
                "name": "n",
                "novelty_claim": "c",
                "why_now": "w",
                "category_tags": ["tag"],
                "violates_existing_systems": False,
                "differentiation": "d",
                "vc_gap_hypothesis": "v",
                "risk_notes": "r",
                "build_vector": {
                    "complexity_estimate": "low",
                    "time_estimate": "short",
                    "compute_estimate": "low",
                },
                "provenance": {"source_ids": ["src"], "created_at": "1970-01-01T00:00:00Z"},
            }
        ],
    }
    _validate_schema("neon_genie.v0.json", payload)


def test_rune_proposal_schema():
    payload = {
        "proposals": [
            {
                "proposal_id": "p",
                "rune_name": "r",
                "glyph_ref": None,
                "semantics": "s",
                "oppositions": [],
                "activation_conditions": [],
                "deactivation_conditions": [],
                "mapping": {"codepoint": None, "deck": None},
                "provenance": {"source_ids": ["src"], "created_at": "1970-01-01T00:00:00Z"},
            }
        ]
    }
    _validate_schema("rune_proposal.v0.json", payload)


def test_export_bundle_schema():
    payload = {
        "bundle_id": "b",
        "created_date": "1970-01-01",
        "included_types": ["aalmanac"],
        "file_manifest": [{"path": "aalmanac.v0.json", "sha256": "hash"}],
        "provenance": {"source_ids": ["src"]},
    }
    _validate_schema("export_bundle.v0.json", payload)
