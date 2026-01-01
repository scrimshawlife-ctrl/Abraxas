from __future__ import annotations

from abraxas.oracle.v2.render import render_by_mode


def _base_env(mode: str):
    return {
        "oracle_signal": {
            "window": {"start_iso": "2025-12-28T00:00:00Z", "end_iso": "2025-12-29T00:00:00Z", "bucket": "day"},
            "scores_v1": {
                "slang": {"top_vital": [], "top_risk": []},
                "aalmanac": {"top_patterns": []},
            },
            "v2": {
                "mode": mode,
                "compliance": {"status": "GREEN", "provenance": {"config_hash": "FIXED_CONFIG_HASH_0000000000000000"}},
            },
        }
    }


def test_snapshot_omits_evidence_even_if_present():
    env = _base_env("SNAPSHOT")
    env["oracle_signal"]["evidence"] = {"paths": {"news": "var/evidence/news.json"}, "hashes": {"news": "abc"}}
    out = render_by_mode(env)
    assert out["mode"] == "SNAPSHOT"
    assert "evidence" not in out


def test_analyst_includes_evidence_pointers_when_present():
    env = _base_env("ANALYST")
    env["oracle_signal"]["evidence"] = {"paths": {"news": "var/evidence/news.json"}, "hashes": {"news": "abc"}}
    out = render_by_mode(env)
    assert out["mode"] == "ANALYST"
    assert "evidence" in out
    assert "paths" in out["evidence"]
    assert "hashes" in out["evidence"]


def test_analyst_omits_evidence_when_absent():
    env = _base_env("ANALYST")
    out = render_by_mode(env)
    assert out["mode"] == "ANALYST"
    assert "evidence" not in out
