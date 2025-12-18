"""Built-in CTD (Cringe-Taxonomic-Drift) operator."""

from __future__ import annotations

import re

from abraxas.core.resonance_frame import ResonanceFrame
from abraxas.slang.models import OperatorReadout
from abraxas.slang.operators.base import Operator, OperatorStatus


class CTDOperator(Operator):
    """
    Cringe-Taxonomic-Drift operator.

    Detects patterns of affiliative play, play aggression, and cringe behaviors
    in online communication through phonetic softening, irony checksums, and
    play aggression markers.
    """

    operator_id: str = "ctd_v1"
    version: str = "1.0.0"
    status: OperatorStatus = OperatorStatus.CANONICAL

    # Pattern definitions
    PHONETIC_SOFTENING: list[str] = [
        r"\b(rawr|raar|nyaa|uwu|owo)\b",
        r"[xX][dD]",
        r"[:;][3pP]",
    ]

    IRONY_CHECKSUMS: list[str] = [
        r"\b(lol|lmao|rofl)\b",
        r"[!]{2,}",
        r"[?]{2,}",
    ]

    PLAY_AGGRESSION: list[str] = [
        r"\b(bonk|yeet|destroy|obliterate)\b",
        r"\*[^*]+\*",  # *action*
    ]

    def __init__(self, **data):
        super().__init__(**data)
        # Compile patterns for efficiency
        self._softening_patterns = [re.compile(p, re.IGNORECASE) for p in self.PHONETIC_SOFTENING]
        self._irony_patterns = [re.compile(p, re.IGNORECASE) for p in self.IRONY_CHECKSUMS]
        self._aggression_patterns = [re.compile(p, re.IGNORECASE) for p in self.PLAY_AGGRESSION]

    def apply(self, text: str, frame: ResonanceFrame | None = None) -> OperatorReadout | None:
        """
        Apply CTD operator to text.

        Returns:
            OperatorReadout with label: "affiliative", "play_aggression", or "cringe_orphan"
        """
        text_lower = text.lower()

        # Count pattern matches
        softening_hits = sum(
            1 for pattern in self._softening_patterns if pattern.search(text)
        )
        irony_hits = sum(1 for pattern in self._irony_patterns if pattern.search(text))
        aggression_hits = sum(
            1 for pattern in self._aggression_patterns if pattern.search(text)
        )

        total_hits = softening_hits + irony_hits + aggression_hits

        # No matches - operator doesn't fire
        if total_hits == 0:
            return None

        # Classification logic
        if softening_hits > 0 and irony_hits > 0:
            label = "affiliative"
            confidence = min(0.9, 0.5 + (softening_hits + irony_hits) * 0.1)
        elif aggression_hits > 0 and (softening_hits > 0 or irony_hits > 0):
            label = "play_aggression"
            confidence = min(0.85, 0.5 + aggression_hits * 0.15)
        elif total_hits > 0:
            label = "cringe_orphan"
            confidence = 0.6
        else:
            return None

        return OperatorReadout(
            operator_id=self.operator_id,
            label=label,
            confidence=confidence,
            features={
                "softening_hits": float(softening_hits),
                "irony_hits": float(irony_hits),
                "aggression_hits": float(aggression_hits),
            },
            metadata={
                "version": self.version,
                "triggers": ["phonetic_softening", "irony_checksums", "play_aggression"],
            },
        )
