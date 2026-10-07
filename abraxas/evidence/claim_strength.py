"""What a claim is worth: how it was assessed, how far it reaches, how long it lasts.

A grade says where data came from. It does not say how strongly the claim built on that data is
supported, how far it generalises, or whether it is still true. Those are three separate
properties, and the literature on evaluation claims proposes exactly them:

* **formality** -- a human assessment is stronger evidence than an automated metric
* **scope**     -- a result applies to the tested distribution, not universally
* **validity**  -- a result expires as contamination accumulates and distributions shift

`grounding` records the evidence environment the claim rests on, reusing the LAB/RESEARCH/FIELD
vocabulary of ``docs/DOCTRINE.md`` so there is one vocabulary rather than two.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from abraxas.evidence.data_grade import DERIVED, REAL, SIMULATED

#: Strongest first.
FORMALITY_TIERS = ("assessed", "verified", "automated")

#: Evidence environments. `research` is declared but has NO producing mechanism yet -- see
#: docs/research/DOCTRINE_GAPS_LITERATURE.md, which records this as an open gap.
GROUNDING_LEVELS = ("field", "research", "lab", "derived")

_GROUNDING_BY_GRADE = {REAL: "field", SIMULATED: "lab", DERIVED: "derived"}


def groundings_for(grade: object) -> Optional[str]:
    """The grounding level implied by a data grade, or ``None`` when nothing was declared."""
    from abraxas.evidence.data_grade import normalize_grade

    return _GROUNDING_BY_GRADE.get(normalize_grade(grade))


@dataclass(frozen=True)
class ClaimStrength:
    """How strong a claim is. Declared, never inferred."""

    formality: str
    scope: str
    validity_days: int
    grounding: str
    declared_at_utc: Optional[str] = None

    def __post_init__(self) -> None:
        if self.formality not in FORMALITY_TIERS:
            raise ValueError(
                f"formality must be one of {FORMALITY_TIERS}, got {self.formality!r}"
            )
        if self.grounding not in GROUNDING_LEVELS:
            raise ValueError(
                f"grounding must be one of {GROUNDING_LEVELS}, got {self.grounding!r}"
            )
        if not self.scope or not str(self.scope).strip():
            raise ValueError("scope must not be blank -- state what the claim covers")
        if int(self.validity_days) <= 0:
            raise ValueError(f"validity_days must be positive, got {self.validity_days!r}")

    def is_expired(self, *, now: Optional[datetime] = None) -> bool:
        """Whether the claim's validity window has elapsed.

        ``now`` is injectable so callers and tests can pin the clock. An UNDECLARED declaration time
        is treated as expired: absence is not a licence to assume freshness.
        """
        if not self.declared_at_utc:
            return True
        try:
            declared = datetime.fromisoformat(self.declared_at_utc.replace("Z", "+00:00"))
        except ValueError:
            return True
        if declared.tzinfo is None:
            declared = declared.replace(tzinfo=timezone.utc)
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        return current > declared + timedelta(days=int(self.validity_days))
