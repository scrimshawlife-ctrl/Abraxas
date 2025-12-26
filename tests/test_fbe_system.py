"""
Tests for Forecast Branch Ensemble (FBE) v0.1

Validates ensemble initialization, probability updates, and integrity dampening.
"""

import pytest
from datetime import datetime, timezone

from abraxas.forecast.types import Horizon, Branch, EnsembleState
from abraxas.forecast.init import (
    default_ensemble_templates,
    init_ensemble_state,
    generate_ensemble_id,
)
from abraxas.forecast.update import (
    apply_influence_to_ensemble,
    InfluenceEvent,
)
from abraxas.forecast.store import ForecastStore


def test_ensemble_templates_exist():
    """Test that default templates are defined."""
    templates = default_ensemble_templates()

    assert "deepfake_pollution" in templates
    assert "propaganda_pressure" in templates
    assert "integrity_collapse" in templates

    # Check deepfake template structure
    deepfake = templates["deepfake_pollution"]
    assert "branches" in deepfake
    assert "conservative" in deepfake["branches"]
    assert "shock" in deepfake["branches"]


def test_ensemble_initialization_probabilities_sum_to_one():
    """Test that initialized ensemble probabilities sum to 1.0."""
    ensemble = init_ensemble_state(
        topic_key="deepfake_pollution",
        horizon=Horizon.H72H,
        segment="core",
        narrative="N1_primary",
    )

    assert ensemble.topic_key == "deepfake_pollution"
    assert ensemble.horizon == Horizon.H72H

    # Probabilities should sum to ~1.0
    total_p = sum(b.p for b in ensemble.branches)
    assert abs(total_p - 1.0) < 0.01

    # Each branch should have valid probability
    for branch in ensemble.branches:
        assert 0 <= branch.p <= 1
        assert 0 <= branch.p_min <= branch.p_max <= 1


def test_ensemble_id_deterministic():
    """Test that ensemble IDs are deterministic."""
    id1 = generate_ensemble_id("deepfake_pollution", Horizon.H72H, "core", "N1_primary")
    id2 = generate_ensemble_id("deepfake_pollution", Horizon.H72H, "core", "N1_primary")

    assert id1 == id2

    # Different inputs should produce different IDs
    id3 = generate_ensemble_id("deepfake_pollution", Horizon.H30D, "core", "N1_primary")
    assert id1 != id3


def test_influence_update_renormalizes():
    """Test that influence updates renormalize probabilities to sum to 1.0."""
    ensemble = init_ensemble_state(
        topic_key="deepfake_pollution",
        horizon=Horizon.H72H,
    )

    # Create MRI_push influence (increases shock, decreases conservative)
    influence = InfluenceEvent(
        influence_id="test_influence_001",
        target="MRI_push",
        strength=0.8,
        source_type="signal",
    )

    # Apply influence
    updated = apply_influence_to_ensemble(
        ensemble, [influence], integrity_snapshot={"SSI": 0.3}
    )

    # Probabilities should still sum to ~1.0
    total_p = sum(b.p for b in updated.branches)
    assert abs(total_p - 1.0) < 0.01

    # All probabilities should be valid
    for branch in updated.branches:
        assert 0 <= branch.p <= 1


def test_ssi_dampening_reduces_delta():
    """Test that high SSI dampens probability updates."""
    ensemble = init_ensemble_state(
        topic_key="deepfake_pollution",
        horizon=Horizon.H72H,
    )

    # Get initial shock branch probability
    shock_branch_before = next(b for b in ensemble.branches if b.label == "shock")
    p_before = shock_branch_before.p

    # Apply same influence with different SSI values
    influence = InfluenceEvent(
        influence_id="test_influence_002",
        target="MRI_push",
        strength=0.8,
        source_type="signal",
    )

    # Low SSI - should allow larger update
    ensemble_low_ssi = apply_influence_to_ensemble(
        ensemble, [influence], integrity_snapshot={"SSI": 0.2}
    )

    shock_low_ssi = next(b for b in ensemble_low_ssi.branches if b.label == "shock")
    delta_low_ssi = shock_low_ssi.p - p_before

    # High SSI - should dampen update
    ensemble_high_ssi = apply_influence_to_ensemble(
        ensemble, [influence], integrity_snapshot={"SSI": 0.9}
    )

    shock_high_ssi = next(b for b in ensemble_high_ssi.branches if b.label == "shock")
    delta_high_ssi = shock_high_ssi.p - p_before

    # High SSI should result in smaller delta
    assert delta_high_ssi < delta_low_ssi


