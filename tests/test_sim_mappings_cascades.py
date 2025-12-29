"""Golden tests for SML NETWORK_CASCADES family mappings."""

import pytest

from abraxas.sim_mappings import (
    ModelFamily,
    ModelParam,
    map_params_to_knobs,
)


@pytest.fixture
def network_cascades_params_full():
    """Full parameter set for NETWORK_CASCADES model."""
    return [
        ModelParam(name="p", value=0.5, description="Activation probability"),
        ModelParam(name="threshold", value=0.3, description="Adoption threshold"),
        ModelParam(name="deactivation_rate", value=0.2, description="Recovery rate"),
        ModelParam(name="delay", value=1.0, units="hours"),
    ]


def test_network_cascades_full_params(network_cascades_params_full):
    """Test mapping with all key parameters."""
    knobs = map_params_to_knobs(ModelFamily.NETWORK_CASCADES, network_cascades_params_full)

    assert knobs.confidence == "HIGH"

    # MRI from p=0.5, threshold=0.3 (inverted)
    # p normalized = 0.5
    # threshold inverted = 1 - 0.3 = 0.7
    # mean ≈ 0.6
    assert 0.55 <= knobs.mri <= 0.65

    # IRI from deactivation_rate=0.2
    assert 0.15 <= knobs.iri <= 0.25


def test_network_cascades_low_threshold():
    """Test with low threshold (easier activation, high MRI)."""
    params = [
        ModelParam(name="threshold", value=0.1),  # Low threshold
    ]

    knobs = map_params_to_knobs(ModelFamily.NETWORK_CASCADES, params)

    # Low threshold (inverted) = high MRI
    # 1 - 0.1 = 0.9
    assert knobs.mri > 0.85


def test_network_cascades_high_activation_prob():
    """Test with high activation probability."""
    params = [
        ModelParam(name="p", value=0.9),  # High activation
    ]

    knobs = map_params_to_knobs(ModelFamily.NETWORK_CASCADES, params)

    # High p = high MRI
    assert knobs.mri > 0.85


def test_network_cascades_high_deactivation():
    """Test with high deactivation rate (high IRI)."""
    params = [
        ModelParam(name="deactivation_rate", value=0.8),  # Fast recovery
    ]

    knobs = map_params_to_knobs(ModelFamily.NETWORK_CASCADES, params)

    # High deactivation = high IRI
    assert knobs.iri > 0.75
