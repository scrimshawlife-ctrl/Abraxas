"""
Score Ledger

Hash-chained ledger for forecast accuracy scores.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from abraxas.core.provenance import hash_canonical_json
from abraxas.scoreboard.types import ScoreResult


class ScoreLedger:
    """
    Append-only hash-chained ledger for forecast scores.
    """

    def __init__(
        self, ledger_path: str | Path = "out/score_ledgers/forecast_scores.jsonl"
    ):
        """
        Initialize score ledger.

        Args:
            ledger_path: Path to score ledger file
        """
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def append_score(
        self, score_result: ScoreResult, run_id: str = "manual"
    ) -> str:
        """
        Append score result to ledger.

        Args:
            score_result: Score result to append
            run_id: Run identifier

        Returns:
            SHA256 hash of ledger entry
        """
        # Get previous hash
        prev_hash = self._get_last_hash()

        # Create ledger entry
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "forecast_score",
            "run_id": run_id,
            "score_id": score_result.score_id,
            "horizon": score_result.horizon,
            "segment": score_result.segment,
            "narrative": score_result.narrative,
            "brier_avg": score_result.brier_avg,
            "log_avg": score_result.log_avg,
            "calibration_bins": [bin.model_dump() for bin in score_result.calibration_bins],
            "coverage": score_result.coverage,
            "abstain_rate": score_result.abstain_rate,
            "cases_scored": score_result.cases_scored,
            "prev_hash": prev_hash,
        }

        # Compute step hash
        step_hash = hash_canonical_json(entry)
        entry["step_hash"] = step_hash

        # Append to ledger
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")

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

    def read_all(self) -> List[Dict[str, Any]]:
        """Read all score entries from ledger."""
        if not self.ledger_path.exists():
            return []

        entries = []
        with open(self.ledger_path, "r") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))

        return entries

    def get_scores_by_horizon(self, horizon: str) -> List[Dict[str, Any]]:
        """Get all scores for a specific horizon."""
        all_scores = self.read_all()
        return [s for s in all_scores if s.get("horizon") == horizon]
