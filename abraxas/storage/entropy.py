"""Entropy estimation for compression codec selection.

Performance Drop v1.0 - Lightweight entropy heuristics.
"""

from __future__ import annotations

import collections
import math


def estimate_entropy(raw_bytes: bytes) -> float:
    """Estimate Shannon entropy of byte stream.

    Uses byte-level histogram for fast approximation.

    Args:
        raw_bytes: Raw byte content

    Returns:
        Estimated entropy (0.0 to 8.0 bits per byte)
    """
    if not raw_bytes:
        return 0.0

    counts = collections.Counter(raw_bytes)
    total = len(raw_bytes)

    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)

    return entropy


def estimate_repetition(raw_bytes: bytes, window_size: int = 64) -> float:
    """Estimate repetition rate using sliding window.

    Args:
        raw_bytes: Raw byte content
        window_size: Sliding window size (default: 64)

    Returns:
        Repetition score (0.0 = no repetition, 1.0 = high repetition)
    """
    if len(raw_bytes) < window_size * 2:
        return 0.0

    seen_windows: set[bytes] = set()
    repeats = 0
    total_windows = 0

    for i in range(len(raw_bytes) - window_size + 1):
        window = raw_bytes[i : i + window_size]
        if window in seen_windows:
            repeats += 1
        else:
            seen_windows.add(window)
        total_windows += 1

    return repeats / total_windows if total_windows > 0 else 0.0
