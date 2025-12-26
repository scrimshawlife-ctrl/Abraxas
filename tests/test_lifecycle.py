"""Golden tests for lifecycle state machine.

Tests deterministic state transitions based on τ thresholds.
"""

import pytest

from abraxas.slang.lifecycle import (
    LifecycleEngine,
    LifecycleState,
    TransitionThresholds,
    MutationEvidence,
    compute_edit_distance,
)
from abraxas.core.temporal_tau import TauSnapshot, ConfidenceLevel
from abraxas.core.provenance import Provenance


@pytest.fixture
def engine():
    """Lifecycle engine with default thresholds."""
    return LifecycleEngine()


@pytest.fixture
def mock_provenance():
    """Mock provenance for tau snapshots."""
    return Provenance(
        run_id="test-run",
        started_at_utc="2025-12-20T12:00:00Z",
        inputs_hash="test-hash",
        config_hash="test-config",
    )


def test_proto_to_front_transition(engine, mock_provenance):
    """Test Proto → Front transition."""
    tau = TauSnapshot(
        tau_half_life=50.0,
        tau_velocity=0.7,  # Above threshold (0.5)
        tau_phase_proximity=0.5,
        confidence=ConfidenceLevel.MED,
        observation_count=10,  # Above min (5)
        observation_window_hours=100.0,
        provenance=mock_provenance,
    )

    new_state = engine.compute_state(LifecycleState.PROTO, tau)
    assert new_state == LifecycleState.FRONT


def test_proto_stays_proto(engine, mock_provenance):
    """Test Proto remains Proto if conditions not met."""
    tau = TauSnapshot(
        tau_half_life=20.0,
        tau_velocity=0.3,  # Below threshold
        tau_phase_proximity=0.2,
        confidence=ConfidenceLevel.LOW,
        observation_count=3,  # Below min
        observation_window_hours=50.0,
        provenance=mock_provenance,
    )

    new_state = engine.compute_state(LifecycleState.PROTO, tau)
    assert new_state == LifecycleState.PROTO


def test_front_to_saturated_transition(engine, mock_provenance):
    """Test Front → Saturated transition."""
    tau = TauSnapshot(
        tau_half_life=200.0,  # Above threshold (168h)
        tau_velocity=0.05,  # Near zero, below threshold (0.1)
        tau_phase_proximity=0.8,
        confidence=ConfidenceLevel.HIGH,
        observation_count=25,
        observation_window_hours=300.0,
        provenance=mock_provenance,
    )

    new_state = engine.compute_state(LifecycleState.FRONT, tau)
    assert new_state == LifecycleState.SATURATED


def test_saturated_to_dormant_transition(engine, mock_provenance):
    """Test Saturated → Dormant transition."""
    tau = TauSnapshot(
        tau_half_life=150.0,
        tau_velocity=-0.2,  # Negative, below threshold (-0.1)
        tau_phase_proximity=0.6,
        confidence=ConfidenceLevel.MED,
        observation_count=15,
        observation_window_hours=200.0,
        provenance=mock_provenance,
    )

    new_state = engine.compute_state(LifecycleState.SATURATED, tau)
    assert new_state == LifecycleState.DORMANT


def test_dormant_to_archived_transition(engine, mock_provenance):
    """Test Dormant → Archived transition."""
    tau = TauSnapshot(
        tau_half_life=20.0,  # Below threshold (24h)
        tau_velocity=-0.3,
        tau_phase_proximity=0.1,
        confidence=ConfidenceLevel.LOW,
        observation_count=3,
        observation_window_hours=50.0,
        provenance=mock_provenance,
    )

    new_state = engine.compute_state(LifecycleState.DORMANT, tau)
    assert new_state == LifecycleState.ARCHIVED


def test_revival_from_archived(engine, mock_provenance):
    """Test revival from Archived state with mutation evidence."""
    tau = TauSnapshot(
        tau_half_life=30.0,
        tau_velocity=0.4,  # Positive velocity
        tau_phase_proximity=0.3,
        confidence=ConfidenceLevel.MED,
        observation_count=5,
        observation_window_hours=60.0,
        provenance=mock_provenance,
    )

    mutation = MutationEvidence(
        edit_distance=3,  # Above threshold (2)
        token_modifier_changed=False,
        description="Significant mutation detected",
    )

    new_state = engine.compute_state(LifecycleState.ARCHIVED, tau, mutation)
    assert new_state == LifecycleState.PROTO  # Revival to Proto


def test_edit_distance_calculation():
    """Test Levenshtein edit distance calculation."""
    # Identical strings
    assert compute_edit_distance("hello", "hello") == 0

    # Single character substitution
    assert compute_edit_distance("hello", "hallo") == 1

    # Single character insertion
    assert compute_edit_distance("hello", "helloo") == 1

    # Single character deletion
    assert compute_edit_distance("hello", "hell") == 1

    # Multiple operations
    assert compute_edit_distance("kitten", "sitting") == 3

    # Completely different
    assert compute_edit_distance("abc", "xyz") == 3
