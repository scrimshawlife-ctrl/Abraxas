"""Storage package - Events + CAS (both acquisition and performance APIs)."""

from __future__ import annotations

# Acquisition CAS (class-based)
from .cas import CASIndexEntry, CASRef, CASStore

# Performance CAS (function-based)
from .cas import cas_put_bytes, cas_get_bytes, cas_put_json, cas_get_json, cas_exists

# Hashing utilities
from .hashes import stable_hash_bytes, stable_hash_json

# Packet codec
from .packet_codec import encode_packet, decode_packet, write_packet, read_packet

# Compression
from .compress import choose_codec, compress_bytes, decompress_bytes

# Deduplication
from .dedup import shingle_hashes, near_dup_score, dedup_items

# Dictionary training
from .dict_train import train_zstd_dict, should_retrain_dict

__all__ = [
    # Events (lazy loaded)
    "write_events_jsonl",
    "read_events_jsonl",
    # Acquisition CAS (class-based)
    "CASIndexEntry",
    "CASRef",
    "CASStore",
    # Performance CAS (function-based)
    "cas_put_bytes",
    "cas_get_bytes",
    "cas_put_json",
    "cas_get_json",
    "cas_exists",
    # Hashing
    "stable_hash_bytes",
    "stable_hash_json",
    # Packet codec
    "encode_packet",
    "decode_packet",
    "write_packet",
    "read_packet",
    # Compression
    "choose_codec",
    "compress_bytes",
    "decompress_bytes",
    # Dedup
    "shingle_hashes",
    "near_dup_score",
    "dedup_items",
    # Dictionary training
    "train_zstd_dict",
    "should_retrain_dict",
]


def __getattr__(name: str):
    """Lazy load events utilities."""
    if name in {"write_events_jsonl", "read_events_jsonl"}:
        from .events import read_events_jsonl, write_events_jsonl

        return {"write_events_jsonl": write_events_jsonl, "read_events_jsonl": read_events_jsonl}[name]
    raise AttributeError(f"module 'abraxas.storage' has no attribute {name}")
