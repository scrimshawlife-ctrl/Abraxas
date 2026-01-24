from __future__ import annotations

from abraxas_ase.lps import LPSParams, lane_decision


def test_core_requires_strict_gates() -> None:
    p = LPSParams()
    lane = lane_decision(lps=99.0, days_seen=5, sources_count=5, events_count=5, params=p)
    assert lane != "core"
