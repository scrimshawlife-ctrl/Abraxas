"""Log compaction with ABX-Runes dictionary coding and compression.

Compactor:
1. Builds a rune dictionary from top-K repeated strings
2. Encodes events by replacing strings with rune tokens (e.g., "ᚱ12")
3. Optionally compresses with gzip (deterministic settings)
4. Stores segments with manifest and integrity hashes
"""

from __future__ import annotations
import gzip
import json
import sqlite3
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from abx.util.jsonutil import dumps_stable
from abx.util.hashutil import sha256_bytes
from abx.log.ledger import get_events_range, LogEvent


# Rune prefix for dictionary tokens
RUNE_PREFIX = "ᚱ"


@dataclass
class RuneDictionary:
    """Dictionary for ABX-Runes encoding."""
    version: int
    entries: Dict[str, str]  # string -> rune token
    reverse: Dict[str, str]  # rune token -> string


def init_compactor_tables(con: sqlite3.Connection) -> None:
    """Initialize compactor storage tables."""
    # Compressed segments
    con.execute("""
    CREATE TABLE IF NOT EXISTS log_segments (
      segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
      start_id INTEGER NOT NULL,
      end_id INTEGER NOT NULL,
      created_ts INTEGER NOT NULL,
      sha256 TEXT NOT NULL,
      codec TEXT NOT NULL,
      blob BLOB NOT NULL
    );
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_log_segments_range ON log_segments(start_id, end_id);")

    # Compaction manifest
    con.execute("""
    CREATE TABLE IF NOT EXISTS log_manifest (
      segment_id INTEGER PRIMARY KEY,
      dict_version INTEGER NOT NULL,
      dict_sha256 TEXT NOT NULL,
      raw_event_count INTEGER NOT NULL,
      compressed_size INTEGER NOT NULL,
      FOREIGN KEY(segment_id) REFERENCES log_segments(segment_id)
    );
    """)

    con.commit()


def _extract_strings(events: List[LogEvent], min_length: int = 3) -> List[str]:
    """Extract all strings from events for frequency analysis."""
    strings = []

    for event in events:
        # Parse event JSON
        data = json.loads(event.event_json)

        # Extract key strings
        strings.append(data.get("kind", ""))
        strings.append(data.get("module", ""))
        strings.append(data.get("frame_id", ""))

        # Extract from payload (only string values)
        payload = data.get("payload", {})
        if isinstance(payload, dict):
            for key, value in payload.items():
                if isinstance(key, str) and len(key) >= min_length:
                    strings.append(key)
                if isinstance(value, str) and len(value) >= min_length:
                    strings.append(value)

    return [s for s in strings if s and len(s) >= min_length]


def build_rune_dictionary(events: List[LogEvent], top_k: int = 256) -> RuneDictionary:
    """Build rune dictionary from top-K most frequent strings.

    Args:
        events: Events to analyze
        top_k: Number of top strings to include in dictionary

    Returns:
        RuneDictionary with bidirectional mappings
    """
    strings = _extract_strings(events)
    counter = Counter(strings)

    # Get top-K by frequency
    top_strings = [s for s, _ in counter.most_common(top_k)]

    # Build dictionary with deterministic ordering (alphabetical for stability)
    top_strings.sort()

    entries = {}
    reverse = {}
    for idx, s in enumerate(top_strings):
        rune_token = f"{RUNE_PREFIX}{idx}"
        entries[s] = rune_token
        reverse[rune_token] = s

    return RuneDictionary(
        version=1,
        entries=entries,
        reverse=reverse,
    )


def _encode_value(value: Any, rune_dict: RuneDictionary) -> Any:
    """Recursively encode a value using rune dictionary."""
    if isinstance(value, str):
        return rune_dict.entries.get(value, value)
    elif isinstance(value, dict):
        return {
            rune_dict.entries.get(k, k): _encode_value(v, rune_dict)
            for k, v in value.items()
        }
    elif isinstance(value, list):
        return [_encode_value(item, rune_dict) for item in value]
    else:
        return value


def encode_events(events: List[LogEvent], rune_dict: RuneDictionary) -> List[Dict[str, Any]]:
    """Encode events using rune dictionary.

    Args:
        events: Events to encode
        rune_dict: Rune dictionary for encoding

    Returns:
        List of encoded event dictionaries
    """
    encoded = []

    for event in events:
        data = json.loads(event.event_json)

        # Encode with runes
        encoded_data = {
            "id": event.id,
            "kind": rune_dict.entries.get(data["kind"], data["kind"]),
            "module": rune_dict.entries.get(data["module"], data["module"]),
            "frame_id": rune_dict.entries.get(data.get("frame_id", ""), data.get("frame_id", "")),
            "ts": data["ts"],
            "payload": _encode_value(data.get("payload", {}), rune_dict),
        }
        encoded.append(encoded_data)

    return encoded


def compress_segment(
    events: List[LogEvent],
    rune_dict: RuneDictionary,
    use_gzip: bool = True
) -> Tuple[bytes, str]:
    """Compress event segment with rune encoding.

    Args:
        events: Events to compress
        rune_dict: Rune dictionary
        use_gzip: Whether to apply gzip compression

    Returns:
        Tuple of (compressed_blob, codec_name)
    """
    # Encode events
    encoded = encode_events(events, rune_dict)

    # Create segment structure
    segment_data = {
        "dict_version": rune_dict.version,
        "dict": {
            "entries": rune_dict.entries,
            "reverse": rune_dict.reverse,
        },
        "events": encoded,
    }

    # Stable JSON serialization
    segment_json = dumps_stable(segment_data)
    segment_bytes = segment_json.encode("utf-8")

    if use_gzip:
        # Deterministic gzip: no timestamp, compression level 9
        compressed = gzip.compress(segment_bytes, compresslevel=9, mtime=0)
        return compressed, "gzip+runes"
    else:
        return segment_bytes, "runes"


def compact(
    con: sqlite3.Connection,
    start_id: int,
    end_id: int,
    top_k: int = 256,
    use_gzip: bool = True
) -> int:
    """Compact a range of events into a compressed segment.

    Args:
        con: Database connection
        start_id: Starting event ID (inclusive)
        end_id: Ending event ID (inclusive)
        top_k: Number of dictionary entries
        use_gzip: Whether to use gzip compression

    Returns:
        Segment ID
    """
    # Fetch events
    events = get_events_range(con, start_id, end_id)
    if not events:
        raise ValueError(f"No events found in range [{start_id}, {end_id}]")

    # Build rune dictionary
    rune_dict = build_rune_dictionary(events, top_k=top_k)

    # Compress segment
    blob, codec = compress_segment(events, rune_dict, use_gzip=use_gzip)

    # Compute SHA256 of compressed blob
    blob_sha256 = sha256_bytes(blob)

    # Compute dictionary hash (for manifest)
    dict_data = dumps_stable({"version": rune_dict.version, "entries": rune_dict.entries})
    dict_sha256 = sha256_bytes(dict_data.encode("utf-8"))

    # Store segment
    ts = int(time.time())
    cur = con.execute("""
    INSERT INTO log_segments(start_id, end_id, created_ts, sha256, codec, blob)
    VALUES(?, ?, ?, ?, ?, ?);
    """, (start_id, end_id, ts, blob_sha256, codec, blob))
    segment_id = cur.lastrowid

    # Store manifest
    con.execute("""
    INSERT INTO log_manifest(segment_id, dict_version, dict_sha256, raw_event_count, compressed_size)
    VALUES(?, ?, ?, ?, ?);
    """, (segment_id, rune_dict.version, dict_sha256, len(events), len(blob)))

    con.commit()

    return segment_id


def get_segment(con: sqlite3.Connection, segment_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a compressed segment."""
    cur = con.execute("""
    SELECT s.segment_id, s.start_id, s.end_id, s.created_ts, s.sha256, s.codec, s.blob,
           m.dict_version, m.dict_sha256, m.raw_event_count, m.compressed_size
    FROM log_segments s
    LEFT JOIN log_manifest m ON s.segment_id = m.segment_id
    WHERE s.segment_id = ?;
    """, (segment_id,))

    row = cur.fetchone()
    if not row:
        return None

    return {
        "segment_id": row[0],
        "start_id": row[1],
        "end_id": row[2],
        "created_ts": row[3],
        "sha256": row[4],
        "codec": row[5],
        "blob_size": len(row[6]),
        "dict_version": row[7],
        "dict_sha256": row[8],
        "raw_event_count": row[9],
        "compressed_size": row[10],
    }


def decompress_segment(blob: bytes, codec: str) -> Dict[str, Any]:
    """Decompress and decode a segment.

    Args:
        blob: Compressed segment blob
        codec: Codec name (e.g., "gzip+runes")

    Returns:
        Decompressed segment data
    """
    if codec == "gzip+runes":
        decompressed = gzip.decompress(blob)
        segment_json = decompressed.decode("utf-8")
    elif codec == "runes":
        segment_json = blob.decode("utf-8")
    else:
        raise ValueError(f"Unknown codec: {codec}")

    return json.loads(segment_json)


def list_segments(con: sqlite3.Connection) -> List[Dict[str, Any]]:
    """List all compressed segments."""
    cur = con.execute("""
    SELECT s.segment_id, s.start_id, s.end_id, s.created_ts, s.sha256, s.codec,
           m.raw_event_count, m.compressed_size
    FROM log_segments s
    LEFT JOIN log_manifest m ON s.segment_id = m.segment_id
    ORDER BY s.segment_id ASC;
    """)

    segments = []
    for row in cur.fetchall():
        segments.append({
            "segment_id": row[0],
            "start_id": row[1],
            "end_id": row[2],
            "created_ts": row[3],
            "sha256": row[4],
            "codec": row[5],
            "raw_event_count": row[6],
            "compressed_size": row[7],
        })

    return segments
