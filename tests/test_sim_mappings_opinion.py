"""Golden tests for SML OPINION_DYNAMICS family mappings."""

import pytest

from abraxas.sim_mappings import (
    ModelFamily,
    ModelParam,
    map_params_to_knobs,
)


@pytest.fixture
def opinion_dynamics_params_full():
    """Full parameter set for OPINION_DYNAMICS model."""
    return [
        ModelParam(name="w", value=0.6, description="Influence weight"),
        ModelParam(name="epsilon", symbol="ε", value=0.2, description="Bounded confidence"),
        ModelParam(name="alpha", symbol="α", value=0.3, description="Inertia"),
        ModelParam(name="update_schedule", value=1.0, units="per step"),
    ]


def test_opinion_dynamics_full_params(opinion_dynamics_params_full):
    """Test mapping with all key parameters."""
    knobs = map_params_to_knobs(ModelFamily.OPINION_DYNAMICS, opinion_dynamics_params_full)

    assert knobs.confidence == "HIGH"

    # MRI from w=0.6
    assert 0.5 <= knobs.mri <= 0.7

    # IRI from epsilon=0.2 (inverted: lower ε = higher selectivity = higher IRI)
    # epsilon is inverted, so 0.2 → 1-0.2 = 0.8
    assert knobs.iri > 0.7


def test_opinion_dynamics_high_influence():
    """Test with high influence weight."""
    params = [
        ModelParam(name="w", value=0.9),  # Strong influence
    ]

    knobs = map_params_to_knobs(ModelFamily.OPINION_DYNAMICS, params)

    # High influence = high MRI
    assert knobs.mri > 0.8


def test_opinion_dynamics_low_bounded_confidence():
    """Test with low bounded confidence (high IRI)."""
    params = [
        ModelParam(name="epsilon", value=0.1),  # Low ε = selective
    ]

    knobs = map_params_to_knobs(ModelFamily.OPINION_DYNAMICS, params)

    # Low ε (inverted) = high IRI
    assert knobs.iri > 0.85


def test_opinion_dynamics_high_inertia():
    """Test with high inertia (low update rate, high τ_memory)."""
    params = [
        ModelParam(name="alpha", value=0.9),  # High inertia
    ]

    knobs = map_params_to_knobs(ModelFamily.OPINION_DYNAMICS, params)

    # High inertia = high τ_memory
    assert knobs.tau_memory > 0.8
