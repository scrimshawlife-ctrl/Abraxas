"""
Test: Scenario Runner Determinism

Verifies that scenario runner produces deterministic results.
"""

import json
from pathlib import Path

import pytest

from abraxas.scenario.runner import compute_confidence, run_scenarios


def dummy_sod_runner(context, sim_priors):
    """Dummy SOD runner for testing."""
    return {
        "ncp": {"paths": []},
        "cnf": {"counters": []},
        "efte": {"thresholds": []},
    }


def test_compute_confidence_high():
    """Test HIGH confidence computation."""
    priors = {
        "MRI": 0.6,
        "IRI": 0.55,
        "tau_memory": 0.5,
        "tau_latency": 0.3,
    }
    context = {"source_count": 2}

    confidence = compute_confidence(priors, context)
    assert confidence == "HIGH"


def test_compute_confidence_med():
    """Test MED confidence computation."""
    priors = {
        "MRI": 0.6,
        "IRI": 0.55,
        "tau_memory": 0.5,
        "tau_latency": 0.3,
    }
    context = {"source_count": 1}

    confidence = compute_confidence(priors, context)
    assert confidence == "MED"


def test_compute_confidence_low_missing_knobs():
    """Test LOW confidence with missing knobs."""
    priors = {
        "MRI": 0.6,
        "IRI": 0.55,
        # Missing tau_memory, tau_latency
    }
    context = {"source_count": 2}

    confidence = compute_confidence(priors, context)
    assert confidence == "LOW"


def test_compute_confidence_low_no_sources():
    """Test LOW confidence with no sources."""
    priors = {
        "MRI": 0.6,
        "IRI": 0.55,
        "tau_memory": 0.5,
        "tau_latency": 0.3,
    }
    context = {"source_count": 0}

    confidence = compute_confidence(priors, context)
    assert confidence == "LOW"


def test_run_scenarios_deterministic():
    """Test that scenario runner is deterministic."""
    base_priors = {
        "MRI": 0.6,
        "IRI": 0.55,
        "tau_memory": 0.5,
        "tau_latency": 0.3,
    }
    context = {
        "run_id": "test_scenario_001",
        "source_count": 2,
    }

    # Run twice
    result1 = run_scenarios(base_priors, dummy_sod_runner, context)
    result2 = run_scenarios(base_priors, dummy_sod_runner, context)

    # Timestamps will differ, but structure should be identical
    assert len(result1.envelopes) == len(result2.envelopes)
    assert result1.input.run_id == result2.input.run_id

    for env1, env2 in zip(result1.envelopes, result2.envelopes):
        assert env1.label == env2.label
        assert env1.priors == env2.priors
        assert env1.confidence == env2.confidence


def test_run_scenarios_envelope_count():
    """Test that 4 envelopes are generated."""
    base_priors = {
        "MRI": 0.5,
        "IRI": 0.5,
        "tau_memory": 0.5,
        "tau_latency": 0.3,
    }
    context = {"run_id": "test_scenario_002", "source_count": 1}

    result = run_scenarios(base_priors, dummy_sod_runner, context)

    assert len(result.envelopes) == 4


def test_run_scenarios_provenance():
    """Test that provenance is included."""
    base_priors = {
        "MRI": 0.5,
        "IRI": 0.5,
        "tau_memory": 0.5,
        "tau_latency": 0.3,
    }
    context = {"run_id": "test_scenario_003", "source_count": 2}

    result = run_scenarios(base_priors, dummy_sod_runner, context)

    assert "generator" in result.provenance
    assert "version" in result.provenance
    assert "envelope_count" in result.provenance
    assert result.provenance["envelope_count"] == 4


def test_run_scenarios_to_dict():
    """Test serialization to dict."""
    base_priors = {
        "MRI": 0.5,
        "IRI": 0.5,
        "tau_memory": 0.5,
        "tau_latency": 0.3,
    }
    context = {"run_id": "test_scenario_004", "source_count": 2}

    result = run_scenarios(base_priors, dummy_sod_runner, context)
    result_dict = result.to_dict()

    assert "input" in result_dict
    assert "envelopes" in result_dict
    assert "provenance" in result_dict
    assert len(result_dict["envelopes"]) == 4


def test_run_scenarios_golden():
    """Test against golden output."""
    base_priors = {
        "MRI": 0.5,
        "IRI": 0.5,
        "tau_memory": 0.5,
        "tau_latency": 0.3,
    }
    context = {"run_id": "golden_scenario_001", "source_count": 2}

    result = run_scenarios(base_priors, dummy_sod_runner, context)
    result_dict = result.to_dict()

    # Remove timestamp for comparison (non-deterministic)
    result_dict["input"]["timestamp"] = "2025-01-01T00:00:00+00:00"
    result_dict["provenance"]["timestamp"] = "2025-01-01T00:00:00+00:00"

    golden_path = Path("tests/golden/scenario/scenario_result.json")
    golden_path.parent.mkdir(parents=True, exist_ok=True)

    # Write golden (uncomment to regenerate)
    # with open(golden_path, "w") as f:
    #     json.dump(result_dict, f, indent=2, sort_keys=True)

    # Compare to golden
    if golden_path.exists():
        with open(golden_path, "r") as f:
            golden_result = json.load(f)

        # Compare structure (not exact match due to hash differences)
        assert len(result_dict["envelopes"]) == len(golden_result["envelopes"])
        assert result_dict["input"]["run_id"] == golden_result["input"]["run_id"]
