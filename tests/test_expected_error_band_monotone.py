from __future__ import annotations

from abraxas.forecast.scoring import expected_error_band


def test_eeb_risk_widens():
    low = expected_error_band(
        horizon="weeks",
        phase="plateau",
        half_life_days=40,
        manipulation_risk=0.1,
        recurrence_days=7,
    )
    high = expected_error_band(
        horizon="weeks",
        phase="plateau",
        half_life_days=40,
        manipulation_risk=0.8,
        recurrence_days=7,
    )
    assert high.timing_days_max > low.timing_days_max
