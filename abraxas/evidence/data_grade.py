"""The data-grade taxonomy -- the single home for how strong a data claim is.

Why this exists
---------------
`data_grade` was a bare string defaulting to `"real"` in three models and coerced with
`or "real"` at seven call sites. The consequence: a packet that declared NOTHING was read as
`"real"` -- observed in the world, the strongest grade available. The absence of a declaration
became the strongest possible claim.

That is fail-open, and it inverts this repository's own doctrine (`docs/DOCTRINE.md`): the
producer's declaration determines evidentiary meaning, not a default. It also contradicts the
stance taken elsewhere here -- `abraxas/engines/manifest.py` holds that a `planned` engine
"must never be presented as available".

Grades
------
`real`        Observed in the world. The only grade that declares an observation.
`derived`     Computed from other data; carries no independent observation of its own.
`simulated`   Synthetic or model-generated (a LAB artefact).
`undeclared`  Nobody said. This is NOT a grade -- it is the absence of one, and it may not be
              read as a claim of any strength.

`undeclared` is deliberately the weakest member of every aggregate, so a single undeclared
input cannot be averaged away.
"""

from __future__ import annotations

from typing import Iterable

REAL = "real"
DERIVED = "derived"
SIMULATED = "simulated"
UNDECLARED = "undeclared"

#: Every value the taxonomy recognises. Anything else normalises to `UNDECLARED`.
GRADES = frozenset({REAL, DERIVED, SIMULATED, UNDECLARED})

#: Total order, strongest first. `undeclared` ranks below every real grade so it can never be
#: averaged away by stronger neighbours.
_STRENGTH = {REAL: 3, DERIVED: 2, SIMULATED: 1, UNDECLARED: 0}


def normalize_grade(value: object) -> str:
    """Map any declared value to a member of :data:`GRADES`.

    Absence, blank strings and unrecognised values all become `UNDECLARED`. An unrecognised value
    is NOT guessed at: a typo like `"reel"` must not silently become the strongest grade.
    """
    if value is None or isinstance(value, bool):
        return UNDECLARED
    text = str(value).strip().lower()
    return text if text in GRADES else UNDECLARED


def weakest_grade(grades: Iterable[object]) -> str:
    """The weakest declared grade in `grades`.

    Weakest-link aggregation: an aggregate is only as strong as its weakest member. An empty
    iterable is `UNDECLARED` -- nothing declared, so nothing is claimed.
    """
    normalized = [normalize_grade(g) for g in grades]
    if not normalized:
        return UNDECLARED
    return min(normalized, key=lambda grade: _STRENGTH[grade])


def declares_observation(grade: object) -> bool:
    """Whether this grade claims an observation of the world.

    Only `real` does. Everything else -- including `undeclared` -- supports no such claim.
    """
    return normalize_grade(grade) == REAL


__all__ = [
    "REAL",
    "DERIVED",
    "SIMULATED",
    "UNDECLARED",
    "GRADES",
    "normalize_grade",
    "weakest_grade",
    "declares_observation",
]
