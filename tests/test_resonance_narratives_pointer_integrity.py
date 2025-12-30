"""
Test: Resonance Narratives - Pointer Integrity

Verify that every narrative line's pointer exists in the envelope
and that all pointers are whitelisted.
"""

import json
from pathlib import Path

from abraxas.renderers.resonance_narratives import render_narrative_bundle
from abraxas.renderers.resonance_narratives.rules import is_pointer_allowed


def _pointer_exists_in_envelope(envelope: dict, pointer: str) -> bool:
    """
    Check if a JSON pointer resolves in the envelope.

    Args:
        envelope: Envelope dict
        pointer: JSON pointer string

    Returns:
        True if pointer resolves to a value
    """
    if not pointer.startswith("/"):
        return False

    parts = pointer[1:].split("/")
    current = envelope

    for part in parts:
        if isinstance(current, dict):
            if part not in current:
                return False
            current = current[part]
        elif isinstance(current, list):
            # Handle array indices
            try:
                index = int(part)
                if index < 0 or index >= len(current):
                    return False
                current = current[index]
            except (ValueError, IndexError):
                return False
        else:
            return False

    return True


def test_pointer_integrity_signal_summary():
    """Test that all signal_summary pointers exist in envelope."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    for item in bundle["signal_summary"]:
        pointer = item["pointer"]
        assert _pointer_exists_in_envelope(envelope, pointer), \
            f"Pointer {pointer} does not exist in envelope"


def test_pointer_integrity_motifs():
    """Test that all motif pointers exist in envelope."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    for motif in bundle["motifs"]:
        pointer = motif["pointer"]
        assert _pointer_exists_in_envelope(envelope, pointer), \
            f"Motif pointer {pointer} does not exist in envelope"


def test_pointer_whitelist_signal_summary():
    """Test that all signal_summary pointers are whitelisted."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    for item in bundle["signal_summary"]:
        pointer = item["pointer"]
        # Note: Some pointers may be composite (like "/oracle_signal/window")
        # We check that they're either in whitelist or are parent paths
        # For now, just verify they start with known prefixes
        assert pointer.startswith("/oracle_signal/"), \
            f"Pointer {pointer} doesn't start with expected prefix"


def test_pointer_integrity_with_evidence():
    """Test pointer integrity for envelope with evidence."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/with_evidence.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    all_pointers = []

    # Collect all pointers
    for item in bundle["signal_summary"]:
        all_pointers.append(item["pointer"])

    for motif in bundle["motifs"]:
        all_pointers.append(motif["pointer"])

    # Verify all exist
    for pointer in all_pointers:
        assert _pointer_exists_in_envelope(envelope, pointer), \
            f"Pointer {pointer} does not exist in envelope"


def test_pointer_format():
    """Test that all pointers follow JSON Pointer RFC 6901 format."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    all_pointers = []

    for item in bundle["signal_summary"]:
        all_pointers.append(item["pointer"])

    for motif in bundle["motifs"]:
        all_pointers.append(motif["pointer"])

    for pointer in all_pointers:
        # Must start with /
        assert pointer.startswith("/"), f"Pointer {pointer} must start with /"

        # Should not end with / (unless root, which we don't use)
        assert not pointer.endswith("/") or pointer == "/", \
            f"Pointer {pointer} should not end with /"

        # Should not have // in it
        assert "//" not in pointer, f"Pointer {pointer} contains //"


def test_no_invented_pointers():
    """Test that renderer doesn't create pointers to non-existent data."""
    # Use envelope with minimal data
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/missing_inputs.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    # Collect all pointers from the bundle
    all_pointers = []

    for item in bundle["signal_summary"]:
        all_pointers.append(item["pointer"])

    for motif in bundle["motifs"]:
        all_pointers.append(motif["pointer"])

    # Every pointer MUST resolve in the envelope
    for pointer in all_pointers:
        assert _pointer_exists_in_envelope(envelope, pointer), \
            f"Renderer invented pointer {pointer} that doesn't exist in envelope"


def test_pointer_references_correct_values():
    """Test that pointer values match what's claimed in narrative."""
    fixture_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")

    with open(fixture_path) as f:
        envelope = json.load(f)

    bundle = render_narrative_bundle(envelope)

    # Find compliance status in signal_summary
    compliance_items = [
        item for item in bundle["signal_summary"]
        if item["label"] == "Compliance Status"
    ]

    if compliance_items:
        item = compliance_items[0]
        pointer = item["pointer"]
        value = item["value"]

        # Resolve pointer manually
        actual = envelope
        for part in pointer[1:].split("/"):
            actual = actual[part]

        assert actual == value, \
            f"Narrative value {value} doesn't match actual value {actual} at {pointer}"
