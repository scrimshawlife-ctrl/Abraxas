from __future__ import annotations


def explain_ownership() -> dict[str, str]:
    return {
        "surface.runtime.workflow": "runtime",
        "surface.boundary.validation": "boundary",
        "surface.operator.console": "operations",
    }
