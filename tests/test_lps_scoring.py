from __future__ import annotations

from abraxas_ase.lps import LPSParams, compute_lps, lane_decision


def test_lane_progression_is_gated() -> None:
    p = LPSParams()
    lps = compute_lps(
        tap_max=0.0,
        sas_sum=25.0,
        pfdi_max=0.0,
        days_seen=7,
        sources_count=2,
        events_count=2,
        mentions_total=14,
        params=p,
    )
    lane = lane_decision(lps=lps, days_seen=7, sources_count=2, events_count=2, params=p)
    assert lane in ("canary", "shadow", "candidate")


def test_core_requires_strict_gates() -> None:
    p = LPSParams()
    lane = lane_decision(lps=99.0, days_seen=5, sources_count=5, events_count=5, params=p)
    assert lane != "core"


def test_lps_is_deterministic() -> None:
    p = LPSParams()
    first = compute_lps(
        tap_max=0.2,
        sas_sum=3.0,
        pfdi_max=1.0,
        days_seen=4,
        sources_count=2,
        events_count=3,
        mentions_total=6,
        params=p,
    )
    second = compute_lps(
        tap_max=0.2,
        sas_sum=3.0,
        pfdi_max=1.0,
        days_seen=4,
        sources_count=2,
        events_count=3,
        mentions_total=6,
        params=p,
    )
    assert first == second
