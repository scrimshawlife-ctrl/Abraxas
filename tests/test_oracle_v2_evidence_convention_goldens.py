from __future__ import annotations

import json
import os
import tempfile

from abraxas.oracle.v2.evidence_convention import evidence_dir_for_envelope, evidence_paths, attach_evidence_from_run_dir


def _env():
    return {
        "oracle_signal": {
            "window": {"start_iso": "2025-12-28T00:00:00Z"},
            "v2": {
                "mode": "SNAPSHOT",
                "mode_decision": {"fingerprint": "FP", "mode": "SNAPSHOT", "reasons": ["DEFAULT"], "tags": {"state": "INFERRED", "confidence": 0.5}, "provenance": {"config_hash": "CFG"}},
                "compliance": {"status": "GREEN", "date_iso": "2025-12-28T00:00:00Z", "checks": {"v1_golden_pass_rate": 1.0, "drift_budget_violations": 0, "evidence_bundle_overflow_rate": 0.0, "ci_volatility_correlation": 1.0, "interaction_noise_rate": 0.0}, "gates": {"min_days_run": 30, "min_v1_pass_rate": 0.98, "max_drift_violations": 0, "max_evidence_overflow": 0.02, "min_ci_corr": 0.6, "max_interaction_noise": 0.3}, "provenance": {"config_hash": "CFG"}},
            },
        }
    }


def test_evidence_dir_deterministic():
    env = _env()
    with tempfile.TemporaryDirectory() as td:
        d1 = evidence_dir_for_envelope(env, out_dir=td)
        d2 = evidence_dir_for_envelope(env, out_dir=td)
        assert d1 == d2
        assert d1.endswith(os.path.join("evidence"))


def test_evidence_paths_creates_dir_and_returns_paths():
    env = _env()
    with tempfile.TemporaryDirectory() as td:
        paths = evidence_paths(envelope=env, out_dir=td, names=["news", "slang"], ext=".json")
        assert "news" in paths and paths["news"].endswith(os.path.join("evidence", "news.json"))
        assert os.path.exists(os.path.dirname(paths["news"]))


def test_attach_evidence_from_run_dir_attaches_only_existing():
    env = _env()
    with tempfile.TemporaryDirectory() as td:
        # Create one evidence file in the deterministic location
        paths = evidence_paths(envelope=env, out_dir=td, names=["news"], ext=".json")
        with open(paths["news"], "w", encoding="utf-8") as f:
            json.dump({"ok": True}, f)

        out = attach_evidence_from_run_dir(
            envelope=env,
            out_dir=td,
            files={"news": "news.json", "missing": "missing.json"},
            compute_hashes=False,
        )
        ev = out["oracle_signal"]["evidence"]
        assert "news" in ev["paths"]
        assert "missing" not in ev["paths"]
