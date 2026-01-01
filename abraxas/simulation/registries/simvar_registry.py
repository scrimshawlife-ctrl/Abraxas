"""Simulation Variable Registry: Canonical storage for latent world state variables.

Variables represent the hidden state that metrics observe through ABX-Runes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

@dataclass(frozen=True)
class PriorDistribution:
    """Prior distribution specification for variable initialization."""
    distribution_type: str
    parameters: Dict[str, Any]
    sml_source: Optional[Dict[str, str]] = None  # {paper_id, knob_mapping, confidence}

    def to_dict(self) -> Dict:
        result = {
            "distribution_type": self.distribution_type,
            "parameters": self.parameters,
        }
        if self.sml_source:
            result["sml_source"] = self.sml_source
        return result

    @staticmethod
    def from_dict(data: Dict) -> PriorDistribution:
        return PriorDistribution(
            distribution_type=data["distribution_type"],
            parameters=data["parameters"],
            sml_source=data.get("sml_source"),
        )


@dataclass(frozen=True)
class EvolutionModel:
    """Evolution model for variable dynamics."""
    update_rule: str
    deterministic: bool
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "update_rule": self.update_rule,
            "deterministic": self.deterministic,
            "parameters": self.parameters,
        }

    @staticmethod
    def from_dict(data: Dict) -> EvolutionModel:
        return EvolutionModel(
            update_rule=data["update_rule"],
            deterministic=data["deterministic"],
            parameters=data.get("parameters", {}),
        )


@dataclass(frozen=True)
class SimVarDefinition:
    """Simulation variable definition."""
    var_id: str
    version: str
    var_class: str
    var_type: str
    bounds: Dict[str, Any]
    prior_distribution: PriorDistribution
    evolution_model: EvolutionModel
    coupling_capacity: Dict[str, Any]  # {max_runes, allowed_metric_classes}
    layer: str  # "world" or "media"
    provenance: Dict[str, str]

    def __post_init__(self):
        # Validate var_id format
        if not self.var_id.islower() or not self.var_id.replace("_", "").isalnum():
            raise ValueError(f"var_id must be lowercase snake_case: {self.var_id}")

        # Validate version
        parts = self.version.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(f"version must be MAJOR.MINOR.PATCH: {self.version}")

        # Validate var_class
        valid_classes = {
            "classical_state",
            "belief_state",
            "context_operator",
            "interference_term",
            "persona_filter",
            "network_state",
            "community_structure",
            "link_probability_field",
            "media_actor_state",
            "strategy_profile",
            "payoff_field",
            "state_over_time",
            "conformity_pressure",
            "peer_influence_field",
        }
        if self.var_class not in valid_classes:
            raise ValueError(f"var_class must be in {valid_classes}")

        # Validate layer
        if self.layer not in {"world", "media"}:
            raise ValueError(f"layer must be 'world' or 'media': {self.layer}")

        # Validate coupling_capacity
        if "max_runes" not in self.coupling_capacity:
            raise ValueError("coupling_capacity must have 'max_runes'")
        if "allowed_metric_classes" not in self.coupling_capacity:
            raise ValueError("coupling_capacity must have 'allowed_metric_classes'")

    def to_dict(self) -> Dict:
        return {
            "var_id": self.var_id,
            "version": self.version,
            "var_class": self.var_class,
            "var_type": self.var_type,
            "bounds": self.bounds,
            "prior_distribution": self.prior_distribution.to_dict(),
            "evolution_model": self.evolution_model.to_dict(),
            "coupling_capacity": self.coupling_capacity,
            "layer": self.layer,
            "provenance": self.provenance,
        }

    @staticmethod
    def from_dict(data: Dict) -> SimVarDefinition:
        return SimVarDefinition(
            var_id=data["var_id"],
            version=data["version"],
            var_class=data["var_class"],
            var_type=data["var_type"],
            bounds=data["bounds"],
            prior_distribution=PriorDistribution.from_dict(data["prior_distribution"]),
            evolution_model=EvolutionModel.from_dict(data["evolution_model"]),
            coupling_capacity=data["coupling_capacity"],
            layer=data["layer"],
            provenance=data["provenance"],
        )


class SimVarRegistry:
    """Registry for all simulation variables."""

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or Path("data/simulation/simvars.json")
        self.vars: Dict[str, SimVarDefinition] = {}
        self._load()

    def _load(self):
        """Load variables from disk."""
        if not self.registry_path.exists():
            return

        with open(self.registry_path, "r") as f:
            data = json.load(f)

        for var_data in data.get("variables", []):
            var = SimVarDefinition.from_dict(var_data)
            self.vars[var.var_id] = var

    def save(self):
        """Save variables to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "variables": [v.to_dict() for v in self.vars.values()],
            "count": len(self.vars),
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def register(self, var: SimVarDefinition):
        """Register a new variable."""
        if var.var_id in self.vars:
            raise ValueError(f"Variable {var.var_id} already registered")

        self.vars[var.var_id] = var

    def get(self, var_id: str) -> Optional[SimVarDefinition]:
        """Retrieve variable by ID."""
        return self.vars.get(var_id)

    def list_all(self) -> List[SimVarDefinition]:
        """List all registered variables."""
        return list(self.vars.values())

    def get_by_layer(self, layer: str) -> List[SimVarDefinition]:
        """Get all variables in a specific layer."""
        return [v for v in self.vars.values() if v.layer == layer]

    def get_by_class(self, var_class: str) -> List[SimVarDefinition]:
        """Get all variables of a specific class."""
        return [v for v in self.vars.values() if v.var_class == var_class]
