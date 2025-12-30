from __future__ import annotations

import os
import tempfile

from abraxas.oracle.v2.bundle import run_bundle


def test_run_bundle_exports_and_returns_run_id():
    env = {"oracle_signal": {"scores_v1": {"slang": {"top_risk": []}, "aalmanac": {"top_patterns": []}}}}
    with tempfile.TemporaryDirectory() as td:
        out = run_bundle(
            envelope=env,
            config_hash="FIXED_CONFIG_HASH_0000000000000000",
            out_dir=td,
            do_stabilization_tick=False,
        )
        assert isinstance(out["run_id"], str)
        assert len(out["run_id"]) == 16
        # latest files should exist via export_run only in run folder; not in td/latest.
        run_path = os.path.join(td, out["run_id"])
        assert os.path.exists(os.path.join(run_path, "surface.json"))
        assert os.path.exists(os.path.join(run_path, "envelope.json"))
        assert os.path.exists(os.path.join(run_path, "manifest.json"))
