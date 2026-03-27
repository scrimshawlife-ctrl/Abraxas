from __future__ import annotations


def build_uncertainty_vocabulary() -> dict[str, str]:
    return {
        "bounded_high": "Confidence calibrated with strong evidence and bounded risk.",
        "bounded_medium": "Confidence bounded with partial calibration and medium evidence.",
        "unbounded": "Confidence signal present but not calibration-supported.",
        "unknown": "No confidence semantics can be computed from available evidence.",
    }