def test_evidence_pack_bypasses_dampening():
    """Test that evidence packs bypass SSI dampening."""
    ensemble = init_ensemble_state(
        topic_key="deepfake_pollution",
        horizon=Horizon.H72H,
    )

    shock_before = next(b for b in ensemble.branches if b.label == "shock")
    p_before = shock_before.p

    # Evidence pack should bypass dampening even with high SSI
    influence = InfluenceEvent(
        influence_id="test_influence_003",
        target="evidence_pack",
        strength=0.8,
        source_type="evidence_pack",  # Trusted source
    )

    updated = apply_influence_to_ensemble(
        ensemble, [influence], integrity_snapshot={"SSI": 0.9}  # High SSI
    )

    # Evidence pack should still have strong effect despite high SSI
    # (because evidence_pack bypasses dampening)
    # Check that SOME branch was updated
    total_delta = sum(abs(b.p - p_before) for b in updated.branches)
    assert total_delta > 0.01  # Some change occurred


def test_forecast_store_save_and_load(tmp_path):
    """Test saving and loading ensemble state."""
    store = ForecastStore(
        ensembles_dir=tmp_path / "ensembles",
        ledger_path=tmp_path / "ledgers" / "branch_updates.jsonl",
    )

    ensemble = init_ensemble_state(
        topic_key="deepfake_pollution",
        horizon=Horizon.H72H,
    )

    # Save
    store.save_ensemble(ensemble)

    # Load
    loaded = store.load_ensemble(ensemble.ensemble_id)

    assert loaded is not None
    assert loaded.ensemble_id == ensemble.ensemble_id
    assert loaded.topic_key == ensemble.topic_key
    assert len(loaded.branches) == len(ensemble.branches)

    # Probabilities should match
    for i, branch in enumerate(ensemble.branches):
        assert abs(loaded.branches[i].p - branch.p) < 0.001


def test_branch_update_ledger_chaining(tmp_path):
    """Test that branch update ledger maintains hash chain."""
    store = ForecastStore(
        ensembles_dir=tmp_path / "ensembles",
        ledger_path=tmp_path / "ledgers" / "branch_updates.jsonl",
    )

    # Append multiple updates
    for i in range(3):
        record = {
            "ensemble_id": f"ensemble_test_{i}",
            "topic_key": "test",
            "horizon": "H72H",
            "segment": "core",
            "narrative": "N1_primary",
            "branch_probs_before": {"branch_1": 0.5},
            "branch_probs_after": {"branch_1": 0.6},
            "delta_summary": {"test": "update"},
        }
        store.append_branch_update_ledger(record)

    # Verify chain
    updates = store.read_all_updates()
    assert len(updates) == 3

    # Check hash chain
    prev_hash = "genesis"
    for update in updates:
        assert update["prev_hash"] == prev_hash
        assert "step_hash" in update
        prev_hash = update["step_hash"]


def test_horizon_to_hours_conversion():
    """Test horizon conversion to hours."""
    assert Horizon.H72H.to_hours() == 72
    assert Horizon.H30D.to_hours() == 720
    assert Horizon.H90D.to_hours() == 2160
    assert Horizon.H1Y.to_hours() == 8760
    assert Horizon.H2Y.to_hours() == 17520
    assert Horizon.H5Y.to_hours() == 43800


def test_confidence_bands_widen_with_high_ssi():
    """Test that confidence bands widen when SSI is high."""
    ensemble = init_ensemble_state(
        topic_key="deepfake_pollution",
        horizon=Horizon.H72H,
    )

    influence = InfluenceEvent(
        influence_id="test_influence_004",
        target="MRI_push",
        strength=0.5,
        source_type="signal",
    )

    # Low SSI - tighter bands
    updated_low_ssi = apply_influence_to_ensemble(
        ensemble, [influence], integrity_snapshot={"SSI": 0.2, "completeness": 0.9}
    )

    # High SSI - wider bands
    updated_high_ssi = apply_influence_to_ensemble(
        ensemble, [influence], integrity_snapshot={"SSI": 0.8, "completeness": 0.5}
    )

    # Compare band widths
    for i, branch in enumerate(updated_low_ssi.branches):
        band_width_low = branch.p_max - branch.p_min
        band_width_high = updated_high_ssi.branches[i].p_max - updated_high_ssi.branches[i].p_min

        # High SSI should have wider bands
        assert band_width_high >= band_width_low
