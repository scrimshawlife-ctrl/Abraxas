"""Which settlements a capability has reached -- declared, and cited.

`docs/DOCTRINE.md` defines three settlements every capability seeks: **empirical** (is the claim
supported by evidence), **technical** (does it reliably meet specification) and **economic** (does
it produce consequences someone adopts). Nothing recorded which ones had been reached.

Attached to the engine manifest rather than to a new artefact type: the manifest is already the
single source of truth for engine topology, and a second home for per-capability facts is the defect
its own docstring was written to fix.

A `settled` value MUST cite evidence. The literature measured that documentation fields covering
limitations and evaluation have the lowest fill-out rates in the wild, so a field like this decays
unless something enforces it -- the tests do.

aether is deliberately the refusing PLANNED case (see sibling SPEC §5). chronos/resonance now have real providers; aether remains the fail-closed example. They are intentionally UNSETTLED on empirical/economic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

SETTLED = "settled"
UNSETTLED = "unsettled"
NOT_APPLICABLE = "not_applicable"

SETTLEMENT_VALUES = (SETTLED, UNSETTLED, NOT_APPLICABLE)


@dataclass(frozen=True)
class Settlement:
    """The three settlements for one capability, with the evidence for each.

    ``<name>_evidence`` holds repo-relative paths supporting a `settled` claim. `unsettled` and
    `not_applicable` require no evidence -- the honest state is allowed to be empty.
    """

    empirical: str = UNSETTLED
    technical: str = UNSETTLED
    economic: str = UNSETTLED
    empirical_evidence: Tuple[str, ...] = field(default_factory=tuple)
    technical_evidence: Tuple[str, ...] = field(default_factory=tuple)
    economic_evidence: Tuple[str, ...] = field(default_factory=tuple)
