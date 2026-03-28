from __future__ import annotations

from abx.interface.types import CrossBoundaryMismatchRecord


def build_cross_boundary_mismatch_records() -> list[CrossBoundaryMismatchRecord]:
    return [
        CrossBoundaryMismatchRecord("mm.001", "hf.005", "MISMATCHED_DELIVERY", "sender authority differs from receiver authority"),
        CrossBoundaryMismatchRecord("mm.002", "hf.006", "REJECTED_DELIVERY", "payload rejected by semantic validator"),
        CrossBoundaryMismatchRecord("mm.003", "hf.007", "REORDERED_DELIVERY", "events applied out of expected sequence"),
    ]
