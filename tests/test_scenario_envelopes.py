"""
Test: Scenario Envelope Generation

Verifies deterministic envelope generation with golden outputs.
"""

import json
from pathlib import Path

import pytest

from abraxas.scenario.envelopes import build_envelopes


def test_build_envelopes_deterministic():
    """Test that envelope generation is deterministic."""
    base_priors = {
        "MRI": 0.5,
        "IRI": 0.5,
        "tau_memory": 0.5,
        "tau_latency": 0.3,
    }

    # Run twice
    envelopes1 = build_envelopes(base_priors)
    envelopes2 = build_envelopes(base_priors)

    # Should be identical
    assert envelopes1 == envelopes2


def test_build_envelopes_count():
    """Test that 4 envelopes are generated."""
    base_priors = {"MRI": 0.5, "IRI": 0.5, "tau_memory": 0.5, "tau_latency": 0.3}
    envelopes = build_envelopes(base_priors)

    assert len(envelopes) == 4


def test_build_envelopes_labels():
    """Test that envelope labels are correct."""
    base_priors = {"MRI": 0.5, "IRI": 0.5, "tau_memory": 0.5, "tau_latency": 0.3}
    envelopes = build_envelopes(base_priors)

    labels = [env["label"] for env in envelopes]
    expected_labels = ["baseline", "push_spread_up", "damping_up", "memory_long"]

    assert labels == expected_labels


def test_build_envelopes_priors_modulation():
    """Test that priors are correctly modulated."""
    base_priors = {"MRI": 0.5, "IRI": 0.5, "tau_memory": 0.5, "tau_latency": 0.3}
    envelopes = build_envelopes(base_priors)

    # Baseline: no change
    baseline = next(env for env in envelopes if env["label"] == "baseline")
    assert baseline["priors"]["MRI"] == 0.5
    assert baseline["priors"]["IRI"] == 0.5

    # Push spread up: MRI +0.15
    push_spread = next(env for env in envelopes if env["label"] == "push_spread_up")
    assert push_spread["priors"]["MRI"] == 0.65
    assert push_spread["priors"]["IRI"] == 0.5  # Unchanged

    # Damping up: IRI +0.15
    damping = next(env for env in envelopes if env["label"] == "damping_up")
    assert damping["priors"]["MRI"] == 0.5  # Unchanged
    assert damping["priors"]["IRI"] == 0.65

    # Memory long: tau_memory +0.20, tau_latency +0.10
    memory_long = next(env for env in envelopes if env["label"] == "memory_long")
    assert memory_long["priors"]["tau_memory"] == 0.7
    assert memory_long["priors"]["tau_latency"] == 0.4


def test_build_envelopes_clamping():
    """Test that priors are clamped to [0,1]."""
    base_priors = {
        "MRI": 0.95,  # Will push to 1.1 without clamping
        "IRI": 0.95,
        "tau_memory": 0.95,
        "tau_latency": 0.95,
    }
    envelopes = build_envelopes(base_priors)

    # Push spread up: MRI should be clamped to 1.0
    push_spread = next(env for env in envelopes if env["label"] == "push_spread_up")
    assert push_spread["priors"]["MRI"] == 1.0

    # Damping up: IRI should be clamped to 1.0
    damping = next(env for env in envelopes if env["label"] == "damping_up")
    assert damping["priors"]["IRI"] == 1.0


def test_build_envelopes_falsifiers_present():
    """Test that all envelopes have falsifiers."""
    base_priors = {"MRI": 0.5, "IRI": 0.5, "tau_memory": 0.5, "tau_latency": 0.3}
    envelopes = build_envelopes(base_priors)

    for env in envelopes:
        assert "falsifiers" in env
        assert isinstance(env["falsifiers"], list)
        assert len(env["falsifiers"]) > 0


def test_build_envelopes_golden():
    """Test against golden output."""
    base_priors = {"MRI": 0.5, "IRI": 0.5, "tau_memory": 0.5, "tau_latency": 0.3}
    envelopes = build_envelopes(base_priors)

    golden_path = Path("tests/golden/scenario/envelopes_baseline.json")
    golden_path.parent.mkdir(parents=True, exist_ok=True)

    # Write golden (uncomment to regenerate)
    # with open(golden_path, "w") as f:
    #     json.dump(envelopes, f, indent=2, sort_keys=True)

    # Compare to golden
    if golden_path.exists():
        with open(golden_path, "r") as f:
            golden_envelopes = json.load(f)

        assert envelopes == golden_envelopes
