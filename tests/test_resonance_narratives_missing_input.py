"""
Test: Resonance Narratives - Missing Input Discipline

Verify that when envelope includes missing_inputs, the narrative:
1. Surfaces them in constraints_report
2. Does not synthesize values for missing data
3. Degrades gracefully
"""

import json
from pathlib import Path

from abraxas.renderers.resonance_narratives import render_narrative_bundle


def test_missing_input_discipline_reports_missing():
    """Test that missing inputs are properly reported."""
    missing_inputs_path = Path("tests/fixtures/resonance_narratives/envelopes/missing_inputs.json")
    with open(missing_inputs_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    constraints = bundle["constraints_report"]

    # Should have missing_inputs field
    assert "missing_inputs" in constraints

    # Should be a list
    assert isinstance(constraints["missing_inputs"], list)

    # Should report at least some missing inputs for this minimal envelope
    assert len(constraints["missing_inputs"]) > 0


def test_missing_input_discipline_no_synthesis():
    """Test that renderer doesn't synthesize values for missing data."""
    missing_inputs_path = Path("tests/fixtures/resonance_narratives/envelopes/missing_inputs.json")
    with open(missing_inputs_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    # Check signal_summary for any synthesized values
    for item in bundle["signal_summary"]:
        pointer = item["pointer"]
        value = item["value"]

        # Verify pointer actually exists in envelope
        parts = pointer[1:].split("/")
        current = envelope
        for part in parts:
            assert part in current, \
                f"Pointer {pointer} references missing data - value may be synthesized"
            current = current[part]

        # The resolved value should match (accounting for aggregation)
        # We don't assert exact equality since some aggregation is allowed
        # (e.g., counting items), but the pointer must resolve


def test_missing_input_discipline_graceful_degradation():
    """Test that renderer degrades gracefully with minimal input."""
    minimal_envelope = {
        "oracle_signal": {
            "v2": {
                "mode": "SNAPSHOT"
            }
        }
    }

    # Should not crash
    bundle = render_narrative_bundle(minimal_envelope)

    # Should still have required fields
    assert "schema_version" in bundle
    assert "artifact_id" in bundle
    assert "headline" in bundle
    assert "signal_summary" in bundle
    assert "constraints_report" in bundle

    # Should report many missing inputs
    assert len(bundle["constraints_report"]["missing_inputs"]) > 0


def test_missing_input_discipline_empty_lists_handled():
    """Test that empty lists in envelope are handled correctly."""
    envelope_with_empties = {
        "oracle_signal": {
            "window": {
                "start_iso": "2025-12-29T00:00:00Z",
                "end_iso": "2025-12-30T00:00:00Z",
                "bucket": "day"
            },
            "scores_v1": {
                "slang": {
                    "top_vital": [],  # Empty list
                    "top_risk": []   # Empty list
                },
                "aalmanac": {
                    "top_patterns": []  # Empty list
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

    bundle = render_narrative_bundle(envelope_with_empties)

    # Should not crash and should not synthesize motifs
    assert len(bundle["motifs"]) == 0, \
        "Should not create motifs from empty lists"

    # Signal summary should note counts as 0, not fabricate data
    vital_items = [
        item for item in bundle["signal_summary"]
        if "vital" in item.get("label", "").lower()
    ]

    # If vital signals are mentioned, value should be 0 or absent
    for item in vital_items:
        if isinstance(item["value"], int):
            assert item["value"] == 0, "Empty list should report count as 0"


def test_missing_input_discipline_partial_data():
    """Test handling of partially complete envelope."""
    partial_envelope = {
        "oracle_signal": {
            "window": {
                "start_iso": "2025-12-29T00:00:00Z",
                "end_iso": "2025-12-30T00:00:00Z",
                "bucket": "day"
            },
            "scores_v1": {
                "slang": {
                    "top_vital": [{"term": "test", "SVS": 50.0}]
                    # Note: no top_risk, no aalmanac
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

    bundle = render_narrative_bundle(partial_envelope)

    # Should have window in signal_summary
    window_items = [
        item for item in bundle["signal_summary"]
        if "window" in item.get("label", "").lower()
    ]
    assert len(window_items) > 0, "Should include window data that is present"

    # Should have vital signals
    vital_items = [
        item for item in bundle["signal_summary"]
        if "vital" in item.get("label", "").lower()
    ]
    assert len(vital_items) > 0, "Should include vital data that is present"

    # Should have motifs from the one vital term
    assert len(bundle["motifs"]) > 0, "Should create motifs from available data"


def test_missing_input_discipline_not_computable():
    """Test that not_computable list is populated correctly."""
    missing_inputs_path = Path("tests/fixtures/resonance_narratives/envelopes/missing_inputs.json")
    with open(missing_inputs_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    constraints = bundle["constraints_report"]

    # Should have not_computable field
    assert "not_computable" in constraints
    assert isinstance(constraints["not_computable"], list)

    # For this minimal envelope, v2_scores should be not computable
    not_computable_str = " ".join(constraints["not_computable"])
    assert "v2_scores" in not_computable_str.lower(), \
        "Should report v2_scores as not computable when missing"
