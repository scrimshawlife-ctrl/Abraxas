from __future__ import annotations

import os
import tempfile

from abraxas.oracle.v2.export import export_run, compute_run_id


def _env():
    return {
        "oracle_signal": {
            "window": {"start_iso": "2025-12-28T00:00:00Z", "end_iso": "2025-12-29T00:00:00Z", "bucket": "day"},
            "scores_v1": {"slang": {"top_vital": [], "top_risk": []}, "aalmanac": {"top_patterns": []}},
            "v2": {
                "mode": "SNAPSHOT",
                "mode_decision": {"mode": "SNAPSHOT", "reasons": ["DEFAULT"], "fingerprint": "FP"},
                "compliance": {"status": "GREEN", "provenance": {"config_hash": "CFG"}},
            },
        }
    }


def _surface():
    return {"mode": "SNAPSHOT", "status": "GREEN", "top_slang_vital": [], "top_slang_risk": [], "top_patterns": []}


def test_compute_run_id_deterministic():
    a = compute_run_id(_env())
    b = compute_run_id(_env())
    assert a == b
    assert isinstance(a, str)
    assert len(a) == 16


def test_export_writes_files_and_manifest_hashes():
    env = _env()
    surf = _surface()
    with tempfile.TemporaryDirectory() as td:
        manifest = export_run(envelope=env, surface=surf, out_dir=td)
        run_id = manifest["run_id"]
        run_path = os.path.join(td, run_id)
        assert os.path.exists(os.path.join(run_path, "surface.json"))
        assert os.path.exists(os.path.join(run_path, "envelope.json"))
        assert os.path.exists(os.path.join(run_path, "manifest.json"))
        assert "surface_sha256" in manifest["hashes"]
        assert "envelope_sha256" in manifest["hashes"]
