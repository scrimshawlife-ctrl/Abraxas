"""Outcome Ledger: Append-only log of simulation outcomes.

IMMUTABLE LAW: Provenance Always.
No overwrites. No deletions. No "memory summaries."

All results must reference metric versions, rune versions, simulation schema version, and input hashes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

@dataclass
class Prediction:
    """Single prediction with confidence interval."""
    prediction_id: str
    variable: str
    predicted_value: float
    confidence_interval: Dict[str, float]  # {lower, upper, level}
    horizon: int  # timesteps

    def to_dict(self) -> Dict:
        return {
            "prediction_id": self.prediction_id,
            "variable": self.variable,
            "predicted_value": self.predicted_value,
            "confidence_interval": self.confidence_interval,
            "horizon": self.horizon,
        }


@dataclass
class OutcomeEntry:
    """Single entry in the outcome ledger.

    APPEND-ONLY. Never modify after writing.
    """
    timestamp: str  # ISO 8601
    sim_seed: int
    sim_version: str
    active_metrics: List[Dict[str, str]]  # [{metric_id, version}, ...]
    active_runes: List[Dict[str, str]]  # [{rune_id, version}, ...]
    prior_state_hash: str
    prior_state_snapshot: Dict[str, Any]
    posterior_state_hash: str
    posterior_state_snapshot: Dict[str, Any]
    predictions_issued: List[Prediction] = field(default_factory=list)
    real_world_outcomes: List[Dict[str, Any]] = field(default_factory=list)
    error_metrics: Dict[str, float] = field(default_factory=dict)
    confidence_deltas: Dict[str, float] = field(default_factory=dict)
    measurement_disturbance: float = 0.0
    world_media_divergence: float = 0.0
    network_drift: float = 0.0
    strategy_shift: float = 0.0
    temporal_correlation_shift: float = 0.0
    community_stability: Optional[float] = None
    conformity_pressure_avg: Optional[float] = None

    def to_dict(self) -> Dict:
        result = {
            "timestamp": self.timestamp,
            "sim_seed": self.sim_seed,
            "sim_version": self.sim_version,
            "active_metrics": self.active_metrics,
            "active_runes": self.active_runes,
            "prior_state_hash": self.prior_state_hash,
            "prior_state_snapshot": self.prior_state_snapshot,
            "posterior_state_hash": self.posterior_state_hash,
            "posterior_state_snapshot": self.posterior_state_snapshot,
            "predictions_issued": [p.to_dict() for p in self.predictions_issued],
            "real_world_outcomes": self.real_world_outcomes,
            "error_metrics": self.error_metrics,
            "confidence_deltas": self.confidence_deltas,
            "measurement_disturbance": self.measurement_disturbance,
            "world_media_divergence": self.world_media_divergence,
            "network_drift": self.network_drift,
            "strategy_shift": self.strategy_shift,
            "temporal_correlation_shift": self.temporal_correlation_shift,
        }

        if self.community_stability is not None:
            result["community_stability"] = self.community_stability

        if self.conformity_pressure_avg is not None:
            result["conformity_pressure_avg"] = self.conformity_pressure_avg

        return result

    @staticmethod
    def from_dict(data: Dict) -> OutcomeEntry:
        predictions = [
            Prediction(
                prediction_id=p["prediction_id"],
                variable=p["variable"],
                predicted_value=p["predicted_value"],
                confidence_interval=p["confidence_interval"],
                horizon=p["horizon"],
            )
            for p in data.get("predictions_issued", [])
        ]

        return OutcomeEntry(
            timestamp=data["timestamp"],
            sim_seed=data["sim_seed"],
            sim_version=data["sim_version"],
            active_metrics=data["active_metrics"],
            active_runes=data["active_runes"],
            prior_state_hash=data["prior_state_hash"],
            prior_state_snapshot=data["prior_state_snapshot"],
            posterior_state_hash=data["posterior_state_hash"],
            posterior_state_snapshot=data["posterior_state_snapshot"],
            predictions_issued=predictions,
            real_world_outcomes=data.get("real_world_outcomes", []),
            error_metrics=data.get("error_metrics", {}),
            confidence_deltas=data.get("confidence_deltas", {}),
            measurement_disturbance=data.get("measurement_disturbance", 0.0),
            world_media_divergence=data.get("world_media_divergence", 0.0),
            network_drift=data.get("network_drift", 0.0),
            strategy_shift=data.get("strategy_shift", 0.0),
            temporal_correlation_shift=data.get("temporal_correlation_shift", 0.0),
            community_stability=data.get("community_stability"),
            conformity_pressure_avg=data.get("conformity_pressure_avg"),
        )

    def compute_state_hash(self, state_dict: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of simulation state."""
        state_str = json.dumps(state_dict, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()


class OutcomeLedger:
    """Append-only ledger for simulation outcomes.

    CRITICAL: This is an append-only log. No entry may be modified or deleted.
    """

    def __init__(self, ledger_path: Optional[Path] = None):
        self.ledger_path = ledger_path or Path("data/simulation/outcome_ledger.jsonl")
        self.entries: List[OutcomeEntry] = []
        self._load()

    def _load(self):
        """Load ledger from disk (JSONL format)."""
        if not self.ledger_path.exists():
            return

        with open(self.ledger_path, "r") as f:
            for line in f:
                if line.strip():
                    entry_data = json.loads(line)
                    entry = OutcomeEntry.from_dict(entry_data)
                    self.entries.append(entry)

    def append(self, entry: OutcomeEntry):
        """Append new entry to ledger.

        APPEND-ONLY. No modifications allowed.
        """
        # Ensure directory exists
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

        # Append to memory
        self.entries.append(entry)

        # Append to disk (JSONL)
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def get_all(self) -> List[OutcomeEntry]:
        """Get all entries (read-only)."""
        return list(self.entries)

    def get_by_seed(self, sim_seed: int) -> List[OutcomeEntry]:
        """Get all entries for a specific simulation seed."""
        return [e for e in self.entries if e.sim_seed == sim_seed]

    def get_recent(self, n: int = 10) -> List[OutcomeEntry]:
        """Get N most recent entries."""
        return self.entries[-n:]

    def compute_aggregate_metrics(self) -> Dict[str, float]:
        """Compute aggregate metrics across all entries."""
        if not self.entries:
            return {}

        total_disturbance = sum(e.measurement_disturbance for e in self.entries)
        total_divergence = sum(e.world_media_divergence for e in self.entries)
        total_network_drift = sum(e.network_drift for e in self.entries)
        total_strategy_shift = sum(e.strategy_shift for e in self.entries)
        total_correlation_shift = sum(e.temporal_correlation_shift for e in self.entries)

        n = len(self.entries)

        return {
            "avg_measurement_disturbance": total_disturbance / n,
            "avg_world_media_divergence": total_divergence / n,
            "avg_network_drift": total_network_drift / n,
            "avg_strategy_shift": total_strategy_shift / n,
            "avg_temporal_correlation_shift": total_correlation_shift / n,
            "total_entries": n,
        }

    def export_to_json(self, output_path: Path):
        """Export entire ledger to JSON array (for analysis).

        NOTE: This is read-only export. Original JSONL remains append-only.
        """
        data = {
            "entries": [e.to_dict() for e in self.entries],
            "count": len(self.entries),
            "exported": datetime.utcnow().isoformat() + "Z",
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
