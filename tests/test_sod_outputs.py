"""Golden tests for SOD outputs.

Tests deterministic scenario generation from NCP and other SOD modules.
"""

import pytest

from abraxas.core.temporal_tau import TauSnapshot, ConfidenceLevel
from abraxas.core.provenance import Provenance
from abraxas.integrity.composites import (
    compute_artifact_integrity,
    compute_narrative_manipulation,
    compute_network_campaign,
    compute_composite_risk,
)
from abraxas.weather.affinity import compute_affinity
from abraxas.weather.registry import WeatherType
from abraxas.sod.models import SODInput
from abraxas.sod.ncp import NarrativeCascadePredictor
from abraxas.sod.cnf import CounterNarrativeForecaster
from abraxas.sod.efte import EpistemicFatigueThresholdEngine


@pytest.fixture
def mock_tau_snapshot():
    """Mock tau snapshot for testing."""
    return TauSnapshot(
        tau_half_life=100.0,
        tau_velocity=0.8,
        tau_phase_proximity=0.6,
        confidence=ConfidenceLevel.MED,
        observation_count=10,
        observation_window_hours=120.0,
        provenance=Provenance(
            run_id="test",
            started_at_utc="2025-12-20T12:00:00Z",
            inputs_hash="test",
            config_hash="test",
        ),
    )


@pytest.fixture
def mock_risk_indices():
    """Mock risk indices for testing."""
    artifact_integrity = compute_artifact_integrity(
        has_timestamp=True,
        has_source_id=True,
        source_chain_length=2,
    )
    narrative_manipulation = compute_narrative_manipulation(
        framing_indicators=2,
        total_framing_checked=5,
    )
    network_campaign = compute_network_campaign(
        uniformity_score=0.5,
        propagation_rate=10.0,
    )
    return compute_composite_risk(
        artifact_integrity, narrative_manipulation, network_campaign
    )


def test_ncp_predicts_scenarios(mock_tau_snapshot, mock_risk_indices):
    """Test NCP generates scenario envelope."""
    affinity = compute_affinity(
        "eggcorn",
        mock_tau_snapshot,
        ["humor"],
        WeatherType.MW_01_SYMBOLIC_DRIFT,
    )

    sod_input = SODInput(
        tau_snapshot=mock_tau_snapshot,
        risk_indices=mock_risk_indices,
        affinity_score=affinity,
        context={},
    )

    ncp = NarrativeCascadePredictor(top_k=5)
    envelope = ncp.predict(sod_input, run_id="test-ncp")

    assert envelope.scenario_id is not None
    assert len(envelope.paths) > 0  # Should generate at least one path
    assert len(envelope.falsifiers) > 0
    assert envelope.confidence in ["LOW", "MED", "HIGH"]
    assert envelope.provenance.run_id == "test-ncp"


def test_ncp_paths_have_probabilities(mock_tau_snapshot, mock_risk_indices):
    """Test NCP paths have valid probabilities."""
    sod_input = SODInput(
        tau_snapshot=mock_tau_snapshot,
        risk_indices=mock_risk_indices,
        affinity_score=None,
        context={},
    )

    ncp = NarrativeCascadePredictor()
    envelope = ncp.predict(sod_input)

    for path in envelope.paths:
        assert 0.0 <= path.probability <= 1.0
        assert path.duration_hours > 0
        assert len(path.intermediates) > 0
        assert path.terminus is not None


def test_cnf_generates_strategies(mock_tau_snapshot, mock_risk_indices):
    """Test CNF generates counter-narrative strategies."""
    sod_input = SODInput(
        tau_snapshot=mock_tau_snapshot,
        risk_indices=mock_risk_indices,
        affinity_score=None,
        context={},
    )

    ncp = NarrativeCascadePredictor()
    envelope = ncp.predict(sod_input)

    cnf = CounterNarrativeForecaster()
    strategies = cnf.forecast(envelope)

    assert len(strategies) > 0  # Should generate at least one strategy
    for strategy in strategies:
        assert 0.0 <= strategy.effectiveness_score <= 1.0
        assert len(strategy.intervention_points) > 0


def test_efte_computes_fatigue():
    """Test EFTE computes epistemic fatigue threshold."""
    efte = EpistemicFatigueThresholdEngine()

    # High exposure, high RRS
    fatigue = efte.compute_fatigue(
        exposure_count=100,
        time_window_hours=24,
        rrs_score=0.8,
        engagement_trend=[0.9, 0.85, 0.8, 0.7, 0.6, 0.5],  # Declining
    )

    assert 0.0 <= fatigue.threshold <= 1.0
    assert fatigue.saturation_risk in ["LOW", "MED", "HIGH"]
    assert fatigue.declining_engagement is True
    assert fatigue.exposure_density > 0


def test_efte_low_fatigue():
    """Test EFTE with low exposure and RRS."""
    efte = EpistemicFatigueThresholdEngine()

    fatigue = efte.compute_fatigue(
        exposure_count=5,
        time_window_hours=168,  # 1 week
        rrs_score=0.2,
        engagement_trend=[0.5, 0.5, 0.5, 0.5],  # Stable
    )

    assert fatigue.threshold < 0.4  # Should be low
    assert fatigue.saturation_risk == "LOW"
    assert fatigue.declining_engagement is False
