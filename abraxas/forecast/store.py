"""
Forecast Store and Ledgers

Storage for ensemble states with append-only hash-chained ledgers.
Full provenance from signal → influence → branch update.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.core.provenance import hash_canonical_json
from abraxas.forecast.types import EnsembleState


class ForecastStore:
    """
    Storage manager for forecast ensembles and branch update ledgers.
    """

    def __init__(
        self,
        ensembles_dir: str | Path = "data/forecast/ensembles",
        ledger_path: str | Path = "out/forecast_ledgers/branch_updates.jsonl",
    ):
        """
        Initialize forecast store.

        Args:
            ensembles_dir: Directory for latest ensemble snapshots
            ledger_path: Path to branch update ledger
        """
        self.ensembles_dir = Path(ensembles_dir)
        self.ledger_path = Path(ledger_path)

        self.ensembles_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def load_ensemble(self, ensemble_id: str) -> Optional[EnsembleState]:
        """
        Load ensemble state from disk.

        Args:
            ensemble_id: Ensemble identifier

        Returns:
            EnsembleState if found, None otherwise
        """
        ensemble_path = self.ensembles_dir / f"{ensemble_id}.json"

        if not ensemble_path.exists():
            return None

        with open(ensemble_path, "r") as f:
            data = json.load(f)

        return EnsembleState(**data)

    def save_ensemble(self, ensemble: EnsembleState) -> Path:
        """
        Save ensemble state to disk (overwrites existing).

        Args:
            ensemble: Ensemble state to save

        Returns:
            Path to saved file
        """
        ensemble_path = self.ensembles_dir / f"{ensemble.ensemble_id}.json"

        with open(ensemble_path, "w") as f:
            json.dump(ensemble.model_dump(), f, indent=2, default=str)

        return ensemble_path

    def append_branch_update_ledger(
        self, record: Dict[str, Any]
    ) -> str:
        """
        Append branch update record to ledger.

        Args:
            record: Update record (must include required fields)

        Returns:
            SHA256 hash of ledger entry
        """
        # Get previous hash
        prev_hash = self._get_last_hash()

        # Add prev_hash to record
        record["prev_hash"] = prev_hash

        # Compute step hash
        step_hash = hash_canonical_json(record)
        record["step_hash"] = step_hash

        # Append to ledger
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")

        return step_hash

    def _get_last_hash(self) -> str:
        """Get hash of last ledger entry."""
        if not self.ledger_path.exists():
            return "genesis"

        with open(self.ledger_path, "r") as f:
            lines = f.readlines()
            if not lines:
                return "genesis"

            last_entry = json.loads(lines[-1])
            return last_entry.get("step_hash", "genesis")

    def read_all_updates(self) -> list[Dict[str, Any]]:
        """Read all branch update entries from ledger."""
        if not self.ledger_path.exists():
            return []

        entries = []
        with open(self.ledger_path, "r") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))

        return entries

    def get_ensemble_updates(self, ensemble_id: str) -> list[Dict[str, Any]]:
        """Get all updates for a specific ensemble."""
        all_updates = self.read_all_updates()
        return [u for u in all_updates if u.get("ensemble_id") == ensemble_id]


# Global store instance
_default_store = None


def get_default_store() -> ForecastStore:
    """Get or create default forecast store instance."""
    global _default_store
    if _default_store is None:
        _default_store = ForecastStore()
    return _default_store


def load_ensemble(ensemble_id: str) -> Optional[EnsembleState]:
    """Load ensemble using default store."""
    return get_default_store().load_ensemble(ensemble_id)


def save_ensemble(ensemble: EnsembleState) -> Path:
    """Save ensemble using default store."""
    return get_default_store().save_ensemble(ensemble)


def append_branch_update_ledger(
    ensemble_id: str,
    topic_key: str,
    horizon: str,
    segment: str,
    narrative: str,
    branch_probs_before: Dict[str, float],
    branch_probs_after: Dict[str, float],
    delta_summary: Dict[str, Any],
    integrity_context: Optional[Dict[str, Any]] = None,
    run_id: str = "manual",
) -> str:
    """
    Append branch update to ledger using default store.

    Convenience function for recording branch updates.
    """
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "branch_update",
        "run_id": run_id,
        "ensemble_id": ensemble_id,
        "topic_key": topic_key,
        "horizon": horizon,
        "segment": segment,
        "narrative": narrative,
        "branch_probs_before": branch_probs_before,
        "branch_probs_after": branch_probs_after,
        "delta_summary": delta_summary,
        "components": delta_summary.get("components", []),
        "integrity_context": integrity_context or {},
    }

    return get_default_store().append_branch_update_ledger(record)
