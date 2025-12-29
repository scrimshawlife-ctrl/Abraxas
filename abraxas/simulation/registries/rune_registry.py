"""ABX-Rune Binding Registry: MANDATORY coupler between metrics and simulation variables.

IMMUTABLE LAW: No Simulation Without Runes.
All metric ⇄ simulation variable couplings MUST occur through ABX-Runes.
No direct metric → variable mutation is allowed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

@dataclass(frozen=True)
class VarTarget:
    """Variable target for rune binding."""
    var_id: str
    role: str  # "observe", "influence", or "both"

    def to_dict(self) -> Dict:
        return {"var_id": self.var_id, "role": self.role}

    @staticmethod
    def from_dict(data: Dict) -> VarTarget:
        return VarTarget(var_id=data["var_id"], role=data["role"])


@dataclass(frozen=True)
class ObserverModel:
    """Observer model: how metric reads variable state."""
    observer_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {"observer_type": self.observer_type, "parameters": self.parameters}

    @staticmethod
    def from_dict(data: Dict) -> ObserverModel:
        return ObserverModel(
            observer_type=data["observer_type"],
            parameters=data.get("parameters", {}),
        )


@dataclass(frozen=True)
class TransitionModel:
    """Transition model: how metric updates variable state."""
    transition_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {"transition_type": self.transition_type, "parameters": self.parameters}

    @staticmethod
    def from_dict(data: Dict) -> TransitionModel:
        return TransitionModel(
            transition_type=data["transition_type"],
            parameters=data.get("parameters", {}),
        )


@dataclass(frozen=True)
class NoiseModel:
    """Noise model: measurement uncertainty."""
    noise_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {"noise_type": self.noise_type, "parameters": self.parameters}

    @staticmethod
    def from_dict(data: Dict) -> NoiseModel:
        return NoiseModel(
            noise_type=data["noise_type"],
            parameters=data.get("parameters", {}),
        )


@dataclass(frozen=True)
class ManipulationModel:
    """Manipulation model: how manipulation distorts measurement."""
    manipulation_type: str
    penetration_scaling: float
    detection_threshold: float = 0.5

    def to_dict(self) -> Dict:
        return {
            "manipulation_type": self.manipulation_type,
            "penetration_scaling": self.penetration_scaling,
            "detection_threshold": self.detection_threshold,
        }

    @staticmethod
    def from_dict(data: Dict) -> ManipulationModel:
        return ManipulationModel(
            manipulation_type=data["manipulation_type"],
            penetration_scaling=data["penetration_scaling"],
            detection_threshold=data.get("detection_threshold", 0.5),
        )


@dataclass(frozen=True)
class ProvenanceManifest:
    """Provenance manifest for rune binding."""
    created: str
    input_hash: str
    metric_version: str
    var_versions: Dict[str, str]
    schema_version: str
    sml_training_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "created": self.created,
            "input_hash": self.input_hash,
            "metric_version": self.metric_version,
            "var_versions": self.var_versions,
            "schema_version": self.schema_version,
            "sml_training_sources": self.sml_training_sources,
        }

    @staticmethod
    def from_dict(data: Dict) -> ProvenanceManifest:
        return ProvenanceManifest(
            created=data["created"],
            input_hash=data["input_hash"],
            metric_version=data["metric_version"],
            var_versions=data["var_versions"],
            schema_version=data["schema_version"],
            sml_training_sources=data.get("sml_training_sources", []),
        )


@dataclass(frozen=True)
class RuneBinding:
    """ABX-Rune binding definition.

    MANDATORY fields enforce coupling contract.
    """
    rune_id: str
    version: str
    metric_id: str
    var_targets: List[VarTarget]
    layer_targets: List[str]
    state_model: str
    measurement_effect: str
    context_sensitivity: float
    observer_model: ObserverModel
    transition_model: TransitionModel
    noise_model: NoiseModel
    manipulation_model: ManipulationModel
    constraints: Dict[str, Any]
    provenance_manifest: ProvenanceManifest

    def __post_init__(self):
        # Validate rune_id format
        if not self.rune_id.startswith("RUNE_"):
            raise ValueError(f"rune_id must start with 'RUNE_': {self.rune_id}")

        # Validate context_sensitivity
        if not 0 <= self.context_sensitivity <= 1:
            raise ValueError(f"context_sensitivity must be in [0,1]: {self.context_sensitivity}")

        # Validate state_model
        if self.state_model not in {"classical", "quantum-inspired", "hybrid"}:
            raise ValueError(f"Invalid state_model: {self.state_model}")

        # Validate measurement_effect
        valid_effects = {"non-destructive", "partial-collapse", "hard-collapse"}
        if self.measurement_effect not in valid_effects:
            raise ValueError(f"measurement_effect must be in {valid_effects}")

        # Validate layer_targets
        if not all(layer in {"world", "media"} for layer in self.layer_targets):
            raise ValueError("layer_targets must be subset of {'world', 'media'}")

        # Validate var_targets
        if not self.var_targets:
            raise ValueError("var_targets cannot be empty")

        for target in self.var_targets:
            if target.role not in {"observe", "influence", "both"}:
                raise ValueError(f"Invalid target role: {target.role}")

    def to_dict(self) -> Dict:
        return {
            "rune_id": self.rune_id,
            "version": self.version,
            "metric_id": self.metric_id,
            "var_targets": [t.to_dict() for t in self.var_targets],
            "layer_targets": self.layer_targets,
            "state_model": self.state_model,
            "measurement_effect": self.measurement_effect,
            "context_sensitivity": self.context_sensitivity,
            "observer_model": self.observer_model.to_dict(),
            "transition_model": self.transition_model.to_dict(),
            "noise_model": self.noise_model.to_dict(),
            "manipulation_model": self.manipulation_model.to_dict(),
            "constraints": self.constraints,
            "provenance_manifest": self.provenance_manifest.to_dict(),
        }

    @staticmethod
    def from_dict(data: Dict) -> RuneBinding:
        return RuneBinding(
            rune_id=data["rune_id"],
            version=data["version"],
            metric_id=data["metric_id"],
            var_targets=[VarTarget.from_dict(t) for t in data["var_targets"]],
            layer_targets=data["layer_targets"],
            state_model=data["state_model"],
            measurement_effect=data["measurement_effect"],
            context_sensitivity=data["context_sensitivity"],
            observer_model=ObserverModel.from_dict(data["observer_model"]),
            transition_model=TransitionModel.from_dict(data["transition_model"]),
            noise_model=NoiseModel.from_dict(data["noise_model"]),
            manipulation_model=ManipulationModel.from_dict(data["manipulation_model"]),
            constraints=data["constraints"],
            provenance_manifest=ProvenanceManifest.from_dict(data["provenance_manifest"]),
        )

    def compute_input_hash(self) -> str:
        """Compute SHA-256 hash of rune configuration for provenance."""
        # Exclude provenance_manifest itself from hash
        config = {
            "rune_id": self.rune_id,
            "version": self.version,
            "metric_id": self.metric_id,
            "var_targets": [t.to_dict() for t in self.var_targets],
            "layer_targets": self.layer_targets,
            "state_model": self.state_model,
            "measurement_effect": self.measurement_effect,
            "context_sensitivity": self.context_sensitivity,
            "observer_model": self.observer_model.to_dict(),
            "transition_model": self.transition_model.to_dict(),
            "noise_model": self.noise_model.to_dict(),
            "manipulation_model": self.manipulation_model.to_dict(),
            "constraints": self.constraints,
        }
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()


class RuneRegistry:
    """Registry for all ABX-Rune bindings."""

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or Path("data/simulation/runes.json")
        self.runes: Dict[str, RuneBinding] = {}
        self._load()

    def _load(self):
        """Load runes from disk."""
        if not self.registry_path.exists():
            return

        with open(self.registry_path, "r") as f:
            data = json.load(f)

        for rune_data in data.get("runes", []):
            rune = RuneBinding.from_dict(rune_data)
            self.runes[rune.rune_id] = rune

    def save(self):
        """Save runes to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "runes": [r.to_dict() for r in self.runes.values()],
            "count": len(self.runes),
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def register(self, rune: RuneBinding):
        """Register a new rune binding."""
        if rune.rune_id in self.runes:
            raise ValueError(f"Rune {rune.rune_id} already registered")

        self.runes[rune.rune_id] = rune

    def get(self, rune_id: str) -> Optional[RuneBinding]:
        """Retrieve rune by ID."""
        return self.runes.get(rune_id)

    def list_all(self) -> List[RuneBinding]:
        """List all registered runes."""
        return list(self.runes.values())

    def get_runes_for_metric(self, metric_id: str) -> List[RuneBinding]:
        """Get all runes bound to a specific metric."""
        return [r for r in self.runes.values() if r.metric_id == metric_id]

    def get_runes_for_var(self, var_id: str) -> List[RuneBinding]:
        """Get all runes that target a specific variable."""
        result = []
        for rune in self.runes.values():
            if any(t.var_id == var_id for t in rune.var_targets):
                result.append(rune)
        return result

    def validate_coupling(self, metric_registry, simvar_registry) -> List[str]:
        """Validate all rune bindings against metric and variable registries.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        for rune in self.runes.values():
            # Check metric exists
            if not metric_registry.get(rune.metric_id):
                errors.append(f"{rune.rune_id}: metric {rune.metric_id} not found")

            # Check all vars exist
            for target in rune.var_targets:
                if not simvar_registry.get(target.var_id):
                    errors.append(f"{rune.rune_id}: var {target.var_id} not found")

        return errors
