from __future__ import annotations

from abraxas_ase.watchlist import WatchlistRule, default_state, evaluate_watchlist


def test_watchlist_triggering_and_decay() -> None:
    rule = WatchlistRule(
        id="sas-war",
        label="SAS surge: war",
        kind="subword",
        target="war",
        metric="sas",
        trigger_delta=0.5,
        trigger_score=1.0,
        decay_halflife_days=2,
        min_days_seen=1,
    )
    history = [
        {"date": "2026-01-23", "top_sas": [{"sub": "war", "sas": 0.4}]},
    ]
    day_point = {"date": "2026-01-24", "top_sas": [{"sub": "war", "sas": 1.2}]}
    triggers, state = evaluate_watchlist(day_point, history, [rule], default_state())
    assert triggers

    day_point2 = {"date": "2026-01-25", "top_sas": [{"sub": "war", "sas": 1.3}]}
    triggers2, _ = evaluate_watchlist(day_point2, history + [day_point], [rule], state)
    assert triggers2 == []
