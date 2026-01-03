"""Stream deduplication using shingling for text and events.

Performance Drop v1.0 - Deterministic near-duplicate detection.
"""

from __future__ import annotations

import hashlib
from typing import Any, TypeVar


T = TypeVar("T")


def shingle_hashes(text: str, k: int = 5) -> set[int]:
    """Compute k-shingle hashes for text.

    Args:
        text: Input text
        k: Shingle size (default: 5 characters)

    Returns:
        Set of shingle hashes
    """
    if len(text) < k:
        # For very short text, just hash the whole thing
        return {hash(text)}

    shingles = set()
    for i in range(len(text) - k + 1):
        shingle = text[i : i + k]
        # Use deterministic hash
        shingle_hash = int(hashlib.sha256(shingle.encode("utf-8")).hexdigest()[:16], 16)
        shingles.add(shingle_hash)

    return shingles


def near_dup_score(text_a: str, text_b: str, k: int = 5) -> float:
    """Compute Jaccard similarity between two texts using shingling.

    Args:
        text_a: First text
        text_b: Second text
        k: Shingle size (default: 5)

    Returns:
        Similarity score (0.0 to 1.0)
    """
    shingles_a = shingle_hashes(text_a, k=k)
    shingles_b = shingle_hashes(text_b, k=k)

    if not shingles_a and not shingles_b:
        return 1.0  # Both empty

    intersection = len(shingles_a & shingles_b)
    union = len(shingles_a | shingles_b)

    return intersection / union if union > 0 else 0.0


def dedup_items(
    items: list[T],
    text_extractor: callable[[T], str],
    *,
    threshold: float = 0.9,
    k: int = 5,
) -> tuple[list[T], dict[int, int]]:
    """Deduplicate items based on text similarity.

    Args:
        items: List of items to deduplicate
        text_extractor: Function to extract text from item
        threshold: Similarity threshold for deduplication (default: 0.9)
        k: Shingle size (default: 5)

    Returns:
        Tuple of (kept_items, dropped_refs)
        dropped_refs maps dropped item index -> kept item index
    """
    if not items:
        return [], {}

    kept: list[T] = []
    kept_shingles: list[set[int]] = []
    dropped_refs: dict[int, int] = {}

    for idx, item in enumerate(items):
        text = text_extractor(item)
        shingles = shingle_hashes(text, k=k)

        # Check against kept items
        is_dup = False
        for kept_idx, kept_shingle_set in enumerate(kept_shingles):
            intersection = len(shingles & kept_shingle_set)
            union = len(shingles | kept_shingle_set)
            similarity = intersection / union if union > 0 else 0.0

            if similarity >= threshold:
                # Mark as duplicate
                dropped_refs[idx] = kept_idx
                is_dup = True
                break

        if not is_dup:
            # Keep this item
            kept.append(item)
            kept_shingles.append(shingles)

    return kept, dropped_refs
