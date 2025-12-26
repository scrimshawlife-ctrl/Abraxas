"""
Simulation Outcome Ledger with Shadow Metric Support

Extends the outcome ledger to log shadow metric values without allowing
them to influence state transitions.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from abraxas.core.provenance import hash_canonical_json


class OutcomeLedger:
    """
    Append-only JSONL ledger for simulation outcomes.

    Records:
    - Canonical metric values (used in state transitions)
    - Shadow metric values (observe-only, no feedback)
    - Simulation state snapshots
    - Rune bindings used
    """

    def __init__(self, ledger_path: str | Path | None = None):
        """
        Initialize outcome ledger.

        Args:
            ledger_path: Path to ledger file (default: .aal/ledger/outcomes.jsonl)
        """
        if ledger_path is None:
            ledger_path = Path(".aal/ledger/outcomes.jsonl")
        self.ledger_path = Path(ledger_path)
        self._ensure_ledger_exists()

    def _ensure_ledger_exists(self) -> None:
        """Create ledger file if it doesn't exist."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.exists():
            self.ledger_path.touch()

    def append_outcome(
        self,
        cycle: int,
        canonical_metrics: dict[str, float],
        shadow_metrics: dict[str, float] | None = None,
        state_snapshot: dict[str, Any] | None = None,
        rune_bindings: list[str] | None = None,
        seed: int | None = None,
    ) -> str:
        """
        Append simulation outcome to ledger.

        CRITICAL: shadow_metrics are logged but NEVER fed back into simulation.

        Args:
            cycle: Simulation cycle number
            canonical_metrics: Metrics that MAY affect state transitions
            shadow_metrics: Shadow metrics (observe-only)
            state_snapshot: Optional state snapshot
            rune_bindings: Active rune IDs for this cycle
            seed: Random seed used

        Returns:
            SHA256 hash of ledger entry
        """
        entry = {
            "cycle": cycle,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "canonical_metrics": canonical_metrics,
            "shadow_metrics": shadow_metrics or {},
            "state_snapshot": state_snapshot,
            "rune_bindings": rune_bindings or [],
            "seed": seed,
        }

        # Hash entry
        entry_hash = hash_canonical_json(entry)
        entry["ledger_sha256"] = entry_hash

        # Append to file
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(entry, default=str, sort_keys=True) + "\n")

        return entry_hash

    def read_all(self) -> list[dict[str, Any]]:
        """Read all entries from ledger."""
        entries = []
        if not self.ledger_path.exists():
            return entries

        with open(self.ledger_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        pass

        return entries

    def read_range(
        self, start_cycle: int | None = None, end_cycle: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Read entries within cycle range.

        Args:
            start_cycle: Inclusive start cycle
            end_cycle: Inclusive end cycle

        Returns:
            Filtered ledger entries
        """
        entries = self.read_all()

        if start_cycle is not None:
            entries = [e for e in entries if e.get("cycle", 0) >= start_cycle]

        if end_cycle is not None:
            entries = [e for e in entries if e.get("cycle", 0) <= end_cycle]

        return entries

    def get_shadow_metric_history(
        self, metric_id: str, limit: int | None = None
    ) -> list[tuple[int, float]]:
        """
        Extract shadow metric time series.

        Args:
            metric_id: Shadow metric ID
            limit: Max number of entries to retrieve

        Returns:
            List of (cycle, value) tuples
        """
        entries = self.read_all()
        history = []

        for entry in entries:
            shadow_metrics = entry.get("shadow_metrics", {})
            if metric_id in shadow_metrics:
                cycle = entry.get("cycle", 0)
                value = shadow_metrics[metric_id]
                history.append((cycle, value))

        if limit:
            history = history[-limit:]

        return history

    def compute_shadow_metric_stats(self, metric_id: str) -> dict[str, float]:
        """
        Compute statistics for a shadow metric.

        Args:
            metric_id: Shadow metric ID

        Returns:
            Dict with mean, std_dev, min, max, count
        """
        history = self.get_shadow_metric_history(metric_id)

        if not history:
            return {
                "mean": 0.0,
                "std_dev": 0.0,
                "min": 0.0,
                "max": 0.0,
                "count": 0,
            }

        values = [v for _, v in history]
        n = len(values)
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n
        std_dev = variance**0.5

        return {
            "mean": mean,
            "std_dev": std_dev,
            "min": min(values),
            "max": max(values),
            "count": n,
        }

    def verify_shadow_isolation(self) -> bool:
        """
        Verify that shadow metrics are never used in canonical metrics.

        This is a safety check to ensure shadow metrics remain observe-only.

        Returns:
            True if shadow isolation is maintained
        """
        entries = self.read_all()

        shadow_metric_ids = set()
        for entry in entries:
            shadow_metric_ids.update(entry.get("shadow_metrics", {}).keys())

        # Check that no shadow metric appears in canonical metrics
        for entry in entries:
            canonical_ids = set(entry.get("canonical_metrics", {}).keys())
            if shadow_metric_ids & canonical_ids:
                return False

        return True

    def get_summary(self) -> dict[str, Any]:
        """Get ledger summary statistics."""
        entries = self.read_all()

        if not entries:
            return {
                "total_entries": 0,
                "cycle_range": (0, 0),
                "canonical_metrics_count": 0,
                "shadow_metrics_count": 0,
            }

        cycles = [e.get("cycle", 0) for e in entries]
        canonical_metric_ids = set()
        shadow_metric_ids = set()

        for entry in entries:
            canonical_metric_ids.update(entry.get("canonical_metrics", {}).keys())
            shadow_metric_ids.update(entry.get("shadow_metrics", {}).keys())

        return {
            "total_entries": len(entries),
            "cycle_range": (min(cycles), max(cycles)),
            "canonical_metrics_count": len(canonical_metric_ids),
            "shadow_metrics_count": len(shadow_metric_ids),
            "shadow_isolation_verified": self.verify_shadow_isolation(),
        }
