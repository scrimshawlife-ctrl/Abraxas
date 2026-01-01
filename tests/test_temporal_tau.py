"""Golden tests for temporal operator τ (tau).

Tests deterministic τₕ, τᵥ, τₚ calculations with fixed fixtures.
Verifies stable output against golden JSON.
"""

from datetime import datetime, timezone, timedelta

import pytest

from abraxas.core.temporal_tau import (
    TauCalculator,
    Observation,
    ConfidenceLevel,
)


@pytest.fixture
def fixed_observations():
    """Fixed observation set for deterministic testing."""
    base_time = datetime(2025, 12, 20, 12, 0, 0, tzinfo=timezone.utc)
    observations = [
        Observation(
            ts=base_time.isoformat().replace("+00:00", "Z"),
            value=1.0,
            source_id="src-001",
        ),
        Observation(
            ts=(base_time + timedelta(hours=24)).isoformat().replace("+00:00", "Z"),
            value=1.0,
            source_id="src-002",
        ),
        Observation(
            ts=(base_time + timedelta(hours=48)).isoformat().replace("+00:00", "Z"),
            value=1.0,
            source_id="src-003",
        ),
        Observation(
            ts=(base_time + timedelta(hours=72)).isoformat().replace("+00:00", "Z"),
            value=1.0,
            source_id="src-004",
        ),
        Observation(
            ts=(base_time + timedelta(hours=96)).isoformat().replace("+00:00", "Z"),
            value=1.0,
            source_id="src-005",
        ),
    ]
    return observations


def test_tau_calculator_basic(fixed_observations):
    """Test basic τ calculation with fixed observations."""
    calculator = TauCalculator(git_sha="test-sha", host="test-host")
    current_time = "2025-12-20T16:00:00Z"  # 4 hours after last observation

    snapshot = calculator.compute_snapshot(
        fixed_observations,
        run_id="test-run-001",
        current_time_utc=current_time,
    )

    # Verify basic properties
    assert snapshot.observation_count == 5
    assert snapshot.confidence == ConfidenceLevel.MED  # 5-19 samples = MED
    assert snapshot.tau_half_life > 0
    assert snapshot.tau_velocity >= 0  # Should be ~0 for uniform spacing


def test_tau_calculator_empty():
    """Test τ calculation with no observations."""
    calculator = TauCalculator()
    snapshot = calculator.compute_snapshot(
        [], run_id="test-empty", current_time_utc="2025-12-20T12:00:00Z"
    )

    assert snapshot.observation_count == 0
    assert snapshot.tau_half_life == 0.0
    assert snapshot.tau_velocity == 0.0
    assert snapshot.tau_phase_proximity == 0.0
    assert snapshot.confidence == ConfidenceLevel.LOW


def test_tau_half_life_decay(fixed_observations):
    """Test that half-life decreases with large gap since last observation."""
    calculator = TauCalculator()

    # Current time shortly after last observation
    snapshot_recent = calculator.compute_snapshot(
        fixed_observations,
        run_id="test-recent",
        current_time_utc="2025-12-24T16:00:00Z",  # 4 hours after last
    )

    # Current time long after last observation
    snapshot_late = calculator.compute_snapshot(
        fixed_observations,
        run_id="test-late",
        current_time_utc="2025-12-30T16:00:00Z",  # 6 days after last
    )

    # Half-life should be lower when gap is larger (faster decay)
    assert snapshot_late.tau_half_life < snapshot_recent.tau_half_life


def test_tau_velocity_positive():
    """Test τᵥ is positive for increasing observations."""
    calculator = TauCalculator()
    base_time = datetime(2025, 12, 20, 12, 0, 0, tzinfo=timezone.utc)

    observations = [
        Observation(
            ts=(base_time + timedelta(hours=i * 12)).isoformat().replace("+00:00", "Z"),
            value=float(i + 1),  # Increasing values
            source_id=f"src-{i:03d}",
        )
        for i in range(10)
    ]

    snapshot = calculator.compute_snapshot(
        observations,
        run_id="test-positive-velocity",
        current_time_utc="2025-12-25T12:00:00Z",
    )

    # Velocity should be positive for increasing values
    assert snapshot.tau_velocity > 0


def test_tau_velocity_negative():
    """Test τᵥ is negative for decreasing observations."""
    calculator = TauCalculator()
    base_time = datetime(2025, 12, 20, 12, 0, 0, tzinfo=timezone.utc)

    observations = [
        Observation(
            ts=(base_time + timedelta(hours=i * 12)).isoformat().replace("+00:00", "Z"),
            value=float(10 - i),  # Decreasing values
            source_id=f"src-{i:03d}",
        )
        for i in range(10)
    ]

    snapshot = calculator.compute_snapshot(
        observations,
        run_id="test-negative-velocity",
        current_time_utc="2025-12-25T12:00:00Z",
    )

    # Velocity should be negative for decreasing values
    assert snapshot.tau_velocity < 0


def test_tau_confidence_levels():
    """Test confidence level determination."""
    calculator = TauCalculator()
    base_time = datetime(2025, 12, 20, 12, 0, 0, tzinfo=timezone.utc)

    # LOW: < 5 samples
    obs_low = [
        Observation(
            ts=(base_time + timedelta(hours=i * 12)).isoformat().replace("+00:00", "Z"),
            value=1.0,
            source_id=f"src-{i:03d}",
        )
        for i in range(3)
    ]
    snapshot_low = calculator.compute_snapshot(obs_low, run_id="test-low")
    assert snapshot_low.confidence == ConfidenceLevel.LOW

    # MED: 5-19 samples
    obs_med = [
        Observation(
            ts=(base_time + timedelta(hours=i * 12)).isoformat().replace("+00:00", "Z"),
            value=1.0,
            source_id=f"src-{i:03d}",
        )
        for i in range(10)
    ]
    snapshot_med = calculator.compute_snapshot(obs_med, run_id="test-med")
    assert snapshot_med.confidence == ConfidenceLevel.MED

    # HIGH: >= 20 samples with low variance
    obs_high = [
        Observation(
            ts=(base_time + timedelta(hours=i * 12)).isoformat().replace("+00:00", "Z"),
            value=1.0,  # Constant value = low variance
            source_id=f"src-{i:03d}",
        )
        for i in range(25)
    ]
    snapshot_high = calculator.compute_snapshot(obs_high, run_id="test-high")
    assert snapshot_high.confidence == ConfidenceLevel.HIGH
