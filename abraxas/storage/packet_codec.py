"""Packet serialization optimization with CBOR/MsgPack + Zstd.

Performance Drop v1.0 - Deterministic packet encoding.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from abraxas.storage.compress import Codec, CompressionChoice, choose_codec, compress_bytes, decompress_bytes
from abraxas.storage.hashes import stable_hash_json
from abraxas.storage.layout import ensure_cas_dirs, get_cas_path, parse_timestamp_components


SerializationFormat = Literal["cbor", "msgpack", "json"]


def encode_packet(packet_obj: Any, fmt: SerializationFormat = "cbor") -> bytes:
    """Encode packet object to bytes using specified format.

    Args:
        packet_obj: Packet object (dict, list, etc.)
        fmt: Serialization format (cbor, msgpack, json)

    Returns:
        Encoded bytes
    """
    if fmt == "cbor":
        try:
            import cbor2
            return cbor2.dumps(packet_obj)
        except ImportError:
            # Fallback to JSON if cbor2 not available
            fmt = "json"

    if fmt == "msgpack":
        try:
            import msgpack
            return msgpack.packb(packet_obj, use_bin_type=True)
        except ImportError:
            # Fallback to JSON if msgpack not available
            fmt = "json"

    if fmt == "json":
        # Canonical JSON for determinism
        return json.dumps(packet_obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

    raise ValueError(f"Unknown serialization format: {fmt}")


def decode_packet(raw_bytes: bytes, fmt: SerializationFormat = "cbor") -> Any:
    """Decode packet bytes to object using specified format.

    Args:
        raw_bytes: Encoded bytes
        fmt: Serialization format (cbor, msgpack, json)

    Returns:
        Decoded packet object
    """
    if fmt == "cbor":
        try:
            import cbor2
            return cbor2.loads(raw_bytes)
        except ImportError:
            fmt = "json"

    if fmt == "msgpack":
        try:
            import msgpack
            return msgpack.unpackb(raw_bytes, raw=False)
        except ImportError:
            fmt = "json"

    if fmt == "json":
        return json.loads(raw_bytes.decode("utf-8"))

    raise ValueError(f"Unknown serialization format: {fmt}")


def write_packet(
    source_id: str,
    window_id: str,
    packet_obj: Any,
    *,
    timestamp_utc: str | None = None,
    codec_choice: CompressionChoice | None = None,
    fmt: SerializationFormat = "cbor",
) -> Path:
    """Write packet to CAS with compression.

    Args:
        source_id: Source identifier
        window_id: Window identifier (used as filename component)
        packet_obj: Packet object to encode
        timestamp_utc: Optional timestamp for temporal partitioning
        codec_choice: Optional compression choice (defaults to choose_codec)
        fmt: Serialization format (default: cbor)

    Returns:
        Path to written packet file
    """
    # Encode packet
    raw_bytes = encode_packet(packet_obj, fmt=fmt)

    # Choose codec
    if codec_choice is None:
        codec_choice = choose_codec(raw_bytes, source_id=source_id)

    # Compress
    compressed_bytes = compress_bytes(raw_bytes, codec_choice)

    # Compute hash of packet object for provenance
    packet_hash = stable_hash_json(packet_obj)

    # Determine path
    year, month = None, None
    if timestamp_utc:
        year, month = parse_timestamp_components(timestamp_utc)

    ext = f"packet.{fmt}.{codec_choice.codec}"
    path = get_cas_path(
        "packets",
        source_id,
        packet_hash,
        year=year,
        month=month,
        ext=ext,
    )
    ensure_cas_dirs(path)

    # Write compressed packet
    with open(path, "wb") as f:
        f.write(compressed_bytes)

    # Write metadata sidecar
    meta_path = path.with_suffix(path.suffix + ".meta.json")
    meta = {
        "source_id": source_id,
        "window_id": window_id,
        "packet_hash": packet_hash,
        "format": fmt,
        "codec": codec_choice.codec,
        "codec_level": codec_choice.level,
        "codec_reason": codec_choice.reason,
        "raw_size": len(raw_bytes),
        "compressed_size": len(compressed_bytes),
        "compression_ratio": len(raw_bytes) / len(compressed_bytes) if compressed_bytes else 1.0,
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2, sort_keys=True)

    return path


def read_packet(packet_path: Path) -> Any:
    """Read packet from CAS.

    Args:
        packet_path: Path to packet file

    Returns:
        Decoded packet object
    """
    # Read metadata to determine format and codec
    meta_path = packet_path.with_suffix(packet_path.suffix + ".meta.json")
    if not meta_path.exists():
        raise ValueError(f"Missing metadata for packet: {packet_path}")

    with open(meta_path, "r") as f:
        meta = json.load(f)

    fmt: SerializationFormat = meta["format"]
    codec: Codec = meta["codec"]

    # Read compressed bytes
    with open(packet_path, "rb") as f:
        compressed_bytes = f.read()

    # Decompress
    raw_bytes = decompress_bytes(compressed_bytes, codec)

    # Decode
    return decode_packet(raw_bytes, fmt=fmt)
