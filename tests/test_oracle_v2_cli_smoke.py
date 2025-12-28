from __future__ import annotations

import json
import os
import tempfile

from abraxas.oracle.v2.cli import main


def test_cli_minimal_shell():
    """Test CLI with minimal envelope shell."""
    with tempfile.TemporaryDirectory() as td:
        ret = main([
            "--config-hash", "FIXED_CONFIG_HASH_0000000000000000",
            "--out-dir", td,
            "--no-ledger",
        ])
        assert ret == 0
        # Should create a run directory
        runs = os.listdir(td)
        assert len(runs) == 1


def test_cli_auto_discover():
    """Test CLI with auto-discovery."""
    with tempfile.TemporaryDirectory() as td:
        # Create a v1 envelope
        v1_out = os.path.join(td, "v1_out")
        latest = os.path.join(v1_out, "latest")
        os.makedirs(latest, exist_ok=True)
        env_path = os.path.join(latest, "envelope.json")
        with open(env_path, "w", encoding="utf-8") as f:
            json.dump({
                "oracle_signal": {
                    "window": {"start_iso": "2025-12-28T00:00:00Z"},
                    "scores_v1": {"slang": {"top_vital": [], "top_risk": []}},
                }
            }, f)

        v2_out = os.path.join(td, "v2_out")
        ret = main([
            "--config-hash", "FIXED_CONFIG_HASH_0000000000000000",
            "--auto-in-envelope",
            "--v1-out-dir", v1_out,
            "--out-dir", v2_out,
            "--no-ledger",
        ])
        assert ret == 0
        # Should create a v2 run directory
        runs = os.listdir(v2_out)
        assert len(runs) == 1
