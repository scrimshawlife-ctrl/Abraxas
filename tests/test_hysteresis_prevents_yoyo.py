from __future__ import annotations

from abraxas_ase.hysteresis import HysteresisParams, apply_hysteresis, default_state


def test_hysteresis_prevents_yoyo() -> None:
    params = HysteresisParams()
    state = default_state()
    lanes = []
    suggestions = ["shadow", "canary", "shadow", "canary", "shadow", "canary"]
    for s in suggestions:
        lane, state, _ = apply_hysteresis(s, state, params)
        lanes.append(lane)

    assert "canary" not in lanes
