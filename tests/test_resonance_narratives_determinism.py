"""
Test: Resonance Narratives - Determinism

Verify that render(envelope) produces exact same output on repeated calls.
"""

import json
from pathlib import Path

from abraxas.renderers.resonance_narratives import render_narrative_bundle


def test_determinism_baseline():
    """Test that rendering the same envelope produces identical output."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")
    with open(fixture_path) as f:
        envelope = json.load(f)

    # Render twice
    # Note: We fix the artifact_id to ensure determinism across renders
    # (created_at will vary, but that's expected for timestamp fields)
    bundle1 = render_narrative_bundle(envelope, artifact_id="NARR-TEST-001")
    bundle2 = render_narrative_bundle(envelope, artifact_id="NARR-TEST-001")

    # Compare all fields except created_at (which is timestamp-based)
    for key in bundle1.keys():
        if key == "provenance_footer":
            # Compare provenance fields except created_at
            for prov_key in bundle1["provenance_footer"].keys():
                if prov_key != "created_at":
                    assert bundle1["provenance_footer"][prov_key] == bundle2["provenance_footer"][prov_key], \
                        f"Provenance field {prov_key} differs between renders"
        else:
            assert bundle1[key] == bundle2[key], f"Field {key} differs between renders"


def test_determinism_input_hash():
    """Test that input_hash is deterministic for same envelope."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")
    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle1 = render_narrative_bundle(envelope)
    bundle2 = render_narrative_bundle(envelope)

    hash1 = bundle1["provenance_footer"]["input_hash"]
    hash2 = bundle2["provenance_footer"]["input_hash"]

    assert hash1 == hash2, "Input hash should be deterministic"
    assert len(hash1) == 64, "Input hash should be 64-char SHA-256"


def test_determinism_signal_summary_order():
    """Test that signal_summary items have stable ordering."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")
    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle1 = render_narrative_bundle(envelope, artifact_id="NARR-TEST-002")
    bundle2 = render_narrative_bundle(envelope, artifact_id="NARR-TEST-002")

    assert bundle1["signal_summary"] == bundle2["signal_summary"], \
        "Signal summary should have deterministic ordering"


def test_determinism_motifs_order():
    """Test that motifs have stable ordering."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")
    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle1 = render_narrative_bundle(envelope, artifact_id="NARR-TEST-003")
    bundle2 = render_narrative_bundle(envelope, artifact_id="NARR-TEST-003")

    assert bundle1["motifs"] == bundle2["motifs"], \
        "Motifs should have deterministic ordering"


def test_determinism_with_evidence():
    """Test determinism with evidence-containing envelope."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/with_evidence.json")
    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle1 = render_narrative_bundle(envelope, artifact_id="NARR-TEST-004")
    bundle2 = render_narrative_bundle(envelope, artifact_id="NARR-TEST-004")

    # Check constraints_report consistency
    assert bundle1["constraints_report"] == bundle2["constraints_report"], \
        "Constraints report should be deterministic"

    # Evidence presence should be consistently detected
    assert bundle1["constraints_report"]["evidence_present"] is True
    assert bundle2["constraints_report"]["evidence_present"] is True
