"""Dynamic compression router with codec selection.

Performance Drop v1.0 - Intelligent compression codec selection.
Performance Tuning Plane v0.1 - Reads ACTIVE tuning IR for per-source settings.
"""

from __future__ import annotations

import gzip
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from abraxas.storage.entropy import estimate_entropy, estimate_repetition


Codec = Literal["zstd", "gzip", "lz4", "none"]

# Import tuning IR loader (optional - graceful degradation)
try:
    from abraxas.tuning.perf_ir import load_active_tuning_ir
    TUNING_AVAILABLE = True
except ImportError:
    TUNING_AVAILABLE = False
    load_active_tuning_ir = None


@dataclass(frozen=True)
class CompressionChoice:
    """Compression codec choice with metadata."""

    codec: Codec
    level: int
    dict_path: Path | None
    reason: str


def choose_codec(
    raw_bytes: bytes,
    *,
    source_id: str | None = None,
    dict_path: Path | None = None,
    force_codec: Codec | None = None,
) -> CompressionChoice:
    """Choose optimal compression codec based on content characteristics.

    Performance Tuning Plane v0.1: Reads ACTIVE tuning IR for per-source settings.

    Args:
        raw_bytes: Raw byte content to compress
        source_id: Optional source identifier for source-specific tuning
        dict_path: Optional zstd dictionary path
        force_codec: Force a specific codec (bypasses heuristics)

    Returns:
        CompressionChoice with codec, level, and reasoning
    """
    # Load tuning IR if available
    tuning_ir = None
    if TUNING_AVAILABLE and load_active_tuning_ir:
        try:
            tuning_ir = load_active_tuning_ir()
        except Exception:
            pass  # Graceful degradation if tuning not configured

    if force_codec:
        return CompressionChoice(
            codec=force_codec,
            level=3 if force_codec != "none" else 0,
            dict_path=dict_path if force_codec == "zstd" else None,
            reason=f"forced:{force_codec}",
        )

    # Already-compressed detection
    if len(raw_bytes) >= 2:
        header = raw_bytes[:2]
        if header == b"\x1f\x8b":  # gzip magic
            return CompressionChoice(
                codec="none", level=0, dict_path=None, reason="already_gzip"
            )
        if header == b"PK":  # zip/jar magic
            return CompressionChoice(
                codec="none", level=0, dict_path=None, reason="already_zip"
            )

    # Estimate entropy and repetition
    entropy = estimate_entropy(raw_bytes)
    repetition = estimate_repetition(raw_bytes)

    # High entropy = already compressed or random
    if entropy > 7.5:
        return CompressionChoice(
            codec="none", level=0, dict_path=None, reason=f"high_entropy:{entropy:.2f}"
        )

    # High repetition = good zstd candidate
    if repetition > 0.3 and dict_path and dict_path.exists():
        # Use tuning IR level if available
        level = tuning_ir.knobs.zstd_level_cold if tuning_ir else 3
        return CompressionChoice(
            codec="zstd",
            level=level,
            dict_path=dict_path,
            reason=f"high_repetition:{repetition:.2f},tuned_level={level}",
        )

    # Default: zstd with tuned level (or level 3 if no tuning)
    default_level = tuning_ir.knobs.zstd_level_cold if tuning_ir else 3
    return CompressionChoice(
        codec="zstd",
        level=default_level,
        dict_path=dict_path if dict_path and dict_path.exists() else None,
        reason=f"default,tuned_level={default_level}",
    )


def compress_bytes(raw_bytes: bytes, choice: CompressionChoice) -> bytes:
    """Compress bytes using chosen codec.

    Args:
        raw_bytes: Raw byte content
        choice: Compression choice from choose_codec()

    Returns:
        Compressed bytes
    """
    if choice.codec == "none":
        return raw_bytes

    if choice.codec == "gzip":
        return gzip.compress(raw_bytes, compresslevel=choice.level)

    if choice.codec == "zstd":
        # Zstd with optional dictionary
        try:
            import zstandard as zstd
        except ImportError:
            # Fallback to gzip if zstd not available
            return gzip.compress(raw_bytes, compresslevel=choice.level)

        if choice.dict_path:
            with open(choice.dict_path, "rb") as f:
                dict_data = zstd.ZstdCompressionDict(f.read())
            compressor = zstd.ZstdCompressor(level=choice.level, dict_data=dict_data)
        else:
            compressor = zstd.ZstdCompressor(level=choice.level)

        return compressor.compress(raw_bytes)

    if choice.codec == "lz4":
        # LZ4 for hot path (not implemented yet - fallback to gzip)
        return gzip.compress(raw_bytes, compresslevel=1)

    raise ValueError(f"Unknown codec: {choice.codec}")


def decompress_bytes(compressed_bytes: bytes, codec: Codec) -> bytes:
    """Decompress bytes using specified codec.

    Args:
        compressed_bytes: Compressed byte content
        codec: Codec used for compression

    Returns:
        Decompressed bytes
    """
    if codec == "none":
        return compressed_bytes

    if codec == "gzip":
        return gzip.decompress(compressed_bytes)

    if codec == "zstd":
        try:
            import zstandard as zstd
        except ImportError:
            raise RuntimeError("zstandard library required for zstd decompression")

        decompressor = zstd.ZstdDecompressor()
        return decompressor.decompress(compressed_bytes)

    if codec == "lz4":
        # LZ4 decompression (not implemented yet - assume gzip fallback)
        return gzip.decompress(compressed_bytes)

    raise ValueError(f"Unknown codec: {codec}")
