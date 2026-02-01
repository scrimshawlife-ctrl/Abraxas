"""
Test: Resonance Narratives - Schema Validation

Verify that rendered output validates against the narrative_bundle.schema.json.
"""

import json
from pathlib import Path

import jsonschema

from abraxas.renderers.resonance_narratives import render_narrative_bundle


def load_schema():
    """Load the narrative bundle JSON schema."""
    schema_path = Path("schemas/renderers/resonance_narratives/v1/narrative_bundle.schema.json")
    with open(schema_path) as f:
        return json.load(f)


def test_schema_validation_baseline():
    """Test that baseline envelope renders to valid schema."""
    schema = load_schema()
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    # Should not raise ValidationError
    jsonschema.validate(instance=bundle, schema=schema)


def test_schema_validation_with_evidence():
    """Test that envelope with evidence renders to valid schema."""
    schema = load_schema()
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/with_evidence.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    # Should not raise ValidationError
    jsonschema.validate(instance=bundle, schema=schema)


def test_schema_validation_missing_inputs():
    """Test that envelope with missing inputs still produces valid schema."""
    schema = load_schema()
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/missing_inputs.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    # Should not raise ValidationError even with missing inputs
    jsonschema.validate(instance=bundle, schema=schema)

    # Should report missing inputs in constraints
    assert len(bundle["constraints_report"]["missing_inputs"]) > 0


def test_schema_required_fields():
    """Test that all required fields are present in rendered output."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    # Required top-level fields
    required = [
        "schema_version",
        "artifact_id",
        "headline",
        "signal_summary",
        "provenance_footer",
        "constraints_report",
    ]

    for field in required:
        assert field in bundle, f"Required field {field} missing from bundle"


def test_schema_artifact_id_format():
    """Test that artifact_id follows the required pattern."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    artifact_id = bundle["artifact_id"]
    assert artifact_id.startswith("NARR-"), "artifact_id should start with NARR-"
    assert len(artifact_id) > 5, "artifact_id should have content after prefix"


def test_schema_headline_length():
    """Test that headline respects max length constraint."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    headline = bundle["headline"]
    assert len(headline) <= 120, "Headline should be max 120 characters"


def test_schema_provenance_input_hash_format():
    """Test that input_hash is a valid SHA-256 hex string."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    input_hash = bundle["provenance_footer"]["input_hash"]
    assert len(input_hash) == 64, "SHA-256 hash should be 64 hex chars"
    assert all(c in "0123456789abcdef" for c in input_hash), "Hash should be lowercase hex"


def test_schema_signal_summary_pointers():
    """Test that all signal_summary items have valid JSON pointers."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    for item in bundle["signal_summary"]:
        assert "pointer" in item, "signal_summary item must have pointer"
        assert item["pointer"].startswith("/"), "Pointer must start with /"


def test_schema_motifs_strength_range():
    """Test that motif strengths are in valid 0-1 range."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    for motif in bundle["motifs"]:
        strength = motif["strength"]
        assert 0.0 <= strength <= 1.0, f"Motif strength {strength} out of range [0,1]"
