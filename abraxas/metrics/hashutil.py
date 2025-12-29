"""Canonical JSON Hashing Utilities

Deterministic hashing for provenance and tamper detection.
All JSON objects are canonicalized before hashing:
- Keys sorted alphabetically
- Floats formatted with fixed precision (6 decimals)
- No extra whitespace
- UTF-8 encoding
"""

import hashlib
import json
from typing import Any, Dict


def canonicalize_json(obj: Any) -> str:
    """Canonicalize JSON object to deterministic string representation.

    Args:
        obj: Any JSON-serializable object

    Returns:
        Canonical JSON string (sorted keys, fixed float precision)
    """
    def float_handler(x):
        """Format floats with 6 decimal places for determinism."""
        if isinstance(x, float):
            return f"{x:.6f}"
        return x

    # Convert floats recursively
    def convert_floats(obj):
        if isinstance(obj, dict):
            return {k: convert_floats(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_floats(item) for item in obj]
        elif isinstance(obj, float):
            return float_handler(obj)
        else:
            return obj

    canonical_obj = convert_floats(obj)

    # Sort keys, no whitespace, ensure_ascii for stability
    return json.dumps(
        canonical_obj,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=True,
    )


def hash_json(obj: Any) -> str:
    """Compute SHA-256 hash of canonicalized JSON object.

    Args:
        obj: Any JSON-serializable object

    Returns:
        Hex-encoded SHA-256 hash (64 characters)
    """
    canonical_str = canonicalize_json(obj)
    return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()


def hash_file(file_path: str) -> str:
    """Compute SHA-256 hash of file contents.

    Args:
        file_path: Path to file

    Returns:
        Hex-encoded SHA-256 hash
    """
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_hash_chain(entries: list, prev_hash_key: str = "prev_hash") -> bool:
    """Verify hash chain integrity.

    Args:
        entries: List of ledger entries (dicts)
        prev_hash_key: Key name for previous hash field

    Returns:
        True if chain is valid, False otherwise
    """
    if not entries:
        return True

    # First entry should have prev_hash = "0" * 64 (genesis)
    if entries[0].get(prev_hash_key) != "0" * 64:
        return False

    for i in range(1, len(entries)):
        # Compute hash of previous entry (excluding signature field)
        prev_entry = {k: v for k, v in entries[i-1].items() if k != "signature"}
        expected_prev_hash = hash_json(prev_entry)

        # Check if current entry's prev_hash matches
        actual_prev_hash = entries[i].get(prev_hash_key)
        if actual_prev_hash != expected_prev_hash:
            return False

    return True


def compute_chain_signature(entry: Dict, prev_hash: str) -> str:
    """Compute signature for hash chain entry.

    Args:
        entry: Ledger entry (without signature field)
        prev_hash: Hash of previous entry

    Returns:
        SHA-256 hash of (prev_hash + canonical_entry)
    """
    entry_with_prev = {"prev_hash": prev_hash, **entry}
    return hash_json(entry_with_prev)


__all__ = [
    "canonicalize_json",
    "hash_json",
    "hash_file",
    "verify_hash_chain",
    "compute_chain_signature",
]
