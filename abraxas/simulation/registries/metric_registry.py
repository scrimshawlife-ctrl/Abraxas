"""Metric Registry: Canonical storage for all Abraxas metrics.

IMMUTABLE LAW: Every metric MUST map to ≥1 simulation variable via ABX-Runes.
Orphan metrics (no rune binding) are rejected at startup.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

@dataclass(frozen=True)
class MetricProvenance:
    """Provenance tracking for metrics."""
    created: str  # ISO 8601
    source: str
    paper_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "created": self.created,
            "source": self.source,
            "paper_refs": self.paper_refs,
        }

    @staticmethod
    def from_dict(data: Dict) -> MetricProvenance:
        return MetricProvenance(
            created=data["created"],
            source=data["source"],
            paper_refs=data.get("paper_refs", []),
        )


@dataclass(frozen=True)
class MetricDefinition:
    """Canonical metric definition.

    All metrics must be observations that bind to simulation variables.
    Direct metric→variable mutation is prohibited.
    """
    metric_id: str
    version: str
    description: str
    metric_class: str  # integrity_risk, manipulation_risk, network_topology, etc.
    units: str
    valid_range: Dict[str, float]  # {"min": ..., "max": ...}
    decay_half_life: float  # hours
    dependencies: List[str]
    adversarial_risk: float  # [0,1]
    layer_scope: List[str]  # ["world"] or ["media"] or ["world", "media"]
    provenance: MetricProvenance

    def __post_init__(self):
        # Validate metric_id format
        if not self.metric_id.isupper() or not self.metric_id.replace("_", "").isalnum():
            raise ValueError(f"metric_id must be uppercase snake_case: {self.metric_id}")

        # Validate version
        parts = self.version.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(f"version must be MAJOR.MINOR.PATCH: {self.version}")

        # Validate ranges
        if self.adversarial_risk < 0 or self.adversarial_risk > 1:
            raise ValueError(f"adversarial_risk must be in [0,1]: {self.adversarial_risk}")

        if "min" not in self.valid_range or "max" not in self.valid_range:
            raise ValueError("valid_range must have 'min' and 'max' keys")

        if self.valid_range["min"] >= self.valid_range["max"]:
            raise ValueError("valid_range min must be < max")

        # Validate layer_scope
        valid_layers = {"world", "media"}
        if not all(layer in valid_layers for layer in self.layer_scope):
            raise ValueError(f"layer_scope must be subset of {valid_layers}")

        if not self.layer_scope:
            raise ValueError("layer_scope cannot be empty")

    def to_dict(self) -> Dict:
        return {
            "metric_id": self.metric_id,
            "version": self.version,
            "description": self.description,
            "metric_class": self.metric_class,
            "units": self.units,
            "valid_range": self.valid_range,
            "decay_half_life": self.decay_half_life,
            "dependencies": self.dependencies,
            "adversarial_risk": self.adversarial_risk,
            "layer_scope": self.layer_scope,
            "provenance": self.provenance.to_dict(),
        }

    @staticmethod
    def from_dict(data: Dict) -> MetricDefinition:
        return MetricDefinition(
            metric_id=data["metric_id"],
            version=data["version"],
            description=data["description"],
            metric_class=data["metric_class"],
            units=data["units"],
            valid_range=data["valid_range"],
            decay_half_life=data["decay_half_life"],
            dependencies=data["dependencies"],
            adversarial_risk=data["adversarial_risk"],
            layer_scope=data["layer_scope"],
            provenance=MetricProvenance.from_dict(data["provenance"]),
        )


class MetricRegistry:
    """Registry for all metrics.

    Enforces:
    - Unique metric IDs
    - Version tracking
    - Dependency resolution
    - Orphan metric detection (metrics without rune bindings)
    """

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or Path("data/simulation/metrics.json")
        self.metrics: Dict[str, MetricDefinition] = {}
        self._load()

    def _load(self):
        """Load metrics from disk."""
        if not self.registry_path.exists():
            return

        with open(self.registry_path, "r") as f:
            data = json.load(f)

        for metric_data in data.get("metrics", []):
            metric = MetricDefinition.from_dict(metric_data)
            self.metrics[metric.metric_id] = metric

    def save(self):
        """Save metrics to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metrics": [m.to_dict() for m in self.metrics.values()],
            "count": len(self.metrics),
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def register(self, metric: MetricDefinition):
        """Register a new metric.

        Raises:
            ValueError: If metric_id already exists
        """
        if metric.metric_id in self.metrics:
            raise ValueError(f"Metric {metric.metric_id} already registered")

        self.metrics[metric.metric_id] = metric

    def get(self, metric_id: str) -> Optional[MetricDefinition]:
        """Retrieve metric by ID."""
        return self.metrics.get(metric_id)

    def list_all(self) -> List[MetricDefinition]:
        """List all registered metrics."""
        return list(self.metrics.values())

    def find_orphans(self, rune_registry) -> List[str]:
        """Find metrics with no rune bindings.

        Args:
            rune_registry: RuneRegistry instance

        Returns:
            List of orphan metric IDs
        """
        orphans = []
        for metric_id in self.metrics:
            if not rune_registry.get_runes_for_metric(metric_id):
                orphans.append(metric_id)
        return orphans
