"""
SDCT v0.1 - TextSubwordCartridge (Cartridge #0)

Wraps the existing ASE text/anagram logic as a domain cartridge.
Extracts subword motifs from text tokens using letter-pool containment.

This is the reference implementation for SDCT cartridges.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set

from ..lexicon import Lexicon, build_default_lexicon
from ..lexicon_runtime import load_canary_words
from ..normalize import (
    extract_tokens,
    filter_token,
    is_stopish,
    normalize_token,
    split_hyphenated,
)
from ..scoring import letter_entropy, token_anagram_potential

from .cartridge import BaseCartridge
from .types import DomainDescriptor, Motif, NormalizedEvidence, RawItem


# -----------------------------------------------------------------------------
# SymbolObject: domain-specific internal representation
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class TokenInfo:
    """Information about a single token."""

    token: str  # Normalized token text
    letters_sorted: str  # Sorted letter pool
    length: int
    unique_letters: int
    letter_entropy: float
    tap: float  # Token Anagram Potential


@dataclass(frozen=True)
class TextSymbol:
    """
    Domain-specific symbol object for text.subword domain.

    Contains all tokens extracted from an item, with their letter pools.
    """

    item_id: str
    source: str
    tokens: tuple[TokenInfo, ...]  # Immutable, deterministically ordered

    def get_letter_pools(self) -> Dict[str, Counter]:
        """Get letter pool Counter for each token."""
        return {t.token: Counter(t.letters_sorted) for t in self.tokens}


# -----------------------------------------------------------------------------
# TextSubwordCartridge
# -----------------------------------------------------------------------------


class TextSubwordCartridge(BaseCartridge[TextSymbol]):
    """
    Text Subword Motif Cartridge (Cartridge #0).

    Extracts subword motifs from text tokens via letter-pool containment.
    This is the ASE Tier-2 matching logic wrapped as a cartridge.

    Configuration:
        - min_token_len: Minimum token length (default: 4)
        - min_sub_len: Minimum subword length (default: 3)
        - lexicon: Lexicon with stopwords and core subwords
        - canary_subwords: Additional canary-lane subwords
    """

    DOMAIN_ID = "text.subword.v1"
    DOMAIN_VERSION = "1.0.0"

    def __init__(
        self,
        *,
        lexicon: Optional[Lexicon] = None,
        canary_subwords: Optional[FrozenSet[str]] = None,
        min_token_len: int = 4,
        min_sub_len: int = 3,
    ) -> None:
        self._lexicon = lexicon or build_default_lexicon()
        self._canary_subwords = canary_subwords or frozenset()
        self._min_token_len = min_token_len
        self._min_sub_len = min_sub_len

        # Pre-compute sorted subword lists for determinism
        self._core_subs = tuple(
            sorted(w for w in self._lexicon.subwords if len(w) >= self._min_sub_len)
        )
        self._canary_subs = tuple(
            sorted(
                w
                for w in self._canary_subwords
                if len(w) >= self._min_sub_len and w not in self._lexicon.subwords
            )
        )
        self._all_subs = self._core_subs + self._canary_subs

    def descriptor(self) -> DomainDescriptor:
        return DomainDescriptor(
            domain_id=self.DOMAIN_ID,
            domain_name="Text Subword Motifs",
            domain_version=self.DOMAIN_VERSION,
            motif_kind="subword",
            alphabet="a-z",
            constraints=frozenset(
                [
                    "alpha_only",
                    f"min_token_len>={self._min_token_len}",
                    f"min_sub_len>={self._min_sub_len}",
                ]
            ),
            params_schema_id="sdct.text_subword.params.v0",
        )

    def encode(self, item: RawItem) -> TextSymbol:
        """
        Encode a raw item into a TextSymbol.

        Extracts all valid tokens with their letter pools.
        """
        blob = f"{item.title}\n{item.text}"
        raw_tokens = extract_tokens(blob)

        tokens: List[TokenInfo] = []
        seen: Set[str] = set()  # Dedupe by (token, letters)

        for raw in raw_tokens:
            nt = normalize_token(raw)
            if not nt:
                continue
            if is_stopish(nt, set(self._lexicon.stopwords)):
                continue

            # Include joined hyphenated token + split parts
            candidates = [nt]
            if "-" in nt:
                candidates.extend(split_hyphenated(nt))

            for t in candidates:
                if not filter_token(t, min_len=self._min_token_len):
                    continue

                ls = self._letters_sorted(t)
                if not ls:
                    continue

                key = (t, ls)
                if key in seen:
                    continue
                seen.add(key)

                ent = letter_entropy(ls)
                ul = len(set(ls))
                tap = token_anagram_potential(len(ls), ul)

                tokens.append(
                    TokenInfo(
                        token=t,
                        letters_sorted=ls,
                        length=len(ls),
                        unique_letters=ul,
                        letter_entropy=float(ent),
                        tap=float(tap),
                    )
                )

        # Deterministic ordering
        tokens_sorted = sorted(tokens, key=lambda x: (x.letters_sorted, x.token))

        return TextSymbol(
            item_id=item.id,
            source=item.source,
            tokens=tuple(tokens_sorted),
        )

    def extract_motifs(self, symbol: TextSymbol) -> List[Motif]:
        """
        Extract subword motifs from tokens via letter-pool containment.

        For each token, find all subwords that can be spelled from its letters.
        """
        motifs: List[Motif] = []
        seen: Set[str] = set()  # Dedupe by motif_id

        for token_info in symbol.tokens:
            parent_letters = Counter(token_info.letters_sorted)

            for sub in self._all_subs:
                if not self._can_spell(parent_letters, sub):
                    continue

                lane = "core" if sub in self._lexicon.subwords else "canary"
                motif_id = self.make_motif_id(sub)

                if motif_id in seen:
                    continue
                seen.add(motif_id)

                # Complexity: ratio of subword length to token length (normalized)
                complexity = len(sub) / max(token_info.length, 1)

                motifs.append(
                    Motif(
                        domain_id=self.DOMAIN_ID,
                        motif_id=motif_id,
                        motif_text=sub,
                        motif_len=len(sub),
                        motif_complexity=complexity,
                        lane_hint=lane,
                        metadata={
                            "source_token": token_info.token,
                            "tap": token_info.tap,
                        },
                    )
                )

        # Deterministic ordering by (lane, motif_text)
        return sorted(motifs, key=lambda m: (m.lane_hint, m.motif_text))

    def emit_evidence(
        self,
        item: RawItem,
        motifs: List[Motif],
        event_key: str,
    ) -> List[NormalizedEvidence]:
        """
        Emit normalized evidence for each motif.

        Each motif-item pair produces one NormalizedEvidence row.
        """
        evidence: List[NormalizedEvidence] = []

        for motif in motifs:
            # Extract TAP from metadata if present
            tap = motif.metadata.get("tap", 0.0) if motif.metadata else 0.0

            evidence.append(
                NormalizedEvidence(
                    domain_id=self.DOMAIN_ID,
                    motif_id=motif.motif_id,
                    item_id=item.id,
                    source=item.source,
                    event_key=event_key,
                    mentions=1,
                    signals={"tap": float(tap)},
                    tags={
                        "lane": motif.lane_hint,
                        "tier": 2,
                    },
                )
            )

        # Deterministic ordering
        return sorted(
            evidence, key=lambda e: (e.motif_id, e.source, e.item_id)
        )

    # -------------------------------------------------------------------------
    # Helpers (same logic as engine.py)
    # -------------------------------------------------------------------------

    @staticmethod
    def _letters_sorted(tok: str) -> str:
        """Get sorted letter pool for a token."""
        bare = tok.replace("-", "").replace("'", "")
        return "".join(sorted(bare))

    @staticmethod
    def _can_spell(parent_letters: Counter, sub: str) -> bool:
        """Check if subword can be spelled from parent letter pool."""
        need = Counter(sub)
        for ch, n in need.items():
            if parent_letters.get(ch, 0) < n:
                return False
        return True


# -----------------------------------------------------------------------------
# Factory function for common configurations
# -----------------------------------------------------------------------------


def create_text_subword_cartridge(
    *,
    lexicon: Optional[Lexicon] = None,
    lanes_dir: Optional[str] = None,
    min_token_len: int = 4,
    min_sub_len: int = 3,
) -> TextSubwordCartridge:
    """
    Create a TextSubwordCartridge with common configuration.

    Args:
        lexicon: Custom lexicon (uses default if None)
        lanes_dir: Path to lanes directory for canary words
        min_token_len: Minimum token length
        min_sub_len: Minimum subword length

    Returns:
        Configured TextSubwordCartridge instance
    """
    lex = lexicon or build_default_lexicon()
    canary_words: FrozenSet[str] = frozenset()

    if lanes_dir:
        from pathlib import Path

        canary_words = frozenset(load_canary_words(Path(lanes_dir)))

    return TextSubwordCartridge(
        lexicon=lex,
        canary_subwords=canary_words,
        min_token_len=min_token_len,
        min_sub_len=min_sub_len,
    )
