from __future__ import annotations

from abraxas_ase.sas import SASParams, compute_sas_for_sub


def test_sas_increases_with_diversity() -> None:
    p = SASParams()
    a = compute_sas_for_sub(mentions=5, sources_count=1, events_count=1, sub_len=4, params=p)
    b = compute_sas_for_sub(mentions=5, sources_count=3, events_count=3, sub_len=4, params=p)
    assert b > a


def test_sas_is_deterministic() -> None:
    p = SASParams()
    first = compute_sas_for_sub(mentions=3, sources_count=2, events_count=2, sub_len=5, params=p)
    second = compute_sas_for_sub(mentions=3, sources_count=2, events_count=2, sub_len=5, params=p)
    assert first == second
