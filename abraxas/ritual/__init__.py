"""Ritual System v1 Specification

Ritual System = Symbolic Modulation Layer

Position: On top of Oracle v2 + Phase Detection Engine
Purpose: Modulate phase transitions, resonance patterns, and symbolic dynamics
through structured ritual protocols.

Architecture:
- RitualEngine: Core execution engine for ritual protocols
- RitualProtocol: Structured symbolic operations (invocation, banishing, charging, etc.)
- ModulationTarget: What gets modulated (phase thresholds, tau parameters, resonance weights)
- EffectTracker: Provenance-tracked measurement of ritual effects

Deterministic, provenance-bearing, evidence-based.
No vibes. No magic without measurement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set  # noqa: F401

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.core.provenance import Provenance


class RitualType(Enum):
    """Types of ritual protocols."""
    PHASE_TRANSITION = "phase_transition"      # Modulate phase boundaries
    RESONANCE_AMPLIFICATION = "resonance_amplification"  # Boost/attenuate resonance
    TAU_RECALIBRATION = "tau_recalibration"    # Adjust tau calculation parameters
    DOMAIN_COUPLING = "domain_coupling"        # Modify cross-domain coupling
    CASCADE_SUPPRESSION = "cascade_suppression"  # Dampen cascade risk
    SYMBOLIC_ANCHORING = "symbolic_anchoring"  # Anchor symbolic state


class ModulationTarget(Enum):
    """What the ritual modulates."""
    PHASE_THRESHOLDS = "phase_thresholds"
    TAU_VELOCITY_WEIGHT = "tau_velocity_weight"
    TAU_HALFLIFE_BASE = "tau_halflife_base"
    RESONANCE_WEIGHTS = "resonance_weights"
    SYNCHRONICITY_LAG = "synchronicity_lag"
    CASCADE_THRESHOLD = "cascade_threshold"
    DOMAIN_WEIGHTS = "domain_weights"


@dataclass(frozen=True)
class RitualParameter:
    """Single ritual parameter with bounds and provenance."""
    target: ModulationTarget
    parameter_name: str
    baseline_value: float
    ritual_value: float
    min_value: float
    max_value: float
    units: str

    def to_dict(self) -> Dict:
        return {
            "target": self.target.value,
            "parameter_name": self.parameter_name,
            "baseline_value": self.baseline_value,
            "ritual_value": self.ritual_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "units": self.units,
        }

    def validate(self) -> bool:
        """Check if ritual value is within bounds."""
        return self.min_value <= self.ritual_value <= self.max_value


@dataclass(frozen=True)
class RitualProtocol:
    """Structured ritual protocol definition."""
    protocol_id: str
    name: str
    ritual_type: RitualType
    description: str
    parameters: List[RitualParameter]
    preconditions: Dict[str, Any]  # Required state before ritual
    postconditions: Dict[str, Any]  # Expected state after ritual
    duration_hours: float  # How long ritual effect persists
    cooldown_hours: float  # Minimum time before repeat

    def to_dict(self) -> Dict:
        return {
            "protocol_id": self.protocol_id,
            "name": self.name,
            "ritual_type": self.ritual_type.value,
            "description": self.description,
            "parameters": [p.to_dict() for p in self.parameters],
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "duration_hours": self.duration_hours,
            "cooldown_hours": self.cooldown_hours,
        }


@dataclass(frozen=True)
class RitualExecution:
    """Record of a ritual execution."""
    execution_id: str
    protocol_id: str
    timestamp_utc: str
    operator: str
    parameters_applied: Dict[str, float]  # parameter_name -> value
    pre_state: Dict[str, Any]  # System state before
    post_state: Dict[str, Any]  # System state after (measured)
    provenance: Provenance
    success: bool
    effect_magnitude: float  # Measured effect size [0, 1]

    def to_dict(self) -> Dict:
        return {
            "execution_id": self.execution_id,
            "protocol_id": self.protocol_id,
            "timestamp_utc": self.timestamp_utc,
            "operator": self.operator,
            "parameters_applied": self.parameters_applied,
            "pre_state": self.pre_state,
            "post_state": self.post_state,
            "provenance": self.provenance.__dict__ if self.provenance else None,
            "success": self.success,
            "effect_magnitude": self.effect_magnitude,
        }


@dataclass
class EffectTracker:
    """Tracks ritual effects over time with provenance."""
    executions: List[RitualExecution] = field(default_factory=list)

    def add_execution(self, execution: RitualExecution) -> None:
        self.executions.append(execution)

    def get_executions_for_protocol(self, protocol_id: str) -> List[RitualExecution]:
        return [e for e in self.executions if e.protocol_id == protocol_id]

    def get_effect_history(self, protocol_id: str) -> List[Dict]:
        executions = self.get_executions_for_protocol(protocol_id)
        return [
            {
                "timestamp": e.timestamp_utc,
                "success": e.success,
                "effect_magnitude": e.effect_magnitude,
                "parameters": e.parameters_applied,
            }
            for e in executions
        ]

    def compute_average_effect(self, protocol_id: str) -> float:
        executions = self.get_executions_for_protocol(protocol_id)
        if not executions:
            return 0.0
        return sum(e.effect_magnitude for e in executions) / len(executions)

    def to_dict(self) -> Dict:
        return {
            "total_executions": len(self.executions),
            "by_protocol": {
                protocol_id: self.get_effect_history(protocol_id)
                for protocol_id in set(e.protocol_id for e in self.executions)
            },
            "average_effects": {
                protocol_id: self.compute_average_effect(protocol_id)
                for protocol_id in set(e.protocol_id for e in self.executions)
            },
        }


# Default Ritual Protocols
def create_default_protocols() -> Dict[str, RitualProtocol]:
    """Create standard ritual protocols."""

    protocols = {}

    # Phase Transition Modulation
    protocols["phase_advance"] = RitualProtocol(
        protocol_id="RIT-PHASE-ADVANCE-001",
        name="Phase Advance Ritual",
        ritual_type=RitualType.PHASE_TRANSITION,
        description="Accelerate domain phase transition by lowering phase thresholds",
        parameters=[
            RitualParameter(
                target=ModulationTarget.PHASE_THRESHOLDS,
                parameter_name="front_to_saturated_threshold",
                baseline_value=0.7,
                ritual_value=0.6,
                min_value=0.4,
                max_value=0.9,
                units="tau_phase_proximity",
            ),
            RitualParameter(
                target=ModulationTarget.TAU_VELOCITY_WEIGHT,
                parameter_name="velocity_amplification",
                baseline_value=1.0,
                ritual_value=1.3,
                min_value=0.5,
                max_value=2.0,
                units="multiplier",
            ),
        ],
        preconditions={"domain_phase": "front", "tau_velocity": ">0.3"},
        postconditions={"expected_phase": "saturated", "time_reduction_hours": 24},
        duration_hours=48.0,
        cooldown_hours=168.0,  # 1 week
    )

    protocols["phase_stabilize"] = RitualProtocol(
        protocol_id="RIT-PHASE-STABILIZE-001",
        name="Phase Stabilization Ritual",
        ritual_type=RitualType.PHASE_TRANSITION,
        description="Stabilize current phase by increasing half-life and reducing velocity sensitivity",
        parameters=[
            RitualParameter(
                target=ModulationTarget.TAU_HALFLIFE_BASE,
                parameter_name="halflife_extension",
                baseline_value=1.0,
                ritual_value=1.5,
                min_value=1.0,
                max_value=3.0,
                units="multiplier",
            ),
            RitualParameter(
                target=ModulationTarget.TAU_VELOCITY_WEIGHT,
                parameter_name="velocity_dampening",
                baseline_value=1.0,
                ritual_value=0.7,
                min_value=0.3,
                max_value=1.0,
                units="multiplier",
            ),
        ],
        preconditions={"domain_phase": "saturated", "stability_risk": "high"},
        postconditions={"expected_phase": "saturated", "stability_increase": 0.3},
        duration_hours=72.0,
        cooldown_hours=168.0,
    )

    # Resonance Amplification
    protocols["resonance_boost"] = RitualProtocol(
        protocol_id="RIT-RESONANCE-BOOST-001",
        name="Resonance Boost Ritual",
        ritual_type=RitualType.RESONANCE_AMPLIFICATION,
        description="Amplify resonance between aligned domains",
        parameters=[
            RitualParameter(
                target=ModulationTarget.RESONANCE_WEIGHTS,
                parameter_name="cross_domain_resonance_gain",
                baseline_value=1.0,
                ritual_value=1.5,
                min_value=0.5,
                max_value=3.0,
                units="multiplier",
            ),
        ],
        preconditions={"alignment_strength": ">0.5", "domains_aligned": ">=2"},
        postconditions={"alignment_strength_increase": 0.2},
        duration_hours=24.0,
        cooldown_hours=72.0,
    )

    # Tau Recalibration
    protocols["tau_recalibrate"] = RitualProtocol(
        protocol_id="RIT-TAU-RECALIBRATE-001",
        name="Tau Recalibration Ritual",
        ritual_type=RitualType.TAU_RECALIBRATION,
        description="Recalibrate tau calculation parameters for current conditions",
        parameters=[
            RitualParameter(
                target=ModulationTarget.TAU_HALFLIFE_BASE,
                parameter_name="base_halflife_hours",
                baseline_value=48.0,
                ritual_value=36.0,
                min_value=12.0,
                max_value=168.0,
                units="hours",
            ),
            RitualParameter(
                target=ModulationTarget.TAU_VELOCITY_WEIGHT,
                parameter_name="velocity_sensitivity",
                baseline_value=1.0,
                ritual_value=1.2,
                min_value=0.5,
                max_value=2.0,
                units="multiplier",
            ),
        ],
        preconditions={"observation_count": ">=10", "confidence": "MED_or_HIGHER"},
        postconditions={"calibration_improved": True},
        duration_hours=168.0,  # 1 week
        cooldown_hours=672.0,  # 4 weeks
    )

    # Domain Coupling
    protocols["domain_couple"] = RitualProtocol(
        protocol_id="RIT-DOMAIN-COUPLE-001",
        name="Domain Coupling Ritual",
        ritual_type=RitualType.DOMAIN_COUPLING,
        description="Strengthen or weaken coupling between specific domains",
        parameters=[
            RitualParameter(
                target=ModulationTarget.DOMAIN_WEIGHTS,
                parameter_name="coupling_strength",
                baseline_value=0.5,
                ritual_value=0.8,
                min_value=0.0,
                max_value=1.0,
                units="weight",
            ),
            RitualParameter(
                target=ModulationTarget.SYNCHRONICITY_LAG,
                parameter_name="expected_lag_reduction",
                baseline_value=0.0,
                ritual_value=12.0,
                min_value=0.0,
                max_value=72.0,
                units="hours",
            ),
        ],
        preconditions={"source_domain": "leading", "target_domain": "following"},
        postconditions={"coupling_increased": True, "lag_reduced_hours": 12},
        duration_hours=96.0,
        cooldown_hours=168.0,
    )

    # Cascade Suppression
    protocols["cascade_suppress"] = RitualProtocol(
        protocol_id="RIT-CASCADE-SUPPRESS-001",
        name="Cascade Suppression Ritual",
        ritual_type=RitualType.CASCADE_SUPPRESSION,
        description="Suppress memetic cascade risk by raising cascade threshold",
        parameters=[
            RitualParameter(
                target=ModulationTarget.CASCADE_THRESHOLD,
                parameter_name="cascade_risk_threshold",
                baseline_value=0.7,
                ritual_value=0.85,
                min_value=0.6,
                max_value=0.95,
                units="probability",
            ),
            RitualParameter(
                target=ModulationTarget.RESONANCE_WEIGHTS,
                parameter_name="drift_resonance_dampening",
                baseline_value=1.0,
                ritual_value=0.6,
                min_value=0.2,
                max_value=1.0,
                units="multiplier",
            ),
        ],
        preconditions={"cascade_risk": "HIGH_or_CRITICAL", "drift_resonance_detected": True},
        postconditions={"cascade_risk_reduction": "MEDIUM_or_LOWER"},
        duration_hours=72.0,
        cooldown_hours=168.0,
    )

    # Symbolic Anchoring
    protocols["symbolic_anchor"] = RitualProtocol(
        protocol_id="RIT-SYMBOLIC-ANCHOR-001",
        name="Symbolic Anchoring Ritual",
        ritual_type=RitualType.SYMBOLIC_ANCHORING,
        description="Anchor current symbolic state against drift",
        parameters=[
            RitualParameter(
                target=ModulationTarget.PHASE_THRESHOLDS,
                parameter_name="anchor_strength",
                baseline_value=0.0,
                ritual_value=0.8,
                min_value=0.0,
                max_value=1.0,
                units="strength",
            ),
        ],
        preconditions={"symbolic_state": "coherent", "drift_detected": True},
        postconditions={"drift_reduced": True, "coherence_maintained": True},
        duration_hours=168.0,  # 1 week
        cooldown_hours=336.0,  # 2 weeks
    )

    return protocols


class RitualEngine:
    """Core ritual execution engine."""

    def __init__(
        self,
        protocols: Optional[Dict[str, RitualProtocol]] = None,
        effect_tracker: Optional[EffectTracker] = None,
    ) -> None:
        self._protocols = protocols or create_default_protocols()
        self._effect_tracker = effect_tracker or EffectTracker()
        self._active_modulations: Dict[str, Dict[str, float]] = {}  # target -> {param -> value}
        self._modulation_expiry: Dict[str, datetime] = {}

    def get_protocol(self, protocol_id: str) -> Optional[RitualProtocol]:
        # Try exact match first (short name)
        protocol = self._protocols.get(protocol_id)
        if protocol:
            return protocol
        # Try by protocol_id field
        for p in self._protocols.values():
            if p.protocol_id == protocol_id:
                return p
        return None

    def list_protocols(self, ritual_type: Optional[RitualType] = None) -> List[RitualProtocol]:
        if ritual_type:
            return [p for p in self._protocols.values() if p.ritual_type == ritual_type]
        return list(self._protocols.values())

    def check_preconditions(
        self, protocol: RitualProtocol, current_state: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """Check if ritual preconditions are met."""
        failures = []

        # Check domain phase
        if "domain_phase" in protocol.preconditions:
            required = protocol.preconditions["domain_phase"]
            actual = current_state.get("domain_phase", "unknown")
            if required != actual:
                failures.append(f"domain_phase: expected {required}, got {actual}")

        # Check tau velocity
        if "tau_velocity" in protocol.preconditions:
            required = protocol.preconditions["tau_velocity"]
            actual = current_state.get("tau_velocity", 0.0)
            # Simple comparison for ">0.3" format
            if required.startswith(">") and actual <= float(required[1:]):
                failures.append(f"tau_velocity: expected {required}, got {actual}")

        # Check alignment strength
        if "alignment_strength" in protocol.preconditions:
            required = protocol.preconditions["alignment_strength"]
            actual = current_state.get("alignment_strength", 0.0)
            if required.startswith(">") and actual <= float(required[1:]):
                failures.append(f"alignment_strength: expected {required}, got {actual}")

        # Check domains aligned
        if "domains_aligned" in protocol.preconditions:
            required = protocol.preconditions["domains_aligned"]
            actual = current_state.get("domains_aligned", 0)
            if required.startswith(">=") and actual < int(required[2:]):
                failures.append(f"domains_aligned: expected {required}, got {actual}")

        # Check cascade risk
        if "cascade_risk" in protocol.preconditions:
            required = protocol.preconditions["cascade_risk"]
            actual = current_state.get("cascade_risk", "LOW")
            if required == "HIGH_or_CRITICAL" and actual not in ("HIGH", "CRITICAL"):
                failures.append(f"cascade_risk: expected HIGH_or_CRITICAL, got {actual}")

        # Check drift resonance
        if "drift_resonance_detected" in protocol.preconditions:
            required = protocol.preconditions["drift_resonance_detected"]
            actual = current_state.get("drift_resonance_detected", False)
            if required != actual:
                failures.append(f"drift_resonance_detected: expected {required}, got {actual}")

        # Check observation count
        if "observation_count" in protocol.preconditions:
            required = protocol.preconditions["observation_count"]
            actual = current_state.get("observation_count", 0)
            if required.startswith(">=") and actual < int(required[2:]):
                failures.append(f"observation_count: expected {required}, got {actual}")

        # Check confidence
        if "confidence" in protocol.preconditions:
            required = protocol.preconditions["confidence"]
            actual = current_state.get("confidence", "LOW")
            if required == "MED_or_HIGHER" and actual not in ("MED", "HIGH"):
                failures.append(f"confidence: expected MED_or_HIGHER, got {actual}")

        # Check symbolic state
        if "symbolic_state" in protocol.preconditions:
            required = protocol.preconditions["symbolic_state"]
            actual = current_state.get("symbolic_state", "unknown")
            if required != actual:
                failures.append(f"symbolic_state: expected {required}, got {actual}")

        # Check drift detected
        if "drift_detected" in protocol.preconditions:
            required = protocol.preconditions["drift_detected"]
            actual = current_state.get("drift_detected", False)
            if required != actual:
                failures.append(f"drift_detected: expected {required}, got {actual}")

        # Check source/target domain
        if "source_domain" in protocol.preconditions:
            required = protocol.preconditions["source_domain"]
            actual = current_state.get("source_domain_role", "unknown")
            if required != actual:
                failures.append(f"source_domain: expected {required}, got {actual}")

        if "target_domain" in protocol.preconditions:
            required = protocol.preconditions["target_domain"]
            actual = current_state.get("target_domain_role", "unknown")
            if required != actual:
                failures.append(f"target_domain: expected {required}, got {actual}")

        return len(failures) == 0, failures

    def execute_ritual(
        self,
        protocol_id: str,
        operator: str,
        current_state: Dict[str, Any],
        timestamp_utc: Optional[str] = None,
    ) -> RitualExecution:
        """Execute a ritual protocol."""
        protocol = self._protocols.get(protocol_id)
        if not protocol:
            raise ValueError(f"Unknown protocol: {protocol_id}")

        if timestamp_utc is None:
            timestamp_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Check preconditions
        preconditions_met, failures = self.check_preconditions(protocol, current_state)
        if not preconditions_met:
            raise ValueError(f"Preconditions not met: {failures}")

        # Validate parameters
        for param in protocol.parameters:
            if not param.validate():
                raise ValueError(f"Parameter {param.parameter_name} value out of bounds")

        # Capture pre-state
        pre_state = {
            "timestamp": timestamp_utc,
            "system_state": current_state.copy(),
            "active_modulations": self._active_modulations.copy(),
        }

        # Apply modulations
        parameters_applied = {}
        for param in protocol.parameters:
            key = f"{param.target.value}.{param.parameter_name}"
            self._active_modulations.setdefault(param.target.value, {})[param.parameter_name] = param.ritual_value
            parameters_applied[param.parameter_name] = param.ritual_value

            # Set expiry
            expiry = datetime.fromisoformat(timestamp_utc.replace("Z", "+00:00"))
            from datetime import timedelta
            expiry += timedelta(hours=protocol.duration_hours)
            self._modulation_expiry[key] = expiry

        # Create provenance
        prov = Provenance(
            run_id=f"ritual-{protocol.protocol_id}",
            started_at_utc=timestamp_utc,
            inputs_hash=sha256_hex(canonical_json({
                "protocol_id": protocol.protocol_id,
                "operator": operator,
                "parameters": parameters_applied,
                "pre_state": current_state,
            })),
            config_hash=sha256_hex(canonical_json(protocol.to_dict())),
        )

        # For now, simulate post-state (in production, measure actual system state after duration)
        post_state = {
            "timestamp": timestamp_utc,
            "system_state": current_state.copy(),
            "active_modulations": self._active_modulations.copy(),
            "modulations_applied": parameters_applied,
        }

        # Calculate effect magnitude (simulated based on parameter changes)
        effect_magnitude = self._calculate_effect_magnitude(protocol, parameters_applied)

        # Create execution record
        execution = RitualExecution(
            execution_id=f"EXEC-{protocol.protocol_id}-{timestamp_utc[:10]}",
            protocol_id=protocol.protocol_id,
            timestamp_utc=timestamp_utc,
            operator=operator,
            parameters_applied=parameters_applied,
            pre_state=pre_state,
            post_state=post_state,
            provenance=prov,
            success=True,
            effect_magnitude=effect_magnitude,
        )

        self._effect_tracker.add_execution(execution)
        return execution

    def _calculate_effect_magnitude(
        self, protocol: RitualProtocol, parameters_applied: Dict[str, float]
    ) -> float:
        """Calculate expected effect magnitude based on parameter changes."""
        total_change = 0.0
        for param in protocol.parameters:
            applied = parameters_applied.get(param.parameter_name, param.baseline_value)
            change = abs(applied - param.baseline_value) / max(abs(param.baseline_value), 0.001)
            total_change += change
        # Normalize by number of parameters
        return min(1.0, total_change / len(protocol.parameters))

    def get_active_modulations(self) -> Dict[str, Dict[str, float]]:
        """Get currently active modulations."""
        # Clean expired
        now = datetime.now(timezone.utc)
        expired_keys = [
            k for k, v in self._modulation_expiry.items()
            if v < now
        ]
        for k in expired_keys:
            target, param = k.split(".", 1)
            if target in self._active_modulations and param in self._active_modulations[target]:
                del self._active_modulations[target][param]
            del self._modulation_expiry[k]
        return self._active_modulations

    def get_effect_tracker(self) -> EffectTracker:
        return self._effect_tracker


def create_ritual_engine() -> RitualEngine:
    """Create ritual engine with default protocols."""
    return RitualEngine()
