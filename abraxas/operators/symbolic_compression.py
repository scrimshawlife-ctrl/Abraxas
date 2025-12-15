# abraxas/operators/symbolic_compression.py
# ABRAXAS CORE MODULE
# Symbolic Compression Operator (SCO)
# Tier-1: Eggcorn Compression Operator (ECO)

from dataclasses import dataclass
from typing import List, Dict, Literal
import math


# -----------------------------
# Data Models
# -----------------------------

CompressionStatus = Literal["proto", "emergent", "stabilizing"]

@dataclass(frozen=True)
class SymbolicCompressionEvent:
    event_type: str  # "SymbolicCompressionEvent"
    original_token: str
    replacement_token: str
    domain: str
    phonetic_similarity: float
    semantic_transparency_delta: float
    intent_preservation_score: float
    compression_pressure: float
    symbolic_load_capacity: float
    replacement_direction_vector: Dict[str, float]
    status: CompressionStatus


# -----------------------------
# Core Operator
# -----------------------------

class SymbolicCompressionOperator:
    """
    SCO detects symbolic compression events where opaque symbols
    are replaced by semantically transparent substitutes while
    preserving intent.

    Eggcorns are Tier-1 events within this operator.
    """

    PHONETIC_THRESHOLD = 0.75
    INTENT_THRESHOLD = 0.70
    TRANSPARENCY_THRESHOLD = 0.15

    def __init__(self, transparency_lexicon: Dict[str, float]):
        """
        transparency_lexicon:
            token -> Symbolic Transparency Index (STI)
        """
        self.transparency_lexicon = transparency_lexicon

    # -----------------------------
    # Public API
    # -----------------------------

    def analyze(
        self,
        original_token: str,
        replacement_token: str,
        context_vector: Dict[str, float],
        phonetic_similarity: float,
        intent_preservation_score: float,
        domain: str,
        observed_frequency: int
    ) -> SymbolicCompressionEvent | None:

        transparency_delta = self._transparency_delta(
            original_token,
            replacement_token
        )

        if not self._passes_thresholds(
            phonetic_similarity,
            transparency_delta,
            intent_preservation_score
        ):
            return None

        compression_pressure = self._compression_pressure(
            phonetic_similarity,
            intent_preservation_score,
            observed_frequency
        )

        status = self._classify_status(compression_pressure)

        return SymbolicCompressionEvent(
            event_type="SymbolicCompressionEvent",
            original_token=original_token,
            replacement_token=replacement_token,
            domain=domain,
            phonetic_similarity=phonetic_similarity,
            semantic_transparency_delta=transparency_delta,
            intent_preservation_score=intent_preservation_score,
            compression_pressure=compression_pressure,
            symbolic_load_capacity=self._symbolic_load_capacity(original_token),
            replacement_direction_vector=context_vector,
            status=status
        )

    # -----------------------------
    # Internal Logic
    # -----------------------------

    def _passes_thresholds(
        self,
        phonetic_similarity: float,
        transparency_delta: float,
        intent_preservation_score: float
    ) -> bool:
        return (
            phonetic_similarity >= self.PHONETIC_THRESHOLD
            and transparency_delta >= self.TRANSPARENCY_THRESHOLD
            and intent_preservation_score >= self.INTENT_THRESHOLD
        )

    def _transparency_delta(self, original: str, replacement: str) -> float:
        return (
            self.transparency_lexicon.get(replacement, 0.0)
            - self.transparency_lexicon.get(original, 0.0)
        )

    def _compression_pressure(
        self,
        phonetic_similarity: float,
        intent_score: float,
        frequency: int
    ) -> float:
        """
        Compression Pressure (CP):
        How strongly the system is incentivized to replace the symbol.
        """
        freq_factor = math.log1p(frequency)
        return round(
            (phonetic_similarity * 0.4 + intent_score * 0.6) * freq_factor,
            4
        )

    def _symbolic_load_capacity(self, token: str) -> float:
        """
        Inverse of transparency:
        lower transparency = lower load capacity
        """
        sti = self.transparency_lexicon.get(token, 0.0)
        return round(1.0 - sti, 4)

    def _classify_status(self, compression_pressure: float) -> CompressionStatus:
        if compression_pressure < 0.8:
            return "proto"
        elif compression_pressure < 1.6:
            return "emergent"
        else:
            return "stabilizing"
