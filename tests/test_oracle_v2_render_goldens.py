from __future__ import annotations

from abraxas.oracle.v2.render import render_by_mode


def _env(mode: str):
    return {
        "oracle_signal": {
            "window": {"start_iso": "2025-12-28T00:00:00Z", "end_iso": "2025-12-29T00:00:00Z", "bucket": "day"},
            "scores_v1": {
                "slang": {
                    "top_vital": [{"term": "ghostmode", "SVS": 85.56}],
                    "top_risk": [{"term": "ghostmode", "MRS": 37.63}],
                },
                "aalmanac": {"top_patterns": [{"pattern": "recurrence"}]},
            },
            "v2": {
                "mode": mode,
                "compliance": {"status": "GREEN", "provenance": {"config_hash": "FIXED"}},
            },
        }
    }


def test_render_snapshot_mode():
    out = render_by_mode(_env("SNAPSHOT"))
    assert out["mode"] == "SNAPSHOT"
    assert "top_slang_vital" in out
    assert "envelope" not in out


def test_render_analyst_mode():
    out = render_by_mode(_env("ANALYST"))
    assert out["mode"] == "ANALYST"
    assert "envelope" in out


def test_render_ritual_mode():
    out = render_by_mode(_env("RITUAL"))
    assert out["mode"] == "RITUAL"
    assert "disclaimer" in out
