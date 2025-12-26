"""
Event Query Module

Loads signal events and domain ledgers from local storage by time range.
Deterministic ordering, no network calls.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class SignalEvent:
    """
    Simplified signal event structure.

    Real implementation would align with your signal ingestion schema.
    """

    def __init__(
        self,
        event_id: str,
        timestamp: datetime,
        text: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.event_id = event_id
        self.timestamp = timestamp
        self.text = text
        self.source = source
        self.metadata = metadata or {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SignalEvent:
        """Parse signal event from dict."""
        timestamp_str = data.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            timestamp = datetime.utcnow()

        return cls(
            event_id=data.get("event_id", ""),
            timestamp=timestamp,
            text=data.get("text", ""),
            source=data.get("source", ""),
            metadata=data.get("metadata", {}),
        )


def load_signal_events(
    time_min: datetime,
    time_max: datetime,
    source_labels: Optional[List[str]] = None,
    events_path: str | Path | None = None,
) -> List[SignalEvent]:
    """
    Load signal events from local JSONL file within time range.

    Args:
        time_min: Minimum timestamp (inclusive)
        time_max: Maximum timestamp (inclusive)
        source_labels: Optional filter by source labels
        events_path: Path to events file (default: data/signals/events.jsonl)

    Returns:
        List of SignalEvent objects, sorted by (timestamp, event_id)
    """
    if events_path is None:
        events_path = Path("data/signals/events.jsonl")
    else:
        events_path = Path(events_path)

    events = []

    if not events_path.exists():
        return events

    with open(events_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                event = SignalEvent.from_dict(data)

                # Time filter
                if not (time_min <= event.timestamp <= time_max):
                    continue

                # Source filter
                if source_labels and event.source not in source_labels:
                    continue

                events.append(event)

            except (json.JSONDecodeError, KeyError):
                continue

    # Deterministic ordering
    events.sort(key=lambda e: (e.timestamp, e.event_id))

    return events


def load_domain_ledgers(
    time_min: datetime,
    time_max: datetime,
    ledger_dir: str | Path | None = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load domain ledgers (oracle_delta, integrity, tau, etc.) within time range.

    Args:
        time_min: Minimum timestamp (inclusive)
        time_max: Maximum timestamp (inclusive)
        ledger_dir: Directory containing ledgers (default: out/temporal_ledgers)

    Returns:
        Dict mapping ledger_name -> list of entries
    """
    if ledger_dir is None:
        ledger_dir = Path("out/temporal_ledgers")
    else:
        ledger_dir = Path(ledger_dir)

    ledgers = {}

    if not ledger_dir.exists():
        return ledgers

    # Known ledger files
    ledger_files = {
        "oracle_delta": "oracle_delta.jsonl",
        "integrity": "integrity_ledger.jsonl",
        "tau": "tau_ledger.jsonl",
        "mw": "mw_ledger.jsonl",
    }

    for ledger_name, filename in ledger_files.items():
        ledger_path = ledger_dir / filename
        if not ledger_path.exists():
            continue

        entries = []
        with open(ledger_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)

                    # Parse timestamp
                    timestamp_str = entry.get("timestamp", "")
                    try:
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                    except (ValueError, AttributeError):
                        continue

                    # Time filter
                    if not (time_min <= timestamp <= time_max):
                        continue

                    entries.append(entry)

                except (json.JSONDecodeError, KeyError):
                    continue

        # Deterministic ordering
        entries.sort(key=lambda e: e.get("timestamp", ""))

        ledgers[ledger_name] = entries

    return ledgers


def check_ledger_completeness(
    required_ledgers: List[str], available_ledgers: Dict[str, List[Dict[str, Any]]]
) -> float:
    """
    Compute completeness fraction of required ledgers.

    Args:
        required_ledgers: List of required ledger paths/names
        available_ledgers: Dict of loaded ledgers

    Returns:
        Completeness fraction (0.0 to 1.0)
    """
    if not required_ledgers:
        return 1.0

    # Extract ledger names from paths
    required_names = set()
    for ledger_path in required_ledgers:
        ledger_name = Path(ledger_path).stem  # e.g., "oracle_delta" from "oracle_delta.jsonl"
        required_names.add(ledger_name)

    available_names = set(available_ledgers.keys())

    matched = required_names & available_names
    completeness = len(matched) / len(required_names) if required_names else 1.0

    return completeness
