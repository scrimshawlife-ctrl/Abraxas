from __future__ import annotations

import json
import os
import tempfile

from abraxas.oracle.v2.evidence_write import main


def test_evidence_write_writes_into_run_dir_and_updates_latest_envelope():
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "out")
        latest = os.path.join(out, "latest")
        os.makedirs(latest, exist_ok=True)

        # Minimal envelope with v2 block already present so compute_run_id works.
        env = {
            "oracle_signal": {
                "window": {"start_iso": "2025-12-28T00:00:00Z"},
                "v2": {
                    "mode": "SNAPSHOT",
                    "mode_decision": {"fingerprint": "FP", "mode": "SNAPSHOT", "reasons": ["DEFAULT"], "tags": {"state": "INFERRED", "confidence": 0.5}, "provenance": {"config_hash": "CFG"}},
                    "compliance": {"status": "GREEN", "date_iso": "2025-12-28T00:00:00Z", "checks": {"v1_golden_pass_rate": 1.0, "drift_budget_violations": 0, "evidence_bundle_overflow_rate": 0.0, "ci_volatility_correlation": 1.0, "interaction_noise_rate": 0.0}, "gates": {"min_days_run": 30, "min_v1_pass_rate": 0.98, "max_drift_violations": 0, "max_evidence_overflow": 0.02, "min_ci_corr": 0.6, "max_interaction_noise": 0.3}, "provenance": {"config_hash": "CFG"}},
                },
            }
        }
        with open(os.path.join(latest, "envelope.json"), "w", encoding="utf-8") as f:
            json.dump(env, f)

        rc = main([
            "--out-dir", out,
            "--v1-out-dir", out,
            "--name", "news",
            "--json", '{"ok":true}',
        ])
        assert rc == 0
        # latest envelope updated with evidence pointers
        with open(os.path.join(latest, "envelope.json"), "r", encoding="utf-8") as f:
            env2 = json.load(f)
        assert "evidence" in env2["oracle_signal"]
        assert "news" in env2["oracle_signal"]["evidence"]["paths"]
