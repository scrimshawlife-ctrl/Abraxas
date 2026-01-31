"""
Test: Resonance Narratives - Diff Mode

Verify that render_narrative_bundle_with_diff correctly:
1. Detects changes between envelopes
2. Populates what_changed with pointer-based diffs
3. Maintains determinism in diff mode
"""

import json
from pathlib import Path

from abraxas.renderers.resonance_narratives import render_narrative_bundle_with_diff


def test_diff_mode_detects_compliance_change():
    """Test that diff mode detects compliance status changes."""
    baseline_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")
    updated_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline_updated.json")

    with open(baseline_path) as f:
        previous = json.load(f)

    with open(updated_path) as f:
        current = json.load(f)

    bundle = render_narrative_bundle_with_diff(
        current,
        previous_envelope=previous,
        artifact_id="DIFF-TEST-001"
    )

    # Should have what_changed populated
    assert "what_changed" in bundle
    assert len(bundle["what_changed"]) > 0

    # Should detect compliance change (GREEN → YELLOW)
    compliance_changes = [
        change for change in bundle["what_changed"]
        if "compliance" in change["pointer"]
    ]

    assert len(compliance_changes) > 0, "Should detect compliance status change"

    change = compliance_changes[0]
    assert change["before"] == "GREEN"
    assert change["after"] == "YELLOW"


def test_diff_mode_detects_mode_change():
    """Test that diff mode detects oracle mode changes."""
    baseline_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")
    updated_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline_updated.json")

    with open(baseline_path) as f:
        previous = json.load(f)

    with open(updated_path) as f:
        current = json.load(f)

    bundle = render_narrative_bundle_with_diff(
        current,
        previous_envelope=previous,
        artifact_id="DIFF-TEST-002"
    )

    # Should detect mode change (SNAPSHOT → ANALYST)
    mode_changes = [
        change for change in bundle["what_changed"]
        if "/mode" in change["pointer"]
    ]

    assert len(mode_changes) > 0, "Should detect mode change"

    change = mode_changes[0]
    assert change["before"] == "SNAPSHOT"
    assert change["after"] == "ANALYST"


def test_diff_mode_detects_signal_count_change():
    """Test that diff mode detects changes in signal counts."""
    baseline_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")
    updated_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline_updated.json")

    with open(baseline_path) as f:
        previous = json.load(f)

    with open(updated_path) as f:
        current = json.load(f)

    bundle = render_narrative_bundle_with_diff(
        current,
        previous_envelope=previous,
        artifact_id="DIFF-TEST-003"
    )

    # Should detect vital signal count change (3 → 4)
    vital_changes = [
        change for change in bundle["what_changed"]
        if "vital" in change["pointer"]
    ]

    assert len(vital_changes) > 0, "Should detect vital signal count change"

    change = vital_changes[0]
    assert change["before"] == 3
    assert change["after"] == 4
    assert "+1" in change["change_description"]


def test_diff_mode_no_previous_envelope():
    """Test that diff mode works without previous envelope."""
    baseline_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")

    with open(baseline_path) as f:
        current = json.load(f)

    bundle = render_narrative_bundle_with_diff(
        current,
        previous_envelope=None,
        artifact_id="DIFF-TEST-004"
    )

    # Should not have what_changed when no previous envelope
    assert "what_changed" not in bundle or len(bundle.get("what_changed", [])) == 0


def test_diff_mode_identical_envelopes():
    """Test that diff mode produces empty what_changed for identical envelopes."""
    baseline_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")

    with open(baseline_path) as f:
        envelope = json.load(f)

    # Use same envelope as both current and previous
    bundle = render_narrative_bundle_with_diff(
        envelope,
        previous_envelope=envelope,
        artifact_id="DIFF-TEST-005"
    )

    # Should have what_changed but it should be empty
    assert "what_changed" in bundle
    assert len(bundle["what_changed"]) == 0, \
        "Identical envelopes should produce no changes"


def test_diff_mode_change_descriptions():
    """Test that change descriptions are human-readable."""
    baseline_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")
    updated_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline_updated.json")

    with open(baseline_path) as f:
        previous = json.load(f)

    with open(updated_path) as f:
        current = json.load(f)

    bundle = render_narrative_bundle_with_diff(
        current,
        previous_envelope=previous,
        artifact_id="DIFF-TEST-006"
    )

    # All changes should have readable descriptions
    for change in bundle["what_changed"]:
        assert "change_description" in change
        assert len(change["change_description"]) > 0
        assert isinstance(change["change_description"], str)

        # Should contain → or similar change indicator
        description = change["change_description"]
        assert "→" in description or "changed" in description.lower(), \
            f"Change description should indicate change: {description}"


def test_diff_mode_pointer_integrity():
    """Test that all what_changed pointers exist in current envelope."""
    baseline_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")
    updated_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline_updated.json")

    with open(baseline_path) as f:
        previous = json.load(f)

    with open(updated_path) as f:
        current = json.load(f)

    bundle = render_narrative_bundle_with_diff(
        current,
        previous_envelope=previous,
        artifact_id="DIFF-TEST-007"
    )

    # Helper to check pointer existence
    def pointer_exists(envelope: dict, pointer: str) -> bool:
        if not pointer.startswith("/"):
            return False
        parts = pointer[1:].split("/")
        obj = envelope
        for part in parts:
            if not isinstance(obj, dict) or part not in obj:
                return False
            obj = obj[part]
        return True

    # All change pointers should exist in current envelope
    for change in bundle["what_changed"]:
        pointer = change["pointer"]
        assert pointer_exists(current, pointer), \
            f"Change pointer {pointer} doesn't exist in current envelope"


def test_diff_mode_determinism():
    """Test that diff mode is deterministic."""
    baseline_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline.json")
    updated_path = Path("tests/fixtures/resonance_narratives/envelopes/baseline_updated.json")

    with open(baseline_path) as f:
        previous = json.load(f)

    with open(updated_path) as f:
        current = json.load(f)

    bundle1 = render_narrative_bundle_with_diff(
        current,
        previous_envelope=previous,
        artifact_id="DIFF-TEST-008"
    )

    bundle2 = render_narrative_bundle_with_diff(
        current,
        previous_envelope=previous,
        artifact_id="DIFF-TEST-008"
    )

    # what_changed should be identical
    assert bundle1["what_changed"] == bundle2["what_changed"], \
        "Diff mode should be deterministic"
