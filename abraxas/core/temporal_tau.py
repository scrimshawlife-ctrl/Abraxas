"""Temporal Operator τ (Tau): Symbolic lifecycle dynamics measurement.

This module provides three complementary temporal metrics:
- τₕ (Tau Half-Life): Symbolic persistence under declining reinforcement
- τᵥ (Tau Velocity): Emergence/decay slope from time-series observations
- τₚ (Tau Phase Proximity): Distance to next lifecycle boundary

All computations are deterministic with provenance embedding.
Silence-as-signal: missing observations affect decay/velocity calculations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.core.provenance import Provenance


class ConfidenceLevel(str, Enum):
    """Confidence band for τ measurements."""

    LOW = "LOW"
    MED = "MED"
    HIGH = "HIGH"


@dataclass(frozen=True)
class Observation:
    """Single observation event with timestamp and value."""

    ts: str  # ISO8601 UTC
    value: float
    source_id: str


@dataclass(frozen=True)
class TauSnapshot:
    """Complete τ measurement snapshot with confidence."""

    tau_half_life: float  # τₕ: persistence measure (hours)
    tau_velocity: float  # τᵥ: emergence/decay slope (events/day)
    tau_phase_proximity: float  # τₚ: distance to next lifecycle boundary [0,1]
    confidence: ConfidenceLevel
    observation_count: int
    observation_window_hours: float
    provenance: Provenance


class TauCalculator:
    """
    Deterministic calculator for temporal τ metrics.

    Implements:
    - Exponential decay model for half-life
    - Linear regression for velocity
    - Threshold-based phase proximity
    """

    # Confidence thresholds
    MIN_SAMPLES_MED = 5
    MIN_SAMPLES_HIGH = 20
    MIN_WINDOW_HOURS = 48.0
    MAX_VARIANCE_HIGH = 0.3  # Coefficient of variation threshold

    def __init__(
        self,
        *,
        git_sha: Optional[str] = None,
        host: Optional[str] = None,
    ):
        """Initialize calculator with optional provenance context."""
        self._git_sha = git_sha
        self._host = host

    def compute_snapshot(
        self,
        observations: List[Observation],
        *,
        run_id: Optional[str] = None,
        current_time_utc: Optional[str] = None,
    ) -> TauSnapshot:
        """
        Compute complete τ snapshot from observation history.

        Args:
            observations: Time-ordered observations (oldest to newest)
            run_id: Optional run identifier
            current_time_utc: Optional reference time (defaults to now)

        Returns:
            TauSnapshot with τₕ, τᵥ, τₚ, and confidence
        """
        if not observations:
            # No observations = zero persistence, zero velocity, archived phase
            return self._empty_snapshot(run_id, current_time_utc)

        # Sort observations by timestamp (deterministic ordering)
        sorted_obs = sorted(observations, key=lambda o: o.ts)

        # Compute observation window
        first_ts = self._parse_iso(sorted_obs[0].ts)
        last_ts = self._parse_iso(sorted_obs[-1].ts)
        current_ts = (
            self._parse_iso(current_time_utc)
            if current_time_utc
            else datetime.now(timezone.utc)
        )
        window_hours = (last_ts - first_ts).total_seconds() / 3600.0
        time_since_last_hours = (current_ts - last_ts).total_seconds() / 3600.0

        # Compute τₕ (half-life)
        tau_h = self._compute_half_life(sorted_obs, time_since_last_hours)

        # Compute τᵥ (velocity)
        tau_v = self._compute_velocity(sorted_obs, window_hours)

        # Compute τₚ (phase proximity)
        tau_p = self._compute_phase_proximity(tau_h, tau_v)

        # Compute confidence
        confidence = self._compute_confidence(sorted_obs, window_hours)

        # Build provenance
        inputs_obj = {
            "observations": [
                {"ts": o.ts, "value": float(o.value), "source_id": o.source_id}
                for o in sorted_obs
            ],
            "current_time_utc": current_ts.isoformat().replace("+00:00", "Z"),
        }
        inputs_hash = sha256_hex(canonical_json(inputs_obj))
        config_hash = sha256_hex(
            canonical_json(
                {
                    "operator": "TauCalculator.v1",
                    "thresholds": {
                        "min_samples_med": self.MIN_SAMPLES_MED,
                        "min_samples_high": self.MIN_SAMPLES_HIGH,
                        "min_window_hours": self.MIN_WINDOW_HOURS,
                        "max_variance_high": self.MAX_VARIANCE_HIGH,
                    },
                }
            )
        )

        prov = Provenance(
            run_id=run_id or "tau-calc",
            started_at_utc=Provenance.now_iso_z(),
            inputs_hash=inputs_hash,
            config_hash=config_hash,
            git_sha=self._git_sha,
            host=self._host,
        )

        return TauSnapshot(
            tau_half_life=tau_h,
            tau_velocity=tau_v,
            tau_phase_proximity=tau_p,
            confidence=confidence,
            observation_count=len(sorted_obs),
            observation_window_hours=window_hours,
            provenance=prov,
        )

    def _compute_half_life(
        self, observations: List[Observation], time_since_last_hours: float
    ) -> float:
        """
        Compute τₕ (half-life) using exponential decay model.

        Model: If observation frequency is declining, half-life represents the time
        for frequency to halve. Silence-as-signal: gap since last observation
        accelerates decay.

        Args:
            observations: Time-ordered observations
            time_since_last_hours: Hours since last observation

        Returns:
            Half-life in hours (lower = faster decay)
        """
        if len(observations) < 2:
            # Insufficient data: assume short half-life with gap penalty
            return max(1.0, 24.0 - time_since_last_hours)

        # Compute inter-observation intervals
        intervals = []
        for i in range(1, len(observations)):
            t1 = self._parse_iso(observations[i - 1].ts)
            t2 = self._parse_iso(observations[i].ts)
            interval_hours = (t2 - t1).total_seconds() / 3600.0
            intervals.append(interval_hours)

        # Mean interval as base half-life estimate
        mean_interval = sum(intervals) / len(intervals)

        # Adjust for recency: if gap since last observation exceeds mean,
        # half-life decreases (faster decay)
        recency_factor = 1.0
        if time_since_last_hours > mean_interval:
            recency_factor = mean_interval / max(time_since_last_hours, 1.0)

        # Half-life = mean_interval * recency_factor
        # Clamped to [1.0, 8760.0] (1 hour to 1 year)
        half_life = mean_interval * recency_factor
        return max(1.0, min(half_life, 8760.0))

    def _compute_velocity(
        self, observations: List[Observation], window_hours: float
    ) -> float:
        """
        Compute τᵥ (velocity) as emergence/decay slope.

        Model: Simple linear regression of observation values over time.
        Positive = emergence, negative = decay, ~0 = stability.

        Args:
            observations: Time-ordered observations
            window_hours: Total observation window

        Returns:
            Velocity (events/day)
        """
        if len(observations) < 2:
            return 0.0

        # Convert timestamps to hours from first observation
        first_ts = self._parse_iso(observations[0].ts)
        time_points = []
        values = []
        for obs in observations:
            ts = self._parse_iso(obs.ts)
            hours_from_start = (ts - first_ts).total_seconds() / 3600.0
            time_points.append(hours_from_start)
            values.append(obs.value)

        # Simple linear regression: slope = Δy / Δx
        n = len(observations)
        mean_x = sum(time_points) / n
        mean_y = sum(values) / n

        numerator = sum(
            (time_points[i] - mean_x) * (values[i] - mean_y) for i in range(n)
        )
        denominator = sum((time_points[i] - mean_x) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        slope_per_hour = numerator / denominator
        # Convert to events/day
        velocity = slope_per_hour * 24.0

        return velocity

    def _compute_phase_proximity(self, tau_h: float, tau_v: float) -> float:
        """
        Compute τₚ (phase proximity) to next lifecycle boundary.

        Phases (simplified thresholds):
        - Proto: τₕ < 48h, τᵥ > 0.5
        - Front: τₕ 48-168h, τᵥ > 0
        - Saturated: τₕ > 168h, |τᵥ| < 0.1
        - Dormant: τₕ < 168h, τᵥ < -0.1
        - Archived: τₕ < 24h, τᵥ < -0.5

        Args:
            tau_h: Half-life (hours)
            tau_v: Velocity (events/day)

        Returns:
            Proximity [0,1] to next boundary (higher = closer to transition)
        """
        # Determine current phase and distance to boundaries
        if tau_h < 24 and tau_v < -0.5:
            # Archived: proximity to revival (very low)
            return 0.1
        elif tau_h < 48 and tau_v > 0.5:
            # Proto: proximity to Front
            proximity = min(tau_h / 48.0, 1.0)
            return proximity
        elif 48 <= tau_h < 168 and tau_v > 0:
            # Front: proximity to Saturated
            proximity = tau_h / 168.0
            return proximity
        elif tau_h >= 168 and abs(tau_v) < 0.1:
            # Saturated: proximity to Dormant (watch for velocity sign change)
            proximity = abs(tau_v) / 0.1
            return 1.0 - proximity  # Closer to 0 velocity = lower proximity
        elif tau_v < -0.1:
            # Dormant: proximity to Archived
            proximity = max(0.0, (168 - tau_h) / 144.0)  # 168 - 24 = 144
            return proximity
        else:
            # Transition state
            return 0.5

    def _compute_confidence(
        self, observations: List[Observation], window_hours: float
    ) -> ConfidenceLevel:
        """
        Compute confidence band based on sample size and variance.

        Rules:
        - LOW: sample_size < 5 OR window < 48h
        - MED: sample_size 5-19 OR variance > threshold
        - HIGH: sample_size >= 20 AND variance <= threshold

        Args:
            observations: All observations
            window_hours: Observation window

        Returns:
            ConfidenceLevel (LOW/MED/HIGH)
        """
        n = len(observations)

        # Sample size check
        if n < self.MIN_SAMPLES_MED or window_hours < self.MIN_WINDOW_HOURS:
            return ConfidenceLevel.LOW

        # Variance check (coefficient of variation)
        values = [obs.value for obs in observations]
        mean_val = sum(values) / n
        if mean_val == 0:
            return ConfidenceLevel.MED

        variance = sum((v - mean_val) ** 2 for v in values) / n
        std_dev = math.sqrt(variance)
        coef_variation = std_dev / abs(mean_val)

        if n >= self.MIN_SAMPLES_HIGH and coef_variation <= self.MAX_VARIANCE_HIGH:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.MED

    def _empty_snapshot(
        self, run_id: Optional[str], current_time_utc: Optional[str]
    ) -> TauSnapshot:
        """Return empty snapshot for zero observations."""
        current_ts = (
            self._parse_iso(current_time_utc)
            if current_time_utc
            else datetime.now(timezone.utc)
        )

        inputs_hash = sha256_hex(canonical_json({"observations": []}))
        config_hash = sha256_hex(canonical_json({"operator": "TauCalculator.v1"}))

        prov = Provenance(
            run_id=run_id or "tau-calc",
            started_at_utc=current_ts.isoformat().replace("+00:00", "Z"),
            inputs_hash=inputs_hash,
            config_hash=config_hash,
            git_sha=self._git_sha,
            host=self._host,
        )

        return TauSnapshot(
            tau_half_life=0.0,
            tau_velocity=0.0,
            tau_phase_proximity=0.0,
            confidence=ConfidenceLevel.LOW,
            observation_count=0,
            observation_window_hours=0.0,
            provenance=prov,
        )

    @staticmethod
    def _parse_iso(ts: str) -> datetime:
        """Parse ISO8601 timestamp to datetime (UTC)."""
        # Handle both Z and +00:00 suffixes
        ts_normalized = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_normalized)
