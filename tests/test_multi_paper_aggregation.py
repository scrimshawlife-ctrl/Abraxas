"""Tests for multi-paper aggregation in SOD adapter."""

import pytest

from abraxas.sim_mappings import (
    ModelFamily,
    ModelParam,
    PaperRef,
    map_paper_model,
)
from abraxas.sod.sim_adapter import aggregate_multi_paper_priors


@pytest.fixture
def paper1():
    """First test paper."""
    return PaperRef(
        paper_id="TEST001",
        title="Test Paper 1",
        url="https://example.com/test001",
        year=2024,
    )


@pytest.fixture
def paper2():
    """Second test paper."""
    return PaperRef(
        paper_id="TEST002",
        title="Test Paper 2",
        url="https://example.com/test002",
        year=2024,
    )


@pytest.fixture
def paper3():
    """Third test paper."""
    return PaperRef(
        paper_id="TEST003",
        title="Test Paper 3",
        url="https://example.com/test003",
        year=2024,
    )


def test_aggregate_two_papers_equal_confidence(paper1, paper2):
    """Test aggregating two papers with equal confidence."""
    # Both papers with HIGH confidence, similar parameters
    params1 = [
        ModelParam(name="beta", value=0.3),
        ModelParam(name="gamma", value=0.1),
        ModelParam(name="k", value=10.0),
    ]

    params2 = [
        ModelParam(name="beta", value=0.5),
        ModelParam(name="gamma", value=0.2),
        ModelParam(name="k", value=15.0),
    ]

    mapping1 = map_paper_model(paper1, ModelFamily.DIFFUSION_SIR, params1)
    mapping2 = map_paper_model(paper2, ModelFamily.DIFFUSION_SIR, params2)

    # Aggregate
    aggregated = aggregate_multi_paper_priors([mapping1, mapping2])

    # Check provenance
    assert aggregated["total_papers"] == 2
    assert "TEST001" in aggregated["sources"]
    assert "TEST002" in aggregated["sources"]
    assert len(aggregated["weights"]) == 2

    # Check aggregated knobs (should be somewhere between the two)
    assert "aggregated_knobs" in aggregated
    assert 0 <= aggregated["aggregated_knobs"]["mri"] <= 1
    assert 0 <= aggregated["aggregated_knobs"]["iri"] <= 1

    # Check SOD priors are present
    assert "cascade_branching_prob" in aggregated
    assert "cascade_damping_factor" in aggregated
    assert "cascade_onset_lag_hours" in aggregated
    assert "cascade_tail_length_hours" in aggregated


def test_aggregate_mixed_confidence(paper1, paper2, paper3):
    """Test aggregating papers with different confidence levels."""
    # High confidence paper
    params_high = [
        ModelParam(name="beta", value=0.3),
        ModelParam(name="gamma", value=0.1),
        ModelParam(name="k", value=10.0),
    ]

    # Medium confidence paper (fewer params)
    params_med = [
        ModelParam(name="beta", value=0.5),
        ModelParam(name="gamma", value=0.2),
    ]

    # Low confidence paper (minimal params)
    params_low = [
        ModelParam(name="beta", value=0.7),
    ]

    mapping_high = map_paper_model(paper1, ModelFamily.DIFFUSION_SIR, params_high)
    mapping_med = map_paper_model(paper2, ModelFamily.DIFFUSION_SIR, params_med)
    mapping_low = map_paper_model(paper3, ModelFamily.DIFFUSION_SIR, params_low)

    # Aggregate
    aggregated = aggregate_multi_paper_priors([mapping_high, mapping_med, mapping_low])

    # Check confidence weighting
    assert aggregated["total_papers"] == 3
    assert len(aggregated["weights"]) == 3

    # Aggregate confidence should be HIGH (max of inputs)
    assert aggregated["aggregate_confidence"] == "HIGH"

    # Higher confidence papers should have more influence
    # (This is implicit in the weighted averaging)
    assert aggregated["weights"][0] >= aggregated["weights"][1]  # HIGH >= MED
    assert aggregated["weights"][1] >= aggregated["weights"][2]  # MED >= LOW


def test_aggregate_empty_list_raises():
    """Test that aggregating empty list raises ValueError."""
    with pytest.raises(ValueError, match="Cannot aggregate empty list"):
        aggregate_multi_paper_priors([])


def test_aggregate_single_paper(paper1):
    """Test aggregating single paper (edge case)."""
    params = [
        ModelParam(name="beta", value=0.3),
        ModelParam(name="gamma", value=0.1),
    ]

    mapping = map_paper_model(paper1, ModelFamily.DIFFUSION_SIR, params)

    aggregated = aggregate_multi_paper_priors([mapping])

    assert aggregated["total_papers"] == 1
    assert aggregated["sources"] == ["TEST001"]

    # Aggregated knobs should match original (no averaging needed)
    assert aggregated["aggregated_knobs"]["mri"] == mapping.mapped.mri
    assert aggregated["aggregated_knobs"]["iri"] == mapping.mapped.iri


