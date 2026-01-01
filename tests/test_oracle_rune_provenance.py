"""Test oracle rune provenance integration."""
from __future__ import annotations
import pytest
from abx.core.pipeline import run_oracle


def test_oracle_with_rune_provenance():
    """Test that oracle output contains ABX-Runes provenance."""
    # Deterministic input
    input_obj = {"intent": "test_oracle", "v": 1}

    # Run oracle with default state (all dims = 0.5)
    output = run_oracle(input_obj)

    # Assert provenance exists
    assert "abx_runes" in output, "Output must contain 'abx_runes' key"

    runes = output["abx_runes"]

    # Assert required fields
    assert "used" in runes
    assert "manifest_sha256" in runes
    assert "gate_state" in runes

    # Assert rune list includes ϟ₄, ϟ₅, ϟ₆
    used = runes["used"]
    assert "ϟ₄" in used, "SDS rune must be used"
    assert "ϟ₅" in used, "IPL rune must be used"
    assert "ϟ₆" in used, "ADD rune must be used"

    # Assert gate_state is valid
    assert runes["gate_state"] in ["CLOSED", "LIMINAL", "OPEN"]

    # Assert manifest SHA256 is stable across runs (deterministic)
    sha256_1 = runes["manifest_sha256"]
    output_2 = run_oracle(input_obj)
    sha256_2 = output_2["abx_runes"]["manifest_sha256"]
    assert sha256_1 == sha256_2, "Manifest SHA256 must be stable across runs"


def test_oracle_gate_states():
    """Test that oracle respects SDS gate states."""
    input_obj = {"intent": "gate_test", "v": 1}

    # Test CLOSED gate (low openness/receptivity)
    state_closed = {
        "arousal": 0.8,
        "coherence": 0.2,
        "openness": 0.1,
        "receptivity": 0.1,
        "stability": 0.5,
    }
    output_closed = run_oracle(input_obj, state_vector=state_closed)
    assert output_closed["abx_runes"]["gate_state"] == "CLOSED"
    assert output_closed["depth"] == "grounding"

    # Test OPEN gate (high openness/receptivity)
    state_open = {
        "arousal": 0.2,
        "coherence": 0.8,
        "openness": 0.9,
        "receptivity": 0.9,
        "stability": 0.8,
    }
    output_open = run_oracle(input_obj, state_vector=state_open)
    assert output_open["abx_runes"]["gate_state"] == "OPEN"
    assert output_open["depth"] in ["shallow", "deep"]


def test_oracle_ipl_scheduling():
    """Test that IPL schedules windows only when gate is OPEN."""
    input_obj = {"intent": "ipl_test", "v": 1}

    # CLOSED gate - no IPL windows
    state_closed = {"openness": 0.1, "receptivity": 0.1}
    output_closed = run_oracle(input_obj, state_vector=state_closed)
    ipl = output_closed["abx_runes"]["ipl"]
    assert ipl["total_windows"] == 0
    assert ipl["lock_status"] == "inactive"

    # OPEN gate - IPL can schedule windows (if phase_series provided)
    state_open = {"openness": 0.9, "receptivity": 0.9}
    output_open = run_oracle(input_obj, state_vector=state_open)
    ipl_open = output_open["abx_runes"]["ipl"]
    # Without phase_series, still inactive but for different reason
    assert ipl_open["total_windows"] == 0


def test_oracle_drift_detection():
    """Test that ADD detects anchor drift."""
    input_obj = {"intent": "drift_test", "v": 1}
    anchor = "oracle stability"

    # No history - no drift
    output_1 = run_oracle(input_obj, anchor=anchor, outputs_history=[])
    drift_1 = output_1["abx_runes"]["drift"]
    assert drift_1["drift_magnitude"] == 0.0
    assert drift_1["integrity_score"] == 1.0
    assert drift_1["auto_recenter"] is False

    # History with similar outputs - low drift
    similar_history = [
        "oracle stability output 1",
        "oracle stability output 2",
        "oracle stability output 3",
    ]
    output_2 = run_oracle(input_obj, anchor=anchor, outputs_history=similar_history)
    drift_2 = output_2["abx_runes"]["drift"]
    assert drift_2["drift_magnitude"] < 0.5

    # History with completely different outputs - high drift
    different_history = [
        "completely unrelated text about random topics",
        "nothing to do with the original anchor at all",
        "divergent content that has drifted away",
    ] * 7  # Repeat to exceed drift threshold
    output_3 = run_oracle(input_obj, anchor=anchor, outputs_history=different_history)
    drift_3 = output_3["abx_runes"]["drift"]
    assert drift_3["drift_magnitude"] > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
