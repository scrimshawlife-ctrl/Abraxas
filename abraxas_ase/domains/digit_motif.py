"""
SDCT v0.1 - DigitMotifCartridge (Proof Cartridge)

A minimal cartridge that extracts digit n-grams as motifs.
This proves the SDCT template works without needing full numogram logic.

Structurally different from TextSubwordCartridge to validate the template.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Set

from .cartridge import BaseCartridge
from .types import DomainDescriptor, Motif, NormalizedEvidence, RawItem


# -----------------------------------------------------------------------------
# SymbolObject: digit-specific representation
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class DigitSequence:
    """A sequence of digits found in text."""

    digits: str  # The raw digit sequence
    position: int  # Character position in original text
    length: int


@dataclass(frozen=True)
class DigitSymbol:
    """
    Domain-specific symbol object for digit domain.

    Contains all digit sequences extracted from an item.
    """

    item_id: str
    source: str
    sequences: tuple[DigitSequence, ...]  # Immutable, deterministically ordered


# -----------------------------------------------------------------------------
# DigitMotifCartridge
# -----------------------------------------------------------------------------


# Historically significant digit patterns (for demo/proof purposes)
DEFAULT_SIGNIFICANT_PATTERNS: FrozenSet[str] = frozenset(
    {
        # Years
        "1776",
        "1984",
        "2001",
        "2012",
        "2020",
        "2024",
        "2025",
        # Significant numbers
        "666",
        "777",
        "888",
        "911",
        "1111",
        "1234",
        "4321",
        # Mathematical
        "314",  # pi
        "271",  # e
        "137",  # fine structure constant
        "1618",  # golden ratio
        # Binary/hex patterns
        "101",
        "111",
        "1010",
        "0101",
    }
)


class DigitMotifCartridge(BaseCartridge[DigitSymbol]):
    """
    Digit Motif Cartridge (Proof Cartridge).

    Extracts digit n-grams from text as motifs.
    This is a minimal implementation to prove the SDCT template works.

    Configuration:
        - min_len: Minimum digit sequence length (default: 3)
        - max_len: Maximum digit sequence length (default: 8)
        - significant_patterns: Set of "core" significant patterns
    """

    DOMAIN_ID = "digit.v1"
    DOMAIN_VERSION = "1.0.0"

    # Regex for digit sequences
    _DIGIT_RE = re.compile(r"\d+")

    def __init__(
        self,
        *,
        min_len: int = 3,
        max_len: int = 8,
        significant_patterns: FrozenSet[str] = DEFAULT_SIGNIFICANT_PATTERNS,
    ) -> None:
        self._min_len = min_len
        self._max_len = max_len
        self._significant_patterns = significant_patterns

    def descriptor(self) -> DomainDescriptor:
        return DomainDescriptor(
            domain_id=self.DOMAIN_ID,
            domain_name="Digit N-gram Motifs",
            domain_version=self.DOMAIN_VERSION,
            motif_kind="digit",
            alphabet="0-9",
            constraints=frozenset(
                [
                    "digits_only",
                    f"min_len>={self._min_len}",
                    f"max_len<={self._max_len}",
                ]
            ),
            params_schema_id="sdct.digit.params.v0",
        )

    def encode(self, item: RawItem) -> DigitSymbol:
        """
        Encode a raw item into a DigitSymbol.

        Extracts all digit sequences from title and text.
        """
        blob = f"{item.title}\n{item.text}"

        sequences: List[DigitSequence] = []
        for match in self._DIGIT_RE.finditer(blob):
            digits = match.group()
            length = len(digits)

            if length < self._min_len or length > self._max_len:
                continue

            sequences.append(
                DigitSequence(
                    digits=digits,
                    position=match.start(),
                    length=length,
                )
            )

        # Deterministic ordering by (digits, position)
        sequences_sorted = sorted(sequences, key=lambda s: (s.digits, s.position))

        return DigitSymbol(
            item_id=item.id,
            source=item.source,
            sequences=tuple(sequences_sorted),
        )

    def extract_motifs(self, symbol: DigitSymbol) -> List[Motif]:
        """
        Extract digit motifs from sequences.

        Extracts both exact sequences and significant n-gram patterns.
        """
        motifs: List[Motif] = []
        seen: Set[str] = set()

        for seq in symbol.sequences:
            # The full sequence as a motif
            motif_id = self.make_motif_id(seq.digits)
            if motif_id not in seen:
                seen.add(motif_id)

                # Determine lane based on significance
                is_significant = seq.digits in self._significant_patterns
                lane = "core" if is_significant else "candidate"

                # Complexity: based on digit entropy
                complexity = self._digit_entropy(seq.digits)

                motifs.append(
                    Motif(
                        domain_id=self.DOMAIN_ID,
                        motif_id=motif_id,
                        motif_text=seq.digits,
                        motif_len=seq.length,
                        motif_complexity=complexity,
                        lane_hint=lane,
                        metadata={
                            "is_significant": is_significant,
                            "first_position": seq.position,
                        },
                    )
                )

            # Also check for significant subsequences
            for pattern in self._significant_patterns:
                if pattern in seq.digits and pattern != seq.digits:
                    sub_motif_id = self.make_motif_id(pattern)
                    if sub_motif_id not in seen:
                        seen.add(sub_motif_id)
                        motifs.append(
                            Motif(
                                domain_id=self.DOMAIN_ID,
                                motif_id=sub_motif_id,
                                motif_text=pattern,
                                motif_len=len(pattern),
                                motif_complexity=self._digit_entropy(pattern),
                                lane_hint="core",
                                metadata={
                                    "is_significant": True,
                                    "found_in": seq.digits,
                                },
                            )
                        )

        # Deterministic ordering
        return sorted(motifs, key=lambda m: (m.lane_hint, m.motif_text))

    def emit_evidence(
        self,
        item: RawItem,
        motifs: List[Motif],
        event_key: str,
    ) -> List[NormalizedEvidence]:
        """
        Emit normalized evidence for each digit motif.
        """
        evidence: List[NormalizedEvidence] = []

        for motif in motifs:
            evidence.append(
                NormalizedEvidence(
                    domain_id=self.DOMAIN_ID,
                    motif_id=motif.motif_id,
                    item_id=item.id,
                    source=item.source,
                    event_key=event_key,
                    mentions=1,
                    signals={
                        "complexity": motif.motif_complexity,
                    },
                    tags={
                        "lane": motif.lane_hint,
                        "tier": 1,  # Digit matches are simpler than subword
                        "is_significant": motif.metadata.get("is_significant", False),
                    },
                )
            )

        # Deterministic ordering
        return sorted(evidence, key=lambda e: (e.motif_id, e.source, e.item_id))

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _digit_entropy(digits: str) -> float:
        """
        Compute normalized entropy over digit distribution.

        Returns value in [0, 1] where 1 = maximum entropy (all digits different).
        """
        if not digits:
            return 0.0

        counts: Dict[str, int] = {}
        for d in digits:
            counts[d] = counts.get(d, 0) + 1

        n = len(digits)
        h = 0.0
        for count in counts.values():
            p = count / n
            if p > 0:
                h -= p * math.log2(p)

        # Normalize by max possible entropy (log2(10) for digits 0-9)
        max_entropy = math.log2(10)
        return float(h / max_entropy) if max_entropy > 0 else 0.0


# -----------------------------------------------------------------------------
# Factory function
# -----------------------------------------------------------------------------


def create_digit_cartridge(
    *,
    min_len: int = 3,
    max_len: int = 8,
    additional_patterns: FrozenSet[str] = frozenset(),
) -> DigitMotifCartridge:
    """
    Create a DigitMotifCartridge with custom configuration.

    Args:
        min_len: Minimum digit sequence length
        max_len: Maximum digit sequence length
        additional_patterns: Additional significant patterns to add

    Returns:
        Configured DigitMotifCartridge instance
    """
    patterns = DEFAULT_SIGNIFICANT_PATTERNS | additional_patterns
    return DigitMotifCartridge(
        min_len=min_len,
        max_len=max_len,
        significant_patterns=patterns,
    )
