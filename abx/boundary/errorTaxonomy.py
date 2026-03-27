from __future__ import annotations

from abx.boundary.types import BoundaryErrorRecord


ERRORS = {
    "BOUNDARY_MALFORMED": ("HIGH", "validation"),
    "BOUNDARY_PARTIAL": ("MEDIUM", "validation"),
    "BOUNDARY_STALE": ("MEDIUM", "timeliness"),
    "BOUNDARY_UNTRUSTED": ("HIGH", "trust"),
    "BOUNDARY_UNKNOWN_TRUST": ("MEDIUM", "trust"),
    "BOUNDARY_REJECTED": ("HIGH", "enforcement"),
}


def make_error(code: str, message: str) -> BoundaryErrorRecord:
    severity, category = ERRORS.get(code, ("MEDIUM", "unknown"))
    return BoundaryErrorRecord(code=code, severity=severity, category=category, message=message)
