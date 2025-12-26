"""
Backtest Ledger — Append-Only Hash-Chained Record

Records backtest evaluation results with provenance and integrity protection.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from abraxas.core.provenance import hash_canonical_json
from abraxas.backtest.schema import BacktestResult


class BacktestLedger:
    """
    Append-only ledger for backtest results.

    Features:
    - Hash-chained entries for integrity
    - Provenance tracking
    - Deterministic ordering
    """

    def __init__(self, ledger_path: str | Path | None = None):
        """
        Initialize backtest ledger.

        Args:
            ledger_path: Path to ledger file (default: out/backtest_ledgers/backtest_runs.jsonl)
        """
        if ledger_path is None:
            ledger_path = Path("out/backtest_ledgers/backtest_runs.jsonl")
        self.ledger_path = Path(ledger_path)
        self._ensure_ledger_exists()

    def _ensure_ledger_exists(self) -> None:
        """Create ledger file if it doesn't exist."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.exists():
            self.ledger_path.touch()

    def append_result(
        self, backtest_run_id: str, result: BacktestResult
    ) -> str:
        """
        Append backtest result to ledger.

        Args:
            backtest_run_id: Unique run ID
            result: BacktestResult instance

        Returns:
            SHA256 hash of ledger entry
        """
        # Get previous hash
        prev_hash = self._get_last_hash()

        # Build entry
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "backtest_run_id": backtest_run_id,
            "case_id": result.case_id,
            "status": result.status.value,
            "score": result.score,
            "confidence": result.confidence.value,
            "satisfied_triggers": result.satisfied_triggers,
            "satisfied_falsifiers": result.satisfied_falsifiers,
            "notes": result.notes,
            "provenance": result.provenance,
            "evaluated_at": result.evaluated_at.isoformat(),
            "prev_hash": prev_hash,
        }

        # Hash entry
        step_hash = hash_canonical_json(entry)
        entry["step_hash"] = step_hash

        # Append to file
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(entry, default=str, sort_keys=True) + "\n")

        return step_hash

    def _get_last_hash(self) -> str:
        """Get hash of last ledger entry."""
        if not self.ledger_path.exists():
            return "0" * 64  # Genesis hash

        last_line = None
        with open(self.ledger_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    last_line = line

        if last_line is None:
            return "0" * 64

        try:
            last_entry = json.loads(last_line)
            return last_entry.get("step_hash", "0" * 64)
        except json.JSONDecodeError:
            return "0" * 64

    def read_all(self) -> List[Dict[str, Any]]:
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

    def get_results_for_cases(
        self, case_ids: List[str], latest_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get backtest results for specific case IDs.

        Args:
            case_ids: List of case IDs to filter
            latest_only: If True, return only most recent result per case

        Returns:
            List of matching ledger entries
        """
        all_entries = self.read_all()

        # Filter by case_id
        matching = [e for e in all_entries if e.get("case_id") in case_ids]

        if not latest_only:
            return matching

        # Get latest for each case
        latest_by_case = {}
        for entry in matching:
            case_id = entry["case_id"]
            timestamp = entry.get("evaluated_at", entry.get("timestamp", ""))

            if case_id not in latest_by_case:
                latest_by_case[case_id] = entry
            else:
                if timestamp > latest_by_case[case_id].get(
                    "evaluated_at", latest_by_case[case_id].get("timestamp", "")
                ):
                    latest_by_case[case_id] = entry

        return list(latest_by_case.values())

    def verify_chain_integrity(self) -> bool:
        """
        Verify hash chain integrity.

        Returns:
            True if chain is valid
        """
        entries = self.read_all()

        if not entries:
            return True

        prev_hash = "0" * 64
        for entry in entries:
            claimed_prev = entry.get("prev_hash", "")
            if claimed_prev != prev_hash:
                return False

            # Verify step_hash
            entry_copy = entry.copy()
            claimed_step = entry_copy.pop("step_hash", "")
            computed_step = hash_canonical_json(entry_copy)

            if claimed_step != computed_step:
                return False

            prev_hash = claimed_step

        return True

    def get_summary(self) -> Dict[str, Any]:
        """Get ledger summary statistics."""
        entries = self.read_all()

        if not entries:
            return {
                "total_entries": 0,
                "status_counts": {},
                "confidence_counts": {},
                "chain_integrity": True,
            }

        status_counts = {}
        confidence_counts = {}

        for entry in entries:
            status = entry.get("status", "UNKNOWN")
            confidence = entry.get("confidence", "LOW")

            status_counts[status] = status_counts.get(status, 0) + 1
            confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1

        return {
            "total_entries": len(entries),
            "status_counts": status_counts,
            "confidence_counts": confidence_counts,
            "chain_integrity": self.verify_chain_integrity(),
            "unique_cases": len(set(e["case_id"] for e in entries)),
        }
