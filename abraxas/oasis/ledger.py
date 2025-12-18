"""OAS Ledger: append-only record of all OAS decisions and events."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from abraxas.core.provenance import ProvenanceRef, hash_canonical_json


class OASLedger:
    """
    Append-only JSONL ledger for OAS operations.

    Records all candidate proposals, validations, and canonization decisions.
    """

    def __init__(self, ledger_path: str | Path | None = None):
        """
        Initialize ledger.

        Args:
            ledger_path: Path to ledger file (default: .aal/ledger/oasis_operators.jsonl)
        """
        if ledger_path is None:
            ledger_path = Path(".aal/ledger/oasis_operators.jsonl")
        self.ledger_path = Path(ledger_path)
        self._ensure_ledger_exists()

    def _ensure_ledger_exists(self) -> None:
        """Create ledger file if it doesn't exist."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.exists():
            self.ledger_path.touch()

    def append(self, entry: dict[str, Any]) -> ProvenanceRef:
        """
        Append entry to ledger.

        Returns ProvenanceRef for the appended entry.
        """
        # Add metadata
        entry["ledger_timestamp"] = datetime.now(timezone.utc).isoformat()
        entry["ledger_sha256"] = hash_canonical_json(entry)

        # Append to file
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(entry, default=str, sort_keys=True) + "\n")

        # Return provenance ref
        return ProvenanceRef(
            scheme="ledger",
            path=str(self.ledger_path),
            sha256=entry["ledger_sha256"],
        )

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
                        # Skip malformed lines
                        pass

        return entries

    def get_latest_status(self, operator_id: str) -> dict[str, Any] | None:
        """
        Get latest status for an operator from ledger.

        Returns the most recent entry for the given operator_id.
        """
        entries = self.read_all()
        # Filter entries for this operator
        operator_entries = [
            e
            for e in entries
            if e.get("candidate", {}).get("operator_id") == operator_id
            or e.get("candidate_id") == operator_id
        ]

        if not operator_entries:
            return None

        # Return most recent
        return operator_entries[-1]

    def count_adoptions(self) -> int:
        """Count number of adoptions in ledger."""
        entries = self.read_all()
        return sum(1 for e in entries if e.get("type") == "adoption")

    def count_rejections(self) -> int:
        """Count number of rejections in ledger."""
        entries = self.read_all()
        return sum(1 for e in entries if e.get("type") == "rejection")

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics from ledger."""
        entries = self.read_all()
        return {
            "total_entries": len(entries),
            "adoptions": self.count_adoptions(),
            "rejections": self.count_rejections(),
            "first_entry": entries[0].get("ledger_timestamp") if entries else None,
            "last_entry": entries[-1].get("ledger_timestamp") if entries else None,
        }
