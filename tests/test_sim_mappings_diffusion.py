"""Golden tests for SML DIFFUSION_SIR family mappings.

Tests deterministic parameter mapping for SIR/SEIR compartment models.
"""

import pytest

from abraxas.sim_mappings import (
    ModelFamily,
    ModelParam,
    PaperRef,
    map_params_to_knobs,
    map_paper_model,
)


@pytest.fixture
def diffusion_sir_params_full():
    """Full parameter set for DIFFUSION_SIR model."""
    return [
        ModelParam(name="beta", symbol="β", value=0.3, units="per day"),
        ModelParam(name="gamma", symbol="γ", value=0.1, units="per day"),
        ModelParam(name="k", value=10.0, description="Network degree"),
        ModelParam(name="delay", value=2.0, units="days"),
    ]


@pytest.fixture
def diffusion_sir_paper():
    """Sample paper reference for DIFFUSION_SIR."""
    return PaperRef(
        paper_id="TEST_SIR_001",
        title="Test SIR Model",
        url="https://test.example.com/sir",
        year=2024,
    )


def test_diffusion_sir_full_params(diffusion_sir_params_full):
    """Test mapping with all key parameters present."""
    knobs = map_params_to_knobs(ModelFamily.DIFFUSION_SIR, diffusion_sir_params_full)

    # Should have HIGH confidence (all 4 key params present)
    assert knobs.confidence == "HIGH"

    # MRI should reflect beta and k
    # beta=0.3 normalized to [0,1] = 0.3
    # k=10 normalized to [1,50] = (10-1)/(50-1) ≈ 0.18
    # mean ≈ 0.24
    assert 0.2 <= knobs.mri <= 0.3

    # IRI should reflect gamma
    # gamma=0.1 normalized to [0,1] = 0.1
    assert 0.08 <= knobs.iri <= 0.15

    # τ_latency should reflect delay
    # delay=2 normalized to [0,14] = 2/14 ≈ 0.14
    assert 0.1 <= knobs.tau_latency <= 0.2

    # Explanation should mention params
    assert "β" in knobs.explanation or "beta" in knobs.explanation
    assert "γ" in knobs.explanation or "gamma" in knobs.explanation


def test_diffusion_sir_partial_params():
    """Test mapping with partial parameters (MED confidence)."""
    params = [
        ModelParam(name="beta", symbol="β", value=0.5),
        ModelParam(name="gamma", symbol="γ", value=0.2),
        # Missing k and delay
    ]

    knobs = map_params_to_knobs(ModelFamily.DIFFUSION_SIR, params)

    # Should have MED confidence (2/4 = 50%)
    assert knobs.confidence == "MED"

    # MRI should reflect beta
    assert 0.4 <= knobs.mri <= 0.6

    # IRI should reflect gamma
    assert 0.15 <= knobs.iri <= 0.25


def test_diffusion_sir_minimal_params():
    """Test mapping with minimal parameters (LOW confidence)."""
    params = [
        ModelParam(name="beta", symbol="β", value=0.4),
        # Only 1/4 key params
    ]

    knobs = map_params_to_knobs(ModelFamily.DIFFUSION_SIR, params)

    # Should have LOW confidence (1/4 = 25%)
    assert knobs.confidence == "LOW"

    # MRI should reflect beta
    assert 0.3 <= knobs.mri <= 0.5


def test_diffusion_sir_paper_mapping(diffusion_sir_paper, diffusion_sir_params_full):
    """Test complete paper model mapping."""
    result = map_paper_model(
        diffusion_sir_paper,
        ModelFamily.DIFFUSION_SIR,
        diffusion_sir_params_full,
    )

    assert result.paper.paper_id == "TEST_SIR_001"
    assert result.family == ModelFamily.DIFFUSION_SIR
    assert len(result.params) == 4
    assert result.mapped.confidence == "HIGH"

    # Check component breakdown
    assert "MRI" in result.mapped_components
    assert "IRI" in result.mapped_components
    assert "τ" in result.mapped_components

    # β and k should be in MRI
    mri_components = result.mapped_components["MRI"]
    assert "β" in mri_components or "beta" in mri_components

    # γ should be in IRI
    iri_components = result.mapped_components["IRI"]
    assert "γ" in iri_components or "gamma" in iri_components

    # delay should be in τ
    tau_components = result.mapped_components["τ"]
    assert "delay" in tau_components


def test_diffusion_sir_high_transmission():
    """Test with high transmission rate (high MRI expected)."""
    params = [
        ModelParam(name="beta", value=0.8),  # High transmission
        ModelParam(name="gamma", value=0.1),  # Low recovery
        ModelParam(name="k", value=40.0),  # High degree
    ]

    knobs = map_params_to_knobs(ModelFamily.DIFFUSION_SIR, params)

    # MRI should be high (beta=0.8, k=40 → normalized ≈ 0.8)
    assert knobs.mri > 0.7


def test_diffusion_sir_high_recovery():
    """Test with high recovery rate (high IRI expected)."""
    params = [
        ModelParam(name="beta", value=0.2),  # Low transmission
        ModelParam(name="gamma", value=0.9),  # High recovery
    ]

    knobs = map_params_to_knobs(ModelFamily.DIFFUSION_SIR, params)

    # IRI should be high (gamma=0.9)
    assert knobs.iri > 0.8


def test_diffusion_sir_long_delay():
    """Test with long incubation delay (high τ_latency expected)."""
    params = [
        ModelParam(name="delay", value=10.0),  # Long delay (10 days)
    ]

    knobs = map_params_to_knobs(ModelFamily.DIFFUSION_SIR, params)

    # τ_latency should be high (10/14 ≈ 0.71)
    assert knobs.tau_latency > 0.6
