"""Golden tests for SML GAME_THEORETIC family mappings."""

import pytest

from abraxas.sim_mappings import (
    ModelFamily,
    ModelParam,
    map_params_to_knobs,
)


@pytest.fixture
def game_theoretic_params_full():
    """Full parameter set for GAME_THEORETIC model."""
    return [
        ModelParam(name="effort", value=5.0, description="Propagandist effort"),
        ModelParam(name="sanction_prob", symbol="p_C", value=0.3, description="Sanction probability"),
        ModelParam(name="sanction_penalty", value=10.0, description="Sanction cost"),
        ModelParam(name="discount", symbol="δ", value=0.9, description="Discount factor"),
    ]


def test_game_theoretic_full_params(game_theoretic_params_full):
    """Test mapping with all key parameters."""
    knobs = map_params_to_knobs(ModelFamily.GAME_THEORETIC, game_theoretic_params_full)

    assert knobs.confidence == "HIGH"

    # MRI from effort=5.0
    # normalized to [0,10] = 5/10 = 0.5
    assert 0.45 <= knobs.mri <= 0.55

    # IRI from sanction_prob=0.3, sanction_penalty=10.0
    # sanction_prob normalized = 0.3
    # (Note: sanction_penalty not in default ranges, uses [0,1] default = clamped to 1.0)
    # mean ≈ 0.65
    assert 0.5 <= knobs.iri <= 0.7


def test_game_theoretic_high_effort():
    """Test with high propagandist effort (high MRI)."""
    params = [
        ModelParam(name="effort", value=9.0),  # High effort
    ]

    knobs = map_params_to_knobs(ModelFamily.GAME_THEORETIC, params)

    # High effort = high MRI
    # 9/10 = 0.9
    assert knobs.mri > 0.85


def test_game_theoretic_high_sanctions():
    """Test with high sanction probability (high IRI)."""
    params = [
        ModelParam(name="sanction_prob", value=0.8),  # High sanctions
    ]

    knobs = map_params_to_knobs(ModelFamily.GAME_THEORETIC, params)

    # High sanctions = high IRI
    assert knobs.iri > 0.75


def test_game_theoretic_low_discount():
    """Test with low discount factor (short horizon, low τ_memory)."""
    params = [
        ModelParam(name="discount", value=0.2),  # Short-sighted
    ]

    knobs = map_params_to_knobs(ModelFamily.GAME_THEORETIC, params)

    # Low discount (inverted) = low τ_memory
    # 1 - 0.2 = 0.8
    assert knobs.tau_memory > 0.75
