"""Canonical append-only event ledger with hash chaining.

Each event is stored with:
- Stable JSON serialization (sorted keys, no whitespace)
- SHA256 hash chain: hash(prev_hash + event_json)
- SQLite persistence with WAL mode
"""

from __future__ import annotations
import hashlib
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass

from abx.util.jsonutil import dumps_stable
from abx.util.hashutil import sha256_bytes


@dataclass
class LogEvent:
    """A single log event with hash chain metadata."""
    id: int
    ts: int
    kind: str
    module: str
    frame_id: str
    event_json: str
    hash: str
    prev_hash: str


def init_ledger(con: sqlite3.Connection) -> None:
    """Initialize ledger tables."""
    con.execute("""
    CREATE TABLE IF NOT EXISTS log_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts INTEGER NOT NULL,
      kind TEXT NOT NULL,
      module TEXT NOT NULL,
      frame_id TEXT NOT NULL,
      event_json TEXT NOT NULL,
      hash TEXT NOT NULL,
      prev_hash TEXT NOT NULL
    );
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_log_events_ts ON log_events(ts);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_log_events_kind ON log_events(kind);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_log_events_module ON log_events(module);")
    con.commit()


def _get_last_hash(con: sqlite3.Connection) -> str:
    """Get hash of the last event in the chain."""
    cur = con.execute("SELECT hash FROM log_events ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
    if row:
        return row[0]
    # Genesis hash for empty chain
    return "0" * 64


def _compute_event_hash(prev_hash: str, event_json: str) -> str:
    """Compute SHA256 hash for event: hash(prev_hash + event_json)."""
    data = prev_hash.encode("utf-8") + event_json.encode("utf-8")
    return sha256_bytes(data)


def append_event(
    con: sqlite3.Connection,
    *,
    kind: str,
    module: str,
    frame_id: str = "",
    payload: Optional[Dict[str, Any]] = None
) -> int:
    """Append a new event to the ledger.

    Args:
        con: Database connection
        kind: Event type/kind
        module: Module name
        frame_id: Optional frame identifier
        payload: Optional event payload

    Returns:
        Event ID (autoincrement primary key)
    """
    ts = int(time.time())
    event_data = {
        "kind": kind,
        "module": module,
        "frame_id": frame_id,
        "ts": ts,
        "payload": payload or {},
    }

    # Deterministic JSON serialization
    event_json = dumps_stable(event_data)

    # Get previous hash and compute new hash
    prev_hash = _get_last_hash(con)
    event_hash = _compute_event_hash(prev_hash, event_json)

    # Insert event
    cur = con.execute("""
    INSERT INTO log_events(ts, kind, module, frame_id, event_json, hash, prev_hash)
    VALUES(?, ?, ?, ?, ?, ?, ?);
    """, (ts, kind, module, frame_id, event_json, event_hash, prev_hash))
    con.commit()

    return cur.lastrowid


def get_event(con: sqlite3.Connection, event_id: int) -> Optional[LogEvent]:
    """Retrieve a single event by ID."""
    cur = con.execute("""
    SELECT id, ts, kind, module, frame_id, event_json, hash, prev_hash
    FROM log_events WHERE id = ?;
    """, (event_id,))
    row = cur.fetchone()
    if not row:
        return None
    return LogEvent(*row)


def get_events_range(
    con: sqlite3.Connection,
    start_id: int,
    end_id: int
) -> List[LogEvent]:
    """Retrieve events in a range [start_id, end_id] inclusive."""
    cur = con.execute("""
    SELECT id, ts, kind, module, frame_id, event_json, hash, prev_hash
    FROM log_events WHERE id >= ? AND id <= ?
    ORDER BY id ASC;
    """, (start_id, end_id))

    events = []
    for row in cur.fetchall():
        events.append(LogEvent(*row))
    return events


def verify_chain(con: sqlite3.Connection, start_id: int = 1, end_id: Optional[int] = None) -> Dict[str, Any]:
    """Verify hash chain integrity.

    Args:
        con: Database connection
        start_id: Starting event ID
        end_id: Optional ending event ID (default: last event)

    Returns:
        Verification result with ok flag and details
    """
    if end_id is None:
        cur = con.execute("SELECT MAX(id) FROM log_events;")
        row = cur.fetchone()
        if not row or row[0] is None:
            return {"ok": True, "verified": 0, "errors": []}
        end_id = row[0]

    events = get_events_range(con, start_id, end_id)
    if not events:
        return {"ok": True, "verified": 0, "errors": []}

    errors = []
    prev_hash = events[0].prev_hash

    for event in events:
        # Check prev_hash matches
        if event.prev_hash != prev_hash:
            errors.append({
                "id": event.id,
                "error": "prev_hash_mismatch",
                "expected": prev_hash,
                "actual": event.prev_hash,
            })

        # Recompute hash
        computed_hash = _compute_event_hash(event.prev_hash, event.event_json)
        if computed_hash != event.hash:
            errors.append({
                "id": event.id,
                "error": "hash_mismatch",
                "expected": computed_hash,
                "actual": event.hash,
            })

        prev_hash = event.hash

    return {
        "ok": len(errors) == 0,
        "verified": len(events),
        "start_id": start_id,
        "end_id": end_id,
        "errors": errors,
    }


def get_stats(con: sqlite3.Connection) -> Dict[str, Any]:
    """Get ledger statistics."""
    cur = con.execute("SELECT COUNT(*), MIN(id), MAX(id), MIN(ts), MAX(ts) FROM log_events;")
    row = cur.fetchone()

    if not row or row[0] == 0:
        return {
            "total_events": 0,
            "min_id": None,
            "max_id": None,
            "min_ts": None,
            "max_ts": None,
        }

    return {
        "total_events": row[0],
        "min_id": row[1],
        "max_id": row[2],
        "min_ts": row[3],
        "max_ts": row[4],
    }
