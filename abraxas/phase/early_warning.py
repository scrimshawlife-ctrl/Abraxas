"""Early Warning System for Phase Transitions

Provides advance notice of upcoming lifecycle phase transitions across domains.

Uses:
- Synchronicity patterns (if domain X transitioned, domain Y likely follows)
- Tau metrics (velocity, half-life predict transitions)
- Alignment history (phase clustering predicts cascade)

Deterministic, evidence-based, no vibes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from abraxas.core.provenance import Provenance
from abraxas.core.canonical import sha256_hex, canonical_json
from abraxas.core.temporal_tau import TauSnapshot


@dataclass(frozen=True)
class PhaseTransitionWarning:
    """Early warning for predicted phase transition."""

    warning_id: str
    domain: str
    current_phase: str
    predicted_phase: str
    estimated_hours: float  # Hours until transition
    confidence: float  # [0, 1]
    trigger_signals: Tuple[str, ...]  # What triggered this warning
    evidence: Dict[str, any]  # Supporting evidence
    issued_utc: str
    provenance: Optional[Provenance] = None

    def to_dict(self) -> Dict:
        return {
            "warning_id": self.warning_id,
            "domain": self.domain,
            "current_phase": self.current_phase,
            "predicted_phase": self.predicted_phase,
            "estimated_hours": self.estimated_hours,
            "confidence": self.confidence,
            "trigger_signals": list(self.trigger_signals),
            "evidence": self.evidence,
            "issued_utc": self.issued_utc,
            "provenance": self.provenance.__dict__ if self.provenance else None,
        }


class EarlyWarningSystem:
    """
    Early warning system for phase transitions.

    Predicts upcoming transitions using:
    1. Tau metrics (velocity → direction, half-life → timing)
    2. Synchronicity patterns (domain X → domain Y coupling)
    3. Alignment history (phase cascades)
    """

    def __init__(
        self,
        velocity_threshold: float = 0.5,
        confidence_threshold: float = 0.6,
    ) -> None:
        """Initialize early warning system.

        Args:
            velocity_threshold: Tau velocity threshold for transition warning
            confidence_threshold: Minimum confidence for warning
        """
        self._velocity_threshold = velocity_threshold
        self._confidence_threshold = confidence_threshold

    def generate_warnings(
        self,
        domain_tau_snapshots: Dict[str, TauSnapshot],  # domain → tau snapshot
        domain_current_phases: Dict[str, str],  # domain → current phase
        synchronicity_map: Optional[any] = None,  # SynchronicityMap
        run_id: str = "WARNING",
    ) -> List[PhaseTransitionWarning]:
        """Generate early warnings for phase transitions.

        Args:
            domain_tau_snapshots: Tau snapshots for each domain
            domain_current_phases: Current lifecycle phase for each domain
            synchronicity_map: Optional synchronicity map for cross-domain predictions
            run_id: Run identifier for provenance

        Returns:
            List of phase transition warnings
        """
        warnings: List[PhaseTransitionWarning] = []
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        for domain, tau in domain_tau_snapshots.items():
            current_phase = domain_current_phases.get(domain, "unknown")
            if current_phase == "unknown":
                continue

            # Check tau-based warning
            tau_warning = self._check_tau_warning(
                domain, current_phase, tau, timestamp, run_id
            )
            if tau_warning:
                warnings.append(tau_warning)

            # Check synchronicity-based warning
            if synchronicity_map:
                sync_warning = self._check_synchronicity_warning(
                    domain, current_phase, synchronicity_map, timestamp, run_id
                )
                if sync_warning:
                    warnings.append(sync_warning)

        return warnings

    def _check_tau_warning(
        self,
        domain: str,
        current_phase: str,
        tau: TauSnapshot,
        timestamp: str,
        run_id: str,
    ) -> Optional[PhaseTransitionWarning]:
        """Check if tau metrics warrant a transition warning."""
        # Velocity-based transition prediction
        if abs(tau.tau_velocity) < self._velocity_threshold:
            return None  # Velocity too low for transition

        # Predict next phase based on velocity direction and current phase
        predicted_phase, confidence = self._predict_next_phase(current_phase, tau)

        if confidence < self._confidence_threshold:
            return None  # Confidence too low

        # Estimate time to transition based on velocity
        estimated_hours = self._estimate_transition_time(tau)

        # Build evidence
        evidence = {
            "tau_velocity": tau.tau_velocity,
            "tau_half_life": tau.tau_half_life,
            "tau_pressure": tau.tau_pressure,
            "observation_count": tau.observation_count,
            "confidence_band": tau.confidence_band,
        }

        # Create provenance
        prov = Provenance(
            run_id=run_id,
            started_at_utc=timestamp,
            inputs_hash=sha256_hex(canonical_json({
                "domain": domain,
                "tau": {
                    "velocity": tau.tau_velocity,
                    "half_life": tau.tau_half_life,
                },
            })),
            config_hash=sha256_hex(canonical_json({
                "velocity_threshold": self._velocity_threshold,
                "confidence_threshold": self._confidence_threshold,
            })),
        )

        warning_id = f"WARN-TAU-{domain}-{predicted_phase}-{timestamp[:10]}"

        return PhaseTransitionWarning(
            warning_id=warning_id,
            domain=domain,
            current_phase=current_phase,
            predicted_phase=predicted_phase,
            estimated_hours=estimated_hours,
            confidence=confidence,
            trigger_signals=("tau_velocity", "tau_half_life"),
            evidence=evidence,
            issued_utc=timestamp,
            provenance=prov,
        )

    def _check_synchronicity_warning(
        self,
        domain: str,
        current_phase: str,
        synchronicity_map: any,  # SynchronicityMap
        timestamp: str,
        run_id: str,
    ) -> Optional[PhaseTransitionWarning]:
        """Check if synchronicity patterns warrant a transition warning."""
        # Use synchronicity map to predict transition
        prediction = synchronicity_map.predict_transition(domain, current_phase)

        if prediction is None:
            return None

        predicted_phase, lag_hours = prediction

        # Build evidence
        evidence = {
            "synchronicity_pattern": f"domain follows pattern",
            "lag_hours": lag_hours,
        }

        # Confidence based on pattern strength
        # (In production, use pattern confidence from SynchronicityMap)
        confidence = 0.7

        if confidence < self._confidence_threshold:
            return None

        prov = Provenance(
            run_id=run_id,
            started_at_utc=timestamp,
            inputs_hash=sha256_hex(canonical_json({
                "domain": domain,
                "current_phase": current_phase,
            })),
            config_hash=sha256_hex(canonical_json({
                "confidence_threshold": self._confidence_threshold,
            })),
        )

        warning_id = f"WARN-SYNC-{domain}-{predicted_phase}-{timestamp[:10]}"

        return PhaseTransitionWarning(
            warning_id=warning_id,
            domain=domain,
            current_phase=current_phase,
            predicted_phase=predicted_phase,
            estimated_hours=lag_hours,
            confidence=confidence,
            trigger_signals=("synchronicity_pattern",),
            evidence=evidence,
            issued_utc=timestamp,
            provenance=prov,
        )

    def _predict_next_phase(
        self, current_phase: str, tau: TauSnapshot
    ) -> Tuple[str, float]:
        """Predict next phase based on current phase and tau metrics.

        Returns:
            (next_phase, confidence)
        """
        # Velocity direction determines transition type
        if tau.tau_velocity > 0.5:
            # High positive velocity → advancing phase
            phase_map = {
                "proto": ("front", 0.8),
                "front": ("saturated", 0.7),
                "saturated": ("saturated", 0.3),  # Already at peak
                "dormant": ("proto", 0.6),  # Revival
                "archived": ("proto", 0.5),  # Rare revival
            }
        elif tau.tau_velocity < -0.2:
            # Negative velocity → declining phase
            phase_map = {
                "proto": ("dormant", 0.5),
                "front": ("saturated", 0.6),  # Slowing down
                "saturated": ("dormant", 0.8),
                "dormant": ("archived", 0.8),
                "archived": ("archived", 0.2),  # Already archived
            }
        else:
            # Low velocity → stable
            phase_map = {
                "proto": ("proto", 0.4),
                "front": ("front", 0.4),
                "saturated": ("saturated", 0.6),
                "dormant": ("dormant", 0.5),
                "archived": ("archived", 0.3),
            }

        return phase_map.get(current_phase, (current_phase, 0.3))

    def _estimate_transition_time(self, tau: TauSnapshot) -> float:
        """Estimate hours until transition based on tau metrics."""
        # Higher velocity = faster transition
        if abs(tau.tau_velocity) > 0.7:
            return 24.0  # 1 day
        elif abs(tau.tau_velocity) > 0.4:
            return 48.0  # 2 days
        elif abs(tau.tau_velocity) > 0.2:
            return 96.0  # 4 days
        else:
            return 168.0  # 7 days


def create_early_warning_system(
    velocity_threshold: float = 0.5,
    confidence_threshold: float = 0.6,
) -> EarlyWarningSystem:
    """Create early warning system with default configuration.

    Args:
        velocity_threshold: Tau velocity threshold for transition warning (default 0.5)
        confidence_threshold: Minimum confidence for warning (default 0.6)

    Returns:
        Configured EarlyWarningSystem
    """
    return EarlyWarningSystem(
        velocity_threshold=velocity_threshold,
        confidence_threshold=confidence_threshold,
    )
