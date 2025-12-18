"""OAS Miner: extracts patterns and structures from slang clusters."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from abraxas.core.resonance_frame import ResonanceFrame
from abraxas.slang.models import SlangCluster


class MinedPattern(dict):
    """A mined pattern (dict subclass for easy JSON serialization)."""

    pass


class OASMiner:
    """
    Mines candidate operator patterns from slang clusters.

    Discovers co-occurrence patterns, drift signatures, and emergent structures.
    """

    def __init__(self, min_frequency: int = 3, min_confidence: float = 0.5):
        """
        Initialize miner.

        Args:
            min_frequency: Minimum pattern frequency to consider
            min_confidence: Minimum confidence score
        """
        self.min_frequency = min_frequency
        self.min_confidence = min_confidence

    def mine(
        self, clusters: list[SlangCluster], frames: list[ResonanceFrame]
    ) -> list[MinedPattern]:
        """
        Mine patterns from clusters and frames.

        Returns list of mined patterns with metadata.
        """
        patterns: list[MinedPattern] = []

        # Mine co-occurrence patterns
        patterns.extend(self._mine_cooccurrence(clusters))

        # Mine drift signatures (temporal patterns)
        patterns.extend(self._mine_drift_signatures(clusters, frames))

        # Mine phonetic patterns
        patterns.extend(self._mine_phonetic_patterns(clusters))

        # Sort for determinism
        patterns.sort(key=lambda p: (p.get("pattern_type", ""), p.get("signature", "")))

        return patterns

    def _mine_cooccurrence(self, clusters: list[SlangCluster]) -> list[MinedPattern]:
        """Mine token co-occurrence patterns."""
        patterns: list[MinedPattern] = []

        # Collect all token pairs from clusters
        token_pairs: Counter[tuple[str, str]] = Counter()

        for cluster in clusters:
            tokens = [t.token.lower() for t in cluster.tokens]
            for i, t1 in enumerate(tokens):
                for t2 in tokens[i + 1 :]:
                    # Deterministic ordering
                    pair = tuple(sorted([t1, t2]))
                    token_pairs[pair] += 1

        # Filter by frequency
        for pair, count in token_pairs.items():
            if count >= self.min_frequency:
                pattern = MinedPattern(
                    {
                        "pattern_type": "cooccurrence",
                        "tokens": list(pair),
                        "frequency": count,
                        "signature": f"cooc_{pair[0]}_{pair[1]}",
                    }
                )
                patterns.append(pattern)

        return patterns

    def _mine_drift_signatures(
        self, clusters: list[SlangCluster], frames: list[ResonanceFrame]
    ) -> list[MinedPattern]:
        """Mine temporal drift patterns."""
        patterns: list[MinedPattern] = []

        # Simple drift detection: look for tokens appearing in increasing frequency
        token_timeline: dict[str, list[float]] = {}

        for cluster in clusters:
            if not cluster.window:
                continue

            timestamp = cluster.window[0].timestamp()
            for token in cluster.tokens:
                token_lower = token.token.lower()
                if token_lower not in token_timeline:
                    token_timeline[token_lower] = []
                token_timeline[token_lower].append(timestamp)

        # Detect increasing trends
        for token, timestamps in token_timeline.items():
            if len(timestamps) >= self.min_frequency:
                # Simple trend: later timestamps more frequent
                timestamps_sorted = sorted(timestamps)
                # Check if there's growth in second half vs first half
                mid = len(timestamps_sorted) // 2
                first_half_rate = mid / (timestamps_sorted[mid] - timestamps_sorted[0] + 1)
                second_half_rate = (len(timestamps_sorted) - mid) / (
                    timestamps_sorted[-1] - timestamps_sorted[mid] + 1
                )

                if second_half_rate > first_half_rate * 1.5:  # 50% growth threshold
                    pattern = MinedPattern(
                        {
                            "pattern_type": "drift",
                            "token": token,
                            "frequency": len(timestamps),
                            "growth_rate": second_half_rate / first_half_rate
                            if first_half_rate > 0
                            else 0,
                            "signature": f"drift_{token}",
                        }
                    )
                    patterns.append(pattern)

        return patterns

    def _mine_phonetic_patterns(self, clusters: list[SlangCluster]) -> list[MinedPattern]:
        """Mine phonetic/orthographic patterns."""
        patterns: list[MinedPattern] = []

        # Common phonetic transformations
        phonetic_rules = [
            (r"(.)\1{2,}", "repetition"),  # Character repetition: "yaaaas"
            (r"[xX][dD]", "xd_pattern"),  # xD emoticon
            (r"[:;][3pPdD]", "emoticon"),  # :3, :P, etc.
            (r"[uU][wW][uU]", "uwu_pattern"),  # uwu
        ]

        pattern_counts: Counter[str] = Counter()

        for cluster in clusters:
            for token in cluster.tokens:
                for regex, pattern_name in phonetic_rules:
                    if re.search(regex, token.token):
                        pattern_counts[pattern_name] += 1

        for pattern_name, count in pattern_counts.items():
            if count >= self.min_frequency:
                pattern = MinedPattern(
                    {
                        "pattern_type": "phonetic",
                        "name": pattern_name,
                        "frequency": count,
                        "signature": f"phonetic_{pattern_name}",
                    }
                )
                patterns.append(pattern)

        return patterns