def test_aggregate_different_families(paper1, paper2):
    """Test aggregating papers from different model families."""
    # DIFFUSION_SIR paper
    params_sir = [
        ModelParam(name="beta", value=0.3),
        ModelParam(name="gamma", value=0.1),
    ]

    # OPINION_DYNAMICS paper
    params_opinion = [
        ModelParam(name="w_ij", value=0.5),
        ModelParam(name="epsilon", value=0.2),
    ]

    mapping_sir = map_paper_model(paper1, ModelFamily.DIFFUSION_SIR, params_sir)
    mapping_opinion = map_paper_model(paper2, ModelFamily.OPINION_DYNAMICS, params_opinion)

    # Should aggregate successfully (different families, but both map to knobs)
    aggregated = aggregate_multi_paper_priors([mapping_sir, mapping_opinion])

    assert aggregated["total_papers"] == 2
    assert "TEST001" in aggregated["sources"]
    assert "TEST002" in aggregated["sources"]


def test_aggregate_preserves_sod_prior_structure(paper1, paper2):
    """Test that aggregation preserves expected SOD prior structure."""
    params1 = [ModelParam(name="beta", value=0.3), ModelParam(name="gamma", value=0.1)]
    params2 = [ModelParam(name="beta", value=0.5), ModelParam(name="gamma", value=0.2)]

    mapping1 = map_paper_model(paper1, ModelFamily.DIFFUSION_SIR, params1)
    mapping2 = map_paper_model(paper2, ModelFamily.DIFFUSION_SIR, params2)

    aggregated = aggregate_multi_paper_priors([mapping1, mapping2])

    # Check all expected SOD prior keys are present
    expected_keys = {
        "cascade_branching_prob",
        "cascade_damping_factor",
        "cascade_onset_lag_hours",
        "cascade_tail_length_hours",
        "max_cascade_depth",
        "path_probability_threshold",
        "confidence_weight",
        "knobs",
        "aggregated_knobs",
        "sources",
        "weights",
        "total_papers",
        "aggregate_confidence",
    }

    assert expected_keys.issubset(set(aggregated.keys()))


def test_aggregate_confidence_propagation():
    """Test that aggregate confidence is max of input confidences."""
    paper_high = PaperRef("HIGH", "High", "http://high", 2024)
    paper_med = PaperRef("MED", "Med", "http://med", 2024)
    paper_low = PaperRef("LOW", "Low", "http://low", 2024)

    # Create mappings with different confidence levels
    # HIGH: all key params present
    params_high = [
        ModelParam(name="beta", value=0.3),
        ModelParam(name="gamma", value=0.1),
        ModelParam(name="k", value=10.0),
        ModelParam(name="delay", value=2.0),
    ]

    # MED: some key params
    params_med = [
        ModelParam(name="beta", value=0.5),
        ModelParam(name="gamma", value=0.2),
    ]

    # LOW: minimal params
    params_low = [
        ModelParam(name="beta", value=0.7),
    ]

    mapping_high = map_paper_model(paper_high, ModelFamily.DIFFUSION_SIR, params_high)
    mapping_med = map_paper_model(paper_med, ModelFamily.DIFFUSION_SIR, params_med)
    mapping_low = map_paper_model(paper_low, ModelFamily.DIFFUSION_SIR, params_low)

    # Test different combinations
    agg_all = aggregate_multi_paper_priors([mapping_high, mapping_med, mapping_low])
    assert agg_all["aggregate_confidence"] == "HIGH"

    agg_med_low = aggregate_multi_paper_priors([mapping_med, mapping_low])
    assert agg_med_low["aggregate_confidence"] == "MED"

    agg_low_only = aggregate_multi_paper_priors([mapping_low])
    assert agg_low_only["aggregate_confidence"] == "LOW"


def test_aggregate_weighted_mean_calculation():
    """Test that weighted mean is calculated correctly."""
    paper1 = PaperRef("P1", "Paper 1", "http://p1", 2024)
    paper2 = PaperRef("P2", "Paper 2", "http://p2", 2024)

    # Create two HIGH confidence mappings with known values
    # Both HIGH confidence (weight = 1.0)
    params1 = [
        ModelParam(name="beta", value=0.2),  # Will map to lower MRI
        ModelParam(name="gamma", value=0.1),
        ModelParam(name="k", value=10.0),
    ]

    params2 = [
        ModelParam(name="beta", value=0.8),  # Will map to higher MRI
        ModelParam(name="gamma", value=0.1),
        ModelParam(name="k", value=10.0),
    ]

    mapping1 = map_paper_model(paper1, ModelFamily.DIFFUSION_SIR, params1)
    mapping2 = map_paper_model(paper2, ModelFamily.DIFFUSION_SIR, params2)

    aggregated = aggregate_multi_paper_priors([mapping1, mapping2])

    # With equal weights (both HIGH), aggregated MRI should be between the two
    mri1 = mapping1.mapped.mri
    mri2 = mapping2.mapped.mri
    agg_mri = aggregated["aggregated_knobs"]["mri"]

    assert min(mri1, mri2) <= agg_mri <= max(mri1, mri2)

    # With equal weights, should be approximately the mean
    expected_mean = (mri1 + mri2) / 2
    assert abs(agg_mri - expected_mean) < 0.01  # Allow small floating point error
