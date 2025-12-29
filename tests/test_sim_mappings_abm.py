"""Golden tests for SML ABM_MISINFO family mappings."""

import pytest

from abraxas.sim_mappings import (
    ModelFamily,
    ModelParam,
    map_params_to_knobs,
)


@pytest.fixture
def abm_misinfo_params_full():
    """Full parameter set for ABM_MISINFO model."""
    return [
        ModelParam(name="share_prob", value=0.4, description="Sharing probability"),
        ModelParam(name="bot_density", value=0.1, description="Bot fraction"),
        ModelParam(name="correction_eff", value=0.6, description="Correction effectiveness"),
        ModelParam(name="content_lifespan", value=72.0, units="hours"),
    ]


def test_abm_misinfo_full_params(abm_misinfo_params_full):
    """Test mapping with all key parameters."""
    knobs = map_params_to_knobs(ModelFamily.ABM_MISINFO, abm_misinfo_params_full)

    assert knobs.confidence == "HIGH"

    # MRI from share_prob=0.4, bot_density=0.1
    # share_prob normalized = 0.4
    # bot_density normalized to [0,0.5] = 0.1/0.5 = 0.2
    # mean ≈ 0.3
    assert 0.25 <= knobs.mri <= 0.35

    # IRI from correction_eff=0.6
    assert 0.5 <= knobs.iri <= 0.7

    # τ_memory from content_lifespan=72h
    # normalized to [0,168] = 72/168 ≈ 0.43
    assert 0.35 <= knobs.tau_memory <= 0.5


def test_abm_misinfo_high_bot_density():
    """Test with high bot density (high MRI)."""
    params = [
        ModelParam(name="bot_density", value=0.4),  # High bots
        ModelParam(name="share_prob", value=0.7),  # High sharing
    ]

    knobs = map_params_to_knobs(ModelFamily.ABM_MISINFO, params)

    # High bots + sharing = high MRI
    # bot_density: 0.4/0.5 = 0.8
    # share_prob: 0.7
    # mean = 0.75
    assert knobs.mri > 0.7


def test_abm_misinfo_high_correction():
    """Test with high correction effectiveness (high IRI)."""
    params = [
        ModelParam(name="correction_eff", value=0.9),  # Effective corrections
    ]

    knobs = map_params_to_knobs(ModelFamily.ABM_MISINFO, params)

    # High correction = high IRI
    assert knobs.iri > 0.85


def test_abm_misinfo_long_lifespan():
    """Test with long content lifespan (high τ_memory)."""
    params = [
        ModelParam(name="content_lifespan", value=150.0),  # ~6 days
    ]

    knobs = map_params_to_knobs(ModelFamily.ABM_MISINFO, params)

    # Long lifespan = high memory
    # 150/168 ≈ 0.89
    assert knobs.tau_memory > 0.85
