"""
Test: Resonance Narratives - Evidence Gating

Verify that renderer removes dependent lines when evidence is missing,
and doesn't synthesize values for missing data.
"""

import json
from pathlib import Path

from abraxas.renderers.resonance_narratives import render_narrative_bundle


def test_evidence_gating_presence_detection():
    """Test that renderer correctly detects evidence presence."""
    # Envelope with evidence
    with_evidence_path = Path("tests/fixtures/resonance_narratives/envelopes/with_evidence.json")
    with open(with_evidence_path) as f:
        envelope_with = json.load(f)

    # Envelope without evidence
    baseline_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")
    with open(baseline_path) as f:
        envelope_without = json.load(f)

    bundle_with = render_narrative_bundle(envelope_with)
    bundle_without = render_narrative_bundle(envelope_without)

    assert bundle_with["constraints_report"]["evidence_present"] is True, \
        "Should detect evidence when present"

    assert bundle_without["constraints_report"]["evidence_present"] is False, \
        "Should detect no evidence when absent"


def test_evidence_gating_no_fabrication():
    """Test that renderer doesn't fabricate evidence when missing."""
    baseline_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")
    with open(baseline_path) as f:
        envelope = json.load(f)

    # Remove evidence if present
    if "evidence" in envelope.get("oracle_signal", {}):
        del envelope["oracle_signal"]["evidence"]

    bundle = render_narrative_bundle(envelope)

    # Should report evidence as not present
    assert bundle["constraints_report"]["evidence_present"] is False

    # Should not have evidence-dependent overlay notes
    evidence_overlays = [
        note for note in bundle.get("overlay_notes", [])
        if "evidence" in note.get("note", "").lower()
    ]

    assert len(evidence_overlays) == 0, \
        "Should not create evidence-related overlays when evidence is absent"


def test_evidence_gating_missing_data_removal():
    """Test that removing envelope fields removes dependent narrative lines."""
    baseline_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")
    with open(baseline_path) as f:
        envelope = json.load(f)

    # Render with full data
    bundle_full = render_narrative_bundle(envelope, artifact_id="FULL")

    # Remove top_vital from envelope
    envelope_stripped = json.loads(json.dumps(envelope))  # Deep copy
    if "top_vital" in envelope_stripped.get("oracle_signal", {}).get("scores_v1", {}).get("slang", {}):
        del envelope_stripped["oracle_signal"]["scores_v1"]["slang"]["top_vital"]

    bundle_stripped = render_narrative_bundle(envelope_stripped, artifact_id="STRIPPED")

    # Count vital-related items in signal_summary
    vital_items_full = [
        item for item in bundle_full["signal_summary"]
        if "vital" in item.get("label", "").lower()
    ]

    vital_items_stripped = [
        item for item in bundle_stripped["signal_summary"]
        if "vital" in item.get("label", "").lower()
    ]

    # Stripped should have fewer vital-related items
    assert len(vital_items_stripped) < len(vital_items_full), \
        "Removing data should remove dependent narrative lines"


def test_evidence_gating_motifs_from_missing_data():
    """Test that motifs aren't generated from missing slang data."""
    minimal_envelope = {
        "oracle_signal": {
            "window": {
                "start_iso": "2025-12-29T00:00:00Z",
                "end_iso": "2025-12-30T00:00:00Z",
                "bucket": "day"
            },
            "scores_v1": {
                "slang": {
                    "top_vital": [],  # Empty
                    "top_risk": []
                },
                "aalmanac": {
                    "top_patterns": []  # Empty
                }
            },
            "v2": {
                "mode": "SNAPSHOT",
                "compliance": {
                    "status": "GREEN"
                }
            }
        }
    }

    bundle = render_narrative_bundle(minimal_envelope)

    # Should have no motifs since source data is empty
    assert len(bundle["motifs"]) == 0, \
        "Should not generate motifs from empty data"


def test_evidence_gating_constraints_report_missing_inputs():
    """Test that missing inputs are reported in constraints."""
    missing_inputs_path = Path("tests/fixtures/resonance_narratives/envelopes/missing_inputs.json")
    with open(missing_inputs_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    constraints = bundle["constraints_report"]

    # Should report missing inputs
    assert len(constraints["missing_inputs"]) > 0, \
        "Should report missing inputs in constraints_report"

    # Should specifically note window is missing
    assert "window/start_iso" in constraints["missing_inputs"], \
        "Should report missing window/start_iso"


def test_evidence_gating_no_causal_claims_without_evidence():
    """Test that renderer doesn't make causal claims without evidence."""
    baseline_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")
    with open(baseline_path) as f:
        envelope = json.load(f)

    # Remove evidence
    if "evidence" in envelope.get("oracle_signal", {}):
        del envelope["oracle_signal"]["evidence"]

    bundle = render_narrative_bundle(envelope)

    # Collect all narrative text
    all_text = []
    all_text.append(bundle["headline"])

    for item in bundle["signal_summary"]:
        if isinstance(item.get("value"), str):
            all_text.append(item["value"])

    for motif in bundle["motifs"]:
        all_text.append(motif["motif"])

    combined_text = " ".join(all_text).lower()

    # Should not contain strong causal language without evidence
    forbidden_phrases = ["because", "caused by", "therefore", "as a result"]

    for phrase in forbidden_phrases:
        assert phrase not in combined_text, \
            f"Found forbidden causal phrase '{phrase}' without evidence support"
