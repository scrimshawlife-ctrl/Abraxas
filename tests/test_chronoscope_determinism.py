from __future__ import annotations

from pathlib import Path

from abraxas_ase.chronoscope import ChronoscopeState, DayPoint, update_state, write_state


def test_chronoscope_determinism(tmp_path: Path) -> None:
    state = ChronoscopeState(version=1, key_fingerprint="deadbeef", series=[])
    dp1 = DayPoint(
        date="2026-01-24",
        run_id="r1",
        counts={"tier2_hits": 2},
        top_tap=[{"token": "alpha", "tap": 1.0}],
        top_sas=[{"sub": "war", "sas": 1.2}],
        lane_counts={"core": 1, "canary": 0},
        pfdi_alerts_count=0,
        pack_hash="h1",
    )
    dp2 = DayPoint(
        date="2026-01-23",
        run_id="r0",
        counts={"tier2_hits": 1},
        top_tap=[{"token": "beta", "tap": 0.8}],
        top_sas=[{"sub": "peace", "sas": 0.9}],
        lane_counts={"core": 0, "canary": 1},
        pfdi_alerts_count=1,
        pack_hash="h0",
    )

    state = update_state(state, dp1)
    state = update_state(state, dp2)
    out1 = tmp_path / "s1.json"
    out2 = tmp_path / "s2.json"
    write_state(out1, state)
    write_state(out2, state)

    assert out1.read_bytes() == out2.read_bytes()
    payload = out1.read_text(encoding="utf-8")
    assert payload.index("2026-01-23") < payload.index("2026-01-24")
