"""
Oracle Pipeline v2: Signal → Compression → Forecast → Narrative

Unified assembly of existing components:
- DCE: Domain compression (signal extraction)
- Lifecycle Forecasting: Phase transition prediction
- Resonance: Cross-domain alignment detection
- Provenance Bundles: Evidence-grade artifacts
- Memetic Weather: Narrative trajectories
- 6-Gate Governance: Metric validation

Architecture:
┌─────────────┐
│   SIGNAL    │  Raw observations, domain signals
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ COMPRESSION │  DCE: Extract domain-specific signals
└──────┬──────┘  Lifecycle: Determine symbolic maturity
       │
       ↓
┌─────────────┐
│  FORECAST   │  Lifecycle: Predict phase transitions
└──────┬──────┘  Resonance: Detect cross-domain alignment
       │          Weather: Generate memetic trajectories
       ↓
┌─────────────┐
│  NARRATIVE  │  Provenance bundles with evidence
└─────────────┘  Cascade sheets, contamination advisories
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from abraxas.core.provenance import Provenance
from abraxas.core.canonical import sha256_hex, canonical_json
from abraxas.core.temporal_tau import TauCalculator, TauSnapshot, ConfidenceLevel
from abraxas.slang.lifecycle import LifecycleEngine, LifecycleState as SlangLifecycleState, TransitionThresholds


@dataclass(frozen=True)
class OracleSignal:
    """Input signal to Oracle v2 pipeline."""

    domain: str
    subdomain: Optional[str]
    observations: List[str]  # Raw text observations
    tokens: List[str]  # Extracted tokens
    timestamp_utc: str
    source_id: Optional[str] = None  # Where did this come from?
    meta: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict) -> "OracleSignal":
        """Deserialize from dictionary."""
        return cls(
            domain=data["domain"],
            subdomain=data.get("subdomain"),
            observations=data["observations"],
            tokens=data["tokens"],
            timestamp_utc=data["timestamp_utc"],
            source_id=data.get("source_id"),
            meta=data.get("meta", {}),
        )


@dataclass(frozen=True)
class CompressionPhase:
    """Output of compression phase."""

    domain: str
    version: str  # DCE version used
    compressed_tokens: Dict[str, float]  # token → weight
    lifecycle_states: Dict[str, str]  # token → lifecycle state
    domain_signals: Tuple[str, ...]  # Signal types detected (e.g., "ideology_left")
    signal_strengths: Dict[str, float]  # signal_type → strength
    transparency_score: float  # STI
    affect_direction: str  # RDV: positive/negative/neutral
    provenance: Provenance

    @classmethod
    def from_dict(cls, data: Dict) -> "CompressionPhase":
        """Deserialize from dictionary."""
        prov_data = data["provenance"]
        provenance = Provenance(
            run_id=prov_data["run_id"],
            started_at_utc=prov_data["started_at_utc"],
            inputs_hash=prov_data["inputs_hash"],
            config_hash=prov_data["config_hash"],
            git_sha=prov_data.get("git_sha"),
            host=prov_data.get("host"),
        )
        return cls(
            domain=data["domain"],
            version=data["version"],
            compressed_tokens=data["compressed_tokens"],
            lifecycle_states=data["lifecycle_states"],
            domain_signals=tuple(data["domain_signals"]),
            signal_strengths=data["signal_strengths"],
            transparency_score=data["transparency_score"],
            affect_direction=data["affect_direction"],
            provenance=provenance,
        )


@dataclass(frozen=True)
class ForecastPhase:
    """Output of forecast phase."""

    # Lifecycle forecasting
    phase_transitions: Dict[str, str]  # token → predicted_next_state
    transition_probabilities: Dict[str, float]  # token → probability
    time_to_transition: Dict[str, float]  # token → estimated_hours

    # Resonance detection
    resonance_score: float  # [0, 1] - cross-domain alignment
    resonating_domains: Tuple[str, ...]  # Domains in resonance

    # Weather forecast
    weather_trajectory: str  # "compression_accelerating", "saturation_plateau", etc.
    memetic_pressure: float  # [0, 1]
    drift_velocity: float  # Change rate

    provenance: Provenance

    @classmethod
    def from_dict(cls, data: Dict) -> "ForecastPhase":
        """Deserialize from dictionary."""
        prov_data = data["provenance"]
        provenance = Provenance(
            run_id=prov_data["run_id"],
            started_at_utc=prov_data["started_at_utc"],
            inputs_hash=prov_data["inputs_hash"],
            config_hash=prov_data["config_hash"],
            git_sha=prov_data.get("git_sha"),
            host=prov_data.get("host"),
        )
        return cls(
            phase_transitions=data["phase_transitions"],
            transition_probabilities=data["transition_probabilities"],
            time_to_transition=data["time_to_transition"],
            resonance_score=data["resonance_score"],
            resonating_domains=tuple(data["resonating_domains"]),
            weather_trajectory=data["weather_trajectory"],
            memetic_pressure=data["memetic_pressure"],
            drift_velocity=data["drift_velocity"],
            provenance=provenance,
        )


@dataclass(frozen=True)
class NarrativePhase:
    """Output of narrative phase."""

    # Provenance bundle
    bundle_id: str  # Unique identifier
    bundle_hash: str  # SHA-256 of full bundle

    # Narrative components
    cascade_sheet: Dict[str, any]  # Tabular cascade summary
    contamination_advisory: Optional[Dict[str, any]]  # High-risk alerts
    trust_drift_series: List[Dict[str, float]]  # Time-series data

    # Evidence trail
    evidence_tokens: Tuple[str, ...]
    evidence_signals: Tuple[str, ...]
    evidence_transitions: Tuple[str, ...]

    # Human-readable
    narrative_summary: str
    confidence_band: str  # "LOW", "MED", "HIGH"

    provenance: Provenance

    @classmethod
    def from_dict(cls, data: Dict) -> "NarrativePhase":
        """Deserialize from dictionary."""
        prov_data = data["provenance"]
        provenance = Provenance(
            run_id=prov_data["run_id"],
            started_at_utc=prov_data["started_at_utc"],
            inputs_hash=prov_data["inputs_hash"],
            config_hash=prov_data["config_hash"],
            git_sha=prov_data.get("git_sha"),
            host=prov_data.get("host"),
        )
        return cls(
            bundle_id=data["bundle_id"],
            bundle_hash=data["bundle_hash"],
            cascade_sheet=data["cascade_sheet"],
            contamination_advisory=data.get("contamination_advisory"),
            trust_drift_series=data["trust_drift_series"],
            evidence_tokens=tuple(data["evidence_tokens"]),
            evidence_signals=tuple(data["evidence_signals"]),
            evidence_transitions=tuple(data["evidence_transitions"]),
            narrative_summary=data["narrative_summary"],
            confidence_band=data["confidence_band"],
            provenance=provenance,
        )


@dataclass(frozen=True)
class OracleV2Output:
    """Complete Oracle v2 pipeline output."""

    run_id: str
    signal: OracleSignal
    compression: CompressionPhase
    forecast: ForecastPhase
    narrative: NarrativePhase
    created_at_utc: str = field(default_factory=lambda: _utc_now_iso())
    pipeline_version: str = "2.0.0"

    @classmethod
    def from_dict(cls, data: Dict) -> "OracleV2Output":
        """Deserialize from dictionary."""
        return cls(
            run_id=data["run_id"],
            signal=OracleSignal.from_dict(data["signal"]),
            compression=CompressionPhase.from_dict(data["compression"]),
            forecast=ForecastPhase.from_dict(data["forecast"]),
            narrative=NarrativePhase.from_dict(data["narrative"]),
            created_at_utc=data.get("created_at_utc", _utc_now_iso()),
            pipeline_version=data.get("pipeline_version", "2.0.0"),
        )


class OracleV2Pipeline:
    """
    Oracle Pipeline v2

    Unified Signal → Compression → Forecast → Narrative flow.

    Components:
    - DCE: Domain compression with lifecycle awareness
    - Lifecycle: Phase transition forecasting
    - Resonance: Cross-domain alignment
    - Weather: Memetic trajectory prediction
    - Provenance: Evidence bundles with SHA-256 tracking
    """

    def __init__(
        self,
        dce_engine: any = None,  # DomainCompressionEngine
        lifecycle_engine: Optional[LifecycleEngine] = None,  # LifecycleEngine from slang
        tau_calculator: Optional[TauCalculator] = None,  # TauCalculator for lifecycle
        weather_config: Optional[Dict] = None,  # Weather configuration
    ) -> None:
        self._dce = dce_engine
        self._lifecycle = lifecycle_engine or LifecycleEngine()
        self._tau_calc = tau_calculator or TauCalculator()
        self._weather_config = weather_config or {}

    def process(self, signal: OracleSignal, run_id: str, git_sha: Optional[str] = None) -> OracleV2Output:
        """
        Process signal through full Oracle v2 pipeline.

        Args:
            signal: Input observations and tokens
            run_id: Run identifier for provenance
            git_sha: Git SHA for provenance

        Returns:
            Complete oracle output with all phases
        """
        # PHASE 1: COMPRESSION
        compression = self._compression_phase(signal, run_id, git_sha)

        # PHASE 2: FORECAST
        forecast = self._forecast_phase(compression, run_id, git_sha)

        # PHASE 3: NARRATIVE
        narrative = self._narrative_phase(compression, forecast, run_id, git_sha)

        return OracleV2Output(
            run_id=run_id,
            signal=signal,
            compression=compression,
            forecast=forecast,
            narrative=narrative,
        )

    def _compression_phase(
        self, signal: OracleSignal, run_id: str, git_sha: Optional[str]
    ) -> CompressionPhase:
        """
        Phase 1: Domain compression with lifecycle awareness.

        Uses DCE to:
        - Extract domain-specific signals
        - Calculate lifecycle states
        - Compute transparency (STI)
        - Determine affect direction (RDV)
        """
        # Real DCE integration if available
        if self._dce is not None:
            from abraxas.lexicon.pipeline import DCEPipelineInput, create_integrated_pipeline

            # Create integrated pipeline
            pipeline = create_integrated_pipeline(self._dce)

            # Create input
            dce_input = DCEPipelineInput(
                domain=signal.domain,
                tokens=signal.tokens,
                subdomain=signal.subdomain,
                run_id=run_id,
                git_sha=git_sha,
            )

            # Process through DCE pipeline
            dce_output = pipeline.process(
                dce_input,
                calculate_transparency=True,
                calculate_affect=True,
            )

            # Extract compression data
            compressed_tokens = dce_output.compression_result.weights_out
            lifecycle_states = {
                token: dce_output.compression_result.lifecycle_info.get(token, "proto")
                for token in compressed_tokens.keys()
            }

            # Convert domain signals to tuple of signal types
            domain_signals = tuple(sig.signal_type for sig in dce_output.domain_signals)
            signal_strengths = {sig.signal_type: sig.strength for sig in dce_output.domain_signals}

            transparency_score = dce_output.transparency_score or 0.5
            affect_direction = dce_output.affect_direction or "neutral"
            version = dce_output.version

        else:
            # Fallback: Placeholder compression when DCE not available
            compressed_tokens = {token: 0.5 for token in signal.tokens[:5]}
            lifecycle_states = {token: "Front" for token in compressed_tokens}  # Canonical PascalCase
            domain_signals = ("ideology_left",) if signal.domain == "politics" else ()
            signal_strengths = {"ideology_left": 0.7} if domain_signals else {}
            transparency_score = 0.75
            affect_direction = "neutral"
            version = "dce-v2.0-fallback"

        prov = Provenance(
            run_id=run_id,
            started_at_utc=Provenance.now_iso_z(),
            inputs_hash=sha256_hex(canonical_json({"signal": signal.tokens})),
            config_hash=sha256_hex(canonical_json({"phase": "compression"})),
            git_sha=git_sha,
        )

        return CompressionPhase(
            domain=signal.domain,
            version=version,
            compressed_tokens=compressed_tokens,
            lifecycle_states=lifecycle_states,
            domain_signals=domain_signals,
            signal_strengths=signal_strengths,
            transparency_score=transparency_score,
            affect_direction=affect_direction,
            provenance=prov,
        )

    def _forecast_phase(
        self, compression: CompressionPhase, run_id: str, git_sha: Optional[str]
    ) -> ForecastPhase:
        """
        Phase 2: Lifecycle forecasting + resonance + weather.

        Predicts:
        - Phase transitions (proto → front → saturated)
        - Cross-domain resonance
        - Memetic weather trajectories
        """
        # Lifecycle forecasting using real LifecycleEngine
        phase_transitions = {}
        transition_probs = {}
        time_to_transition = {}

        for token, state in compression.lifecycle_states.items():
            # DCE lifecycle states are now canonical slang LifecycleState
            current_state = SlangLifecycleState(state)

            # Get token weight for tau calculation
            weight = compression.compressed_tokens.get(token, 0.0)

            # Create tau snapshot (simplified - in production, use historical data)
            tau_snapshot = TauSnapshot(
                tau_half_life=self._estimate_half_life(weight, state),
                tau_velocity=self._estimate_velocity(weight, state),
                tau_phase_proximity=0.5,  # Simplified - would calculate from lifecycle position
                confidence=ConfidenceLevel.MED,
                observation_count=int(weight * 10),  # Proxy for observations
                observation_window_hours=168.0,  # 1 week window
                provenance=Provenance(
                    run_id=run_id,
                    started_at_utc=Provenance.now_iso_z(),
                    inputs_hash=sha256_hex(canonical_json({"token": token, "weight": weight})),
                    config_hash=sha256_hex(canonical_json({"estimator": "oracle_v2_tau"})),
                    git_sha=git_sha,
                ),
            )

            # Compute next state using lifecycle engine
            next_state = self._lifecycle.compute_state(
                current_state=current_state,
                tau_snapshot=tau_snapshot,
                mutation_evidence=None,
            )

            # Record transition if state changes
            if next_state != current_state:
                phase_transitions[token] = next_state.value

                # Estimate probability based on tau metrics
                prob = self._estimate_transition_probability(tau_snapshot, current_state, next_state)
                transition_probs[token] = prob

                # Estimate time based on velocity
                time_to_transition[token] = self._estimate_transition_time(tau_snapshot)

        # Resonance detection using signal strengths
        resonance_score = self._compute_resonance(compression)
        resonating_domains = self._detect_resonating_domains(compression)

        # Weather forecast using compression metrics
        weather_trajectory = self._compute_weather_trajectory(compression)
        memetic_pressure = self._compute_memetic_pressure(compression)
        drift_velocity = self._compute_drift_velocity(compression)

        prov = Provenance(
            run_id=run_id,
            started_at_utc=Provenance.now_iso_z(),
            inputs_hash=sha256_hex(
                canonical_json({"compression_hash": compression.provenance.inputs_hash})
            ),
            config_hash=sha256_hex(canonical_json({"phase": "forecast"})),
            git_sha=git_sha,
        )

        return ForecastPhase(
            phase_transitions=phase_transitions,
            transition_probabilities=transition_probs,
            time_to_transition=time_to_transition,
            resonance_score=resonance_score,
            resonating_domains=resonating_domains,
            weather_trajectory=weather_trajectory,
            memetic_pressure=memetic_pressure,
            drift_velocity=drift_velocity,
            provenance=prov,
        )

    def _narrative_phase(
        self,
        compression: CompressionPhase,
        forecast: ForecastPhase,
        run_id: str,
        git_sha: Optional[str],
    ) -> NarrativePhase:
        """
        Phase 3: Narrative generation with provenance bundles.

        Generates:
        - Cascade sheets
        - Contamination advisories
        - Trust drift time-series
        - Human-readable summaries
        """
        bundle_id = f"ORACLE-{run_id}-{_utc_now_iso()[:10]}"

        # Build provenance bundle
        bundle_data = {
            "compression": asdict(compression),
            "forecast": asdict(forecast),
            "run_id": run_id,
        }
        bundle_hash = sha256_hex(canonical_json(bundle_data))

        # Cascade sheet (simplified)
        cascade_sheet = {
            "token_count": len(compression.compressed_tokens),
            "lifecycle_distribution": _count_lifecycle_states(compression.lifecycle_states),
            "transition_forecast": len(forecast.phase_transitions),
        }

        # Contamination advisory (if high risk)
        contamination_advisory = None
        if forecast.memetic_pressure > 0.7:
            contamination_advisory = {
                "risk_level": "HIGH",
                "memetic_pressure": forecast.memetic_pressure,
                "trajectory": forecast.weather_trajectory,
            }

        # Trust drift series (simplified)
        trust_drift_series = [
            {"t": 0, "sti": compression.transparency_score},
            {"t": 24, "sti": compression.transparency_score * 0.95},
            {"t": 48, "sti": compression.transparency_score * 0.90},
        ]

        # Evidence trail
        evidence_tokens = tuple(compression.compressed_tokens.keys())
        evidence_signals = compression.domain_signals
        evidence_transitions = tuple(forecast.phase_transitions.keys())

        # Narrative summary
        narrative_summary = self._generate_narrative(compression, forecast)

        # Confidence band
        avg_prob = (
            sum(forecast.transition_probabilities.values()) / len(forecast.transition_probabilities)
            if forecast.transition_probabilities
            else 0.5
        )
        confidence_band = "HIGH" if avg_prob > 0.7 else ("MED" if avg_prob > 0.4 else "LOW")

        prov = Provenance(
            run_id=run_id,
            started_at_utc=Provenance.now_iso_z(),
            inputs_hash=bundle_hash,
            config_hash=sha256_hex(canonical_json({"phase": "narrative"})),
            git_sha=git_sha,
        )

        return NarrativePhase(
            bundle_id=bundle_id,
            bundle_hash=bundle_hash,
            cascade_sheet=cascade_sheet,
            contamination_advisory=contamination_advisory,
            trust_drift_series=trust_drift_series,
            evidence_tokens=evidence_tokens,
            evidence_signals=evidence_signals,
            evidence_transitions=evidence_transitions,
            narrative_summary=narrative_summary,
            confidence_band=confidence_band,
            provenance=prov,
        )

    def _generate_narrative(self, compression: CompressionPhase, forecast: ForecastPhase) -> str:
        """Generate human-readable narrative summary."""
        lines = []

        lines.append(f"Domain: {compression.domain}")
        lines.append(f"Tokens analyzed: {len(compression.compressed_tokens)}")

        if compression.domain_signals:
            lines.append(f"Signals detected: {', '.join(compression.domain_signals)}")

        lines.append(f"Transparency: {compression.transparency_score:.2f} (STI)")
        lines.append(f"Affect: {compression.affect_direction}")

        if forecast.phase_transitions:
            count = len(forecast.phase_transitions)
            lines.append(f"Forecast: {count} tokens transitioning")

        lines.append(f"Weather: {forecast.weather_trajectory}")
        lines.append(f"Memetic pressure: {forecast.memetic_pressure:.2f}")

        return " | ".join(lines)

    # Lifecycle forecasting helpers

    def _estimate_half_life(self, weight: float, state: str) -> float:
        """Estimate tau half-life based on weight and state."""
        # Higher weight = longer half-life (more persistent)
        # States now use canonical PascalCase from slang.lifecycle
        base_half_life = {
            "Proto": 24.0,  # 1 day
            "Front": 72.0,  # 3 days
            "Saturated": 168.0,  # 7 days
            "Dormant": 48.0,  # 2 days
            "Archived": 12.0,  # 12 hours
        }.get(state, 48.0)

        return base_half_life * (0.5 + weight)

    def _estimate_velocity(self, weight: float, state: str) -> float:
        """Estimate tau velocity based on weight and state."""
        # Velocity indicates growth/decay rate
        # States now use canonical PascalCase from slang.lifecycle
        velocity_map = {
            "Proto": 0.6,  # Growing
            "Front": 0.8,  # Rapidly growing
            "Saturated": 0.05,  # Stable
            "Dormant": -0.2,  # Declining
            "Archived": -0.5,  # Rapidly declining
        }.get(state, 0.0)

        # Weight modulates velocity
        return velocity_map * (0.5 + weight)

    def _estimate_transition_probability(
        self, tau: TauSnapshot, current: SlangLifecycleState, next_state: SlangLifecycleState
    ) -> float:
        """Estimate transition probability based on tau metrics."""
        # Base probability from velocity
        if tau.tau_velocity > 0.5:
            base_prob = 0.7  # High velocity = high transition prob
        elif tau.tau_velocity > 0.0:
            base_prob = 0.5
        elif tau.tau_velocity > -0.2:
            base_prob = 0.3
        else:
            base_prob = 0.6  # Rapid decline = high transition prob to dormant

        # Adjust by half-life (longer half-life = more stable = lower transition)
        if tau.tau_half_life > 100:
            base_prob *= 0.8
        elif tau.tau_half_life < 30:
            base_prob *= 1.2

        return min(1.0, max(0.0, base_prob))

    def _estimate_transition_time(self, tau: TauSnapshot) -> float:
        """Estimate hours to transition based on tau velocity."""
        # Higher velocity = faster transition
        if abs(tau.tau_velocity) > 0.5:
            return 24.0  # 1 day
        elif abs(tau.tau_velocity) > 0.2:
            return 48.0  # 2 days
        elif abs(tau.tau_velocity) > 0.05:
            return 96.0  # 4 days
        else:
            return 168.0  # 7 days (slow transition)

    # Resonance detection helpers

    def _compute_resonance(self, compression: CompressionPhase) -> float:
        """Compute resonance score from signal strengths."""
        if not compression.signal_strengths:
            return 0.0

        # Resonance = average signal strength
        strengths = list(compression.signal_strengths.values())
        return sum(strengths) / len(strengths)

    def _detect_resonating_domains(self, compression: CompressionPhase) -> Tuple[str, ...]:
        """Detect which domains are in resonance."""
        # Placeholder: In production, compare cross-domain signal patterns
        # For now, just return domain if high resonance
        resonance = self._compute_resonance(compression)
        if resonance > 0.6:
            return (compression.domain,)
        return ()

    # Weather forecasting helpers

    def _compute_weather_trajectory(self, compression: CompressionPhase) -> str:
        """Compute weather trajectory from compression metrics."""
        # Trajectory based on lifecycle distribution and signals
        # States now use canonical PascalCase from slang.lifecycle
        lifecycle_counts = _count_lifecycle_states(compression.lifecycle_states)

        proto_count = lifecycle_counts.get("Proto", 0)
        front_count = lifecycle_counts.get("Front", 0)
        saturated_count = lifecycle_counts.get("Saturated", 0)

        total = sum(lifecycle_counts.values())
        if total == 0:
            return "stable"

        # Compute ratios
        proto_ratio = proto_count / total
        front_ratio = front_count / total

        if proto_ratio > 0.4:
            return "emergence_accelerating"
        elif front_ratio > 0.5:
            return "compression_accelerating"
        elif saturated_count / total > 0.6:
            return "saturation_plateau"
        else:
            return "stable"

    def _compute_memetic_pressure(self, compression: CompressionPhase) -> float:
        """Compute memetic pressure from signal strengths."""
        # Pressure = weighted sum of signal strengths
        if not compression.signal_strengths:
            return 0.0

        total_strength = sum(compression.signal_strengths.values())
        num_signals = len(compression.signal_strengths)

        # Normalize to [0, 1]
        return min(1.0, total_strength / max(1, num_signals))

    def _compute_drift_velocity(self, compression: CompressionPhase) -> float:
        """Compute drift velocity from affect direction."""
        # Drift based on affect direction
        affect_map = {
            "positive": 0.2,
            "negative": -0.2,
            "neutral": 0.0,
        }
        return affect_map.get(compression.affect_direction, 0.0)


def _count_lifecycle_states(states: Dict[str, str]) -> Dict[str, int]:
    """Count tokens by lifecycle state."""
    counts: Dict[str, int] = {}
    for state in states.values():
        counts[state] = counts.get(state, 0) + 1
    return counts


def _utc_now_iso() -> str:
    """Generate ISO8601 timestamp with Zulu timezone (no microseconds)."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# Convenience function

def create_oracle_v2_pipeline() -> OracleV2Pipeline:
    """
    Create Oracle v2 pipeline with default components.

    Returns:
        Configured pipeline ready for use
    """
    # TODO: Wire up real DCE, lifecycle, resonance, weather engines
    return OracleV2Pipeline()
